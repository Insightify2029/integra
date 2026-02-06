"""
Database Connection Module
==========================
Handles database connectivity with connection pool support.
"""

from .connector import connect, get_connection, return_connection
from .disconnector import disconnect
from .connection_checker import is_connected, get_connection_status
from .connection_config import get_connection_string, get_connection_params
from .pool import (
    get_pooled_connection,
    get_pool_status,
    is_pool_initialized,
    check_pool_health
)

__all__ = [
    # Connection management
    'connect',
    'get_connection',
    'return_connection',
    'disconnect',
    'is_connected',
    'get_connection_status',
    'get_connection_string',
    'get_connection_params',
    # Pool utilities
    'get_pooled_connection',
    'get_pool_status',
    'is_pool_initialized',
    'check_pool_health'
]
