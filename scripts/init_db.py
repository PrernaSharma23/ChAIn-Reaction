#!/usr/bin/env python
"""Initialize Postgres database and create tables.

Usage:
  Set DATABASE_URL env var (e.g. postgresql://user:pass@host:port/dbname) then run:
    python scripts/init_db.py

This script will:
 - connect to Postgres server
 - create the target database if it does not exist
 - import and call create_tables() from src.repository.user_repository

"""
import os
import sys
import urllib.parse
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add project root to sys.path so we can import src module
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


def parse_database_url(db_url: str):
    # Use urllib to parse the URL
    parsed = urllib.parse.urlparse(db_url)
    username = parsed.username
    password = parsed.password
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    dbname = parsed.path.lstrip("/")
    return {
        "username": username,
        "password": password,
        "host": host,
        "port": port,
        "dbname": dbname,
    }


def create_database_if_not_exists(db_url: str):
    info = parse_database_url(db_url)
    target_db = info["dbname"]

    # Connect to default 'postgres' database to create the target DB
    admin_conn_str = (
        f"dbname=postgres user={info['username']} password={info['password']} host={info['host']} port={info['port']}"
    )

    print(f"Connecting to Postgres at {info['host']}:{info['port']} to ensure DB '{target_db}' exists...")
    try:
        conn = psycopg2.connect(admin_conn_str)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # Check if database exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (target_db,))
        exists = cur.fetchone()
        if exists:
            print(f"Database '{target_db}' already exists.")
        else:
            print(f"Creating database '{target_db}'...")
            cur.execute(f"CREATE DATABASE \"{target_db}\";")
            print("Database created.")

        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error ensuring database exists: {e}")
        return False


def create_tables(db_url: str):
    # Import here so we use the same DATABASE_URL when SQLAlchemy engine is created
    print("Creating tables via SQLAlchemy create_all()...")
    # Set the env var for the module
    os.environ.setdefault("DATABASE_URL", db_url)
    try:
        from src.repository.user_repository import create_tables as ct

        ct()
        print("Tables created (or already existed).")
        return True
    except Exception as e:
        print(f"Error creating tables: {e}")
        return False


def main():
    user = os.getenv("pg_user", "postgres")
    password = os.getenv("pg_password")
    host = os.getenv("pg_host", "localhost")
    port = os.getenv("pg_port", "5432")
    dbname = os.getenv("pg_database", "ChAIn-Reaction")
    
    db_url =  f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    ok = create_database_if_not_exists(db_url)
    if not ok:
        print("Could not ensure database exists. Exiting.")
        sys.exit(1)

    ok = create_tables(db_url)
    if not ok:
        print("Could not create tables. Exiting.")
        sys.exit(2)

    print("Initialization complete.")


if __name__ == "__main__":
    main()
