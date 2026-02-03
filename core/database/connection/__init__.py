"""
Database Connection Module
==========================
Handles database connectivity.

Components:
  - Single connection: connect(), get_connection(), disconnect()
  - Connection pool: get_pool_connection(), pooled_connection()
"""

from .connector import connect, get_connection
from .disconnector import disconnect
from .connection_checker import is_connected, get_connection_status
from .connection_config import get_connection_string, get_connection_params
from .pool import (
    get_pool,
    get_pool_connection,
    release_connection,
    close_pool,
    pooled_connection,
    execute_in_pool,
)

__all__ = [
    # Single connection
    'connect',
    'get_connection',
    'disconnect',
    'is_connected',
    'get_connection_status',
    'get_connection_string',
    'get_connection_params',
    # Connection pool (thread-safe)
    'get_pool',
    'get_pool_connection',
    'release_connection',
    'close_pool',
    'pooled_connection',
    'execute_in_pool',
]
