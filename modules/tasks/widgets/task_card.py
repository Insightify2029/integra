"""
INTEGRA - Task Card Widget
بطاقة المهمة
المحور H

التاريخ: 4 فبراير 2026
"""

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QMenu, QAction, QProgressBar,
    QSizePolicy, QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QCursor

from ..models import Task, TaskStatus, TaskPriority
from core.themes import get_current_palette, get_font, FONT_SIZE_BODY, FONT_SIZE_SMALL, FONT_SIZE_TINY, FONT_WEIGHT_BOLD


class TaskCard(QFrame):
    """
    بطاقة عرض المهمة

    تعرض معلومات المهمة بشكل مختصر مع إجراءات سريعة.
    """

    # Signals
    clicked = pyqtSignal(int)           # task_id
    status_changed = pyqtSignal(int, str)  # task_id, new_status
    priority_changed = pyqtSignal(int, str)  # task_id, new_priority
    edit_requested = pyqtSignal(int)    # task_id
    delete_requested = pyqtSignal(int)  # task_id

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self.task = task
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setObjectName("taskCard")
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setMinimumHeight(100)
        self.setMaximumHeight(150)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(8)

        # Header: Priority indicator + Title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # Priority indicator
        self.priority_indicator = QFrame()
        self.priority_indicator.setFixedSize(4, 40)
        self.priority_indicator.setStyleSheet(
            f"background-color: {self.task.priority.color}; border-radius: 2px;"
        )
        header_layout.addWidget(self.priority_indicator)

        # Title and category
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)

        p = get_current_palette()

        self.title_label = QLabel(self.task.title)
        self.title_label.setFont(get_font(FONT_SIZE_BODY, FONT_WEIGHT_BOLD))
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumHeight(44)
        title_layout.addWidget(self.title_label)

        if self.task.category_ar:
            self.category_label = QLabel(self.task.category_ar)
            self.category_label.setFont(get_font(FONT_SIZE_TINY))
            self.category_label.setStyleSheet(
                f"color: {self.task.category_color or p['text_muted']};"
            )
            title_layout.addWidget(self.category_label)

        header_layout.addLayout(title_layout, 1)

        # Status menu button
        self.status_btn = QPushButton(self.task.status_label)
        self.status_btn.setFixedHeight(28)
        self.status_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.status_btn.clicked.connect(self._show_status_menu)
        self._style_status_button()
        header_layout.addWidget(self.status_btn)

        main_layout.addLayout(header_layout)

        # Info row: Due date + Progress
        info_layout = QHBoxLayout()
        info_layout.setSpacing(16)

        # Due date
        if self.task.due_date:
            due_text = self.task.due_date_formatted
            due_color = p['danger'] if self.task.is_overdue else p['text_muted']
            self.due_label = QLabel(f"📅 {due_text}")
            self.due_label.setFont(get_font(FONT_SIZE_TINY))
            self.due_label.setStyleSheet(f"color: {due_color};")
            info_layout.addWidget(self.due_label)

        # Checklist progress
        if self.task.checklist_count > 0:
            progress_text = f"✓ {self.task.checklist_completed}/{self.task.checklist_count}"
            self.progress_label = QLabel(progress_text)
            self.progress_label.setFont(get_font(FONT_SIZE_TINY))
            self.progress_label.setStyleSheet(f"color: {p['text_muted']};")
            info_layout.addWidget(self.progress_label)

        # Attachments count
        if self.task.attachments_count > 0:
            self.attachments_label = QLabel(f"📎 {self.task.attachments_count}")
            self.attachments_label.setFont(get_font(FONT_SIZE_TINY))
            self.attachments_label.setStyleSheet(f"color: {p['text_muted']};")
            info_layout.addWidget(self.attachments_label)

        # Comments count
        if self.task.comments_count > 0:
            self.comments_label = QLabel(f"💬 {self.task.comments_count}")
            self.comments_label.setFont(get_font(FONT_SIZE_TINY))
            self.comments_label.setStyleSheet(f"color: {p['text_muted']};")
            info_layout.addWidget(self.comments_label)

        # Recurring indicator
        if self.task.is_recurring:
            self.recurring_label = QLabel("🔄")
            self.recurring_label.setToolTip("مهمة متكررة")
            info_layout.addWidget(self.recurring_label)

        info_layout.addStretch()

        # Priority label
        self.priority_label = QLabel(self.task.priority_label)
        self.priority_label.setFont(get_font(FONT_SIZE_TINY))
        self.priority_label.setStyleSheet(
            f"color: {self.task.priority.color}; font-weight: bold;"
        )
        self.priority_label.setCursor(QCursor(Qt.PointingHandCursor))
        self.priority_label.mousePressEvent = lambda e: self._show_priority_menu()
        info_layout.addWidget(self.priority_label)

        main_layout.addLayout(info_layout)

        # Progress bar for checklist
        if self.task.checklist_count > 0:
            self.progress_bar = QProgressBar()
            self.progress_bar.setFixedHeight(4)
            self.progress_bar.setTextVisible(False)
            self.progress_bar.setValue(int(self.task.checklist_progress))
            self.progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    background-color: {p['border']};
                    border-radius: 2px;
                }}
                QProgressBar::chunk {{
                    background-color: {p['success']};
                    border-radius: 2px;
                }}
            """)
            main_layout.addWidget(self.progress_bar)

    def _apply_style(self):
        """تطبيق التنسيق"""
        p = get_current_palette()
        base_bg = p['bg_card']
        border_color = p['border']

        # تنسيق مختلف للمهام المتأخرة
        if self.task.is_overdue:
            border_color = p['danger']
            base_bg = f"{p['danger']}08"
        elif self.task.status == TaskStatus.COMPLETED:
            base_bg = f"{p['success']}08"
            border_color = p['success']

        self.setStyleSheet(f"""
            QFrame#taskCard {{
                background-color: {base_bg};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
            QFrame#taskCard:hover {{
                border-color: {p['primary']};
                background-color: {p['bg_hover']};
            }}
        """)

    def _style_status_button(self):
        """تنسيق زر الحالة"""
        color = self.task.status.color
        self.status_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color}20;
                color: {color};
                border: 1px solid {color}40;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {color}40;
            }}
        """)

    def _show_status_menu(self):
        """عرض قائمة تغيير الحالة"""
        menu = QMenu(self)
        menu.setLayoutDirection(Qt.RightToLeft)

        for status in TaskStatus:
            action = QAction(status.label_ar, self)
            action.setData(status.value)
            if status == self.task.status:
                action.setEnabled(False)
            action.triggered.connect(
                lambda checked, s=status: self._change_status(s)
            )
            menu.addAction(action)

        menu.exec_(QCursor.pos())

    def _show_priority_menu(self):
        """عرض قائمة تغيير الأولوية"""
        menu = QMenu(self)
        menu.setLayoutDirection(Qt.RightToLeft)

        for priority in TaskPriority:
            action = QAction(priority.label_ar, self)
            action.setData(priority.value)
            if priority == self.task.priority:
                action.setEnabled(False)
            action.triggered.connect(
                lambda checked, p=priority: self._change_priority(p)
            )
            menu.addAction(action)

        menu.exec_(QCursor.pos())

    def _change_status(self, new_status: TaskStatus):
        """تغيير الحالة"""
        self.status_changed.emit(self.task.id, new_status.value)

    def _change_priority(self, new_priority: TaskPriority):
        """تغيير الأولوية"""
        self.priority_changed.emit(self.task.id, new_priority.value)

    def mousePressEvent(self, event):
        """عند الضغط على البطاقة"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.task.id)
        super().mousePressEvent(event)

    def contextMenuEvent(self, event):
        """قائمة السياق"""
        menu = QMenu(self)
        menu.setLayoutDirection(Qt.RightToLeft)

        # Edit action
        edit_action = QAction("✏️ تعديل", self)
        edit_action.triggered.connect(lambda: self.edit_requested.emit(self.task.id))
        menu.addAction(edit_action)

        # Status submenu
        status_menu = menu.addMenu("📋 تغيير الحالة")
        for status in TaskStatus:
            action = QAction(status.label_ar, self)
            action.triggered.connect(
                lambda checked, s=status: self._change_status(s)
            )
            status_menu.addAction(action)

        # Priority submenu
        priority_menu = menu.addMenu("⚡ تغيير الأولوية")
        for priority in TaskPriority:
            action = QAction(priority.label_ar, self)
            action.triggered.connect(
                lambda checked, p=priority: self._change_priority(p)
            )
            priority_menu.addAction(action)

        menu.addSeparator()

        # Delete action
        delete_action = QAction("🗑️ حذف", self)
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.task.id))
        menu.addAction(delete_action)

        menu.exec_(event.globalPos())

    def update_task(self, task: Task):
        """تحديث بيانات المهمة"""
        self.task = task
        self.title_label.setText(task.title)
        self.status_btn.setText(task.status_label)
        self.priority_label.setText(task.priority_label)
        self.priority_indicator.setStyleSheet(
            f"background-color: {task.priority.color}; border-radius: 2px;"
        )
        self._style_status_button()
        self._apply_style()


class CompactTaskCard(QFrame):
    """
    بطاقة مهمة مصغرة

    للاستخدام في لوحة Kanban أو القوائم المدمجة.
    """

    clicked = pyqtSignal(int)
    status_changed = pyqtSignal(int, str)

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self.task = task
        self._setup_ui()

    def _setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setObjectName("compactTaskCard")
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setMinimumHeight(50)
        self.setMaximumHeight(70)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        # Priority indicator
        indicator = QFrame()
        indicator.setFixedSize(3, 30)
        indicator.setStyleSheet(
            f"background-color: {self.task.priority.color}; border-radius: 1px;"
        )
        layout.addWidget(indicator)

        p = get_current_palette()

        # Title
        self.title_label = QLabel(self.task.title)
        self.title_label.setFont(get_font(FONT_SIZE_BODY))
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label, 1)

        # Due indicator
        if self.task.due_date:
            if self.task.is_overdue:
                due_icon = "🔴"
            elif self.task.is_due_today:
                due_icon = "🟡"
            else:
                due_icon = "⚪"
            due_label = QLabel(due_icon)
            due_label.setToolTip(self.task.due_date_formatted)
            layout.addWidget(due_label)

        # Style
        border_color = p['danger'] if self.task.is_overdue else p['border']
        self.setStyleSheet(f"""
            QFrame#compactTaskCard {{
                background-color: {p['bg_card']};
                border: 1px solid {border_color};
                border-radius: 6px;
            }}
            QFrame#compactTaskCard:hover {{
                background-color: {p['bg_hover']};
                border-color: {p['primary']};
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.task.id)
        super().mousePressEvent(event)
