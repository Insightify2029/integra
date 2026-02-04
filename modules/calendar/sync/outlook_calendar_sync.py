"""
INTEGRA - Outlook Calendar Sync
مزامنة التقويم مع Outlook
المحور I

التاريخ: 4 فبراير 2026
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Tuple, Dict, Any
import threading
from core.logging import app_logger

from ..models import (
    CalendarEvent, EventType, EventStatus,
    Attendee, AttendeeStatus, Reminder, ReminderType
)
from ..repository import (
    create_event, update_event, get_event, get_all_events
)


class OutlookCalendarSync:
    """مزامنة التقويم مع Outlook"""

    def __init__(self):
        self._outlook = None
        self._namespace = None
        self._calendar_folder = None
        self._connected = False
        self._lock = threading.Lock()

    def connect(self) -> bool:
        """الاتصال بـ Outlook"""
        with self._lock:
            if self._connected:
                return True

            try:
                import win32com.client

                self._outlook = win32com.client.Dispatch("Outlook.Application")
                self._namespace = self._outlook.GetNamespace("MAPI")
                # 9 = olFolderCalendar
                self._calendar_folder = self._namespace.GetDefaultFolder(9)
                self._connected = True
                app_logger.info("تم الاتصال بتقويم Outlook")
                return True

            except ImportError:
                app_logger.warning("pywin32 غير مثبت - مزامنة Outlook غير متاحة")
                return False
            except Exception as e:
                app_logger.error(f"خطأ في الاتصال بـ Outlook: {e}")
                return False

    def disconnect(self):
        """قطع الاتصال"""
        with self._lock:
            self._outlook = None
            self._namespace = None
            self._calendar_folder = None
            self._connected = False

    def is_available(self) -> bool:
        """هل Outlook متاح؟"""
        if not self._connected:
            return self.connect()
        return self._connected

    def get_outlook_events(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        جلب الأحداث من Outlook

        Returns:
            قائمة بالأحداث كقواميس
        """
        if not self.is_available():
            return []

        try:
            events = []

            # تحديد النطاق الزمني
            if not start_date:
                start_date = date.today()
            if not end_date:
                end_date = start_date + timedelta(days=30)

            # تصفية الأحداث حسب التاريخ
            items = self._calendar_folder.Items
            items.Sort("[Start]")
            items.IncludeRecurrences = True

            # فلتر التاريخ
            start_str = start_date.strftime("%m/%d/%Y")
            end_str = end_date.strftime("%m/%d/%Y")
            restriction = f"[Start] >= '{start_str}' AND [Start] <= '{end_str}'"
            filtered_items = items.Restrict(restriction)

            count = 0
            for item in filtered_items:
                if count >= limit:
                    break

                try:
                    event_data = {
                        "entry_id": item.EntryID,
                        "subject": item.Subject,
                        "body": item.Body,
                        "start": item.Start,
                        "end": item.End,
                        "all_day_event": item.AllDayEvent,
                        "location": item.Location,
                        "organizer": item.Organizer,
                        "is_recurring": item.IsRecurring,
                        "importance": item.Importance,
                        "sensitivity": item.Sensitivity,
                        "categories": item.Categories,
                    }

                    # المشاركون
                    attendees = []
                    for recipient in item.Recipients:
                        attendees.append({
                            "name": recipient.Name,
                            "address": recipient.Address,
                            "type": recipient.Type  # 1=Required, 2=Optional
                        })
                    event_data["attendees"] = attendees

                    events.append(event_data)
                    count += 1

                except Exception as e:
                    app_logger.warning(f"خطأ في قراءة حدث Outlook: {e}")
                    continue

            app_logger.info(f"تم جلب {len(events)} حدث من Outlook")
            return events

        except Exception as e:
            app_logger.error(f"خطأ في جلب أحداث Outlook: {e}")
            return []

    def sync_from_outlook(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Tuple[int, int, int]:
        """
        مزامنة الأحداث من Outlook إلى INTEGRA

        Returns:
            (أحداث جديدة، أحداث محدثة، أحداث فشلت)
        """
        added = 0
        updated = 0
        failed = 0

        outlook_events = self.get_outlook_events(start_date, end_date)

        for outlook_event in outlook_events:
            try:
                # التحقق من وجود الحدث (بواسطة external_id)
                external_id = outlook_event.get("entry_id")
                existing = self._find_event_by_external_id(external_id)

                # تحويل إلى CalendarEvent
                event = self._outlook_to_calendar_event(outlook_event)

                if existing:
                    # تحديث الحدث الموجود
                    event.id = existing.id
                    if update_event(event):
                        updated += 1
                    else:
                        failed += 1
                else:
                    # إضافة حدث جديد
                    if create_event(event):
                        added += 1
                    else:
                        failed += 1

            except Exception as e:
                app_logger.error(f"خطأ في مزامنة حدث Outlook: {e}")
                failed += 1

        app_logger.info(f"مزامنة من Outlook: {added} جديد، {updated} محدث، {failed} فشل")
        return added, updated, failed

    def sync_to_outlook(
        self,
        events: Optional[List[CalendarEvent]] = None
    ) -> Tuple[int, int, int]:
        """
        مزامنة الأحداث من INTEGRA إلى Outlook

        Returns:
            (أحداث جديدة، أحداث محدثة، أحداث فشلت)
        """
        if not self.is_available():
            return 0, 0, 0

        added = 0
        updated = 0
        failed = 0

        if not events:
            events = get_all_events(limit=100)

        for event in events:
            try:
                # تجاهل الأحداث القادمة من Outlook
                if event.source == "outlook":
                    continue

                if event.external_id:
                    # محاولة تحديث الحدث الموجود
                    if self._update_outlook_event(event):
                        updated += 1
                    else:
                        failed += 1
                else:
                    # إنشاء حدث جديد في Outlook
                    external_id = self._create_outlook_event(event)
                    if external_id:
                        # تحديث external_id في قاعدة البيانات
                        event.external_id = external_id
                        event.source = "integra"
                        update_event(event)
                        added += 1
                    else:
                        failed += 1

            except Exception as e:
                app_logger.error(f"خطأ في مزامنة حدث إلى Outlook: {e}")
                failed += 1

        app_logger.info(f"مزامنة إلى Outlook: {added} جديد، {updated} محدث، {failed} فشل")
        return added, updated, failed

    def create_outlook_event(
        self,
        title: str,
        start_datetime: datetime,
        end_datetime: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        is_all_day: bool = False
    ) -> Optional[str]:
        """
        إنشاء حدث جديد في Outlook

        Returns:
            EntryID للحدث الجديد
        """
        if not self.is_available():
            return None

        try:
            # 1 = olAppointmentItem
            item = self._outlook.CreateItem(1)

            item.Subject = title
            item.Start = start_datetime
            item.End = end_datetime
            item.AllDayEvent = is_all_day

            if description:
                item.Body = description

            if location:
                item.Location = location

            item.Save()

            app_logger.info(f"تم إنشاء حدث في Outlook: {title}")
            return item.EntryID

        except Exception as e:
            app_logger.error(f"خطأ في إنشاء حدث Outlook: {e}")
            return None

    def _create_outlook_event(self, event: CalendarEvent) -> Optional[str]:
        """إنشاء حدث Outlook من CalendarEvent"""
        return self.create_outlook_event(
            title=event.title,
            start_datetime=event.start_datetime,
            end_datetime=event.end_datetime or (event.start_datetime + timedelta(hours=1)),
            description=event.description,
            location=event.location,
            is_all_day=event.is_all_day
        )

    def _update_outlook_event(self, event: CalendarEvent) -> bool:
        """تحديث حدث Outlook موجود"""
        if not self.is_available() or not event.external_id:
            return False

        try:
            item = self._namespace.GetItemFromID(event.external_id)

            item.Subject = event.title
            item.Start = event.start_datetime
            item.End = event.end_datetime or (event.start_datetime + timedelta(hours=1))
            item.AllDayEvent = event.is_all_day

            if event.description:
                item.Body = event.description

            if event.location:
                item.Location = event.location

            item.Save()

            app_logger.info(f"تم تحديث حدث Outlook: {event.title}")
            return True

        except Exception as e:
            app_logger.error(f"خطأ في تحديث حدث Outlook: {e}")
            return False

    def _find_event_by_external_id(self, external_id: str) -> Optional[CalendarEvent]:
        """البحث عن حدث بواسطة external_id"""
        try:
            from core.database import select_one
            sql = "SELECT * FROM calendar_events_view WHERE external_id = %s"
            columns, row = select_one(sql, (external_id,))
            if row:
                return CalendarEvent.from_row(row, columns)
            return None
        except Exception:
            return None

    def _outlook_to_calendar_event(self, outlook_data: Dict[str, Any]) -> CalendarEvent:
        """تحويل بيانات Outlook إلى CalendarEvent"""
        # تحديد نوع الحدث
        event_type = EventType.EVENT
        categories = outlook_data.get("categories", "")
        if categories:
            if "meeting" in categories.lower() or "اجتماع" in categories:
                event_type = EventType.MEETING
            elif "task" in categories.lower() or "مهمة" in categories:
                event_type = EventType.TASK

        # المشاركون
        attendees = []
        for att in outlook_data.get("attendees", []):
            attendees.append(Attendee(
                email=att.get("address", ""),
                name=att.get("name"),
                status=AttendeeStatus.PENDING
            ))

        event = CalendarEvent(
            title=outlook_data.get("subject", ""),
            description=outlook_data.get("body"),
            event_type=event_type,
            start_datetime=outlook_data.get("start"),
            end_datetime=outlook_data.get("end"),
            is_all_day=outlook_data.get("all_day_event", False),
            location=outlook_data.get("location"),
            is_recurring=outlook_data.get("is_recurring", False),
            attendees=attendees,
            source="outlook",
            external_id=outlook_data.get("entry_id"),
            category=categories.split(",")[0] if categories else None
        )

        return event


# ═══════════════════════════════════════════════════════════════
# Singleton Instance
# ═══════════════════════════════════════════════════════════════

_sync_instance: Optional[OutlookCalendarSync] = None


def get_outlook_calendar_sync() -> OutlookCalendarSync:
    """الحصول على مثيل مزامنة Outlook"""
    global _sync_instance
    if _sync_instance is None:
        _sync_instance = OutlookCalendarSync()
    return _sync_instance


def is_outlook_calendar_available() -> bool:
    """هل تقويم Outlook متاح؟"""
    return get_outlook_calendar_sync().is_available()


def sync_with_outlook(
    direction: str = "both",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Dict[str, Tuple[int, int, int]]:
    """
    مزامنة مع Outlook

    Args:
        direction: "from_outlook", "to_outlook", أو "both"
        start_date: تاريخ البداية
        end_date: تاريخ النهاية

    Returns:
        نتائج المزامنة لكل اتجاه
    """
    sync = get_outlook_calendar_sync()
    results = {}

    if direction in ["from_outlook", "both"]:
        results["from_outlook"] = sync.sync_from_outlook(start_date, end_date)

    if direction in ["to_outlook", "both"]:
        results["to_outlook"] = sync.sync_to_outlook()

    return results
