# db_utils.py
"""Database utility functions and context managers."""

from contextlib import contextmanager
from typing import Iterator, Optional, List, Tuple, Any
import sqlite3
import logging
from db import get_conn

logger = logging.getLogger(__name__)


@contextmanager
def db_connection(auto_commit: bool = True) -> Iterator[sqlite3.Connection]:
    """
    Context manager for database connections.
    
    Args:
        auto_commit: If True, automatically commit on success and rollback on error
    
    Usage:
        with db_connection() as conn:
            conn.execute("INSERT ...")
            # Committed automatically
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
        conn.close()


@contextmanager
def db_transaction(conn: Optional[sqlite3.Connection] = None):
    """
    Context manager for atomic transactions.
    
    Args:
        conn: Existing connection or None to create new one
    
    Usage:
        with db_transaction() as conn:
            conn.execute("INSERT ...")
            conn.execute("UPDATE ...")
            # All-or-nothing
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
            conn.close()


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
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(query, params)
        return cur.fetchone() if fetch_one else cur.fetchall()


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