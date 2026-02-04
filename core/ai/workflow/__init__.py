"""
INTEGRA - Workflow Engine
محرك سير العمل
المحور K

نظام تعريف وتنفيذ سيناريوهات العمل الآلية.

الاستخدام:
    from core.ai.workflow import (
        Workflow, Step, Condition,
        get_workflow_engine, start_workflow
    )

    # بدء سير عمل مسجل
    instance_id = start_workflow("vacation_settlement", context={"email": email_data})

    # أو إنشاء سير عمل مخصص
    workflow = Workflow("custom", "Custom Workflow", "سير عمل مخصص")
    workflow.add_step("step1", "Step 1", "الخطوة الأولى", handler=my_handler)
    result = workflow.execute(context={})
"""

from .workflow_engine import (
    # Enums
    StepStatus,
    WorkflowStatus,

    # Data classes
    StepResult,
    Step,
    Condition,

    # Main classes
    Workflow,
    WorkflowEngine,

    # Functions
    get_workflow_engine,
    start_workflow,
    get_available_workflows,
    register_workflow,

    # Types
    StepHandler,
    ConditionChecker
)


__all__ = [
    # Enums
    "StepStatus",
    "WorkflowStatus",

    # Data classes
    "StepResult",
    "Step",
    "Condition",

    # Main classes
    "Workflow",
    "WorkflowEngine",

    # Functions
    "get_workflow_engine",
    "start_workflow",
    "get_available_workflows",
    "register_workflow",

    # Types
    "StepHandler",
    "ConditionChecker"
]
