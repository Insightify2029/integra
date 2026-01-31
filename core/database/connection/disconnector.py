"""
Database Disconnector
=====================
Closes database connection.
"""

from .connector import _connection, get_connection


def disconnect():
    """Close database connection."""
    global _connection
    
    conn = get_connection()
    if conn and not conn.closed:
        conn.close()
        print("Database connection closed")
        return True
    return False
