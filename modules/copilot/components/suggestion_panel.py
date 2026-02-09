"""
Suggestion Panel
================
Panel for displaying AI suggestions and tips.
"""

from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

from core.logging import app_logger
from core.themes import get_current_palette


class SuggestionType(Enum):
    """Types of suggestions."""
    TIP = "tip"
    ACTION = "action"
    WARNING = "warning"
    INFO = "info"
    SHORTCUT = "shortcut"


@dataclass
class Suggestion:
    """A suggestion from the AI."""
    id: str
    type: SuggestionType
    title: str
    description: str
    action_label: Optional[str] = None
    action_data: Dict[str, Any] = field(default_factory=dict)
    dismissible: bool = True
    priority: int = 0  # Higher = more important
    created_at: datetime = field(default_factory=datetime.now)


class SuggestionCard(QFrame):
    """Card widget for a single suggestion."""

    action_clicked = pyqtSignal(dict)
    dismissed = pyqtSignal(str)

    def __init__(self, suggestion: Suggestion, parent=None):
        super().__init__(parent)
        self.suggestion = suggestion
        self._setup_ui()

    def _setup_ui(self):
        """Setup the card UI."""
        p = get_current_palette()
        # Colors based on type
        colors = {
            SuggestionType.TIP: (f"{p['info']}20", p['info'], "💡"),
            SuggestionType.ACTION: (f"{p['success']}20", p['success'], "⚡"),
            SuggestionType.WARNING: (f"{p['warning']}20", p['warning'], "⚠️"),
            SuggestionType.INFO: (f"{p['accent']}20", p['accent'], "ℹ️"),
            SuggestionType.SHORTCUT: (f"{p['primary']}20", p['primary'], "⌨️"),
        }

        bg_color, text_color, icon = colors.get(
            self.suggestion.type,
            (p['bg_hover'], p['text_primary'], "💬")
        )

        self.setStyleSheet(f"""
            SuggestionCard {{
                background-color: {bg_color};
                border-radius: 12px;
                border: none;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 20px;")
        icon_label.setAlignment(Qt.AlignTop)

        # Content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)

        title = QLabel(self.suggestion.title)
        title.setStyleSheet(f"color: {text_color}; font-size: 13px; font-weight: bold;")

        desc = QLabel(self.suggestion.description)
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {text_color}; font-size: 12px;")

        content_layout.addWidget(title)
        content_layout.addWidget(desc)

        # Action button
        if self.suggestion.action_label:
            action_btn = QPushButton(self.suggestion.action_label)
            action_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {text_color};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    opacity: 0.9;
                }}
            """)
            action_btn.clicked.connect(
                lambda: self.action_clicked.emit(self.suggestion.action_data)
            )
            content_layout.addWidget(action_btn, alignment=Qt.AlignLeft)

        # Dismiss button
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(4)

        if self.suggestion.dismissible:
            dismiss_btn = QPushButton("✕")
            dismiss_btn.setFixedSize(24, 24)
            dismiss_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {text_color};
                    border: none;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: rgba(0,0,0,0.1);
                    border-radius: 12px;
                }}
            """)
            dismiss_btn.clicked.connect(
                lambda: self.dismissed.emit(self.suggestion.id)
            )
            actions_layout.addWidget(dismiss_btn)

        actions_layout.addStretch()

        layout.addWidget(icon_label)
        layout.addLayout(content_layout, 1)
        layout.addLayout(actions_layout)


class SuggestionPanel(QWidget):
    """
    Panel for displaying AI suggestions.

    Features:
    - Multiple suggestion types
    - Priority ordering
    - Dismissible suggestions
    - Action triggers

    Usage:
        panel = SuggestionPanel()
        panel.add_suggestion(suggestion)
    """

    suggestion_actioned = pyqtSignal(dict)
    suggestion_dismissed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._suggestions: Dict[str, Suggestion] = {}
        self._cards: Dict[str, SuggestionCard] = {}
        self._max_visible = 5
        self._setup_ui()

    def _setup_ui(self):
        """Setup the panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header (optional, hidden by default)
        self.header = QFrame()
        self.header.setStyleSheet("""
            QFrame {
                background-color: transparent;
            }
        """)
        self.header.hide()

        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(0, 0, 0, 8)

        p = get_current_palette()
        title = QLabel("💡 اقتراحات")
        title.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {p['text_primary']};")

        clear_btn = QPushButton("مسح الكل")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {p['text_muted']};
                border: none;
                font-size: 11px;
            }}
            QPushButton:hover {{
                color: {p['text_primary']};
            }}
        """)
        clear_btn.clicked.connect(self.clear)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(clear_btn)

        layout.addWidget(self.header)

        # Cards container
        self.cards_layout = QVBoxLayout()
        self.cards_layout.setSpacing(8)
        layout.addLayout(self.cards_layout)

        # Empty state
        self.empty_label = QLabel("")
        self.empty_label.hide()
        layout.addWidget(self.empty_label)

        layout.addStretch()

    def add_suggestion(self, suggestion: Suggestion):
        """Add a suggestion."""
        self._suggestions[suggestion.id] = suggestion

        card = SuggestionCard(suggestion)
        card.action_clicked.connect(self._on_action)
        card.dismissed.connect(self._on_dismissed)

        self._cards[suggestion.id] = card

        # Insert by priority
        self._reorder_cards()
        self._update_visibility()

    def remove_suggestion(self, suggestion_id: str):
        """Remove a suggestion."""
        if suggestion_id in self._suggestions:
            del self._suggestions[suggestion_id]

        if suggestion_id in self._cards:
            card = self._cards.pop(suggestion_id)
            self.cards_layout.removeWidget(card)
            card.deleteLater()

        self._update_visibility()

    def clear(self):
        """Clear all suggestions."""
        for card in self._cards.values():
            card.deleteLater()

        self._suggestions.clear()
        self._cards.clear()
        self._update_visibility()

    def _reorder_cards(self):
        """Reorder cards by priority."""
        # Remove all cards
        for card in self._cards.values():
            self.cards_layout.removeWidget(card)

        # Sort by priority (descending)
        sorted_ids = sorted(
            self._suggestions.keys(),
            key=lambda id: self._suggestions[id].priority,
            reverse=True
        )

        # Re-add in order
        for suggestion_id in sorted_ids[:self._max_visible]:
            card = self._cards[suggestion_id]
            self.cards_layout.addWidget(card)

    def _update_visibility(self):
        """Update visibility based on suggestion count."""
        has_suggestions = bool(self._suggestions)
        self.header.setVisible(has_suggestions and len(self._suggestions) > 1)

        if has_suggestions:
            self.empty_label.hide()
        else:
            self.empty_label.show()

    def _on_action(self, action_data: dict):
        """Handle suggestion action."""
        self.suggestion_actioned.emit(action_data)

    def _on_dismissed(self, suggestion_id: str):
        """Handle suggestion dismissal."""
        self.suggestion_dismissed.emit(suggestion_id)
        self.remove_suggestion(suggestion_id)

    def show_tip(self, title: str, description: str, action_label: str = None, action_data: dict = None):
        """Show a tip suggestion."""
        import uuid
        suggestion = Suggestion(
            id=str(uuid.uuid4()),
            type=SuggestionType.TIP,
            title=title,
            description=description,
            action_label=action_label,
            action_data=action_data or {}
        )
        self.add_suggestion(suggestion)

    def show_warning(self, title: str, description: str):
        """Show a warning suggestion."""
        import uuid
        suggestion = Suggestion(
            id=str(uuid.uuid4()),
            type=SuggestionType.WARNING,
            title=title,
            description=description,
            priority=10  # Higher priority for warnings
        )
        self.add_suggestion(suggestion)
