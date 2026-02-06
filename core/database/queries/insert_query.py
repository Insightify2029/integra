"""
INSERT Query Handler
====================
Handles INSERT queries.
"""

from core.database.connection import get_connection, return_connection
from core.logging import app_logger


def insert(query, params=None):
    """
    Execute INSERT query.

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
            app_logger.error("INSERT failed: no database connection")
            return False
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return True
    except Exception as e:
        if conn:
            conn.rollback()
        app_logger.error(f"INSERT error: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        return_connection(conn)


def insert_returning_id(query, params=None):
    """
    Execute INSERT query and return the new ID.

    Args:
        query: SQL query string (must include RETURNING id)
        params: Query parameters (optional)

    Returns:
        int: New record ID or None if error
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if conn is None:
            app_logger.error("INSERT RETURNING failed: no database connection")
            return None
        cursor = conn.cursor()
        cursor.execute(query, params)

        result = cursor.fetchone()
        if result is None:
            app_logger.error("INSERT RETURNING returned no rows")
            return None
        new_id = result[0]
        conn.commit()

        return new_id
    except Exception as e:
        if conn:
            conn.rollback()
        app_logger.error(f"INSERT RETURNING error: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        return_connection(conn)
