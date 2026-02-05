"""
Action Preview
==============
Preview widget for AI-suggested actions.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal

from core.logging import app_logger


class ActionStatus(Enum):
    """Status of an action."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"


@dataclass
class PreviewAction:
    """An action to preview."""
    id: str
    type: str  # create, edit, delete, etc.
    title: str
    description: str
    target: str  # What will be affected
    changes: Dict[str, Any] = field(default_factory=dict)
    preview_data: str = ""
    status: ActionStatus = ActionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "target": self.target,
            "changes": self.changes,
            "status": self.status.value,
            "created_at": self.created_at.isoformat()
        }


class ActionPreviewCard(QFrame):
    """Card widget for a single action preview."""

    approved = pyqtSignal(str)  # action_id
    rejected = pyqtSignal(str)  # action_id
    edited = pyqtSignal(str, dict)  # action_id, changes

    def __init__(self, action: PreviewAction, parent=None):
        super().__init__(parent)
        self.action = action
        self._setup_ui()

    def _setup_ui(self):
        """Setup the card UI."""
        self.setStyleSheet("""
            ActionPreviewCard {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()

        # Icon based on action type
        icons = {
            "create": "➕",
            "edit": "✏️",
            "delete": "🗑️",
            "view": "👁️",
            "export": "📤",
            "import": "📥",
            "send": "📧"
        }
        icon = icons.get(self.action.type, "⚡")

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 20px;")

        # Title and type
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        title = QLabel(self.action.title)
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #1f2937;")

        type_labels = {
            "create": ("إنشاء جديد", "#10b981"),
            "edit": ("تعديل", "#f59e0b"),
            "delete": ("حذف", "#ef4444"),
            "view": ("عرض", "#3b82f6"),
            "export": ("تصدير", "#6366f1"),
            "import": ("استيراد", "#8b5cf6"),
            "send": ("إرسال", "#0ea5e9")
        }
        type_text, type_color = type_labels.get(self.action.type, ("إجراء", "#6b7280"))

        type_label = QLabel(type_text)
        type_label.setStyleSheet(f"""
            background-color: {type_color}20;
            color: {type_color};
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 10px;
        """)

        title_layout.addWidget(title)

        header.addWidget(icon_label)
        header.addSpacing(12)
        header.addLayout(title_layout)
        header.addStretch()
        header.addWidget(type_label)

        layout.addLayout(header)

        # Description
        if self.action.description:
            desc = QLabel(self.action.description)
            desc.setWordWrap(True)
            desc.setStyleSheet("color: #6b7280; font-size: 12px;")
            layout.addWidget(desc)

        # Target
        target_label = QLabel(f"الهدف: {self.action.target}")
        target_label.setStyleSheet("color: #9ca3af; font-size: 11px;")
        layout.addWidget(target_label)

        # Preview data
        if self.action.preview_data:
            preview_frame = QFrame()
            preview_frame.setStyleSheet("""
                QFrame {
                    background-color: #f9fafb;
                    border: 1px solid #e5e7eb;
                    border-radius: 8px;
                }
            """)

            preview_layout = QVBoxLayout(preview_frame)
            preview_layout.setContentsMargins(12, 8, 12, 8)

            preview_title = QLabel("معاينة التغييرات:")
            preview_title.setStyleSheet("color: #374151; font-size: 11px; font-weight: bold;")

            preview_text = QTextEdit()
            preview_text.setPlainText(self.action.preview_data)
            preview_text.setReadOnly(True)
            preview_text.setMaximumHeight(100)
            preview_text.setStyleSheet("""
                QTextEdit {
                    border: none;
                    background: transparent;
                    color: #4b5563;
                    font-size: 12px;
                    font-family: monospace;
                }
            """)

            preview_layout.addWidget(preview_title)
            preview_layout.addWidget(preview_text)
            layout.addWidget(preview_frame)

        # Changes summary
        if self.action.changes:
            changes_text = self._format_changes()
            changes_label = QLabel(changes_text)
            changes_label.setWordWrap(True)
            changes_label.setStyleSheet("""
                background-color: #fef3c7;
                color: #92400e;
                padding: 8px 12px;
                border-radius: 8px;
                font-size: 12px;
            """)
            layout.addWidget(changes_label)

        # Action buttons
        buttons = QHBoxLayout()
        buttons.setSpacing(12)

        # Edit button
        edit_btn = QPushButton("تعديل")
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                color: #374151;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
            }
        """)
        edit_btn.clicked.connect(self._on_edit)

        # Reject button
        reject_btn = QPushButton("رفض")
        reject_btn.setStyleSheet("""
            QPushButton {
                background-color: #fee2e2;
                color: #dc2626;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #fecaca;
            }
        """)
        reject_btn.clicked.connect(self._on_reject)

        # Approve button
        approve_btn = QPushButton("موافقة وتنفيذ")
        approve_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        approve_btn.clicked.connect(self._on_approve)

        buttons.addWidget(edit_btn)
        buttons.addStretch()
        buttons.addWidget(reject_btn)
        buttons.addWidget(approve_btn)

        layout.addLayout(buttons)

    def _format_changes(self) -> str:
        """Format changes for display."""
        lines = []
        for key, value in self.action.changes.items():
            if isinstance(value, dict) and "old" in value and "new" in value:
                lines.append(f"• {key}: {value['old']} → {value['new']}")
            else:
                lines.append(f"• {key}: {value}")
        return "\n".join(lines)

    def _on_edit(self):
        """Handle edit button."""
        self.edited.emit(self.action.id, self.action.changes)

    def _on_reject(self):
        """Handle reject button."""
        self.rejected.emit(self.action.id)
        self.hide()

    def _on_approve(self):
        """Handle approve button."""
        self.approved.emit(self.action.id)
        self.hide()


class ActionPreview(QWidget):
    """
    Action Preview Panel.

    Shows pending actions for user approval.

    Usage:
        preview = ActionPreview()
        preview.add_action(action)
        preview.action_approved.connect(handle_approved)
    """

    action_approved = pyqtSignal(object)  # PreviewAction
    action_rejected = pyqtSignal(object)  # PreviewAction
    action_edited = pyqtSignal(object, dict)  # PreviewAction, changes

    def __init__(self, parent=None):
        super().__init__(parent)
        self._actions: Dict[str, PreviewAction] = {}
        self._cards: Dict[str, ActionPreviewCard] = {}
        self._setup_ui()

    def _setup_ui(self):
        """Setup the preview UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #fef3c7;
                border-bottom: 1px solid #fcd34d;
            }
        """)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)

        icon = QLabel("⚡")
        icon.setStyleSheet("font-size: 18px;")

        title = QLabel("إجراءات معلقة")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #92400e;")

        self.count_label = QLabel("0")
        self.count_label.setStyleSheet("""
            background-color: #f59e0b;
            color: white;
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 10px;
        """)

        header_layout.addWidget(icon)
        header_layout.addWidget(title)
        header_layout.addWidget(self.count_label)
        header_layout.addStretch()

        layout.addWidget(header)

        # Scroll area for cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #f9fafb; }")

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(16, 16, 16, 16)
        self.cards_layout.setSpacing(12)
        self.cards_layout.addStretch()

        scroll.setWidget(self.cards_container)
        layout.addWidget(scroll, 1)

        # Empty state
        self.empty_label = QLabel("لا توجد إجراءات معلقة")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("color: #9ca3af; font-size: 13px; padding: 40px;")
        self.cards_layout.insertWidget(0, self.empty_label)

    def add_action(self, action: PreviewAction):
        """Add an action to preview."""
        self._actions[action.id] = action

        card = ActionPreviewCard(action)
        card.approved.connect(lambda id: self._on_approved(id))
        card.rejected.connect(lambda id: self._on_rejected(id))
        card.edited.connect(lambda id, changes: self._on_edited(id, changes))

        self._cards[action.id] = card
        self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

        self._update_count()
        self.empty_label.hide()

    def remove_action(self, action_id: str):
        """Remove an action."""
        if action_id in self._actions:
            del self._actions[action_id]

        if action_id in self._cards:
            card = self._cards.pop(action_id)
            card.deleteLater()

        self._update_count()
        if not self._actions:
            self.empty_label.show()

    def clear(self):
        """Clear all actions."""
        for card in self._cards.values():
            card.deleteLater()

        self._actions.clear()
        self._cards.clear()
        self._update_count()
        self.empty_label.show()

    def _update_count(self):
        """Update the count label."""
        count = len(self._actions)
        self.count_label.setText(str(count))

    def _on_approved(self, action_id: str):
        """Handle action approval."""
        if action_id in self._actions:
            action = self._actions[action_id]
            action.status = ActionStatus.APPROVED
            self.action_approved.emit(action)
            self.remove_action(action_id)

    def _on_rejected(self, action_id: str):
        """Handle action rejection."""
        if action_id in self._actions:
            action = self._actions[action_id]
            action.status = ActionStatus.REJECTED
            self.action_rejected.emit(action)
            self.remove_action(action_id)

    def _on_edited(self, action_id: str, changes: dict):
        """Handle action edit."""
        if action_id in self._actions:
            action = self._actions[action_id]
            self.action_edited.emit(action, changes)
