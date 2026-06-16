from datetime import datetime, timezone
from io import BytesIO
from PIL import Image
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import re
import base64
import boto3
import requests
import argparse
import hashlib
import os

from app.etl.db_conn import DatabaseConn
from app.download.cloudflare import load_image_variant_table_from_cloudflare

load_dotenv()


def sanitize_ascii(text):
    """Remove non-ASCII characters from a string."""
    return re.sub(r'[^\x00-\x7F]+', '', text)

def encode_base64(text):
    """Encode text to Base64 for safe storage."""
    return base64.b64encode(text.encode('utf-8')).decode('ascii')


def format_image(conn,
                 s3,
                 source_url,
                 result,
                 content,
                 content_type,
                 save_download=False,
                 quality=100):

    if not source_url: return None

    object_key = None
    public_url = None
    error_message = None
    sha256 = None
    byte_size = None
    actual_width = None
    actual_height = None

    image_asset_id = result.get("image_asset_id")
    description = result.get("description")
    path_str = result.get("path_str")
    variant_id = result.get("variant_id")
    target_width = result.get("target_width") or None
    target_height = result.get("target_height") or None
    is_cropped = result.get("is_cropped") or False

    s3_bucket = os.environ.get("CLOUDFLARE_BUCKET")
    s3_provider = os.environ.get("CLOUDFLARE_PROVIDER")

    image = Image.open(BytesIO(content))

    try:
        if target_width:
            image = resize_image(image, target_width)
            if is_cropped or target_height:
                image = resize_and_crop(image, target_width, target_height)

        actual_width = image.width
        actual_height = image.height

        filename = f"{image_asset_id}.webp"

        object_key = path_str + "/" + filename
        public_domain = os.environ.get("CLOUDFLARE_PUBLIC_URL")

        if object_key and public_domain:
            public_url = f"https://{public_domain}/{object_key}"
        else:
            raise Exception(f"public_domain = {public_domain}, object_key = {object_key}")

        buffer = BytesIO()
        image.save(buffer, format="WEBP", quality=quality)
        body = buffer.getvalue()
        content_type = "image/webp"

        sha256 = hashlib.sha256(body).hexdigest()
        byte_size = len(body)

        if save_download:
            debug_object_key = object_key.replace("/","_")
            debug_path = f"./app/data/{debug_object_key}"
            image.save(debug_path, format="WEBP", quality=quality)
            print(debug_path)

        try:
            metadata = {"source": "app.download.images",
                        "content_type": content_type,
                        'description': sanitize_ascii(description),
                        'description_base64': encode_base64(sanitize_ascii(description)),
                        "source_url": source_url,
                        "path_str": path_str,
                        "width": str(actual_width),
                        "height": str(actual_height),
                        "sha256": str(sha256),
                        "byte_size": str(byte_size),
                        "image_asset_id": str(image_asset_id),
                        "object_key": object_key,
                        "quality": str(quality),
                        }
            try:
                response = s3.head_object(Bucket=s3_bucket, Key=object_key)
                response_meta = response["Metadata"]

                s3.copy_object(
                    Bucket=s3_bucket,
                    Key=object_key,
                    CopySource={"Bucket": s3_bucket, "Key": object_key},
                    ContentType=content_type,
                    Metadata=response_meta|metadata,
                    MetadataDirective="REPLACE",
                )
            except ClientError as e:
                s3.put_object(
                    Bucket=s3_bucket,
                    Key=object_key,
                    Body=body,
                    ContentType=content_type,
                    Metadata=metadata,
                )

            print("public_url", public_url)

        except Exception as e:
            error_message = str(e)
            print("Cloudflare failed:", error_message)

    except Exception as e:
        error_message = str(e)
        print("Formatting failed:", error_message)


    status = 'failed' if error_message else 'cached'
    current_time = datetime.now(timezone.utc)
    with conn.execute("""
            INSERT INTO image_variant (image_asset_id, variant_id, storage_provider, storage_bucket,
                                       object_key, public_url, content_type, width, height,
                                       byte_size, sha256, status, error_message,
                                       last_checked_at, cached_at, updated_at)
            VALUES (%(image_asset_id)s, %(variant_id)s, %(storage_provider)s, %(storage_bucket)s,
                    %(object_key)s, %(public_url)s, %(content_type)s, %(width)s, %(height)s,
                    %(byte_size)s, %(sha256)s, %(status)s, %(error_message)s,
                    %(last_checked_at)s, %(cached_at)s, %(updated_at)s)
            ON CONFLICT (image_asset_id, variant_id, storage_bucket, storage_provider)
                DO UPDATE SET object_key      = excluded.object_key,
                              public_url      = excluded.public_url,
                              content_type    = excluded.content_type,
                              width           = excluded.width,
                              height          = excluded.height,
                              byte_size       = excluded.byte_size,
                              sha256          = excluded.sha256,
                              status          = excluded.status,
                              error_message   = excluded.error_message,
                              attempt_count   = image_variant.attempt_count + 1,
                              last_checked_at = excluded.last_checked_at,
                              cached_at       = excluded.cached_at,
                              updated_at      = excluded.updated_at
                RETURNING image_asset_id;
            """, {
                "image_asset_id": result.get("image_asset_id"),
                "variant_id": variant_id,
                "storage_provider": s3_provider,
                "storage_bucket": s3_bucket,
                "object_key": object_key,
                "public_url": public_url,
                "content_type": content_type,
                "width": actual_width,
                "height": actual_height,
                "byte_size": byte_size,
                "sha256": sha256,
                "status": status,
                "error_message": error_message,
                "last_checked": current_time,
                "last_checked_at": current_time,
                "cached_at": current_time if not error_message else None,
                "updated_at": current_time,
            }) as cur:
        conn.commit()
        return cur.fetchone()[0]


def loop_through(db, s3, results, save_download=False):

    for result in results:
        conn = db.connect()

        source_url = result.get("source_url")
        if not source_url: continue

        image_asset_id = result.get("image_asset_id")
        content_type = result.get("content_type")
        error_message = None
        sha256 = None

        try:
            content, content_type, sha256 = download_image(source_url)
            print("")
            print(f"Downloaded {source_url}")
            print(f"Content type: {content_type}")
            print(f"Sha256: {sha256}")

            for variant_needed in result.get("variants_needed"):
                print(f"path_str: {variant_needed["path_str"]}")
                original_content = content
                if variant_needed.get("needs_variant"):
                    image_asset_id = format_image(conn=conn,
                                 s3=s3,
                                 source_url=source_url,
                                 result=variant_needed,
                                 content=original_content,
                                 content_type=content_type,
                                 save_download=save_download,)

        except Exception as e:
            error_message = str(e)
            conn.rollback()
            print(f"Error downloading {source_url}")
            print(f"Error message: {error_message}")

        if not image_asset_id: continue

        print(f"image_asset_id: {image_asset_id}")
        status = 'failed' if error_message else 'cached'
        attempts = 0 if error_message else 1
        current_time = datetime.now(timezone.utc)
        conn.execute("""
            update image_asset 
               set source_content_type = %(content_type)s, 
                   source_sha256 = %(sha256)s, 
                   error_message = %(error_message)s,
                   status = %(status)s, 
                   attempt_count = image_asset.attempt_count + %(attempts)s,
                   last_checked_at = %(last_checked_at)s, 
                   updated_at = %(updated_at)s
             where image_asset_id = %(image_asset_id)s
        """, {
            "content_type": content_type,
            "sha256": sha256,
            "error_message": error_message,
            "status": status,
            "image_asset_id": image_asset_id,
            "last_checked_at": current_time,
            "updated_at": current_time,
            "attempts": attempts,
        })
        conn.commit()

        if status == "failed":
            print("\n", "*"*80, "failed", "*"*80, "\n")
            quit()

        print("")
        print("")


def download_image(url):
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")

    if not content_type.startswith("image/"):
        raise ValueError(f"URL did not return an image: {content_type}")

    sha256 = hashlib.sha256(response.content).hexdigest()

    return response.content, content_type, sha256


def resize_image(img, target_width):
    try:
        # img = Image.open(BytesIO(content))

        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")

        aspect_ratio = img.height / img.width
        target_height = int(target_width * aspect_ratio)

        resized_img = img.resize((target_width, target_height), Image.LANCZOS)

        return resized_img

    except IOError as e:
        print(f"IOError processing image: {e}")
    return None


# https://www.w3tutorials.net/blog/resize-image-maintaining-aspect-ratio-and-making-portrait-and-landscape-images-exact-same-size/
def resize_and_crop(img, target_width, target_height=None):
    target_height = target_height or round(target_width * 1.5)

    original_width, original_height = img.size
    original_aspect = original_width / original_height
    target_aspect = target_width / target_height

    # Resize to fit within target, then crop
    if original_aspect > target_aspect:
        # Landscape: resize to target height, crop width
        new_width = int(target_height * original_aspect)
        resized = img.resize((new_width, target_height), Image.Resampling.LANCZOS)
        left = (new_width - target_width) // 2
        cropped = resized.crop((left, 0, left + target_width, target_height))
    else:
        # Portrait or square: resize to target width, crop height
        new_height = int(target_width * (original_height / original_width))
        resized = img.resize((target_width, new_height), Image.Resampling.LANCZOS)
        top = (new_height - target_height) // 2
        cropped = resized.crop((0, top, target_width, top + target_height))

    return cropped


def run_images_download(db=None, count=0, save_download=False):
    db = db or DatabaseConn()

    s3 = boto3.client(
        service_name="s3",
        endpoint_url=os.environ.get("CLOUDFLARE_ENDPOINT"),
        aws_access_key_id=os.environ.get("CLOUDFLARE_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("CLOUDFLARE_SECRET_ACCESS_KEY"),
        region_name="auto",
    )

    results = db.images_to_download()
    rows = results[:count] if count > 0 else results
    loop_through(db, s3, rows, save_download)


###################################################################

if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(description='download images for medias and providers')

    # Add arguments
    parser.add_argument('-c','--count', dest='count', nargs='?', default=0, type=int, help='the number of media/providers to download')
    parser.add_argument("-t","--truncate", dest='truncate', action='store_true', help='truncate the image tables')
    parser.add_argument("-d","--drop", dest='drop', action='store_true', help='drop ALL the tables, reload the data')
    parser.add_argument("-i","--images", dest='images', action='store_true', help='reload image_variant from cloudflare')
    parser.add_argument("-s","--schema", dest='schema', action='store_true', help='run schema.sql')
    parser.add_argument("-v","--view", dest='view', action='store_true', help='create media_full_view')
    parser.add_argument("-r","--run-test", dest='run_test', nargs='?', default=0, type=int, help='run app.etl.ingest --count 10')

    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--no-download", dest='no_download', action='store_true', help='do NOT run the download process')
    group.add_argument("--save-download", dest='save_download', action='store_true', help='save the downloaded images')


    # Parse the arguments
    args = parser.parse_args()

    db = DatabaseConn()

    if args.drop:
        args.schema = True
        args.view = True
        args.images = True

    if args.drop:
        db.drop_tables()

    if args.schema:
        db.create_default_schema()

    if args.view:
        db.create_view()

    if args.truncate:
        db.truncate_image_tables()
        args.run_test = 2
        args.images = True

    if args.run_test and args.run_test > 0:
        from app.etl.ingest import ingest_trending
        ingest_trending(count=args.run_test, force=True)

    if args.images:
        load_image_variant_table_from_cloudflare()

    if args.no_download:
        print("-------------------------------")
        print("No download option is selected.")
        print()
    else: run_images_download(db, count=0, save_download=args.save_download)




