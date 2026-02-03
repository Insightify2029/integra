"""
Database Connection Pool
========================
SQLAlchemy-based connection pool for thread-safe database access.

Features:
- Thread-safe connection management
- Auto-reconnect on connection failure
- Connection health checks (pre-ping)
- Configurable pool size and overflow

Usage:
    from core.database.connection.pool import get_pool, get_pooled_connection

    # Get connection from pool
    with get_pooled_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM employees")
        rows = cursor.fetchall()
    # Connection automatically returned to pool
"""

from contextlib import contextmanager
from urllib.parse import quote_plus
from sqlalchemy import create_engine, event, text
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import DisconnectionError
from core.logging import app_logger
from .connection_config import get_connection_params


# Pool configuration
POOL_SIZE = 5           # Number of permanent connections
MAX_OVERFLOW = 10       # Extra connections when pool is full
POOL_TIMEOUT = 30       # Seconds to wait for connection
POOL_RECYCLE = 1800     # Recycle connections every 30 minutes
POOL_PRE_PING = True    # Check connection health before use


_engine = None
_pool_initialized = False


def _create_engine():
    """Create SQLAlchemy engine with connection pool."""
    global _engine, _pool_initialized

    if _engine is not None:
        return _engine

    try:
        # Get connection params and URL-encode password for special characters
        params = get_connection_params()
        encoded_password = quote_plus(str(params['password']))

        connection_string = (
            f"postgresql://{params['user']}:{encoded_password}"
            f"@{params['host']}:{params['port']}/{params['database']}"
        )

        _engine = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=POOL_SIZE,
            max_overflow=MAX_OVERFLOW,
            pool_timeout=POOL_TIMEOUT,
            pool_recycle=POOL_RECYCLE,
            pool_pre_ping=POOL_PRE_PING,
            echo=False,  # Set to True for SQL debugging
        )

        # Event listener for connection checkout
        @event.listens_for(_engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Called when connection is retrieved from pool."""
            pass  # Can add logging here if needed

        # Event listener for connection invalidation
        @event.listens_for(_engine, "invalidate")
        def receive_invalidate(dbapi_connection, connection_record, exception):
            """Called when connection is invalidated."""
            app_logger.warning(f"Connection invalidated: {exception}")

        _pool_initialized = True
        app_logger.info(
            f"Connection pool initialized (size={POOL_SIZE}, "
            f"max_overflow={MAX_OVERFLOW})"
        )
        return _engine

    except Exception as e:
        app_logger.error(f"Failed to create connection pool: {e}")
        _engine = None
        _pool_initialized = False
        return None


def get_pool():
    """Get the connection pool (SQLAlchemy engine)."""
    return _create_engine()


def get_pool_status():
    """
    Get pool statistics.

    Returns:
        dict: Pool status information
    """
    if _engine is None:
        return {
            "initialized": False,
            "pool_size": 0,
            "checked_out": 0,
            "overflow": 0,
            "checked_in": 0
        }

    pool = _engine.pool
    return {
        "initialized": True,
        "pool_size": pool.size(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "checked_in": pool.checkedin(),
        "max_overflow": MAX_OVERFLOW,
        "pool_timeout": POOL_TIMEOUT
    }


@contextmanager
def get_pooled_connection():
    """
    Get a connection from the pool with automatic return.

    Usage:
        with get_pooled_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            result = cursor.fetchall()

    Yields:
        psycopg2 connection object
    """
    engine = get_pool()
    if engine is None:
        raise ConnectionError("Connection pool not initialized")

    connection = None
    try:
        # Get raw DBAPI connection
        connection = engine.raw_connection()
        yield connection
    except Exception as e:
        if connection is not None:
            try:
                connection.rollback()
            except Exception:
                pass
        raise
    finally:
        if connection is not None:
            try:
                connection.close()  # Returns to pool, doesn't actually close
            except Exception:
                pass


def get_connection_from_pool():
    """
    Get a connection from the pool (without context manager).
    IMPORTANT: Caller must close the connection when done!

    Returns:
        psycopg2 connection object or None
    """
    engine = get_pool()
    if engine is None:
        return None

    try:
        return engine.raw_connection()
    except Exception as e:
        app_logger.error(f"Failed to get connection from pool: {e}")
        return None


def dispose_pool():
    """Dispose all connections in the pool."""
    global _engine, _pool_initialized

    if _engine is not None:
        try:
            _engine.dispose()
            app_logger.info("Connection pool disposed")
        except Exception as e:
            app_logger.error(f"Error disposing pool: {e}")
        finally:
            _engine = None
            _pool_initialized = False


def is_pool_initialized():
    """Check if pool is initialized."""
    return _pool_initialized and _engine is not None


def check_pool_health():
    """
    Check if pool is healthy by testing a connection.

    Returns:
        bool: True if healthy, False otherwise
    """
    try:
        with get_pooled_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
        return True
    except Exception as e:
        app_logger.error(f"Pool health check failed: {e}")
        return False
