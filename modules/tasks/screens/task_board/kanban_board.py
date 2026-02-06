"""
INTEGRA - Kanban Board
لوحة كانبان للمهام
المحور H

التاريخ: 4 فبراير 2026
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QScrollArea,
    QFrame, QLabel, QPushButton, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData, QTimer
from PyQt5.QtGui import QFont, QDrag, QPixmap, QPainter

from typing import List, Dict, Optional

from ...models import Task, TaskStatus, TaskPriority
from ...widgets import CompactTaskCard, TaskFormDialog
from ...repository import (
    get_all_tasks, change_task_status, get_task_by_id
)

from core.logging import app_logger


class DraggableTaskCard(QFrame):
    """
    بطاقة مهمة قابلة للسحب

    تدعم السحب والإفلات لنقل المهام بين الأعمدة.
    """

    clicked = pyqtSignal(int)  # task_id
    drag_started = pyqtSignal(int)  # task_id

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self.task = task
        self._setup_ui()
        self.setAcceptDrops(False)

    def _setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setObjectName("draggableTaskCard")
        self.setCursor(Qt.OpenHandCursor)
        self.setMinimumHeight(60)
        self.setMaximumHeight(100)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # Priority indicator and title
        header = QHBoxLayout()
        header.setSpacing(8)

        # Priority dot
        priority_dot = QFrame()
        priority_dot.setFixedSize(8, 8)
        priority_dot.setStyleSheet(f"""
            background-color: {self.task.priority.color};
            border-radius: 4px;
        """)
        header.addWidget(priority_dot)

        # Title
        self.title_label = QLabel(self.task.title)
        self.title_label.setFont(QFont("Cairo", 10))
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumHeight(40)
        header.addWidget(self.title_label, 1)

        layout.addLayout(header)

        # Info row
        info_layout = QHBoxLayout()
        info_layout.setSpacing(8)

        if self.task.due_date:
            due_icon = "🔴" if self.task.is_overdue else "📅"
            due_label = QLabel(f"{due_icon} {self.task.due_date_formatted}")
            due_label.setFont(QFont("Cairo", 8))
            due_label.setStyleSheet(
                f"color: {'#dc3545' if self.task.is_overdue else '#6c757d'};"
            )
            info_layout.addWidget(due_label)

        info_layout.addStretch()

        if self.task.checklist_count > 0:
            check_label = QLabel(f"✓{self.task.checklist_completed}/{self.task.checklist_count}")
            check_label.setFont(QFont("Cairo", 8))
            check_label.setStyleSheet("color: #6c757d;")
            info_layout.addWidget(check_label)

        layout.addLayout(info_layout)

        # Style
        border_color = "#dc3545" if self.task.is_overdue else "#e9ecef"
        self.setStyleSheet(f"""
            QFrame#draggableTaskCard {{
                background-color: white;
                border: 1px solid {border_color};
                border-radius: 6px;
            }}
            QFrame#draggableTaskCard:hover {{
                border-color: #007bff;
                background-color: #f8f9fa;
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setCursor(Qt.ClosedHandCursor)
            self._drag_start_position = event.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.OpenHandCursor)
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return

        if not hasattr(self, '_drag_start_position'):
            return

        # Check if drag distance is enough
        distance = (event.pos() - self._drag_start_position).manhattanLength()
        if distance < 10:
            return

        # Start drag
        self.drag_started.emit(self.task.id)

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(str(self.task.id))
        drag.setMimeData(mime_data)

        # Create drag pixmap
        pixmap = self.grab()
        pixmap = pixmap.scaled(
            int(pixmap.width() * 0.8),
            int(pixmap.height() * 0.8),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        drag.setPixmap(pixmap)
        from PyQt5.QtCore import QPoint
        drag.setHotSpot(QPoint(int(event.pos().x() * 0.8), int(event.pos().y() * 0.8)))

        # Execute drag
        drag.exec_(Qt.MoveAction)

    def mouseDoubleClickEvent(self, event):
        self.clicked.emit(self.task.id)
        super().mouseDoubleClickEvent(event)


class KanbanColumn(QFrame):
    """
    عمود كانبان

    يعرض المهام لحالة معينة.
    """

    task_dropped = pyqtSignal(int, str)  # task_id, new_status
    task_clicked = pyqtSignal(int)  # task_id
    add_task_requested = pyqtSignal(str)  # status

    def __init__(self, status: TaskStatus, parent=None):
        super().__init__(parent)
        self.status = status
        self.tasks: List[Task] = []
        self._setup_ui()
        self.setAcceptDrops(True)

    def _setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setObjectName("kanbanColumn")
        self.setMinimumWidth(280)
        self.setMaximumWidth(320)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(50)
        header.setObjectName("columnHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)

        # Status indicator
        indicator = QFrame()
        indicator.setFixedSize(12, 12)
        indicator.setStyleSheet(f"""
            background-color: {self.status.color};
            border-radius: 6px;
        """)
        header_layout.addWidget(indicator)

        # Title
        title = QLabel(self.status.label_ar)
        title.setFont(QFont("Cairo", 12, QFont.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Count badge
        self.count_label = QLabel("0")
        self.count_label.setFixedSize(24, 24)
        self.count_label.setAlignment(Qt.AlignCenter)
        self.count_label.setFont(QFont("Cairo", 10, QFont.Bold))
        self.count_label.setStyleSheet(f"""
            background-color: {self.status.color}20;
            color: {self.status.color};
            border-radius: 12px;
        """)
        header_layout.addWidget(self.count_label)

        # Add button
        add_btn = QPushButton("+")
        add_btn.setFixedSize(24, 24)
        add_btn.clicked.connect(lambda: self.add_task_requested.emit(self.status.value))
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-size: 16px;
                color: #6c757d;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        header_layout.addWidget(add_btn)

        header.setStyleSheet(f"""
            QFrame#columnHeader {{
                background-color: {self.status.color}10;
                border-bottom: 2px solid {self.status.color};
            }}
        """)
        layout.addWidget(header)

        # Task list scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background-color: transparent;")

        self.task_container = QWidget()
        self.task_layout = QVBoxLayout(self.task_container)
        self.task_layout.setContentsMargins(8, 8, 8, 8)
        self.task_layout.setSpacing(8)
        self.task_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.task_container)
        layout.addWidget(scroll, 1)

        # Style
        self.setStyleSheet("""
            QFrame#kanbanColumn {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e9ecef;
            }
        """)

    def set_tasks(self, tasks: List[Task]):
        """تعيين المهام"""
        self.tasks = tasks
        self._render_tasks()

    def _render_tasks(self):
        """عرض المهام"""
        # Clear existing cards
        while self.task_layout.count() > 0:
            item = self.task_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add task cards
        for task in self.tasks:
            card = DraggableTaskCard(task)
            card.clicked.connect(self.task_clicked.emit)
            self.task_layout.addWidget(card)

        # Update count
        self.count_label.setText(str(len(self.tasks)))

        # Add stretch
        self.task_layout.addStretch()

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QFrame#kanbanColumn {
                    background-color: #e3f2fd;
                    border-radius: 8px;
                    border: 2px dashed #007bff;
                }
            """)

    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QFrame#kanbanColumn {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e9ecef;
            }
        """)

    def dropEvent(self, event):
        task_id = int(event.mimeData().text())
        self.task_dropped.emit(task_id, self.status.value)
        self.setStyleSheet("""
            QFrame#kanbanColumn {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e9ecef;
            }
        """)
        event.acceptProposedAction()


class KanbanBoard(QWidget):
    """
    لوحة كانبان للمهام

    تعرض المهام في أعمدة حسب الحالة مع دعم السحب والإفلات.
    """

    task_selected = pyqtSignal(int)  # task_id
    status_changed = pyqtSignal(int, str)  # task_id, new_status

    def __init__(self, parent=None):
        super().__init__(parent)
        self.columns: Dict[str, KanbanColumn] = {}
        self.tasks: List[Task] = []
        self._setup_ui()
        QTimer.singleShot(100, self.load_tasks)

    def _setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setObjectName("kanbanBoard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel("📊 لوحة المهام")
        title.setFont(QFont("Cairo", 16, QFont.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.setFixedHeight(36)
        refresh_btn.clicked.connect(self.load_tasks)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 0 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        header_layout.addWidget(refresh_btn)

        header.setStyleSheet("""
            QFrame {
                background-color: white;
                border-bottom: 1px solid #dee2e6;
            }
        """)
        layout.addWidget(header)

        # Board scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background-color: #f5f7fa;")

        board_container = QWidget()
        board_layout = QHBoxLayout(board_container)
        board_layout.setContentsMargins(16, 16, 16, 16)
        board_layout.setSpacing(16)
        board_layout.setAlignment(Qt.AlignLeft)

        # Create columns for each status
        for status in TaskStatus:
            column = KanbanColumn(status)
            column.task_dropped.connect(self._on_task_dropped)
            column.task_clicked.connect(self._on_task_clicked)
            column.add_task_requested.connect(self._on_add_task_requested)
            board_layout.addWidget(column)
            self.columns[status.value] = column

        board_layout.addStretch()

        scroll.setWidget(board_container)
        layout.addWidget(scroll, 1)

    def load_tasks(self):
        """تحميل المهام"""
        try:
            self.tasks = get_all_tasks(limit=500)
            self._distribute_tasks()
        except Exception as e:
            app_logger.error(f"Failed to load tasks for kanban: {e}")

    def _distribute_tasks(self):
        """توزيع المهام على الأعمدة"""
        # Group tasks by status
        tasks_by_status: Dict[str, List[Task]] = {
            status.value: [] for status in TaskStatus
        }

        for task in self.tasks:
            status_value = task.status.value
            if status_value in tasks_by_status:
                tasks_by_status[status_value].append(task)

        # Update columns
        for status_value, column in self.columns.items():
            column.set_tasks(tasks_by_status.get(status_value, []))

    def _on_task_dropped(self, task_id: int, new_status: str):
        """عند إفلات مهمة في عمود"""
        try:
            success = change_task_status(task_id, TaskStatus(new_status))
            if success:
                self.status_changed.emit(task_id, new_status)
                self.load_tasks()
        except Exception as e:
            app_logger.error(f"Failed to change task status: {e}")

    def _on_task_clicked(self, task_id: int):
        """عند النقر على مهمة"""
        self.task_selected.emit(task_id)
        self._show_task_dialog(task_id)

    def _on_add_task_requested(self, status: str):
        """عند طلب إضافة مهمة"""
        from ...models import Task
        task = Task(status=TaskStatus(status))
        dialog = TaskFormDialog(task=task, parent=self)
        dialog.task_saved.connect(self._on_task_saved)
        dialog.exec_()

    def _show_task_dialog(self, task_id: int):
        """عرض نافذة تعديل المهمة"""
        task = get_task_by_id(task_id)
        if task:
            dialog = TaskFormDialog(task=task, parent=self)
            dialog.task_saved.connect(self._on_task_saved)
            dialog.exec_()

    def _on_task_saved(self, task: Task):
        """عند حفظ مهمة"""
        try:
            from ...repository import create_task, update_task
            if task.id:
                update_task(task)
            else:
                create_task(task)
            self.load_tasks()
        except Exception as e:
            app_logger.error(f"Failed to save task: {e}")

    def refresh(self):
        """تحديث اللوحة"""
        self.load_tasks()
