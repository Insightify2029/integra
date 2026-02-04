"""
INTEGRA - Calendar Module
موديول التقويم
المحور I

التاريخ: 4 فبراير 2026

هذا الموديول يوفر نظام تقويم متكامل مع:
- إدارة الأحداث والمواعيد
- عرض شهري/أسبوعي/يومي
- ربط المهام بالتقويم
- مزامنة مع Outlook Calendar
- تذكيرات وإشعارات
- دعم الأحداث المتكررة

الاستخدام:
---------
```python
from modules.calendar import (
    # Models
    CalendarEvent, EventType, EventStatus,

    # CRUD
    create_event, get_event, update_event, delete_event,

    # Queries
    get_events_today, get_events_this_week, get_events_in_range,

    # Settings
    get_calendar_settings, save_calendar_settings,
)

# إنشاء حدث جديد
event = CalendarEvent(
    title="اجتماع مع الفريق",
    event_type=EventType.MEETING,
    start_datetime=datetime(2026, 2, 5, 10, 0),
    end_datetime=datetime(2026, 2, 5, 11, 0),
    location="قاعة الاجتماعات"
)
event_id = create_event(event)

# جلب أحداث اليوم
today_events = get_events_today()

# جلب أحداث الأسبوع
week_events = get_events_this_week()
```
"""

# Models
from .models import (
    # Enums
    EventType,
    EventStatus,
    ReminderType,
    AttendeeStatus,
    CalendarView,
    RecurrenceType,

    # Data Classes
    Reminder,
    Attendee,
    RecurrencePattern,
    CalendarEvent,
    CalendarCategory,
    PublicHoliday,
    CalendarSettings,
    EventStatistics,
    TimeSlot,
    DayEvents,
)

# Repository
from .repository import (
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
    # Enums
    "EventType",
    "EventStatus",
    "ReminderType",
    "AttendeeStatus",
    "CalendarView",
    "RecurrenceType",

    # Data Classes
    "Reminder",
    "Attendee",
    "RecurrencePattern",
    "CalendarEvent",
    "CalendarCategory",
    "PublicHoliday",
    "CalendarSettings",
    "EventStatistics",
    "TimeSlot",
    "DayEvents",

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

__version__ = "1.0.0"
