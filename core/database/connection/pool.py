# -*- coding: utf-8 -*-
"""
Database Connection Pool
========================
Thread-safe connection pool for background workers.

Uses psycopg2.pool.ThreadedConnectionPool for safe concurrent access.

Usage:
    from core.database.connection import get_pool_connection, release_connection

    # In a worker thread
    conn = get_pool_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM employees")
            rows = cur.fetchall()
        conn.commit()
    finally:
        release_connection(conn)

    # Or use context manager
    with pooled_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM employees")
"""

from typing import Optional
from contextlib import contextmanager
import threading

import psycopg2
from psycopg2 import pool

from .connection_config import get_connection_params


class ConnectionPool:
    """
    Thread-safe database connection pool.

    Singleton pattern ensures one pool per application.
    """

    _instance: Optional["ConnectionPool"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                # Double-check locking
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._pool: Optional[pool.ThreadedConnectionPool] = None
        self._min_conn = 2
        self._max_conn = 10
        self._initialized = True

    def initialize(self, min_conn: int = 2, max_conn: int = 10) -> bool:
        """
        Initialize the connection pool.

        Args:
            min_conn: Minimum connections to keep open
            max_conn: Maximum connections allowed

        Returns:
            True if successful, False otherwise
        """
        if self._pool is not None:
            return True

        try:
            params = get_connection_params()
            self._pool = pool.ThreadedConnectionPool(
                minconn=min_conn,
                maxconn=max_conn,
                **params
            )
            self._min_conn = min_conn
            self._max_conn = max_conn
            return True
        except Exception as e:
            print(f"Connection pool initialization error: {e}")
            return False

    def get_connection(self):
        """
        Get a connection from the pool.

        Returns:
            A database connection

        Raises:
            RuntimeError: If pool not initialized
            psycopg2.pool.PoolError: If no connections available
        """
        if self._pool is None:
            if not self.initialize():
                raise RuntimeError("Connection pool not initialized")

        return self._pool.getconn()

    def release_connection(self, conn):
        """
        Return a connection to the pool.

        Args:
            conn: The connection to release
        """
        if self._pool is not None and conn is not None:
            try:
                # Reset connection state before returning to pool
                if not conn.closed:
                    conn.rollback()
                self._pool.putconn(conn)
            except Exception:
                # If release fails, try to close the connection
                try:
                    conn.close()
                except Exception:
                    pass

    def close_all(self):
        """Close all connections in the pool."""
        if self._pool is not None:
            self._pool.closeall()
            self._pool = None

    @property
    def is_initialized(self) -> bool:
        """Check if pool is initialized."""
        return self._pool is not None

    @property
    def min_connections(self) -> int:
        """Minimum connections in pool."""
        return self._min_conn

    @property
    def max_connections(self) -> int:
        """Maximum connections in pool."""
        return self._max_conn


# Module-level convenience functions

def get_pool() -> ConnectionPool:
    """Get the global connection pool instance."""
    return ConnectionPool()


def get_pool_connection():
    """
    Get a connection from the pool.

    Remember to release it with release_connection() when done.
    """
    return get_pool().get_connection()


def release_connection(conn):
    """Release a connection back to the pool."""
    get_pool().release_connection(conn)


def close_pool():
    """Close all pooled connections."""
    get_pool().close_all()


@contextmanager
def pooled_connection():
    """
    Context manager for pooled connections.

    Usage:
        with pooled_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM table")

    Automatically releases connection and handles rollback on error.
    """
    conn = get_pool_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        release_connection(conn)


def execute_in_pool(query: str, params: tuple = None, fetch: bool = True):
    """
    Execute a query using a pooled connection.

    Args:
        query: SQL query to execute
        params: Query parameters
        fetch: Whether to fetch results

    Returns:
        Query results if fetch=True, otherwise row count
    """
    with pooled_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            if fetch:
                return cur.fetchall()
            return cur.rowcount
