from datetime import date, datetime, timedelta
import pprint


def upsert_trending_snapshot(
        db,
        trending_arr
) -> None:

    print("")
    print("upsert_trending_snapshot")

    db.conn.execute("""
        delete from trending_snapshot
        where snapshot_date = date_trunc('hour', now() + interval '30 minutes') 
    """)

    try:
        for a in trending_arr:
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
            print(a)
            db.conn.execute(
                sql,
                a,
            )
        db.conn.commit()
    except Exception as e:
        print(e)
        db.conn.rollback()



