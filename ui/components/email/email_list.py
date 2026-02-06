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
from PyQt5.QtGui import QFont, QColor, QIcon

from core.email import Email, EmailImportance
from core.logging import app_logger
from core.themes import get_current_theme


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
        self._is_dark = get_current_theme() == 'dark'
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
        dot_color = "#3b82f6" if self._is_dark else "#0078d4"
        self.unread_dot = QLabel("●" if not self.email.is_read else "")
        self.unread_dot.setStyleSheet(f"color: {dot_color}; font-size: 8px;")
        self.unread_dot.setFixedWidth(12)

        # Sender
        text_color = "#f1f5f9" if self._is_dark else "#333"
        self.sender_label = QLabel(self.email.sender_name or self.email.sender_email)
        self.sender_label.setStyleSheet(
            f"font-weight: {'bold' if not self.email.is_read else 'normal'}; "
            f"font-size: 13px; color: {text_color};"
        )

        # Date
        date_color = "#64748b" if self._is_dark else "#888"
        self.date_label = QLabel(self.email.display_date)
        self.date_label.setStyleSheet(f"font-size: 11px; color: {date_color};")

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
        subj_color = "#f1f5f9" if self._is_dark else "#333"
        self.subject_label = QLabel(self.email.subject)
        self.subject_label.setStyleSheet(
            f"font-weight: {'600' if not self.email.is_read else 'normal'}; "
            f"font-size: 12px; color: {subj_color};"
        )
        self.subject_label.setWordWrap(False)

        # Preview row
        prev_color = "#94a3b8" if self._is_dark else "#666"
        self.preview_label = QLabel(self.email.preview)
        self.preview_label.setStyleSheet(f"font-size: 11px; color: {prev_color};")
        self.preview_label.setWordWrap(False)

        # AI info row (if analyzed)
        self.ai_label = QLabel()
        if self.email.ai_summary or self.email.ai_category:
            ai_text = []
            if self.email.ai_category:
                ai_text.append(f"📁 {self.email.ai_category}")
            if self.email.ai_priority:
                ai_text.append(f"⚡ {self.email.ai_priority}")
            ai_label_color = "#93c5fd" if self._is_dark else "#0078d4"
            self.ai_label.setText(" | ".join(ai_text))
            self.ai_label.setStyleSheet(f"font-size: 10px; color: {ai_label_color};")
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
        is_dark = getattr(self, '_is_dark', False)
        if not self.email.is_read:
            bg_color = "#1e3a5f" if is_dark else "#f0f7ff"
        else:
            bg_color = "#0f172a" if is_dark else "#ffffff"

        border_color = "#334155" if is_dark else "#e8e8e8"
        hover_color = "#1e293b" if is_dark else "#e8f4ff"
        self.setStyleSheet(f"""
            EmailListItem {{
                background-color: {bg_color};
                border-bottom: 1px solid {border_color};
            }}
            EmailListItem:hover {{
                background-color: {hover_color};
            }}
        """)

    def mark_as_read(self):
        """Mark email as read and update UI."""
        self.email.is_read = True
        self.unread_dot.setText("")
        self.sender_label.setStyleSheet("font-weight: normal; font-size: 13px; color: #333;")
        self.subject_label.setStyleSheet("font-weight: normal; font-size: 12px; color: #333;")
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
        self._is_dark = get_current_theme() == 'dark'
        self._setup_ui()

    def _setup_ui(self):
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Search bar
        search_frame = QFrame()
        sf_bg = "#1e293b" if self._is_dark else "#f8f8f8"
        sf_border = "#334155" if self._is_dark else "#ddd"
        search_frame.setStyleSheet(f"background-color: {sf_bg}; border-bottom: 1px solid {sf_border};")
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(8, 6, 8, 6)

        si_bg = "#0f172a" if self._is_dark else "white"
        si_border = "#475569" if self._is_dark else "#ddd"
        si_color = "#f1f5f9" if self._is_dark else "#333"
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 بحث في الإيميلات...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {si_border};
                border-radius: 4px;
                padding: 6px 10px;
                background: {si_bg};
                color: {si_color};
            }}
            QLineEdit:focus {{
                border-color: #2563eb;
            }}
        """)
        self.search_input.textChanged.connect(self._on_search)

        search_layout.addWidget(self.search_input)
        layout.addWidget(search_frame)

        # Email list
        list_bg = "#0f172a" if self._is_dark else "white"
        list_sel = "#1e3a5f" if self._is_dark else "#e8f4ff"
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_widget.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                border: none;
                background-color: {list_bg};
            }}
            QListWidget::item {{
                padding: 0;
                border: none;
            }}
            QListWidget::item:selected {{
                background-color: {list_sel};
            }}
        """)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self.list_widget)

        # Status bar
        sl_color = "#94a3b8" if self._is_dark else "#666"
        sl_bg = "#1e293b" if self._is_dark else "#f8f8f8"
        self.status_label = QLabel("لا توجد رسائل")
        self.status_label.setStyleSheet(f"padding: 8px; color: {sl_color}; font-size: 11px; background: {sl_bg};")
        layout.addWidget(self.status_label)

    def _create_toolbar(self) -> QWidget:
        """Create the toolbar."""
        toolbar = QFrame()
        tb_bg = "#1e293b" if self._is_dark else "#f0f0f0"
        tb_border = "#334155" if self._is_dark else "#ddd"
        toolbar.setStyleSheet(f"background-color: {tb_bg}; border-bottom: 1px solid {tb_border};")
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
        is_dark = getattr(self, '_is_dark', False)
        if active:
            return """
                QPushButton {
                    background-color: #2563eb;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 12px;
                    font-size: 11px;
                }
            """
        border = "#475569" if is_dark else "#ccc"
        color = "#f1f5f9" if is_dark else "#333"
        hover = "#334155" if is_dark else "#e8e8e8"
        return f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {border};
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
                color: {color};
            }}
            QPushButton:hover {{
                background-color: {hover};
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
