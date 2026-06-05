from datetime import date, datetime, timedelta


def round_to_nearest_hour(dt):
    if not isinstance(dt, datetime):
        raise TypeError("Input must be a datetime object")

    # Calculate minutes to decide rounding
    if dt.minute >= 30:
        dt = dt.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    else:
        dt = dt.replace(minute=0, second=0, microsecond=0)
    return dt


def upsert_trending_snapshot(
        conn,
        media_id: int,
        rank: int,
        snapshot_date: datetime | None = date.today(),
) -> None:
    if not media_id or rank is None:
        raise ValueError("media_id and rank are required for upserting trending snapshot.")

    snapshot_date = round_to_nearest_hour(snapshot_date)

    sql = """
          INSERT INTO trending_snapshot (media_id, \
                                         rank, \
                                         snapshot_date)
          VALUES (%(media_id)s, \
                  %(rank)s, \
                  COALESCE(%(snapshot_date)s, current_date))
          ON CONFLICT (media_id, snapshot_date)
          DO NOTHING  \
          """

    conn.execute(
        sql,
        {
            "media_id": media_id,
            "rank": rank,
            "snapshot_date": snapshot_date,
        },
    )

