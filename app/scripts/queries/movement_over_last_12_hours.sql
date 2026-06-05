WITH latest AS (
    SELECT max(snapshot_date) AS latest_snapshot
    FROM trending_snapshot
),
windowed AS (
    SELECT
        ts.*
    FROM trending_snapshot ts
    CROSS JOIN latest l
    WHERE ts.snapshot_date >= l.latest_snapshot - interval '12 hours'
),
ranked AS (
    SELECT DISTINCT ON (media_id)
        media_id,
        rank AS current_rank,
        snapshot_date AS current_snapshot
    FROM windowed
    ORDER BY media_id, snapshot_date DESC
),
baseline AS (
    SELECT DISTINCT ON (media_id)
        media_id,
        rank AS previous_rank,
        snapshot_date AS previous_snapshot
    FROM windowed
    ORDER BY media_id, snapshot_date ASC
)
SELECT
    r.media_id,
    b.previous_snapshot,
    b.previous_rank,
    r.current_snapshot,
    r.current_rank,
    b.previous_rank - r.current_rank AS movement
FROM ranked r
JOIN baseline b
    ON b.media_id = r.media_id
WHERE r.current_snapshot = (
    SELECT latest_snapshot FROM latest
)
ORDER BY current_rank;