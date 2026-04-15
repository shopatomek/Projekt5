{{ config(materialized='table', unique_key='date') }}

SELECT
    cp.date,
    ROUND(AVG(CASE WHEN cp.symbol = 'BTC' THEN cp.price_usd END)::numeric, 2) AS btc_avg_price,
    ROUND(AVG(CASE WHEN cp.symbol = 'ETH' THEN cp.price_usd END)::numeric, 2) AS eth_avg_price,
    ROUND(AVG(cp.price_change_24h)::numeric, 2) AS avg_price_change,
    COUNT(DISTINCT cp.symbol) AS active_coins,
    COUNT(DISTINCT na.id) AS news_count,
    ROUND(AVG(wd.temperature)::numeric, 1) AS avg_temperature,
    COUNT(DISTINCT ai.id) AS dq_failures_count   -- ← dodaj tę linię
FROM {{ ref('stg_crypto_prices') }} cp
LEFT JOIN {{ ref('stg_news_articles') }} na ON cp.date = na.date
LEFT JOIN {{ ref('stg_weather_data') }} wd ON cp.date = wd.date
LEFT JOIN {{ source('raw', 'ai_insights') }} ai 
    ON DATE(ai.generated_at AT TIME ZONE 'Europe/Warsaw') = cp.date
    AND ai.insight_type = 'dq_failure'
GROUP BY cp.date
ORDER BY cp.date DESC