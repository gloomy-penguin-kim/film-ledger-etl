import hashlib
import requests

from app.etl.db_conn import DatabaseConn

db = DatabaseConn()

def loop_through_rows():
    with db.conn.cursor() as cur:
        cur.execute("select * from image_asset",())
        if cur.description:
            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]

            for result in results:
                source_url = result["source_url"]


def download_image(source_url: str | None) -> tuple[bytes, str]:
    if not source_url: return (None, None)

    response = requests.get(source_url, timeout=20)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")

    if not content_type.startswith("image/"):
        raise ValueError(f"URL did not return an image: {content_type}")

    return response.content, content_type


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()