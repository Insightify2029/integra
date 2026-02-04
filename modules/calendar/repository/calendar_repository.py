"""
INTEGRA - Calendar Repository
موديول التقويم - مستودع البيانات (CRUD)
المحور I

التاريخ: 4 فبراير 2026
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Tuple, Dict, Any
import json

from core.database import select_all, select_one, insert_returning_id, update, delete
from core.logging import app_logger

from ..models import (
    CalendarEvent,
    CalendarCategory,
    PublicHoliday,
    CalendarSettings,
    EventStatistics,
    EventType,
    EventStatus,
    RecurrencePattern,
    RecurrenceType,
)


class CalendarRepository:
    """مستودع بيانات التقويم"""

    # ═══════════════════════════════════════════════════════════════
    # Event CRUD
    # ═══════════════════════════════════════════════════════════════

    def create_event(self, event: CalendarEvent) -> Optional[int]:
        """إنشاء حدث جديد"""
        try:
            sql = """
                INSERT INTO calendar_events (
                    title, description, event_type,
                    start_datetime, end_datetime, is_all_day, timezone,
                    task_id, employee_id,
                    reminders, attendees,
                    is_recurring, recurrence_pattern, recurrence_end_date, parent_event_id,
                    color, category,
                    location, location_url,
                    source, external_id, external_link,
                    status, is_private,
                    metadata, created_by
                ) VALUES (
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s, %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s
                )
                RETURNING id
            """

            params = (
                event.title,
                event.description,
                event.event_type.value,
                event.start_datetime,
                event.end_datetime,
                event.is_all_day,
                event.timezone,
                event.task_id,
                event.employee_id,
                json.dumps([r.to_dict() for r in event.reminders], ensure_ascii=False),
                json.dumps([a.to_dict() for a in event.attendees], ensure_ascii=False),
                event.is_recurring,
                event.recurrence_pattern.to_json() if event.recurrence_pattern else None,
                event.recurrence_end_date,
                event.parent_event_id,
                event.color,
                event.category,
                event.location,
                event.location_url,
                event.source,
                event.external_id,
                event.external_link,
                event.status.value,
                event.is_private,
                json.dumps(event.metadata, ensure_ascii=False) if event.metadata else "{}",
                event.created_by
            )

            event_id = insert_returning_id(sql, params)
            app_logger.info(f"تم إنشاء حدث جديد: {event.title} (ID: {event_id})")
            return event_id

        except Exception as e:
            app_logger.error(f"خطأ في إنشاء الحدث: {e}")
            return None

    def get_event(self, event_id: int) -> Optional[CalendarEvent]:
        """جلب حدث بالمعرف"""
        try:
            sql = "SELECT * FROM calendar_events_view WHERE id = %s"
            columns, row = select_one(sql, (event_id,))
            if row:
                return CalendarEvent.from_row(row, columns)
            return None
        except Exception as e:
            app_logger.error(f"خطأ في جلب الحدث {event_id}: {e}")
            return None

    def update_event(self, event: CalendarEvent) -> bool:
        """تحديث حدث"""
        if not event.id:
            return False

        try:
            sql = """
                UPDATE calendar_events SET
                    title = %s,
                    description = %s,
                    event_type = %s,
                    start_datetime = %s,
                    end_datetime = %s,
                    is_all_day = %s,
                    timezone = %s,
                    task_id = %s,
                    employee_id = %s,
                    reminders = %s,
                    attendees = %s,
                    is_recurring = %s,
                    recurrence_pattern = %s,
                    recurrence_end_date = %s,
                    color = %s,
                    category = %s,
                    location = %s,
                    location_url = %s,
                    status = %s,
                    is_private = %s,
                    metadata = %s,
                    updated_by = %s
                WHERE id = %s
            """

            params = (
                event.title,
                event.description,
                event.event_type.value,
                event.start_datetime,
                event.end_datetime,
                event.is_all_day,
                event.timezone,
                event.task_id,
                event.employee_id,
                json.dumps([r.to_dict() for r in event.reminders], ensure_ascii=False),
                json.dumps([a.to_dict() for a in event.attendees], ensure_ascii=False),
                event.is_recurring,
                event.recurrence_pattern.to_json() if event.recurrence_pattern else None,
                event.recurrence_end_date,
                event.color,
                event.category,
                event.location,
                event.location_url,
                event.status.value,
                event.is_private,
                json.dumps(event.metadata, ensure_ascii=False) if event.metadata else "{}",
                event.updated_by,
                event.id
            )

            update(sql, params)
            app_logger.info(f"تم تحديث الحدث: {event.title} (ID: {event.id})")
            return True

        except Exception as e:
            app_logger.error(f"خطأ في تحديث الحدث {event.id}: {e}")
            return False

    def delete_event(self, event_id: int) -> bool:
        """حذف حدث"""
        try:
            sql = "DELETE FROM calendar_events WHERE id = %s"
            delete(sql, (event_id,))
            app_logger.info(f"تم حذف الحدث: {event_id}")
            return True
        except Exception as e:
            app_logger.error(f"خطأ في حذف الحدث {event_id}: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════
    # Event Queries
    # ═══════════════════════════════════════════════════════════════

    def get_all_events(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[EventStatus] = None,
        event_type: Optional[EventType] = None,
        category: Optional[str] = None
    ) -> List[CalendarEvent]:
        """جلب كل الأحداث مع فلترة"""
        try:
            conditions = []
            params = []

            if status:
                conditions.append("status = %s")
                params.append(status.value)

            if event_type:
                conditions.append("event_type = %s")
                params.append(event_type.value)

            if category:
                conditions.append("category = %s")
                params.append(category)

            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)

            sql = f"""
                SELECT * FROM calendar_events_view
                {where_clause}
                ORDER BY start_datetime DESC
                LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])

            columns, rows = select_all(sql, tuple(params))
            return [CalendarEvent.from_row(row, columns) for row in rows]

        except Exception as e:
            app_logger.error(f"خطأ في جلب الأحداث: {e}")
            return []

    def get_events_in_range(
        self,
        start_date: datetime,
        end_date: datetime,
        category: Optional[str] = None,
        event_type: Optional[EventType] = None
    ) -> List[CalendarEvent]:
        """جلب الأحداث في نطاق تاريخ معين"""
        try:
            conditions = [
                """(
                    (start_datetime >= %s AND start_datetime < %s)
                    OR (end_datetime > %s AND end_datetime <= %s)
                    OR (start_datetime <= %s AND end_datetime >= %s)
                )"""
            ]
            params = [start_date, end_date, start_date, end_date, start_date, end_date]

            if category:
                conditions.append("category = %s")
                params.append(category)

            if event_type:
                conditions.append("event_type = %s")
                params.append(event_type.value)

            conditions.append("status != 'cancelled'")

            sql = f"""
                SELECT * FROM calendar_events_view
                WHERE {" AND ".join(conditions)}
                ORDER BY start_datetime
            """

            columns, rows = select_all(sql, tuple(params))
            return [CalendarEvent.from_row(row, columns) for row in rows]

        except Exception as e:
            app_logger.error(f"خطأ في جلب الأحداث في النطاق: {e}")
            return []

    def get_events_by_date(self, target_date: date) -> List[CalendarEvent]:
        """جلب أحداث يوم معين"""
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())
        return self.get_events_in_range(start, end)

    def get_events_today(self) -> List[CalendarEvent]:
        """جلب أحداث اليوم"""
        return self.get_events_by_date(date.today())

    def get_events_this_week(self) -> List[CalendarEvent]:
        """جلب أحداث الأسبوع الحالي"""
        today = date.today()
        # الأحد = 6 في Python
        days_since_sunday = (today.weekday() + 1) % 7
        week_start = today - timedelta(days=days_since_sunday)
        week_end = week_start + timedelta(days=7)

        start = datetime.combine(week_start, datetime.min.time())
        end = datetime.combine(week_end, datetime.max.time())
        return self.get_events_in_range(start, end)

    def get_events_this_month(self) -> List[CalendarEvent]:
        """جلب أحداث الشهر الحالي"""
        today = date.today()
        month_start = today.replace(day=1)
        # آخر يوم في الشهر
        if today.month == 12:
            month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

        start = datetime.combine(month_start, datetime.min.time())
        end = datetime.combine(month_end, datetime.max.time())
        return self.get_events_in_range(start, end)

    def get_upcoming_events(self, limit: int = 10) -> List[CalendarEvent]:
        """جلب الأحداث القادمة"""
        try:
            sql = """
                SELECT * FROM calendar_events_view
                WHERE start_datetime >= NOW()
                  AND status != 'cancelled'
                ORDER BY start_datetime
                LIMIT %s
            """
            columns, rows = select_all(sql, (limit,))
            return [CalendarEvent.from_row(row, columns) for row in rows]
        except Exception as e:
            app_logger.error(f"خطأ في جلب الأحداث القادمة: {e}")
            return []

    def get_events_by_task(self, task_id: int) -> List[CalendarEvent]:
        """جلب الأحداث المرتبطة بمهمة"""
        try:
            sql = """
                SELECT * FROM calendar_events_view
                WHERE task_id = %s
                ORDER BY start_datetime
            """
            columns, rows = select_all(sql, (task_id,))
            return [CalendarEvent.from_row(row, columns) for row in rows]
        except Exception as e:
            app_logger.error(f"خطأ في جلب أحداث المهمة {task_id}: {e}")
            return []

    def get_events_by_employee(self, employee_id: int) -> List[CalendarEvent]:
        """جلب الأحداث المرتبطة بموظف"""
        try:
            sql = """
                SELECT * FROM calendar_events_view
                WHERE employee_id = %s
                ORDER BY start_datetime DESC
            """
            columns, rows = select_all(sql, (employee_id,))
            return [CalendarEvent.from_row(row, columns) for row in rows]
        except Exception as e:
            app_logger.error(f"خطأ في جلب أحداث الموظف {employee_id}: {e}")
            return []

    # ═══════════════════════════════════════════════════════════════
    # Categories
    # ═══════════════════════════════════════════════════════════════

    def get_all_categories(self) -> List[CalendarCategory]:
        """جلب كل التصنيفات"""
        try:
            sql = """
                SELECT * FROM calendar_categories
                WHERE is_visible = TRUE
                ORDER BY sort_order, name
            """
            columns, rows = select_all(sql)
            return [CalendarCategory.from_row(row, columns) for row in rows]
        except Exception as e:
            app_logger.error(f"خطأ في جلب التصنيفات: {e}")
            return []

    def get_category_by_name(self, name: str) -> Optional[CalendarCategory]:
        """جلب تصنيف بالاسم"""
        try:
            sql = "SELECT * FROM calendar_categories WHERE name = %s"
            columns, row = select_one(sql, (name,))
            if row:
                return CalendarCategory.from_row(row, columns)
            return None
        except Exception as e:
            app_logger.error(f"خطأ في جلب التصنيف {name}: {e}")
            return None

    # ═══════════════════════════════════════════════════════════════
    # Holidays
    # ═══════════════════════════════════════════════════════════════

    def get_holidays_in_range(
        self,
        start_date: date,
        end_date: date,
        country_code: str = "SA"
    ) -> List[PublicHoliday]:
        """جلب العطلات في نطاق"""
        try:
            sql = """
                SELECT * FROM public_holidays
                WHERE holiday_date >= %s AND holiday_date <= %s
                  AND country_code = %s
                ORDER BY holiday_date
            """
            columns, rows = select_all(sql, (start_date, end_date, country_code))
            return [PublicHoliday.from_row(row, columns) for row in rows]
        except Exception as e:
            app_logger.error(f"خطأ في جلب العطلات: {e}")
            return []

    def get_holidays_by_year(self, year: int, country_code: str = "SA") -> List[PublicHoliday]:
        """جلب عطلات سنة معينة"""
        start = date(year, 1, 1)
        end = date(year, 12, 31)
        return self.get_holidays_in_range(start, end, country_code)

    # ═══════════════════════════════════════════════════════════════
    # Settings
    # ═══════════════════════════════════════════════════════════════

    def get_calendar_settings(self, user_id: Optional[int] = None) -> CalendarSettings:
        """جلب إعدادات التقويم"""
        try:
            if user_id:
                sql = "SELECT * FROM calendar_settings WHERE user_id = %s"
                columns, row = select_one(sql, (user_id,))
                if row:
                    return CalendarSettings.from_row(row, columns)

            # إرجاع الإعدادات الافتراضية
            return CalendarSettings()

        except Exception as e:
            app_logger.error(f"خطأ في جلب إعدادات التقويم: {e}")
            return CalendarSettings()

    def save_calendar_settings(self, settings: CalendarSettings) -> bool:
        """حفظ إعدادات التقويم"""
        try:
            # التحقق من وجود إعدادات للمستخدم
            if settings.user_id:
                sql = "SELECT id FROM calendar_settings WHERE user_id = %s"
                columns, row = select_one(sql, (settings.user_id,))

                if row:
                    # تحديث
                    sql = """
                        UPDATE calendar_settings SET
                            default_view = %s,
                            week_starts_on = %s,
                            show_weekends = %s,
                            show_week_numbers = %s,
                            work_hours_start = %s,
                            work_hours_end = %s,
                            work_days = %s,
                            sync_outlook = %s,
                            outlook_calendar_id = %s,
                            sync_google = %s,
                            google_calendar_id = %s,
                            default_reminder_minutes = %s,
                            enable_desktop_notifications = %s,
                            enable_email_notifications = %s,
                            preferences = %s
                        WHERE user_id = %s
                    """
                else:
                    # إدراج
                    sql = """
                        INSERT INTO calendar_settings (
                            default_view, week_starts_on, show_weekends, show_week_numbers,
                            work_hours_start, work_hours_end, work_days,
                            sync_outlook, outlook_calendar_id, sync_google, google_calendar_id,
                            default_reminder_minutes, enable_desktop_notifications, enable_email_notifications,
                            preferences, user_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """

                params = (
                    settings.default_view.value,
                    settings.week_starts_on,
                    settings.show_weekends,
                    settings.show_week_numbers,
                    settings.work_hours_start,
                    settings.work_hours_end,
                    settings.work_days,
                    settings.sync_outlook,
                    settings.outlook_calendar_id,
                    settings.sync_google,
                    settings.google_calendar_id,
                    settings.default_reminder_minutes,
                    settings.enable_desktop_notifications,
                    settings.enable_email_notifications,
                    json.dumps(settings.preferences, ensure_ascii=False),
                    settings.user_id
                )

                update(sql, params)
                return True

            return False

        except Exception as e:
            app_logger.error(f"خطأ في حفظ إعدادات التقويم: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════
    # Statistics
    # ═══════════════════════════════════════════════════════════════

    def get_event_statistics(self) -> EventStatistics:
        """جلب إحصائيات الأحداث"""
        try:
            sql = """
                SELECT
                    COUNT(*) as total_events,
                    COUNT(*) FILTER (WHERE DATE(start_datetime) = CURRENT_DATE) as events_today,
                    COUNT(*) FILTER (WHERE DATE(start_datetime) >= DATE_TRUNC('week', CURRENT_DATE)
                                    AND DATE(start_datetime) < DATE_TRUNC('week', CURRENT_DATE) + INTERVAL '7 days') as events_this_week,
                    COUNT(*) FILTER (WHERE DATE_TRUNC('month', start_datetime) = DATE_TRUNC('month', CURRENT_DATE)) as events_this_month,
                    COUNT(*) FILTER (WHERE event_type = 'meeting') as meetings_count,
                    COUNT(*) FILTER (WHERE event_type = 'task') as tasks_count,
                    COUNT(*) FILTER (WHERE event_type = 'reminder') as reminders_count,
                    COUNT(*) FILTER (WHERE is_recurring = TRUE) as recurring_events,
                    COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled_events
                FROM calendar_events
            """
            columns, row = select_one(sql)
            if row:
                return EventStatistics.from_row(row, columns)
            return EventStatistics()
        except Exception as e:
            app_logger.error(f"خطأ في جلب إحصائيات الأحداث: {e}")
            return EventStatistics()

    # ═══════════════════════════════════════════════════════════════
    # Conflict Detection
    # ═══════════════════════════════════════════════════════════════

    def check_conflicts(
        self,
        start_datetime: datetime,
        end_datetime: datetime,
        exclude_event_id: Optional[int] = None
    ) -> List[CalendarEvent]:
        """التحقق من تعارض الأحداث"""
        try:
            conditions = [
                "status != 'cancelled'",
                "is_all_day = FALSE",
                """(
                    (start_datetime >= %s AND start_datetime < %s)
                    OR (end_datetime > %s AND end_datetime <= %s)
                    OR (start_datetime <= %s AND end_datetime >= %s)
                )"""
            ]
            params = [start_datetime, end_datetime, start_datetime, end_datetime, start_datetime, end_datetime]

            if exclude_event_id:
                conditions.append("id != %s")
                params.append(exclude_event_id)

            sql = f"""
                SELECT * FROM calendar_events_view
                WHERE {" AND ".join(conditions)}
                ORDER BY start_datetime
            """

            columns, rows = select_all(sql, tuple(params))
            return [CalendarEvent.from_row(row, columns) for row in rows]

        except Exception as e:
            app_logger.error(f"خطأ في التحقق من التعارضات: {e}")
            return []

    # ═══════════════════════════════════════════════════════════════
    # Recurrence
    # ═══════════════════════════════════════════════════════════════

    def generate_recurring_events(
        self,
        parent_event: CalendarEvent,
        until_date: date
    ) -> List[CalendarEvent]:
        """توليد الأحداث المتكررة"""
        if not parent_event.is_recurring or not parent_event.recurrence_pattern:
            return []

        generated = []
        pattern = parent_event.recurrence_pattern
        current_date = parent_event.start_datetime.date() if parent_event.start_datetime else date.today()

        # حساب المدة الأصلية
        duration = timedelta(hours=1)
        if parent_event.start_datetime and parent_event.end_datetime:
            duration = parent_event.end_datetime - parent_event.start_datetime

        count = 0
        max_count = pattern.end_count or 365  # حد أقصى للتكرارات

        while current_date <= until_date and count < max_count:
            # تخطي التاريخ الأصلي
            if parent_event.start_datetime and current_date == parent_event.start_datetime.date():
                current_date = self._get_next_occurrence(current_date, pattern)
                continue

            # التحقق من تاريخ الانتهاء
            if pattern.end_date and current_date > pattern.end_date:
                break

            # التحقق من أيام الأسبوع (للأسبوعي)
            if pattern.type == RecurrenceType.WEEKLY and pattern.days_of_week:
                day_of_week = (current_date.weekday() + 1) % 7  # تحويل إلى 0=الأحد
                if day_of_week not in pattern.days_of_week:
                    current_date = self._get_next_occurrence(current_date, pattern)
                    continue

            # إنشاء الحدث المتكرر
            start_time = parent_event.start_datetime.time() if parent_event.start_datetime else datetime.min.time()
            new_start = datetime.combine(current_date, start_time)
            new_end = new_start + duration

            new_event = CalendarEvent(
                title=parent_event.title,
                description=parent_event.description,
                event_type=parent_event.event_type,
                start_datetime=new_start,
                end_datetime=new_end,
                is_all_day=parent_event.is_all_day,
                timezone=parent_event.timezone,
                task_id=parent_event.task_id,
                employee_id=parent_event.employee_id,
                color=parent_event.color,
                category=parent_event.category,
                location=parent_event.location,
                location_url=parent_event.location_url,
                parent_event_id=parent_event.id,
                is_recurring=False
            )

            generated.append(new_event)
            count += 1

            current_date = self._get_next_occurrence(current_date, pattern)

        return generated

    def _get_next_occurrence(self, current: date, pattern: RecurrencePattern) -> date:
        """حساب التاريخ التالي للتكرار"""
        if pattern.type == RecurrenceType.DAILY:
            return current + timedelta(days=pattern.interval)

        elif pattern.type == RecurrenceType.WEEKLY:
            return current + timedelta(weeks=pattern.interval)

        elif pattern.type == RecurrenceType.MONTHLY:
            # إضافة أشهر
            month = current.month + pattern.interval
            year = current.year + (month - 1) // 12
            month = ((month - 1) % 12) + 1
            day = pattern.day_of_month or current.day
            # تصحيح اليوم إذا كان أكبر من أيام الشهر
            while True:
                try:
                    return date(year, month, day)
                except ValueError:
                    day -= 1

        elif pattern.type == RecurrenceType.YEARLY:
            return current.replace(year=current.year + pattern.interval)

        return current + timedelta(days=1)


# ═══════════════════════════════════════════════════════════════
# Singleton Instance
# ═══════════════════════════════════════════════════════════════

_repository: Optional[CalendarRepository] = None


def get_calendar_repository() -> CalendarRepository:
    """الحصول على مثيل مستودع التقويم"""
    global _repository
    if _repository is None:
        _repository = CalendarRepository()
    return _repository


# ═══════════════════════════════════════════════════════════════
# Convenience Functions
# ═══════════════════════════════════════════════════════════════

def create_event(event: CalendarEvent) -> Optional[int]:
    """إنشاء حدث جديد"""
    return get_calendar_repository().create_event(event)


def get_event(event_id: int) -> Optional[CalendarEvent]:
    """جلب حدث بالمعرف"""
    return get_calendar_repository().get_event(event_id)


def update_event(event: CalendarEvent) -> bool:
    """تحديث حدث"""
    return get_calendar_repository().update_event(event)


def delete_event(event_id: int) -> bool:
    """حذف حدث"""
    return get_calendar_repository().delete_event(event_id)


def get_all_events(
    limit: int = 100,
    offset: int = 0,
    status: Optional[EventStatus] = None,
    event_type: Optional[EventType] = None,
    category: Optional[str] = None
) -> List[CalendarEvent]:
    """جلب كل الأحداث"""
    return get_calendar_repository().get_all_events(limit, offset, status, event_type, category)


def get_events_in_range(
    start_date: datetime,
    end_date: datetime,
    category: Optional[str] = None,
    event_type: Optional[EventType] = None
) -> List[CalendarEvent]:
    """جلب الأحداث في نطاق"""
    return get_calendar_repository().get_events_in_range(start_date, end_date, category, event_type)


def get_events_by_date(target_date: date) -> List[CalendarEvent]:
    """جلب أحداث يوم معين"""
    return get_calendar_repository().get_events_by_date(target_date)


def get_events_today() -> List[CalendarEvent]:
    """جلب أحداث اليوم"""
    return get_calendar_repository().get_events_today()


def get_events_this_week() -> List[CalendarEvent]:
    """جلب أحداث الأسبوع"""
    return get_calendar_repository().get_events_this_week()


def get_events_this_month() -> List[CalendarEvent]:
    """جلب أحداث الشهر"""
    return get_calendar_repository().get_events_this_month()


def get_upcoming_events(limit: int = 10) -> List[CalendarEvent]:
    """جلب الأحداث القادمة"""
    return get_calendar_repository().get_upcoming_events(limit)


def get_events_by_task(task_id: int) -> List[CalendarEvent]:
    """جلب أحداث المهمة"""
    return get_calendar_repository().get_events_by_task(task_id)


def get_events_by_employee(employee_id: int) -> List[CalendarEvent]:
    """جلب أحداث الموظف"""
    return get_calendar_repository().get_events_by_employee(employee_id)


def get_all_categories() -> List[CalendarCategory]:
    """جلب كل التصنيفات"""
    return get_calendar_repository().get_all_categories()


def get_category_by_name(name: str) -> Optional[CalendarCategory]:
    """جلب تصنيف بالاسم"""
    return get_calendar_repository().get_category_by_name(name)


def get_holidays_in_range(
    start_date: date,
    end_date: date,
    country_code: str = "SA"
) -> List[PublicHoliday]:
    """جلب العطلات"""
    return get_calendar_repository().get_holidays_in_range(start_date, end_date, country_code)


def get_holidays_by_year(year: int, country_code: str = "SA") -> List[PublicHoliday]:
    """جلب عطلات السنة"""
    return get_calendar_repository().get_holidays_by_year(year, country_code)


def get_calendar_settings(user_id: Optional[int] = None) -> CalendarSettings:
    """جلب إعدادات التقويم"""
    return get_calendar_repository().get_calendar_settings(user_id)


def save_calendar_settings(settings: CalendarSettings) -> bool:
    """حفظ إعدادات التقويم"""
    return get_calendar_repository().save_calendar_settings(settings)


def get_event_statistics() -> EventStatistics:
    """جلب إحصائيات الأحداث"""
    return get_calendar_repository().get_event_statistics()


def check_conflicts(
    start_datetime: datetime,
    end_datetime: datetime,
    exclude_event_id: Optional[int] = None
) -> List[CalendarEvent]:
    """التحقق من التعارضات"""
    return get_calendar_repository().check_conflicts(start_datetime, end_datetime, exclude_event_id)


def generate_recurring_events(
    parent_event: CalendarEvent,
    until_date: date
) -> List[CalendarEvent]:
    """توليد الأحداث المتكررة"""
    return get_calendar_repository().generate_recurring_events(parent_event, until_date)
