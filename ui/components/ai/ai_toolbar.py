"""
AI Toolbar
==========
Quick action toolbar for AI features.
"""

from typing import Optional, Callable, List
from dataclasses import dataclass

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel,
    QFrame, QMenu, QAction, QToolButton
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon

from core.ai import is_ollama_available, get_ai_service
from core.logging import app_logger
from core.themes import get_current_palette

try:
    from core.utils import Icons, icon
    HAS_ICONS = True
except ImportError:
    HAS_ICONS = False
    Icons = None


@dataclass
class AIAction:
    """Represents an AI action."""
    id: str
    text: str
    tooltip: str
    icon_name: Optional[str] = None
    shortcut: Optional[str] = None


# Pre-defined AI actions
AI_ACTIONS = [
    AIAction("summarize", "لخّص", "تلخيص البيانات المعروضة", "fa5s.compress-alt"),
    AIAction("analyze", "حلّل", "تحليل ذكي للبيانات", "fa5s.chart-bar"),
    AIAction("suggest", "اقترح", "اقتراحات للتحسين", "fa5s.lightbulb"),
    AIAction("ask", "اسأل", "طرح سؤال على الذكاء الاصطناعي", "fa5s.comment-dots"),
]


class AIToolbar(QFrame):
    """
    AI Actions Toolbar.

    Features:
    - Quick AI actions
    - Status indicator
    - Customizable actions

    Usage:
        toolbar = AIToolbar(parent)
        toolbar.action_triggered.connect(on_ai_action)
    """

    action_triggered = pyqtSignal(str)  # Emits action ID
    chat_requested = pyqtSignal()  # Request to open chat panel

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        actions: Optional[List[AIAction]] = None,
        show_status: bool = True,
        compact: bool = False
    ):
        super().__init__(parent)
        self._actions = actions or AI_ACTIONS
        self._show_status = show_status
        self._compact = compact
        self._setup_ui()

    def _setup_ui(self):
        """Setup toolbar UI."""
        self._palette = get_current_palette()
        self.setStyleSheet(f"""
            AIToolbar {{
                background-color: {self._palette['bg_card']};
                border: 1px solid {self._palette['border']};
                border-radius: 8px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        # AI Icon
        ai_icon = QLabel("🤖")
        ai_icon.setStyleSheet("font-size: 16px;")
        layout.addWidget(ai_icon)

        # Status indicator
        if self._show_status:
            self.status_dot = QLabel("●")
            self._update_status()
            layout.addWidget(self.status_dot)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet(f"background-color: {self._palette['border_light']};")
        layout.addWidget(sep)

        # Action buttons
        for action in self._actions:
            btn = self._create_action_button(action)
            layout.addWidget(btn)

        # Chat button
        chat_btn = QPushButton("💬 محادثة")
        chat_btn.setStyleSheet(self._get_button_style(primary=True))
        chat_btn.setToolTip("فتح نافذة المحادثة مع الذكاء الاصطناعي")
        chat_btn.clicked.connect(self.chat_requested.emit)
        layout.addWidget(chat_btn)

        layout.addStretch()

    def _create_action_button(self, action: AIAction) -> QPushButton:
        """Create a button for an action."""
        if self._compact:
            text = ""
            btn = QToolButton()
        else:
            text = action.text
            btn = QPushButton(text)

        btn.setToolTip(action.tooltip)
        btn.setStyleSheet(self._get_button_style())

        # Set icon if available
        if HAS_ICONS and action.icon_name and Icons:
            try:
                btn.setIcon(icon(action.icon_name, color='#0066cc'))
            except Exception:
                pass

        btn.clicked.connect(lambda: self._on_action_clicked(action.id))

        return btn

    def _get_button_style(self, primary: bool = False) -> str:
        """Get button stylesheet (theme-aware)."""
        p = getattr(self, '_palette', get_current_palette())
        if primary:
            return f"""
                QPushButton {{
                    background-color: {p['primary']};
                    color: {p['text_on_primary']};
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: {p['primary_hover']};
                }}
                QPushButton:disabled {{
                    background-color: {p['disabled_bg']};
                    color: {p['disabled_text']};
                }}
            """
        else:
            return f"""
                QPushButton, QToolButton {{
                    background-color: transparent;
                    border: 1px solid {p['border_light']};
                    border-radius: 4px;
                    padding: 6px 10px;
                    font-size: 12px;
                    color: {p['info']};
                }}
                QPushButton:hover, QToolButton:hover {{
                    background-color: {p['bg_hover']};
                }}
                QPushButton:disabled, QToolButton:disabled {{
                    color: {p['disabled_text']};
                    border-color: {p['border']};
                }}
            """

    def _update_status(self):
        """Update status indicator."""
        if not hasattr(self, 'status_dot'):
            return

        p = getattr(self, '_palette', get_current_palette())
        if is_ollama_available():
            self.status_dot.setStyleSheet(f"color: {p['success']}; font-size: 10px;")
            self.status_dot.setToolTip("الذكاء الاصطناعي متاح")
        else:
            self.status_dot.setStyleSheet(f"color: {p['danger']}; font-size: 10px;")
            self.status_dot.setToolTip("الذكاء الاصطناعي غير متاح")

    def _on_action_clicked(self, action_id: str):
        """Handle action button click."""
        if not is_ollama_available():
            app_logger.warning("AI not available for action: " + action_id)
            return

        self.action_triggered.emit(action_id)

    def refresh_status(self):
        """Refresh AI availability status."""
        self._update_status()

    def set_actions_enabled(self, enabled: bool):
        """Enable or disable all action buttons."""
        for child in self.findChildren(QPushButton):
            child.setEnabled(enabled)


class AIStatusWidget(QWidget):
    """
    Small AI status widget.

    Shows AI availability with a simple indicator.
    """

    clicked = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Setup UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        self.icon_label = QLabel("🤖")
        self.icon_label.setStyleSheet("font-size: 14px;")

        self.status_label = QLabel()
        self._update_status()

        layout.addWidget(self.icon_label)
        layout.addWidget(self.status_label)

        self.setCursor(Qt.PointingHandCursor)

    def _update_status(self):
        """Update status display."""
        p = get_current_palette()
        if is_ollama_available():
            self.status_label.setText("AI")
            self.status_label.setStyleSheet(f"""
                color: {p['success']};
                font-size: 11px;
                font-weight: bold;
            """)
            self.setToolTip("الذكاء الاصطناعي متاح - انقر للمحادثة")
        else:
            self.status_label.setText("AI")
            self.status_label.setStyleSheet(f"""
                color: {p['text_muted']};
                font-size: 11px;
            """)
            self.setToolTip("الذكاء الاصطناعي غير متاح")

    def mousePressEvent(self, event):
        """Handle click."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def refresh(self):
        """Refresh status."""
        self._update_status()


def create_ai_toolbar(
    parent: Optional[QWidget] = None,
    compact: bool = False
) -> AIToolbar:
    """Create and return an AI toolbar."""
    return AIToolbar(parent, compact=compact)
