"""
Configuration Module
====================
All application configurations.
"""

from .app import APP_NAME, APP_VERSION, APP_SUBTITLE, APP_AUTHOR
from .database import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from .window import WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT
from .modules import get_all_modules, get_enabled_modules, get_module_by_id

__all__ = [
    # App
    'APP_NAME',
    'APP_VERSION', 
    'APP_SUBTITLE',
    'APP_AUTHOR',
    # Database
    'DB_HOST',
    'DB_PORT',
    'DB_NAME',
    'DB_USER',
    'DB_PASSWORD',
    # Window
    'WINDOW_MIN_WIDTH',
    'WINDOW_MIN_HEIGHT',
    # Modules
    'get_all_modules',
    'get_enabled_modules',
    'get_module_by_id'
]
