
#     raw_id = save_raw_payload(
#         source="imdb_trending",
#         source_key=date.today().isoformat(),
#         payload=payload,
#     )

# CREATE TABLE IF NOT EXISTS raw_imdb_payloads (
#     id BIGSERIAL PRIMARY KEY,
#     source TEXT NOT NULL,
#     source_key TEXT NOT NULL,
#     payload JSONB NOT NULL,
#     fetched_at TIMESTAMPTZ DEFAULT now(),
#     processed_at TIMESTAMPTZ,
#     status TEXT DEFAULT 'new'
# );

def update_movie(conn, movie_id: str):
    """
    Retrieve if the movie has been updated in the last 6 months. Returns the id if found, otherwise None.
    """
    sql = """
    SELECT   media_id
    FROM     media 
    WHERE    (updated_at >= NOW() - INTERVAL '2 months' and (media_release_date IS NULL or media_release_date >= NOW() - INTERVAL '18 months')) 
             OR (updated_at >= NOW() - INTERVAL '6 months')
    AND      media_imdb_id = %s
    """
    try:
        result = conn.execute(sql, (movie_id,))  
        return False if result else True  
    except Exception as e:
        print(f"Error retrieving last updated timestamp for movie {movie_id}: {e}")
        return True


def get_last_processed_payload(conn, source: str, version: int):
    """
    Retrieve the last processed payload for a given source and source_key.
    """
    sql = """
    SELECT  id, payload, fetched_at, processed_at
    FROM    raw_imdb_payloads
    WHERE   source = %s AND  
            version = %s AND
            fetched_at::date >= CURRENT_DATE
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