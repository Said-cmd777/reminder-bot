"""
Database adapter - provides unified interface for SQLite and PostgreSQL.
"""

import os
import logging
from typing import Any, Optional, List
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Import database-specific modules
import sqlite3

try:
    import psycopg2
    import psycopg2.extras
    from psycopg2 import pool
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logger.warning("psycopg2 not available - PostgreSQL support disabled")

from db_config import DB_TYPE, get_connection_info


# Connection pool for PostgreSQL
_pg_pool = None


class Row:
    """
    Row wrapper that provides dict-like access to database rows.
    Makes PostgreSQL rows behave like SQLite Row objects.
    """
    def __init__(self, data: dict):
        self._data = data
    
    def __getitem__(self, key):
        if isinstance(key, int):
            # Access by index
            return list(self._data.values())[key]
        return self._data[key]
    
    def __contains__(self, key):
        return key in self._data
    
    def keys(self):
        return self._data.keys()
    
    def values(self):
        return self._data.values()
    
    def items(self):
        return self._data.items()
    
    def __iter__(self):
        return iter(self._data.values())
    
    def __len__(self):
        return len(self._data)
    
    def __repr__(self):
        return f"Row({self._data})"


class DatabaseAdapter:
    """
    Unified database interface for SQLite and PostgreSQL.
    """
    
    def __init__(self, db_type: str, connection_info: dict):
        self.db_type = db_type
        self.connection_info = connection_info
        
        if db_type == "postgresql":
            if not PSYCOPG2_AVAILABLE:
                raise RuntimeError("PostgreSQL selected but psycopg2 is not installed")
            self._init_pg_pool()
    
    def _init_pg_pool(self):
        """Initialize PostgreSQL connection pool."""
        global _pg_pool
        if _pg_pool is None:
            try:
                _pg_pool = psycopg2.pool.SimpleConnectionPool(
                    minconn=1,
                    maxconn=10,
                    dsn=self.connection_info["url"]
                )
                logger.info("✅ PostgreSQL connection pool initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize PostgreSQL pool: {e}")
                raise
    
    def get_connection(self):
        """
        Get a database connection.
        
        Returns:
            Connection object (sqlite3.Connection or psycopg2 connection)
        """
        if self.db_type == "sqlite":
            conn = sqlite3.connect(
                self.connection_info["path"],
                check_same_thread=False,
                timeout=30
            )
            conn.row_factory = sqlite3.Row
            try:
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("PRAGMA synchronous=NORMAL;")
            except Exception:
                pass
            return conn
        
        elif self.db_type == "postgresql":
            try:
                conn = _pg_pool.getconn()
                # Enable autocommit by default (matches SQLite behavior)
                conn.autocommit = False
                return conn
            except Exception as e:
                logger.error(f"❌ Failed to get PostgreSQL connection: {e}")
                raise
    
    def release_connection(self, conn):
        """Release a database connection back to the pool (PostgreSQL only)."""
        if self.db_type == "postgresql" and conn:
            try:
                _pg_pool.putconn(conn)
            except Exception as e:
                logger.error(f"Error releasing connection: {e}")
    
    def execute_query(self, conn, query: str, params: tuple = (), fetch: str = "none"):
        """
        Execute a query with unified interface.
        
        Args:
            conn: Database connection
            query: SQL query
            params: Query parameters
            fetch: "none", "one", "all"
        
        Returns:
            Query results or None
        """
        if self.db_type == "sqlite":
            cur = conn.cursor()
            cur.execute(query, params)
            
            if fetch == "one":
                return cur.fetchone()
            elif fetch == "all":
                return cur.fetchall()
            else:
                return None
        
        elif self.db_type == "postgresql":
            # Use RealDictCursor for dict-like access
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(query, params)
            
            if fetch == "one":
                result = cur.fetchone()
                return Row(dict(result)) if result else None
            elif fetch == "all":
                results = cur.fetchall()
                return [Row(dict(r)) for r in results]
            else:
                return None
    
    def get_lastrowid(self, conn, cursor=None) -> Optional[int]:
        """
        Get the last inserted row ID.
        
        For PostgreSQL, you need to use RETURNING id in your INSERT statement.
        """
        if self.db_type == "sqlite":
            return cursor.lastrowid if cursor else None
        elif self.db_type == "postgresql":
            # For PostgreSQL, lastrowid should be retrieved using RETURNING clause
            return None


# Singleton adapter instance
_adapter = None


def get_adapter() -> DatabaseAdapter:
    """Get the global database adapter instance."""
    global _adapter
    if _adapter is None:
        conn_info = get_connection_info()
        _adapter = DatabaseAdapter(DB_TYPE, conn_info)
    return _adapter


def get_conn(db_path: Optional[str] = None):
    """
    Get a database connection using the adapter.
    
    Args:
        db_path: For SQLite, override the default path (optional)
    
    Returns:
        Database connection
    """
    adapter = get_adapter()
    
    # For SQLite, allow path override
    if adapter.db_type == "sqlite" and db_path:
        # Create a temporary adapter with custom path
        temp_adapter = DatabaseAdapter("sqlite", {"type": "sqlite", "path": db_path})
        return temp_adapter.get_connection()
    
    return adapter.get_connection()


def close_conn(conn):
    """
    Close a database connection properly.
    
    For SQLite: closes the connection
    For PostgreSQL: returns connection to pool
    """
    adapter = get_adapter()
    
    if adapter.db_type == "sqlite":
        if conn:
            conn.close()
    elif adapter.db_type == "postgresql":
        adapter.release_connection(conn)
