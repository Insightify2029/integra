"""
UI Components
=============
All reusable UI components.
"""

from .cards import ModuleCard, StatCard
from .tables import BaseTable
from .buttons import PrimaryButton, SecondaryButton, DangerButton
from .inputs import TextInput, SearchInput, StyledComboBox
from .labels import TitleLabel, LogoLabel, SubtitleLabel, SectionLabel
from .notifications import (
    ToastManager,
    toast_success,
    toast_error,
    toast_warning,
    toast_info,
    get_toast_manager
)
from .fluent import (
    FluentButton,
    FluentPrimaryButton,
    FluentLineEdit,
    FluentSearchBox,
    FluentComboBox,
    FluentCheckBox,
    FluentProgressBar,
    FluentInfoBar,
    FluentCard,
    FLUENT_AVAILABLE
)

__all__ = [
    # Cards
    'ModuleCard',
    'StatCard',
    # Tables
    'BaseTable',
    # Buttons
    'PrimaryButton',
    'SecondaryButton',
    'DangerButton',
    # Inputs
    'TextInput',
    'SearchInput',
    'StyledComboBox',
    # Labels
    'TitleLabel',
    'LogoLabel',
    'SubtitleLabel',
    'SectionLabel',
    # Notifications
    'ToastManager',
    'toast_success',
    'toast_error',
    'toast_warning',
    'toast_info',
    'get_toast_manager',
    # Fluent Widgets (Windows 11 style)
    'FluentButton',
    'FluentPrimaryButton',
    'FluentLineEdit',
    'FluentSearchBox',
    'FluentComboBox',
    'FluentCheckBox',
    'FluentProgressBar',
    'FluentInfoBar',
    'FluentCard',
    'FLUENT_AVAILABLE'
]
