"""
AI Orchestration - منظومة وكلاء AI المتكاملة
============================================

نظام تنسيق مركزي لوكلاء AI يدير التواصل والتوجيه بينهم.

المكونات:
    - EventBus: نظام الأحداث المركزي (publish/subscribe)
    - AgentRegistry: سجل الوكلاء وقدراتهم
    - CoordinatorAgent: المنسق الرئيسي

الاستخدام:
    from core.ai.orchestration import (
        get_coordinator, start_coordinator, stop_coordinator,
        get_event_bus, publish_event, subscribe_to_event,
        get_agent_registry, register_agent
    )

    # بدء المنسق
    start_coordinator()

    # تسجيل وكيل
    register_agent("my_agent", agent, [AgentCapability.DATA_ANALYSIS])

    # نشر حدث
    publish_event(EventType.NEW_EMAIL, data={"email": email_obj})

    # معالجة طلب
    from core.ai.orchestration import process, RequestType
    response = process(RequestType.ANALYZE_EMAIL, data={"email": email_obj})
"""

# Event Bus
from .event_bus import (
    EventType,
    EventPriority,
    Event,
    EventHandler,
    EventBus,
    get_event_bus,
    publish_event,
    subscribe_to_event
)

# Agent Registry
from .agent_registry import (
    AgentCapability,
    AgentStatus,
    AgentInfo,
    BaseAgent,
    AgentRegistry,
    get_agent_registry,
    register_agent,
    get_agent,
    get_agent_for
)

# Coordinator
from .coordinator_agent import (
    RequestType,
    Request,
    Response,
    CoordinatorAgent,
    get_coordinator,
    process,
    start_coordinator,
    stop_coordinator
)


# تصدير
__all__ = [
    # Event Bus
    "EventType",
    "EventPriority",
    "Event",
    "EventHandler",
    "EventBus",
    "get_event_bus",
    "publish_event",
    "subscribe_to_event",

    # Agent Registry
    "AgentCapability",
    "AgentStatus",
    "AgentInfo",
    "BaseAgent",
    "AgentRegistry",
    "get_agent_registry",
    "register_agent",
    "get_agent",
    "get_agent_for",

    # Coordinator
    "RequestType",
    "Request",
    "Response",
    "CoordinatorAgent",
    "get_coordinator",
    "process",
    "start_coordinator",
    "stop_coordinator"
]
