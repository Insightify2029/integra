"""
INTEGRA - Task Screens
شاشات المهام
المحور H

التاريخ: 4 فبراير 2026
"""

from .task_list import TaskListScreen
from .task_board import KanbanBoard

__all__ = [
    "TaskListScreen",
    "KanbanBoard",
]
