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

import psycopg2
from .connection_config import get_connection_params
from .pool import (
    get_pool,
    get_connection_from_pool,
    get_pooled_connection,
    dispose_pool,
    is_pool_initialized,
    get_pool_status,
    check_pool_health
)
from core.logging import app_logger


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

    if USE_POOL:
        try:
            pool = get_pool()
            if pool is not None:
                # Test the pool with a quick connection
                if check_pool_health():
                    app_logger.info("Database connected (using pool)")
                    print("✅ Database connected successfully (pool)")
                    return True
        except Exception as e:
            app_logger.warning(f"Pool init failed, falling back: {e}")

    # Fallback to single connection
    try:
        params = get_connection_params()
        _connection = psycopg2.connect(**params)
        _connection.autocommit = False
        app_logger.info("Database connected (single connection)")
        print("✅ Database connected successfully")
        return _connection
    except Exception as e:
        app_logger.error(f"Database connection error: {e}")
        print(f"❌ Database connection error: {e}")
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
    return _connection


# Export pool utilities for advanced usage
__all__ = [
    'connect',
    'get_connection',
    'get_pooled_connection',
    'get_pool_status',
    'is_pool_initialized',
    'check_pool_health'
]
