"""
Dialogs
=======
All application dialogs.
"""

from .settings import SettingsDialog
from .themes import ThemesDialog
from .sync_settings import SyncSettingsDialog
from .message import show_info, show_warning, show_error, show_success, confirm

# Toast notifications (modern, non-blocking)
from ui.components.notifications import (
    toast_success,
    toast_error,
    toast_warning,
    toast_info
)

__all__ = [
    'SettingsDialog',
    'ThemesDialog',
    'SyncSettingsDialog',
    # Modal dialogs (blocking)
    'show_info',
    'show_warning',
    'show_error',
    'show_success',
    'confirm',
    # Toast notifications (non-blocking)
    'toast_success',
    'toast_error',
    'toast_warning',
    'toast_info'
]
