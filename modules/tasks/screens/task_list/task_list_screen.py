"""
INTEGRA - Task List Screen
شاشة قائمة المهام
المحور H

التاريخ: 4 فبراير 2026
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QFrame, QLabel, QPushButton, QMessageBox,
    QSplitter, QStackedWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from typing import List, Optional

from ...models import Task, TaskStatus, TaskPriority, TaskStatistics
from ...widgets import (
    TaskCard, TaskFilters, QuickFilters,
    TaskFormDialog, QuickTaskInput
)
from ...repository import (
    get_all_tasks, get_task_by_id, get_task_statistics,
    get_tasks_due_today, get_overdue_tasks,
    create_task, update_task, delete_task, change_task_status
)

from core.logging import app_logger


class TaskListScreen(QWidget):
    """
    شاشة قائمة المهام

    تعرض كل المهام مع إمكانية:
    - البحث والفلترة
    - إنشاء مهام جديدة
    - تعديل وحذف المهام
    - تغيير الحالة والأولوية
    """

    task_selected = pyqtSignal(int)  # task_id
    view_changed = pyqtSignal(str)   # "list" or "board"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks: List[Task] = []
        self.current_filters = {}
        self._setup_ui()
        self._connect_signals()
        QTimer.singleShot(100, self.load_tasks)

    def _setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setObjectName("taskListScreen")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ═══════════════════════════════════════════════════════════════
        # Header
        # ═══════════════════════════════════════════════════════════════
        header = QFrame()
        header.setObjectName("taskListHeader")
        header.setFixedHeight(70)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        # Title
        title = QLabel("📋 المهام")
        title.setFont(QFont("Cairo", 18, QFont.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Statistics
        self.stats_frame = QFrame()
        stats_layout = QHBoxLayout(self.stats_frame)
        stats_layout.setSpacing(24)
        stats_layout.setContentsMargins(0, 0, 0, 0)

        self.pending_label = self._create_stat_label("قيد الانتظار", "0", "#6c757d")
        stats_layout.addWidget(self.pending_label)

        self.progress_label = self._create_stat_label("قيد التنفيذ", "0", "#007bff")
        stats_layout.addWidget(self.progress_label)

        self.completed_label = self._create_stat_label("مكتملة", "0", "#28a745")
        stats_layout.addWidget(self.completed_label)

        self.overdue_label = self._create_stat_label("متأخرة", "0", "#dc3545")
        stats_layout.addWidget(self.overdue_label)

        header_layout.addWidget(self.stats_frame)

        header_layout.addStretch()

        # Add task button
        self.add_btn = QPushButton("➕ مهمة جديدة")
        self.add_btn.setFixedHeight(40)
        self.add_btn.clicked.connect(self._show_add_dialog)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        header_layout.addWidget(self.add_btn)

        header.setStyleSheet("""
            QFrame#taskListHeader {
                background-color: white;
                border-bottom: 1px solid #dee2e6;
            }
        """)
        main_layout.addWidget(header)

        # ═══════════════════════════════════════════════════════════════
        # Filters
        # ═══════════════════════════════════════════════════════════════
        self.filters = TaskFilters()
        self.filters.filters_changed.connect(self._on_filters_changed)
        self.filters.search_changed.connect(self._on_search_changed)
        self.filters.view_changed.connect(self._on_view_changed)
        main_layout.addWidget(self.filters)

        # ═══════════════════════════════════════════════════════════════
        # Quick Filters
        # ═══════════════════════════════════════════════════════════════
        quick_filters_frame = QFrame()
        quick_filters_frame.setFixedHeight(50)
        quick_filters_layout = QHBoxLayout(quick_filters_frame)
        quick_filters_layout.setContentsMargins(20, 8, 20, 8)

        self.quick_filters = QuickFilters()
        self.quick_filters.filter_selected.connect(self._on_quick_filter)
        quick_filters_layout.addWidget(self.quick_filters)

        main_layout.addWidget(quick_filters_frame)

        # ═══════════════════════════════════════════════════════════════
        # Quick Task Input
        # ═══════════════════════════════════════════════════════════════
        quick_input_frame = QFrame()
        quick_input_layout = QHBoxLayout(quick_input_frame)
        quick_input_layout.setContentsMargins(20, 8, 20, 8)

        self.quick_input = QuickTaskInput()
        self.quick_input.task_created.connect(self._on_quick_task_created)
        quick_input_layout.addWidget(self.quick_input)

        main_layout.addWidget(quick_input_frame)

        # ═══════════════════════════════════════════════════════════════
        # Task List
        # ═══════════════════════════════════════════════════════════════
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(20, 12, 20, 20)
        self.list_layout.setSpacing(12)
        self.list_layout.setAlignment(Qt.AlignTop)

        self.scroll_area.setWidget(self.list_container)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #f5f7fa;
            }
        """)

        main_layout.addWidget(self.scroll_area, 1)

        # ═══════════════════════════════════════════════════════════════
        # Empty State
        # ═══════════════════════════════════════════════════════════════
        self.empty_state = QFrame()
        self.empty_state.hide()
        empty_layout = QVBoxLayout(self.empty_state)
        empty_layout.setAlignment(Qt.AlignCenter)

        empty_icon = QLabel("📋")
        empty_icon.setFont(QFont("Cairo", 48))
        empty_icon.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(empty_icon)

        self.empty_text = QLabel("لا توجد مهام")
        self.empty_text.setFont(QFont("Cairo", 16))
        self.empty_text.setStyleSheet("color: #6c757d;")
        self.empty_text.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(self.empty_text)

        empty_btn = QPushButton("➕ أضف مهمة جديدة")
        empty_btn.setFixedHeight(40)
        empty_btn.clicked.connect(self._show_add_dialog)
        empty_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 24px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        empty_layout.addWidget(empty_btn, alignment=Qt.AlignCenter)

    def _create_stat_label(self, title: str, value: str, color: str) -> QFrame:
        """إنشاء تسمية إحصائية"""
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)

        value_label = QLabel(value)
        value_label.setObjectName("statValue")
        value_label.setFont(QFont("Cairo", 16, QFont.Bold))
        value_label.setStyleSheet(f"color: {color};")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)

        title_label = QLabel(title)
        title_label.setFont(QFont("Cairo", 10))
        title_label.setStyleSheet("color: #6c757d;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        return frame

    def _connect_signals(self):
        """ربط الإشارات"""
        pass

    # ═══════════════════════════════════════════════════════════════
    # Data Loading
    # ═══════════════════════════════════════════════════════════════

    def load_tasks(self):
        """تحميل المهام من قاعدة البيانات"""
        try:
            # Get filters
            filters = self.current_filters.copy()

            # Handle quick filters (today/overdue) via dedicated queries
            quick = filters.pop("_quick", None)
            if quick == "today":
                self.tasks = get_tasks_due_today()
            elif quick == "overdue":
                self.tasks = get_overdue_tasks()
            else:
                # Convert filter values to proper types
                status = None
                if filters.get("status"):
                    status = TaskStatus(filters["status"])

                priority = None
                if filters.get("priority"):
                    priority = TaskPriority(filters["priority"])

                # Fetch tasks
                self.tasks = get_all_tasks(
                    status=status,
                    priority=priority,
                    category=filters.get("category"),
                    search=filters.get("search"),
                    limit=200
                )

            self._render_tasks()
            self._update_statistics()

        except Exception as e:
            app_logger.error(f"Failed to load tasks: {e}")

    def _render_tasks(self):
        """عرض المهام"""
        # Clear existing cards
        while self.list_layout.count() > 0:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.tasks:
            self._show_empty_state()
            return

        self._hide_empty_state()

        # Create task cards
        for task in self.tasks:
            card = TaskCard(task)
            card.clicked.connect(self._on_task_clicked)
            card.status_changed.connect(self._on_status_changed)
            card.priority_changed.connect(self._on_priority_changed)
            card.edit_requested.connect(self._on_edit_requested)
            card.delete_requested.connect(self._on_delete_requested)
            self.list_layout.addWidget(card)

        # Add stretch at the end
        self.list_layout.addStretch()

    def _show_empty_state(self):
        """عرض الحالة الفارغة"""
        if self.current_filters.get("search"):
            self.empty_text.setText("لا توجد نتائج للبحث")
        elif any(self.current_filters.values()):
            self.empty_text.setText("لا توجد مهام تطابق الفلترة")
        else:
            self.empty_text.setText("لا توجد مهام")

        self.scroll_area.hide()
        self.list_layout.addWidget(self.empty_state)
        self.empty_state.show()

    def _hide_empty_state(self):
        """إخفاء الحالة الفارغة"""
        self.empty_state.hide()
        self.scroll_area.show()

    def _update_statistics(self):
        """تحديث الإحصائيات"""
        try:
            stats = get_task_statistics()

            # Update labels
            self.pending_label.findChild(QLabel, "statValue").setText(
                str(stats.pending_count)
            )
            self.progress_label.findChild(QLabel, "statValue").setText(
                str(stats.in_progress_count)
            )
            self.completed_label.findChild(QLabel, "statValue").setText(
                str(stats.completed_count)
            )
            self.overdue_label.findChild(QLabel, "statValue").setText(
                str(stats.overdue_count)
            )

        except Exception as e:
            app_logger.error(f"Failed to update statistics: {e}")

    # ═══════════════════════════════════════════════════════════════
    # Event Handlers
    # ═══════════════════════════════════════════════════════════════

    def _on_filters_changed(self, filters: dict):
        """عند تغيير الفلاتر"""
        self.current_filters.update(filters)
        self.load_tasks()

    def _on_search_changed(self, text: str):
        """عند تغيير البحث"""
        self.current_filters["search"] = text
        # Debounce search
        QTimer.singleShot(300, self.load_tasks)

    def _on_view_changed(self, view: str):
        """عند تغيير العرض"""
        self.view_changed.emit(view)

    def _on_quick_filter(self, filter_type: str):
        """عند اختيار فلتر سريع"""
        self.current_filters = {}  # Reset filters

        if filter_type == "today":
            self.current_filters["_quick"] = "today"
        elif filter_type == "overdue":
            self.current_filters["_quick"] = "overdue"
        elif filter_type == "urgent":
            self.current_filters["priority"] = "urgent"
        elif filter_type == "in_progress":
            self.current_filters["status"] = "in_progress"

        self.load_tasks()

    def _on_task_clicked(self, task_id: int):
        """عند النقر على مهمة"""
        self.task_selected.emit(task_id)
        self._show_edit_dialog(task_id)

    def _on_status_changed(self, task_id: int, new_status: str):
        """عند تغيير حالة مهمة"""
        try:
            success = change_task_status(task_id, TaskStatus(new_status))
            if success:
                self.load_tasks()
        except Exception as e:
            app_logger.error(f"Failed to change status: {e}")

    def _on_priority_changed(self, task_id: int, new_priority: str):
        """عند تغيير أولوية مهمة"""
        try:
            task = get_task_by_id(task_id)
            if task:
                task.priority = TaskPriority(new_priority)
                update_task(task)
                self.load_tasks()
        except Exception as e:
            app_logger.error(f"Failed to change priority: {e}")

    def _on_edit_requested(self, task_id: int):
        """عند طلب تعديل مهمة"""
        self._show_edit_dialog(task_id)

    def _on_delete_requested(self, task_id: int):
        """عند طلب حذف مهمة"""
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            "هل أنت متأكد من حذف هذه المهمة؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                success = delete_task(task_id)
                if success:
                    self.load_tasks()
            except Exception as e:
                app_logger.error(f"Failed to delete task: {e}")

    def _on_quick_task_created(self, task: Task):
        """عند إنشاء مهمة سريعة"""
        try:
            task_id = create_task(task)
            if task_id:
                self.load_tasks()
        except Exception as e:
            app_logger.error(f"Failed to create quick task: {e}")

    # ═══════════════════════════════════════════════════════════════
    # Dialogs
    # ═══════════════════════════════════════════════════════════════

    def _show_add_dialog(self):
        """عرض نافذة إضافة مهمة"""
        dialog = TaskFormDialog(parent=self)
        dialog.task_saved.connect(self._on_task_saved)
        dialog.exec_()

    def _show_edit_dialog(self, task_id: int):
        """عرض نافذة تعديل مهمة"""
        task = get_task_by_id(task_id)
        if not task:
            return

        dialog = TaskFormDialog(task=task, parent=self)
        dialog.task_saved.connect(self._on_task_saved)
        dialog.exec_()

    def _on_task_saved(self, task: Task):
        """عند حفظ مهمة"""
        try:
            if task.id:
                update_task(task)
            else:
                create_task(task)
            self.load_tasks()
        except Exception as e:
            app_logger.error(f"Failed to save task: {e}")

    # ═══════════════════════════════════════════════════════════════
    # Public Methods
    # ═══════════════════════════════════════════════════════════════

    def refresh(self):
        """تحديث القائمة"""
        self.load_tasks()

    def set_filter(self, filter_type: str, value):
        """تعيين فلتر"""
        self.current_filters[filter_type] = value
        self.load_tasks()

    def clear_filters(self):
        """مسح الفلاتر"""
        self.current_filters = {}
        self.filters.reset_filters()
        self.load_tasks()
