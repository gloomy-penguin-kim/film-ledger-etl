WITH snapshots AS (
    SELECT DISTINCT snapshot_date
    FROM trending_snapshot
    ORDER BY snapshot_date DESC
    LIMIT 2
),
ordered AS (
    SELECT snapshot_date,
           row_number() OVER (
               ORDER BY snapshot_date DESC
           ) rn
    FROM snapshots
)

SELECT
    cur.media_id,
    cur.rank
FROM trending_snapshot cur
JOIN ordered o1
    ON cur.snapshot_date = o1.snapshot_date
   AND o1.rn = 1

WHERE NOT EXISTS (
    SELECT 1
    FROM trending_snapshot prev
    JOIN ordered o2
        ON prev.snapshot_date = o2.snapshot_date
       AND o2.rn = 2
    WHERE prev.media_id = cur.media_id
);