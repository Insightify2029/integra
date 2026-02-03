# -*- coding: utf-8 -*-
"""
Backup Module
=============
Advanced database backup system with GFS retention.

Components:
  - BackupManager: Backup creation and restoration
  - RetentionPolicy: GFS (Grandfather-Father-Son) retention
"""

from .backup_manager import (
    BackupManager,
    get_backup_manager,
    BackupInfo,
    BackupType,
)
from .retention_policy import (
    RetentionPolicy,
    GFSPolicy,
)

__all__ = [
    "BackupManager",
    "get_backup_manager",
    "BackupInfo",
    "BackupType",
    "RetentionPolicy",
    "GFSPolicy",
]
