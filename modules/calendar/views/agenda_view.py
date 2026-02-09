"""
INTEGRA - Agenda View
عرض قائمة الأحداث (الأجندة)
المحور I

التاريخ: 4 فبراير 2026
"""

from datetime import date, datetime, timedelta
from typing import Optional, List, Dict
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from core.themes import get_current_palette, get_font, FONT_SIZE_SUBTITLE, FONT_SIZE_TITLE, FONT_WEIGHT_BOLD
from ..models import CalendarEvent
from ..widgets.calendar_header import DAY_NAMES_AR, MONTH_NAMES_AR
from ..widgets.event_item import EventItem


class DaySection(QFrame):
    """قسم يوم في عرض الأجندة"""

    event_clicked = pyqtSignal(CalendarEvent)

    def __init__(
        self,
        section_date: date,
        events: List[CalendarEvent],
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.section_date = section_date
        self.events = events

        self._setup_ui()

    def _setup_ui(self):
        p = get_current_palette()
        self.setStyleSheet(f"""
            DaySection {{
                background-color: {p['bg_card']};
                border-bottom: 1px solid {p['border']};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        # عمود التاريخ
        date_container = QFrame()
        date_container.setFixedWidth(80)
        date_layout = QVBoxLayout(date_container)
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.setSpacing(2)

        # اسم اليوم
        day_index = (self.section_date.weekday() + 1) % 7
        day_name = DAY_NAMES_AR[day_index]

        day_label = QLabel(day_name)
        day_label.setAlignment(Qt.AlignCenter)

        is_today = self.section_date == date.today()
        is_weekend = day_index == 5 or day_index == 6

        if is_today:
            day_label.setStyleSheet(f"color: {p['primary']}; font-size: 11px; font-weight: bold;")
        elif is_weekend:
            day_label.setStyleSheet(f"color: {p['danger']}; font-size: 11px;")
        else:
            day_label.setStyleSheet(f"color: {p['text_muted']}; font-size: 11px;")

        date_layout.addWidget(day_label)

        # رقم اليوم
        number_label = QLabel(str(self.section_date.day))
        number_label.setFont(get_font(FONT_SIZE_TITLE, FONT_WEIGHT_BOLD))
        number_label.setAlignment(Qt.AlignCenter)

        if is_today:
            number_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {p['primary']};
                    color: {p['text_on_primary']};
                    border-radius: 20px;
                    min-width: 40px;
                    max-width: 40px;
                    min-height: 40px;
                    max-height: 40px;
                }}
            """)
        elif is_weekend:
            number_label.setStyleSheet(f"color: {p['danger']};")
        else:
            number_label.setStyleSheet(f"color: {p['text_primary']};")

        date_layout.addWidget(number_label, alignment=Qt.AlignCenter)

        # الشهر (إذا كان أول يوم في الشهر أو أول قسم)
        if self.section_date.day == 1:
            month_name = MONTH_NAMES_AR[self.section_date.month - 1]
            month_label = QLabel(month_name)
            month_label.setAlignment(Qt.AlignCenter)
            month_label.setStyleSheet(f"color: {p['text_muted']}; font-size: 10px;")
            date_layout.addWidget(month_label)

        date_layout.addStretch()
        layout.addWidget(date_container)

        # فاصل عمودي
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setStyleSheet(f"background-color: {p['border']};")
        layout.addWidget(separator)

        # عمود الأحداث
        events_container = QWidget()
        events_layout = QVBoxLayout(events_container)
        events_layout.setContentsMargins(0, 0, 0, 0)
        events_layout.setSpacing(8)

        if self.events:
            for event in self.events:
                event_widget = EventItem(event, show_date=False, compact=False)
                event_widget.clicked.connect(self.event_clicked.emit)
                events_layout.addWidget(event_widget)
        else:
            no_events_label = QLabel("لا توجد أحداث")
            no_events_label.setStyleSheet(f"color: {p['text_muted']}; font-style: italic;")
            events_layout.addWidget(no_events_label)

        events_layout.addStretch()
        layout.addWidget(events_container, 1)


class AgendaView(QWidget):
    """عرض قائمة الأحداث (الأجندة)"""

    # Signals
    event_clicked = pyqtSignal(CalendarEvent)
    date_clicked = pyqtSignal(date)

    def __init__(
        self,
        start_date: Optional[date] = None,
        events: Optional[List[CalendarEvent]] = None,
        days_ahead: int = 14,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.start_date = start_date or date.today()
        self.events = events or []
        self.days_ahead = days_ahead

        self._events_by_date: Dict[date, List[CalendarEvent]] = {}

        self._setup_ui()
        self._organize_events()
        self._build_agenda()

    def _setup_ui(self):
        p = get_current_palette()
        self.setStyleSheet(f"background-color: {p['bg_main']};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # رأس الأجندة
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {p['bg_card']};
                border-bottom: 1px solid {p['border']};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)

        title_label = QLabel("الأجندة")
        title_label.setFont(get_font(FONT_SIZE_SUBTITLE, FONT_WEIGHT_BOLD))
        title_label.setStyleSheet(f"color: {p['text_primary']};")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # عداد الأحداث
        self.count_label = QLabel()
        self.count_label.setStyleSheet(f"color: {p['text_muted']}; font-size: 12px;")
        header_layout.addWidget(self.count_label)

        layout.addWidget(header)

        # منطقة التمرير
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background-color: transparent;")

        self.sections_container = QWidget()
        self.sections_layout = QVBoxLayout(self.sections_container)
        self.sections_layout.setContentsMargins(0, 0, 0, 0)
        self.sections_layout.setSpacing(0)

        scroll.setWidget(self.sections_container)
        layout.addWidget(scroll, 1)

    def _organize_events(self):
        """تنظيم الأحداث حسب التاريخ"""
        self._events_by_date.clear()

        for event in self.events:
            if event.start_datetime:
                event_date = event.start_datetime.date()
                # فقط الأحداث في النطاق
                if self.start_date <= event_date < self.start_date + timedelta(days=self.days_ahead):
                    if event_date not in self._events_by_date:
                        self._events_by_date[event_date] = []
                    self._events_by_date[event_date].append(event)

        # ترتيب الأحداث في كل يوم حسب الوقت
        for d in self._events_by_date:
            self._events_by_date[d].sort(
                key=lambda e: e.start_datetime or datetime.min
            )

    def _build_agenda(self):
        """بناء عرض الأجندة"""
        # مسح المحتوى الحالي
        while self.sections_layout.count():
            item = self.sections_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # تحديث العداد
        total_events = sum(len(events) for events in self._events_by_date.values())
        days_with_events = len(self._events_by_date)
        self.count_label.setText(f"{total_events} حدث في {days_with_events} يوم")

        # بناء أقسام الأيام
        current_date = self.start_date
        end_date = self.start_date + timedelta(days=self.days_ahead)

        has_sections = False

        while current_date < end_date:
            events_on_day = self._events_by_date.get(current_date, [])

            # عرض فقط الأيام التي بها أحداث
            if events_on_day:
                section = DaySection(current_date, events_on_day)
                section.event_clicked.connect(self.event_clicked.emit)
                self.sections_layout.addWidget(section)
                has_sections = True

            current_date += timedelta(days=1)

        # رسالة إذا لم تكن هناك أحداث
        if not has_sections:
            empty_label = QLabel("لا توجد أحداث قادمة")
            empty_label.setAlignment(Qt.AlignCenter)
            p = get_current_palette()
            empty_label.setStyleSheet(f"""
                QLabel {{
                    color: {p['text_muted']};
                    font-size: 14px;
                    padding: 40px;
                }}
            """)
            self.sections_layout.addWidget(empty_label)

        self.sections_layout.addStretch()

    # ═══════════════════════════════════════════════════════════════
    # Public Methods
    # ═══════════════════════════════════════════════════════════════

    def set_start_date(self, new_date: date):
        """تغيير تاريخ البداية"""
        self.start_date = new_date
        self._organize_events()
        self._build_agenda()

    def set_events(self, events: List[CalendarEvent]):
        """تعيين الأحداث"""
        self.events = events
        self._organize_events()
        self._build_agenda()

    def set_days_ahead(self, days: int):
        """تعيين عدد الأيام المعروضة"""
        self.days_ahead = days
        self._organize_events()
        self._build_agenda()

    def refresh(self):
        """تحديث العرض"""
        self._organize_events()
        self._build_agenda()

    def go_today(self):
        """الذهاب لليوم"""
        self.start_date = date.today()
        self._organize_events()
        self._build_agenda()

    def get_visible_date_range(self) -> tuple:
        """الحصول على نطاق التواريخ المرئية"""
        return self.start_date, self.start_date + timedelta(days=self.days_ahead)
