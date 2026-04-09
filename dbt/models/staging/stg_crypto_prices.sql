{{ config(materialized='view') }}

SELECT
    symbol,
    price_usd,
    volume_24h,
    price_change_24h,
    timestamp AT TIME ZONE 'Europe/Warsaw' AS timestamp_local,
    DATE(timestamp AT TIME ZONE 'Europe/Warsaw') AS date
FROM {{ source('raw', 'crypto_prices') }}
WHERE price_usd > 0
  AND timestamp <= NOW()
