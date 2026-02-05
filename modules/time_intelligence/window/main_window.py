"""
Time Intelligence Window
========================
Main window for the Time Intelligence module.
Displays comprehensive time context, analytics, and calendar information.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QGroupBox, QGridLayout,
    QPushButton, QComboBox,
)
from PyQt5.QtCore import Qt, QTimer

from ui.windows.base import BaseWindow
from core.logging import app_logger


class TimeIntelligenceWindow(BaseWindow):
    """
    Time Intelligence Module Window.

    Displays:
    - Current time context (Gregorian + Hijri)
    - Working calendar status
    - Upcoming holidays and events
    - Productivity insights
    - Time analytics
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("الوعي الزمني - INTEGRA")
        self.setMinimumSize(1000, 700)

        self._setup_ui()
        self._load_data()

        # Auto-refresh every minute
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_time)
        self._refresh_timer.start(60000)

    def _setup_ui(self):
        """Setup the window UI."""
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Title
        title = QLabel("الوعي الزمني الفائق")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #f59e0b;
            padding: 10px;
            font-family: 'Cairo', sans-serif;
        """)
        main_layout.addWidget(title)

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_widget = QWidget()
        self.content_layout = QVBoxLayout(scroll_widget)
        self.content_layout.setSpacing(15)
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

        # Time Context Section
        self._create_time_section()

        # Work Calendar Section
        self._create_work_section()

        # Upcoming Events Section
        self._create_events_section()

        # Analytics Section
        self._create_analytics_section()

        # Productivity Section
        self._create_productivity_section()

        # Country Selector
        self._create_settings_section()

        self.content_layout.addStretch()

    def _create_section(self, title: str, color: str = "#f59e0b") -> QGroupBox:
        """Create a styled section group box."""
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 16px;
                font-weight: bold;
                color: {color};
                border: 2px solid {color}40;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 20px;
                font-family: 'Cairo', sans-serif;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
            }}
        """)
        self.content_layout.addWidget(group)
        return group

    def _create_info_label(self, key: str, value: str) -> QWidget:
        """Create a key-value info widget."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)

        key_label = QLabel(f"{key}:")
        key_label.setStyleSheet("font-size: 13px; color: #9ca3af; font-family: 'Cairo', sans-serif;")
        key_label.setFixedWidth(180)
        key_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        value_label = QLabel(str(value))
        value_label.setObjectName(f"value_{key.replace(' ', '_')}")
        value_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #e5e7eb; font-family: 'Cairo', sans-serif;")
        value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addWidget(value_label)
        layout.addWidget(key_label)
        layout.setDirection(QHBoxLayout.RightToLeft)

        return widget

    def _create_time_section(self):
        """Create the time context section."""
        group = self._create_section("التاريخ والوقت")
        layout = QGridLayout()
        layout.setSpacing(8)
        group.setLayout(layout)

        # Gregorian date
        self.lbl_gregorian = QLabel("---")
        self.lbl_gregorian.setStyleSheet("font-size: 18px; font-weight: bold; color: #e5e7eb; font-family: 'Cairo';")
        self.lbl_gregorian.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_gregorian, 0, 0, 1, 2)

        # Hijri date
        self.lbl_hijri = QLabel("---")
        self.lbl_hijri.setStyleSheet("font-size: 16px; color: #f59e0b; font-family: 'Cairo';")
        self.lbl_hijri.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_hijri, 1, 0, 1, 2)

        # Time
        self.lbl_time = QLabel("--:--")
        self.lbl_time.setStyleSheet("font-size: 28px; font-weight: bold; color: #60a5fa; font-family: 'Cairo';")
        self.lbl_time.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_time, 2, 0, 1, 2)

        # Day info
        self.lbl_day_info = QLabel("---")
        self.lbl_day_info.setStyleSheet("font-size: 13px; color: #9ca3af; font-family: 'Cairo';")
        self.lbl_day_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_day_info, 3, 0, 1, 2)

    def _create_work_section(self):
        """Create the work calendar section."""
        group = self._create_section("حالة العمل", "#10b981")
        layout = QVBoxLayout()
        layout.setSpacing(5)
        group.setLayout(layout)

        self.lbl_work_status = QLabel("---")
        self.lbl_work_status.setStyleSheet("font-size: 16px; font-weight: bold; font-family: 'Cairo';")
        self.lbl_work_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_work_status)

        self.lbl_work_hours = QLabel("---")
        self.lbl_work_hours.setStyleSheet("font-size: 13px; color: #9ca3af; font-family: 'Cairo';")
        self.lbl_work_hours.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_work_hours)

        self.lbl_next_working = QLabel("---")
        self.lbl_next_working.setStyleSheet("font-size: 13px; color: #9ca3af; font-family: 'Cairo';")
        self.lbl_next_working.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_next_working)

    def _create_events_section(self):
        """Create the upcoming events section."""
        group = self._create_section("الأحداث القادمة", "#8b5cf6")
        self.events_layout = QVBoxLayout()
        self.events_layout.setSpacing(5)
        group.setLayout(self.events_layout)

        self.lbl_no_events = QLabel("جاري التحميل...")
        self.lbl_no_events.setStyleSheet("font-size: 13px; color: #9ca3af; font-family: 'Cairo';")
        self.lbl_no_events.setAlignment(Qt.AlignCenter)
        self.events_layout.addWidget(self.lbl_no_events)

    def _create_analytics_section(self):
        """Create the analytics section."""
        group = self._create_section("الفترة الحالية", "#3b82f6")
        layout = QGridLayout()
        layout.setSpacing(8)
        group.setLayout(layout)

        self.lbl_quarter = QLabel("---")
        self.lbl_quarter.setStyleSheet("font-size: 14px; color: #e5e7eb; font-family: 'Cairo';")
        self.lbl_quarter.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_quarter, 0, 0)

        self.lbl_fiscal = QLabel("---")
        self.lbl_fiscal.setStyleSheet("font-size: 14px; color: #e5e7eb; font-family: 'Cairo';")
        self.lbl_fiscal.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_fiscal, 0, 1)

        self.lbl_week = QLabel("---")
        self.lbl_week.setStyleSheet("font-size: 14px; color: #e5e7eb; font-family: 'Cairo';")
        self.lbl_week.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_week, 1, 0)

        self.lbl_working_days = QLabel("---")
        self.lbl_working_days.setStyleSheet("font-size: 14px; color: #e5e7eb; font-family: 'Cairo';")
        self.lbl_working_days.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_working_days, 1, 1)

    def _create_productivity_section(self):
        """Create the productivity section."""
        group = self._create_section("الإنتاجية", "#ef4444")
        layout = QVBoxLayout()
        layout.setSpacing(5)
        group.setLayout(layout)

        self.lbl_productivity = QLabel("سيبدأ التعلم مع استخدامك للبرنامج")
        self.lbl_productivity.setStyleSheet("font-size: 13px; color: #9ca3af; font-family: 'Cairo';")
        self.lbl_productivity.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_productivity)

    def _create_settings_section(self):
        """Create settings section."""
        group = self._create_section("الإعدادات", "#6b7280")
        layout = QHBoxLayout()
        layout.setSpacing(10)
        group.setLayout(layout)

        lbl = QLabel("الدولة:")
        lbl.setStyleSheet("font-size: 13px; color: #9ca3af; font-family: 'Cairo';")
        layout.addWidget(lbl)

        self.country_combo = QComboBox()
        self.country_combo.addItem("المملكة العربية السعودية", "SA")
        self.country_combo.addItem("جمهورية مصر العربية", "EG")
        self.country_combo.addItem("الإمارات العربية المتحدة", "AE")
        self.country_combo.setStyleSheet("font-size: 13px; font-family: 'Cairo'; padding: 5px;")
        self.country_combo.currentIndexChanged.connect(self._on_country_changed)
        layout.addWidget(self.country_combo)

        refresh_btn = QPushButton("تحديث")
        refresh_btn.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                font-family: 'Cairo';
                padding: 5px 15px;
                background-color: #f59e0b;
                color: #1f2937;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d97706;
            }
        """)
        refresh_btn.clicked.connect(self._load_data)
        layout.addWidget(refresh_btn)

        layout.addStretch()

    def _load_data(self):
        """Load and display all time intelligence data."""
        try:
            from core.time_intelligence import get_system_time, get_working_calendar
            from core.time_intelligence.hijri_utils import get_upcoming_islamic_events

            st = get_system_time()
            context = st.get_full_context()

            # Gregorian
            greg = context["gregorian"]
            self.lbl_gregorian.setText(
                f"{greg['day_ar']} - {greg['date']}"
            )

            # Hijri
            hijri = context["hijri"]
            self.lbl_hijri.setText(hijri.get("formatted", "---"))

            # Time
            self.lbl_time.setText(greg["time"][:5])

            # Day info
            self.lbl_day_info.setText(
                f"الأسبوع {greg['week']} | {greg['quarter']} | {greg['month_ar']} {greg['year']}"
            )

            # Work status
            country_code = self.country_combo.currentData() or "SA"
            calendar = get_working_calendar(country_code)
            work_ctx = calendar.get_context()

            if work_ctx["is_work_time"]:
                self.lbl_work_status.setText("يوم عمل - داخل ساعات العمل")
                self.lbl_work_status.setStyleSheet(
                    "font-size: 16px; font-weight: bold; color: #10b981; font-family: 'Cairo';"
                )
            elif work_ctx["is_working_day"]:
                self.lbl_work_status.setText("يوم عمل - خارج ساعات العمل")
                self.lbl_work_status.setStyleSheet(
                    "font-size: 16px; font-weight: bold; color: #f59e0b; font-family: 'Cairo';"
                )
            else:
                status = work_ctx["today_status"]
                reason = status.get("reason", "إجازة")
                self.lbl_work_status.setText(f"إجازة: {reason}")
                self.lbl_work_status.setStyleSheet(
                    "font-size: 16px; font-weight: bold; color: #ef4444; font-family: 'Cairo';"
                )

            self.lbl_work_hours.setText(
                f"ساعات العمل: {work_ctx['working_hours']['start']} - {work_ctx['working_hours']['end']}"
            )
            self.lbl_next_working.setText(
                f"يوم العمل القادم: {work_ctx['next_working_day']}"
            )

            # Events
            self._clear_layout(self.events_layout)
            events = []

            # Islamic events
            islamic_events = get_upcoming_islamic_events(count=3)
            events.extend(islamic_events)

            # Country holidays
            upcoming_holidays = work_ctx.get("upcoming_holidays", [])
            for h in upcoming_holidays[:3]:
                events.append({
                    "name": h.get("name_ar", ""),
                    "gregorian_date": h.get("date", ""),
                    "days_away": h.get("days_away", 0),
                })

            # Remove duplicates and sort
            seen = set()
            unique_events = []
            for e in events:
                key = e.get("name", "")
                if key not in seen:
                    seen.add(key)
                    unique_events.append(e)
            unique_events.sort(key=lambda x: x.get("days_away", 999))

            if unique_events:
                for event in unique_events[:5]:
                    days = event.get("days_away", 0)
                    days_text = "اليوم" if days == 0 else f"بعد {days} يوم"
                    event_lbl = QLabel(f"  {event.get('name', '')} - {days_text}")
                    event_lbl.setStyleSheet("font-size: 13px; color: #c4b5fd; font-family: 'Cairo';")
                    event_lbl.setAlignment(Qt.AlignRight)
                    self.events_layout.addWidget(event_lbl)
            else:
                no_events = QLabel("لا توجد أحداث قريبة")
                no_events.setStyleSheet("font-size: 13px; color: #9ca3af; font-family: 'Cairo';")
                no_events.setAlignment(Qt.AlignCenter)
                self.events_layout.addWidget(no_events)

            # Analytics
            fiscal = context["fiscal"]
            self.lbl_quarter.setText(f"الربع: {fiscal['quarter']}")
            self.lbl_fiscal.setText(f"السنة المالية: {fiscal['year']}")
            self.lbl_week.setText(f"الأسبوع: {greg['week']}")

            # Working days in month
            from datetime import date as dt_date
            today = dt_date.today()
            wd_count = calendar.get_working_days_in_month(today.year, today.month)
            self.lbl_working_days.setText(f"أيام العمل هذا الشهر: {wd_count}")

            # Productivity
            from core.time_intelligence import get_productivity_learner
            learner = get_productivity_learner()
            summary = learner.get_productivity_summary()
            if summary.get("total_tasks", 0) > 0:
                self.lbl_productivity.setText(
                    f"المهام: {summary['total_tasks']} | "
                    f"الساعات: {summary.get('total_hours', 0)} | "
                    f"نسبة التأخير: {summary.get('delay_rate', 0)}%"
                )
            else:
                self.lbl_productivity.setText(
                    summary.get("message", "سيبدأ التعلم مع استخدامك للبرنامج")
                )

        except Exception as e:
            app_logger.error(f"Failed to load time intelligence data: {e}")

    def _refresh_time(self):
        """Refresh time display."""
        try:
            from core.time_intelligence import get_system_time
            st = get_system_time()
            self.lbl_time.setText(st.current_time.strftime("%H:%M"))
        except Exception:
            pass

    def _on_country_changed(self, index):
        """Handle country change."""
        self._load_data()

    def _clear_layout(self, layout):
        """Clear all widgets from a layout."""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def closeEvent(self, event):
        """Clean up on close."""
        if hasattr(self, '_refresh_timer'):
            self._refresh_timer.stop()
        event.accept()
