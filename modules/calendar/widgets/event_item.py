"""
INTEGRA - Event Item Widgets
عناصر عرض الأحداث
المحور I

التاريخ: 4 فبراير 2026
"""

from datetime import datetime
from typing import Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QMenu, QAction, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QColor, QCursor, QIcon

from core.themes import get_current_palette, get_font, FONT_SIZE_SUBTITLE, FONT_SIZE_SMALL, FONT_WEIGHT_BOLD
from ..models import CalendarEvent, EventType, EventStatus


class MiniEventItem(QLabel):
    """عنصر حدث مصغر (للعرض في خلية اليوم)"""

    clicked = pyqtSignal(CalendarEvent)

    def __init__(
        self,
        event: CalendarEvent,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.event = event

        self._setup_ui()

    def _setup_ui(self):
        self.setText(self.event.title)
        self.setWordWrap(False)
        self.setToolTip(f"{self.event.title}\n{self.event.time_formatted}")
        self.setCursor(QCursor(Qt.PointingHandCursor))

        # تحديد اللون
        color = self.event.color or self.event.event_type.default_color
        text_color = self._get_contrast_color(color)

        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: {text_color};
                border-radius: 3px;
                padding: 2px 4px;
                font-size: 10px;
                font-family: Cairo;
            }}
            QLabel:hover {{
                background-color: {self._darken_color(color)};
            }}
        """)

    def _get_contrast_color(self, hex_color: str) -> str:
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return "#ffffff" if luminance < 0.5 else "#000000"

    def _darken_color(self, hex_color: str, factor: float = 0.85) -> str:
        hex_color = hex_color.lstrip('#')
        r = max(0, int(int(hex_color[0:2], 16) * factor))
        g = max(0, int(int(hex_color[2:4], 16) * factor))
        b = max(0, int(int(hex_color[4:6], 16) * factor))
        return f"#{r:02x}{g:02x}{b:02x}"

    def mousePressEvent(self, event):
        self.clicked.emit(self.event)
        super().mousePressEvent(event)


class EventItem(QFrame):
    """عنصر حدث للعرض في القائمة"""

    clicked = pyqtSignal(CalendarEvent)
    edit_requested = pyqtSignal(CalendarEvent)
    delete_requested = pyqtSignal(CalendarEvent)

    def __init__(
        self,
        event: CalendarEvent,
        show_date: bool = False,
        compact: bool = False,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.event = event
        self.show_date = show_date
        self.compact = compact

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.setCursor(QCursor(Qt.PointingHandCursor))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8) if not self.compact else layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        # شريط اللون
        color_bar = QFrame()
        color_bar.setFixedWidth(4)
        color_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {self.event.color or self.event.event_type.default_color};
                border-radius: 2px;
            }}
        """)
        layout.addWidget(color_bar)

        # المحتوى
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)

        # العنوان
        title_layout = QHBoxLayout()
        title_layout.setSpacing(4)

        # أيقونة النوع
        type_label = QLabel(self.event.event_type.label_ar)
        type_label.setStyleSheet(f"""
            QLabel {{
                background-color: {self.event.event_type.default_color}20;
                color: {self.event.event_type.default_color};
                border-radius: 3px;
                padding: 1px 4px;
                font-size: 9px;
            }}
        """)
        title_layout.addWidget(type_label)

        p = get_current_palette()
        title_label = QLabel(self.event.title)
        title_label.setFont(get_font(FONT_SIZE_SMALL, FONT_WEIGHT_BOLD))
        title_label.setStyleSheet(f"color: {p['text_primary']};")
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        content_layout.addLayout(title_layout)

        # الوقت والتاريخ
        time_layout = QHBoxLayout()
        time_layout.setSpacing(8)

        if self.show_date:
            date_label = QLabel(self.event.date_formatted)
            date_label.setStyleSheet(f"color: {p['text_muted']}; font-size: 11px;")
            time_layout.addWidget(date_label)

        time_label = QLabel(self.event.time_formatted)
        time_label.setStyleSheet(f"color: {p['primary']}; font-size: 11px;")
        time_layout.addWidget(time_label)

        if self.event.duration_formatted and not self.event.is_all_day:
            duration_label = QLabel(f"({self.event.duration_formatted})")
            duration_label.setStyleSheet(f"color: {p['text_muted']}; font-size: 10px;")
            time_layout.addWidget(duration_label)

        time_layout.addStretch()
        content_layout.addLayout(time_layout)

        # الموقع (إن وجد)
        if self.event.location and not self.compact:
            location_label = QLabel(f"📍 {self.event.location}")
            location_label.setStyleSheet(f"color: {p['text_muted']}; font-size: 10px;")
            content_layout.addWidget(location_label)

        # الوصف (إن وجد)
        if self.event.description and not self.compact:
            desc_label = QLabel(self.event.description[:100] + "..." if len(self.event.description or "") > 100 else self.event.description)
            desc_label.setStyleSheet(f"color: {p['text_muted']}; font-size: 10px;")
            desc_label.setWordWrap(True)
            content_layout.addWidget(desc_label)

        layout.addLayout(content_layout, 1)

        # أزرار الإجراءات
        if not self.compact:
            actions_layout = QVBoxLayout()
            actions_layout.setSpacing(4)

            # زر القائمة
            menu_btn = QPushButton("⋮")
            menu_btn.setFixedSize(24, 24)
            menu_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    font-size: 16px;
                    color: {p['text_muted']};
                }}
                QPushButton:hover {{
                    background-color: {p['bg_hover']};
                    border-radius: 4px;
                }}
            """)
            menu_btn.clicked.connect(self._show_menu)
            actions_layout.addWidget(menu_btn)
            actions_layout.addStretch()

            layout.addLayout(actions_layout)

    def _apply_style(self):
        p = get_current_palette()
        base_style = f"""
            EventItem {{
                background-color: {p['bg_card']};
                border: 1px solid {p['border']};
                border-radius: 6px;
            }}
            EventItem:hover {{
                border-color: {p['primary']};
                background-color: {p['bg_hover']};
            }}
        """

        if self.event.status == EventStatus.CANCELLED:
            base_style = f"""
                EventItem {{
                    background-color: {p['danger']}15;
                    border: 1px solid {p['danger']}40;
                    border-radius: 6px;
                }}
            """

        self.setStyleSheet(base_style)

    def _show_menu(self):
        """عرض قائمة الإجراءات"""
        menu = QMenu(self)
        p = get_current_palette()
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {p['bg_card']};
                border: 1px solid {p['border']};
                border-radius: 4px;
                padding: 4px;
                color: {p['text_primary']};
            }}
            QMenu::item {{
                padding: 6px 20px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {p['primary']};
                color: {p['text_on_primary']};
            }}
        """)

        edit_action = QAction("✏️ تعديل", self)
        edit_action.triggered.connect(lambda: self.edit_requested.emit(self.event))
        menu.addAction(edit_action)

        delete_action = QAction("🗑️ حذف", self)
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.event))
        menu.addAction(delete_action)

        menu.exec_(QCursor.pos())

    def mousePressEvent(self, event):
        self.clicked.emit(self.event)
        super().mousePressEvent(event)


class EventCard(QFrame):
    """بطاقة حدث كاملة (للعرض في التفاصيل)"""

    edit_requested = pyqtSignal(CalendarEvent)
    delete_requested = pyqtSignal(CalendarEvent)
    close_requested = pyqtSignal()

    def __init__(
        self,
        event: CalendarEvent,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.event = event

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # رأس البطاقة
        header_layout = QHBoxLayout()

        # شريط اللون والعنوان
        color_title_layout = QHBoxLayout()
        color_title_layout.setSpacing(8)

        color_bar = QFrame()
        color_bar.setFixedSize(4, 40)
        color_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {self.event.color or self.event.event_type.default_color};
                border-radius: 2px;
            }}
        """)
        color_title_layout.addWidget(color_bar)

        title_container = QVBoxLayout()
        title_container.setSpacing(2)

        type_label = QLabel(self.event.event_type.label_ar)
        type_label.setStyleSheet(f"""
            QLabel {{
                color: {self.event.event_type.default_color};
                font-size: 10px;
            }}
        """)
        title_container.addWidget(type_label)

        p = get_current_palette()
        title_label = QLabel(self.event.title)
        title_label.setFont(get_font(FONT_SIZE_SUBTITLE, FONT_WEIGHT_BOLD))
        title_label.setStyleSheet(f"color: {p['text_primary']};")
        title_label.setWordWrap(True)
        title_container.addWidget(title_label)

        color_title_layout.addLayout(title_container, 1)
        header_layout.addLayout(color_title_layout, 1)

        # زر الإغلاق
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                font-size: 16px;
                color: {p['text_muted']};
            }}
            QPushButton:hover {{
                background-color: {p['danger']}20;
                color: {p['danger']};
                border-radius: 4px;
            }}
        """)
        close_btn.clicked.connect(self.close_requested.emit)
        header_layout.addWidget(close_btn)

        layout.addLayout(header_layout)

        # فاصل
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(f"background-color: {p['border']};")
        layout.addWidget(separator)

        # التفاصيل
        details_layout = QVBoxLayout()
        details_layout.setSpacing(8)

        # التاريخ والوقت
        datetime_layout = QHBoxLayout()
        datetime_layout.setSpacing(16)

        date_container = QVBoxLayout()
        date_label = QLabel("📅 التاريخ")
        date_label.setStyleSheet(f"color: {p['text_muted']}; font-size: 10px;")
        date_container.addWidget(date_label)
        date_value = QLabel(self.event.date_formatted)
        date_value.setStyleSheet(f"color: {p['text_primary']}; font-size: 12px; font-weight: bold;")
        date_container.addWidget(date_value)
        datetime_layout.addLayout(date_container)

        time_container = QVBoxLayout()
        time_label = QLabel("⏰ الوقت")
        time_label.setStyleSheet(f"color: {p['text_muted']}; font-size: 10px;")
        time_container.addWidget(time_label)
        time_value = QLabel(self.event.time_formatted)
        time_value.setStyleSheet(f"color: {p['primary']}; font-size: 12px; font-weight: bold;")
        time_container.addWidget(time_value)
        datetime_layout.addLayout(time_container)

        datetime_layout.addStretch()
        details_layout.addLayout(datetime_layout)

        # المدة
        if self.event.duration_formatted:
            duration_layout = QHBoxLayout()
            duration_icon = QLabel("⏱️ المدة:")
            duration_icon.setStyleSheet(f"color: {p['text_muted']}; font-size: 11px;")
            duration_layout.addWidget(duration_icon)
            duration_value = QLabel(self.event.duration_formatted)
            duration_value.setStyleSheet(f"color: {p['text_primary']}; font-size: 11px;")
            duration_layout.addWidget(duration_value)
            duration_layout.addStretch()
            details_layout.addLayout(duration_layout)

        # الموقع
        if self.event.location:
            location_layout = QHBoxLayout()
            location_icon = QLabel("📍 الموقع:")
            location_icon.setStyleSheet(f"color: {p['text_muted']}; font-size: 11px;")
            location_layout.addWidget(location_icon)
            location_value = QLabel(self.event.location)
            location_value.setStyleSheet(f"color: {p['text_primary']}; font-size: 11px;")
            location_value.setWordWrap(True)
            location_layout.addWidget(location_value, 1)
            details_layout.addLayout(location_layout)

        # الوصف
        if self.event.description:
            desc_label = QLabel("📝 الوصف")
            desc_label.setStyleSheet(f"color: {p['text_muted']}; font-size: 10px;")
            details_layout.addWidget(desc_label)
            desc_value = QLabel(self.event.description)
            desc_value.setStyleSheet(f"color: {p['text_primary']}; font-size: 11px; padding: 8px; background-color: {p['bg_main']}; border-radius: 4px;")
            desc_value.setWordWrap(True)
            details_layout.addWidget(desc_value)

        # المهمة المرتبطة
        if self.event.task_title:
            task_layout = QHBoxLayout()
            task_icon = QLabel("✅ المهمة:")
            task_icon.setStyleSheet(f"color: {p['text_muted']}; font-size: 11px;")
            task_layout.addWidget(task_icon)
            task_value = QLabel(self.event.task_title)
            task_value.setStyleSheet(f"color: {p['success']}; font-size: 11px;")
            task_layout.addWidget(task_value, 1)
            details_layout.addLayout(task_layout)

        # الموظف المرتبط
        if self.event.employee_name:
            emp_layout = QHBoxLayout()
            emp_icon = QLabel("👤 الموظف:")
            emp_icon.setStyleSheet(f"color: {p['text_muted']}; font-size: 11px;")
            emp_layout.addWidget(emp_icon)
            emp_value = QLabel(self.event.employee_name)
            emp_value.setStyleSheet(f"color: {p['text_primary']}; font-size: 11px;")
            emp_layout.addWidget(emp_value, 1)
            details_layout.addLayout(emp_layout)

        layout.addLayout(details_layout)

        # أزرار الإجراءات
        layout.addStretch()

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)

        edit_btn = QPushButton("✏️ تعديل")
        edit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {p['primary']};
                color: {p['text_on_primary']};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {p['primary_hover']};
            }}
        """)
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.event))
        buttons_layout.addWidget(edit_btn)

        delete_btn = QPushButton("🗑️ حذف")
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {p['danger']};
                color: {p['text_on_primary']};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {p['danger']};
            }}
        """)
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.event))
        buttons_layout.addWidget(delete_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

    def _apply_style(self):
        p = get_current_palette()
        self.setStyleSheet(f"""
            EventCard {{
                background-color: {p['bg_card']};
                border: 1px solid {p['border']};
                border-radius: 8px;
            }}
        """)
