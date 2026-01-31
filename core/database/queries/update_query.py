"""
UPDATE Query Handler
====================
Handles UPDATE queries.
"""

from core.database.connection import get_connection


def update(query, params=None):
    """
    Execute UPDATE query.
    
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
        print(f"❌ UPDATE error: {e}")
        return False


def update_returning_count(query, params=None):
    """
    Execute UPDATE query and return affected rows count.
    
    Args:
        query: SQL query string
        params: Query parameters (optional)
    
    Returns:
        int: Number of affected rows or -1 if error
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
        print(f"❌ UPDATE COUNT error: {e}")
        return -1
