"""
Agent Registry - سجل الوكلاء
============================

نظام تسجيل وإدارة وكلاء AI المتاحين.

الاستخدام:
    from core.ai.orchestration import get_agent_registry, AgentCapability

    # تسجيل وكيل
    registry = get_agent_registry()
    registry.register_agent(
        agent_id="email_agent",
        agent=email_agent_instance,
        capabilities=[AgentCapability.EMAIL_ANALYSIS, AgentCapability.EMAIL_REPLY]
    )

    # جلب وكيل بقدرة معينة
    agent = registry.get_agent_by_capability(AgentCapability.EMAIL_ANALYSIS)
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Type
from datetime import datetime
import threading
from abc import ABC, abstractmethod
from core.logging import app_logger


class AgentCapability(Enum):
    """قدرات الوكلاء"""

    # قدرات الإيميل
    EMAIL_ANALYSIS = auto()
    EMAIL_CLASSIFICATION = auto()
    EMAIL_SUMMARIZATION = auto()
    EMAIL_REPLY_SUGGESTION = auto()
    EMAIL_TASK_EXTRACTION = auto()

    # قدرات المهام
    TASK_CREATION = auto()
    TASK_PRIORITIZATION = auto()
    TASK_SCHEDULING = auto()
    TASK_ANALYSIS = auto()

    # قدرات التقويم
    CALENDAR_SCHEDULING = auto()
    CALENDAR_CONFLICT_DETECTION = auto()
    CALENDAR_REMINDER = auto()
    CALENDAR_OPTIMIZATION = auto()

    # قدرات النماذج
    FORM_DETECTION = auto()
    FORM_FILLING = auto()
    FORM_VALIDATION = auto()
    DATA_EXTRACTION = auto()

    # قدرات الإجراءات
    DATABASE_WRITE = auto()
    DATABASE_READ = auto()
    FILE_OPERATION = auto()
    NOTIFICATION_SEND = auto()
    EMAIL_SEND = auto()
    PRINT_DOCUMENT = auto()

    # قدرات التعلم
    PATTERN_DETECTION = auto()
    USER_PREFERENCE_LEARNING = auto()
    SUGGESTION_IMPROVEMENT = auto()

    # قدرات التنبيه
    ALERT_DETECTION = auto()
    ANOMALY_DETECTION = auto()
    DEADLINE_MONITORING = auto()

    # قدرات البيانات
    DATA_ANALYSIS = auto()
    REPORT_GENERATION = auto()
    STATISTICS_CALCULATION = auto()

    # قدرات عامة
    NATURAL_LANGUAGE_QUERY = auto()
    CONTEXT_UNDERSTANDING = auto()
    WORKFLOW_EXECUTION = auto()


class AgentStatus(Enum):
    """حالة الوكيل"""
    INACTIVE = "inactive"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class AgentInfo:
    """معلومات الوكيل"""
    id: str
    name: str
    name_ar: str
    description: str
    capabilities: List[AgentCapability]
    status: AgentStatus = AgentStatus.INACTIVE
    priority: int = 0  # الأولوية (الأعلى يُختار أولاً)
    version: str = "1.0.0"
    registered_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    usage_count: int = 0
    error_count: int = 0
    avg_response_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """تحويل لـ dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "name_ar": self.name_ar,
            "description": self.description,
            "capabilities": [c.name for c in self.capabilities],
            "status": self.status.value,
            "priority": self.priority,
            "version": self.version,
            "registered_at": self.registered_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "usage_count": self.usage_count,
            "error_count": self.error_count,
            "avg_response_time_ms": self.avg_response_time_ms,
            "metadata": self.metadata
        }


class BaseAgent(ABC):
    """
    الفئة الأساسية لجميع الوكلاء

    يجب على كل وكيل أن يرث من هذه الفئة.
    """

    def __init__(self, agent_id: str, name: str, name_ar: str):
        self.agent_id = agent_id
        self.name = name
        self.name_ar = name_ar
        self._status = AgentStatus.INACTIVE

    @property
    @abstractmethod
    def capabilities(self) -> List[AgentCapability]:
        """قدرات الوكيل"""
        pass

    @property
    def status(self) -> AgentStatus:
        """حالة الوكيل"""
        return self._status

    @status.setter
    def status(self, value: AgentStatus):
        self._status = value

    @abstractmethod
    def can_handle(self, task_type: str, data: Dict[str, Any]) -> bool:
        """
        هل يمكن للوكيل معالجة هذه المهمة؟

        Args:
            task_type: نوع المهمة
            data: بيانات المهمة

        Returns:
            True إذا كان يمكنه المعالجة
        """
        pass

    @abstractmethod
    def handle(self, task_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        معالجة المهمة

        Args:
            task_type: نوع المهمة
            data: بيانات المهمة

        Returns:
            نتيجة المعالجة
        """
        pass

    def activate(self):
        """تفعيل الوكيل"""
        self._status = AgentStatus.ACTIVE

    def deactivate(self):
        """إيقاف الوكيل"""
        self._status = AgentStatus.INACTIVE

    def get_info(self) -> AgentInfo:
        """جلب معلومات الوكيل"""
        return AgentInfo(
            id=self.agent_id,
            name=self.name,
            name_ar=self.name_ar,
            description=self.__class__.__doc__ or "",
            capabilities=self.capabilities,
            status=self.status
        )


class AgentRegistry:
    """
    سجل الوكلاء

    يدير تسجيل وجلب واستخدام الوكلاء.
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

        self._agents: Dict[str, Any] = {}  # agent_id -> agent instance
        self._agent_info: Dict[str, AgentInfo] = {}  # agent_id -> info
        self._capability_index: Dict[AgentCapability, List[str]] = {}  # capability -> [agent_ids]
        self._lock = threading.RLock()

        self._initialized = True
        app_logger.info("AgentRegistry initialized")

    def register_agent(
        self,
        agent_id: str,
        agent: Any,
        capabilities: List[AgentCapability],
        name: Optional[str] = None,
        name_ar: Optional[str] = None,
        description: Optional[str] = None,
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        تسجيل وكيل جديد

        Args:
            agent_id: معرف الوكيل
            agent: كائن الوكيل
            capabilities: قدرات الوكيل
            name: الاسم بالإنجليزي
            name_ar: الاسم بالعربي
            description: الوصف
            priority: الأولوية
            metadata: بيانات إضافية

        Returns:
            True إذا تم التسجيل بنجاح
        """
        with self._lock:
            if agent_id in self._agents:
                app_logger.warning(f"Agent {agent_id} already registered, updating...")

            # استخراج المعلومات من الوكيل إذا كان BaseAgent
            if isinstance(agent, BaseAgent):
                name = name or agent.name
                name_ar = name_ar or agent.name_ar
                description = description or agent.__class__.__doc__
                capabilities = capabilities or agent.capabilities

            # إنشاء معلومات الوكيل
            info = AgentInfo(
                id=agent_id,
                name=name or agent_id,
                name_ar=name_ar or agent_id,
                description=description or "",
                capabilities=capabilities,
                priority=priority,
                metadata=metadata or {}
            )

            # تسجيل
            self._agents[agent_id] = agent
            self._agent_info[agent_id] = info

            # فهرسة القدرات
            for capability in capabilities:
                if capability not in self._capability_index:
                    self._capability_index[capability] = []
                if agent_id not in self._capability_index[capability]:
                    self._capability_index[capability].append(agent_id)

            # ترتيب حسب الأولوية
            for capability in capabilities:
                self._capability_index[capability].sort(
                    key=lambda aid: self._agent_info[aid].priority,
                    reverse=True
                )

            app_logger.info(
                f"Registered agent {agent_id} with capabilities: "
                f"{[c.name for c in capabilities]}"
            )
            return True

    def unregister_agent(self, agent_id: str) -> bool:
        """
        إلغاء تسجيل وكيل

        Args:
            agent_id: معرف الوكيل

        Returns:
            True إذا تم الإلغاء
        """
        with self._lock:
            if agent_id not in self._agents:
                return False

            # إزالة من فهرس القدرات
            for capability, agent_ids in self._capability_index.items():
                if agent_id in agent_ids:
                    agent_ids.remove(agent_id)

            # إزالة
            del self._agents[agent_id]
            del self._agent_info[agent_id]

            app_logger.info(f"Unregistered agent {agent_id}")
            return True

    def get_agent(self, agent_id: str) -> Optional[Any]:
        """
        جلب وكيل بالمعرف

        Args:
            agent_id: معرف الوكيل

        Returns:
            كائن الوكيل أو None
        """
        return self._agents.get(agent_id)

    def get_agent_info(self, agent_id: str) -> Optional[AgentInfo]:
        """جلب معلومات وكيل"""
        return self._agent_info.get(agent_id)

    def get_agent_by_capability(
        self,
        capability: AgentCapability,
        status: Optional[AgentStatus] = None
    ) -> Optional[Any]:
        """
        جلب أول وكيل بقدرة معينة

        Args:
            capability: القدرة المطلوبة
            status: فلترة بالحالة (اختياري)

        Returns:
            كائن الوكيل أو None
        """
        agent_ids = self._capability_index.get(capability, [])

        for agent_id in agent_ids:
            info = self._agent_info.get(agent_id)
            if info and (status is None or info.status == status):
                return self._agents.get(agent_id)

        return None

    def get_agents_by_capability(
        self,
        capability: AgentCapability,
        status: Optional[AgentStatus] = None
    ) -> List[Any]:
        """
        جلب جميع الوكلاء بقدرة معينة

        Args:
            capability: القدرة المطلوبة
            status: فلترة بالحالة (اختياري)

        Returns:
            قائمة الوكلاء
        """
        agent_ids = self._capability_index.get(capability, [])
        agents = []

        for agent_id in agent_ids:
            info = self._agent_info.get(agent_id)
            if info and (status is None or info.status == status):
                agent = self._agents.get(agent_id)
                if agent:
                    agents.append(agent)

        return agents

    def find_agents_for_task(
        self,
        required_capabilities: List[AgentCapability]
    ) -> List[str]:
        """
        إيجاد الوكلاء القادرين على مهمة تتطلب عدة قدرات

        Args:
            required_capabilities: القدرات المطلوبة

        Returns:
            قائمة معرفات الوكلاء
        """
        if not required_capabilities:
            return []

        # ابدأ بالوكلاء الذين لديهم القدرة الأولى
        candidate_ids = set(
            self._capability_index.get(required_capabilities[0], [])
        )

        # فلترة بباقي القدرات
        for capability in required_capabilities[1:]:
            capability_agents = set(
                self._capability_index.get(capability, [])
            )
            candidate_ids &= capability_agents

        return list(candidate_ids)

    def get_all_agents(self) -> Dict[str, Any]:
        """جلب جميع الوكلاء"""
        return dict(self._agents)

    def get_all_agent_info(self) -> Dict[str, AgentInfo]:
        """جلب معلومات جميع الوكلاء"""
        return dict(self._agent_info)

    def get_capabilities_summary(self) -> Dict[str, List[str]]:
        """ملخص القدرات والوكلاء"""
        return {
            cap.name: list(agent_ids)
            for cap, agent_ids in self._capability_index.items()
            if agent_ids
        }

    def update_agent_status(self, agent_id: str, status: AgentStatus) -> bool:
        """تحديث حالة وكيل"""
        if agent_id not in self._agent_info:
            return False

        self._agent_info[agent_id].status = status

        # تحديث حالة الوكيل نفسه إذا كان BaseAgent
        agent = self._agents.get(agent_id)
        if isinstance(agent, BaseAgent):
            agent.status = status

        app_logger.debug(f"Agent {agent_id} status updated to {status.value}")
        return True

    def record_usage(
        self,
        agent_id: str,
        response_time_ms: float,
        success: bool = True
    ):
        """
        تسجيل استخدام وكيل

        Args:
            agent_id: معرف الوكيل
            response_time_ms: وقت الاستجابة بالمللي ثانية
            success: هل نجح؟
        """
        if agent_id not in self._agent_info:
            return

        info = self._agent_info[agent_id]
        info.last_used = datetime.now()
        info.usage_count += 1

        if not success:
            info.error_count += 1

        # حساب متوسط وقت الاستجابة (moving average)
        if info.usage_count == 1:
            info.avg_response_time_ms = response_time_ms
        else:
            info.avg_response_time_ms = (
                (info.avg_response_time_ms * (info.usage_count - 1) + response_time_ms)
                / info.usage_count
            )

    def activate_all(self):
        """تفعيل جميع الوكلاء"""
        for agent_id in self._agents:
            self.update_agent_status(agent_id, AgentStatus.ACTIVE)

    def deactivate_all(self):
        """إيقاف جميع الوكلاء"""
        for agent_id in self._agents:
            self.update_agent_status(agent_id, AgentStatus.INACTIVE)

    def shutdown(self):
        """إغلاق السجل"""
        self.deactivate_all()
        app_logger.info("AgentRegistry shutdown complete")


# Singleton instance
_registry: Optional[AgentRegistry] = None


def get_agent_registry() -> AgentRegistry:
    """جلب AgentRegistry singleton"""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry


def register_agent(
    agent_id: str,
    agent: Any,
    capabilities: List[AgentCapability],
    **kwargs
) -> bool:
    """تسجيل وكيل (دالة مختصرة)"""
    return get_agent_registry().register_agent(
        agent_id, agent, capabilities, **kwargs
    )


def get_agent(agent_id: str) -> Optional[Any]:
    """جلب وكيل (دالة مختصرة)"""
    return get_agent_registry().get_agent(agent_id)


def get_agent_for(capability: AgentCapability) -> Optional[Any]:
    """جلب وكيل بقدرة (دالة مختصرة)"""
    return get_agent_registry().get_agent_by_capability(capability)


# تصدير
__all__ = [
    "AgentCapability",
    "AgentStatus",
    "AgentInfo",
    "BaseAgent",
    "AgentRegistry",
    "get_agent_registry",
    "register_agent",
    "get_agent",
    "get_agent_for"
]
