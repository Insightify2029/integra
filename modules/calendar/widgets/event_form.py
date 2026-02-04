"""
INTEGRA - Event Form Widgets
نماذج إنشاء وتعديل الأحداث
المحور I

التاريخ: 4 فبراير 2026
"""

from datetime import datetime, date, time, timedelta
from typing import Optional, List
from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QPushButton, QComboBox,
    QDateTimeEdit, QCheckBox, QFrame, QGridLayout,
    QSpinBox, QScrollArea, QFormLayout, QDialogButtonBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QDateTime
from PyQt5.QtGui import QFont

from ..models import (
    CalendarEvent, EventType, EventStatus,
    Reminder, ReminderType, RecurrencePattern, RecurrenceType
)


class QuickEventInput(QFrame):
    """إدخال سريع لحدث جديد"""

    event_created = pyqtSignal(CalendarEvent)

    def __init__(
        self,
        default_date: Optional[date] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.default_date = default_date or date.today()

        self._setup_ui()

    def _setup_ui(self):
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.setStyleSheet("""
            QuickEventInput {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # حقل العنوان
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("أضف حدث جديد...")
        self.title_input.setStyleSheet("""
            QLineEdit {
                border: none;
                font-family: Cairo;
                font-size: 13px;
                padding: 4px;
            }
        """)
        self.title_input.returnPressed.connect(self._create_quick_event)
        layout.addWidget(self.title_input, 1)

        # زر الإضافة
        add_btn = QPushButton("+")
        add_btn.setFixedSize(32, 32)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        add_btn.clicked.connect(self._create_quick_event)
        layout.addWidget(add_btn)

    def _create_quick_event(self):
        """إنشاء حدث سريع"""
        title = self.title_input.text().strip()
        if not title:
            return

        # إنشاء حدث افتراضي
        event = CalendarEvent(
            title=title,
            event_type=EventType.EVENT,
            start_datetime=datetime.combine(self.default_date, time(9, 0)),
            end_datetime=datetime.combine(self.default_date, time(10, 0)),
            is_all_day=False
        )

        self.title_input.clear()
        self.event_created.emit(event)

    def set_date(self, new_date: date):
        """تعيين التاريخ الافتراضي"""
        self.default_date = new_date


class EventFormDialog(QDialog):
    """نافذة إنشاء/تعديل حدث"""

    event_saved = pyqtSignal(CalendarEvent)

    def __init__(
        self,
        event: Optional[CalendarEvent] = None,
        default_date: Optional[date] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.event = event
        self.default_date = default_date or date.today()
        self.is_edit_mode = event is not None

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        self.setWindowTitle("تعديل حدث" if self.is_edit_mode else "حدث جديد")
        self.setMinimumWidth(500)
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # رأس النافذة
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: white;
                border-bottom: 1px solid #e0e0e0;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 16, 16, 16)

        title_label = QLabel("تعديل حدث" if self.is_edit_mode else "إضافة حدث جديد")
        title_font = QFont("Cairo", 14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        layout.addWidget(header)

        # منطقة التمرير
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background-color: transparent;")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(16)

        # النموذج
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignRight)

        # العنوان
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("أدخل عنوان الحدث")
        self.title_input.setStyleSheet(self._input_style())
        form_layout.addRow("العنوان *", self.title_input)

        # نوع الحدث
        self.type_combo = QComboBox()
        for event_type in EventType:
            self.type_combo.addItem(f"{event_type.label_ar}", event_type)
        self.type_combo.setStyleSheet(self._input_style())
        form_layout.addRow("النوع", self.type_combo)

        # طوال اليوم
        self.all_day_check = QCheckBox("طوال اليوم")
        self.all_day_check.stateChanged.connect(self._on_all_day_changed)
        form_layout.addRow("", self.all_day_check)

        # تاريخ ووقت البداية
        self.start_datetime = QDateTimeEdit()
        self.start_datetime.setDisplayFormat("yyyy-MM-dd hh:mm AP")
        self.start_datetime.setCalendarPopup(True)
        self.start_datetime.setDateTime(QDateTime.currentDateTime())
        self.start_datetime.setStyleSheet(self._input_style())
        self.start_datetime.dateTimeChanged.connect(self._on_start_changed)
        form_layout.addRow("البداية *", self.start_datetime)

        # تاريخ ووقت النهاية
        self.end_datetime = QDateTimeEdit()
        self.end_datetime.setDisplayFormat("yyyy-MM-dd hh:mm AP")
        self.end_datetime.setCalendarPopup(True)
        self.end_datetime.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self.end_datetime.setStyleSheet(self._input_style())
        form_layout.addRow("النهاية", self.end_datetime)

        # الموقع
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("أدخل الموقع (اختياري)")
        self.location_input.setStyleSheet(self._input_style())
        form_layout.addRow("الموقع", self.location_input)

        # الوصف
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("أدخل وصف الحدث (اختياري)")
        self.description_input.setMaximumHeight(100)
        self.description_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                font-family: Cairo;
                font-size: 12px;
                background-color: white;
            }
            QTextEdit:focus {
                border-color: #3498db;
            }
        """)
        form_layout.addRow("الوصف", self.description_input)

        # التصنيف
        self.category_combo = QComboBox()
        self.category_combo.addItem("بدون تصنيف", "")
        self.category_combo.addItem("🔵 العمل", "work")
        self.category_combo.addItem("🟣 اجتماع", "meeting")
        self.category_combo.addItem("🟢 مهمة", "task")
        self.category_combo.addItem("🟡 تذكير", "reminder")
        self.category_combo.addItem("🟤 شخصي", "personal")
        self.category_combo.setStyleSheet(self._input_style())
        form_layout.addRow("التصنيف", self.category_combo)

        # اللون
        self.color_combo = QComboBox()
        colors = [
            ("#3498db", "أزرق"),
            ("#2ecc71", "أخضر"),
            ("#e74c3c", "أحمر"),
            ("#f39c12", "برتقالي"),
            ("#9b59b6", "بنفسجي"),
            ("#1abc9c", "فيروزي"),
            ("#34495e", "رمادي غامق"),
        ]
        for color, name in colors:
            self.color_combo.addItem(f"● {name}", color)
        self.color_combo.setStyleSheet(self._input_style())
        form_layout.addRow("اللون", self.color_combo)

        # التذكير
        self.reminder_combo = QComboBox()
        reminders = [
            (0, "بدون تذكير"),
            (5, "قبل 5 دقائق"),
            (15, "قبل 15 دقيقة"),
            (30, "قبل 30 دقيقة"),
            (60, "قبل ساعة"),
            (1440, "قبل يوم"),
        ]
        for minutes, label in reminders:
            self.reminder_combo.addItem(label, minutes)
        self.reminder_combo.setCurrentIndex(3)  # 30 دقيقة افتراضياً
        self.reminder_combo.setStyleSheet(self._input_style())
        form_layout.addRow("التذكير", self.reminder_combo)

        # التكرار
        self.recurrence_combo = QComboBox()
        self.recurrence_combo.addItem("لا يتكرر", None)
        self.recurrence_combo.addItem("يومياً", RecurrenceType.DAILY)
        self.recurrence_combo.addItem("أسبوعياً", RecurrenceType.WEEKLY)
        self.recurrence_combo.addItem("شهرياً", RecurrenceType.MONTHLY)
        self.recurrence_combo.addItem("سنوياً", RecurrenceType.YEARLY)
        self.recurrence_combo.setStyleSheet(self._input_style())
        form_layout.addRow("التكرار", self.recurrence_combo)

        content_layout.addLayout(form_layout)
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        # أزرار الإجراءات
        buttons_frame = QFrame()
        buttons_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-top: 1px solid #e0e0e0;
            }
        """)
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setContentsMargins(16, 12, 16, 12)
        buttons_layout.setSpacing(8)

        buttons_layout.addStretch()

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #666;
                border: none;
                border-radius: 4px;
                padding: 8px 24px;
                font-family: Cairo;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        save_btn = QPushButton("حفظ" if self.is_edit_mode else "إضافة")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 24px;
                font-family: Cairo;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        save_btn.clicked.connect(self._save)
        buttons_layout.addWidget(save_btn)

        layout.addWidget(buttons_frame)

    def _input_style(self) -> str:
        return """
            QLineEdit, QComboBox, QDateTimeEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                font-family: Cairo;
                font-size: 12px;
                background-color: white;
            }
            QLineEdit:focus, QComboBox:focus, QDateTimeEdit:focus {
                border-color: #3498db;
            }
        """

    def _load_data(self):
        """تحميل بيانات الحدث للتعديل"""
        if not self.event:
            # تعيين التاريخ الافتراضي
            default_dt = datetime.combine(self.default_date, time(9, 0))
            self.start_datetime.setDateTime(QDateTime(default_dt))
            self.end_datetime.setDateTime(QDateTime(default_dt + timedelta(hours=1)))
            return

        self.title_input.setText(self.event.title)

        # نوع الحدث
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == self.event.event_type:
                self.type_combo.setCurrentIndex(i)
                break

        self.all_day_check.setChecked(self.event.is_all_day)

        if self.event.start_datetime:
            self.start_datetime.setDateTime(QDateTime(self.event.start_datetime))

        if self.event.end_datetime:
            self.end_datetime.setDateTime(QDateTime(self.event.end_datetime))

        if self.event.location:
            self.location_input.setText(self.event.location)

        if self.event.description:
            self.description_input.setPlainText(self.event.description)

        # التصنيف
        if self.event.category:
            for i in range(self.category_combo.count()):
                if self.category_combo.itemData(i) == self.event.category:
                    self.category_combo.setCurrentIndex(i)
                    break

        # اللون
        if self.event.color:
            for i in range(self.color_combo.count()):
                if self.color_combo.itemData(i) == self.event.color:
                    self.color_combo.setCurrentIndex(i)
                    break

    def _on_all_day_changed(self, state: int):
        """عند تغيير خيار طوال اليوم"""
        is_all_day = state == Qt.Checked
        # تغيير تنسيق العرض
        if is_all_day:
            self.start_datetime.setDisplayFormat("yyyy-MM-dd")
            self.end_datetime.setDisplayFormat("yyyy-MM-dd")
        else:
            self.start_datetime.setDisplayFormat("yyyy-MM-dd hh:mm AP")
            self.end_datetime.setDisplayFormat("yyyy-MM-dd hh:mm AP")

    def _on_start_changed(self, dt: QDateTime):
        """عند تغيير وقت البداية"""
        # تحديث وقت النهاية تلقائياً
        if dt > self.end_datetime.dateTime():
            self.end_datetime.setDateTime(dt.addSecs(3600))

    def _save(self):
        """حفظ الحدث"""
        title = self.title_input.text().strip()
        if not title:
            self.title_input.setFocus()
            self.title_input.setStyleSheet(self._input_style() + "border-color: #e74c3c !important;")
            return

        # إنشاء/تحديث الحدث
        if not self.event:
            self.event = CalendarEvent()

        self.event.title = title
        self.event.event_type = self.type_combo.currentData()
        self.event.is_all_day = self.all_day_check.isChecked()
        self.event.start_datetime = self.start_datetime.dateTime().toPyDateTime()
        self.event.end_datetime = self.end_datetime.dateTime().toPyDateTime()
        self.event.location = self.location_input.text().strip() or None
        self.event.description = self.description_input.toPlainText().strip() or None
        self.event.category = self.category_combo.currentData() or None
        self.event.color = self.color_combo.currentData()

        # التذكير
        reminder_minutes = self.reminder_combo.currentData()
        if reminder_minutes and reminder_minutes > 0:
            self.event.reminders = [Reminder(
                type=ReminderType.NOTIFICATION,
                minutes_before=reminder_minutes
            )]
        else:
            self.event.reminders = []

        # التكرار
        recurrence_type = self.recurrence_combo.currentData()
        if recurrence_type:
            self.event.is_recurring = True
            self.event.recurrence_pattern = RecurrencePattern(type=recurrence_type)
        else:
            self.event.is_recurring = False
            self.event.recurrence_pattern = None

        self.event_saved.emit(self.event)
        self.accept()
