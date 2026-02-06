"""
Scalar Query Handler
====================
Handles queries that return a single value.
"""

import re

from psycopg2 import sql as psycopg2_sql

from core.database.connection import get_connection, return_connection
from core.logging import app_logger


# Pattern to detect potentially dangerous SQL in where clauses
_UNSAFE_WHERE_PATTERN = re.compile(
    r"(;|--|\b(DROP|ALTER|DELETE|INSERT|UPDATE|EXEC|EXECUTE|UNION)\b)",
    re.IGNORECASE
)


def get_scalar(query, params=None):
    """
    Execute query and return single scalar value.

    Args:
        query: SQL query string
        params: Query parameters (optional)

    Returns:
        Single value or None if error/no result
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        if conn is None:
            app_logger.error("SCALAR failed: no database connection")
            return None
        cursor = conn.cursor()
        cursor.execute(query, params)

        result = cursor.fetchone()

        return result[0] if result else None
    except Exception as e:
        app_logger.error(f"SCALAR error: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        return_connection(conn)


def get_count(table_name, where_clause=None, params=None):
    """
    Get count of rows in a table.

    Args:
        table_name: Name of the table
        where_clause: WHERE clause without 'WHERE' keyword (optional)
        params: Query parameters (optional)

    Returns:
        int: Count of rows or 0 if error
    """
    try:
        query = psycopg2_sql.SQL("SELECT COUNT(*) FROM {}").format(
            psycopg2_sql.Identifier(table_name)
        )
        if where_clause:
            # Validate where_clause against dangerous SQL patterns
            if _UNSAFE_WHERE_PATTERN.search(where_clause):
                app_logger.error(f"COUNT rejected: unsafe where_clause detected")
                return 0
            query = query + psycopg2_sql.SQL(" WHERE ") + psycopg2_sql.SQL(where_clause)

        return get_scalar(query, params) or 0
    except Exception as e:
        app_logger.error(f"COUNT error: {e}")
        return 0
