{{
    config(
        materialized='view'
    )
}}

SELECT
    city,
    temperature,
    humidity,
    weather_condition,
    timestamp AT TIME ZONE 'Europe/Warsaw' AS timestamp_local,
    DATE(timestamp AT TIME ZONE 'Europe/Warsaw') AS date
FROM {{ source('raw', 'weather_data') }}
WHERE city = 'Warsaw'