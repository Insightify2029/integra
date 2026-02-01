"""
Dialogs
=======
All application dialogs.
"""

from .settings import SettingsDialog
from .themes import ThemesDialog
from .sync_settings import SyncSettingsDialog
from .message import show_info, show_warning, show_error, show_success, confirm

__all__ = [
    'SettingsDialog',
    'ThemesDialog',
    'SyncSettingsDialog',
    'show_info',
    'show_warning',
    'show_error',
    'show_success',
    'confirm'
]
