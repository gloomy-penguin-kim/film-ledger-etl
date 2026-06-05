WITH latest AS (
    SELECT max(snapshot_date) AS snapshot_date
    FROM trending_snapshot
)
SELECT
    ts.rank,
    ts.media_id,
    m.media_title
FROM trending_snapshot ts
JOIN latest l
    ON l.snapshot_date = ts.snapshot_date
JOIN media m
    ON m.media_id = ts.media_id
ORDER BY ts.rank;