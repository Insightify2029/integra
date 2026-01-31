"""
INSERT Query Handler
====================
Handles INSERT queries.
"""

from core.database.connection import get_connection


def insert(query, params=None):
    """
    Execute INSERT query.
    
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
        print(f"❌ INSERT error: {e}")
        return False


def insert_returning_id(query, params=None):
    """
    Execute INSERT query and return the new ID.
    
    Args:
        query: SQL query string (must include RETURNING id)
        params: Query parameters (optional)
    
    Returns:
        int: New record ID or None if error
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        new_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        
        return new_id
    except Exception as e:
        conn.rollback()
        print(f"❌ INSERT RETURNING error: {e}")
        return None
