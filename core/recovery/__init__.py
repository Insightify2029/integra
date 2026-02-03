# -*- coding: utf-8 -*-
"""
Recovery Module
===============
Auto-save and crash recovery system.

Components:
  - AutoSave: Periodic auto-save of unsaved data
  - RecoveryManager: Crash recovery and data restoration
"""

from .auto_save import (
    AutoSave,
    get_auto_save,
    save_draft,
    get_draft,
    clear_drafts,
)
from .recovery_manager import (
    RecoveryManager,
    get_recovery_manager,
    RecoveryData,
)

__all__ = [
    # Auto-save
    "AutoSave",
    "get_auto_save",
    "save_draft",
    "get_draft",
    "clear_drafts",
    # Recovery
    "RecoveryManager",
    "get_recovery_manager",
    "RecoveryData",
]
