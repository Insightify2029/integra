"""
Scalar Query Handler
====================
Handles queries that return a single value.
"""

from core.database.connection import get_connection


def get_scalar(query, params=None):
    """
    Execute query and return single scalar value.
    
    Args:
        query: SQL query string
        params: Query parameters (optional)
    
    Returns:
        Single value or None if error/no result
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        result = cursor.fetchone()
        cursor.close()
        
        return result[0] if result else None
    except Exception as e:
        print(f"❌ SCALAR error: {e}")
        return None


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
        query = f"SELECT COUNT(*) FROM {table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"
        
        return get_scalar(query, params) or 0
    except Exception as e:
        print(f"❌ COUNT error: {e}")
        return 0
