"""
INTEGRA - Task-Calendar Sync
مزامنة المهام مع التقويم
المحور I

التاريخ: 4 فبراير 2026
"""

from datetime import datetime, date, time, timedelta
from typing import Optional, List, Tuple
from core.logging import app_logger

from ..models import CalendarEvent, EventType, EventStatus
from ..repository import create_event, update_event, delete_event, get_events_by_task


class TaskCalendarSync:
    """مزامنة المهام مع التقويم"""

    def __init__(self):
        self._enabled = True

    def sync_task_to_calendar(
        self,
        task_id: int,
        task_title: str,
        task_description: Optional[str] = None,
        due_date: Optional[datetime] = None,
        reminder_date: Optional[datetime] = None,
        category: Optional[str] = None,
        employee_id: Optional[int] = None,
        color: str = "#2ecc71"
    ) -> Optional[int]:
        """
        مزامنة مهمة إلى التقويم

        - إذا كانت المهمة لها تاريخ استحقاق، يتم إنشاء حدث في التقويم
        - إذا كان هناك حدث سابق للمهمة، يتم تحديثه
        """
        if not self._enabled:
            return None

        try:
            # التحقق من وجود حدث سابق
            existing_events = get_events_by_task(task_id)

            if due_date:
                # إنشاء أو تحديث الحدث
                event = CalendarEvent(
                    title=f"📋 {task_title}",
                    description=task_description,
                    event_type=EventType.TASK,
                    start_datetime=due_date,
                    end_datetime=due_date + timedelta(hours=1),
                    is_all_day=False,
                    task_id=task_id,
                    employee_id=employee_id,
                    category=category or "task",
                    color=color,
                    source="integra_task"
                )

                if existing_events:
                    # تحديث الحدث الموجود
                    event.id = existing_events[0].id
                    success = update_event(event)
                    if success:
                        app_logger.info(f"تم تحديث حدث التقويم للمهمة: {task_id}")
                        return event.id
                else:
                    # إنشاء حدث جديد
                    event_id = create_event(event)
                    if event_id:
                        app_logger.info(f"تم إنشاء حدث تقويم للمهمة: {task_id} -> Event {event_id}")
                        return event_id
            else:
                # إذا لم يكن هناك تاريخ استحقاق، حذف الأحداث المرتبطة
                for event in existing_events:
                    if event.id:
                        delete_event(event.id)
                        app_logger.info(f"تم حذف حدث التقويم للمهمة: {task_id}")

            return None

        except Exception as e:
            app_logger.error(f"خطأ في مزامنة المهمة {task_id} مع التقويم: {e}")
            return None

    def sync_calendar_to_task(
        self,
        event_id: int,
        new_start_datetime: datetime
    ) -> Tuple[bool, Optional[int]]:
        """
        مزامنة تغيير في التقويم إلى المهمة

        عند سحب حدث في التقويم، يتم تحديث تاريخ استحقاق المهمة
        """
        if not self._enabled:
            return False, None

        try:
            # البحث عن الحدث
            from ..repository import get_event
            event = get_event(event_id)

            if not event or not event.task_id:
                return False, None

            # تحديث المهمة
            # ملاحظة: يجب استيراد موديول المهام هنا لتجنب الدورة
            try:
                from modules.tasks.repository import get_task, update_task
                from modules.tasks.models import Task

                task = get_task(event.task_id)
                if task:
                    task.due_date = new_start_datetime
                    success = update_task(task)
                    if success:
                        app_logger.info(f"تم تحديث تاريخ المهمة {task.id} من التقويم")
                        return True, task.id
            except ImportError:
                app_logger.warning("لم يتم العثور على موديول المهام")
                return False, None

            return False, None

        except Exception as e:
            app_logger.error(f"خطأ في مزامنة التقويم إلى المهمة: {e}")
            return False, None

    def create_event_from_task(
        self,
        task_id: int,
        task_title: str,
        task_description: Optional[str] = None,
        due_date: Optional[datetime] = None,
        category: Optional[str] = None,
        employee_id: Optional[int] = None,
        priority: Optional[str] = None
    ) -> Optional[CalendarEvent]:
        """
        إنشاء كائن حدث من بيانات المهمة

        هذه الدالة لا تحفظ في قاعدة البيانات، فقط تنشئ الكائن
        """
        if not due_date:
            return None

        # تحديد اللون حسب الأولوية
        color_map = {
            "urgent": "#e74c3c",
            "high": "#f39c12",
            "normal": "#3498db",
            "low": "#95a5a6"
        }
        color = color_map.get(priority or "normal", "#2ecc71")

        event = CalendarEvent(
            title=f"📋 {task_title}",
            description=task_description,
            event_type=EventType.TASK,
            start_datetime=due_date,
            end_datetime=due_date + timedelta(hours=1),
            is_all_day=False,
            task_id=task_id,
            employee_id=employee_id,
            category=category or "task",
            color=color,
            source="integra_task"
        )

        return event

    def update_task_from_event(
        self,
        event: CalendarEvent
    ) -> bool:
        """
        تحديث المهمة من بيانات الحدث

        عند تعديل حدث في التقويم، يتم تحديث المهمة المرتبطة
        """
        if not self._enabled or not event.task_id:
            return False

        try:
            from modules.tasks.repository import get_task, update_task

            task = get_task(event.task_id)
            if not task:
                return False

            # تحديث تاريخ الاستحقاق
            if event.start_datetime:
                task.due_date = event.start_datetime

            success = update_task(task)
            if success:
                app_logger.info(f"تم تحديث المهمة {task.id} من الحدث {event.id}")

            return success

        except ImportError:
            app_logger.warning("لم يتم العثور على موديول المهام")
            return False
        except Exception as e:
            app_logger.error(f"خطأ في تحديث المهمة من الحدث: {e}")
            return False

    def sync_all_tasks(self) -> Tuple[int, int]:
        """
        مزامنة كل المهام مع التقويم

        Returns:
            (عدد المهام المضافة، عدد المهام المحدثة)
        """
        added = 0
        updated = 0

        try:
            from modules.tasks.repository import get_all_tasks

            tasks = get_all_tasks(status=None)  # كل المهام

            for task in tasks:
                if task.due_date:
                    existing = get_events_by_task(task.id)

                    result = self.sync_task_to_calendar(
                        task_id=task.id,
                        task_title=task.title,
                        task_description=task.description,
                        due_date=task.due_date,
                        category=task.category,
                        employee_id=task.employee_id
                    )

                    if result:
                        if existing:
                            updated += 1
                        else:
                            added += 1

            app_logger.info(f"مزامنة المهام: {added} مضافة، {updated} محدثة")

        except ImportError:
            app_logger.warning("لم يتم العثور على موديول المهام")
        except Exception as e:
            app_logger.error(f"خطأ في مزامنة كل المهام: {e}")

        return added, updated

    def enable(self):
        """تفعيل المزامنة"""
        self._enabled = True

    def disable(self):
        """تعطيل المزامنة"""
        self._enabled = False

    @property
    def is_enabled(self) -> bool:
        """هل المزامنة مفعلة؟"""
        return self._enabled


# ═══════════════════════════════════════════════════════════════
# Singleton Instance
# ═══════════════════════════════════════════════════════════════

_sync_instance: Optional[TaskCalendarSync] = None


def get_task_calendar_sync() -> TaskCalendarSync:
    """الحصول على مثيل مزامنة المهام"""
    global _sync_instance
    if _sync_instance is None:
        _sync_instance = TaskCalendarSync()
    return _sync_instance


# ═══════════════════════════════════════════════════════════════
# Convenience Functions
# ═══════════════════════════════════════════════════════════════

def sync_task_to_calendar(
    task_id: int,
    task_title: str,
    task_description: Optional[str] = None,
    due_date: Optional[datetime] = None,
    reminder_date: Optional[datetime] = None,
    category: Optional[str] = None,
    employee_id: Optional[int] = None,
    color: str = "#2ecc71"
) -> Optional[int]:
    """مزامنة مهمة إلى التقويم"""
    return get_task_calendar_sync().sync_task_to_calendar(
        task_id, task_title, task_description, due_date,
        reminder_date, category, employee_id, color
    )


def sync_calendar_to_task(
    event_id: int,
    new_start_datetime: datetime
) -> Tuple[bool, Optional[int]]:
    """مزامنة تغيير في التقويم إلى المهمة"""
    return get_task_calendar_sync().sync_calendar_to_task(event_id, new_start_datetime)


def create_event_from_task(
    task_id: int,
    task_title: str,
    task_description: Optional[str] = None,
    due_date: Optional[datetime] = None,
    category: Optional[str] = None,
    employee_id: Optional[int] = None,
    priority: Optional[str] = None
) -> Optional[CalendarEvent]:
    """إنشاء كائن حدث من مهمة"""
    return get_task_calendar_sync().create_event_from_task(
        task_id, task_title, task_description, due_date,
        category, employee_id, priority
    )


def update_task_from_event(event: CalendarEvent) -> bool:
    """تحديث المهمة من الحدث"""
    return get_task_calendar_sync().update_task_from_event(event)
