"""
INTEGRA - Task Integrations
تكاملات المهام
المحور H

التاريخ: 4 فبراير 2026
"""

from .calendar_sync import (
    TaskCalendarSync,
    get_task_calendar_sync,
    task_to_calendar_event,
    sync_task_to_calendar,
    get_tasks_for_date,
    get_tasks_for_range,
)
from .email_integration import (
    EmailTaskIntegration,
    get_email_task_integration,
    create_task_from_email,
)

__all__ = [
    # Calendar
    "TaskCalendarSync",
    "get_task_calendar_sync",
    "task_to_calendar_event",
    "sync_task_to_calendar",
    "get_tasks_for_date",
    "get_tasks_for_range",
    # Email
    "EmailTaskIntegration",
    "get_email_task_integration",
    "create_task_from_email",
]
