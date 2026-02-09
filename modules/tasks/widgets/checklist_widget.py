"""
INTEGRA - Checklist Widget
ويدجت قائمة التحقق (المهام الفرعية)
المحور H

التاريخ: 4 فبراير 2026
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLabel, QLineEdit, QPushButton, QCheckBox,
    QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from typing import List, Optional

from ..models import ChecklistItem
from ..repository import (
    add_checklist_item, toggle_checklist_item,
    delete_checklist_item, get_task_repository
)
from core.themes import get_current_palette, get_font, FONT_SIZE_BODY, FONT_SIZE_SMALL, FONT_WEIGHT_BOLD


class ChecklistItemWidget(QFrame):
    """
    عنصر قائمة التحقق

    يعرض عنصر واحد مع إمكانية تبديل الحالة والحذف.
    """

    toggled = pyqtSignal(int, bool)  # item_id, is_completed
    deleted = pyqtSignal(int)  # item_id

    def __init__(self, item: ChecklistItem, parent=None):
        super().__init__(parent)
        self.item = item
        self._setup_ui()

    def _setup_ui(self):
        """إعداد واجهة المستخدم"""
        p = get_current_palette()
        self.setObjectName("checklistItem")
        self.setFixedHeight(40)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.item.is_completed)
        self.checkbox.stateChanged.connect(self._on_toggled)
        layout.addWidget(self.checkbox)

        # Title
        self.title_label = QLabel(self.item.title)
        self.title_label.setFont(get_font(FONT_SIZE_BODY))
        if self.item.is_completed:
            self.title_label.setStyleSheet(
                f"color: {p['text_muted']}; text-decoration: line-through;"
            )
        layout.addWidget(self.title_label, 1)

        # Delete button
        self.delete_btn = QPushButton("×")
        self.delete_btn.setFixedSize(24, 24)
        self.delete_btn.clicked.connect(lambda: self.deleted.emit(self.item.id))
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {p['danger']};
                border: none;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {p['danger']}20;
                border-radius: 4px;
            }}
        """)
        self.delete_btn.hide()
        layout.addWidget(self.delete_btn)

        # Style
        self.setStyleSheet(f"""
            QFrame#checklistItem {{
                background-color: {p['bg_card']};
                border: 1px solid {p['border']};
                border-radius: 6px;
            }}
            QFrame#checklistItem:hover {{
                border-color: {p['border_light']};
            }}
        """)

    def _on_toggled(self, state):
        """عند تبديل الحالة"""
        is_completed = state == Qt.Checked
        self.toggled.emit(self.item.id, is_completed)

        # Update style
        p = get_current_palette()
        if is_completed:
            self.title_label.setStyleSheet(
                f"color: {p['text_muted']}; text-decoration: line-through;"
            )
        else:
            self.title_label.setStyleSheet("")

    def enterEvent(self, event):
        self.delete_btn.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.delete_btn.hide()
        super().leaveEvent(event)


class ChecklistWidget(QFrame):
    """
    ويدجت قائمة التحقق الكامل

    يعرض كل عناصر قائمة التحقق مع إمكانية الإضافة والتعديل.
    """

    item_toggled = pyqtSignal(int, bool)  # item_id, is_completed
    item_added = pyqtSignal(str)  # title
    item_deleted = pyqtSignal(int)  # item_id
    progress_changed = pyqtSignal(int, int)  # completed, total

    def __init__(self, task_id: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.task_id = task_id
        self.items: List[ChecklistItem] = []
        self._setup_ui()

    def _setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setObjectName("checklistWidget")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header
        header = QHBoxLayout()
        header.setSpacing(8)

        p = get_current_palette()
        title = QLabel("✓ قائمة التحقق")
        title.setFont(get_font(FONT_SIZE_BODY, FONT_WEIGHT_BOLD))
        header.addWidget(title)

        header.addStretch()

        self.progress_label = QLabel("0/0")
        self.progress_label.setFont(get_font(FONT_SIZE_BODY))
        self.progress_label.setStyleSheet(f"color: {p['text_muted']};")
        header.addWidget(self.progress_label)

        layout.addLayout(header)

        # Items container
        self.items_container = QWidget()
        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(6)
        self.items_layout.setAlignment(Qt.AlignTop)

        layout.addWidget(self.items_container)

        # Add item input
        add_layout = QHBoxLayout()
        add_layout.setSpacing(8)

        self.add_input = QLineEdit()
        self.add_input.setPlaceholderText("➕ أضف عنصر جديد...")
        self.add_input.setFixedHeight(36)
        self.add_input.returnPressed.connect(self._add_item)
        self.add_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {p['border']};
                border-radius: 6px;
                padding: 0 12px;
                font-size: 12px;
                background-color: {p['bg_input']};
            }}
            QLineEdit:focus {{
                border-color: {p['border_focus']};
                background-color: {p['bg_card']};
            }}
        """)
        add_layout.addWidget(self.add_input, 1)

        self.add_btn = QPushButton("+")
        self.add_btn.setFixedSize(36, 36)
        self.add_btn.clicked.connect(self._add_item)
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {p['success']};
                color: {p['text_on_primary']};
                border: none;
                border-radius: 6px;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {p['success']}dd;
            }}
        """)
        add_layout.addWidget(self.add_btn)

        layout.addLayout(add_layout)

    def set_items(self, items: List[ChecklistItem]):
        """تعيين العناصر"""
        self.items = items
        self._render_items()

    def _render_items(self):
        """عرض العناصر"""
        # Clear existing items
        while self.items_layout.count() > 0:
            item = self.items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add item widgets
        for item in self.items:
            widget = ChecklistItemWidget(item)
            widget.toggled.connect(self._on_item_toggled)
            widget.deleted.connect(self._on_item_deleted)
            self.items_layout.addWidget(widget)

        self._update_progress()

    def _add_item(self):
        """إضافة عنصر جديد"""
        title = self.add_input.text().strip()
        if not title:
            return

        if self.task_id:
            # Save to database
            item_id = add_checklist_item(self.task_id, title, len(self.items))
            if item_id:
                new_item = ChecklistItem(
                    id=item_id,
                    task_id=self.task_id,
                    title=title,
                    sort_order=len(self.items)
                )
                self.items.append(new_item)
                self._render_items()
        else:
            # Just add locally (for new task form)
            new_item = ChecklistItem(
                title=title,
                sort_order=len(self.items)
            )
            self.items.append(new_item)
            self._render_items()

        self.add_input.clear()
        self.item_added.emit(title)

    def _on_item_toggled(self, item_id: int, is_completed: bool):
        """عند تبديل حالة عنصر"""
        if self.task_id and item_id:
            toggle_checklist_item(item_id)

        # Update local state
        for item in self.items:
            if item.id == item_id:
                item.is_completed = is_completed
                break

        self._update_progress()
        self.item_toggled.emit(item_id, is_completed)

    def _on_item_deleted(self, item_id: int):
        """عند حذف عنصر"""
        if self.task_id and item_id:
            delete_checklist_item(item_id)

        # Remove from local list
        self.items = [i for i in self.items if i.id != item_id]
        self._render_items()
        self.item_deleted.emit(item_id)

    def _update_progress(self):
        """تحديث شريط التقدم"""
        total = len(self.items)
        completed = sum(1 for i in self.items if i.is_completed)
        self.progress_label.setText(f"{completed}/{total}")
        self.progress_changed.emit(completed, total)

    def get_items(self) -> List[ChecklistItem]:
        """الحصول على العناصر"""
        return self.items

    def get_progress(self) -> tuple:
        """الحصول على التقدم (مكتمل، الكل)"""
        total = len(self.items)
        completed = sum(1 for i in self.items if i.is_completed)
        return completed, total
