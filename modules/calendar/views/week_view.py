"""
INTEGRA - Week View
العرض الأسبوعي للتقويم
المحور I

التاريخ: 4 فبراير 2026
"""

from datetime import date, datetime, time, timedelta
from typing import Optional, List, Dict
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QGridLayout, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QTime
from PyQt5.QtGui import QFont, QColor

from ..models import CalendarEvent, PublicHoliday
from ..widgets.calendar_header import DAY_NAMES_AR, MONTH_NAMES_AR


class TimeSlotWidget(QFrame):
    """خلية فترة زمنية في العرض الأسبوعي"""

    clicked = pyqtSignal(datetime)
    event_clicked = pyqtSignal(CalendarEvent)

    def __init__(
        self,
        slot_datetime: datetime,
        events: Optional[List[CalendarEvent]] = None,
        is_working_hour: bool = True,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.slot_datetime = slot_datetime
        self.events = events or []
        self.is_working_hour = is_working_hour

        self._setup_ui()

    def _setup_ui(self):
        self.setMinimumHeight(40)
        self.setFrameStyle(QFrame.Box | QFrame.Plain)

        bg_color = "#ffffff" if self.is_working_hour else "#f8f9fa"
        self.setStyleSheet(f"""
            TimeSlotWidget {{
                background-color: {bg_color};
                border: 1px solid #eee;
            }}
            TimeSlotWidget:hover {{
                background-color: #f0f7ff;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(1)

        # عرض الأحداث
        for event in self.events[:2]:  # حد أقصى 2
            event_widget = self._create_event_widget(event)
            layout.addWidget(event_widget)

        if len(self.events) > 2:
            more_label = QLabel(f"+{len(self.events) - 2}")
            more_label.setStyleSheet("color: #7f8c8d; font-size: 9px;")
            more_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(more_label)

        layout.addStretch()

    def _create_event_widget(self, event: CalendarEvent) -> QLabel:
        """إنشاء عنصر حدث"""
        label = QLabel(event.title)
        label.setWordWrap(False)
        label.setToolTip(f"{event.title}\n{event.time_formatted}")

        color = event.color or "#3498db"
        text_color = self._get_contrast_color(color)

        label.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: {text_color};
                border-radius: 2px;
                padding: 2px 4px;
                font-size: 9px;
            }}
        """)

        return label

    def _get_contrast_color(self, hex_color: str) -> str:
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return "#ffffff" if luminance < 0.5 else "#000000"

    def mousePressEvent(self, event):
        self.clicked.emit(self.slot_datetime)
        super().mousePressEvent(event)


class DayColumnHeader(QFrame):
    """رأس عمود اليوم في العرض الأسبوعي"""

    def __init__(
        self,
        day_date: date,
        is_today: bool = False,
        is_weekend: bool = False,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.day_date = day_date
        self.is_today = is_today
        self.is_weekend = is_weekend

        self._setup_ui()

    def _setup_ui(self):
        self.setFixedHeight(60)

        if self.is_today:
            self.setStyleSheet("""
                DayColumnHeader {
                    background-color: #eef7ff;
                    border-bottom: 2px solid #3498db;
                }
            """)
        else:
            self.setStyleSheet("""
                DayColumnHeader {
                    background-color: #f8f9fa;
                    border-bottom: 1px solid #e0e0e0;
                }
            """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setAlignment(Qt.AlignCenter)

        # اسم اليوم
        day_index = (self.day_date.weekday() + 1) % 7
        day_name = DAY_NAMES_AR[day_index]
        name_label = QLabel(day_name)
        name_label.setAlignment(Qt.AlignCenter)

        color = "#e74c3c" if self.is_weekend else "#7f8c8d"
        name_label.setStyleSheet(f"color: {color}; font-size: 10px;")
        layout.addWidget(name_label)

        # رقم اليوم
        day_label = QLabel(str(self.day_date.day))
        day_font = QFont("Cairo", 16)
        day_font.setBold(True)
        day_label.setFont(day_font)
        day_label.setAlignment(Qt.AlignCenter)

        if self.is_today:
            day_label.setStyleSheet("""
                QLabel {
                    background-color: #3498db;
                    color: white;
                    border-radius: 16px;
                    min-width: 32px;
                    max-width: 32px;
                    min-height: 32px;
                    max-height: 32px;
                }
            """)
        elif self.is_weekend:
            day_label.setStyleSheet("color: #e74c3c;")
        else:
            day_label.setStyleSheet("color: #2c3e50;")

        layout.addWidget(day_label, alignment=Qt.AlignCenter)


class WeekView(QWidget):
    """العرض الأسبوعي للتقويم"""

    # Signals
    time_slot_clicked = pyqtSignal(datetime)
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

        self._events_by_datetime: Dict[datetime, List[CalendarEvent]] = {}

        self._setup_ui()
        self._organize_events()
        self._build_week()

    def _setup_ui(self):
        self.setStyleSheet("background-color: white;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # رأس الأسبوع
        self.header = QFrame()
        self.header_layout = QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(60, 0, 0, 0)  # مسافة لعمود الوقت
        self.header_layout.setSpacing(0)
        layout.addWidget(self.header)

        # منطقة التمرير للشبكة
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(0)

        scroll.setWidget(self.grid_container)
        layout.addWidget(scroll, 1)

    def _get_week_start(self) -> date:
        """الحصول على بداية الأسبوع (الأحد)"""
        days_since_sunday = (self.current_date.weekday() + 1) % 7
        return self.current_date - timedelta(days=days_since_sunday)

    def _organize_events(self):
        """تنظيم الأحداث حسب التاريخ والوقت"""
        self._events_by_datetime.clear()

        for event in self.events:
            if event.start_datetime and not event.is_all_day:
                # تقريب إلى بداية الساعة
                slot_time = event.start_datetime.replace(minute=0, second=0, microsecond=0)
                if slot_time not in self._events_by_datetime:
                    self._events_by_datetime[slot_time] = []
                self._events_by_datetime[slot_time].append(event)

    def _build_week(self):
        """بناء شبكة الأسبوع"""
        # مسح المحتوى الحالي
        while self.header_layout.count():
            item = self.header_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        week_start = self._get_week_start()
        today = date.today()

        # بناء رأس الأسبوع
        for day_offset in range(7):
            day_date = week_start + timedelta(days=day_offset)
            is_today = day_date == today
            is_weekend = day_offset == 5 or day_offset == 6  # الجمعة والسبت

            header = DayColumnHeader(day_date, is_today, is_weekend)
            self.header_layout.addWidget(header)

        # بناء شبكة الوقت
        hours = list(range(24))

        for row, hour in enumerate(hours):
            # عمود الوقت
            time_label = QLabel(f"{hour:02d}:00")
            time_label.setFixedWidth(60)
            time_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
            time_label.setStyleSheet("""
                QLabel {
                    color: #7f8c8d;
                    font-size: 10px;
                    padding-right: 8px;
                    padding-top: 2px;
                }
            """)
            self.grid_layout.addWidget(time_label, row, 0)

            # خلايا الأيام
            for col in range(7):
                day_date = week_start + timedelta(days=col)
                slot_time = datetime.combine(day_date, time(hour, 0))

                events_in_slot = self._events_by_datetime.get(slot_time, [])
                is_working = self.work_hours_start <= hour < self.work_hours_end

                slot_widget = TimeSlotWidget(
                    slot_datetime=slot_time,
                    events=events_in_slot,
                    is_working_hour=is_working
                )
                slot_widget.clicked.connect(self.time_slot_clicked.emit)
                slot_widget.event_clicked.connect(self.event_clicked.emit)

                self.grid_layout.addWidget(slot_widget, row, col + 1)

        # ضبط نسب الأعمدة
        self.grid_layout.setColumnStretch(0, 0)  # عمود الوقت
        for i in range(1, 8):
            self.grid_layout.setColumnStretch(i, 1)

    # ═══════════════════════════════════════════════════════════════
    # Public Methods
    # ═══════════════════════════════════════════════════════════════

    def set_date(self, new_date: date):
        """تغيير التاريخ"""
        self.current_date = new_date
        self._build_week()

    def set_events(self, events: List[CalendarEvent]):
        """تعيين الأحداث"""
        self.events = events
        self._organize_events()
        self._build_week()

    def refresh(self):
        """تحديث العرض"""
        self._organize_events()
        self._build_week()

    def go_previous_week(self):
        """الأسبوع السابق"""
        self.current_date = self.current_date - timedelta(weeks=1)
        self._build_week()

    def go_next_week(self):
        """الأسبوع التالي"""
        self.current_date = self.current_date + timedelta(weeks=1)
        self._build_week()

    def go_today(self):
        """الذهاب لليوم"""
        self.current_date = date.today()
        self._build_week()

    def get_visible_date_range(self) -> tuple:
        """الحصول على نطاق التواريخ المرئية"""
        week_start = self._get_week_start()
        week_end = week_start + timedelta(days=6)
        return week_start, week_end
