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

-- Widoki agregujące dla dashboardu
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

