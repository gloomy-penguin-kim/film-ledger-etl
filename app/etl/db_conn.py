import os
from dotenv import load_dotenv
import psycopg

load_dotenv()


class DatabaseConn: 

    def __init__(self, conn=None):
        self.conn = conn
        self.connect() 
        self._create_default_schema()

    def connect(self):
        if not self.conn: 
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                raise RuntimeError("DATABASE_URL is not set. Add it to your .env file.") 
            self.conn = psycopg.connect(database_url)
        return self.conn  

    def _create_default_schema(self):  
        """Create the raw_json table if it doesn't exist"""
        # Connect to your PostgreSQL database
        if not os.path.exists("./app/etl/schema.sql"):
            raise FileNotFoundError("schema.sql file not found. Please ensure it exists in the current directory.")
        try: 
            with self.conn.cursor() as cur: 
                with open("./app/etl/schema.sql", "r", encoding="utf-8") as file:
                    sql_script = file.read()
                pieces = sql_script.split(";")
                for piece in pieces: 
                    if piece.strip():
                        try:
                            cur.execute(piece)
                        except psycopg.Error as e:
                            print(f"Error executing SQL piece: {e}")
                print("Schema SQL script executed successfully!")
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
                else: cur
        except psycopg.Error as e: 
            print(f"Database error: {e}") 
            self.conn.rollback()  
            return []