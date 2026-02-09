"""
INTEGRA - Task Form Widget
نموذج المهمة
المحور H

التاريخ: 4 فبراير 2026
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QTextEdit, QComboBox,
    QPushButton, QDateTimeEdit, QCheckBox, QFrame,
    QScrollArea, QWidget, QSpinBox, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QDateTime
from PyQt5.QtGui import QFont

from datetime import datetime, timedelta
from typing import Optional

from ..models import (
    Task, TaskStatus, TaskPriority, TaskCategory,
    RecurrencePattern, RecurrenceType
)
from core.themes import get_current_palette, get_font, FONT_SIZE_BODY


class TaskFormDialog(QDialog):
    """
    نافذة إنشاء/تعديل مهمة

    تسمح بإدخال كل تفاصيل المهمة.
    """

    task_saved = pyqtSignal(Task)

    def __init__(self, task: Optional[Task] = None, parent=None):
        super().__init__(parent)
        self.task = task or Task()
        self.is_edit_mode = task is not None and task.id is not None
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("تعديل المهمة" if self.is_edit_mode else "مهمة جديدة")
        self.setMinimumSize(500, 600)
        self.setMaximumWidth(600)
        self.setLayoutDirection(Qt.RightToLeft)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Scroll area for form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(16)

        # ═══════════════════════════════════════════════════════════════
        # Basic Info
        # ═══════════════════════════════════════════════════════════════
        basic_group = QGroupBox("المعلومات الأساسية")
        basic_layout = QFormLayout(basic_group)
        basic_layout.setSpacing(12)

        # Title
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("عنوان المهمة...")
        self.title_input.setFixedHeight(40)
        self._style_input(self.title_input)
        basic_layout.addRow("العنوان *:", self.title_input)

        # Description
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("وصف المهمة (اختياري)...")
        self.desc_input.setFixedHeight(80)
        self._style_input(self.desc_input)
        basic_layout.addRow("الوصف:", self.desc_input)

        # Status
        self.status_combo = QComboBox()
        self.status_combo.setFixedHeight(36)
        for status in TaskStatus:
            self.status_combo.addItem(status.label_ar, status.value)
        self._style_combo(self.status_combo)
        basic_layout.addRow("الحالة:", self.status_combo)

        # Priority
        self.priority_combo = QComboBox()
        self.priority_combo.setFixedHeight(36)
        for priority in TaskPriority:
            self.priority_combo.addItem(priority.label_ar, priority.value)
        self._style_combo(self.priority_combo)
        basic_layout.addRow("الأولوية:", self.priority_combo)

        # Category
        self.category_combo = QComboBox()
        self.category_combo.setFixedHeight(36)
        self.category_combo.addItem("-- اختر التصنيف --", None)
        for category in TaskCategory:
            self.category_combo.addItem(category.label_ar, category.value)
        self._style_combo(self.category_combo)
        basic_layout.addRow("التصنيف:", self.category_combo)

        form_layout.addWidget(basic_group)

        # ═══════════════════════════════════════════════════════════════
        # Dates
        # ═══════════════════════════════════════════════════════════════
        dates_group = QGroupBox("التواريخ")
        dates_layout = QFormLayout(dates_group)
        dates_layout.setSpacing(12)

        # Due date
        self.due_date_input = QDateTimeEdit()
        self.due_date_input.setCalendarPopup(True)
        self.due_date_input.setDisplayFormat("yyyy-MM-dd hh:mm")
        self.due_date_input.setFixedHeight(36)
        self.due_date_input.setDateTime(QDateTime.currentDateTime().addDays(1))
        self._style_input(self.due_date_input)

        self.due_date_check = QCheckBox("تحديد موعد استحقاق")
        self.due_date_check.stateChanged.connect(
            lambda: self.due_date_input.setEnabled(self.due_date_check.isChecked())
        )
        self.due_date_input.setEnabled(False)

        due_layout = QHBoxLayout()
        due_layout.addWidget(self.due_date_check)
        due_layout.addWidget(self.due_date_input, 1)
        dates_layout.addRow("الاستحقاق:", due_layout)

        # Reminder date
        self.reminder_date_input = QDateTimeEdit()
        self.reminder_date_input.setCalendarPopup(True)
        self.reminder_date_input.setDisplayFormat("yyyy-MM-dd hh:mm")
        self.reminder_date_input.setFixedHeight(36)
        self._style_input(self.reminder_date_input)

        self.reminder_check = QCheckBox("تذكير")
        self.reminder_check.stateChanged.connect(
            lambda: self.reminder_date_input.setEnabled(self.reminder_check.isChecked())
        )
        self.reminder_date_input.setEnabled(False)

        reminder_layout = QHBoxLayout()
        reminder_layout.addWidget(self.reminder_check)
        reminder_layout.addWidget(self.reminder_date_input, 1)
        dates_layout.addRow("التذكير:", reminder_layout)

        form_layout.addWidget(dates_group)

        # ═══════════════════════════════════════════════════════════════
        # Recurrence
        # ═══════════════════════════════════════════════════════════════
        recurrence_group = QGroupBox("التكرار")
        recurrence_layout = QVBoxLayout(recurrence_group)
        recurrence_layout.setSpacing(12)

        self.recurring_check = QCheckBox("مهمة متكررة")
        self.recurring_check.stateChanged.connect(self._toggle_recurrence)
        recurrence_layout.addWidget(self.recurring_check)

        # Recurrence options (hidden by default)
        self.recurrence_frame = QFrame()
        rec_form = QFormLayout(self.recurrence_frame)
        rec_form.setSpacing(8)

        self.rec_type_combo = QComboBox()
        self.rec_type_combo.setFixedHeight(36)
        for rec_type in RecurrenceType:
            self.rec_type_combo.addItem(rec_type.label_ar, rec_type.value)
        self._style_combo(self.rec_type_combo)
        rec_form.addRow("نوع التكرار:", self.rec_type_combo)

        self.rec_interval_spin = QSpinBox()
        self.rec_interval_spin.setMinimum(1)
        self.rec_interval_spin.setMaximum(99)
        self.rec_interval_spin.setValue(1)
        self.rec_interval_spin.setFixedHeight(36)
        rec_form.addRow("كل:", self.rec_interval_spin)

        self.recurrence_frame.hide()
        recurrence_layout.addWidget(self.recurrence_frame)

        form_layout.addWidget(recurrence_group)

        form_layout.addStretch()

        scroll.setWidget(form_widget)
        layout.addWidget(scroll, 1)

        # ═══════════════════════════════════════════════════════════════
        # Buttons
        # ═══════════════════════════════════════════════════════════════
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)

        p = get_current_palette()
        self.cancel_btn = QPushButton("إلغاء")
        self.cancel_btn.setFixedHeight(40)
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {p['bg_main']};
                color: {p['text_secondary']};
                border: 1px solid {p['border']};
                border-radius: 6px;
                padding: 0 24px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {p['bg_hover']};
            }}
        """)
        buttons_layout.addWidget(self.cancel_btn)

        buttons_layout.addStretch()

        self.save_btn = QPushButton("💾 حفظ")
        self.save_btn.setFixedHeight(40)
        self.save_btn.clicked.connect(self._save)
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {p['primary']};
                color: {p['text_on_primary']};
                border: none;
                border-radius: 6px;
                padding: 0 32px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {p['primary_hover']};
            }}
        """)
        buttons_layout.addWidget(self.save_btn)

        layout.addLayout(buttons_layout)

    def _style_input(self, widget):
        """تنسيق حقل الإدخال"""
        p = get_current_palette()
        widget.setStyleSheet(f"""
            QLineEdit, QTextEdit, QDateTimeEdit, QSpinBox {{
                border: 1px solid {p['border']};
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
                background-color: {p['bg_card']};
            }}
            QLineEdit:focus, QTextEdit:focus, QDateTimeEdit:focus {{
                border-color: {p['border_focus']};
            }}
        """)

    def _style_combo(self, combo):
        """تنسيق ComboBox"""
        p = get_current_palette()
        combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {p['border']};
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
                background-color: {p['bg_card']};
            }}
            QComboBox:hover {{
                border-color: {p['border_focus']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
        """)

    def _toggle_recurrence(self):
        """تبديل عرض خيارات التكرار"""
        self.recurrence_frame.setVisible(self.recurring_check.isChecked())

    def _load_data(self):
        """تحميل بيانات المهمة للتعديل"""
        if not self.is_edit_mode:
            return

        self.title_input.setText(self.task.title)
        self.desc_input.setPlainText(self.task.description or "")

        # Status
        index = self.status_combo.findData(self.task.status.value)
        if index >= 0:
            self.status_combo.setCurrentIndex(index)

        # Priority
        index = self.priority_combo.findData(self.task.priority.value)
        if index >= 0:
            self.priority_combo.setCurrentIndex(index)

        # Category
        if self.task.category:
            index = self.category_combo.findData(self.task.category)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)

        # Due date
        if self.task.due_date:
            self.due_date_check.setChecked(True)
            self.due_date_input.setDateTime(
                QDateTime(self.task.due_date)
            )

        # Reminder
        if self.task.reminder_date:
            self.reminder_check.setChecked(True)
            self.reminder_date_input.setDateTime(
                QDateTime(self.task.reminder_date)
            )

        # Recurrence
        if self.task.is_recurring and self.task.recurrence_pattern:
            self.recurring_check.setChecked(True)
            index = self.rec_type_combo.findData(
                self.task.recurrence_pattern.type.value
            )
            if index >= 0:
                self.rec_type_combo.setCurrentIndex(index)
            self.rec_interval_spin.setValue(
                self.task.recurrence_pattern.interval
            )

    def _validate(self) -> bool:
        """التحقق من صحة البيانات"""
        # Reset any previous error styling
        self._style_input(self.title_input)

        title = self.title_input.text().strip()
        if not title:
            p = get_current_palette()
            self.title_input.setFocus()
            self.title_input.setStyleSheet(f"""
                QLineEdit, QTextEdit, QDateTimeEdit, QSpinBox {{
                    border: 1px solid {p['danger']};
                    border-radius: 6px;
                    padding: 8px;
                    font-size: 13px;
                    background-color: {p['bg_card']};
                }}
                QLineEdit:focus, QTextEdit:focus, QDateTimeEdit:focus {{
                    border-color: {p['danger']};
                }}
            """)
            return False
        return True

    def _save(self):
        """حفظ المهمة"""
        if not self._validate():
            return

        # Update task object
        self.task.title = self.title_input.text().strip()
        self.task.description = self.desc_input.toPlainText().strip() or None
        self.task.status = TaskStatus(self.status_combo.currentData())
        self.task.priority = TaskPriority(self.priority_combo.currentData())
        self.task.category = self.category_combo.currentData()

        # Due date
        if self.due_date_check.isChecked():
            self.task.due_date = self.due_date_input.dateTime().toPyDateTime()
        else:
            self.task.due_date = None

        # Reminder
        if self.reminder_check.isChecked():
            self.task.reminder_date = self.reminder_date_input.dateTime().toPyDateTime()
        else:
            self.task.reminder_date = None

        # Recurrence
        if self.recurring_check.isChecked():
            self.task.is_recurring = True
            self.task.recurrence_pattern = RecurrencePattern(
                type=RecurrenceType(self.rec_type_combo.currentData()),
                interval=self.rec_interval_spin.value()
            )
        else:
            self.task.is_recurring = False
            self.task.recurrence_pattern = None

        self.task_saved.emit(self.task)
        self.accept()

    def get_task(self) -> Task:
        """الحصول على المهمة"""
        return self.task


class QuickTaskInput(QFrame):
    """
    إدخال مهمة سريع

    حقل إدخال بسيط لإنشاء مهمة سريعة.
    """

    task_created = pyqtSignal(Task)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setObjectName("quickTaskInput")
        self.setFixedHeight(50)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Input
        p = get_current_palette()
        self.input = QLineEdit()
        self.input.setPlaceholderText("➕ أضف مهمة جديدة...")
        self.input.setFixedHeight(36)
        self.input.returnPressed.connect(self._create_task)
        self.input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {p['border']};
                border-radius: 6px;
                padding: 0 12px;
                font-size: 14px;
                background-color: {p['bg_card']};
            }}
            QLineEdit:focus {{
                border-color: {p['border_focus']};
            }}
        """)
        layout.addWidget(self.input, 1)

        # Priority selector
        self.priority_combo = QComboBox()
        self.priority_combo.setFixedSize(100, 36)
        for priority in TaskPriority:
            self.priority_combo.addItem(priority.label_ar, priority.value)
        # Default to normal
        self.priority_combo.setCurrentIndex(2)
        self.priority_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {p['border']};
                border-radius: 6px;
                padding: 0 8px;
                font-size: 12px;
                background-color: {p['bg_card']};
            }}
        """)
        layout.addWidget(self.priority_combo)

        # Add button
        self.add_btn = QPushButton("إضافة")
        self.add_btn.setFixedSize(80, 36)
        self.add_btn.clicked.connect(self._create_task)
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {p['success']};
                color: {p['text_on_primary']};
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {p['success']}dd;
            }}
        """)
        layout.addWidget(self.add_btn)

        # Frame style
        self.setStyleSheet(f"""
            QFrame#quickTaskInput {{
                background-color: {p['bg_main']};
                border: 1px solid {p['border']};
                border-radius: 8px;
            }}
        """)

    def _create_task(self):
        """إنشاء مهمة من الإدخال"""
        title = self.input.text().strip()
        if not title:
            return

        task = Task(
            title=title,
            status=TaskStatus.PENDING,
            priority=TaskPriority(self.priority_combo.currentData())
        )

        self.task_created.emit(task)
        self.input.clear()
