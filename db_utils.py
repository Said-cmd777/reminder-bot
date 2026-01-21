
"""Database utility functions and context managers."""

from contextlib import contextmanager
from typing import Iterator, Optional, List, Tuple, Any
import sqlite3
import logging
from db import get_conn
from db_adapter import close_conn
from db_config import DB_TYPE

logger = logging.getLogger(__name__)


@contextmanager
def db_connection(auto_commit: bool = True) -> Iterator:
    """
    Context manager for database connections.
    
    Args:
        auto_commit: If True, automatically commit on success and rollback on error
    
    Usage:
        with db_connection() as conn:
            conn.execute("INSERT ...")
            
    """
    conn = get_conn()
    try:
        yield conn
        if auto_commit:
            conn.commit()
    except Exception:
        if auto_commit:
            conn.rollback()
        raise
    finally:
        close_conn(conn)


@contextmanager
def db_transaction(conn=None):
    """
    Context manager for atomic transactions.
    
    Args:
        conn: Existing connection or None to create new one
    
    Usage:
        with db_transaction() as conn:
            conn.execute("INSERT ...")
            conn.execute("UPDATE ...")
            
    """
    own_conn = conn is None
    if own_conn:
        conn = get_conn()
    
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        if own_conn:
            close_conn(conn)


def safe_get(row, key: str, default=None, warn: bool = False):
    """
    Safely get a value from a sqlite3.Row or dict.
    
    Args:
        row: sqlite3.Row or dict-like object
        key: Key to retrieve
        default: Default value if key not found
        warn: If True, log warning when key is missing
        
    Returns:
        Value from row or default
    """
    try:
        return row[key]
    except (KeyError, TypeError, IndexError):
        if warn:
            logger.warning(f"Key '{key}' not found in row, using default: {default}")
        try:
            return dict(row).get(key, default)
        except (TypeError, AttributeError):
            return default


def execute_query(query: str, params: tuple = (), fetch_one: bool = False):
    """Execute query and return results."""
    with db_connection() as conn:
        if DB_TYPE == "sqlite":
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(query, params)
        else:
            # PostgreSQL
            import psycopg2.extras
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(query, params)
        
        if fetch_one:
            result = cur.fetchone()
            if DB_TYPE == "postgresql" and result:
                from db_adapter import Row
                return Row(dict(result))
            return result
        else:
            results = cur.fetchall()
            if DB_TYPE == "postgresql":
                from db_adapter import Row
                return [Row(dict(r)) for r in results]
            return results


def get_single_value(query: str, params: tuple = (), default=None):
    """Get single value from query (useful for COUNT, MAX, etc.)."""
    with db_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        row = cur.fetchone()
        if row is None:
            return default
        try:
            return row[0]
        except (IndexError, TypeError):
            return default