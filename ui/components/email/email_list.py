"""
Email List Widget
=================
Displays a list of emails with preview.
"""

from typing import Optional, List, Callable
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QFrame, QLineEdit,
    QPushButton, QMenu, QAction, QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QColor, QIcon

from core.email import Email, EmailImportance
from core.logging import app_logger
from core.themes import get_current_palette


class EmailListItem(QFrame):
    """
    Widget for a single email item in the list.
    """

    def __init__(self, email: Email, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.email = email
        self._setup_ui()

    def _setup_ui(self):
        """Setup the item UI."""
        self._palette = get_current_palette()
        self.setFrameShape(QFrame.NoFrame)
        self.setCursor(Qt.PointingHandCursor)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        # Top row: sender + date + icons
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        # Unread indicator
        self.unread_dot = QLabel("●" if not self.email.is_read else "")
        self.unread_dot.setStyleSheet(f"color: {self._palette['primary']}; font-size: 8px;")
        self.unread_dot.setFixedWidth(12)

        # Sender
        self.sender_label = QLabel(self.email.sender_name or self.email.sender_email)
        self.sender_label.setStyleSheet(
            f"font-weight: {'bold' if not self.email.is_read else 'normal'}; "
            f"font-size: 13px; color: {self._palette['text_primary']};"
        )

        # Date
        self.date_label = QLabel(self.email.display_date)
        self.date_label.setStyleSheet(f"font-size: 11px; color: {self._palette['text_muted']};")

        # Icons
        icons = []
        if self.email.has_attachments:
            icons.append("📎")
        if self.email.is_flagged:
            icons.append("🚩")
        if self.email.importance == EmailImportance.HIGH:
            icons.append("❗")

        self.icons_label = QLabel(" ".join(icons))
        self.icons_label.setStyleSheet("font-size: 12px;")

        top_row.addWidget(self.unread_dot)
        top_row.addWidget(self.sender_label, 1)
        top_row.addWidget(self.icons_label)
        top_row.addWidget(self.date_label)

        # Subject row
        self.subject_label = QLabel(self.email.subject)
        self.subject_label.setStyleSheet(
            f"font-weight: {'600' if not self.email.is_read else 'normal'}; "
            f"font-size: 12px; color: {self._palette['text_primary']};"
        )
        self.subject_label.setWordWrap(False)

        # Preview row
        self.preview_label = QLabel(self.email.preview)
        self.preview_label.setStyleSheet(f"font-size: 11px; color: {self._palette['text_secondary']};")
        self.preview_label.setWordWrap(False)

        # AI info row (if analyzed)
        self.ai_label = QLabel()
        if self.email.ai_summary or self.email.ai_category:
            ai_text = []
            if self.email.ai_category:
                ai_text.append(f"📁 {self.email.ai_category}")
            if self.email.ai_priority:
                ai_text.append(f"⚡ {self.email.ai_priority}")
            self.ai_label.setText(" | ".join(ai_text))
            self.ai_label.setStyleSheet(f"font-size: 10px; color: {self._palette['info']};")
        else:
            self.ai_label.hide()

        layout.addLayout(top_row)
        layout.addWidget(self.subject_label)
        layout.addWidget(self.preview_label)
        layout.addWidget(self.ai_label)

        # Style
        self._update_style()

    def _update_style(self):
        """Update item style based on state."""
        p = getattr(self, '_palette', get_current_palette())
        if not self.email.is_read:
            bg_color = p['primary_light']
        else:
            bg_color = p['bg_main']

        self.setStyleSheet(f"""
            EmailListItem {{
                background-color: {bg_color};
                border-bottom: 1px solid {p['border']};
            }}
            EmailListItem:hover {{
                background-color: {p['bg_hover']};
            }}
        """)

    def mark_as_read(self):
        """Mark email as read and update UI."""
        self.email.is_read = True
        p = getattr(self, '_palette', get_current_palette())
        self.unread_dot.setText("")
        self.sender_label.setStyleSheet(f"font-weight: normal; font-size: 13px; color: {p['text_primary']};")
        self.subject_label.setStyleSheet(f"font-weight: normal; font-size: 12px; color: {p['text_primary']};")
        self._update_style()


class EmailListWidget(QWidget):
    """
    Widget displaying a list of emails.

    Signals:
        email_selected: Emitted when an email is selected
        email_double_clicked: Emitted on double-click
        refresh_requested: Emitted when refresh is requested
    """

    email_selected = pyqtSignal(Email)
    email_double_clicked = pyqtSignal(Email)
    refresh_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._emails: List[Email] = []
        self._items: dict = {}  # entry_id -> QListWidgetItem
        self._palette = get_current_palette()
        self._setup_ui()

    def _setup_ui(self):
        """Setup the widget UI."""
        p = self._palette
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Search bar
        search_frame = QFrame()
        search_frame.setStyleSheet(
            f"background-color: {p['bg_card']}; border-bottom: 1px solid {p['border']};"
        )
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(8, 6, 8, 6)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("بحث في الإيميلات...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {p['border_light']};
                border-radius: 4px;
                padding: 6px 10px;
                background: {p['bg_input']};
                color: {p['text_primary']};
            }}
            QLineEdit:focus {{
                border-color: {p['primary']};
            }}
        """)
        self.search_input.textChanged.connect(self._on_search)

        search_layout.addWidget(self.search_input)
        layout.addWidget(search_frame)

        # Email list
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_widget.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                border: none;
                background-color: {p['bg_main']};
            }}
            QListWidget::item {{
                padding: 0;
                border: none;
            }}
            QListWidget::item:selected {{
                background-color: {p['primary_light']};
            }}
        """)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self.list_widget)

        # Status bar
        self.status_label = QLabel("لا توجد رسائل")
        self.status_label.setStyleSheet(
            f"padding: 8px; color: {p['text_secondary']}; font-size: 11px;"
            f" background: {p['bg_card']};"
        )
        layout.addWidget(self.status_label)

    def _create_toolbar(self) -> QWidget:
        """Create the toolbar."""
        p = self._palette
        toolbar = QFrame()
        toolbar.setStyleSheet(f"background-color: {p['bg_card']}; border-bottom: 1px solid {p['border']};")
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        # Refresh button
        refresh_btn = QPushButton("🔄")
        refresh_btn.setToolTip("تحديث")
        refresh_btn.setFixedSize(32, 28)
        refresh_btn.setStyleSheet(self._button_style())
        refresh_btn.clicked.connect(self.refresh_requested.emit)

        # Filter buttons
        self.all_btn = QPushButton("الكل")
        self.all_btn.setStyleSheet(self._button_style(active=True))
        self.all_btn.clicked.connect(lambda: self._filter_emails("all"))

        self.unread_btn = QPushButton("غير مقروء")
        self.unread_btn.setStyleSheet(self._button_style())
        self.unread_btn.clicked.connect(lambda: self._filter_emails("unread"))

        self.flagged_btn = QPushButton("مميز")
        self.flagged_btn.setStyleSheet(self._button_style())
        self.flagged_btn.clicked.connect(lambda: self._filter_emails("flagged"))

        layout.addWidget(refresh_btn)
        layout.addSpacing(8)
        layout.addWidget(self.all_btn)
        layout.addWidget(self.unread_btn)
        layout.addWidget(self.flagged_btn)
        layout.addStretch()

        return toolbar

    def _button_style(self, active: bool = False) -> str:
        """Get button style (theme-aware)."""
        p = getattr(self, '_palette', get_current_palette())
        if active:
            return f"""
                QPushButton {{
                    background-color: {p['primary']};
                    color: {p['text_on_primary']};
                    border: none;
                    border-radius: 4px;
                    padding: 4px 12px;
                    font-size: 11px;
                }}
            """
        return f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {p['border_light']};
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
                color: {p['text_primary']};
            }}
            QPushButton:hover {{
                background-color: {p['bg_hover']};
            }}
        """

    def set_emails(self, emails: List[Email]):
        """Set the emails to display."""
        self._emails = emails
        self._refresh_list()

    def _refresh_list(self, filter_type: str = "all"):
        """Refresh the list widget."""
        self.list_widget.clear()
        self._items.clear()

        filtered = self._emails

        if filter_type == "unread":
            filtered = [e for e in self._emails if not e.is_read]
        elif filter_type == "flagged":
            filtered = [e for e in self._emails if e.is_flagged]

        for email in filtered:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, email)
            item.setSizeHint(QSize(0, 90))

            widget = EmailListItem(email)
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)
            self._items[email.entry_id] = (item, widget)

        # Update status
        unread = len([e for e in self._emails if not e.is_read])
        self.status_label.setText(f"{len(filtered)} رسالة ({unread} غير مقروء)")

    def _filter_emails(self, filter_type: str):
        """Filter emails."""
        # Update button styles
        self.all_btn.setStyleSheet(self._button_style(filter_type == "all"))
        self.unread_btn.setStyleSheet(self._button_style(filter_type == "unread"))
        self.flagged_btn.setStyleSheet(self._button_style(filter_type == "flagged"))

        self._refresh_list(filter_type)

    def _on_search(self, text: str):
        """Handle search input."""
        if not text:
            self._refresh_list()
            return

        text = text.lower()
        filtered = [
            e for e in self._emails
            if text in e.subject.lower()
            or text in e.sender_name.lower()
            or text in e.sender_email.lower()
            or text in e.body.lower()
        ]

        self.list_widget.clear()
        self._items.clear()

        for email in filtered:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, email)
            item.setSizeHint(QSize(0, 90))

            widget = EmailListItem(email)
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)
            self._items[email.entry_id] = (item, widget)

        self.status_label.setText(f"نتائج البحث: {len(filtered)} رسالة")

    def _on_item_clicked(self, item: QListWidgetItem):
        """Handle item click."""
        email = item.data(Qt.UserRole)
        if email:
            self.email_selected.emit(email)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        """Handle item double-click."""
        email = item.data(Qt.UserRole)
        if email:
            self.email_double_clicked.emit(email)

    def _show_context_menu(self, position):
        """Show context menu."""
        item = self.list_widget.itemAt(position)
        if not item:
            return

        email = item.data(Qt.UserRole)
        if not email:
            return

        menu = QMenu(self)

        # Mark as read/unread
        if email.is_read:
            mark_action = QAction("✉️ تحديد كغير مقروء", self)
        else:
            mark_action = QAction("📭 تحديد كمقروء", self)
        menu.addAction(mark_action)

        # Flag/Unflag
        if email.is_flagged:
            flag_action = QAction("🏳️ إزالة العلامة", self)
        else:
            flag_action = QAction("🚩 تمييز", self)
        menu.addAction(flag_action)

        menu.addSeparator()

        # AI actions
        analyze_action = QAction("🤖 تحليل بالذكاء الاصطناعي", self)
        menu.addAction(analyze_action)

        menu.addSeparator()

        # Delete
        delete_action = QAction("🗑️ حذف", self)
        menu.addAction(delete_action)

        menu.exec_(self.list_widget.viewport().mapToGlobal(position))

    def mark_email_as_read(self, entry_id: str):
        """Mark an email as read in the list."""
        if entry_id in self._items:
            item, widget = self._items[entry_id]
            widget.mark_as_read()


def create_email_list(parent: Optional[QWidget] = None) -> EmailListWidget:
    """Create and return an email list widget."""
    return EmailListWidget(parent)
