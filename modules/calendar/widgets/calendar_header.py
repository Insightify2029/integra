"""
INTEGRA - Calendar Header Widgets
رأس التقويم وشريط الأدوات
المحور I

التاريخ: 4 فبراير 2026
"""

from datetime import date, datetime
from typing import Optional
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QFrame, QComboBox, QButtonGroup
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from ..models import CalendarView


# أسماء الأشهر بالعربي
MONTH_NAMES_AR = [
    "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
    "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
]

# أسماء الأيام بالعربي
DAY_NAMES_AR = ["الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"]
DAY_NAMES_SHORT_AR = ["أحد", "إثن", "ثلا", "أرب", "خمي", "جمع", "سبت"]


class CalendarHeader(QFrame):
    """رأس التقويم - يعرض الشهر والسنة مع أزرار التنقل"""

    # Signals
    previous_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    today_clicked = pyqtSignal()
    date_changed = pyqtSignal(int, int)  # year, month

    def __init__(
        self,
        current_date: Optional[date] = None,
        view_type: CalendarView = CalendarView.MONTH,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.current_date = current_date or date.today()
        self.view_type = view_type

        self._setup_ui()
        self._update_display()

    def _setup_ui(self):
        self.setFrameStyle(QFrame.NoFrame)
        self.setStyleSheet("""
            CalendarHeader {
                background-color: white;
                border-bottom: 1px solid #e0e0e0;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # أزرار التنقل
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(4)

        # زر السابق
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setFixedSize(32, 32)
        self.prev_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.prev_btn.clicked.connect(self.previous_clicked.emit)
        nav_layout.addWidget(self.prev_btn)

        # زر التالي
        self.next_btn = QPushButton("▶")
        self.next_btn.setFixedSize(32, 32)
        self.next_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.next_btn.clicked.connect(self.next_clicked.emit)
        nav_layout.addWidget(self.next_btn)

        layout.addLayout(nav_layout)

        # عرض الشهر والسنة
        self.date_label = QLabel()
        date_font = QFont("Cairo", 16)
        date_font.setBold(True)
        self.date_label.setFont(date_font)
        self.date_label.setStyleSheet("color: #2c3e50;")
        layout.addWidget(self.date_label)

        layout.addStretch()

        # زر اليوم
        self.today_btn = QPushButton("اليوم")
        self.today_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-family: Cairo;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.today_btn.clicked.connect(self.today_clicked.emit)
        layout.addWidget(self.today_btn)

    def _update_display(self):
        """تحديث عرض التاريخ"""
        month_name = MONTH_NAMES_AR[self.current_date.month - 1]
        year = self.current_date.year

        if self.view_type == CalendarView.MONTH:
            self.date_label.setText(f"{month_name} {year}")
        elif self.view_type == CalendarView.WEEK:
            # حساب نطاق الأسبوع
            week_start = self.current_date
            week_end = self.current_date
            # تعديل لبداية الأسبوع
            days_since_sunday = (self.current_date.weekday() + 1) % 7
            week_start = self.current_date.replace(day=self.current_date.day - days_since_sunday)
            week_end = week_start.replace(day=week_start.day + 6)
            self.date_label.setText(f"{week_start.day} - {week_end.day} {month_name} {year}")
        elif self.view_type == CalendarView.DAY:
            day_name = DAY_NAMES_AR[(self.current_date.weekday() + 1) % 7]
            self.date_label.setText(f"{day_name}، {self.current_date.day} {month_name} {year}")
        else:
            self.date_label.setText(f"{month_name} {year}")

    def set_date(self, new_date: date):
        """تغيير التاريخ"""
        self.current_date = new_date
        self._update_display()

    def set_view_type(self, view_type: CalendarView):
        """تغيير نوع العرض"""
        self.view_type = view_type
        self._update_display()

    def go_previous(self):
        """الذهاب للسابق"""
        if self.view_type == CalendarView.MONTH:
            if self.current_date.month == 1:
                self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
            else:
                self.current_date = self.current_date.replace(month=self.current_date.month - 1)
        elif self.view_type == CalendarView.WEEK:
            self.current_date = self.current_date.replace(day=self.current_date.day - 7)
        elif self.view_type == CalendarView.DAY:
            self.current_date = self.current_date.replace(day=self.current_date.day - 1)

        self._update_display()
        self.date_changed.emit(self.current_date.year, self.current_date.month)

    def go_next(self):
        """الذهاب للتالي"""
        if self.view_type == CalendarView.MONTH:
            if self.current_date.month == 12:
                self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
            else:
                self.current_date = self.current_date.replace(month=self.current_date.month + 1)
        elif self.view_type == CalendarView.WEEK:
            self.current_date = self.current_date.replace(day=self.current_date.day + 7)
        elif self.view_type == CalendarView.DAY:
            self.current_date = self.current_date.replace(day=self.current_date.day + 1)

        self._update_display()
        self.date_changed.emit(self.current_date.year, self.current_date.month)

    def go_today(self):
        """الذهاب لليوم"""
        self.current_date = date.today()
        self._update_display()
        self.date_changed.emit(self.current_date.year, self.current_date.month)


class CalendarToolbar(QFrame):
    """شريط أدوات التقويم"""

    # Signals
    view_changed = pyqtSignal(CalendarView)
    add_event_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    refresh_clicked = pyqtSignal()
    category_changed = pyqtSignal(str)  # category name or empty for all

    def __init__(
        self,
        current_view: CalendarView = CalendarView.MONTH,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.current_view = current_view

        self._setup_ui()

    def _setup_ui(self):
        self.setFrameStyle(QFrame.NoFrame)
        self.setStyleSheet("""
            CalendarToolbar {
                background-color: #f8f9fa;
                border-bottom: 1px solid #e0e0e0;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(8)

        # أزرار تبديل العرض
        view_group = QButtonGroup(self)

        views = [
            (CalendarView.MONTH, "شهري"),
            (CalendarView.WEEK, "أسبوعي"),
            (CalendarView.DAY, "يومي"),
            (CalendarView.AGENDA, "قائمة"),
        ]

        for view_type, label in views:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(view_type == self.current_view)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    color: #666;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-family: Cairo;
                    font-size: 11px;
                }
                QPushButton:checked {
                    background-color: #3498db;
                    color: white;
                    border-color: #3498db;
                }
                QPushButton:hover:!checked {
                    background-color: #f0f0f0;
                }
            """)
            btn.clicked.connect(lambda checked, v=view_type: self._on_view_selected(v))
            view_group.addButton(btn)
            layout.addWidget(btn)

        layout.addStretch()

        # فلتر التصنيف
        self.category_combo = QComboBox()
        self.category_combo.addItem("كل التصنيفات", "")
        self.category_combo.addItem("🔵 العمل", "work")
        self.category_combo.addItem("🟣 اجتماع", "meeting")
        self.category_combo.addItem("🟢 مهمة", "task")
        self.category_combo.addItem("🟡 تذكير", "reminder")
        self.category_combo.addItem("🔴 إجازة", "holiday")
        self.category_combo.addItem("🟤 شخصي", "personal")
        self.category_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 6px 12px;
                font-family: Cairo;
                font-size: 11px;
                min-width: 120px;
            }
            QComboBox:hover {
                border-color: #3498db;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        self.category_combo.currentIndexChanged.connect(self._on_category_changed)
        layout.addWidget(self.category_combo)

        # زر التحديث
        refresh_btn = QPushButton("🔄")
        refresh_btn.setToolTip("تحديث")
        refresh_btn.setFixedSize(32, 32)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_clicked.emit)
        layout.addWidget(refresh_btn)

        # زر الإعدادات
        settings_btn = QPushButton("⚙️")
        settings_btn.setToolTip("الإعدادات")
        settings_btn.setFixedSize(32, 32)
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        settings_btn.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(settings_btn)

        # زر إضافة حدث
        add_btn = QPushButton("+ حدث جديد")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-family: Cairo;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        add_btn.clicked.connect(self.add_event_clicked.emit)
        layout.addWidget(add_btn)

    def _on_view_selected(self, view_type: CalendarView):
        """عند اختيار نوع العرض"""
        self.current_view = view_type
        self.view_changed.emit(view_type)

    def _on_category_changed(self, index: int):
        """عند تغيير التصنيف"""
        category = self.category_combo.itemData(index)
        self.category_changed.emit(category or "")

    def set_view(self, view_type: CalendarView):
        """تعيين نوع العرض"""
        self.current_view = view_type
        # تحديث الأزرار
        for btn in self.findChildren(QPushButton):
            if btn.isCheckable():
                # مقارنة النص
                pass  # يمكن تحسين هذا
