"""
INTEGRA - Task AI Agent
وكيل المهام الذكي
المحور H + K

يحلل المهام ويقترح الأولوية والتصنيف والإجراءات.
متكامل مع منظومة وكلاء AI (Track K).

التاريخ: 4 فبراير 2026
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field

from core.logging import app_logger

# Try importing AI service
try:
    from core.ai import get_ai_service, is_ollama_available
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    app_logger.warning("AI service not available for task agent")

# Try importing orchestration
try:
    from core.ai.orchestration import (
        BaseAgent, AgentCapability, AgentStatus,
        get_agent_registry, register_agent
    )
    ORCHESTRATION_AVAILABLE = True
except ImportError:
    ORCHESTRATION_AVAILABLE = False
    BaseAgent = object  # Fallback
    app_logger.debug("Orchestration not available for task agent")


@dataclass
class TaskAnalysis:
    """نتيجة تحليل المهمة"""
    suggested_priority: str = "normal"
    suggested_category: str = "general"
    suggested_due_date: Optional[datetime] = None
    suggested_action: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    related_employee_ids: List[int] = field(default_factory=list)
    priority_score: float = 0.5
    confidence: float = 0.0
    reasoning: Optional[str] = None


@dataclass
class TaskSuggestion:
    """اقتراح للمهمة"""
    type: str  # priority, category, due_date, action, delegate
    suggestion: str
    reason: str
    confidence: float = 0.0


class TaskAgent(BaseAgent if ORCHESTRATION_AVAILABLE else object):
    """
    وكيل المهام الذكي

    قدرات:
    - تحليل المهمة واقتراح الأولوية والتصنيف
    - اقتراح تاريخ الاستحقاق
    - اقتراح الإجراء المناسب
    - اكتشاف المهام المتأخرة
    - اقتراح تفويض المهمة

    متكامل مع منظومة التنسيق (Orchestration).
    """

    _instance = None

    # قدرات الوكيل للـ Orchestration
    AGENT_CAPABILITIES = [
        AgentCapability.TASK_CREATION,
        AgentCapability.TASK_PRIORITIZATION,
        AgentCapability.TASK_SCHEDULING,
        AgentCapability.TASK_ANALYSIS
    ] if ORCHESTRATION_AVAILABLE else []

    # Keywords for classification
    PRIORITY_KEYWORDS = {
        "urgent": ["عاجل", "فوري", "طوارئ", "ضروري", "الآن", "urgent", "asap", "immediately"],
        "high": ["مهم", "هام", "أولوية", "سريع", "important", "priority", "critical"],
        "low": ["لاحقاً", "غير عاجل", "عادي", "بسيط", "later", "low priority"]
    }

    CATEGORY_KEYWORDS = {
        "hr": ["موظف", "موظفين", "إجازة", "راتب", "رواتب", "تعيين", "فصل", "تسوية", "employee", "hr", "salary", "leave"],
        "finance": ["مالية", "محاسبة", "فاتورة", "دفع", "تحويل", "بنك", "ميزانية", "finance", "payment", "invoice"],
        "operations": ["عمليات", "تشغيل", "صيانة", "إنتاج", "operations", "maintenance"],
        "it": ["تقنية", "برمجة", "نظام", "برنامج", "كمبيوتر", "شبكة", "it", "software", "system"],
        "legal": ["قانوني", "عقد", "قضية", "محكمة", "legal", "contract", "court"],
        "admin": ["إداري", "إدارة", "مكتب", "سكرتارية", "admin", "office"]
    }

    ACTION_TEMPLATES = {
        "hr": {
            "إجازة": "مراجعة طلب الإجازة → التحقق من الرصيد → الموافقة/الرفض",
            "راتب": "مراجعة البيانات → حساب المستحقات → التحويل",
            "تعيين": "مراجعة السيرة الذاتية → المقابلة → إعداد العقد",
            "تسوية": "حساب المستحقات النهائية → تجهيز شهادة الخبرة",
        },
        "finance": {
            "فاتورة": "مراجعة الفاتورة → التحقق من البنود → الاعتماد → الدفع",
            "تحويل": "التحقق من البيانات → إعداد التحويل → التنفيذ",
        }
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return

        # تهيئة BaseAgent إذا كان متاحاً
        if ORCHESTRATION_AVAILABLE:
            super().__init__(
                agent_id="task_agent",
                name="Task Agent",
                name_ar="وكيل المهام"
            )

        self._initialized = True
        app_logger.info("TaskAgent initialized")

    # ═══════════════════════════════════════════════════════════════
    # Orchestration Integration (BaseAgent methods)
    # ═══════════════════════════════════════════════════════════════

    @property
    def capabilities(self) -> List:
        """قدرات الوكيل"""
        return self.AGENT_CAPABILITIES

    def can_handle(self, task_type: str, data: Dict[str, Any]) -> bool:
        """
        هل يمكن للوكيل معالجة هذه المهمة؟

        Args:
            task_type: نوع المهمة
            data: بيانات المهمة

        Returns:
            True إذا كان يمكنه المعالجة
        """
        supported_types = [
            "analyze_task", "prioritize_task", "create_task",
            "schedule_task", "task_analysis", "task_prioritization",
            "task_creation", "task_scheduling"
        ]
        return task_type.lower() in supported_types

    def handle(self, task_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        معالجة المهمة

        Args:
            task_type: نوع المهمة
            data: بيانات المهمة

        Returns:
            نتيجة المعالجة
        """
        task_type_lower = task_type.lower()

        if task_type_lower in ["analyze_task", "task_analysis"]:
            title = data.get("title", "")
            description = data.get("description")
            source = data.get("source")
            analysis = self.analyze_task(title, description, source)
            return {
                "priority": analysis.suggested_priority,
                "category": analysis.suggested_category,
                "due_date": analysis.suggested_due_date.isoformat() if analysis.suggested_due_date else None,
                "action": analysis.suggested_action,
                "keywords": analysis.keywords,
                "confidence": analysis.confidence
            }

        elif task_type_lower in ["prioritize_task", "task_prioritization"]:
            title = data.get("title", "")
            description = data.get("description")
            analysis = self.analyze_task(title, description)
            return {
                "priority": analysis.suggested_priority,
                "priority_score": analysis.priority_score,
                "reasoning": analysis.reasoning
            }

        elif task_type_lower in ["schedule_task", "task_scheduling"]:
            title = data.get("title", "")
            description = data.get("description")
            analysis = self.analyze_task(title, description)
            return {
                "suggested_due_date": analysis.suggested_due_date.isoformat() if analysis.suggested_due_date else None,
                "priority": analysis.suggested_priority
            }

        elif task_type_lower in ["create_task", "task_creation"]:
            # تحليل وإنشاء مهمة جديدة
            title = data.get("title", "")
            description = data.get("description")
            analysis = self.analyze_task(title, description)
            return {
                "title": title,
                "description": description,
                "suggested_priority": analysis.suggested_priority,
                "suggested_category": analysis.suggested_category,
                "suggested_due_date": analysis.suggested_due_date.isoformat() if analysis.suggested_due_date else None,
                "suggested_action": analysis.suggested_action,
                "keywords": analysis.keywords
            }

        else:
            raise ValueError(f"Unsupported task type: {task_type}")

    # ═══════════════════════════════════════════════════════════════
    # Original Task Analysis Methods
    # ═══════════════════════════════════════════════════════════════

    def analyze_task(
        self,
        title: str,
        description: Optional[str] = None,
        source: Optional[str] = None
    ) -> TaskAnalysis:
        """
        تحليل مهمة واقتراح التصنيف والأولوية

        Args:
            title: عنوان المهمة
            description: وصف المهمة
            source: مصدر المهمة (email, manual, etc.)

        Returns:
            نتيجة التحليل
        """
        text = f"{title} {description or ''}"
        text_lower = text.lower()

        # Analyze priority
        priority, priority_score = self._analyze_priority(text_lower)

        # Analyze category
        category, cat_confidence = self._analyze_category(text_lower)

        # Extract keywords
        keywords = self._extract_keywords(text)

        # Suggest due date
        due_date = self._suggest_due_date(priority, category)

        # Suggest action
        action = self._suggest_action(category, text_lower)

        # Use AI if available for better analysis
        ai_analysis = None
        if AI_AVAILABLE and is_ollama_available():
            ai_analysis = self._ai_analyze(title, description)

        # Merge AI analysis if available
        if ai_analysis:
            if ai_analysis.get("priority"):
                priority = ai_analysis["priority"]
                priority_score = ai_analysis.get("priority_score", priority_score)
            if ai_analysis.get("category"):
                category = ai_analysis["category"]
            if ai_analysis.get("action"):
                action = ai_analysis["action"]
            if ai_analysis.get("keywords"):
                keywords.extend(ai_analysis["keywords"])

        return TaskAnalysis(
            suggested_priority=priority,
            suggested_category=category,
            suggested_due_date=due_date,
            suggested_action=action,
            keywords=list(set(keywords)),
            priority_score=priority_score,
            confidence=cat_confidence
        )

    def _analyze_priority(self, text: str) -> Tuple[str, float]:
        """تحليل الأولوية"""
        for priority, keywords in self.PRIORITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    score = 0.9 if priority == "urgent" else (0.7 if priority == "high" else 0.3)
                    return priority, score

        return "normal", 0.5

    def _analyze_category(self, text: str) -> Tuple[str, float]:
        """تحليل التصنيف"""
        matches = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            count = sum(1 for keyword in keywords if keyword in text)
            if count > 0:
                matches[category] = count

        if matches:
            best_category = max(matches, key=matches.get)
            confidence = min(matches[best_category] / 3, 1.0)
            return best_category, confidence

        return "general", 0.3

    def _extract_keywords(self, text: str) -> List[str]:
        """استخراج الكلمات المفتاحية"""
        keywords = []

        # All keywords from our dictionaries
        all_keywords = []
        for kw_list in self.PRIORITY_KEYWORDS.values():
            all_keywords.extend(kw_list)
        for kw_list in self.CATEGORY_KEYWORDS.values():
            all_keywords.extend(kw_list)

        text_lower = text.lower()
        for keyword in all_keywords:
            if keyword in text_lower:
                keywords.append(keyword)

        return keywords

    def _suggest_due_date(
        self,
        priority: str,
        category: str
    ) -> Optional[datetime]:
        """اقتراح تاريخ الاستحقاق"""
        now = datetime.now()

        if priority == "urgent":
            return now + timedelta(hours=4)
        elif priority == "high":
            return now + timedelta(days=1)
        elif category in ["hr", "finance"]:
            return now + timedelta(days=3)
        else:
            return now + timedelta(days=7)

    def _suggest_action(self, category: str, text: str) -> Optional[str]:
        """اقتراح الإجراء"""
        if category in self.ACTION_TEMPLATES:
            templates = self.ACTION_TEMPLATES[category]
            for keyword, action in templates.items():
                if keyword in text:
                    return action

        # Generic action
        return "مراجعة المهمة → تحديد الخطوات → التنفيذ → التأكيد"

    def _ai_analyze(
        self,
        title: str,
        description: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """تحليل بالذكاء الاصطناعي"""
        try:
            service = get_ai_service()

            prompt = f"""حلل المهمة التالية واقترح:
1. الأولوية (urgent/high/normal/low)
2. التصنيف (hr/finance/operations/it/legal/admin/general)
3. الإجراء المقترح (خطوات مختصرة)
4. كلمات مفتاحية

العنوان: {title}
الوصف: {description or 'لا يوجد'}

الرد بصيغة JSON فقط:
{{"priority": "...", "category": "...", "action": "...", "keywords": [...]}}"""

            response = service.chat(prompt)

            # Try to parse JSON from response
            import json
            import re

            # Find JSON in response
            json_match = re.search(r'\{[^{}]*\}', response)
            if json_match:
                return json.loads(json_match.group())

        except Exception as e:
            app_logger.debug(f"AI analysis failed: {e}")

        return None

    def get_suggestions(self, task) -> List[TaskSuggestion]:
        """
        الحصول على اقتراحات للمهمة

        Args:
            task: المهمة (Task object)

        Returns:
            قائمة الاقتراحات
        """
        suggestions = []

        # Analyze task
        analysis = self.analyze_task(task.title, task.description)

        # Priority suggestion
        if analysis.suggested_priority != task.priority.value:
            suggestions.append(TaskSuggestion(
                type="priority",
                suggestion=analysis.suggested_priority,
                reason=f"بناءً على محتوى المهمة، الأولوية المقترحة: {analysis.suggested_priority}",
                confidence=analysis.priority_score
            ))

        # Category suggestion
        if analysis.suggested_category != task.category:
            suggestions.append(TaskSuggestion(
                type="category",
                suggestion=analysis.suggested_category,
                reason=f"التصنيف المقترح بناءً على المحتوى: {analysis.suggested_category}",
                confidence=analysis.confidence
            ))

        # Due date suggestion
        if not task.due_date and analysis.suggested_due_date:
            suggestions.append(TaskSuggestion(
                type="due_date",
                suggestion=analysis.suggested_due_date.strftime("%Y-%m-%d %H:%M"),
                reason="اقتراح تاريخ استحقاق بناءً على الأولوية والتصنيف",
                confidence=0.6
            ))

        # Action suggestion
        if analysis.suggested_action and not task.ai_suggested_action:
            suggestions.append(TaskSuggestion(
                type="action",
                suggestion=analysis.suggested_action,
                reason="خطوات مقترحة لإنجاز المهمة",
                confidence=0.7
            ))

        return suggestions

    def detect_overdue_risks(self, tasks: list) -> List[Dict[str, Any]]:
        """
        اكتشاف المهام المعرضة للتأخير

        Args:
            tasks: قائمة المهام

        Returns:
            قائمة بالمهام المعرضة للتأخير
        """
        risks = []
        now = datetime.now()

        for task in tasks:
            if task.status.value in ["completed", "cancelled"]:
                continue

            if task.due_date:
                time_until_due = task.due_date - now

                # Already overdue
                if time_until_due.total_seconds() < 0:
                    risks.append({
                        "task_id": task.id,
                        "title": task.title,
                        "risk_level": "critical",
                        "message": f"المهمة متأخرة بـ {abs(time_until_due.days)} يوم",
                        "action": "يجب البدء فوراً أو إعادة جدولة"
                    })

                # Due within 24 hours
                elif time_until_due.total_seconds() < 86400:
                    risks.append({
                        "task_id": task.id,
                        "title": task.title,
                        "risk_level": "high",
                        "message": "المهمة مستحقة خلال 24 ساعة",
                        "action": "ابدأ العمل على المهمة الآن"
                    })

                # Due within 3 days and high priority
                elif time_until_due.days <= 3 and task.priority.value in ["urgent", "high"]:
                    risks.append({
                        "task_id": task.id,
                        "title": task.title,
                        "risk_level": "medium",
                        "message": f"مهمة عالية الأولوية مستحقة خلال {time_until_due.days} أيام",
                        "action": "خطط للبدء قريباً"
                    })

        return risks

    def suggest_task_order(self, tasks: list) -> List[int]:
        """
        اقتراح ترتيب المهام

        Args:
            tasks: قائمة المهام

        Returns:
            قائمة معرفات المهام مرتبة
        """
        # Score each task
        scored_tasks = []
        now = datetime.now()

        for task in tasks:
            if task.status.value in ["completed", "cancelled"]:
                continue

            score = 0

            # Priority score
            priority_scores = {"urgent": 100, "high": 70, "normal": 40, "low": 10}
            score += priority_scores.get(task.priority.value, 40)

            # Due date score
            if task.due_date:
                days_until_due = (task.due_date - now).days
                if days_until_due < 0:
                    score += 200  # Overdue gets highest score
                elif days_until_due == 0:
                    score += 100
                elif days_until_due <= 3:
                    score += 50
                elif days_until_due <= 7:
                    score += 20

            # Category bonus (HR and Finance are often time-sensitive)
            if task.category in ["hr", "finance"]:
                score += 15

            scored_tasks.append((task.id, score))

        # Sort by score descending
        scored_tasks.sort(key=lambda x: x[1], reverse=True)

        return [task_id for task_id, _ in scored_tasks]


# ═══════════════════════════════════════════════════════════════
# Singleton & Quick Access Functions
# ═══════════════════════════════════════════════════════════════

_agent: Optional[TaskAgent] = None


def get_task_agent() -> TaskAgent:
    """الحصول على instance الوكيل"""
    global _agent
    if _agent is None:
        _agent = TaskAgent()
    return _agent


def analyze_task(
    title: str,
    description: Optional[str] = None
) -> TaskAnalysis:
    """تحليل مهمة"""
    return get_task_agent().analyze_task(title, description)


def get_task_suggestions(task) -> List[TaskSuggestion]:
    """الحصول على اقتراحات للمهمة"""
    return get_task_agent().get_suggestions(task)


def detect_overdue_risks(tasks: list) -> List[Dict[str, Any]]:
    """اكتشاف المهام المعرضة للتأخير"""
    return get_task_agent().detect_overdue_risks(tasks)


def suggest_task_order(tasks: list) -> List[int]:
    """اقتراح ترتيب المهام"""
    return get_task_agent().suggest_task_order(tasks)


def register_task_agent() -> bool:
    """
    تسجيل وكيل المهام في منظومة التنسيق

    Returns:
        True إذا تم التسجيل بنجاح
    """
    if not ORCHESTRATION_AVAILABLE:
        app_logger.debug("Orchestration not available, skipping task agent registration")
        return False

    try:
        agent = get_task_agent()
        register_agent(
            agent_id="task_agent",
            agent=agent,
            capabilities=agent.AGENT_CAPABILITIES,
            name="Task Agent",
            name_ar="وكيل المهام",
            description="وكيل ذكي لتحليل المهام واقتراح الأولوية والتصنيف",
            priority=10
        )
        app_logger.info("TaskAgent registered with orchestration")
        return True
    except Exception as e:
        app_logger.error(f"Failed to register TaskAgent: {e}")
        return False
