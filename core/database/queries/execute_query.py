"""
Execute Query Handler
=====================
Handles raw DDL/DML queries (CREATE, DROP, ALTER, etc.).
"""

from core.database.connection import get_connection, return_connection
from core.logging import app_logger


def execute_query(query, params=None):
    """
    Execute a raw SQL query (DDL/DML).

    Used for schema operations like CREATE, DROP, ALTER, etc.

    Args:
        query: SQL query string (can be psycopg2.sql.Composed)
        params: Query parameters (optional)

    Returns:
        bool: True if successful, False otherwise
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if conn is None:
            app_logger.error("EXECUTE failed: no database connection")
            return False
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return True
    except Exception as e:
        if conn:
            conn.rollback()
        app_logger.error(f"EXECUTE error: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        return_connection(conn)
