from datetime import date, datetime, timedelta


def upsert_trending_snapshot(
        conn,
        media_id: int,
        rank: int,
        snapshot_date: datetime | None = date.today(),
) -> None:
    if not media_id or rank is None:
        raise ValueError("media_id and rank are required for upserting trending snapshot.")

    sql = """
          INSERT INTO trending_snapshot (media_id, 
                                         rank, 
                                         snapshot_date)
          VALUES (%(media_id)s, 
                  %(rank)s, 
                  date_trunc('hour', now() + interval '30 minutes')  
                 ) 
          ON CONFLICT (media_id, snapshot_date)
          DO NOTHING  
          """

    conn.execute(
        sql,
        {
            "media_id": media_id,
            "rank": rank
        },
    )

