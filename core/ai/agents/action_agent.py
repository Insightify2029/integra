"""
INTEGRA - Action AI Agent
وكيل الإجراءات الذكي
المحور K

ينفذ الإجراءات في قاعدة البيانات والنظام.

التاريخ: 4 فبراير 2026
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading

from core.logging import app_logger

# Try importing orchestration
try:
    from core.ai.orchestration import (
        BaseAgent, AgentCapability, AgentStatus,
        get_agent_registry, register_agent,
        publish_event, EventType
    )
    ORCHESTRATION_AVAILABLE = True
except ImportError:
    ORCHESTRATION_AVAILABLE = False
    BaseAgent = object
    app_logger.debug("Orchestration not available for action agent")


class ActionType(Enum):
    """أنواع الإجراءات"""
    # قاعدة البيانات
    DB_INSERT = "db_insert"
    DB_UPDATE = "db_update"
    DB_DELETE = "db_delete"
    DB_QUERY = "db_query"

    # الإشعارات
    NOTIFY_USER = "notify_user"
    NOTIFY_SYSTEM = "notify_system"
    SEND_EMAIL = "send_email"

    # الملفات
    FILE_CREATE = "file_create"
    FILE_READ = "file_read"
    FILE_DELETE = "file_delete"
    PRINT_DOCUMENT = "print_document"
    EXPORT_DATA = "export_data"

    # واجهة المستخدم
    OPEN_FORM = "open_form"
    OPEN_SCREEN = "open_screen"
    SHOW_DIALOG = "show_dialog"
    REFRESH_VIEW = "refresh_view"

    # سير العمل
    WORKFLOW_NEXT = "workflow_next"
    WORKFLOW_APPROVE = "workflow_approve"
    WORKFLOW_REJECT = "workflow_reject"


class ActionLevel(Enum):
    """مستوى خطورة الإجراء"""
    READ_ONLY = 0       # قراءة فقط - فوري
    LOW_RISK = 1        # منخفض الخطورة - تلقائي + إشعار
    MEDIUM_RISK = 2     # متوسط - بطلب المستخدم
    HIGH_RISK = 3       # عالي الخطورة - يحتاج موافقة


class ActionStatus(Enum):
    """حالة الإجراء"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Action:
    """إجراء للتنفيذ"""
    id: str
    type: ActionType
    level: ActionLevel
    description: str
    description_ar: str
    params: Dict[str, Any] = field(default_factory=dict)
    status: ActionStatus = ActionStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    executed_at: Optional[datetime] = None
    approved_by: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """تحويل لـ dictionary"""
        return {
            "id": self.id,
            "type": self.type.value,
            "level": self.level.value,
            "description": self.description,
            "description_ar": self.description_ar,
            "params": self.params,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "executed_at": self.executed_at.isoformat() if self.executed_at else None
        }


@dataclass
class ActionResult:
    """نتيجة تنفيذ إجراء"""
    success: bool
    action_id: str
    action_type: ActionType
    data: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0


# نوع دالة المعالج
ActionHandler = Callable[[Dict[str, Any]], Any]


class ActionRegistry:
    """سجل معالجات الإجراءات"""

    def __init__(self):
        self._handlers: Dict[ActionType, ActionHandler] = {}
        self._level_overrides: Dict[ActionType, ActionLevel] = {}
        self._lock = threading.RLock()

    def register(
        self,
        action_type: ActionType,
        handler: ActionHandler,
        level: Optional[ActionLevel] = None
    ):
        """تسجيل معالج لنوع إجراء"""
        with self._lock:
            self._handlers[action_type] = handler
            if level:
                self._level_overrides[action_type] = level

    def unregister(self, action_type: ActionType):
        """إلغاء تسجيل معالج"""
        with self._lock:
            self._handlers.pop(action_type, None)
            self._level_overrides.pop(action_type, None)

    def get_handler(self, action_type: ActionType) -> Optional[ActionHandler]:
        """جلب معالج"""
        return self._handlers.get(action_type)

    def get_level(self, action_type: ActionType) -> ActionLevel:
        """جلب مستوى الإجراء"""
        if action_type in self._level_overrides:
            return self._level_overrides[action_type]

        # مستويات افتراضية
        default_levels = {
            ActionType.DB_QUERY: ActionLevel.READ_ONLY,
            ActionType.FILE_READ: ActionLevel.READ_ONLY,
            ActionType.REFRESH_VIEW: ActionLevel.READ_ONLY,

            ActionType.NOTIFY_USER: ActionLevel.LOW_RISK,
            ActionType.NOTIFY_SYSTEM: ActionLevel.LOW_RISK,
            ActionType.OPEN_FORM: ActionLevel.LOW_RISK,
            ActionType.OPEN_SCREEN: ActionLevel.LOW_RISK,
            ActionType.SHOW_DIALOG: ActionLevel.LOW_RISK,

            ActionType.DB_INSERT: ActionLevel.MEDIUM_RISK,
            ActionType.DB_UPDATE: ActionLevel.MEDIUM_RISK,
            ActionType.FILE_CREATE: ActionLevel.MEDIUM_RISK,
            ActionType.EXPORT_DATA: ActionLevel.MEDIUM_RISK,
            ActionType.SEND_EMAIL: ActionLevel.MEDIUM_RISK,
            ActionType.PRINT_DOCUMENT: ActionLevel.MEDIUM_RISK,

            ActionType.DB_DELETE: ActionLevel.HIGH_RISK,
            ActionType.FILE_DELETE: ActionLevel.HIGH_RISK,
        }

        return default_levels.get(action_type, ActionLevel.MEDIUM_RISK)


class ActionAgent(BaseAgent if ORCHESTRATION_AVAILABLE else object):
    """
    وكيل الإجراءات الذكي

    قدرات:
    - تنفيذ الإجراءات في قاعدة البيانات
    - إدارة مستويات الخطورة
    - التحقق من الموافقات
    - تتبع سجل الإجراءات
    """

    _instance = None

    # قدرات الوكيل
    AGENT_CAPABILITIES = [
        AgentCapability.DATABASE_WRITE,
        AgentCapability.DATABASE_READ,
        AgentCapability.FILE_OPERATION,
        AgentCapability.NOTIFICATION_SEND,
        AgentCapability.EMAIL_SEND,
        AgentCapability.PRINT_DOCUMENT
    ] if ORCHESTRATION_AVAILABLE else []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return

        if ORCHESTRATION_AVAILABLE:
            super().__init__(
                agent_id="action_agent",
                name="Action Agent",
                name_ar="وكيل الإجراءات"
            )

        self._registry = ActionRegistry()
        self._pending_actions: Dict[str, Action] = {}
        self._action_history: List[Action] = []
        self._max_history = 500
        self._lock = threading.RLock()

        # تسجيل المعالجات الافتراضية
        self._register_default_handlers()

        self._initialized = True
        app_logger.info("ActionAgent initialized")

    def _register_default_handlers(self):
        """تسجيل المعالجات الافتراضية"""

        # معالج الإشعارات
        def notify_handler(params: Dict[str, Any]) -> Dict[str, Any]:
            title = params.get("title", "إشعار")
            message = params.get("message", "")
            notification_type = params.get("type", "info")

            # نشر حدث إشعار
            if ORCHESTRATION_AVAILABLE:
                publish_event(
                    EventType.NOTIFICATION_CREATED,
                    data={
                        "title": title,
                        "message": message,
                        "type": notification_type
                    }
                )

            return {"notified": True, "title": title}

        self._registry.register(ActionType.NOTIFY_USER, notify_handler)
        self._registry.register(ActionType.NOTIFY_SYSTEM, notify_handler)

        # معالج فتح الشاشة
        def open_screen_handler(params: Dict[str, Any]) -> Dict[str, Any]:
            screen_name = params.get("screen")
            screen_params = params.get("params", {})

            # هذا placeholder - سيتم ربطه بالـ UI
            return {
                "action": "open_screen",
                "screen": screen_name,
                "params": screen_params
            }

        self._registry.register(ActionType.OPEN_SCREEN, open_screen_handler)
        self._registry.register(ActionType.OPEN_FORM, open_screen_handler)

    # ═══════════════════════════════════════════════════════════════
    # Orchestration Integration
    # ═══════════════════════════════════════════════════════════════

    @property
    def capabilities(self) -> List:
        """قدرات الوكيل"""
        return self.AGENT_CAPABILITIES

    def can_handle(self, task_type: str, data: Dict[str, Any]) -> bool:
        """هل يمكن للوكيل معالجة هذه المهمة؟"""
        supported_types = [
            "execute_action", "save_record", "send_notification",
            "database_write", "database_read", "file_operation",
            "notification_send", "email_send", "print_document"
        ]
        return task_type.lower() in supported_types

    def handle(self, task_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """معالجة المهمة"""
        task_type_lower = task_type.lower()

        if task_type_lower == "execute_action":
            action_type_str = data.get("action_type", "")
            action_type = ActionType(action_type_str) if action_type_str else None
            params = data.get("params", {})

            if action_type:
                result = self.execute(action_type, params)
                return {
                    "success": result.success,
                    "action_id": result.action_id,
                    "data": result.data,
                    "error": result.error
                }

        elif task_type_lower in ["send_notification", "notification_send"]:
            result = self.execute(ActionType.NOTIFY_USER, data)
            return {
                "success": result.success,
                "action_id": result.action_id
            }

        elif task_type_lower == "save_record":
            table = data.get("table")
            record = data.get("record", {})
            result = self.execute(
                ActionType.DB_INSERT,
                {"table": table, "record": record}
            )
            return {
                "success": result.success,
                "action_id": result.action_id,
                "data": result.data
            }

        return {"success": False, "error": f"Unsupported task type: {task_type}"}

    # ═══════════════════════════════════════════════════════════════
    # Action Execution
    # ═══════════════════════════════════════════════════════════════

    def create_action(
        self,
        action_type: ActionType,
        params: Dict[str, Any],
        description: Optional[str] = None,
        description_ar: Optional[str] = None
    ) -> Action:
        """
        إنشاء إجراء جديد

        Args:
            action_type: نوع الإجراء
            params: معاملات الإجراء
            description: الوصف بالإنجليزي
            description_ar: الوصف بالعربي

        Returns:
            كائن الإجراء
        """
        import uuid

        action_id = str(uuid.uuid4())[:8]
        level = self._registry.get_level(action_type)

        action = Action(
            id=action_id,
            type=action_type,
            level=level,
            description=description or f"Execute {action_type.value}",
            description_ar=description_ar or f"تنفيذ {action_type.value}",
            params=params
        )

        with self._lock:
            self._pending_actions[action_id] = action

        return action

    def execute(
        self,
        action_type: ActionType,
        params: Dict[str, Any],
        force: bool = False
    ) -> ActionResult:
        """
        تنفيذ إجراء

        Args:
            action_type: نوع الإجراء
            params: معاملات الإجراء
            force: تجاوز التحقق من المستوى

        Returns:
            نتيجة التنفيذ
        """
        import time
        start_time = time.time()

        action = self.create_action(action_type, params)
        level = self._registry.get_level(action_type)

        # التحقق من المستوى
        if not force and level == ActionLevel.HIGH_RISK:
            action.status = ActionStatus.PENDING
            return ActionResult(
                success=False,
                action_id=action.id,
                action_type=action_type,
                error="هذا الإجراء يحتاج موافقة. استخدم approve_action() أولاً"
            )

        # الحصول على المعالج
        handler = self._registry.get_handler(action_type)

        if not handler:
            action.status = ActionStatus.FAILED
            action.error = f"No handler for {action_type.value}"
            self._add_to_history(action)

            return ActionResult(
                success=False,
                action_id=action.id,
                action_type=action_type,
                error=f"لا يوجد معالج للإجراء: {action_type.value}"
            )

        # التنفيذ
        action.status = ActionStatus.EXECUTING

        try:
            result = handler(params)
            action.status = ActionStatus.COMPLETED
            action.result = result
            action.executed_at = datetime.now()

            execution_time = (time.time() - start_time) * 1000
            self._add_to_history(action)

            # إزالة من قائمة الانتظار
            with self._lock:
                self._pending_actions.pop(action.id, None)

            return ActionResult(
                success=True,
                action_id=action.id,
                action_type=action_type,
                data=result,
                execution_time_ms=execution_time
            )

        except Exception as e:
            action.status = ActionStatus.FAILED
            action.error = str(e)
            self._add_to_history(action)

            app_logger.error(f"Action {action.id} failed: {e}")

            return ActionResult(
                success=False,
                action_id=action.id,
                action_type=action_type,
                error=str(e)
            )

    def approve_action(self, action_id: str, approved_by: str) -> ActionResult:
        """
        الموافقة على إجراء وتنفيذه

        Args:
            action_id: معرف الإجراء
            approved_by: اسم الموافق

        Returns:
            نتيجة التنفيذ
        """
        with self._lock:
            action = self._pending_actions.get(action_id)

        if not action:
            return ActionResult(
                success=False,
                action_id=action_id,
                action_type=ActionType.DB_QUERY,  # placeholder
                error="الإجراء غير موجود"
            )

        action.status = ActionStatus.APPROVED
        action.approved_by = approved_by

        return self.execute(action.type, action.params, force=True)

    def reject_action(self, action_id: str, reason: Optional[str] = None) -> bool:
        """
        رفض إجراء

        Args:
            action_id: معرف الإجراء
            reason: سبب الرفض

        Returns:
            True إذا تم الرفض
        """
        with self._lock:
            action = self._pending_actions.pop(action_id, None)

        if action:
            action.status = ActionStatus.REJECTED
            action.error = reason or "تم الرفض"
            self._add_to_history(action)
            return True

        return False

    def cancel_action(self, action_id: str) -> bool:
        """إلغاء إجراء قبل تنفيذه"""
        with self._lock:
            action = self._pending_actions.pop(action_id, None)

        if action:
            action.status = ActionStatus.CANCELLED
            self._add_to_history(action)
            return True

        return False

    # ═══════════════════════════════════════════════════════════════
    # Registry Management
    # ═══════════════════════════════════════════════════════════════

    def register_handler(
        self,
        action_type: ActionType,
        handler: ActionHandler,
        level: Optional[ActionLevel] = None
    ):
        """تسجيل معالج جديد"""
        self._registry.register(action_type, handler, level)

    def unregister_handler(self, action_type: ActionType):
        """إلغاء تسجيل معالج"""
        self._registry.unregister(action_type)

    # ═══════════════════════════════════════════════════════════════
    # History & Status
    # ═══════════════════════════════════════════════════════════════

    def _add_to_history(self, action: Action):
        """إضافة للتاريخ"""
        self._action_history.append(action)
        if len(self._action_history) > self._max_history:
            self._action_history = self._action_history[-self._max_history:]

    def get_pending_actions(self) -> List[Action]:
        """جلب الإجراءات المعلقة"""
        with self._lock:
            return list(self._pending_actions.values())

    def get_action_history(self, limit: int = 100) -> List[Action]:
        """جلب تاريخ الإجراءات"""
        return list(reversed(self._action_history[-limit:]))

    def get_action(self, action_id: str) -> Optional[Action]:
        """جلب إجراء بالمعرف"""
        # البحث في المعلقة
        with self._lock:
            if action_id in self._pending_actions:
                return self._pending_actions[action_id]

        # البحث في التاريخ
        for action in self._action_history:
            if action.id == action_id:
                return action

        return None


# ═══════════════════════════════════════════════════════════════
# Singleton & Quick Access Functions
# ═══════════════════════════════════════════════════════════════

_agent: Optional[ActionAgent] = None


def get_action_agent() -> ActionAgent:
    """الحصول على instance الوكيل"""
    global _agent
    if _agent is None:
        _agent = ActionAgent()
    return _agent


def execute_action(
    action_type: ActionType,
    params: Dict[str, Any],
    force: bool = False
) -> ActionResult:
    """تنفيذ إجراء"""
    return get_action_agent().execute(action_type, params, force)


def approve_action(action_id: str, approved_by: str) -> ActionResult:
    """الموافقة على إجراء"""
    return get_action_agent().approve_action(action_id, approved_by)


def reject_action(action_id: str, reason: Optional[str] = None) -> bool:
    """رفض إجراء"""
    return get_action_agent().reject_action(action_id, reason)


def get_pending_actions() -> List[Action]:
    """جلب الإجراءات المعلقة"""
    return get_action_agent().get_pending_actions()


def register_action_handler(
    action_type: ActionType,
    handler: ActionHandler,
    level: Optional[ActionLevel] = None
):
    """تسجيل معالج إجراء"""
    get_action_agent().register_handler(action_type, handler, level)


def register_action_agent() -> bool:
    """تسجيل وكيل الإجراءات في منظومة التنسيق"""
    if not ORCHESTRATION_AVAILABLE:
        return False

    try:
        agent = get_action_agent()
        register_agent(
            agent_id="action_agent",
            agent=agent,
            capabilities=agent.AGENT_CAPABILITIES,
            name="Action Agent",
            name_ar="وكيل الإجراءات",
            description="وكيل ذكي لتنفيذ الإجراءات في النظام",
            priority=5  # أقل أولوية لأنه منفذ
        )
        app_logger.info("ActionAgent registered with orchestration")
        return True
    except Exception as e:
        app_logger.error(f"Failed to register ActionAgent: {e}")
        return False
