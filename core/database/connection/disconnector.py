"""
Database Disconnector
=====================
Closes database connection.
"""

from .connector import get_connection


def disconnect():
    """Close database connection."""
    conn = get_connection()
    if conn and not conn.closed:
        conn.close()
        print("Database connection closed")
        return True
    return False
