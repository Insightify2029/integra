"""
INTEGRA - Calendar Repository
موديول التقويم - مستودع البيانات
المحور I

التاريخ: 4 فبراير 2026
"""

from .calendar_repository import (
    # Event CRUD
    create_event,
    get_event,
    update_event,
    delete_event,
    get_all_events,

    # Event Queries
    get_events_in_range,
    get_events_by_date,
    get_events_today,
    get_events_this_week,
    get_events_this_month,
    get_upcoming_events,
    get_events_by_task,
    get_events_by_employee,

    # Category
    get_all_categories,
    get_category_by_name,

    # Holidays
    get_holidays_in_range,
    get_holidays_by_year,

    # Settings
    get_calendar_settings,
    save_calendar_settings,

    # Statistics
    get_event_statistics,

    # Conflict Detection
    check_conflicts,

    # Recurrence
    generate_recurring_events,

    # Repository class
    CalendarRepository,
    get_calendar_repository,
)

__all__ = [
    # Event CRUD
    "create_event",
    "get_event",
    "update_event",
    "delete_event",
    "get_all_events",

    # Event Queries
    "get_events_in_range",
    "get_events_by_date",
    "get_events_today",
    "get_events_this_week",
    "get_events_this_month",
    "get_upcoming_events",
    "get_events_by_task",
    "get_events_by_employee",

    # Category
    "get_all_categories",
    "get_category_by_name",

    # Holidays
    "get_holidays_in_range",
    "get_holidays_by_year",

    # Settings
    "get_calendar_settings",
    "save_calendar_settings",

    # Statistics
    "get_event_statistics",

    # Conflict Detection
    "check_conflicts",

    # Recurrence
    "generate_recurring_events",

    # Repository class
    "CalendarRepository",
    "get_calendar_repository",
]
