# Metabase Dashboard Setup Instructions

## Prerequisites

- Metabase running at http://localhost:3001
- PostgreSQL database `business_intelligence` added as a data source

## Dashboard 1: Market Daily Overview

### Card 1: Last Update Time

```sql
SELECT MAX(timestamp) as last_update FROM crypto_prices
```

Visualization: Scalar / Number

### Card 2: Avg Market Change (24h)

```sql
SELECT ROUND(AVG(price_change_24h)::numeric, 2) as avg_change_percent
FROM crypto_prices
WHERE timestamp > NOW() - INTERVAL '1 day'
```

Visualization: Gauge

### Card 3: Market Sentiment

```sql
SELECT
    CASE
        WHEN AVG(price_change_24h) > 1 THEN 'BULLISH 🐂'
        WHEN AVG(price_change_24h) < -1 THEN 'BEARISH 🐻'
        ELSE 'NEUTRAL ⚖️'
    END as sentiment
FROM crypto_prices
WHERE timestamp > NOW() - INTERVAL '1 day'
```

Visualization: Scalar

### Card 4: Price Anomalies (24h)

```sql
SELECT COUNT(*) as anomaly_count
FROM ai_insights
WHERE insight_type = 'price_anomaly'
  AND generated_at > NOW() - INTERVAL '1 day'
```

Visualization: Gauge

### Card 5: BTC & ETH Price Trend (7d)

```sql
SELECT
    DATE(timestamp AT TIME ZONE 'Europe/Warsaw') as date,
    MAX(CASE WHEN symbol = 'BTC' THEN price_usd END) as BTC,
    MAX(CASE WHEN symbol = 'ETH' THEN price_usd END) as ETH
FROM crypto_prices
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY DATE(timestamp AT TIME ZONE 'Europe/Warsaw')
ORDER BY date
```

Visualization: Line chart

### Card 6: Top 10 Coins by Volume

```sql
SELECT
    symbol,
    price_usd,
    price_change_24h,
    volume_24h
FROM crypto_prices
WHERE timestamp IN (SELECT MAX(timestamp) FROM crypto_prices GROUP BY symbol)
ORDER BY volume_24h DESC
LIMIT 10
```

Visualization: Table

### Card 7: Recent Anomalies

```sql
SELECT
    generated_at as detected_at,
    content->>'affected_symbols' as symbols,
    LEFT(content->>'message', 150) as message
FROM ai_insights
WHERE insight_type = 'price_anomaly'
ORDER BY generated_at DESC
LIMIT 5
```

Visualization: Table

## Dashboard 2: dbt Analytics Dashboard

### Card 1: Weekly Market Summary

```sql
SELECT
    week,
    avg_btc_price AS "BTC ($)",
    avg_eth_price AS "ETH ($)",
    avg_market_change AS "Avg Change (%)",
    total_news AS "News",
    avg_temperature AS "Temp (°C)"
FROM dbt_analytics_analytics.mart_weekly_summary
ORDER BY week DESC
```

Visualization: Table

### Card 2: News vs BTC Price Correlation

```sql
SELECT
    date,
    news_count AS "News Count",
    btc_avg_price AS "BTC Price ($)",
    btc_daily_pct_change AS "BTC Daily Change (%)"
FROM dbt_analytics_analytics.mart_news_correlation
ORDER BY date DESC
LIMIT 30
```

Visualization: Line chart (dual axis)

### Card 3: Data Quality Trend

```sql
SELECT
    date,
    table_name AS "Table",
    failures_count AS "Failures",
    auto_repaired_count AS "Auto Repaired"
FROM dbt_analytics_analytics.mart_dq_trend
ORDER BY date DESC, table_name
LIMIT 30
```

Visualization: Bar chart (grouped by Table)

### Card 4: Weather vs BTC Price

```sql
SELECT
    date,
    avg_temperature AS "Temperature (°C)",
    btc_avg_price AS "BTC Price ($)",
    btc_daily_pct_change AS "BTC Daily Change (%)"
FROM dbt_analytics_analytics.mart_weather_crypto_correlation
ORDER BY date DESC
LIMIT 30
```

Visualization: Line chart (dual axis)

### Card 5: Current BTC Price

```sql
SELECT price_usd AS "BTC Price ($)"
FROM crypto_prices
WHERE symbol = 'BTC'
ORDER BY timestamp DESC
LIMIT 1
```

Visualization: Gauge

### Card 6: Last Crypto Data Update

```sql
SELECT MAX(timestamp) AS "Last Binance Update"
FROM crypto_prices
```

Visualization: Scalar
