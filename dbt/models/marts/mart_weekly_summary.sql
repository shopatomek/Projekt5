{{ config(materialized='table') }}

SELECT
    DATE_TRUNC('week', date) as week,
    ROUND(AVG(btc_avg_price)::numeric, 2) as avg_btc_price,
    ROUND(AVG(eth_avg_price)::numeric, 2) as avg_eth_price,
    ROUND(AVG(avg_price_change)::numeric, 2) as avg_market_change,
    SUM(news_count) as total_news,
    ROUND(AVG(avg_temperature)::numeric, 1) as avg_temperature
FROM {{ ref('mart_market_daily') }}
WHERE date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY DATE_TRUNC('week', date)
ORDER BY week DESC