"""
INTEGRA - Task Calendar Sync
تكامل المهام مع التقويم
المحور H

يحول المهام إلى أحداث تقويم والعكس.

التاريخ: 4 فبراير 2026
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from ..models import Task, TaskStatus, TaskPriority
from ..repository import get_all_tasks, get_task_by_id, get_overdue_tasks, get_tasks_by_due_date, get_tasks_by_due_date_range

from core.logging import app_logger


@dataclass
class CalendarEvent:
    """
    حدث تقويم مُنشأ من مهمة

    يستخدم للعرض في واجهة التقويم.
    """
    id: str
    title: str
    description: Optional[str] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    all_day: bool = False
    color: str = "#007bff"
    task_id: Optional[int] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    is_overdue: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "start": self.start.isoformat() if self.start else None,
            "end": self.end.isoformat() if self.end else None,
            "allDay": self.all_day,
            "color": self.color,
            "extendedProps": {
                "task_id": self.task_id,
                "status": self.status,
                "priority": self.priority,
                "category": self.category,
                "is_overdue": self.is_overdue,
            }
        }


class TaskCalendarSync:
    """
    مزامنة المهام مع التقويم

    يحول المهام إلى أحداث تقويم ويوفر طرق للبحث حسب التاريخ.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def task_to_event(self, task: Task) -> CalendarEvent:
        """
        تحويل مهمة إلى حدث تقويم

        Args:
            task: المهمة

        Returns:
            حدث التقويم
        """
        # Determine color based on priority and status
        if task.is_overdue:
            color = "#dc3545"  # Red for overdue
        elif task.status == TaskStatus.COMPLETED:
            color = "#28a745"  # Green for completed
        elif task.priority == TaskPriority.URGENT:
            color = "#dc3545"  # Red for urgent
        elif task.priority == TaskPriority.HIGH:
            color = "#fd7e14"  # Orange for high
        else:
            color = task.category_color or "#007bff"

        # Determine start and end times
        start_time = task.due_date or task.start_date or task.created_at
        end_time = None

        if start_time:
            # If only date (no specific time), mark as all-day
            all_day = start_time.hour == 0 and start_time.minute == 0

            if not all_day:
                # Assume 1-hour duration for tasks with specific time
                end_time = start_time + timedelta(hours=1)
        else:
            all_day = True

        # Build title with status indicator
        title_prefix = ""
        if task.status == TaskStatus.COMPLETED:
            title_prefix = "✓ "
        elif task.is_overdue:
            title_prefix = "⚠️ "
        elif task.priority == TaskPriority.URGENT:
            title_prefix = "🔥 "

        return CalendarEvent(
            id=f"task_{task.id}",
            title=f"{title_prefix}{task.title}",
            description=task.description,
            start=start_time,
            end=end_time,
            all_day=all_day,
            color=color,
            task_id=task.id,
            status=task.status.value,
            priority=task.priority.value,
            category=task.category,
            is_overdue=task.is_overdue
        )

    def get_events_for_date(self, target_date: date) -> List[CalendarEvent]:
        """
        جلب أحداث ليوم معين

        Args:
            target_date: التاريخ المطلوب

        Returns:
            قائمة الأحداث
        """
        try:
            tasks = get_tasks_by_due_date(target_date)
            return [self.task_to_event(task) for task in tasks]

        except Exception as e:
            app_logger.error(f"Failed to get events for date: {e}")
            return []

    def get_events_for_range(
        self,
        start_date: date,
        end_date: date
    ) -> List[CalendarEvent]:
        """
        جلب أحداث لفترة زمنية

        Args:
            start_date: بداية الفترة
            end_date: نهاية الفترة

        Returns:
            قائمة الأحداث
        """
        try:
            tasks = get_tasks_by_due_date_range(start_date, end_date)
            return [self.task_to_event(task) for task in tasks]

        except Exception as e:
            app_logger.error(f"Failed to get events for range: {e}")
            return []

    def get_events_for_month(self, year: int, month: int) -> List[CalendarEvent]:
        """
        جلب أحداث لشهر معين

        Args:
            year: السنة
            month: الشهر

        Returns:
            قائمة الأحداث
        """
        import calendar
        _, last_day = calendar.monthrange(year, month)

        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)

        return self.get_events_for_range(start_date, end_date)

    def get_events_for_week(self, week_start: date) -> List[CalendarEvent]:
        """
        جلب أحداث لأسبوع

        Args:
            week_start: بداية الأسبوع

        Returns:
            قائمة الأحداث
        """
        week_end = week_start + timedelta(days=6)
        return self.get_events_for_range(week_start, week_end)

    def get_today_events(self) -> List[CalendarEvent]:
        """جلب أحداث اليوم"""
        return self.get_events_for_date(date.today())

    def get_overdue_events(self) -> List[CalendarEvent]:
        """جلب الأحداث المتأخرة"""
        try:
            tasks = get_overdue_tasks()
            return [self.task_to_event(task) for task in tasks]

        except Exception as e:
            app_logger.error(f"Failed to get overdue events: {e}")
            return []

    def get_upcoming_events(self, days: int = 7) -> List[CalendarEvent]:
        """
        جلب الأحداث القادمة

        Args:
            days: عدد الأيام للأمام

        Returns:
            قائمة الأحداث
        """
        today = date.today()
        end_date = today + timedelta(days=days)
        return self.get_events_for_range(today, end_date)


# ═══════════════════════════════════════════════════════════════
# Singleton & Quick Access Functions
# ═══════════════════════════════════════════════════════════════

_sync: Optional[TaskCalendarSync] = None


def get_task_calendar_sync() -> TaskCalendarSync:
    """الحصول على instance المزامنة"""
    global _sync
    if _sync is None:
        _sync = TaskCalendarSync()
    return _sync


def task_to_calendar_event(task: Task) -> CalendarEvent:
    """تحويل مهمة إلى حدث تقويم"""
    return get_task_calendar_sync().task_to_event(task)


def sync_task_to_calendar(task_id: int) -> Optional[CalendarEvent]:
    """مزامنة مهمة محددة"""
    task = get_task_by_id(task_id)
    if task:
        return task_to_calendar_event(task)
    return None


def get_tasks_for_date(target_date: date) -> List[CalendarEvent]:
    """جلب مهام ليوم معين"""
    return get_task_calendar_sync().get_events_for_date(target_date)


def get_tasks_for_range(start_date: date, end_date: date) -> List[CalendarEvent]:
    """جلب مهام لفترة زمنية"""
    return get_task_calendar_sync().get_events_for_range(start_date, end_date)
