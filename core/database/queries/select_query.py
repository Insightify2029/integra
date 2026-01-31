"""
SELECT Query Handler
====================
Handles SELECT queries.
"""

from core.database.connection import get_connection


def select_all(query, params=None):
    """
    Execute SELECT query and return all results.
    
    Args:
        query: SQL query string
        params: Query parameters (optional)
    
    Returns:
        tuple: (columns, rows) or ([], []) if error
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        
        return columns, rows
    except Exception as e:
        print(f"❌ SELECT error: {e}")
        return [], []


def select_one(query, params=None):
    """
    Execute SELECT query and return one result.
    
    Args:
        query: SQL query string
        params: Query parameters (optional)
    
    Returns:
        tuple or None
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        result = cursor.fetchone()
        cursor.close()
        
        return result
    except Exception as e:
        print(f"❌ SELECT ONE error: {e}")
        return None
