SELECT
    media_id,
    round(avg(rank), 2) AS avg_rank,
    min(rank) AS best_rank,
    count(*) AS snapshots
FROM trending_snapshot
GROUP BY media_id
HAVING count(*) >= 3
ORDER BY avg_rank;