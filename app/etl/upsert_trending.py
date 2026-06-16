from datetime import date, datetime, timedelta


def upsert_trending_snapshot(
        db,
        trending_arr
) -> None:

    print("")
    print("upsert_trending_snapshot")

    for media_id, rank in trending_arr:

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

        db.conn.execute(
            sql,
            {
                "media_id": media_id,
                "rank": rank
            },
        )

