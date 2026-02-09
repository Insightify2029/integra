"""
INTEGRA - Mini Calendar Widget
تقويم مصغر للاختيار السريع
المحور I

التاريخ: 4 فبراير 2026
"""

from datetime import date, datetime, timedelta
from typing import Optional, List, Set
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGridLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from core.themes import get_current_palette, get_font, FONT_SIZE_SMALL, FONT_WEIGHT_BOLD
from .calendar_header import MONTH_NAMES_AR, DAY_NAMES_SHORT_AR


class MiniCalendar(QFrame):
    """تقويم مصغر لاختيار التاريخ"""

    # Signals
    date_selected = pyqtSignal(date)
    date_changed = pyqtSignal(int, int)  # year, month

    def __init__(
        self,
        selected_date: Optional[date] = None,
        highlighted_dates: Optional[Set[date]] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.selected_date = selected_date or date.today()
        self.display_date = self.selected_date
        self.highlighted_dates = highlighted_dates or set()

        self._setup_ui()
        self._build_calendar()

    def _setup_ui(self):
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        p = get_current_palette()
        self.setStyleSheet(f"""
            MiniCalendar {{
                background-color: {p['bg_card']};
                border: 1px solid {p['border']};
                border-radius: 8px;
            }}
        """)
        self.setFixedWidth(240)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        nav_btn_style = f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                font-size: 12px;
                color: {p['text_secondary']};
            }}
            QPushButton:hover {{
                background-color: {p['bg_hover']};
                border-radius: 4px;
            }}
        """

        # رأس التقويم
        header_layout = QHBoxLayout()
        header_layout.setSpacing(4)

        # زر الشهر السابق
        prev_btn = QPushButton("◀")
        prev_btn.setFixedSize(24, 24)
        prev_btn.setStyleSheet(nav_btn_style)
        prev_btn.clicked.connect(self._go_previous_month)
        header_layout.addWidget(prev_btn)

        # عرض الشهر والسنة
        self.month_label = QLabel()
        self.month_label.setFont(get_font(FONT_SIZE_SMALL, FONT_WEIGHT_BOLD))
        self.month_label.setAlignment(Qt.AlignCenter)
        self.month_label.setStyleSheet(f"color: {p['text_primary']};")
        header_layout.addWidget(self.month_label, 1)

        # زر الشهر التالي
        next_btn = QPushButton("▶")
        next_btn.setFixedSize(24, 24)
        next_btn.setStyleSheet(nav_btn_style)
        next_btn.clicked.connect(self._go_next_month)
        header_layout.addWidget(next_btn)

        layout.addLayout(header_layout)

        # أسماء الأيام
        days_layout = QHBoxLayout()
        days_layout.setSpacing(0)
        for day_name in DAY_NAMES_SHORT_AR:
            day_label = QLabel(day_name)
            day_label.setAlignment(Qt.AlignCenter)
            day_label.setStyleSheet(f"color: {p['text_muted']}; font-size: 9px; padding: 4px 0;")
            day_label.setFixedWidth(30)
            days_layout.addWidget(day_label)
        layout.addLayout(days_layout)

        # شبكة الأيام
        self.days_grid = QGridLayout()
        self.days_grid.setSpacing(2)
        layout.addLayout(self.days_grid)

        # زر اليوم
        today_btn = QPushButton("اليوم")
        today_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {p['primary']};
                border: none;
                font-size: 10px;
                padding: 4px;
            }}
            QPushButton:hover {{
                text-decoration: underline;
            }}
        """)
        today_btn.clicked.connect(self._go_today)
        layout.addWidget(today_btn, alignment=Qt.AlignCenter)

    def _build_calendar(self):
        """بناء شبكة الأيام"""
        # تحديث عنوان الشهر
        month_name = MONTH_NAMES_AR[self.display_date.month - 1]
        self.month_label.setText(f"{month_name} {self.display_date.year}")

        # مسح الشبكة الحالية
        while self.days_grid.count():
            item = self.days_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # حساب أول يوم في الشهر
        first_day = self.display_date.replace(day=1)
        # الأحد = 0، السبت = 6
        first_weekday = (first_day.weekday() + 1) % 7

        # حساب آخر يوم في الشهر
        if self.display_date.month == 12:
            last_day = self.display_date.replace(year=self.display_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            last_day = self.display_date.replace(month=self.display_date.month + 1, day=1) - timedelta(days=1)

        # أيام الشهر السابق
        if first_weekday > 0:
            prev_month_last = first_day - timedelta(days=1)
            for i in range(first_weekday):
                day = prev_month_last.day - (first_weekday - i - 1)
                btn = self._create_day_button(day, is_other_month=True)
                self.days_grid.addWidget(btn, 0, i)

        # أيام الشهر الحالي
        row = 0
        col = first_weekday
        for day in range(1, last_day.day + 1):
            current_date = self.display_date.replace(day=day)
            is_today = current_date == date.today()
            is_selected = current_date == self.selected_date
            is_highlighted = current_date in self.highlighted_dates
            is_weekend = col == 5 or col == 6  # الجمعة والسبت

            btn = self._create_day_button(
                day,
                is_today=is_today,
                is_selected=is_selected,
                is_highlighted=is_highlighted,
                is_weekend=is_weekend,
                actual_date=current_date
            )
            self.days_grid.addWidget(btn, row, col)

            col += 1
            if col > 6:
                col = 0
                row += 1

        # أيام الشهر التالي
        if col > 0:
            next_day = 1
            while col <= 6:
                btn = self._create_day_button(next_day, is_other_month=True)
                self.days_grid.addWidget(btn, row, col)
                next_day += 1
                col += 1

    def _create_day_button(
        self,
        day: int,
        is_other_month: bool = False,
        is_today: bool = False,
        is_selected: bool = False,
        is_highlighted: bool = False,
        is_weekend: bool = False,
        actual_date: Optional[date] = None
    ) -> QPushButton:
        """إنشاء زر يوم"""
        btn = QPushButton(str(day))
        btn.setFixedSize(30, 30)
        p = get_current_palette()

        base = f"border: none; border-radius: 15px; font-size: 11px;"
        # تحديد التنسيق
        if is_selected:
            style = f"""
                QPushButton {{
                    background-color: {p['primary']};
                    color: {p['text_on_primary']};
                    {base}
                    font-weight: bold;
                }}
            """
        elif is_today:
            style = f"""
                QPushButton {{
                    background-color: {p['primary_light']};
                    color: {p['primary']};
                    border: 2px solid {p['primary']};
                    border-radius: 15px;
                    font-size: 11px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {p['bg_hover']};
                }}
            """
        elif is_other_month:
            style = f"""
                QPushButton {{
                    background-color: transparent;
                    color: {p['disabled_text']};
                    {base}
                }}
                QPushButton:hover {{
                    background-color: {p['bg_hover']};
                }}
            """
        elif is_highlighted:
            style = f"""
                QPushButton {{
                    background-color: {p['warning']}30;
                    color: {p['warning']};
                    {base}
                }}
                QPushButton:hover {{
                    background-color: {p['warning']}50;
                }}
            """
        elif is_weekend:
            style = f"""
                QPushButton {{
                    background-color: transparent;
                    color: {p['danger']};
                    {base}
                }}
                QPushButton:hover {{
                    background-color: {p['danger']}15;
                }}
            """
        else:
            style = f"""
                QPushButton {{
                    background-color: transparent;
                    color: {p['text_primary']};
                    {base}
                }}
                QPushButton:hover {{
                    background-color: {p['bg_hover']};
                }}
            """

        btn.setStyleSheet(style)

        # ربط الحدث
        if actual_date and not is_other_month:
            btn.clicked.connect(lambda checked, d=actual_date: self._on_date_clicked(d))

        return btn

    def _on_date_clicked(self, clicked_date: date):
        """عند النقر على تاريخ"""
        self.selected_date = clicked_date
        self._build_calendar()
        self.date_selected.emit(clicked_date)

    def _go_previous_month(self):
        """الذهاب للشهر السابق"""
        if self.display_date.month == 1:
            self.display_date = self.display_date.replace(year=self.display_date.year - 1, month=12)
        else:
            self.display_date = self.display_date.replace(month=self.display_date.month - 1)
        self._build_calendar()
        self.date_changed.emit(self.display_date.year, self.display_date.month)

    def _go_next_month(self):
        """الذهاب للشهر التالي"""
        if self.display_date.month == 12:
            self.display_date = self.display_date.replace(year=self.display_date.year + 1, month=1)
        else:
            self.display_date = self.display_date.replace(month=self.display_date.month + 1)
        self._build_calendar()
        self.date_changed.emit(self.display_date.year, self.display_date.month)

    def _go_today(self):
        """الذهاب لليوم"""
        self.selected_date = date.today()
        self.display_date = date.today()
        self._build_calendar()
        self.date_selected.emit(self.selected_date)

    def set_selected_date(self, new_date: date):
        """تعيين التاريخ المحدد"""
        self.selected_date = new_date
        self.display_date = new_date
        self._build_calendar()

    def set_highlighted_dates(self, dates: Set[date]):
        """تعيين التواريخ المميزة"""
        self.highlighted_dates = dates
        self._build_calendar()
