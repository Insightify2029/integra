"""
Event Bus - نظام الأحداث المركزي
================================

نظام publish/subscribe للتواصل بين الوكلاء والموديولات.

الاستخدام:
    from core.ai.orchestration import get_event_bus, Event, EventType

    # الاشتراك في حدث
    bus = get_event_bus()
    bus.subscribe(EventType.NEW_EMAIL, handle_new_email)

    # نشر حدث
    bus.publish(Event(EventType.NEW_EMAIL, data={"email": email_obj}))
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime
import threading
import queue
import uuid
from core.logging import app_logger


class EventType(Enum):
    """أنواع الأحداث المدعومة"""

    # أحداث الإيميل
    NEW_EMAIL = auto()
    EMAIL_READ = auto()
    EMAIL_REPLIED = auto()
    EMAIL_FORWARDED = auto()
    EMAIL_DELETED = auto()
    EMAIL_ANALYZED = auto()

    # أحداث المهام
    TASK_CREATED = auto()
    TASK_UPDATED = auto()
    TASK_COMPLETED = auto()
    TASK_DELETED = auto()
    TASK_OVERDUE = auto()
    TASK_ASSIGNED = auto()

    # أحداث التقويم
    EVENT_CREATED = auto()
    EVENT_UPDATED = auto()
    EVENT_DELETED = auto()
    EVENT_REMINDER = auto()
    EVENT_STARTED = auto()
    EVENT_ENDED = auto()

    # أحداث الإشعارات
    NOTIFICATION_CREATED = auto()
    NOTIFICATION_READ = auto()
    NOTIFICATION_DISMISSED = auto()
    NOTIFICATION_ACTION = auto()

    # أحداث الموظفين
    EMPLOYEE_CREATED = auto()
    EMPLOYEE_UPDATED = auto()
    EMPLOYEE_DELETED = auto()
    EMPLOYEE_CONTRACT_EXPIRING = auto()

    # أحداث النظام
    SYSTEM_STARTUP = auto()
    SYSTEM_SHUTDOWN = auto()
    USER_LOGIN = auto()
    USER_LOGOUT = auto()
    MODULE_OPENED = auto()
    MODULE_CLOSED = auto()

    # أحداث AI
    AI_REQUEST = auto()
    AI_RESPONSE = auto()
    AI_ERROR = auto()
    AI_SUGGESTION = auto()

    # أحداث سير العمل
    WORKFLOW_STARTED = auto()
    WORKFLOW_STEP_COMPLETED = auto()
    WORKFLOW_COMPLETED = auto()
    WORKFLOW_ERROR = auto()

    # أحداث النماذج
    FORM_OPENED = auto()
    FORM_FILLED = auto()
    FORM_SUBMITTED = auto()
    FORM_CANCELLED = auto()

    # أحداث عامة
    CUSTOM = auto()


class EventPriority(Enum):
    """أولوية الأحداث"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


@dataclass
class Event:
    """كائن الحدث"""

    type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    source: Optional[str] = None  # المصدر (مثل: email_agent, task_module)
    target: Optional[str] = None  # الهدف (مثل: coordinator, task_agent)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    processed: bool = False
    result: Optional[Any] = None
    error: Optional[str] = None

    def __lt__(self, other: "Event") -> bool:
        """Compare events for PriorityQueue ordering."""
        if not isinstance(other, Event):
            return NotImplemented
        return self.timestamp < other.timestamp

    def to_dict(self) -> Dict[str, Any]:
        """تحويل لـ dictionary"""
        return {
            "id": self.id,
            "type": self.type.name,
            "data": self.data,
            "priority": self.priority.name,
            "source": self.source,
            "target": self.target,
            "timestamp": self.timestamp.isoformat(),
            "processed": self.processed,
            "result": self.result,
            "error": self.error
        }


# نوع الـ callback
EventHandler = Callable[[Event], Optional[Any]]


class EventBus:
    """
    ناقل الأحداث المركزي

    يدير الاشتراكات والنشر للأحداث بين مكونات النظام.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._subscribers: Dict[EventType, List[Dict[str, Any]]] = {}
        self._event_queue: queue.PriorityQueue = queue.PriorityQueue()
        self._event_history: List[Event] = []
        self._max_history = 1000
        self._processing = False
        self._async_mode = False
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.RLock()

        self._initialized = True
        app_logger.info("EventBus initialized")

    def subscribe(
        self,
        event_type: EventType,
        handler: EventHandler,
        handler_id: Optional[str] = None,
        priority: int = 0
    ) -> str:
        """
        الاشتراك في نوع حدث معين

        Args:
            event_type: نوع الحدث
            handler: دالة المعالجة
            handler_id: معرف المعالج (اختياري)
            priority: أولوية المعالج (الأعلى يُنفذ أولاً)

        Returns:
            معرف الاشتراك
        """
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []

            sub_id = handler_id or str(uuid.uuid4())

            # تحقق من عدم وجود اشتراك مكرر
            for sub in self._subscribers[event_type]:
                if sub["id"] == sub_id:
                    app_logger.warning(f"Handler {sub_id} already subscribed to {event_type.name}")
                    return sub_id

            self._subscribers[event_type].append({
                "id": sub_id,
                "handler": handler,
                "priority": priority
            })

            # ترتيب حسب الأولوية (الأعلى أولاً)
            self._subscribers[event_type].sort(
                key=lambda x: x["priority"],
                reverse=True
            )

            app_logger.debug(f"Subscribed {sub_id} to {event_type.name}")
            return sub_id

    def unsubscribe(self, event_type: EventType, handler_id: str) -> bool:
        """
        إلغاء الاشتراك

        Args:
            event_type: نوع الحدث
            handler_id: معرف المعالج

        Returns:
            True إذا تم الإلغاء بنجاح
        """
        with self._lock:
            if event_type not in self._subscribers:
                return False

            original_count = len(self._subscribers[event_type])
            self._subscribers[event_type] = [
                sub for sub in self._subscribers[event_type]
                if sub["id"] != handler_id
            ]

            removed = len(self._subscribers[event_type]) < original_count
            if removed:
                app_logger.debug(f"Unsubscribed {handler_id} from {event_type.name}")

            return removed

    def unsubscribe_all(self, handler_id: str) -> int:
        """
        إلغاء جميع اشتراكات معالج معين

        Returns:
            عدد الاشتراكات الملغاة
        """
        count = 0
        with self._lock:
            for event_type in list(self._subscribers.keys()):
                if self.unsubscribe(event_type, handler_id):
                    count += 1
        return count

    def publish(self, event: Event) -> List[Any]:
        """
        نشر حدث (متزامن)

        Args:
            event: الحدث للنشر

        Returns:
            قائمة نتائج المعالجات
        """
        results = []

        with self._lock:
            handlers = self._subscribers.get(event.type, [])

        if not handlers:
            app_logger.debug(f"No handlers for event {event.type.name}")
            return results

        for sub in handlers:
            try:
                result = sub["handler"](event)
                results.append({
                    "handler_id": sub["id"],
                    "result": result,
                    "success": True
                })
            except Exception as e:
                app_logger.error(
                    f"Error in handler {sub['id']} for {event.type.name}: {e}",
                    exc_info=True
                )
                results.append({
                    "handler_id": sub["id"],
                    "error": str(e),
                    "success": False
                })

        # تسجيل في التاريخ
        event.processed = True
        self._add_to_history(event)

        app_logger.debug(
            f"Published {event.type.name} to {len(handlers)} handlers"
        )

        return results

    def publish_async(self, event: Event):
        """
        نشر حدث (غير متزامن)

        يضيف الحدث للطابور ليُعالج لاحقاً.
        """
        # الأولوية: urgent=0, high=1, normal=2, low=3
        priority_value = 3 - event.priority.value
        self._event_queue.put((priority_value, event.timestamp, event))
        app_logger.debug(f"Queued async event {event.type.name}")

    def start_async_processing(self):
        """بدء معالجة الأحداث غير المتزامنة"""
        if self._processing:
            return

        self._processing = True
        self._stop_event.clear()
        self._worker_thread = threading.Thread(
            target=self._process_queue,
            daemon=True,
            name="EventBusWorker"
        )
        self._worker_thread.start()
        app_logger.info("Started async event processing")

    def stop_async_processing(self):
        """إيقاف معالجة الأحداث غير المتزامنة"""
        if not self._processing:
            return

        self._stop_event.set()
        self._processing = False

        if self._worker_thread:
            self._worker_thread.join(timeout=5)

        app_logger.info("Stopped async event processing")

    def _process_queue(self):
        """معالجة طابور الأحداث"""
        while not self._stop_event.is_set():
            try:
                # انتظار حدث (مع timeout للتحقق من إيقاف)
                priority, timestamp, event = self._event_queue.get(timeout=0.5)
                self.publish(event)
                self._event_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                app_logger.error(f"Error processing queued event: {e}")

    def _add_to_history(self, event: Event):
        """إضافة حدث للتاريخ"""
        self._event_history.append(event)

        # تنظيف إذا تجاوز الحد
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]

    def get_history(
        self,
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        جلب تاريخ الأحداث

        Args:
            event_type: فلترة بنوع (اختياري)
            limit: الحد الأقصى

        Returns:
            قائمة الأحداث (الأحدث أولاً)
        """
        history = self._event_history.copy()

        if event_type:
            history = [e for e in history if e.type == event_type]

        return list(reversed(history[-limit:]))

    def get_subscriber_count(self, event_type: Optional[EventType] = None) -> int:
        """عدد المشتركين"""
        if event_type:
            return len(self._subscribers.get(event_type, []))
        return sum(len(subs) for subs in self._subscribers.values())

    def clear_history(self):
        """مسح التاريخ"""
        self._event_history.clear()
        app_logger.info("Event history cleared")

    def shutdown(self):
        """إيقاف EventBus"""
        self.stop_async_processing()
        self.clear_history()
        self._subscribers.clear()
        app_logger.info("EventBus shutdown complete")


# Singleton instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """جلب EventBus singleton"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def publish_event(
    event_type: EventType,
    data: Optional[Dict[str, Any]] = None,
    priority: EventPriority = EventPriority.NORMAL,
    source: Optional[str] = None,
    async_mode: bool = False
) -> Optional[List[Any]]:
    """
    نشر حدث (دالة مختصرة)

    Args:
        event_type: نوع الحدث
        data: بيانات الحدث
        priority: الأولوية
        source: المصدر
        async_mode: نشر غير متزامن

    Returns:
        نتائج المعالجات (للمتزامن فقط)
    """
    event = Event(
        type=event_type,
        data=data or {},
        priority=priority,
        source=source
    )

    bus = get_event_bus()

    if async_mode:
        bus.publish_async(event)
        return None
    else:
        return bus.publish(event)


def subscribe_to_event(
    event_type: EventType,
    handler: EventHandler,
    handler_id: Optional[str] = None
) -> str:
    """اشتراك في حدث (دالة مختصرة)"""
    return get_event_bus().subscribe(event_type, handler, handler_id)


# تصدير
__all__ = [
    "EventType",
    "EventPriority",
    "Event",
    "EventHandler",
    "EventBus",
    "get_event_bus",
    "publish_event",
    "subscribe_to_event"
]
