"""
Database Connector
==================
Creates database connection using connection pool.

This module provides backward-compatible connection management
while using SQLAlchemy connection pool internally for:
- Thread-safe connections
- Auto-reconnect
- Better performance
"""

# Heavy imports (psycopg2, sqlalchemy) deferred to connect() for faster startup
from .pool import (
    get_pool,
    get_connection_from_pool,
    get_pooled_connection,
    dispose_pool,
    is_pool_initialized,
    get_pool_status,
    check_pool_health
)


# Use pool by default, fallback to single connection if pool fails
USE_POOL = True

# Legacy single connection (fallback)
_connection = None


def connect():
    """
    Initialize database connection.
    Uses connection pool if available, falls back to single connection.
    Returns connection object or None if failed.
    """
    global _connection
    from core.logging import app_logger

    if USE_POOL:
        try:
            pool = get_pool()
            if pool is not None:
                if check_pool_health():
                    app_logger.info("Database connected (using pool)")
                    return True
        except Exception as e:
            app_logger.warning(f"Pool init failed, falling back: {e}")

    # Fallback to single connection
    try:
        import psycopg2
        from .connection_config import get_connection_params
        params = get_connection_params()
        _connection = psycopg2.connect(**params)
        _connection.autocommit = False
        app_logger.info("Database connected (single connection)")
        return True
    except Exception as e:
        app_logger.error(f"Database connection error: {e}")
        _connection = None
        return None


def get_connection():
    """
    Get a database connection.
    Uses pool if available, otherwise returns single connection.

    Note: When using pool, the connection is borrowed and should
    be closed when done (returns to pool, not actually closed).
    """
    global _connection

    if USE_POOL and is_pool_initialized():
        conn = get_connection_from_pool()
        if conn is not None:
            return conn

    # Fallback to single connection
    if _connection is None or _connection.closed:
        connect()
    if _connection is None:
        from core.logging import app_logger
        app_logger.warning("Database connection unavailable")
    return _connection


def return_connection(conn):
    """
    Return a connection after use.

    For pooled connections: closes the proxy (returns to pool).
    For the single fallback connection: does nothing (kept alive for reuse).
    """
    if conn is None:
        return
    # Only close if it's NOT the shared single connection
    if conn is not _connection:
        try:
            conn.close()  # Returns to pool, not actually closed
        except Exception:
            pass


def get_raw_connection():
    """
    Get the raw single connection object (for internal use).
    Use get_connection() for normal operations.
    """
    return _connection


# Export pool utilities for advanced usage
__all__ = [
    'connect',
    'get_connection',
    'return_connection',
    'get_raw_connection',
    'get_pooled_connection',
    'get_pool_status',
    'is_pool_initialized',
    'check_pool_health'
]
