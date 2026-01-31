"""
UI Module
=========
User interface components, windows, and dialogs.
"""

from .windows import BaseWindow, LauncherWindow
from .components import (
    ModuleCard, StatCard, BaseTable,
    PrimaryButton, SecondaryButton, DangerButton,
    TextInput, SearchInput, StyledComboBox,
    TitleLabel, LogoLabel, SubtitleLabel, SectionLabel
)
from .dialogs import (
    SettingsDialog, ThemesDialog,
    show_info, show_warning, show_error, show_success, confirm
)

__all__ = [
    # Windows
    'BaseWindow',
    'LauncherWindow',
    # Components
    'ModuleCard',
    'StatCard',
    'BaseTable',
    'PrimaryButton',
    'SecondaryButton',
    'DangerButton',
    'TextInput',
    'SearchInput',
    'StyledComboBox',
    'TitleLabel',
    'LogoLabel',
    'SubtitleLabel',
    'SectionLabel',
    # Dialogs
    'SettingsDialog',
    'ThemesDialog',
    'show_info',
    'show_warning',
    'show_error',
    'show_success',
    'confirm'
]
