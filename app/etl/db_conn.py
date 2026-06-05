import os
from dotenv import load_dotenv
import psycopg

load_dotenv()


class DatabaseConn: 

    def __init__(self, conn=None):
        self.conn = conn
        self.connect()

    def connect(self):
        if not self.conn: 
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                raise RuntimeError("DATABASE_URL is not set. Add it to your .env file.") 
            self.conn = psycopg.connect(database_url)
        return self.conn

    def images_to_download(self):
        sql_file = "./app/scripts/queries/images_to_download.sql"
        desc = "Images to download ran"
        return self.select_from_file(sql_file, desc)

    def create_default_schema(self):
        sql_file = "./app/scripts/schema.sql"
        desc = "Default schema created"
        self._run_script(sql_file, desc)

    def drop_tables(self):
        sql_file = "./app/scripts/drop_tables.sql"
        desc = "Tables dropped"
        self._run_script(sql_file, desc)

    def create_view(self):
        sql_file = "./app/scripts/media_full_view.sql"
        desc = "Media full view created"
        self._run_script(sql_file, desc)

    def truncate_image_tables(self):
        sql_file="./app/scripts/truncate_image_tables.sql"
        desc="Image tables truncated"
        self._run_script(sql_file, desc)

    def _run_script(self, sql_file, desc):
        if not os.path.exists(sql_file):
            raise FileNotFoundError(f"{sql_file} file not found. Please ensure it exists in the current directory.")
        try:
            with self.conn.cursor() as cur:
                with open(sql_file, "r", encoding="utf-8") as file:
                    sql_script = file.read()
                pieces = sql_script.split(";")
                for piece in pieces:
                    if piece.strip():
                        try:
                            cur.execute(piece)
                        except psycopg.Error as e:
                            print(f"Error executing SQL piece: {e}")
                            print(f"Code: {piece}")
                            quit()
                self.conn.commit()
                print(f"{desc} successfully.")
        except psycopg.Error as e:
            print(f"Ignored database error: {e}")
            self.conn.rollback()

    def select_from_file(self, sql_file, desc=None):
        if not os.path.exists(sql_file):
            raise FileNotFoundError(f"{sql_file} file not found. Please ensure it exists in the current directory.")
        try:
            with self.conn.cursor() as cur:
                with open(sql_file, "r", encoding="utf-8") as file:
                    sql_script = file.read()
                    try:
                        cur.execute(sql_script)
                    except psycopg.Error as e:
                        print(f"Error executing SQL piece: {e}")
                        print(f"Code: {sql_script}")
                        quit()
                if cur.description:
                    columns = [desc[0] for desc in cur.description]
                    results = [dict(zip(columns, row)) for row in cur.fetchall()]
                    if desc: print(f"{desc} successfully with {len(results)} rows.")
                    return results
        except psycopg.Error as e:
            print(f"Ignored database error: {e}")
            self.conn.rollback()


    def execute(self, sql="", args=None):
        """Run a SQL query and return the results as a list of dictionaries"""
        if not sql:
            raise ValueError("SQL query is empty. Please provide a valid SQL query.")
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, (args or ()))
                self.conn.commit()
                if cur.description:
                    columns = [desc[0] for desc in cur.description]
                    results = [dict(zip(columns, row)) for row in cur.fetchall()]
                    return results
        except psycopg.Error as e:
            print(f"Database error: {e}")
            self.conn.rollback()
            return []
