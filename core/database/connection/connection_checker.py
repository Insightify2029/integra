"""
Connection Checker
==================
Checks database connection status.
"""

from .connector import get_connection


def is_connected():
    """
    Check if database is connected.
    Returns True if connected, False otherwise.
    """
    try:
        conn = get_connection()
        if conn and not conn.closed:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        return False
    except:
        return False


def get_connection_status():
    """
    Get connection status as string.
    Returns: 'connected' or 'disconnected'
    """
    return "connected" if is_connected() else "disconnected"
