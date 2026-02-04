"""
INTEGRA - Recurrence Manager
مدير المهام المتكررة
المحور H

يتعامل مع حساب التكرارات وإنشاء المهام الدورية.

التاريخ: 4 فبراير 2026
"""

from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from typing import Optional, List, Tuple
import calendar

from ..models import (
    Task, TaskStatus, RecurrencePattern, RecurrenceType
)
from ..repository import (
    get_task_repository, get_all_tasks, create_task, update_task
)
from core.logging import app_logger


class RecurrenceManager:
    """
    مدير المهام المتكررة

    يحسب التكرارات القادمة وينشئ مهام دورية.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def calculate_next_occurrence(
        self,
        pattern: RecurrencePattern,
        from_date: Optional[date] = None
    ) -> Optional[date]:
        """
        حساب التاريخ التالي للتكرار

        Args:
            pattern: نمط التكرار
            from_date: التاريخ الابتدائي (افتراضي: اليوم)

        Returns:
            التاريخ التالي أو None إذا انتهى التكرار
        """
        if from_date is None:
            from_date = date.today()

        # Check end conditions
        if pattern.end_type == "date" and pattern.end_date:
            if from_date >= pattern.end_date:
                return None

        next_date = from_date

        if pattern.type == RecurrenceType.DAILY:
            next_date = from_date + timedelta(days=pattern.interval)

        elif pattern.type == RecurrenceType.WEEKLY:
            if pattern.days_of_week:
                # Find next matching day
                next_date = self._find_next_weekday(
                    from_date, pattern.days_of_week, pattern.interval
                )
            else:
                next_date = from_date + timedelta(weeks=pattern.interval)

        elif pattern.type == RecurrenceType.MONTHLY:
            if pattern.day_of_month:
                next_date = self._find_next_month_day(
                    from_date, pattern.day_of_month, pattern.interval
                )
            else:
                next_date = from_date + relativedelta(months=pattern.interval)

        elif pattern.type == RecurrenceType.YEARLY:
            next_date = from_date + relativedelta(years=pattern.interval)

        # Validate against end date
        if pattern.end_type == "date" and pattern.end_date:
            if next_date > pattern.end_date:
                return None

        return next_date

    def _find_next_weekday(
        self,
        from_date: date,
        days_of_week: List[str],
        interval: int
    ) -> date:
        """
        إيجاد اليوم التالي من أيام الأسبوع المحددة
        """
        day_map = {
            "sunday": 6, "monday": 0, "tuesday": 1,
            "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5
        }

        target_days = [day_map.get(d.lower(), 0) for d in days_of_week]
        current_weekday = from_date.weekday()

        # Find next matching day
        for i in range(1, 8 * interval + 1):
            check_date = from_date + timedelta(days=i)
            if check_date.weekday() in target_days:
                return check_date

        return from_date + timedelta(weeks=interval)

    def _find_next_month_day(
        self,
        from_date: date,
        day_of_month: int,
        interval: int
    ) -> date:
        """
        إيجاد اليوم التالي من الشهر
        """
        next_month = from_date + relativedelta(months=interval)

        # Handle months with fewer days
        last_day = calendar.monthrange(next_month.year, next_month.month)[1]
        actual_day = min(day_of_month, last_day)

        return next_month.replace(day=actual_day)

    def create_recurring_instance(
        self,
        parent_task: Task,
        occurrence_date: date
    ) -> Optional[int]:
        """
        إنشاء نسخة من المهمة المتكررة

        Args:
            parent_task: المهمة الأصلية
            occurrence_date: تاريخ التكرار

        Returns:
            معرف المهمة الجديدة
        """
        try:
            # Create new task based on parent
            new_task = Task(
                title=parent_task.title,
                description=parent_task.description,
                status=TaskStatus.PENDING,
                priority=parent_task.priority,
                category=parent_task.category,
                parent_task_id=parent_task.id,
                employee_id=parent_task.employee_id,
                assigned_to=parent_task.assigned_to,
                due_date=datetime.combine(occurrence_date, datetime.min.time()),
                tags=parent_task.tags.copy() if parent_task.tags else [],
                metadata={"recurring_instance": True, "parent_id": parent_task.id}
            )

            task_id = create_task(new_task)

            if task_id:
                app_logger.info(
                    f"Created recurring instance {task_id} for task {parent_task.id}"
                )
            return task_id

        except Exception as e:
            app_logger.error(f"Failed to create recurring instance: {e}")
            return None

    def process_due_recurring_tasks(self) -> Tuple[int, int]:
        """
        معالجة المهام المتكررة المستحقة

        تفحص كل المهام المتكررة وتنشئ نسخ جديدة إذا لزم الأمر.

        Returns:
            (عدد المهام المعالجة، عدد النسخ المنشأة)
        """
        try:
            # Get all recurring tasks
            recurring_tasks = get_all_tasks(is_recurring=True)

            processed = 0
            created = 0
            today = date.today()

            for task in recurring_tasks:
                if not task.recurrence_pattern:
                    continue

                # Check if we need to create new instance
                if task.next_occurrence and task.next_occurrence <= today:
                    # Create instance for today
                    instance_id = self.create_recurring_instance(task, today)
                    if instance_id:
                        created += 1

                    # Calculate and update next occurrence
                    next_date = self.calculate_next_occurrence(
                        task.recurrence_pattern,
                        today
                    )

                    if next_date:
                        task.next_occurrence = next_date
                        update_task(task)
                    else:
                        # Recurrence ended
                        task.is_recurring = False
                        task.recurrence_pattern = None
                        update_task(task)

                    processed += 1

            app_logger.info(
                f"Processed {processed} recurring tasks, created {created} instances"
            )
            return processed, created

        except Exception as e:
            app_logger.error(f"Failed to process recurring tasks: {e}")
            return 0, 0

    def get_upcoming_occurrences(
        self,
        task: Task,
        count: int = 5
    ) -> List[date]:
        """
        الحصول على التكرارات القادمة

        Args:
            task: المهمة المتكررة
            count: عدد التكرارات المطلوبة

        Returns:
            قائمة بالتواريخ القادمة
        """
        if not task.is_recurring or not task.recurrence_pattern:
            return []

        occurrences = []
        current_date = task.next_occurrence or date.today()

        for _ in range(count):
            next_date = self.calculate_next_occurrence(
                task.recurrence_pattern,
                current_date
            )
            if next_date:
                occurrences.append(next_date)
                current_date = next_date
            else:
                break

        return occurrences


# ═══════════════════════════════════════════════════════════════
# Singleton & Quick Access Functions
# ═══════════════════════════════════════════════════════════════

_manager: Optional[RecurrenceManager] = None


def get_recurrence_manager() -> RecurrenceManager:
    """الحصول على instance المدير"""
    global _manager
    if _manager is None:
        _manager = RecurrenceManager()
    return _manager


def calculate_next_occurrence(
    pattern: RecurrencePattern,
    from_date: Optional[date] = None
) -> Optional[date]:
    """حساب التاريخ التالي للتكرار"""
    return get_recurrence_manager().calculate_next_occurrence(pattern, from_date)


def create_recurring_instance(
    parent_task: Task,
    occurrence_date: date
) -> Optional[int]:
    """إنشاء نسخة من المهمة المتكررة"""
    return get_recurrence_manager().create_recurring_instance(parent_task, occurrence_date)


def process_due_recurring_tasks() -> Tuple[int, int]:
    """معالجة المهام المتكررة المستحقة"""
    return get_recurrence_manager().process_due_recurring_tasks()
