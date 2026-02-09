"""
INTEGRA - Task Filters Widget
فلاتر المهام
المحور H

التاريخ: 4 فبراير 2026
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QComboBox, QLineEdit, QPushButton, QFrame,
    QButtonGroup, QToolButton
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from ..models import TaskStatus, TaskPriority, TaskCategory
from core.themes import get_current_palette, get_font, FONT_SIZE_BODY


class TaskFilters(QFrame):
    """
    شريط فلاتر المهام

    يوفر فلترة حسب: الحالة، الأولوية، التصنيف، البحث
    """

    # Signals
    filters_changed = pyqtSignal(dict)  # {"status": ..., "priority": ..., ...}
    search_changed = pyqtSignal(str)
    view_changed = pyqtSignal(str)  # "list" or "board"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """إعداد واجهة المستخدم"""
        p = get_current_palette()
        self.setObjectName("taskFilters")
        self.setFixedHeight(60)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(16)

        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 البحث في المهام...")
        self.search_input.setFixedWidth(250)
        self.search_input.setFixedHeight(36)
        self.search_input.textChanged.connect(self._on_search_changed)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {p['border']};
                border-radius: 6px;
                padding: 0 12px;
                font-size: 13px;
                background-color: {p['bg_card']};
            }}
            QLineEdit:focus {{
                border-color: {p['border_focus']};
            }}
        """)
        layout.addWidget(self.search_input)

        # Separator
        layout.addWidget(self._create_separator())

        # Status filter
        status_label = QLabel("الحالة:")
        status_label.setFont(get_font(FONT_SIZE_BODY))
        layout.addWidget(status_label)

        self.status_combo = QComboBox()
        self.status_combo.setFixedWidth(130)
        self.status_combo.setFixedHeight(36)
        self.status_combo.addItem("الكل", None)
        for status in TaskStatus:
            self.status_combo.addItem(status.label_ar, status.value)
        self.status_combo.currentIndexChanged.connect(self._on_filter_changed)
        self._style_combo(self.status_combo)
        layout.addWidget(self.status_combo)

        # Priority filter
        priority_label = QLabel("الأولوية:")
        priority_label.setFont(get_font(FONT_SIZE_BODY))
        layout.addWidget(priority_label)

        self.priority_combo = QComboBox()
        self.priority_combo.setFixedWidth(120)
        self.priority_combo.setFixedHeight(36)
        self.priority_combo.addItem("الكل", None)
        for priority in TaskPriority:
            self.priority_combo.addItem(priority.label_ar, priority.value)
        self.priority_combo.currentIndexChanged.connect(self._on_filter_changed)
        self._style_combo(self.priority_combo)
        layout.addWidget(self.priority_combo)

        # Category filter
        category_label = QLabel("التصنيف:")
        category_label.setFont(get_font(FONT_SIZE_BODY))
        layout.addWidget(category_label)

        self.category_combo = QComboBox()
        self.category_combo.setFixedWidth(140)
        self.category_combo.setFixedHeight(36)
        self.category_combo.addItem("الكل", None)
        for category in TaskCategory:
            self.category_combo.addItem(category.label_ar, category.value)
        self.category_combo.currentIndexChanged.connect(self._on_filter_changed)
        self._style_combo(self.category_combo)
        layout.addWidget(self.category_combo)

        layout.addStretch()

        # View toggle buttons
        self.view_group = QButtonGroup(self)

        self.list_btn = QToolButton()
        self.list_btn.setText("📋")
        self.list_btn.setToolTip("عرض القائمة")
        self.list_btn.setCheckable(True)
        self.list_btn.setChecked(True)
        self.list_btn.setFixedSize(36, 36)
        self.view_group.addButton(self.list_btn, 0)
        layout.addWidget(self.list_btn)

        self.board_btn = QToolButton()
        self.board_btn.setText("📊")
        self.board_btn.setToolTip("عرض الكانبان")
        self.board_btn.setCheckable(True)
        self.board_btn.setFixedSize(36, 36)
        self.view_group.addButton(self.board_btn, 1)
        layout.addWidget(self.board_btn)

        self.view_group.buttonClicked.connect(self._on_view_changed)

        # Style view buttons
        self._style_view_buttons()

        # Reset button
        self.reset_btn = QPushButton("↺")
        self.reset_btn.setToolTip("إعادة تعيين الفلاتر")
        self.reset_btn.setFixedSize(36, 36)
        self.reset_btn.clicked.connect(self.reset_filters)
        self.reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {p['bg_main']};
                border: 1px solid {p['border']};
                border-radius: 6px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {p['bg_hover']};
            }}
        """)
        layout.addWidget(self.reset_btn)

        # Frame style
        self.setStyleSheet(f"""
            QFrame#taskFilters {{
                background-color: {p['bg_main']};
                border-bottom: 1px solid {p['border']};
            }}
        """)

    def _create_separator(self) -> QFrame:
        """إنشاء فاصل"""
        p = get_current_palette()
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet(f"background-color: {p['border']};")
        sep.setFixedWidth(1)
        return sep

    def _style_combo(self, combo: QComboBox):
        """تنسيق ComboBox"""
        p = get_current_palette()
        combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {p['border']};
                border-radius: 6px;
                padding: 0 10px;
                background-color: {p['bg_card']};
                font-size: 12px;
            }}
            QComboBox:hover {{
                border-color: {p['border_focus']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {p['text_muted']};
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                border: 1px solid {p['border']};
                background-color: {p['bg_card']};
                selection-background-color: {p['primary']};
            }}
        """)

    def _style_view_buttons(self):
        """تنسيق أزرار العرض"""
        p = get_current_palette()
        style = f"""
            QToolButton {{
                background-color: {p['bg_card']};
                border: 1px solid {p['border']};
                border-radius: 6px;
                font-size: 16px;
            }}
            QToolButton:hover {{
                background-color: {p['bg_hover']};
            }}
            QToolButton:checked {{
                background-color: {p['primary']};
                border-color: {p['primary']};
            }}
        """
        self.list_btn.setStyleSheet(style)
        self.board_btn.setStyleSheet(style)

    def _on_filter_changed(self):
        """عند تغيير الفلاتر"""
        filters = self.get_filters()
        self.filters_changed.emit(filters)

    def _on_search_changed(self, text: str):
        """عند تغيير البحث"""
        self.search_changed.emit(text)

    def _on_view_changed(self, button):
        """عند تغيير العرض"""
        view = "list" if button == self.list_btn else "board"
        self.view_changed.emit(view)

    def get_filters(self) -> dict:
        """الحصول على الفلاتر الحالية"""
        return {
            "status": self.status_combo.currentData(),
            "priority": self.priority_combo.currentData(),
            "category": self.category_combo.currentData(),
            "search": self.search_input.text().strip()
        }

    def reset_filters(self):
        """إعادة تعيين الفلاتر"""
        self.status_combo.setCurrentIndex(0)
        self.priority_combo.setCurrentIndex(0)
        self.category_combo.setCurrentIndex(0)
        self.search_input.clear()
        self._on_filter_changed()

    def set_view(self, view: str):
        """تعيين نوع العرض"""
        if view == "list":
            self.list_btn.setChecked(True)
        else:
            self.board_btn.setChecked(True)


class QuickFilters(QWidget):
    """
    فلاتر سريعة

    أزرار للفلترة السريعة: اليوم، متأخرة، عاجلة، الكل
    """

    filter_selected = pyqtSignal(str)  # filter_type

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_filter = "all"
        self._setup_ui()

    def _setup_ui(self):
        """إعداد واجهة المستخدم"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.buttons = {}

        filters = [
            ("all", "📋 الكل", None),
            ("today", "📅 اليوم", None),
            ("overdue", "⚠️ متأخرة", "#dc3545"),
            ("urgent", "🔥 عاجلة", "#fd7e14"),
            ("in_progress", "🔄 قيد التنفيذ", "#007bff"),
        ]

        for filter_id, label, accent_color in filters:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedHeight(32)
            btn.clicked.connect(lambda checked, f=filter_id: self._on_filter_clicked(f))
            self.buttons[filter_id] = btn
            layout.addWidget(btn)

        # Set "all" as default
        self.buttons["all"].setChecked(True)

        layout.addStretch()

        self._update_styles()

    def _on_filter_clicked(self, filter_type: str):
        """عند اختيار فلتر"""
        self._current_filter = filter_type

        # Update button states
        for fid, btn in self.buttons.items():
            btn.setChecked(fid == filter_type)

        self._update_styles()
        self.filter_selected.emit(filter_type)

    def _update_styles(self):
        """تحديث تنسيق الأزرار"""
        p = get_current_palette()
        for fid, btn in self.buttons.items():
            if btn.isChecked():
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {p['primary']};
                        color: {p['text_on_primary']};
                        border: none;
                        border-radius: 4px;
                        padding: 0 16px;
                        font-weight: bold;
                        font-size: 12px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {p['bg_main']};
                        color: {p['text_secondary']};
                        border: 1px solid {p['border']};
                        border-radius: 4px;
                        padding: 0 16px;
                        font-size: 12px;
                    }}
                    QPushButton:hover {{
                        background-color: {p['bg_hover']};
                    }}
                """)

    def get_current_filter(self) -> str:
        """الحصول على الفلتر الحالي"""
        return self._current_filter
