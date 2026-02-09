"""
INTEGRA - Day View
العرض اليومي للتقويم
المحور I

التاريخ: 4 فبراير 2026
"""

from datetime import date, datetime, time, timedelta
from typing import Optional, List, Dict
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from core.themes import get_current_palette, get_font, FONT_SIZE_SUBTITLE, FONT_WEIGHT_BOLD
from ..models import CalendarEvent
from ..widgets.calendar_header import DAY_NAMES_AR, MONTH_NAMES_AR
from ..widgets.event_item import EventItem


class HourBlock(QFrame):
    """كتلة الساعة في العرض اليومي"""

    clicked = pyqtSignal(datetime)
    event_clicked = pyqtSignal(CalendarEvent)

    def __init__(
        self,
        block_datetime: datetime,
        events: Optional[List[CalendarEvent]] = None,
        is_working_hour: bool = True,
        is_current_hour: bool = False,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.block_datetime = block_datetime
        self.events = events or []
        self.is_working_hour = is_working_hour
        self.is_current_hour = is_current_hour

        self._setup_ui()

    def _setup_ui(self):
        self.setMinimumHeight(60)
        self.setFrameStyle(QFrame.Box | QFrame.Plain)
        p = get_current_palette()

        if self.is_current_hour:
            bg_color = p['primary_light']
            border = f"2px solid {p['primary']}"
        elif self.is_working_hour:
            bg_color = p['bg_card']
            border = f"1px solid {p['border_light']}"
        else:
            bg_color = p['bg_main']
            border = f"1px solid {p['border_light']}"

        self.setStyleSheet(f"""
            HourBlock {{
                background-color: {bg_color};
                border: {border};
            }}
            HourBlock:hover {{
                background-color: {p['bg_hover']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # عرض الأحداث
        for event in self.events:
            event_widget = EventItem(event, show_date=False, compact=True)
            event_widget.clicked.connect(lambda e=event: self.event_clicked.emit(e))
            layout.addWidget(event_widget)

        layout.addStretch()

    def mousePressEvent(self, event):
        if not self.events:  # فقط إذا لم يكن هناك أحداث
            self.clicked.emit(self.block_datetime)
        super().mousePressEvent(event)


class DayView(QWidget):
    """العرض اليومي للتقويم"""

    # Signals
    time_clicked = pyqtSignal(datetime)
    event_clicked = pyqtSignal(CalendarEvent)

    def __init__(
        self,
        current_date: Optional[date] = None,
        events: Optional[List[CalendarEvent]] = None,
        work_hours_start: int = 8,
        work_hours_end: int = 17,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.current_date = current_date or date.today()
        self.events = events or []
        self.work_hours_start = work_hours_start
        self.work_hours_end = work_hours_end

        self._events_by_hour: Dict[int, List[CalendarEvent]] = {}
        self._all_day_events: List[CalendarEvent] = []

        self._setup_ui()
        self._organize_events()
        self._build_day()

    def _setup_ui(self):
        p = get_current_palette()
        self.setStyleSheet(f"background-color: {p['bg_card']};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # رأس اليوم
        self.header = QFrame()
        self.header.setStyleSheet(f"""
            QFrame {{
                background-color: {p['bg_main']};
                border-bottom: 1px solid {p['border']};
            }}
        """)
        header_layout = QVBoxLayout(self.header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(4)

        # تاريخ اليوم
        self.date_label = QLabel()
        self.date_label.setFont(get_font(FONT_SIZE_SUBTITLE, FONT_WEIGHT_BOLD))
        self.date_label.setStyleSheet(f"color: {p['text_primary']};")
        header_layout.addWidget(self.date_label)

        # أحداث طوال اليوم
        self.all_day_container = QWidget()
        self.all_day_layout = QVBoxLayout(self.all_day_container)
        self.all_day_layout.setContentsMargins(0, 8, 0, 0)
        self.all_day_layout.setSpacing(4)
        header_layout.addWidget(self.all_day_container)

        layout.addWidget(self.header)

        # منطقة التمرير
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.hours_container = QWidget()
        self.hours_layout = QVBoxLayout(self.hours_container)
        self.hours_layout.setContentsMargins(0, 0, 0, 0)
        self.hours_layout.setSpacing(0)

        scroll.setWidget(self.hours_container)
        layout.addWidget(scroll, 1)

    def _organize_events(self):
        """تنظيم الأحداث حسب الساعة"""
        self._events_by_hour.clear()
        self._all_day_events.clear()

        for event in self.events:
            if not event.start_datetime:
                continue

            if event.start_datetime.date() != self.current_date:
                continue

            if event.is_all_day:
                self._all_day_events.append(event)
            else:
                hour = event.start_datetime.hour
                if hour not in self._events_by_hour:
                    self._events_by_hour[hour] = []
                self._events_by_hour[hour].append(event)

    def _build_day(self):
        """بناء عرض اليوم"""
        # تحديث رأس اليوم
        day_index = (self.current_date.weekday() + 1) % 7
        day_name = DAY_NAMES_AR[day_index]
        month_name = MONTH_NAMES_AR[self.current_date.month - 1]

        is_today = self.current_date == date.today()
        today_marker = " (اليوم)" if is_today else ""

        self.date_label.setText(
            f"{day_name}، {self.current_date.day} {month_name} {self.current_date.year}{today_marker}"
        )

        p = get_current_palette()
        if is_today:
            self.date_label.setStyleSheet(f"color: {p['primary']};")
        else:
            self.date_label.setStyleSheet(f"color: {p['text_primary']};")

        # مسح أحداث طوال اليوم
        while self.all_day_layout.count():
            item = self.all_day_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # عرض أحداث طوال اليوم
        if self._all_day_events:
            label = QLabel("طوال اليوم:")
            label.setStyleSheet(f"color: {p['text_muted']}; font-size: 10px;")
            self.all_day_layout.addWidget(label)

            for event in self._all_day_events:
                event_widget = EventItem(event, show_date=False, compact=True)
                event_widget.clicked.connect(self.event_clicked.emit)
                self.all_day_layout.addWidget(event_widget)

        self.all_day_container.setVisible(bool(self._all_day_events))

        # مسح الساعات
        while self.hours_layout.count():
            item = self.hours_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # بناء كتل الساعات
        now = datetime.now()
        current_hour = now.hour if self.current_date == date.today() else -1

        for hour in range(24):
            hour_frame = QFrame()
            hour_layout = QHBoxLayout(hour_frame)
            hour_layout.setContentsMargins(0, 0, 0, 0)
            hour_layout.setSpacing(0)

            # تسمية الوقت
            time_label = QLabel(f"{hour:02d}:00")
            time_label.setFixedWidth(60)
            time_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
            time_label.setStyleSheet(f"""
                QLabel {{
                    color: {p['text_muted']};
                    font-size: 11px;
                    padding-right: 12px;
                    padding-top: 4px;
                }}
            """)
            hour_layout.addWidget(time_label)

            # كتلة الساعة
            block_datetime = datetime.combine(self.current_date, time(hour, 0))
            events_in_hour = self._events_by_hour.get(hour, [])
            is_working = self.work_hours_start <= hour < self.work_hours_end
            is_current = hour == current_hour

            hour_block = HourBlock(
                block_datetime=block_datetime,
                events=events_in_hour,
                is_working_hour=is_working,
                is_current_hour=is_current
            )
            hour_block.clicked.connect(self.time_clicked.emit)
            hour_block.event_clicked.connect(self.event_clicked.emit)
            hour_layout.addWidget(hour_block, 1)

            self.hours_layout.addWidget(hour_frame)

    # ═══════════════════════════════════════════════════════════════
    # Public Methods
    # ═══════════════════════════════════════════════════════════════

    def set_date(self, new_date: date):
        """تغيير التاريخ"""
        self.current_date = new_date
        self._organize_events()
        self._build_day()

    def set_events(self, events: List[CalendarEvent]):
        """تعيين الأحداث"""
        self.events = events
        self._organize_events()
        self._build_day()

    def refresh(self):
        """تحديث العرض"""
        self._organize_events()
        self._build_day()

    def go_previous_day(self):
        """اليوم السابق"""
        self.current_date = self.current_date - timedelta(days=1)
        self._organize_events()
        self._build_day()

    def go_next_day(self):
        """اليوم التالي"""
        self.current_date = self.current_date + timedelta(days=1)
        self._organize_events()
        self._build_day()

    def go_today(self):
        """الذهاب لليوم"""
        self.current_date = date.today()
        self._organize_events()
        self._build_day()
