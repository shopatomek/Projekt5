

CREATE TABLE IF NOT EXISTS crypto_prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    price_usd DECIMAL(18, 8) NOT NULL,
    market_cap BIGINT,
    volume_24h BIGINT,
    price_change_24h DECIMAL(10, 2),
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_crypto_timestamp ON crypto_prices(timestamp DESC);

-- Tabela dla danych pogodowych
CREATE TABLE IF NOT EXISTS weather_data (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    temperature DECIMAL(5, 2),
    humidity INTEGER,
    weather_condition VARCHAR(50),
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Tabela dla newsów
CREATE TABLE IF NOT EXISTS news_articles (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    source VARCHAR(100),
    url TEXT,
    published_at TIMESTAMPTZ,
    sentiment_score DECIMAL(3, 2),
    fetched_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Tabela dla danych giełdowych
CREATE TABLE IF NOT EXISTS stock_prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    close_price DECIMAL(10, 2),
    volume BIGINT,
    trading_date DATE NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, trading_date)
);

-- Tabela dla AI insights (cache)
CREATE TABLE IF NOT EXISTS ai_insights (
    id SERIAL PRIMARY KEY,
    insight_type VARCHAR(50) NOT NULL,
    content JSONB NOT NULL,
    data_snapshot JSONB,
    generated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);


CREATE OR REPLACE VIEW daily_crypto_stats AS
SELECT
    symbol,
    AVG(price_usd) as avg_price,
    MAX(price_usd) as max_price,
    MIN(price_usd) as min_price,
    DATE(timestamp AT TIME ZONE 'Europe/Warsaw') as date
FROM crypto_prices
WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY symbol, DATE(timestamp AT TIME ZONE 'Europe/Warsaw');




-- 1. INDEKS FULL-TEXT SEARCH dla newsów
CREATE INDEX IF NOT EXISTS idx_news_fts
    ON news_articles
    USING GIN(to_tsvector('english', title || ' ' || COALESCE(description, '')));

-- Indeks na timestamp dla szybszych zapytań z zakresem dat
CREATE INDEX IF NOT EXISTS idx_news_published_at ON news_articles(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_insights_type_time ON ai_insights(insight_type, generated_at DESC);


-- 2. WIDOK: v_dq_summary — agregacja DQ failures
CREATE OR REPLACE VIEW v_dq_summary AS
SELECT
    DATE(generated_at AT TIME ZONE 'Europe/Warsaw') AS date,
    content->>'table' AS table_name,
    COUNT(*) AS failure_count,
    SUM(CASE WHEN (content->>'auto_repaired')::boolean = true THEN 1 ELSE 0 END) AS auto_repaired_count,
    content->'failed_checks'->>0 AS primary_failure_type,
    MAX(generated_at) AS last_seen
FROM ai_insights
WHERE insight_type = 'dq_failure'
GROUP BY
    DATE(generated_at AT TIME ZONE 'Europe/Warsaw'),
    content->>'table',
    content->'failed_checks'->>0
ORDER BY date DESC, failure_count DESC;


-- 3. WIDOK: v_dq_record_detail — szczegóły każdego błędu
CREATE OR REPLACE VIEW v_dq_record_detail AS
SELECT
    generated_at,
    content->>'table' AS table_name,
    content->>'record_id' AS record_id,
    content->'failed_checks' AS failed_checks,
    (content->>'auto_repaired')::boolean AS auto_repaired,
    content->'original_record' AS original_record
FROM ai_insights
WHERE insight_type = 'dq_failure'
ORDER BY generated_at DESC;


-- 4. WIDOK: v_news_sentiment_daily — sentyment newsów per dzień
CREATE OR REPLACE VIEW v_news_sentiment_daily AS
SELECT
    DATE(published_at AT TIME ZONE 'Europe/Warsaw') AS date,
    COUNT(*) AS article_count,
    ROUND(AVG(sentiment_score)::numeric, 3) AS avg_sentiment,
    ROUND(MIN(sentiment_score)::numeric, 3) AS min_sentiment,
    ROUND(MAX(sentiment_score)::numeric, 3) AS max_sentiment,
    COUNT(CASE WHEN sentiment_score > 0.2 THEN 1 END) AS positive_count,
    COUNT(CASE WHEN sentiment_score < -0.2 THEN 1 END) AS negative_count,
    COUNT(CASE WHEN sentiment_score IS NULL THEN 1 END) AS no_sentiment_count
FROM news_articles
WHERE published_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(published_at AT TIME ZONE 'Europe/Warsaw')
ORDER BY date DESC;


-- 5. MATERIALIZED VIEW: mart_market_daily — główny widok dashboard
CREATE MATERIALIZED VIEW IF NOT EXISTS mart_market_daily AS
SELECT
    DATE(cp.timestamp AT TIME ZONE 'Europe/Warsaw') AS date,

    -- Krypto — agregaty dzienne
    COUNT(DISTINCT cp.symbol) AS active_coins,
    ROUND(AVG(cp.price_usd) FILTER (WHERE cp.symbol = 'BTC')::numeric, 2) AS btc_avg_price,
    ROUND(AVG(cp.price_usd) FILTER (WHERE cp.symbol = 'ETH')::numeric, 2) AS eth_avg_price,
    ROUND(AVG(cp.price_change_24h)::numeric, 4) AS market_avg_change,
    ROUND(MAX(ABS(cp.price_change_24h))::numeric, 4) AS max_abs_price_change,
    CASE
        WHEN AVG(cp.price_change_24h) > 1  THEN 'Bullish'
        WHEN AVG(cp.price_change_24h) < -1 THEN 'Bearish'
        ELSE 'Neutral'
    END AS market_sentiment,

    -- Newsy — agregaty dzienne
    COUNT(DISTINCT na.id) AS news_count,
    ROUND(AVG(na.sentiment_score)::numeric, 3) AS avg_news_sentiment,
    COUNT(DISTINCT na.id) FILTER (WHERE na.sentiment_score > 0.2) AS positive_news,
    COUNT(DISTINCT na.id) FILTER (WHERE na.sentiment_score < -0.2) AS negative_news,

    -- Pogoda Warszawa
    ROUND(AVG(wd.temperature)::numeric, 1) AS warsaw_avg_temp,
    MODE() WITHIN GROUP (ORDER BY wd.weather_condition) AS dominant_weather,

    -- DQ stats — ile błędów wykryto tego dnia
    COUNT(DISTINCT ai.id) AS dq_failures_count

FROM crypto_prices cp

LEFT JOIN news_articles na
    ON DATE(na.published_at AT TIME ZONE 'Europe/Warsaw')
     = DATE(cp.timestamp AT TIME ZONE 'Europe/Warsaw')

LEFT JOIN weather_data wd
    ON DATE(wd.timestamp AT TIME ZONE 'Europe/Warsaw')
     = DATE(cp.timestamp AT TIME ZONE 'Europe/Warsaw')

LEFT JOIN ai_insights ai
    ON DATE(ai.generated_at AT TIME ZONE 'Europe/Warsaw')
     = DATE(cp.timestamp AT TIME ZONE 'Europe/Warsaw')
    AND ai.insight_type = 'dq_failure'

WHERE cp.timestamp >= CURRENT_DATE - INTERVAL '90 days'

GROUP BY DATE(cp.timestamp AT TIME ZONE 'Europe/Warsaw')
ORDER BY date DESC;

-- Unikalny indeks wymagany dla REFRESH CONCURRENTLY
CREATE UNIQUE INDEX IF NOT EXISTS idx_mart_market_daily_date ON mart_market_daily(date);