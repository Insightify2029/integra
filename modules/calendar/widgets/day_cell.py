"""
INTEGRA - Day Cell Widget
خلية اليوم في التقويم الشهري
المحور I

التاريخ: 4 فبراير 2026
"""

from datetime import date, datetime
from typing import Optional, List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QSizePolicy, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QColor, QPalette, QCursor

from ..models import CalendarEvent, DayEvents


class DayCellHeader(QWidget):
    """رأس خلية اليوم"""

    def __init__(
        self,
        day_number: int,
        is_today: bool = False,
        is_weekend: bool = False,
        is_holiday: bool = False,
        is_other_month: bool = False,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.day_number = day_number
        self.is_today = is_today
        self.is_weekend = is_weekend
        self.is_holiday = is_holiday
        self.is_other_month = is_other_month

        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        # رقم اليوم
        self.day_label = QLabel(str(self.day_number))
        font = QFont("Cairo", 11)

        if self.is_today:
            font.setBold(True)
            self.day_label.setStyleSheet("""
                QLabel {
                    background-color: #3498db;
                    color: white;
                    border-radius: 12px;
                    padding: 2px 6px;
                    min-width: 24px;
                }
            """)
        elif self.is_other_month:
            self.day_label.setStyleSheet("QLabel { color: #bdc3c7; }")
        elif self.is_weekend:
            self.day_label.setStyleSheet("QLabel { color: #e74c3c; }")
        elif self.is_holiday:
            self.day_label.setStyleSheet("QLabel { color: #e74c3c; font-weight: bold; }")

        self.day_label.setFont(font)
        self.day_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.day_label)
        layout.addStretch()


class DayCell(QFrame):
    """خلية اليوم في التقويم الشهري"""

    # Signals
    clicked = pyqtSignal(date)  # عند النقر على اليوم
    double_clicked = pyqtSignal(date)  # عند النقر المزدوج (لإنشاء حدث)
    event_clicked = pyqtSignal(CalendarEvent)  # عند النقر على حدث

    def __init__(
        self,
        cell_date: date,
        events: Optional[List[CalendarEvent]] = None,
        is_today: bool = False,
        is_weekend: bool = False,
        is_holiday: bool = False,
        holiday_name: Optional[str] = None,
        is_other_month: bool = False,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.cell_date = cell_date
        self.events = events or []
        self.is_today = is_today
        self.is_weekend = is_weekend
        self.is_holiday = is_holiday
        self.holiday_name = holiday_name
        self.is_other_month = is_other_month

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        self.setFrameStyle(QFrame.Box | QFrame.Plain)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setMinimumHeight(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        # رأس الخلية
        self.header = DayCellHeader(
            self.cell_date.day,
            self.is_today,
            self.is_weekend,
            self.is_holiday,
            self.is_other_month
        )
        layout.addWidget(self.header)

        # اسم العطلة (إن وجد)
        if self.is_holiday and self.holiday_name:
            holiday_label = QLabel(self.holiday_name)
            holiday_label.setStyleSheet("""
                QLabel {
                    color: #e74c3c;
                    font-size: 9px;
                    padding: 0 4px;
                }
            """)
            holiday_label.setWordWrap(True)
            layout.addWidget(holiday_label)

        # منطقة الأحداث
        self.events_container = QWidget()
        events_layout = QVBoxLayout(self.events_container)
        events_layout.setContentsMargins(2, 0, 2, 0)
        events_layout.setSpacing(1)

        # عرض الأحداث (حد أقصى 3)
        max_visible = 3
        for i, event in enumerate(self.events[:max_visible]):
            event_widget = self._create_event_item(event)
            events_layout.addWidget(event_widget)

        # عرض عدد الأحداث الإضافية
        if len(self.events) > max_visible:
            more_count = len(self.events) - max_visible
            more_label = QLabel(f"+{more_count} أحداث أخرى")
            more_label.setStyleSheet("""
                QLabel {
                    color: #7f8c8d;
                    font-size: 10px;
                    padding: 2px 4px;
                }
            """)
            events_layout.addWidget(more_label)

        events_layout.addStretch()
        layout.addWidget(self.events_container)

    def _create_event_item(self, event: CalendarEvent) -> QWidget:
        """إنشاء عنصر حدث مصغر"""
        item = QLabel(event.title)
        item.setWordWrap(False)
        item.setToolTip(f"{event.title}\n{event.time_formatted}")

        # تحديد اللون
        color = event.color or "#3498db"
        text_color = self._get_contrast_color(color)

        item.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: {text_color};
                border-radius: 3px;
                padding: 2px 4px;
                font-size: 10px;
            }}
            QLabel:hover {{
                background-color: {self._darken_color(color)};
            }}
        """)

        item.setCursor(QCursor(Qt.PointingHandCursor))
        item.mousePressEvent = lambda e: self.event_clicked.emit(event)

        return item

    def _apply_style(self):
        """تطبيق التنسيق"""
        base_style = """
            DayCell {
                background-color: white;
                border: 1px solid #e0e0e0;
            }
        """

        if self.is_today:
            base_style = """
                DayCell {
                    background-color: #eef7ff;
                    border: 2px solid #3498db;
                }
            """
        elif self.is_other_month:
            base_style = """
                DayCell {
                    background-color: #f8f9fa;
                    border: 1px solid #e0e0e0;
                }
            """
        elif self.is_weekend:
            base_style = """
                DayCell {
                    background-color: #fff9f9;
                    border: 1px solid #e0e0e0;
                }
            """

        self.setStyleSheet(base_style)

    def _get_contrast_color(self, hex_color: str) -> str:
        """الحصول على لون متباين للنص"""
        # إزالة #
        hex_color = hex_color.lstrip('#')
        # حساب السطوع
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return "#ffffff" if luminance < 0.5 else "#000000"

    def _darken_color(self, hex_color: str, factor: float = 0.85) -> str:
        """تغميق اللون"""
        hex_color = hex_color.lstrip('#')
        r = max(0, int(int(hex_color[0:2], 16) * factor))
        g = max(0, int(int(hex_color[2:4], 16) * factor))
        b = max(0, int(int(hex_color[4:6], 16) * factor))
        return f"#{r:02x}{g:02x}{b:02x}"

    def mousePressEvent(self, event):
        """عند النقر على الخلية"""
        self.clicked.emit(self.cell_date)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """عند النقر المزدوج"""
        self.double_clicked.emit(self.cell_date)
        super().mouseDoubleClickEvent(event)

    def set_events(self, events: List[CalendarEvent]):
        """تحديث الأحداث"""
        self.events = events
        # مسح layout القديم قبل إنشاء الجديد
        old_layout = self.layout()
        if old_layout is not None:
            while old_layout.count():
                item = old_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
            # نقل layout القديم لـ widget مؤقت لحذفه
            QWidget().setLayout(old_layout)
        # إعادة بناء الواجهة
        self._setup_ui()
        self._apply_style()

    def highlight(self, enabled: bool = True):
        """تمييز الخلية"""
        if enabled:
            self.setStyleSheet("""
                DayCell {
                    background-color: #fff3cd;
                    border: 2px solid #ffc107;
                }
            """)
        else:
            self._apply_style()
