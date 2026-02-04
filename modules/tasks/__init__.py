"""
INTEGRA - Tasks Module
موديول المهام
المحور H

نظام إدارة مهام متكامل مستوحى من Google Tasks مع قوة AI

التاريخ: 4 فبراير 2026
الإصدار: 1.0.0
"""

# Models
from .models import (
    # Enums
    TaskStatus,
    TaskPriority,
    RecurrenceType,
    TaskCategory,
    # Data Classes
    RecurrencePattern,
    ChecklistItem,
    TaskAttachment,
    TaskComment,
    AIAnalysis,
    Task,
    TaskStatistics,
)

# Repository
from .repository import (
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

# Recurring Tasks
from .recurring import (
    RecurrenceManager,
    get_recurrence_manager,
    calculate_next_occurrence,
    create_recurring_instance,
    process_due_recurring_tasks,
)

# Integration
from .integration import (
    # Calendar
    TaskCalendarSync,
    get_task_calendar_sync,
    task_to_calendar_event,
    get_tasks_for_date,
    get_tasks_for_range,
    # Email
    EmailTaskIntegration,
    get_email_task_integration,
    create_task_from_email,
)

__version__ = "1.0.0"

__all__ = [
    # Version
    "__version__",
    # Enums
    "TaskStatus",
    "TaskPriority",
    "RecurrenceType",
    "TaskCategory",
    # Data Classes
    "RecurrencePattern",
    "ChecklistItem",
    "TaskAttachment",
    "TaskComment",
    "AIAnalysis",
    "Task",
    "TaskStatistics",
    # Repository
    "TaskRepository",
    "get_task_repository",
    # Quick Functions
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
    # Recurring
    "RecurrenceManager",
    "get_recurrence_manager",
    "calculate_next_occurrence",
    "create_recurring_instance",
    "process_due_recurring_tasks",
    # Calendar Integration
    "TaskCalendarSync",
    "get_task_calendar_sync",
    "task_to_calendar_event",
    "get_tasks_for_date",
    "get_tasks_for_range",
    # Email Integration
    "EmailTaskIntegration",
    "get_email_task_integration",
    "create_task_from_email",
]
