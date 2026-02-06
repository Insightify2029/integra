"""
UPDATE Query Handler
====================
Handles UPDATE queries.
"""

from core.database.connection import get_connection, return_connection
from core.logging import app_logger


def update(query, params=None):
    """
    Execute UPDATE query.

    Args:
        query: SQL query string
        params: Query parameters (optional)

    Returns:
        bool: True if successful, False otherwise
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if conn is None:
            app_logger.error("UPDATE failed: no database connection")
            return False
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return True
    except Exception as e:
        if conn:
            conn.rollback()
        app_logger.error(f"UPDATE error: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        return_connection(conn)


def update_returning_count(query, params=None):
    """
    Execute UPDATE query and return affected rows count.

    Args:
        query: SQL query string
        params: Query parameters (optional)

    Returns:
        int: Number of affected rows or -1 if error
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if conn is None:
            app_logger.error("UPDATE COUNT failed: no database connection")
            return -1
        cursor = conn.cursor()
        cursor.execute(query, params)

        count = cursor.rowcount
        conn.commit()

        return count
    except Exception as e:
        if conn:
            conn.rollback()
        app_logger.error(f"UPDATE COUNT error: {e}")
        return -1
    finally:
        if cursor:
            cursor.close()
        return_connection(conn)
