import boto3
import os
from dotenv import load_dotenv

from app.etl.db_conn import DatabaseConn

load_dotenv()

def load_image_variant_table_from_cloudflare():

    db = DatabaseConn()

    s3 = boto3.client(
        service_name="s3",
        endpoint_url=os.environ.get("CLOUDFLARE_ENDPOINT"),
        aws_access_key_id=os.environ.get("CLOUDFLARE_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("CLOUDFLARE_SECRET_ACCESS_KEY"),
        region_name="auto",
    )

    BUCKET = os.environ.get("CLOUDFLARE_BUCKET")

    # Get all filenames
    filenames = []
    continuation_token = None

    while True:
        kwargs = {"Bucket": BUCKET, "MaxKeys": 1000}
        if continuation_token:
            kwargs["ContinuationToken"] = continuation_token

        response = s3.list_objects_v2(**kwargs)
        for obj in response.get("Contents", []):
            filenames.append(obj["Key"])

        if response.get("IsTruncated"):
            continuation_token = response["NextContinuationToken"]
        else:
            break

    path_arr = []
    for name in filenames:
        splits = name.split("/")
        path_arr.append("/".join(splits[:len(splits)-1]))

    with db.conn.cursor() as cur:
        cur.execute(f"""
            select path_str 
            from variant 
            where active = true 
            order by path_str 
        """)
        columns = [desc[0] for desc in cur.description]
        paths = [dict(zip(columns, row)) for row in cur.fetchall()]

        for path_str in path_arr:
            variant_name = path_str.replace("/","_")
            path_id = [x["path_str"] for x in paths if x["path_str"] == path_str]
            if len(path_id) == 0:
                with db.conn.cursor() as curr:
                    curr.execute("""
                        insert into variant (variant_name, path_str) values (%s, %s)
                            on conflict (path_str) do nothing 
                            returning variant_id 
                    """, (variant_name, path_str))
                db.conn.commit()

    with db.conn.cursor() as cur:
        cur.execute(f"""
            select variant_id, variant_name, path_str
            from variant 
            order by path_str 
        """)
        columns = [desc[0] for desc in cur.description]
        paths = [dict(zip(columns, row)) for row in cur.fetchall()]

        for object_key in filenames:
            filename = os.path.basename(object_key)
            image_asset_id = os.path.splitext(filename)[0]

            try:
                image_asset_id = int(image_asset_id)

                dirname = os.path.dirname(object_key)
                extension = os.path.splitext(object_key)[1]
                variant_id = [x["variant_id"] for x in paths if x["path_str"] == dirname]

                if len(variant_id) == 0:
                    print("filename", filename)
                    print("object_key", object_key)
                    print("dirname", dirname)
                    print("paths", paths)
                    print("*"*80)
                    print("")
                    print("")
                    continue
                else:
                    variant_id = variant_id[0]

                public_domain = os.environ.get("CLOUDFLARE_ENDPOINT")
                if object_key and public_domain:
                    public_url = f"https://{public_domain}/{object_key}"
                else:
                    print ("object_key", object_key)
                    print ("public_domain", public_domain)
                    raise Exception(f"Public Domain, {public_domain} or Object key, {object_key}, missing.")

                db.conn.execute("""
                    insert into image_variant (image_asset_id, variant_id, storage_bucket, storage_provider,
                                               object_key, public_url, content_type, status, error_message,
                                               last_checked_at, created_at, updated_at)
                        values (%(image_asset_id)s, %(variant_id)s, %(storage_bucket)s, %(storage_provider)s,
                                %(object_key)s, %(public_url)s, %(content_type)s, %(status)s, %(error_message)s,
                               now(), now(), now())
                        on conflict (image_asset_id, variant_id, storage_bucket, storage_provider)
                        do update
                            set variant_id = coalesce(image_variant.variant_id, %(variant_id)s),
                                status = %(status)s,
                                last_checked_at = now(),
                                updated_at = now()
                        returning variant_id, image_variant_id
                    """,
                    {
                        "image_asset_id": image_asset_id,
                        "variant_id": variant_id,
                        "storage_bucket": os.environ.get("CLOUDFLARE_BUCKET"),
                        "storage_provider": os.environ.get("CLOUDFLARE_PROVIDER"),
                        "object_key": object_key,
                        "public_url": public_url,
                        "content_type": "image/webp" if extension == "webp" else None,
                        "status": "cached",
                        "error_message": None
                    })
                db.conn.commit()
            except Exception as e:
                print(str(e))
                print("filename", filename)
                print("object_key", object_key)
                print("dirname", dirname)
                print("paths", paths)
                print("*"*80)
                print("")
                print("")


