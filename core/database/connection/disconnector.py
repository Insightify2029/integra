"""
Database Disconnector
=====================
Closes database connections and disposes pool.
"""

from core.logging import app_logger


def disconnect():
    """
    Close database connections.
    If using pool, disposes all pooled connections.
    """
    try:
        # Import here to avoid circular imports
        from .pool import dispose_pool, is_pool_initialized
        from .connector import _connection

        # Dispose pool if initialized
        if is_pool_initialized():
            dispose_pool()
            app_logger.info("Database pool disposed")
            print("Database pool disposed")

        # Close single connection if exists
        if _connection is not None and not _connection.closed:
            _connection.close()
            app_logger.info("Database connection closed")
            print("Database connection closed")

        return True

    except Exception as e:
        app_logger.error(f"Error disconnecting: {e}")
        return False
