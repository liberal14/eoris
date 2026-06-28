"""
Migration: Add feature_vector column to explosives table
=========================================================
Run ONCE before starting the app for the first time after the upgrade:

    python add_feature_vector_column.py

It is safe to run multiple times – it checks first whether the column exists.
"""

import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

HOST     = os.getenv("POSTGRES_HOST",     "localhost")
PORT     = os.getenv("POSTGRES_PORT",     "5432")
USER     = os.getenv("POSTGRES_USER",     "postgres")
PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
DBNAME   = os.getenv("POSTGRES_DATABASE","explosives_db")

def column_exists(cursor, table, column):
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s
    """, (table, column))
    return cursor.fetchone()[0] > 0

def main():
    print(f"Connecting to {DBNAME} on {HOST}:{PORT} ...")
    conn = psycopg2.connect(
        host=HOST, port=PORT, user=USER, password=PASSWORD, dbname=DBNAME
    )
    conn.autocommit = True
    cur = conn.cursor()

    if column_exists(cur, "explosives", "feature_vector"):
        print("Column 'feature_vector' already exists. Nothing to do.")
    else:
        print("Adding column 'feature_vector' (JSON) to table 'explosives' ...")
        cur.execute("ALTER TABLE explosives ADD COLUMN feature_vector JSON;")
        print("Done! Column added successfully.")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
