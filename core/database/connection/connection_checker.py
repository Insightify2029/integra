"""
Connection Checker
==================
Checks database connection status.
"""

from .pool import is_pool_initialized, check_pool_health, get_pool_status


def is_connected():
    """
    Check if database is connected.
    Returns True if connected, False otherwise.
    """
    # Check pool health if initialized
    if is_pool_initialized():
        return check_pool_health()

    # Fallback: check single connection
    try:
        from .connector import _connection
        if _connection and not _connection.closed:
            cursor = _connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        return False
    except Exception:
        return False


def get_connection_status():
    """
    Get detailed connection status.

    Returns:
        dict: Connection status information
    """
    if is_pool_initialized():
        pool_status = get_pool_status()
        return {
            "connected": check_pool_health(),
            "mode": "pool",
            "pool_size": pool_status.get("pool_size", 0),
            "checked_out": pool_status.get("checked_out", 0),
            "checked_in": pool_status.get("checked_in", 0)
        }

    connected = is_connected()
    return {
        "connected": connected,
        "mode": "single",
        "pool_size": 0,
        "checked_out": 0,
        "checked_in": 0
    }


def get_connection_status_string():
    """
    Get connection status as simple string.
    Returns: 'connected' or 'disconnected'
    """
    return "connected" if is_connected() else "disconnected"
