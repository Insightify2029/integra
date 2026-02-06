"""
INTEGRA - Learning AI Agent
وكيل التعلم الذكي
المحور K

يتعلم من أنماط المستخدم ويحسن الاقتراحات.

التاريخ: 4 فبراير 2026
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import json
import os
import threading

from core.logging import app_logger

# Try importing orchestration
try:
    from core.ai.orchestration import (
        BaseAgent, AgentCapability, AgentStatus,
        get_agent_registry, register_agent,
        subscribe_to_event, EventType
    )
    ORCHESTRATION_AVAILABLE = True
except ImportError:
    ORCHESTRATION_AVAILABLE = False
    BaseAgent = object
    app_logger.debug("Orchestration not available for learning agent")


@dataclass
class UserPreference:
    """تفضيل المستخدم"""
    key: str
    value: Any
    category: str
    confidence: float = 0.5
    times_used: int = 1
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class UserPattern:
    """نمط سلوكي للمستخدم"""
    pattern_type: str
    description: str
    frequency: int
    average_value: Optional[float] = None
    values: List[Any] = field(default_factory=list)
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)


@dataclass
class Feedback:
    """ردود فعل المستخدم"""
    suggestion_type: str
    suggestion_value: Any
    accepted: bool
    user_modified_value: Optional[Any] = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class LearningInsight:
    """رؤية مستفادة"""
    insight_type: str
    description: str
    description_ar: str
    recommendation: str
    recommendation_ar: str
    confidence: float
    supporting_data: Dict[str, Any] = field(default_factory=dict)


class LearningAgent(BaseAgent if ORCHESTRATION_AVAILABLE else object):
    """
    وكيل التعلم الذكي

    قدرات:
    - تعلم تفضيلات المستخدم
    - اكتشاف الأنماط السلوكية
    - تحسين الاقتراحات بناءً على الردود
    - تذكر السياق
    """

    _instance = None

    # قدرات الوكيل
    AGENT_CAPABILITIES = [
        AgentCapability.PATTERN_DETECTION,
        AgentCapability.USER_PREFERENCE_LEARNING,
        AgentCapability.SUGGESTION_IMPROVEMENT
    ] if ORCHESTRATION_AVAILABLE else []

    # مسار ملف التخزين
    STORAGE_PATH = "data/learning"
    PREFERENCES_FILE = "user_preferences.json"
    PATTERNS_FILE = "user_patterns.json"
    FEEDBACK_FILE = "feedback_history.json"

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
                agent_id="learning_agent",
                name="Learning Agent",
                name_ar="وكيل التعلم"
            )

        # البيانات في الذاكرة
        self._preferences: Dict[str, UserPreference] = {}
        self._patterns: Dict[str, UserPattern] = {}
        self._feedback_history: List[Feedback] = []
        self._session_context: Dict[str, Any] = {}
        self._lock = threading.RLock()

        # تحميل البيانات المحفوظة
        self._load_data()

        # الاشتراك في الأحداث
        self._subscribe_to_events()

        self._initialized = True
        app_logger.info("LearningAgent initialized")

    def _subscribe_to_events(self):
        """الاشتراك في الأحداث للتعلم منها"""
        if not ORCHESTRATION_AVAILABLE:
            return

        # الاشتراك في أحداث مختلفة للتعلم
        events_to_learn_from = [
            EventType.TASK_COMPLETED,
            EventType.FORM_SUBMITTED,
            EventType.EMAIL_REPLIED,
            EventType.NOTIFICATION_ACTION
        ]

        for event_type in events_to_learn_from:
            try:
                subscribe_to_event(
                    event_type,
                    self._learn_from_event,
                    f"learning_{event_type.name}"
                )
            except Exception:
                pass  # قد لا تكون كل الأحداث متاحة

    def _learn_from_event(self, event) -> None:
        """التعلم من حدث"""
        try:
            event_data = event.data if hasattr(event, 'data') else {}

            # تسجيل النمط
            self._record_pattern(
                pattern_type=event.type.name if hasattr(event, 'type') else "unknown",
                value=event_data
            )

        except Exception as e:
            app_logger.debug(f"Error learning from event: {e}")

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
            "learn_preference", "get_preference", "record_feedback",
            "get_patterns", "get_insights", "pattern_detection",
            "user_preference_learning", "suggestion_improvement"
        ]
        return task_type.lower() in supported_types

    def handle(self, task_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """معالجة المهمة"""
        task_type_lower = task_type.lower()

        if task_type_lower in ["learn_preference", "user_preference_learning"]:
            key = data.get("key", "")
            value = data.get("value")
            category = data.get("category", "general")
            self.learn_preference(key, value, category)
            return {"success": True, "key": key}

        elif task_type_lower == "get_preference":
            key = data.get("key", "")
            default = data.get("default")
            value = self.get_preference(key, default)
            return {"key": key, "value": value}

        elif task_type_lower == "record_feedback":
            self.record_feedback(
                suggestion_type=data.get("suggestion_type", ""),
                suggestion_value=data.get("suggestion_value"),
                accepted=data.get("accepted", False),
                user_modified_value=data.get("user_modified_value"),
                context=data.get("context", {})
            )
            return {"success": True}

        elif task_type_lower in ["get_patterns", "pattern_detection"]:
            pattern_type = data.get("pattern_type")
            patterns = self.get_patterns(pattern_type)
            return {
                "patterns": [
                    {
                        "type": p.pattern_type,
                        "description": p.description,
                        "frequency": p.frequency
                    }
                    for p in patterns
                ]
            }

        elif task_type_lower == "get_insights":
            insights = self.get_insights()
            return {
                "insights": [
                    {
                        "type": i.insight_type,
                        "description_ar": i.description_ar,
                        "recommendation_ar": i.recommendation_ar,
                        "confidence": i.confidence
                    }
                    for i in insights
                ]
            }

        return {"success": False, "error": f"Unsupported task type: {task_type}"}

    # ═══════════════════════════════════════════════════════════════
    # User Preferences
    # ═══════════════════════════════════════════════════════════════

    def learn_preference(
        self,
        key: str,
        value: Any,
        category: str = "general"
    ):
        """
        تعلم تفضيل جديد

        Args:
            key: مفتاح التفضيل
            value: القيمة
            category: التصنيف
        """
        with self._lock:
            if key in self._preferences:
                pref = self._preferences[key]
                pref.value = value
                pref.times_used += 1
                pref.confidence = min(pref.confidence + 0.1, 1.0)
                pref.last_updated = datetime.now()
            else:
                self._preferences[key] = UserPreference(
                    key=key,
                    value=value,
                    category=category
                )

        self._save_preferences()
        app_logger.debug(f"Learned preference: {key} = {value}")

    def get_preference(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """
        جلب تفضيل

        Args:
            key: مفتاح التفضيل
            default: القيمة الافتراضية

        Returns:
            قيمة التفضيل
        """
        with self._lock:
            pref = self._preferences.get(key)

        if pref:
            return pref.value
        return default

    def get_preferences_by_category(self, category: str) -> Dict[str, Any]:
        """جلب تفضيلات بالتصنيف"""
        with self._lock:
            return {
                k: v.value
                for k, v in self._preferences.items()
                if v.category == category
            }

    # ═══════════════════════════════════════════════════════════════
    # Pattern Detection
    # ═══════════════════════════════════════════════════════════════

    def _record_pattern(
        self,
        pattern_type: str,
        value: Any = None,
        description: str = ""
    ):
        """تسجيل نمط"""
        with self._lock:
            if pattern_type in self._patterns:
                pattern = self._patterns[pattern_type]
                pattern.frequency += 1
                pattern.last_seen = datetime.now()
                if value is not None:
                    pattern.values.append(value)
                    # حساب المتوسط للقيم الرقمية
                    if isinstance(value, (int, float)):
                        pattern.average_value = sum(
                            v for v in pattern.values if isinstance(v, (int, float))
                        ) / len([v for v in pattern.values if isinstance(v, (int, float))])
            else:
                self._patterns[pattern_type] = UserPattern(
                    pattern_type=pattern_type,
                    description=description or pattern_type,
                    frequency=1,
                    values=[value] if value else []
                )

        self._save_patterns()

    def get_patterns(
        self,
        pattern_type: Optional[str] = None
    ) -> List[UserPattern]:
        """جلب الأنماط المكتشفة"""
        with self._lock:
            if pattern_type:
                pattern = self._patterns.get(pattern_type)
                return [pattern] if pattern else []
            return list(self._patterns.values())

    def detect_time_patterns(self) -> Dict[str, Any]:
        """
        اكتشاف أنماط الوقت

        Returns:
            أنماط مثل: أفضل أوقات العمل، أيام الذروة
        """
        patterns = {
            "preferred_work_hours": [],
            "peak_days": [],
            "average_task_duration": None
        }

        # تحليل بناءً على الأنماط المسجلة
        task_times = self._patterns.get("TASK_COMPLETED")
        if task_times and task_times.values:
            # استخراج الساعات
            hours = []
            for val in task_times.values:
                if isinstance(val, dict) and "timestamp" in val:
                    try:
                        dt = datetime.fromisoformat(val["timestamp"])
                        hours.append(dt.hour)
                    except (ValueError, TypeError):
                        pass

            if hours:
                # حساب الساعات الأكثر تكراراً
                from collections import Counter
                hour_counts = Counter(hours)
                patterns["preferred_work_hours"] = [
                    h for h, _ in hour_counts.most_common(3)
                ]

        return patterns

    # ═══════════════════════════════════════════════════════════════
    # Feedback Learning
    # ═══════════════════════════════════════════════════════════════

    def record_feedback(
        self,
        suggestion_type: str,
        suggestion_value: Any,
        accepted: bool,
        user_modified_value: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        تسجيل رد فعل المستخدم على اقتراح

        Args:
            suggestion_type: نوع الاقتراح (priority, category, etc.)
            suggestion_value: القيمة المقترحة
            accepted: هل قُبل؟
            user_modified_value: القيمة المعدلة (إذا عُدل)
            context: السياق
        """
        feedback = Feedback(
            suggestion_type=suggestion_type,
            suggestion_value=suggestion_value,
            accepted=accepted,
            user_modified_value=user_modified_value,
            context=context or {}
        )

        with self._lock:
            self._feedback_history.append(feedback)

        # التعلم من الرد
        if accepted:
            # تعزيز الثقة في هذا النوع من الاقتراحات
            self.learn_preference(
                f"suggestion_accepted_{suggestion_type}",
                suggestion_value,
                category="suggestions"
            )
        elif user_modified_value is not None:
            # تعلم التفضيل الجديد
            self.learn_preference(
                f"preferred_{suggestion_type}",
                user_modified_value,
                category="suggestions"
            )

        self._save_feedback()
        app_logger.debug(
            f"Recorded feedback: {suggestion_type} "
            f"{'accepted' if accepted else 'modified/rejected'}"
        )

    def get_acceptance_rate(self, suggestion_type: str) -> float:
        """
        حساب معدل قبول نوع اقتراح

        Args:
            suggestion_type: نوع الاقتراح

        Returns:
            نسبة القبول (0-1)
        """
        with self._lock:
            relevant = [
                f for f in self._feedback_history
                if f.suggestion_type == suggestion_type
            ]

        if not relevant:
            return 0.5  # افتراضي

        accepted_count = sum(1 for f in relevant if f.accepted)
        return accepted_count / len(relevant)

    def get_preferred_value(
        self,
        suggestion_type: str,
        default: Any = None
    ) -> Any:
        """
        جلب القيمة المفضلة بناءً على التاريخ

        Args:
            suggestion_type: نوع الاقتراح
            default: الافتراضي

        Returns:
            القيمة المفضلة
        """
        # أولاً: التحقق من التفضيلات المحفوظة
        pref_key = f"preferred_{suggestion_type}"
        pref_value = self.get_preference(pref_key)
        if pref_value is not None:
            return pref_value

        # ثانياً: تحليل تاريخ الردود
        with self._lock:
            relevant = [
                f for f in self._feedback_history
                if f.suggestion_type == suggestion_type
                and (f.accepted or f.user_modified_value is not None)
            ]

        if relevant:
            # جلب آخر قيمة مقبولة أو معدلة
            last = relevant[-1]
            return last.user_modified_value if last.user_modified_value else last.suggestion_value

        return default

    # ═══════════════════════════════════════════════════════════════
    # Insights Generation
    # ═══════════════════════════════════════════════════════════════

    def get_insights(self) -> List[LearningInsight]:
        """
        توليد رؤى من البيانات المتعلمة

        Returns:
            قائمة الرؤى
        """
        insights = []

        with self._lock:
            # رؤية: معدلات القبول
            suggestion_types = set(f.suggestion_type for f in self._feedback_history)
            # snapshot patterns for iteration
            patterns_snapshot = dict(self._patterns)

        for stype in suggestion_types:
            rate = self.get_acceptance_rate(stype)
            if rate < 0.3:
                insights.append(LearningInsight(
                    insight_type="low_acceptance",
                    description=f"Low acceptance rate for {stype} suggestions",
                    description_ar=f"معدل قبول منخفض لاقتراحات {stype}",
                    recommendation=f"Consider adjusting {stype} suggestion algorithm",
                    recommendation_ar=f"يُنصح بتعديل خوارزمية اقتراحات {stype}",
                    confidence=0.8,
                    supporting_data={"acceptance_rate": rate}
                ))

        # رؤية: الأنماط المكررة
        for pattern_type, pattern in patterns_snapshot.items():
            if pattern.frequency > 10:
                insights.append(LearningInsight(
                    insight_type="frequent_pattern",
                    description=f"Frequent pattern detected: {pattern_type}",
                    description_ar=f"تم اكتشاف نمط متكرر: {pattern_type}",
                    recommendation="Consider automating this action",
                    recommendation_ar="يُنصح بأتمتة هذا الإجراء",
                    confidence=min(pattern.frequency / 20, 1.0),
                    supporting_data={"frequency": pattern.frequency}
                ))

        return insights

    # ═══════════════════════════════════════════════════════════════
    # Session Context
    # ═══════════════════════════════════════════════════════════════

    def set_context(self, key: str, value: Any):
        """تعيين سياق الجلسة"""
        with self._lock:
            self._session_context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """جلب سياق الجلسة"""
        with self._lock:
            return self._session_context.get(key, default)

    def clear_context(self):
        """مسح سياق الجلسة"""
        with self._lock:
            self._session_context.clear()

    # ═══════════════════════════════════════════════════════════════
    # Persistence
    # ═══════════════════════════════════════════════════════════════

    def _ensure_storage_path(self):
        """التأكد من وجود مجلد التخزين"""
        os.makedirs(self.STORAGE_PATH, exist_ok=True)

    def _load_data(self):
        """تحميل البيانات المحفوظة"""
        self._ensure_storage_path()

        # تحميل التفضيلات
        pref_path = os.path.join(self.STORAGE_PATH, self.PREFERENCES_FILE)
        if os.path.exists(pref_path):
            try:
                with open(pref_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, val in data.items():
                        self._preferences[key] = UserPreference(
                            key=key,
                            value=val.get("value"),
                            category=val.get("category", "general"),
                            confidence=val.get("confidence", 0.5),
                            times_used=val.get("times_used", 1)
                        )
            except Exception as e:
                app_logger.warning(f"Failed to load preferences: {e}")

        # تحميل الأنماط
        patterns_path = os.path.join(self.STORAGE_PATH, self.PATTERNS_FILE)
        if os.path.exists(patterns_path):
            try:
                with open(patterns_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, val in data.items():
                        self._patterns[key] = UserPattern(
                            pattern_type=key,
                            description=val.get("description", key),
                            frequency=val.get("frequency", 1),
                            values=val.get("values", [])
                        )
            except Exception as e:
                app_logger.warning(f"Failed to load patterns: {e}")

    def _save_preferences(self):
        """حفظ التفضيلات"""
        self._ensure_storage_path()
        pref_path = os.path.join(self.STORAGE_PATH, self.PREFERENCES_FILE)

        try:
            with self._lock:
                data = {
                    k: {
                        "value": v.value,
                        "category": v.category,
                        "confidence": v.confidence,
                        "times_used": v.times_used
                    }
                    for k, v in self._preferences.items()
                }

            with open(pref_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            app_logger.warning(f"Failed to save preferences: {e}")

    def _save_patterns(self):
        """حفظ الأنماط"""
        self._ensure_storage_path()
        patterns_path = os.path.join(self.STORAGE_PATH, self.PATTERNS_FILE)

        try:
            with self._lock:
                data = {
                    k: {
                        "description": v.description,
                        "frequency": v.frequency,
                        "values": v.values[-100:]  # آخر 100 قيمة فقط
                    }
                    for k, v in self._patterns.items()
                }

            with open(patterns_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            app_logger.warning(f"Failed to save patterns: {e}")

    def _save_feedback(self):
        """حفظ تاريخ الردود"""
        self._ensure_storage_path()
        feedback_path = os.path.join(self.STORAGE_PATH, self.FEEDBACK_FILE)

        try:
            with self._lock:
                # آخر 500 رد فقط
                data = [
                    {
                        "suggestion_type": f.suggestion_type,
                        "suggestion_value": f.suggestion_value,
                        "accepted": f.accepted,
                        "user_modified_value": f.user_modified_value,
                        "timestamp": f.timestamp.isoformat()
                    }
                    for f in self._feedback_history[-500:]
                ]

            with open(feedback_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            app_logger.warning(f"Failed to save feedback: {e}")


# ═══════════════════════════════════════════════════════════════
# Singleton & Quick Access Functions
# ═══════════════════════════════════════════════════════════════

_agent: Optional[LearningAgent] = None


def get_learning_agent() -> LearningAgent:
    """الحصول على instance الوكيل"""
    global _agent
    if _agent is None:
        _agent = LearningAgent()
    return _agent


def learn_preference(key: str, value: Any, category: str = "general"):
    """تعلم تفضيل"""
    get_learning_agent().learn_preference(key, value, category)


def get_preference(key: str, default: Any = None) -> Any:
    """جلب تفضيل"""
    return get_learning_agent().get_preference(key, default)


def record_feedback(
    suggestion_type: str,
    suggestion_value: Any,
    accepted: bool,
    user_modified_value: Optional[Any] = None
):
    """تسجيل رد فعل"""
    get_learning_agent().record_feedback(
        suggestion_type, suggestion_value, accepted, user_modified_value
    )


def get_preferred_value(suggestion_type: str, default: Any = None) -> Any:
    """جلب القيمة المفضلة"""
    return get_learning_agent().get_preferred_value(suggestion_type, default)


def register_learning_agent() -> bool:
    """تسجيل وكيل التعلم في منظومة التنسيق"""
    if not ORCHESTRATION_AVAILABLE:
        return False

    try:
        agent = get_learning_agent()
        register_agent(
            agent_id="learning_agent",
            agent=agent,
            capabilities=agent.AGENT_CAPABILITIES,
            name="Learning Agent",
            name_ar="وكيل التعلم",
            description="وكيل ذكي للتعلم من أنماط المستخدم",
            priority=3
        )
        app_logger.info("LearningAgent registered with orchestration")
        return True
    except Exception as e:
        app_logger.error(f"Failed to register LearningAgent: {e}")
        return False
