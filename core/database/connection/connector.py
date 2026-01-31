"""
Database Connector
==================
Creates database connection.
"""

import psycopg2
from .connection_config import get_connection_params


_connection = None


def connect():
    """
    Create database connection.
    Returns connection object or None if failed.
    """
    global _connection
    
    try:
        params = get_connection_params()
        _connection = psycopg2.connect(**params)
        _connection.autocommit = False
        print("✅ Database connected successfully")
        return _connection
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        _connection = None
        return None


def get_connection():
    """Get existing connection or create new one."""
    global _connection
    
    if _connection is None or _connection.closed:
        return connect()
    return _connection
