"""
INTEGRA - Month View
العرض الشهري للتقويم
المحور I

التاريخ: 4 فبراير 2026
"""

from datetime import date, datetime, timedelta
from typing import Optional, List, Dict
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QGridLayout, QSizePolicy, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from ..models import CalendarEvent, DayEvents, PublicHoliday
from ..widgets.day_cell import DayCell
from ..widgets.calendar_header import DAY_NAMES_AR


class MonthView(QWidget):
    """العرض الشهري للتقويم"""

    # Signals
    date_selected = pyqtSignal(date)
    date_double_clicked = pyqtSignal(date)
    event_clicked = pyqtSignal(CalendarEvent)
    event_double_clicked = pyqtSignal(CalendarEvent)

    def __init__(
        self,
        current_date: Optional[date] = None,
        events: Optional[List[CalendarEvent]] = None,
        holidays: Optional[List[PublicHoliday]] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.current_date = current_date or date.today()
        self.events = events or []
        self.holidays = holidays or []
        self.selected_date: Optional[date] = None

        self._events_by_date: Dict[date, List[CalendarEvent]] = {}
        self._holidays_by_date: Dict[date, PublicHoliday] = {}
        self._day_cells: Dict[date, DayCell] = {}

        self._setup_ui()
        self._organize_events()
        self._build_calendar()

    def _setup_ui(self):
        self.setStyleSheet("background-color: white;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # رأس الأيام
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-bottom: 1px solid #e0e0e0;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 8, 0, 8)
        header_layout.setSpacing(0)

        for day_name in DAY_NAMES_AR:
            day_label = QLabel(day_name)
            day_label.setAlignment(Qt.AlignCenter)
            day_label.setStyleSheet("""
                QLabel {
                    color: #7f8c8d;
                    font-family: Cairo;
                    font-size: 11px;
                    font-weight: bold;
                }
            """)
            day_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            header_layout.addWidget(day_label)

        layout.addWidget(header)

        # شبكة الأيام
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(0)

        layout.addWidget(self.grid_container, 1)

    def _organize_events(self):
        """تنظيم الأحداث حسب التاريخ"""
        self._events_by_date.clear()
        self._holidays_by_date.clear()

        # تنظيم الأحداث
        for event in self.events:
            if event.start_datetime:
                event_date = event.start_datetime.date()
                if event_date not in self._events_by_date:
                    self._events_by_date[event_date] = []
                self._events_by_date[event_date].append(event)

        # تنظيم العطلات
        for holiday in self.holidays:
            if holiday.holiday_date:
                self._holidays_by_date[holiday.holiday_date] = holiday

    def _build_calendar(self):
        """بناء شبكة التقويم"""
        # مسح الشبكة الحالية
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self._day_cells.clear()

        # حساب أول يوم في الشهر
        first_day = self.current_date.replace(day=1)
        # الأحد = 0، السبت = 6
        first_weekday = (first_day.weekday() + 1) % 7

        # حساب آخر يوم في الشهر
        if self.current_date.month == 12:
            last_day = self.current_date.replace(year=self.current_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            last_day = self.current_date.replace(month=self.current_date.month + 1, day=1) - timedelta(days=1)

        # تحديد عدد الأسابيع المطلوبة
        total_cells = first_weekday + last_day.day
        num_rows = (total_cells + 6) // 7

        today = date.today()

        # أيام الشهر السابق
        if first_weekday > 0:
            prev_month_last = first_day - timedelta(days=1)
            for i in range(first_weekday):
                day = prev_month_last.day - (first_weekday - i - 1)
                cell_date = prev_month_last.replace(day=day)
                events = self._events_by_date.get(cell_date, [])

                cell = DayCell(
                    cell_date=cell_date,
                    events=events,
                    is_other_month=True,
                    parent=self
                )
                self._connect_cell_signals(cell)
                self.grid_layout.addWidget(cell, 0, i)
                self._day_cells[cell_date] = cell

        # أيام الشهر الحالي
        row = 0
        col = first_weekday
        for day in range(1, last_day.day + 1):
            cell_date = self.current_date.replace(day=day)
            events = self._events_by_date.get(cell_date, [])
            holiday = self._holidays_by_date.get(cell_date)

            is_today = cell_date == today
            is_weekend = col == 5 or col == 6  # الجمعة والسبت
            is_holiday = holiday is not None
            holiday_name = holiday.name_ar or holiday.name if holiday else None

            cell = DayCell(
                cell_date=cell_date,
                events=events,
                is_today=is_today,
                is_weekend=is_weekend,
                is_holiday=is_holiday,
                holiday_name=holiday_name,
                parent=self
            )
            self._connect_cell_signals(cell)
            self.grid_layout.addWidget(cell, row, col)
            self._day_cells[cell_date] = cell

            col += 1
            if col > 6:
                col = 0
                row += 1

        # أيام الشهر التالي
        if col > 0:
            next_month_first = last_day + timedelta(days=1)
            next_day = 1
            while col <= 6:
                cell_date = next_month_first.replace(day=next_day)
                events = self._events_by_date.get(cell_date, [])

                cell = DayCell(
                    cell_date=cell_date,
                    events=events,
                    is_other_month=True,
                    parent=self
                )
                self._connect_cell_signals(cell)
                self.grid_layout.addWidget(cell, row, col)
                self._day_cells[cell_date] = cell

                next_day += 1
                col += 1

        # ضبط نسب الصفوف
        for i in range(num_rows):
            self.grid_layout.setRowStretch(i, 1)

        for i in range(7):
            self.grid_layout.setColumnStretch(i, 1)

    def _connect_cell_signals(self, cell: DayCell):
        """ربط إشارات الخلية"""
        cell.clicked.connect(self._on_date_clicked)
        cell.double_clicked.connect(self._on_date_double_clicked)
        cell.event_clicked.connect(self._on_event_clicked)

    def _on_date_clicked(self, clicked_date: date):
        """عند النقر على تاريخ"""
        # إلغاء تحديد السابق
        if self.selected_date and self.selected_date in self._day_cells:
            self._day_cells[self.selected_date].highlight(False)

        # تحديد الجديد
        self.selected_date = clicked_date
        if clicked_date in self._day_cells:
            self._day_cells[clicked_date].highlight(True)

        self.date_selected.emit(clicked_date)

    def _on_date_double_clicked(self, clicked_date: date):
        """عند النقر المزدوج على تاريخ"""
        self.date_double_clicked.emit(clicked_date)

    def _on_event_clicked(self, event: CalendarEvent):
        """عند النقر على حدث"""
        self.event_clicked.emit(event)

    # ═══════════════════════════════════════════════════════════════
    # Public Methods
    # ═══════════════════════════════════════════════════════════════

    def set_date(self, new_date: date):
        """تغيير الشهر المعروض"""
        self.current_date = new_date
        self._build_calendar()

    def set_events(self, events: List[CalendarEvent]):
        """تعيين الأحداث"""
        self.events = events
        self._organize_events()
        self._build_calendar()

    def set_holidays(self, holidays: List[PublicHoliday]):
        """تعيين العطلات"""
        self.holidays = holidays
        self._organize_events()
        self._build_calendar()

    def add_event(self, event: CalendarEvent):
        """إضافة حدث"""
        self.events.append(event)
        if event.start_datetime:
            event_date = event.start_datetime.date()
            if event_date not in self._events_by_date:
                self._events_by_date[event_date] = []
            self._events_by_date[event_date].append(event)

            # تحديث الخلية إذا كانت مرئية
            if event_date in self._day_cells:
                self._day_cells[event_date].set_events(self._events_by_date[event_date])

    def remove_event(self, event: CalendarEvent):
        """إزالة حدث"""
        if event in self.events:
            self.events.remove(event)

        if event.start_datetime:
            event_date = event.start_datetime.date()
            if event_date in self._events_by_date and event in self._events_by_date[event_date]:
                self._events_by_date[event_date].remove(event)

                # تحديث الخلية إذا كانت مرئية
                if event_date in self._day_cells:
                    self._day_cells[event_date].set_events(self._events_by_date[event_date])

    def refresh(self):
        """تحديث العرض"""
        self._organize_events()
        self._build_calendar()

    def go_previous_month(self):
        """الذهاب للشهر السابق"""
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12, day=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month - 1, day=1)
        self._build_calendar()

    def go_next_month(self):
        """الذهاب للشهر التالي"""
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1, day=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month + 1, day=1)
        self._build_calendar()

    def go_today(self):
        """الذهاب لليوم"""
        self.current_date = date.today()
        self._build_calendar()

    def get_visible_date_range(self) -> tuple:
        """الحصول على نطاق التواريخ المرئية"""
        first_day = self.current_date.replace(day=1)
        first_weekday = (first_day.weekday() + 1) % 7

        # أول يوم مرئي
        start = first_day - timedelta(days=first_weekday)

        # آخر يوم في الشهر
        if self.current_date.month == 12:
            last_day = self.current_date.replace(year=self.current_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            last_day = self.current_date.replace(month=self.current_date.month + 1, day=1) - timedelta(days=1)

        # آخر يوم مرئي
        total_cells = first_weekday + last_day.day
        remaining = (7 - (total_cells % 7)) % 7
        end = last_day + timedelta(days=remaining)

        return start, end
