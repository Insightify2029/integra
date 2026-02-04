"""
Coordinator Agent - المنسق الرئيسي
==================================

العقل المدبر لمنظومة وكلاء AI. يستقبل الأحداث ويوجهها للوكلاء المناسبين.

الاستخدام:
    from core.ai.orchestration import get_coordinator

    coordinator = get_coordinator()
    coordinator.start()

    # معالجة حدث
    result = coordinator.handle_event(Event(EventType.NEW_EMAIL, data={...}))

    # أو طلب مباشر
    result = coordinator.process_request("analyze_email", {"email": email_data})
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime
from enum import Enum, auto
import threading
import time
import uuid
from queue import Queue, Empty

from core.logging import app_logger
from .event_bus import (
    EventBus, Event, EventType, EventPriority,
    get_event_bus, subscribe_to_event
)
from .agent_registry import (
    AgentRegistry, AgentCapability, AgentStatus,
    get_agent_registry, BaseAgent
)


class RequestType(Enum):
    """أنواع الطلبات"""

    # طلبات الإيميل
    ANALYZE_EMAIL = "analyze_email"
    CLASSIFY_EMAIL = "classify_email"
    SUGGEST_EMAIL_REPLY = "suggest_email_reply"
    EXTRACT_EMAIL_TASKS = "extract_email_tasks"

    # طلبات المهام
    CREATE_TASK = "create_task"
    PRIORITIZE_TASK = "prioritize_task"
    SCHEDULE_TASK = "schedule_task"
    ANALYZE_TASK = "analyze_task"

    # طلبات التقويم
    SCHEDULE_EVENT = "schedule_event"
    FIND_FREE_TIME = "find_free_time"
    CHECK_CONFLICTS = "check_conflicts"

    # طلبات النماذج
    DETECT_FORM_TYPE = "detect_form_type"
    FILL_FORM = "fill_form"
    VALIDATE_FORM = "validate_form"
    EXTRACT_DATA = "extract_data"

    # طلبات الإجراءات
    EXECUTE_ACTION = "execute_action"
    SAVE_RECORD = "save_record"
    SEND_NOTIFICATION = "send_notification"

    # طلبات التحليل
    ANALYZE_DATA = "analyze_data"
    GENERATE_REPORT = "generate_report"
    DETECT_ANOMALIES = "detect_anomalies"

    # طلبات عامة
    NATURAL_QUERY = "natural_query"
    WORKFLOW_EXECUTE = "workflow_execute"


@dataclass
class Request:
    """طلب للمنسق"""
    type: RequestType
    data: Dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    source: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Response:
    """استجابة من المنسق"""
    request_id: str
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    agent_id: Optional[str] = None
    processing_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


# خريطة نوع الطلب → القدرة المطلوبة
REQUEST_CAPABILITY_MAP: Dict[RequestType, List[AgentCapability]] = {
    # إيميل
    RequestType.ANALYZE_EMAIL: [AgentCapability.EMAIL_ANALYSIS],
    RequestType.CLASSIFY_EMAIL: [AgentCapability.EMAIL_CLASSIFICATION],
    RequestType.SUGGEST_EMAIL_REPLY: [AgentCapability.EMAIL_REPLY_SUGGESTION],
    RequestType.EXTRACT_EMAIL_TASKS: [AgentCapability.EMAIL_TASK_EXTRACTION],

    # مهام
    RequestType.CREATE_TASK: [AgentCapability.TASK_CREATION],
    RequestType.PRIORITIZE_TASK: [AgentCapability.TASK_PRIORITIZATION],
    RequestType.SCHEDULE_TASK: [AgentCapability.TASK_SCHEDULING],
    RequestType.ANALYZE_TASK: [AgentCapability.TASK_ANALYSIS],

    # تقويم
    RequestType.SCHEDULE_EVENT: [AgentCapability.CALENDAR_SCHEDULING],
    RequestType.FIND_FREE_TIME: [AgentCapability.CALENDAR_OPTIMIZATION],
    RequestType.CHECK_CONFLICTS: [AgentCapability.CALENDAR_CONFLICT_DETECTION],

    # نماذج
    RequestType.DETECT_FORM_TYPE: [AgentCapability.FORM_DETECTION],
    RequestType.FILL_FORM: [AgentCapability.FORM_FILLING],
    RequestType.VALIDATE_FORM: [AgentCapability.FORM_VALIDATION],
    RequestType.EXTRACT_DATA: [AgentCapability.DATA_EXTRACTION],

    # إجراءات
    RequestType.EXECUTE_ACTION: [AgentCapability.DATABASE_WRITE],
    RequestType.SAVE_RECORD: [AgentCapability.DATABASE_WRITE],
    RequestType.SEND_NOTIFICATION: [AgentCapability.NOTIFICATION_SEND],

    # تحليل
    RequestType.ANALYZE_DATA: [AgentCapability.DATA_ANALYSIS],
    RequestType.GENERATE_REPORT: [AgentCapability.REPORT_GENERATION],
    RequestType.DETECT_ANOMALIES: [AgentCapability.ANOMALY_DETECTION],

    # عام
    RequestType.NATURAL_QUERY: [AgentCapability.NATURAL_LANGUAGE_QUERY],
    RequestType.WORKFLOW_EXECUTE: [AgentCapability.WORKFLOW_EXECUTION],
}

# خريطة نوع الحدث → نوع الطلب
EVENT_REQUEST_MAP: Dict[EventType, RequestType] = {
    EventType.NEW_EMAIL: RequestType.ANALYZE_EMAIL,
    EventType.EMAIL_ANALYZED: RequestType.EXTRACT_EMAIL_TASKS,
    EventType.TASK_CREATED: RequestType.PRIORITIZE_TASK,
    EventType.TASK_OVERDUE: RequestType.SEND_NOTIFICATION,
    EventType.EVENT_REMINDER: RequestType.SEND_NOTIFICATION,
    EventType.EMPLOYEE_CONTRACT_EXPIRING: RequestType.SEND_NOTIFICATION,
}


class CoordinatorAgent:
    """
    المنسق الرئيسي

    يدير التواصل بين الوكلاء ويوجه الطلبات للوكيل المناسب.
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

        self._event_bus: EventBus = get_event_bus()
        self._registry: AgentRegistry = get_agent_registry()
        self._request_queue: Queue = Queue()
        self._response_cache: Dict[str, Response] = {}
        self._cache_ttl_seconds = 300  # 5 دقائق
        self._processing = False
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.RLock()

        # إحصائيات
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_events": 0,
            "avg_response_time_ms": 0.0
        }

        # Hooks للتخصيص
        self._pre_process_hooks: List[Callable[[Request], Request]] = []
        self._post_process_hooks: List[Callable[[Request, Response], Response]] = []

        self._initialized = True
        app_logger.info("CoordinatorAgent initialized")

    def start(self):
        """بدء المنسق"""
        if self._processing:
            return

        self._processing = True
        self._stop_event.clear()

        # الاشتراك في الأحداث
        self._subscribe_to_events()

        # بدء معالجة الطابور
        self._worker_thread = threading.Thread(
            target=self._process_queue,
            daemon=True,
            name="CoordinatorWorker"
        )
        self._worker_thread.start()

        # تفعيل الوكلاء
        self._registry.activate_all()

        app_logger.info("CoordinatorAgent started")

    def stop(self):
        """إيقاف المنسق"""
        if not self._processing:
            return

        self._stop_event.set()
        self._processing = False

        if self._worker_thread:
            self._worker_thread.join(timeout=5)

        self._registry.deactivate_all()

        app_logger.info("CoordinatorAgent stopped")

    def _subscribe_to_events(self):
        """الاشتراك في الأحداث المهمة"""
        events_to_subscribe = [
            EventType.NEW_EMAIL,
            EventType.EMAIL_ANALYZED,
            EventType.TASK_CREATED,
            EventType.TASK_OVERDUE,
            EventType.EVENT_REMINDER,
            EventType.EMPLOYEE_CONTRACT_EXPIRING,
            EventType.AI_REQUEST,
        ]

        for event_type in events_to_subscribe:
            subscribe_to_event(
                event_type,
                self._handle_event_callback,
                f"coordinator_{event_type.name}"
            )

    def _handle_event_callback(self, event: Event) -> Optional[Any]:
        """Callback لمعالجة الأحداث"""
        self._stats["total_events"] += 1

        # تحويل الحدث لطلب
        request_type = EVENT_REQUEST_MAP.get(event.type)

        if request_type:
            request = Request(
                type=request_type,
                data=event.data,
                priority=event.priority,
                source=event.source or f"event_{event.type.name}"
            )
            return self.process_request_sync(request)

        return None

    def handle_event(self, event: Event) -> Optional[Response]:
        """
        معالجة حدث

        Args:
            event: الحدث

        Returns:
            استجابة أو None
        """
        return self._handle_event_callback(event)

    def process_request(
        self,
        request_type: RequestType,
        data: Optional[Dict[str, Any]] = None,
        priority: EventPriority = EventPriority.NORMAL,
        source: Optional[str] = None,
        async_mode: bool = False
    ) -> Optional[Response]:
        """
        معالجة طلب

        Args:
            request_type: نوع الطلب
            data: بيانات الطلب
            priority: الأولوية
            source: المصدر
            async_mode: غير متزامن

        Returns:
            استجابة (للمتزامن فقط)
        """
        request = Request(
            type=request_type,
            data=data or {},
            priority=priority,
            source=source
        )

        if async_mode:
            self._request_queue.put(request)
            return None
        else:
            return self.process_request_sync(request)

    def process_request_sync(self, request: Request) -> Response:
        """
        معالجة طلب بشكل متزامن

        Args:
            request: الطلب

        Returns:
            الاستجابة
        """
        start_time = time.time()
        self._stats["total_requests"] += 1

        try:
            # تطبيق hooks قبل المعالجة
            for hook in self._pre_process_hooks:
                request = hook(request)

            # البحث عن الوكيل المناسب
            agent, agent_id = self._find_suitable_agent(request)

            if not agent:
                response = Response(
                    request_id=request.id,
                    success=False,
                    error=f"لا يوجد وكيل قادر على معالجة {request.type.value}"
                )
                self._stats["failed_requests"] += 1
                return response

            # تحديث حالة الوكيل
            self._registry.update_agent_status(agent_id, AgentStatus.BUSY)

            # المعالجة
            result = self._execute_agent(agent, request)

            # إعداد الاستجابة
            processing_time = (time.time() - start_time) * 1000

            response = Response(
                request_id=request.id,
                success=True,
                data=result,
                agent_id=agent_id,
                processing_time_ms=processing_time
            )

            # تحديث الإحصائيات
            self._stats["successful_requests"] += 1
            self._registry.record_usage(agent_id, processing_time, success=True)
            self._update_avg_response_time(processing_time)

            # تحديث حالة الوكيل
            self._registry.update_agent_status(agent_id, AgentStatus.ACTIVE)

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000

            response = Response(
                request_id=request.id,
                success=False,
                error=str(e),
                processing_time_ms=processing_time
            )

            self._stats["failed_requests"] += 1
            app_logger.error(f"Error processing request {request.type.value}: {e}")

        # تطبيق hooks بعد المعالجة
        for hook in self._post_process_hooks:
            response = hook(request, response)

        return response

    def _find_suitable_agent(
        self,
        request: Request
    ) -> Tuple[Optional[Any], Optional[str]]:
        """
        البحث عن الوكيل المناسب للطلب

        Returns:
            (agent, agent_id) أو (None, None)
        """
        # جلب القدرات المطلوبة
        required_capabilities = REQUEST_CAPABILITY_MAP.get(request.type, [])

        if not required_capabilities:
            app_logger.warning(f"No capability mapping for {request.type.value}")
            return None, None

        # البحث عن وكيل بالقدرة الأولى
        for capability in required_capabilities:
            agent = self._registry.get_agent_by_capability(
                capability,
                status=AgentStatus.ACTIVE
            )

            if agent:
                info = self._registry.get_agent_info(agent.agent_id if hasattr(agent, 'agent_id') else str(id(agent)))
                agent_id = info.id if info else str(id(agent))
                return agent, agent_id

        return None, None

    def _execute_agent(
        self,
        agent: Any,
        request: Request
    ) -> Dict[str, Any]:
        """
        تنفيذ الوكيل

        Args:
            agent: كائن الوكيل
            request: الطلب

        Returns:
            نتيجة المعالجة
        """
        # إذا كان BaseAgent
        if isinstance(agent, BaseAgent):
            return agent.handle(request.type.value, request.data)

        # إذا كان له دالة handle
        if hasattr(agent, 'handle'):
            return agent.handle(request.type.value, request.data)

        # إذا كان له دالة باسم نوع الطلب
        method_name = request.type.value
        if hasattr(agent, method_name):
            method = getattr(agent, method_name)
            return method(request.data)

        # إذا كان له دالة process
        if hasattr(agent, 'process'):
            return agent.process(request.type.value, request.data)

        raise ValueError(f"Agent does not have a suitable handler method")

    def _process_queue(self):
        """معالجة طابور الطلبات"""
        while not self._stop_event.is_set():
            try:
                request = self._request_queue.get(timeout=0.5)
                self.process_request_sync(request)
                self._request_queue.task_done()
            except Empty:
                continue
            except Exception as e:
                app_logger.error(f"Error processing queued request: {e}")

    def _update_avg_response_time(self, new_time: float):
        """تحديث متوسط وقت الاستجابة"""
        total = self._stats["successful_requests"]
        if total == 1:
            self._stats["avg_response_time_ms"] = new_time
        else:
            current_avg = self._stats["avg_response_time_ms"]
            self._stats["avg_response_time_ms"] = (
                (current_avg * (total - 1) + new_time) / total
            )

    def add_pre_process_hook(self, hook: Callable[[Request], Request]):
        """إضافة hook قبل المعالجة"""
        self._pre_process_hooks.append(hook)

    def add_post_process_hook(
        self,
        hook: Callable[[Request, Response], Response]
    ):
        """إضافة hook بعد المعالجة"""
        self._post_process_hooks.append(hook)

    def get_stats(self) -> Dict[str, Any]:
        """جلب الإحصائيات"""
        return dict(self._stats)

    def get_registered_agents(self) -> List[str]:
        """جلب قائمة الوكلاء المسجلين"""
        return list(self._registry.get_all_agents().keys())

    def get_capabilities_summary(self) -> Dict[str, List[str]]:
        """ملخص القدرات المتاحة"""
        return self._registry.get_capabilities_summary()


# Singleton instance
_coordinator: Optional[CoordinatorAgent] = None


def get_coordinator() -> CoordinatorAgent:
    """جلب CoordinatorAgent singleton"""
    global _coordinator
    if _coordinator is None:
        _coordinator = CoordinatorAgent()
    return _coordinator


def process(
    request_type: RequestType,
    data: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Optional[Response]:
    """معالجة طلب (دالة مختصرة)"""
    return get_coordinator().process_request(request_type, data, **kwargs)


def start_coordinator():
    """بدء المنسق"""
    get_coordinator().start()


def stop_coordinator():
    """إيقاف المنسق"""
    get_coordinator().stop()


# تصدير
__all__ = [
    "RequestType",
    "Request",
    "Response",
    "CoordinatorAgent",
    "get_coordinator",
    "process",
    "start_coordinator",
    "stop_coordinator"
]
