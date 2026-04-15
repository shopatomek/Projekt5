{{ config(materialized='table') }}

SELECT
    date,
    table_name,
    COUNT(*) as failures_count,
    SUM(CASE WHEN auto_repaired = 'true' THEN 1 ELSE 0 END) as auto_repaired_count
FROM {{ ref('mart_dq_failures') }}
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY date, table_name
ORDER BY date DESC, table_name