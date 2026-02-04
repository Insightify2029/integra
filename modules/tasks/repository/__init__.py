"""
INTEGRA - Task Repository
موديول المهام - مستودع البيانات

التاريخ: 4 فبراير 2026
"""

from .task_repository import (
    TaskRepository,
    get_task_repository,
    # Quick access functions
    get_all_tasks,
    get_task_by_id,
    get_tasks_by_status,
    get_tasks_due_today,
    get_overdue_tasks,
    get_task_statistics,
    create_task,
    update_task,
    delete_task,
    change_task_status,
    # Checklist
    add_checklist_item,
    toggle_checklist_item,
    delete_checklist_item,
    # Setup
    setup_tasks_schema,
)

__all__ = [
    "TaskRepository",
    "get_task_repository",
    "get_all_tasks",
    "get_task_by_id",
    "get_tasks_by_status",
    "get_tasks_due_today",
    "get_overdue_tasks",
    "get_task_statistics",
    "create_task",
    "update_task",
    "delete_task",
    "change_task_status",
    "add_checklist_item",
    "toggle_checklist_item",
    "delete_checklist_item",
    "setup_tasks_schema",
]
