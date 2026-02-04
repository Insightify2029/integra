"""
INTEGRA - Calendar Models
موديول التقويم - نماذج البيانات
المحور I

التاريخ: 4 فبراير 2026
"""

from dataclasses import dataclass, field
from datetime import datetime, date, time, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any
import json


# ═══════════════════════════════════════════════════════════════
# Enums - التعدادات
# ═══════════════════════════════════════════════════════════════

class EventType(Enum):
    """أنواع الأحداث"""
    EVENT = "event"           # حدث عام
    TASK = "task"             # مهمة
    REMINDER = "reminder"     # تذكير
    MEETING = "meeting"       # اجتماع
    HOLIDAY = "holiday"       # إجازة/عطلة

    @property
    def label_ar(self) -> str:
        labels = {
            "event": "حدث",
            "task": "مهمة",
            "reminder": "تذكير",
            "meeting": "اجتماع",
            "holiday": "إجازة"
        }
        return labels.get(self.value, self.value)

    @property
    def icon(self) -> str:
        icons = {
            "event": "fa5s.calendar",
            "task": "fa5s.tasks",
            "reminder": "fa5s.bell",
            "meeting": "fa5s.users",
            "holiday": "fa5s.umbrella-beach"
        }
        return icons.get(self.value, "fa5s.calendar")

    @property
    def default_color(self) -> str:
        colors = {
            "event": "#3498db",
            "task": "#2ecc71",
            "reminder": "#f39c12",
            "meeting": "#9b59b6",
            "holiday": "#e74c3c"
        }
        return colors.get(self.value, "#3498db")


class EventStatus(Enum):
    """حالات الحدث"""
    CONFIRMED = "confirmed"     # مؤكد
    TENTATIVE = "tentative"     # مؤقت
    CANCELLED = "cancelled"     # ملغي

    @property
    def label_ar(self) -> str:
        labels = {
            "confirmed": "مؤكد",
            "tentative": "مؤقت",
            "cancelled": "ملغي"
        }
        return labels.get(self.value, self.value)


class ReminderType(Enum):
    """أنواع التذكيرات"""
    NOTIFICATION = "notification"   # إشعار
    EMAIL = "email"                 # بريد إلكتروني
    SMS = "sms"                     # رسالة نصية
    POPUP = "popup"                 # نافذة منبثقة

    @property
    def label_ar(self) -> str:
        labels = {
            "notification": "إشعار",
            "email": "بريد إلكتروني",
            "sms": "رسالة نصية",
            "popup": "نافذة منبثقة"
        }
        return labels.get(self.value, self.value)


class AttendeeStatus(Enum):
    """حالات حضور المشاركين"""
    PENDING = "pending"       # في الانتظار
    ACCEPTED = "accepted"     # قبل
    DECLINED = "declined"     # رفض
    TENTATIVE = "tentative"   # مؤقت

    @property
    def label_ar(self) -> str:
        labels = {
            "pending": "في الانتظار",
            "accepted": "قبل",
            "declined": "رفض",
            "tentative": "مؤقت"
        }
        return labels.get(self.value, self.value)

    @property
    def color(self) -> str:
        colors = {
            "pending": "#f39c12",
            "accepted": "#2ecc71",
            "declined": "#e74c3c",
            "tentative": "#95a5a6"
        }
        return colors.get(self.value, "#6c757d")


class CalendarView(Enum):
    """أنواع عرض التقويم"""
    DAY = "day"       # يومي
    WEEK = "week"     # أسبوعي
    MONTH = "month"   # شهري
    AGENDA = "agenda" # قائمة الأحداث

    @property
    def label_ar(self) -> str:
        labels = {
            "day": "يومي",
            "week": "أسبوعي",
            "month": "شهري",
            "agenda": "الأجندة"
        }
        return labels.get(self.value, self.value)


class RecurrenceType(Enum):
    """أنماط التكرار"""
    DAILY = "daily"       # يومي
    WEEKLY = "weekly"     # أسبوعي
    MONTHLY = "monthly"   # شهري
    YEARLY = "yearly"     # سنوي

    @property
    def label_ar(self) -> str:
        labels = {
            "daily": "يومي",
            "weekly": "أسبوعي",
            "monthly": "شهري",
            "yearly": "سنوي"
        }
        return labels.get(self.value, self.value)


# ═══════════════════════════════════════════════════════════════
# Data Classes - نماذج البيانات
# ═══════════════════════════════════════════════════════════════

@dataclass
class Reminder:
    """تذكير الحدث"""
    type: ReminderType = ReminderType.NOTIFICATION
    minutes_before: int = 30

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "minutes_before": self.minutes_before
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Reminder":
        return cls(
            type=ReminderType(data.get("type", "notification")),
            minutes_before=data.get("minutes_before", 30)
        )

    @property
    def label_ar(self) -> str:
        """وصف التذكير بالعربي"""
        if self.minutes_before < 60:
            return f"قبل {self.minutes_before} دقيقة"
        elif self.minutes_before < 1440:
            hours = self.minutes_before // 60
            return f"قبل {hours} ساعة"
        else:
            days = self.minutes_before // 1440
            return f"قبل {days} يوم"


@dataclass
class Attendee:
    """مشارك في الحدث"""
    email: str = ""
    name: Optional[str] = None
    employee_id: Optional[int] = None
    status: AttendeeStatus = AttendeeStatus.PENDING
    is_organizer: bool = False
    is_optional: bool = False
    responded_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "email": self.email,
            "name": self.name,
            "employee_id": self.employee_id,
            "status": self.status.value,
            "is_organizer": self.is_organizer,
            "is_optional": self.is_optional,
            "responded_at": self.responded_at.isoformat() if self.responded_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Attendee":
        return cls(
            email=data.get("email", ""),
            name=data.get("name"),
            employee_id=data.get("employee_id"),
            status=AttendeeStatus(data.get("status", "pending")),
            is_organizer=data.get("is_organizer", False),
            is_optional=data.get("is_optional", False),
            responded_at=datetime.fromisoformat(data["responded_at"]) if data.get("responded_at") else None
        )


@dataclass
class RecurrencePattern:
    """نمط التكرار"""
    type: RecurrenceType
    interval: int = 1                         # كل كم (يوم/أسبوع/شهر)
    days_of_week: Optional[List[int]] = None  # أيام الأسبوع (0=الأحد، 6=السبت)
    day_of_month: Optional[int] = None        # يوم الشهر (1-31)
    month_of_year: Optional[int] = None       # شهر السنة (1-12)
    end_type: str = "never"                   # never, count, date
    end_count: Optional[int] = None           # عدد التكرارات
    end_date: Optional[date] = None           # تاريخ الانتهاء

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "interval": self.interval,
            "days_of_week": self.days_of_week,
            "day_of_month": self.day_of_month,
            "month_of_year": self.month_of_year,
            "end_type": self.end_type,
            "end_count": self.end_count,
            "end_date": self.end_date.isoformat() if self.end_date else None
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecurrencePattern":
        return cls(
            type=RecurrenceType(data.get("type", "daily")),
            interval=data.get("interval", 1),
            days_of_week=data.get("days_of_week"),
            day_of_month=data.get("day_of_month"),
            month_of_year=data.get("month_of_year"),
            end_type=data.get("end_type", "never"),
            end_count=data.get("end_count"),
            end_date=date.fromisoformat(data["end_date"]) if data.get("end_date") else None
        )

    @classmethod
    def from_json(cls, json_str: str) -> "RecurrencePattern":
        return cls.from_dict(json.loads(json_str))

    @property
    def label_ar(self) -> str:
        """وصف نمط التكرار بالعربي"""
        if self.interval == 1:
            return self.type.label_ar
        else:
            type_labels = {
                "daily": f"كل {self.interval} أيام",
                "weekly": f"كل {self.interval} أسابيع",
                "monthly": f"كل {self.interval} أشهر",
                "yearly": f"كل {self.interval} سنوات"
            }
            return type_labels.get(self.type.value, self.type.label_ar)


@dataclass
class CalendarEvent:
    """نموذج الحدث الرئيسي"""
    # الهوية
    id: Optional[int] = None

    # البيانات الأساسية
    title: str = ""
    description: Optional[str] = None
    event_type: EventType = EventType.EVENT

    # التوقيت
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    is_all_day: bool = False
    timezone: str = "Asia/Riyadh"

    # الروابط
    task_id: Optional[int] = None
    employee_id: Optional[int] = None

    # البيانات المرتبطة (للعرض)
    task_title: Optional[str] = None
    employee_name: Optional[str] = None
    category_ar: Optional[str] = None

    # التذكيرات والمشاركون
    reminders: List[Reminder] = field(default_factory=list)
    attendees: List[Attendee] = field(default_factory=list)

    # التكرار
    is_recurring: bool = False
    recurrence_pattern: Optional[RecurrencePattern] = None
    recurrence_end_date: Optional[date] = None
    parent_event_id: Optional[int] = None

    # اللون والتصنيف
    color: str = "#3498db"
    category: Optional[str] = None

    # الموقع
    location: Optional[str] = None
    location_url: Optional[str] = None

    # المصدر والمزامنة
    source: str = "integra"
    external_id: Optional[str] = None
    external_link: Optional[str] = None
    sync_status: str = "synced"
    last_synced_at: Optional[datetime] = None

    # الحالة
    status: EventStatus = EventStatus.CONFIRMED
    is_private: bool = False

    # البيانات الإضافية
    metadata: Dict[str, Any] = field(default_factory=dict)

    # الإحصائيات (للعرض)
    duration_minutes: Optional[int] = None
    attendees_count: int = 0

    # تتبع التغييرات
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس للحفظ"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "event_type": self.event_type.value,
            "start_datetime": self.start_datetime.isoformat() if self.start_datetime else None,
            "end_datetime": self.end_datetime.isoformat() if self.end_datetime else None,
            "is_all_day": self.is_all_day,
            "timezone": self.timezone,
            "task_id": self.task_id,
            "employee_id": self.employee_id,
            "reminders": [r.to_dict() for r in self.reminders],
            "attendees": [a.to_dict() for a in self.attendees],
            "is_recurring": self.is_recurring,
            "recurrence_pattern": self.recurrence_pattern.to_dict() if self.recurrence_pattern else None,
            "recurrence_end_date": self.recurrence_end_date.isoformat() if self.recurrence_end_date else None,
            "parent_event_id": self.parent_event_id,
            "color": self.color,
            "category": self.category,
            "location": self.location,
            "location_url": self.location_url,
            "source": self.source,
            "external_id": self.external_id,
            "external_link": self.external_link,
            "status": self.status.value,
            "is_private": self.is_private,
            "metadata": self.metadata,
            "created_by": self.created_by,
            "updated_by": self.updated_by
        }

    @classmethod
    def from_row(cls, row: tuple, columns: List[str]) -> "CalendarEvent":
        """إنشاء من صف قاعدة البيانات"""
        data = dict(zip(columns, row))

        event = cls(
            id=data.get("id"),
            title=data.get("title", ""),
            description=data.get("description"),
            event_type=EventType(data.get("event_type", "event")),
            start_datetime=data.get("start_datetime"),
            end_datetime=data.get("end_datetime"),
            is_all_day=data.get("is_all_day", False),
            timezone=data.get("timezone", "Asia/Riyadh"),
            task_id=data.get("task_id"),
            employee_id=data.get("employee_id"),
            task_title=data.get("task_title"),
            employee_name=data.get("employee_name"),
            category_ar=data.get("category_ar"),
            is_recurring=data.get("is_recurring", False),
            recurrence_end_date=data.get("recurrence_end_date"),
            parent_event_id=data.get("parent_event_id"),
            color=data.get("color", "#3498db"),
            category=data.get("category"),
            location=data.get("location"),
            location_url=data.get("location_url"),
            source=data.get("source", "integra"),
            external_id=data.get("external_id"),
            external_link=data.get("external_link"),
            sync_status=data.get("sync_status", "synced"),
            last_synced_at=data.get("last_synced_at"),
            status=EventStatus(data.get("status", "confirmed")),
            is_private=data.get("is_private", False),
            duration_minutes=data.get("duration_minutes"),
            attendees_count=data.get("attendees_count", 0),
            created_by=data.get("created_by"),
            updated_by=data.get("updated_by"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )

        # تحليل JSON
        if data.get("reminders"):
            reminders_data = data["reminders"]
            if isinstance(reminders_data, str):
                reminders_data = json.loads(reminders_data)
            event.reminders = [Reminder.from_dict(r) for r in reminders_data]

        if data.get("attendees"):
            attendees_data = data["attendees"]
            if isinstance(attendees_data, str):
                attendees_data = json.loads(attendees_data)
            event.attendees = [Attendee.from_dict(a) for a in attendees_data]

        if data.get("recurrence_pattern"):
            pattern_data = data["recurrence_pattern"]
            if isinstance(pattern_data, str):
                pattern_data = json.loads(pattern_data)
            event.recurrence_pattern = RecurrencePattern.from_dict(pattern_data)

        if data.get("metadata"):
            metadata = data["metadata"]
            if isinstance(metadata, str):
                event.metadata = json.loads(metadata)
            else:
                event.metadata = metadata

        return event

    # ═══════════════════════════════════════════════════════════════
    # Properties - الخصائص
    # ═══════════════════════════════════════════════════════════════

    @property
    def duration(self) -> Optional[timedelta]:
        """مدة الحدث"""
        if self.start_datetime and self.end_datetime:
            return self.end_datetime - self.start_datetime
        return None

    @property
    def duration_formatted(self) -> str:
        """مدة الحدث منسقة"""
        if self.is_all_day:
            return "طوال اليوم"

        duration = self.duration
        if not duration:
            return "غير محدد"

        total_minutes = int(duration.total_seconds() / 60)
        if total_minutes < 60:
            return f"{total_minutes} دقيقة"
        elif total_minutes < 1440:
            hours = total_minutes // 60
            minutes = total_minutes % 60
            if minutes > 0:
                return f"{hours} ساعة و {minutes} دقيقة"
            return f"{hours} ساعة"
        else:
            days = total_minutes // 1440
            return f"{days} يوم"

    @property
    def is_past(self) -> bool:
        """هل الحدث في الماضي؟"""
        if not self.end_datetime:
            if not self.start_datetime:
                return False
            return self.start_datetime < datetime.now()
        return self.end_datetime < datetime.now()

    @property
    def is_ongoing(self) -> bool:
        """هل الحدث جاري الآن؟"""
        if not self.start_datetime:
            return False
        now = datetime.now()
        end = self.end_datetime or self.start_datetime + timedelta(hours=1)
        return self.start_datetime <= now <= end

    @property
    def is_today(self) -> bool:
        """هل الحدث اليوم؟"""
        if not self.start_datetime:
            return False
        return self.start_datetime.date() == date.today()

    @property
    def is_tomorrow(self) -> bool:
        """هل الحدث غداً؟"""
        if not self.start_datetime:
            return False
        tomorrow = date.today() + timedelta(days=1)
        return self.start_datetime.date() == tomorrow

    @property
    def time_formatted(self) -> str:
        """الوقت منسق"""
        if self.is_all_day:
            return "طوال اليوم"
        if not self.start_datetime:
            return ""
        if self.end_datetime:
            return f"{self.start_datetime.strftime('%H:%M')} - {self.end_datetime.strftime('%H:%M')}"
        return self.start_datetime.strftime("%H:%M")

    @property
    def date_formatted(self) -> str:
        """التاريخ منسق"""
        if not self.start_datetime:
            return ""
        today = date.today()
        event_date = self.start_datetime.date()

        if event_date == today:
            return "اليوم"
        elif event_date == today + timedelta(days=1):
            return "غداً"
        elif event_date == today - timedelta(days=1):
            return "أمس"
        else:
            return self.start_datetime.strftime("%Y-%m-%d")

    @property
    def status_label(self) -> str:
        """تسمية الحالة بالعربي"""
        return self.status.label_ar

    @property
    def event_type_label(self) -> str:
        """تسمية نوع الحدث بالعربي"""
        return self.event_type.label_ar


@dataclass
class CalendarCategory:
    """تصنيف التقويم"""
    id: Optional[int] = None
    name: str = ""
    name_ar: Optional[str] = None
    color: str = "#3498db"
    icon: Optional[str] = None
    is_visible: bool = True
    sort_order: int = 0
    is_system: bool = False
    created_at: Optional[datetime] = None

    @classmethod
    def from_row(cls, row: tuple, columns: List[str]) -> "CalendarCategory":
        data = dict(zip(columns, row))
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            name_ar=data.get("name_ar"),
            color=data.get("color", "#3498db"),
            icon=data.get("icon"),
            is_visible=data.get("is_visible", True),
            sort_order=data.get("sort_order", 0),
            is_system=data.get("is_system", False),
            created_at=data.get("created_at")
        )


@dataclass
class PublicHoliday:
    """العطلة الرسمية"""
    id: Optional[int] = None
    name: str = ""
    name_ar: Optional[str] = None
    holiday_date: Optional[date] = None
    holiday_type: str = "official"
    country_code: str = "SA"
    is_recurring_yearly: bool = False
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    @classmethod
    def from_row(cls, row: tuple, columns: List[str]) -> "PublicHoliday":
        data = dict(zip(columns, row))
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            name_ar=data.get("name_ar"),
            holiday_date=data.get("holiday_date"),
            holiday_type=data.get("holiday_type", "official"),
            country_code=data.get("country_code", "SA"),
            is_recurring_yearly=data.get("is_recurring_yearly", False),
            notes=data.get("notes"),
            created_at=data.get("created_at")
        )


@dataclass
class CalendarSettings:
    """إعدادات التقويم"""
    id: Optional[int] = None
    user_id: Optional[int] = None

    # إعدادات العرض
    default_view: CalendarView = CalendarView.MONTH
    week_starts_on: int = 0  # 0 = الأحد
    show_weekends: bool = True
    show_week_numbers: bool = False

    # ساعات العمل
    work_hours_start: time = field(default_factory=lambda: time(8, 0))
    work_hours_end: time = field(default_factory=lambda: time(17, 0))
    work_days: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4])  # الأحد - الخميس

    # المزامنة
    sync_outlook: bool = False
    outlook_calendar_id: Optional[str] = None
    sync_google: bool = False
    google_calendar_id: Optional[str] = None

    # التنبيهات
    default_reminder_minutes: int = 30
    enable_desktop_notifications: bool = True
    enable_email_notifications: bool = False

    # البيانات الإضافية
    preferences: Dict[str, Any] = field(default_factory=dict)

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_row(cls, row: tuple, columns: List[str]) -> "CalendarSettings":
        data = dict(zip(columns, row))
        return cls(
            id=data.get("id"),
            user_id=data.get("user_id"),
            default_view=CalendarView(data.get("default_view", "month")),
            week_starts_on=data.get("week_starts_on", 0),
            show_weekends=data.get("show_weekends", True),
            show_week_numbers=data.get("show_week_numbers", False),
            work_hours_start=data.get("work_hours_start") or time(8, 0),
            work_hours_end=data.get("work_hours_end") or time(17, 0),
            work_days=data.get("work_days") or [0, 1, 2, 3, 4],
            sync_outlook=data.get("sync_outlook", False),
            outlook_calendar_id=data.get("outlook_calendar_id"),
            sync_google=data.get("sync_google", False),
            google_calendar_id=data.get("google_calendar_id"),
            default_reminder_minutes=data.get("default_reminder_minutes", 30),
            enable_desktop_notifications=data.get("enable_desktop_notifications", True),
            enable_email_notifications=data.get("enable_email_notifications", False),
            preferences=data.get("preferences") or {},
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


@dataclass
class EventStatistics:
    """إحصائيات الأحداث"""
    total_events: int = 0
    events_today: int = 0
    events_this_week: int = 0
    events_this_month: int = 0
    meetings_count: int = 0
    tasks_count: int = 0
    reminders_count: int = 0
    recurring_events: int = 0
    cancelled_events: int = 0

    @classmethod
    def from_row(cls, row: tuple, columns: List[str]) -> "EventStatistics":
        data = dict(zip(columns, row))
        return cls(
            total_events=data.get("total_events", 0),
            events_today=data.get("events_today", 0),
            events_this_week=data.get("events_this_week", 0),
            events_this_month=data.get("events_this_month", 0),
            meetings_count=data.get("meetings_count", 0),
            tasks_count=data.get("tasks_count", 0),
            reminders_count=data.get("reminders_count", 0),
            recurring_events=data.get("recurring_events", 0),
            cancelled_events=data.get("cancelled_events", 0)
        )


@dataclass
class TimeSlot:
    """فترة زمنية (للعرض في التقويم)"""
    start_time: time
    end_time: time
    events: List[CalendarEvent] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return len(self.events) == 0

    @property
    def has_conflicts(self) -> bool:
        return len(self.events) > 1


@dataclass
class DayEvents:
    """أحداث يوم معين (للعرض)"""
    date: date
    events: List[CalendarEvent] = field(default_factory=list)
    all_day_events: List[CalendarEvent] = field(default_factory=list)
    is_today: bool = False
    is_weekend: bool = False
    is_holiday: bool = False
    holiday_name: Optional[str] = None

    @property
    def total_events(self) -> int:
        return len(self.events) + len(self.all_day_events)

    @property
    def has_events(self) -> bool:
        return self.total_events > 0

    @property
    def day_number(self) -> int:
        return self.date.day

    @property
    def day_name(self) -> str:
        """اسم اليوم بالعربي"""
        day_names = ["الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"]
        return day_names[self.date.weekday()]
