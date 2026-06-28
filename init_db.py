import os
import sqlalchemy
from database import POSTGRES_ROOT_URL, POSTGRES_DATABASE, engine, Base
from models import ExplosiveItem

def init_db():
    # 1. Create database if it doesn't exist
    temp_engine = sqlalchemy.create_engine(POSTGRES_ROOT_URL)
    
    # We need to set isolation_level to 'AUTOCOMMIT' to create a database
    temp_engine = temp_engine.execution_options(isolation_level="AUTOCOMMIT")
    
    conn = temp_engine.connect()
    try:
        # Check if database exists
        result = conn.execute(sqlalchemy.text(f"SELECT 1 FROM pg_database WHERE datname='{POSTGRES_DATABASE}'"))
        if not result.fetchone():
            conn.execute(sqlalchemy.text(f"CREATE DATABASE {POSTGRES_DATABASE}"))
            print(f"Database '{POSTGRES_DATABASE}' created.")
        else:
            print(f"Database '{POSTGRES_DATABASE}' already exists.")
    except Exception as e:
        print(f"Error checking/creating database: {e}")
    finally:
        conn.close()
        temp_engine.dispose()

    # 2. Create tables
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

if __name__ == "__main__":
    init_db()
