"""
Database Queries Module
=======================
Handles all database query operations.
"""

from .select_query import select_all, select_one
from .insert_query import insert, insert_returning_id
from .update_query import update, update_returning_count
from .delete_query import delete, delete_returning_count
from .scalar_query import get_scalar, get_count

__all__ = [
    'select_all',
    'select_one',
    'insert',
    'insert_returning_id',
    'update',
    'update_returning_count',
    'delete',
    'delete_returning_count',
    'get_scalar',
    'get_count'
]
