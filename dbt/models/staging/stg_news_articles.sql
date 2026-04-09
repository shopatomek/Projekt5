{{
    config(
        materialized='view'
    )
}}

SELECT
    id,
    title,
    description,
    source,
    url,
    published_at AT TIME ZONE 'Europe/Warsaw' AS published_at_local,
    DATE(published_at AT TIME ZONE 'Europe/Warsaw') AS date
FROM {{ source('raw', 'news_articles') }}
WHERE title IS NOT NULL AND title != ''