import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
POSTGRES_DATABASE = os.getenv("POSTGRES_DATABASE", "explosives_db")

def migrate():
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        dbname=POSTGRES_DATABASE
    )
    cursor = conn.cursor()
    
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT TRUE')
        cursor.execute('ALTER TABLE users ADD COLUMN otp VARCHAR(6)')
        cursor.execute('ALTER TABLE users ADD COLUMN otp_expires_at TIMESTAMP')
        conn.commit()
        print("Migration successful: Added is_verified, otp, and otp_expires_at to users table.")
    except psycopg2.Error as e:
        print(f"Migration error (might already exist): {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
