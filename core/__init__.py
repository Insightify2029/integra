# -*- coding: utf-8 -*-
"""
INTEGRA Core Module
===================
Infrastructure layer containing all core systems.

Components:
  - database: Database connectivity and queries
  - config: Application configuration
  - themes: UI theming system
  - logging: Structured logging (app + audit)
  - error_handling: Global exception handler
  - sync: Git + Database sync system
  - threading: Background task management (A5)
  - validation: Pydantic data validation (A10)
  - security: RBAC and authentication (A9)
  - recovery: Auto-save and crash recovery (A3)
  - scheduler: APScheduler integration (A6)
  - backup: Advanced backup system (A8)
  - file_watcher: Hot folder monitoring (A7)
"""

from . import database
from . import config
from . import themes
from . import logging
from . import error_handling
from . import sync
from . import threading
from . import validation
from . import security
from . import recovery
from . import scheduler
from . import backup
from . import file_watcher

__all__ = [
    'database',
    'config',
    'themes',
    'logging',
    'error_handling',
    'sync',
    'threading',
    'validation',
    'security',
    'recovery',
    'scheduler',
    'backup',
    'file_watcher',
]
