"""
SELECT Query Handler
====================
Handles SELECT queries.
"""

from core.database.connection import get_connection
from core.logging import app_logger


def select_all(query, params=None):
    """
    Execute SELECT query and return all results.

    Args:
        query: SQL query string
        params: Query parameters (optional)

    Returns:
        tuple: (columns, rows) or ([], []) if error
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if conn is None:
            app_logger.error("SELECT failed: no database connection")
            return [], []
        cursor = conn.cursor()
        cursor.execute(query, params)

        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        return columns, rows
    except Exception as e:
        app_logger.error(f"SELECT error: {e}")
        return [], []
    finally:
        if cursor:
            cursor.close()


def select_one(query, params=None):
    """
    Execute SELECT query and return one result.

    Args:
        query: SQL query string
        params: Query parameters (optional)

    Returns:
        tuple or None
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if conn is None:
            app_logger.error("SELECT ONE failed: no database connection")
            return None
        cursor = conn.cursor()
        cursor.execute(query, params)

        result = cursor.fetchone()

        return result
    except Exception as e:
        app_logger.error(f"SELECT ONE error: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
