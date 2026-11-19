"""
database.py
-----------
Tiny wrapper around psycopg2 so the rest of the pipeline never imports
psycopg2 directly. Connection settings match the docker-compose.yml
shipped with Task 1 (same Postgres container is reused for Task 3/4).
"""

import psycopg2
import psycopg2.extras
import os

DB_CONFIG = {
    "dbname": os.environ.get("PGDATABASE", "mydatabase"),
    "user": os.environ.get("PGUSER", "admin"),
    "password": os.environ.get("PGPASSWORD", "secret"),
    "host": os.environ.get("PGHOST", "localhost"),
    "port": int(os.environ.get("PGPORT", 5432)),
}


def get_connection():
    """Open a fresh connection. Caller is responsible for closing it."""
    return psycopg2.connect(**DB_CONFIG)


def run_query(sql: str):
    """
    Execute a read-only SQL query and return (rows, column_names).
    Raises the underlying psycopg2 exception on failure -- callers
    (executor.py) decide how to handle/retry it.
    """
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql)
        rows = cur.fetchall()
        col_names = [d[0] for d in cur.description] if cur.description else []
        cur.close()
        return [dict(r) for r in rows], col_names
    finally:
        conn.close()
