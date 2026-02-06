"""
DELETE Query Handler
====================
Handles DELETE queries.
"""

from core.database.connection import get_connection
from core.logging import app_logger


def delete(query, params=None):
    """
    Execute DELETE query.

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
            app_logger.error("DELETE failed: no database connection")
            return False
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return True
    except Exception as e:
        if conn:
            conn.rollback()
        app_logger.error(f"DELETE error: {e}")
        return False
    finally:
        if cursor:
            cursor.close()


def delete_returning_count(query, params=None):
    """
    Execute DELETE query and return deleted rows count.

    Args:
        query: SQL query string
        params: Query parameters (optional)

    Returns:
        int: Number of deleted rows or -1 if error
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if conn is None:
            app_logger.error("DELETE COUNT failed: no database connection")
            return -1
        cursor = conn.cursor()
        cursor.execute(query, params)

        count = cursor.rowcount
        conn.commit()

        return count
    except Exception as e:
        if conn:
            conn.rollback()
        app_logger.error(f"DELETE COUNT error: {e}")
        return -1
    finally:
        if cursor:
            cursor.close()
