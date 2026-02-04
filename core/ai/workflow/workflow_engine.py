"""
INTEGRA - Workflow Engine
محرك سير العمل
المحور K

يدير تعريف وتنفيذ سيناريوهات العمل الآلية.

الاستخدام:
    from core.ai.workflow import Workflow, Step, Condition

    # تعريف سير عمل
    workflow = Workflow("vacation_settlement")
    workflow.add_step(Step("analyze_email", email_agent.analyze))
    workflow.add_step(Step("create_task", task_agent.create))
    workflow.add_condition(Condition("user_approves", then_step, else_step))
    workflow.add_step(Step("save", action_agent.save))

    # تنفيذ
    result = workflow.execute(context={"email": email_data})

التاريخ: 4 فبراير 2026
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import threading
import uuid

from core.logging import app_logger


class StepStatus(Enum):
    """حالة الخطوة"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING = "waiting"  # انتظار إدخال المستخدم


class WorkflowStatus(Enum):
    """حالة سير العمل"""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING_USER = "waiting_user"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class StepResult:
    """نتيجة تنفيذ خطوة"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    next_step: Optional[str] = None


# نوع دالة الخطوة
StepHandler = Callable[[Dict[str, Any]], StepResult]

# نوع دالة الشرط
ConditionChecker = Callable[[Dict[str, Any]], bool]


@dataclass
class Step:
    """خطوة في سير العمل"""
    id: str
    name: str
    name_ar: str
    handler: Optional[StepHandler] = None
    agent_id: Optional[str] = None  # استخدام وكيل بدل handler
    agent_task: Optional[str] = None  # نوع المهمة للوكيل
    status: StepStatus = StepStatus.PENDING
    result: Optional[StepResult] = None
    requires_user_input: bool = False
    user_prompt: Optional[str] = None
    user_prompt_ar: Optional[str] = None
    timeout_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 3
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def execute(self, context: Dict[str, Any]) -> StepResult:
        """تنفيذ الخطوة"""
        self.status = StepStatus.RUNNING
        self.started_at = datetime.now()

        try:
            if self.handler:
                result = self.handler(context)
            elif self.agent_id and self.agent_task:
                result = self._execute_via_agent(context)
            else:
                result = StepResult(
                    success=True,
                    data=context
                )

            self.result = result
            self.status = StepStatus.COMPLETED if result.success else StepStatus.FAILED
            self.completed_at = datetime.now()

            return result

        except Exception as e:
            self.status = StepStatus.FAILED
            self.completed_at = datetime.now()
            error_result = StepResult(success=False, error=str(e))
            self.result = error_result
            return error_result

    def _execute_via_agent(self, context: Dict[str, Any]) -> StepResult:
        """تنفيذ عبر وكيل"""
        try:
            from core.ai.orchestration import get_agent

            agent = get_agent(self.agent_id)
            if not agent:
                return StepResult(
                    success=False,
                    error=f"Agent {self.agent_id} not found"
                )

            result = agent.handle(self.agent_task, context)
            return StepResult(success=True, data=result)

        except ImportError:
            return StepResult(
                success=False,
                error="Orchestration not available"
            )

    def to_dict(self) -> Dict[str, Any]:
        """تحويل لـ dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "name_ar": self.name_ar,
            "status": self.status.value,
            "requires_user_input": self.requires_user_input
        }


@dataclass
class Condition:
    """شرط في سير العمل"""
    id: str
    name: str
    checker: ConditionChecker
    then_step: str  # معرف الخطوة إذا تحقق الشرط
    else_step: Optional[str] = None  # معرف الخطوة إذا لم يتحقق

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """تقييم الشرط"""
        try:
            return self.checker(context)
        except Exception as e:
            app_logger.error(f"Condition {self.id} evaluation failed: {e}")
            return False


class Workflow:
    """
    سير عمل

    يمثل سلسلة من الخطوات والشروط التي تُنفذ بالترتيب.
    """

    def __init__(
        self,
        id: str,
        name: str,
        name_ar: str,
        description: str = "",
        description_ar: str = ""
    ):
        self.id = id
        self.name = name
        self.name_ar = name_ar
        self.description = description
        self.description_ar = description_ar

        self._steps: Dict[str, Step] = {}
        self._conditions: Dict[str, Condition] = {}
        self._step_order: List[str] = []  # ترتيب الخطوات
        self._first_step: Optional[str] = None
        self._current_step: Optional[str] = None

        self.status = WorkflowStatus.NOT_STARTED
        self.context: Dict[str, Any] = {}
        self.history: List[Dict[str, Any]] = []

        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.instance_id = str(uuid.uuid4())[:8]

    def add_step(
        self,
        step_id: str,
        name: str,
        name_ar: str,
        handler: Optional[StepHandler] = None,
        agent_id: Optional[str] = None,
        agent_task: Optional[str] = None,
        requires_user_input: bool = False,
        user_prompt_ar: Optional[str] = None
    ) -> "Workflow":
        """
        إضافة خطوة

        Args:
            step_id: معرف الخطوة
            name: الاسم بالإنجليزي
            name_ar: الاسم بالعربي
            handler: دالة المعالجة
            agent_id: معرف الوكيل (بديل عن handler)
            agent_task: نوع المهمة للوكيل
            requires_user_input: هل تحتاج إدخال المستخدم
            user_prompt_ar: السؤال للمستخدم

        Returns:
            self للـ chaining
        """
        step = Step(
            id=step_id,
            name=name,
            name_ar=name_ar,
            handler=handler,
            agent_id=agent_id,
            agent_task=agent_task,
            requires_user_input=requires_user_input,
            user_prompt_ar=user_prompt_ar
        )

        self._steps[step_id] = step
        self._step_order.append(step_id)

        if self._first_step is None:
            self._first_step = step_id

        return self

    def add_condition(
        self,
        condition_id: str,
        name: str,
        checker: ConditionChecker,
        then_step: str,
        else_step: Optional[str] = None
    ) -> "Workflow":
        """
        إضافة شرط

        Args:
            condition_id: معرف الشرط
            name: الاسم
            checker: دالة التحقق
            then_step: الخطوة إذا تحقق
            else_step: الخطوة إذا لم يتحقق

        Returns:
            self للـ chaining
        """
        condition = Condition(
            id=condition_id,
            name=name,
            checker=checker,
            then_step=then_step,
            else_step=else_step
        )

        self._conditions[condition_id] = condition
        self._step_order.append(f"condition:{condition_id}")

        return self

    def set_step_transition(
        self,
        from_step: str,
        to_step: str,
        condition: Optional[ConditionChecker] = None
    ) -> "Workflow":
        """
        تعيين انتقال بين خطوتين

        Args:
            from_step: الخطوة المصدر
            to_step: الخطوة الهدف
            condition: شرط الانتقال (اختياري)

        Returns:
            self
        """
        # حالياً نستخدم الترتيب الخطي
        # يمكن توسيعه لدعم الانتقالات المعقدة
        return self

    def execute(
        self,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        تنفيذ سير العمل

        Args:
            context: السياق الأولي

        Returns:
            نتيجة التنفيذ
        """
        self.context = context or {}
        self.status = WorkflowStatus.RUNNING
        self.started_at = datetime.now()
        self._current_step = self._first_step

        app_logger.info(f"Starting workflow {self.id} (instance: {self.instance_id})")

        try:
            while self._current_step:
                # التحقق من الإلغاء
                if self.status == WorkflowStatus.CANCELLED:
                    break

                # معالجة الخطوة الحالية
                current = self._current_step

                if current.startswith("condition:"):
                    # معالجة شرط
                    condition_id = current.replace("condition:", "")
                    next_step = self._evaluate_condition(condition_id)
                else:
                    # معالجة خطوة
                    next_step = self._execute_step(current)

                self._current_step = next_step

            # اكتمال
            if self.status != WorkflowStatus.CANCELLED:
                self.status = WorkflowStatus.COMPLETED

            self.completed_at = datetime.now()

            return {
                "success": self.status == WorkflowStatus.COMPLETED,
                "status": self.status.value,
                "context": self.context,
                "history": self.history
            }

        except Exception as e:
            self.status = WorkflowStatus.FAILED
            self.completed_at = datetime.now()
            app_logger.error(f"Workflow {self.id} failed: {e}")

            return {
                "success": False,
                "status": self.status.value,
                "error": str(e),
                "context": self.context,
                "history": self.history
            }

    def _execute_step(self, step_id: str) -> Optional[str]:
        """تنفيذ خطوة"""
        step = self._steps.get(step_id)
        if not step:
            app_logger.warning(f"Step {step_id} not found")
            return self._get_next_step(step_id)

        # التحقق من الحاجة لإدخال المستخدم
        if step.requires_user_input:
            self.status = WorkflowStatus.WAITING_USER
            # في التطبيق الفعلي، سيتوقف هنا وينتظر
            # حالياً نتخطى
            return self._get_next_step(step_id)

        app_logger.debug(f"Executing step: {step.name_ar}")

        result = step.execute(self.context)

        # تسجيل في التاريخ
        self.history.append({
            "step_id": step_id,
            "step_name": step.name_ar,
            "status": step.status.value,
            "timestamp": datetime.now().isoformat(),
            "success": result.success
        })

        # تحديث السياق
        if result.success and result.data:
            if isinstance(result.data, dict):
                self.context.update(result.data)
            else:
                self.context[f"step_{step_id}_result"] = result.data

        # التحقق من الفشل
        if not result.success:
            if step.retry_count < step.max_retries:
                step.retry_count += 1
                step.status = StepStatus.PENDING
                return step_id  # إعادة المحاولة
            else:
                self.status = WorkflowStatus.FAILED
                return None

        # الخطوة التالية
        if result.next_step:
            return result.next_step

        return self._get_next_step(step_id)

    def _evaluate_condition(self, condition_id: str) -> Optional[str]:
        """تقييم شرط"""
        condition = self._conditions.get(condition_id)
        if not condition:
            return self._get_next_after_condition(condition_id)

        result = condition.evaluate(self.context)

        # تسجيل في التاريخ
        self.history.append({
            "condition_id": condition_id,
            "condition_name": condition.name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })

        if result:
            return condition.then_step
        elif condition.else_step:
            return condition.else_step
        else:
            return self._get_next_after_condition(condition_id)

    def _get_next_step(self, current_step_id: str) -> Optional[str]:
        """الحصول على الخطوة التالية"""
        try:
            idx = self._step_order.index(current_step_id)
            if idx + 1 < len(self._step_order):
                return self._step_order[idx + 1]
        except ValueError:
            pass
        return None

    def _get_next_after_condition(self, condition_id: str) -> Optional[str]:
        """الحصول على الخطوة بعد الشرط"""
        key = f"condition:{condition_id}"
        return self._get_next_step(key)

    def pause(self):
        """إيقاف مؤقت"""
        if self.status == WorkflowStatus.RUNNING:
            self.status = WorkflowStatus.PAUSED

    def resume(self):
        """استئناف"""
        if self.status == WorkflowStatus.PAUSED:
            self.status = WorkflowStatus.RUNNING
            # استمرار التنفيذ من الخطوة الحالية
            return self.execute(self.context)

    def cancel(self):
        """إلغاء"""
        self.status = WorkflowStatus.CANCELLED

    def provide_user_input(self, input_data: Dict[str, Any]):
        """توفير إدخال المستخدم"""
        self.context.update(input_data)
        if self.status == WorkflowStatus.WAITING_USER:
            self.status = WorkflowStatus.RUNNING

    def get_current_step(self) -> Optional[Step]:
        """الخطوة الحالية"""
        if self._current_step:
            return self._steps.get(self._current_step)
        return None

    def get_progress(self) -> Dict[str, Any]:
        """تقدم سير العمل"""
        total = len(self._steps)
        completed = sum(
            1 for s in self._steps.values()
            if s.status == StepStatus.COMPLETED
        )

        return {
            "total_steps": total,
            "completed_steps": completed,
            "progress_percent": (completed / total * 100) if total > 0 else 0,
            "current_step": self._current_step,
            "status": self.status.value
        }

    def to_dict(self) -> Dict[str, Any]:
        """تحويل لـ dictionary"""
        return {
            "id": self.id,
            "instance_id": self.instance_id,
            "name": self.name,
            "name_ar": self.name_ar,
            "status": self.status.value,
            "progress": self.get_progress(),
            "steps": [s.to_dict() for s in self._steps.values()],
            "history": self.history
        }


class WorkflowEngine:
    """
    محرك سير العمل

    يدير تعريف وتنفيذ سيناريوهات العمل.
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

        self._workflow_definitions: Dict[str, Callable[[], Workflow]] = {}
        self._running_workflows: Dict[str, Workflow] = {}
        self._workflow_history: List[Dict[str, Any]] = []
        self._lock = threading.RLock()

        # تسجيل السيناريوهات الافتراضية
        self._register_default_workflows()

        self._initialized = True
        app_logger.info("WorkflowEngine initialized")

    def _register_default_workflows(self):
        """تسجيل سيناريوهات العمل الافتراضية"""

        # سيناريو تسوية الإجازة
        def vacation_settlement_workflow() -> Workflow:
            wf = Workflow(
                id="vacation_settlement",
                name="Vacation Settlement",
                name_ar="تسوية الإجازة",
                description_ar="سير عمل تسوية إجازة من إيميل"
            )

            wf.add_step(
                "analyze_email",
                "Analyze Email",
                "تحليل الإيميل",
                agent_id="email_agent",
                agent_task="analyze_email"
            )

            wf.add_step(
                "detect_form",
                "Detect Form Type",
                "اكتشاف نوع النموذج",
                agent_id="form_agent",
                agent_task="detect_form_type"
            )

            wf.add_step(
                "fill_form",
                "Fill Form",
                "ملء النموذج",
                agent_id="form_agent",
                agent_task="fill_form"
            )

            wf.add_step(
                "user_approval",
                "User Approval",
                "موافقة المستخدم",
                requires_user_input=True,
                user_prompt_ar="يرجى مراجعة البيانات والموافقة"
            )

            wf.add_step(
                "save_record",
                "Save Record",
                "حفظ السجل",
                agent_id="action_agent",
                agent_task="save_record"
            )

            wf.add_step(
                "notify",
                "Send Notification",
                "إرسال إشعار",
                agent_id="action_agent",
                agent_task="send_notification"
            )

            return wf

        self.register_workflow("vacation_settlement", vacation_settlement_workflow)

        # سيناريو إنشاء مهمة من إيميل
        def email_to_task_workflow() -> Workflow:
            wf = Workflow(
                id="email_to_task",
                name="Email to Task",
                name_ar="تحويل الإيميل لمهمة",
                description_ar="سير عمل إنشاء مهمة من إيميل"
            )

            wf.add_step(
                "analyze_email",
                "Analyze Email",
                "تحليل الإيميل",
                agent_id="email_agent",
                agent_task="analyze_email"
            )

            wf.add_step(
                "create_task",
                "Create Task",
                "إنشاء المهمة",
                agent_id="task_agent",
                agent_task="create_task"
            )

            wf.add_step(
                "schedule_task",
                "Schedule Task",
                "جدولة المهمة",
                agent_id="task_agent",
                agent_task="schedule_task"
            )

            wf.add_step(
                "notify",
                "Notify User",
                "إشعار المستخدم",
                agent_id="action_agent",
                agent_task="send_notification"
            )

            return wf

        self.register_workflow("email_to_task", email_to_task_workflow)

    def register_workflow(
        self,
        workflow_id: str,
        workflow_factory: Callable[[], Workflow]
    ):
        """
        تسجيل تعريف سير عمل

        Args:
            workflow_id: معرف السير
            workflow_factory: دالة إنشاء السير
        """
        with self._lock:
            self._workflow_definitions[workflow_id] = workflow_factory
        app_logger.debug(f"Registered workflow: {workflow_id}")

    def unregister_workflow(self, workflow_id: str):
        """إلغاء تسجيل سير عمل"""
        with self._lock:
            self._workflow_definitions.pop(workflow_id, None)

    def create_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """
        إنشاء instance من سير عمل

        Args:
            workflow_id: معرف السير

        Returns:
            كائن Workflow أو None
        """
        with self._lock:
            factory = self._workflow_definitions.get(workflow_id)

        if factory:
            return factory()
        return None

    def start_workflow(
        self,
        workflow_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        بدء سير عمل

        Args:
            workflow_id: معرف السير
            context: السياق الأولي

        Returns:
            معرف النسخة أو None
        """
        workflow = self.create_workflow(workflow_id)
        if not workflow:
            app_logger.warning(f"Workflow {workflow_id} not found")
            return None

        with self._lock:
            self._running_workflows[workflow.instance_id] = workflow

        # التنفيذ في thread منفصل
        def run():
            result = workflow.execute(context)
            self._on_workflow_complete(workflow, result)

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

        return workflow.instance_id

    def _on_workflow_complete(
        self,
        workflow: Workflow,
        result: Dict[str, Any]
    ):
        """عند اكتمال سير العمل"""
        # تسجيل في التاريخ
        self._workflow_history.append({
            "workflow_id": workflow.id,
            "instance_id": workflow.instance_id,
            "status": workflow.status.value,
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "success": result.get("success", False)
        })

        # إزالة من القائمة الجارية
        with self._lock:
            self._running_workflows.pop(workflow.instance_id, None)

        app_logger.info(
            f"Workflow {workflow.id} ({workflow.instance_id}) "
            f"completed with status: {workflow.status.value}"
        )

    def get_running_workflow(self, instance_id: str) -> Optional[Workflow]:
        """جلب سير عمل جاري"""
        with self._lock:
            return self._running_workflows.get(instance_id)

    def get_all_running_workflows(self) -> List[Workflow]:
        """جلب جميع السيرات الجارية"""
        with self._lock:
            return list(self._running_workflows.values())

    def cancel_workflow(self, instance_id: str) -> bool:
        """إلغاء سير عمل"""
        workflow = self.get_running_workflow(instance_id)
        if workflow:
            workflow.cancel()
            return True
        return False

    def get_available_workflows(self) -> List[Dict[str, str]]:
        """جلب السيرات المتاحة"""
        workflows = []
        for wf_id, factory in self._workflow_definitions.items():
            wf = factory()
            workflows.append({
                "id": wf_id,
                "name": wf.name,
                "name_ar": wf.name_ar,
                "description_ar": wf.description_ar
            })
        return workflows

    def get_workflow_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """جلب تاريخ السيرات"""
        return list(reversed(self._workflow_history[-limit:]))


# ═══════════════════════════════════════════════════════════════
# Singleton & Quick Access Functions
# ═══════════════════════════════════════════════════════════════

_engine: Optional[WorkflowEngine] = None


def get_workflow_engine() -> WorkflowEngine:
    """الحصول على محرك سير العمل"""
    global _engine
    if _engine is None:
        _engine = WorkflowEngine()
    return _engine


def start_workflow(
    workflow_id: str,
    context: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """بدء سير عمل"""
    return get_workflow_engine().start_workflow(workflow_id, context)


def get_available_workflows() -> List[Dict[str, str]]:
    """جلب السيرات المتاحة"""
    return get_workflow_engine().get_available_workflows()


def register_workflow(
    workflow_id: str,
    workflow_factory: Callable[[], Workflow]
):
    """تسجيل سير عمل"""
    get_workflow_engine().register_workflow(workflow_id, workflow_factory)
