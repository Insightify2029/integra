"""
Fluent Widgets
==============
Modern Windows 11 style components using PyQt-Fluent-Widgets.

Usage:
    from ui.components.fluent import (
        FluentButton, FluentPrimaryButton,
        FluentLineEdit, FluentSearchBox,
        FluentComboBox, FluentCheckBox,
        FluentInfoBar
    )

    # Create a modern button
    btn = FluentPrimaryButton("Save", parent=self)
    btn.setIcon(Icons.SAVE)

    # Show info bar notification
    FluentInfoBar.success("Success", "Data saved!", parent=self)
"""

from .widgets import (
    # Buttons
    FluentButton,
    FluentPrimaryButton,
    FluentTransparentButton,
    FluentToolButton,
    # Inputs
    FluentLineEdit,
    FluentSearchBox,
    FluentTextEdit,
    FluentSpinBox,
    # Selection
    FluentComboBox,
    FluentCheckBox,
    FluentRadioButton,
    FluentSwitch,
    # Progress
    FluentProgressBar,
    FluentProgressRing,
    # Notification
    FluentInfoBar,
    # Cards
    FluentCard,
    # Navigation
    FluentPivot,
    # Misc
    FluentBadge,
    FluentToolTip,
    # Availability check
    FLUENT_AVAILABLE
)

__all__ = [
    # Buttons
    'FluentButton',
    'FluentPrimaryButton',
    'FluentTransparentButton',
    'FluentToolButton',
    # Inputs
    'FluentLineEdit',
    'FluentSearchBox',
    'FluentTextEdit',
    'FluentSpinBox',
    # Selection
    'FluentComboBox',
    'FluentCheckBox',
    'FluentRadioButton',
    'FluentSwitch',
    # Progress
    'FluentProgressBar',
    'FluentProgressRing',
    # Notification
    'FluentInfoBar',
    # Cards
    'FluentCard',
    # Navigation
    'FluentPivot',
    # Misc
    'FluentBadge',
    'FluentToolTip',
    # Availability
    'FLUENT_AVAILABLE'
]
