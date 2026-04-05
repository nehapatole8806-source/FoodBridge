"""
config/database.py
------------------
Handles PostgreSQL connection using psycopg2.
Provides a get_db() helper to obtain a connection,
and a close_db() to release it after each request.
"""

import psycopg2
import psycopg2.extras
from flask import g
import os


def get_db():
    """
    Get a database connection from Flask's application context (g).
    """
    if 'db' not in g:
        # 1. Define the connection string clearly
        # Using sslmode=require is often necessary for Supabase
        conn_string = "postgresql://postgres.druyctwsweemwvawpvpp:Sl2WEfhlxF8k5m8K@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"
        
        try:
            # 2. Use the 'dsn' parameter explicitly
            g.db = psycopg2.connect(
                dsn=conn_string,
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            g.db.autocommit = False
        except Exception as e:
            # This will print the EXACT error to your terminal
            print("\n--- DATABASE CONNECTION ERROR ---")
            print(e)
            print("---------------------------------\n")
            raise e
            
    return g.db


def close_db(e=None):
    """
    Close the database connection at end of request.
    Registered with app.teardown_appcontext in app.py.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False, commit=False):
    """
    Utility: Execute a query and return results.
    - one=True  → return a single row dict (or None)
    - one=False → return a list of row dicts
    - commit=True → commit the transaction (for INSERT/UPDATE/DELETE)
    """
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(query, args)
        if commit:
            conn.commit()
            return cur.rowcount  # Number of affected rows
        results = cur.fetchall()
        return (results[0] if results else None) if one else results
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()


def insert_db(query, args=()):
    """
    Utility: Execute an INSERT query and return the new row.
    Uses RETURNING * to fetch inserted record.
    """
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(query, args)
        result = cur.fetchone()
        conn.commit()
        return result
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
