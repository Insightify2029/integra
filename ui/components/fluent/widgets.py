"""
Fluent Widgets Wrapper
======================
Wrapper around PyQt-Fluent-Widgets for easy integration.
Falls back gracefully if the library is not available.

This module provides Windows 11 style widgets with:
- Modern appearance
- Smooth animations
- Dark/Light theme support
- RTL support

Usage:
    from ui.components.fluent import FluentPrimaryButton, FluentInfoBar

    btn = FluentPrimaryButton("Save")
    FluentInfoBar.success("Done", "Saved successfully!", parent=self)
"""

from typing import Optional
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLineEdit, QTextEdit,
    QComboBox, QCheckBox, QRadioButton, QProgressBar,
    QSpinBox, QToolButton, QLabel, QFrame
)
from PyQt5.QtCore import Qt

try:
    from qfluentwidgets import (
        # Buttons
        PushButton, PrimaryPushButton, TransparentPushButton, ToolButton,
        # Inputs
        LineEdit, SearchLineEdit, TextEdit, SpinBox,
        # Selection
        ComboBox, CheckBox, RadioButton, SwitchButton,
        # Progress
        ProgressBar, ProgressRing,
        # Notification
        InfoBar, InfoBarPosition,
        # Cards
        CardWidget,
        # Navigation
        Pivot,
        # Misc
        ToolTipFilter,
        # Icons
        FluentIcon
    )
    FLUENT_AVAILABLE = True
except ImportError:
    FLUENT_AVAILABLE = False

from core.logging import app_logger
from core.themes import get_current_palette


if not FLUENT_AVAILABLE:
    app_logger.warning("PyQt-Fluent-Widgets not available. Using standard Qt widgets.")


# ============================================================================
# BUTTONS
# ============================================================================

class FluentButton(QPushButton if not FLUENT_AVAILABLE else PushButton):
    """
    Modern styled button.
    Falls back to QPushButton if Fluent is not available.
    """
    pass


class FluentPrimaryButton(QPushButton if not FLUENT_AVAILABLE else PrimaryPushButton):
    """
    Primary action button with accent color.
    Use for main actions like Save, Submit, etc.
    """
    pass


class FluentTransparentButton(QPushButton if not FLUENT_AVAILABLE else TransparentPushButton):
    """
    Transparent button for secondary actions.
    """
    pass


class FluentToolButton(QToolButton if not FLUENT_AVAILABLE else ToolButton):
    """
    Tool button for toolbars.
    """
    pass


# ============================================================================
# INPUTS
# ============================================================================

class FluentLineEdit(QLineEdit if not FLUENT_AVAILABLE else LineEdit):
    """
    Modern text input field.
    """
    pass


class FluentSearchBox(QLineEdit if not FLUENT_AVAILABLE else SearchLineEdit):
    """
    Search input with icon.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        if not FLUENT_AVAILABLE:
            self.setPlaceholderText("Search...")


class FluentTextEdit(QTextEdit if not FLUENT_AVAILABLE else TextEdit):
    """
    Multi-line text editor.
    """
    pass


class FluentSpinBox(QSpinBox if not FLUENT_AVAILABLE else SpinBox):
    """
    Numeric input with up/down buttons.
    """
    pass


# ============================================================================
# SELECTION
# ============================================================================

class FluentComboBox(QComboBox if not FLUENT_AVAILABLE else ComboBox):
    """
    Modern dropdown selection.
    """
    pass


class FluentCheckBox(QCheckBox if not FLUENT_AVAILABLE else CheckBox):
    """
    Modern checkbox.
    """
    pass


class FluentRadioButton(QRadioButton if not FLUENT_AVAILABLE else RadioButton):
    """
    Modern radio button.
    """
    pass


class FluentSwitch(QCheckBox if not FLUENT_AVAILABLE else SwitchButton):
    """
    Toggle switch (on/off).
    Modern alternative to checkbox for binary settings.
    """
    pass


# ============================================================================
# PROGRESS
# ============================================================================

class FluentProgressBar(QProgressBar if not FLUENT_AVAILABLE else ProgressBar):
    """
    Modern progress bar.
    """
    pass


class FluentProgressRing(QProgressBar if not FLUENT_AVAILABLE else ProgressRing):
    """
    Circular progress indicator.
    """
    pass


# ============================================================================
# NOTIFICATION
# ============================================================================

class FluentInfoBar:
    """
    Modern notification bar (similar to Toast but embedded in window).

    Usage:
        FluentInfoBar.success("Title", "Message", parent=self)
        FluentInfoBar.error("Error", "Something went wrong", parent=self)
        FluentInfoBar.warning("Warning", "Please check...", parent=self)
        FluentInfoBar.info("Info", "FYI...", parent=self)
    """

    @staticmethod
    def success(title: str, content: str, parent: QWidget,
                duration: int = 3000, position=None):
        """Show success info bar."""
        if FLUENT_AVAILABLE:
            pos = position or InfoBarPosition.TOP_RIGHT
            InfoBar.success(
                title=title,
                content=content,
                orient=Qt.Horizontal,
                isClosable=True,
                position=pos,
                duration=duration,
                parent=parent
            )
        else:
            app_logger.info(f"InfoBar [SUCCESS]: {title} - {content}")

    @staticmethod
    def error(title: str, content: str, parent: QWidget,
              duration: int = 5000, position=None):
        """Show error info bar."""
        if FLUENT_AVAILABLE:
            pos = position or InfoBarPosition.TOP_RIGHT
            InfoBar.error(
                title=title,
                content=content,
                orient=Qt.Horizontal,
                isClosable=True,
                position=pos,
                duration=duration,
                parent=parent
            )
        else:
            app_logger.error(f"InfoBar [ERROR]: {title} - {content}")

    @staticmethod
    def warning(title: str, content: str, parent: QWidget,
                duration: int = 4000, position=None):
        """Show warning info bar."""
        if FLUENT_AVAILABLE:
            pos = position or InfoBarPosition.TOP_RIGHT
            InfoBar.warning(
                title=title,
                content=content,
                orient=Qt.Horizontal,
                isClosable=True,
                position=pos,
                duration=duration,
                parent=parent
            )
        else:
            app_logger.warning(f"InfoBar [WARNING]: {title} - {content}")

    @staticmethod
    def info(title: str, content: str, parent: QWidget,
             duration: int = 3000, position=None):
        """Show info info bar."""
        if FLUENT_AVAILABLE:
            pos = position or InfoBarPosition.TOP_RIGHT
            InfoBar.info(
                title=title,
                content=content,
                orient=Qt.Horizontal,
                isClosable=True,
                position=pos,
                duration=duration,
                parent=parent
            )
        else:
            app_logger.info(f"InfoBar [INFO]: {title} - {content}")


# ============================================================================
# CARDS
# ============================================================================

class FluentCard(QFrame if not FLUENT_AVAILABLE else CardWidget):
    """
    Modern card container with shadow.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        if not FLUENT_AVAILABLE:
            palette = get_current_palette()
            self.setFrameShape(QFrame.StyledPanel)
            self.setStyleSheet(f"""
                FluentCard {{
                    background: {palette['bg_card']};
                    border-radius: 8px;
                    border: 1px solid {palette['border']};
                }}
            """)


# ============================================================================
# NAVIGATION
# ============================================================================

class FluentPivot(QWidget if not FLUENT_AVAILABLE else Pivot):
    """
    Tab-like navigation component.
    """
    pass


# ============================================================================
# MISC
# ============================================================================

class FluentBadge(QLabel):
    """
    Badge/tag component for showing status or counts.

    Usage:
        badge = FluentBadge("3", color="danger")
        badge = FluentBadge("New", color="success")
    """

    def __init__(self, text: str, color: str = 'primary',
                 parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        palette = get_current_palette()

        # Map color names to palette keys
        _color_map = {
            'primary': (palette['primary'], palette['text_on_primary']),
            'success': (palette['success'], palette['text_on_primary']),
            'danger': (palette['danger'], palette['text_on_primary']),
            'warning': (palette['warning'], '#000000'),
            'info': (palette['info'], palette['text_on_primary']),
        }

        bg, fg = _color_map.get(color, _color_map['primary'])
        self.setStyleSheet(f"""
            FluentBadge {{
                background: {bg};
                color: {fg};
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 12px;
                font-weight: bold;
            }}
        """)
        self.setAlignment(Qt.AlignCenter)


class FluentToolTip:
    """
    Modern tooltip helper.

    Usage:
        FluentToolTip.install(widget, "This is a tooltip")
    """

    @staticmethod
    def install(widget: QWidget, tooltip: str):
        """Install tooltip on widget."""
        if FLUENT_AVAILABLE:
            widget.setToolTip(tooltip)
            widget.installEventFilter(ToolTipFilter(widget))
        else:
            widget.setToolTip(tooltip)
