"""
Database Module
===============
Complete database handling.
"""

from .connection import (
    connect,
    get_connection,
    disconnect,
    is_connected,
    get_connection_status
)

from .queries import (
    select_all,
    select_one,
    insert,
    insert_returning_id,
    update,
    update_returning_count,
    delete,
    delete_returning_count,
    get_scalar,
    get_count,
    execute_query
)

__all__ = [
    # Connection
    'connect',
    'get_connection',
    'disconnect',
    'is_connected',
    'get_connection_status',
    # Queries
    'select_all',
    'select_one',
    'insert',
    'insert_returning_id',
    'update',
    'update_returning_count',
    'delete',
    'delete_returning_count',
    'get_scalar',
    'get_count',
    'execute_query'
]
