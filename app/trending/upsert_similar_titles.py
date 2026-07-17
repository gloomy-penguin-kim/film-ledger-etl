from app.trending.upsert_images import insert_image

from typing import Any

def upsert_similar_titles(conn, media_id: int, media: dict[str, Any]) -> None:
     similar_titles = media.get("similar_titles") or []

     print(f"{len(similar_titles)} similar_titles")

     if len(similar_titles) > 0:
         sql = "delete from media_similar_titles where media_id in (%s)"
         conn.execute(sql, (media_id,))

     st = 0
     for similar in similar_titles:
        similar_id = similar.get("id").strip()
        poster_url = similar.get("poster_url")

        if not similar_id: continue

        results = conn.execute(
            """
            INSERT INTO media_similar_titles (media_id,
                                              related_media_id,
                                              related_media_imdb_id)
            SELECT %(media_id)s as media_id,
                   m.media_id as related_media_id,
                   %(related_media_imdb_id)s as related_media_imdb_id
            FROM (SELECT %(related_media_imdb_id)s AS imdb_id) imdb
                     LEFT JOIN media m
                               ON m.media_imdb_id = imdb.imdb_id
            WHERE m.media_type = 'Movie' 
            ON CONFLICT (media_id, related_media_imdb_id)
                DO UPDATE SET related_media_id = EXCLUDED.related_media_id

            RETURNING related_media_id;
            """,
            {
                "media_id": media_id,
                "related_media_imdb_id": similar.get("id"),
            },
        )

        if not results: continue

        try:
            result = results.fetchone()

            if not result or not poster_url: continue

            related_media_id = result[0]

            if poster_url and related_media_id:
                insert_image(conn, {
                             "owner_id"   : related_media_id,
                             "owner_type" : "media",
                             "image_kind" : "poster",
                             "source_url" : poster_url,
                             "is_primary" : True
                })
        except Exception as e:
            print("-------------------------------------------------")
            print(e)
            print("-------------------------------------------------")
            raise Exception("here")




def upsert_connections(conn, media_id: int, media: dict[str, Any]) -> None:
    connections = media.get("connections") or []

    print(f"{len(connections)} connections")

    for connection in connections:
        connection_name = connection.get("relationship").strip()

        if not connection_name:
            continue

        with conn.execute(
                """
                INSERT INTO connection (connection_name)
                VALUES (%s)
                ON CONFLICT (connection_name) 
                    DO UPDATE SET connection_name = EXCLUDED.connection_name 
                RETURNING connection_id;
                """,
                (connection_name,),
        ) as cur:
            connection_id = cur.fetchone()[0]

        conn.execute(
            """
            INSERT INTO media_connection (media_id, 
                                          related_media_id, 
                                          related_media_imdb_id,  
                                          connection_id)
                SELECT %(media_id)s, 
                       m.media_id as related_media_id, 
                       imdb.imdb_id,  
                       %(connection_id)s
                FROM   (select %(related_media_imdb_id)s as imdb_id) as imdb 
                        left outer join media m 
                            on m.media_imdb_id = imdb.imdb_id
                WHERE m.media_type = 'Movie'
                LIMIT 1 
            ON CONFLICT (media_id, related_media_imdb_id, connection_id)
            DO NOTHING;
            """,
            {
                "media_id": media_id,
                "related_media_imdb_id": connection.get("id"),
                "connection_id": connection_id,
            },
        )


