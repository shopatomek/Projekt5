{{ config(materialized='table') }}

SELECT
    date,
    avg_temperature,
    btc_avg_price,
    LAG(btc_avg_price, 1) OVER (ORDER BY date) as prev_btc_price,
    ROUND(
        (btc_avg_price - LAG(btc_avg_price, 1) OVER (ORDER BY date)) / 
        NULLIF(LAG(btc_avg_price, 1) OVER (ORDER BY date), 0) * 100, 2
    ) as btc_daily_pct_change
FROM {{ ref('mart_market_daily') }}
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY date DESC