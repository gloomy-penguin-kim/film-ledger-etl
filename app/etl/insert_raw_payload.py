def update_movie(conn, movie_id: str):
    """
    Retrieve if the movie has been updated in the last 6 months. Returns the id if found, otherwise None.
    UNLESS - if there is now an image for it
    """
    sql = """
             SELECT
                m.media_id,
            
                (
                    m.updated_at < now() - interval '2 months'
                    AND (
                        m.media_release_year IS NULL
                        OR m.media_release_date >= current_date - interval '18 months'
                    )
                ) OR (
                    m.updated_at < now() - interval '6 months'
                ) AS needs_a_refresh,
            
                NOT EXISTS (
                    SELECT 1
                    FROM image_asset_link ial
                    JOIN image_asset ia
                        ON ia.image_asset_id = ial.image_asset_id
                    WHERE ial.owner_type = 'media'
                      AND ial.owner_id = m.media_id
                      AND ial.image_kind = 'poster'
                      AND ia.source_url IS NOT NULL
                ) AS missing_image
            
            FROM media m
            WHERE m.media_imdb_id = %s
              AND m.updated_at = (
                  SELECT max(mm.updated_at)
                  FROM media mm
                  WHERE mm.media_imdb_id = m.media_imdb_id
              );
          """
    try:
        with conn.execute(sql, (movie_id,)) as cur:
            if cur.description:
                columns = [desc[0] for desc in cur.description]
                results = [dict(zip(columns, row)) for row in cur.fetchall()]
                return results[0] if len(results) > 0 else None, True, True
            return None, True, True

    except Exception as e:
        print(f"Error retrieving update info for movie {movie_id}: {e}")
        return None, True, True


def get_last_processed_payload(conn, source: str, version: int):
    """
    Retrieve the last processed payload for a given source and source_key.
    """
    sql = """
    SELECT  id, payload, fetched_at, processed_at
    FROM    raw_imdb_payloads
    WHERE   source = %s AND  
            version = %s AND
            fetched_at::date >= CURRENT_DATE - interval '1 hour'
    ORDER   BY fetched_at DESC
    LIMIT 1
    """
    try:
        with conn.execute(sql, (source, version)) as cur: 
            if cur.description: 
                columns = [desc[0] for desc in cur.description] 
                results = [dict(zip(columns, row)) for row in cur.fetchall()] 
                return results[0] if results else None 
    except Exception as e:
        print(f"Error retrieving last processed payload: {e}")
        return None


def save_raw_payload(conn, source: str, version: int, payload: str):
    """
    Save the raw JSON payload to the database.
    """
    sql = """
    INSERT INTO raw_imdb_payloads (source, version, payload)
    VALUES (%s, %s, %s)
    RETURNING id
    """
    try:
        result = conn.execute(sql, (source, version, payload))
        print(f"Saved raw payload with ID: {result[0]['id']}" if result else "Failed to save raw payload.")
        return result[0]["id"] if result else None
    except Exception as e:
        print(f"Error saving raw payload: {e}")
        return None


def mark_processed(conn, raw_id: int): 
    """Mark a raw payload as processed"""
    sql = """
    UPDATE raw_imdb_payloads
    SET status = 'processed', processed_at = now()
    WHERE id = %s
    """
    try:
        conn.execute(sql, (raw_id,))
        print(f"Marked raw payload {raw_id} as processed.")
    except Exception as e:
        print(f"Error marking raw payload, {raw_id}, as processed: {e}")        