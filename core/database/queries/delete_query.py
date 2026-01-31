"""
DELETE Query Handler
====================
Handles DELETE queries.
"""

from core.database.connection import get_connection


def delete(query, params=None):
    """
    Execute DELETE query.
    
    Args:
        query: SQL query string
        params: Query parameters (optional)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        conn.rollback()
        print(f"❌ DELETE error: {e}")
        return False


def delete_returning_count(query, params=None):
    """
    Execute DELETE query and return deleted rows count.
    
    Args:
        query: SQL query string
        params: Query parameters (optional)
    
    Returns:
        int: Number of deleted rows or -1 if error
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        count = cursor.rowcount
        conn.commit()
        cursor.close()
        
        return count
    except Exception as e:
        conn.rollback()
        print(f"❌ DELETE COUNT error: {e}")
        return -1
