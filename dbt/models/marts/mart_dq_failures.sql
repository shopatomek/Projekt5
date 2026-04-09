{{
    config(
        materialized='view',
        schema='analytics'
    )
}}

SELECT
    DATE(generated_at AT TIME ZONE 'Europe/Warsaw') AS date,
    content->>'table' AS table_name,
    content->>'record_id' AS record_id,
    content->'failed_checks' AS failed_checks,
    content->>'auto_repaired' AS auto_repaired,
    generated_at
FROM {{ source('raw', 'ai_insights') }}
WHERE insight_type = 'dq_failure'