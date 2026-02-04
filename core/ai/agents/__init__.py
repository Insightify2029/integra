"""
AI Agents
=========
Specialized agents for different tasks.
"""

from .data_agent import (
    DataAgent,
    get_data_agent,
    analyze_employees,
    analyze_salaries,
    find_anomalies,
    generate_insights
)

from .email_agent import (
    EmailAgent,
    get_email_agent,
    analyze_email,
    summarize_email,
    extract_email_tasks,
    suggest_email_reply,
    EmailAnalysis,
    EmailCategory,
    EmailPriorityAI
)

from .alert_agent import (
    AlertAgent,
    get_alert_agent,
    check_all_alerts,
    get_critical_alerts,
    get_alert_summary,
    create_custom_alert,
    Alert,
    AlertPriority,
    AlertCategory,
    AlertSummary,
    AlertSignals
)

from .task_agent import (
    TaskAgent,
    get_task_agent,
    analyze_task,
    get_task_suggestions,
    detect_overdue_risks,
    suggest_task_order,
    TaskAnalysis,
    TaskSuggestion
)

from .calendar_agent import (
    CalendarAgent,
    get_calendar_agent,
    suggest_best_time,
    check_calendar_conflicts,
    analyze_work_patterns,
    suggest_break_times,
    TimeSlotSuggestion,
    ConflictAnalysis,
    WorkPatternAnalysis,
    ConflictSeverity
)

# Track K - AI Orchestration Agents
from .form_agent import (
    FormAgent,
    get_form_agent,
    detect_form_type,
    fill_form,
    extract_form_data,
    validate_form,
    register_form_agent,
    FormType,
    FormField,
    FormDetectionResult,
    FormFillingResult
)

from .action_agent import (
    ActionAgent,
    get_action_agent,
    execute_action,
    approve_action,
    reject_action,
    get_pending_actions,
    register_action_handler,
    register_action_agent,
    ActionType,
    ActionLevel,
    ActionStatus,
    Action,
    ActionResult
)

from .learning_agent import (
    LearningAgent,
    get_learning_agent,
    learn_preference,
    get_preference,
    record_feedback,
    get_preferred_value,
    register_learning_agent,
    UserPreference,
    UserPattern,
    Feedback,
    LearningInsight
)

__all__ = [
    # Data Agent
    'DataAgent',
    'get_data_agent',
    'analyze_employees',
    'analyze_salaries',
    'find_anomalies',
    'generate_insights',
    # Email Agent
    'EmailAgent',
    'get_email_agent',
    'analyze_email',
    'summarize_email',
    'extract_email_tasks',
    'suggest_email_reply',
    'EmailAnalysis',
    'EmailCategory',
    'EmailPriorityAI',
    # Alert Agent
    'AlertAgent',
    'get_alert_agent',
    'check_all_alerts',
    'get_critical_alerts',
    'get_alert_summary',
    'create_custom_alert',
    'Alert',
    'AlertPriority',
    'AlertCategory',
    'AlertSummary',
    'AlertSignals',
    # Task Agent
    'TaskAgent',
    'get_task_agent',
    'analyze_task',
    'get_task_suggestions',
    'detect_overdue_risks',
    'suggest_task_order',
    'TaskAnalysis',
    'TaskSuggestion',
    # Calendar Agent
    'CalendarAgent',
    'get_calendar_agent',
    'suggest_best_time',
    'check_calendar_conflicts',
    'analyze_work_patterns',
    'suggest_break_times',
    'TimeSlotSuggestion',
    'ConflictAnalysis',
    'WorkPatternAnalysis',
    'ConflictSeverity',
    # Form Agent (Track K)
    'FormAgent',
    'get_form_agent',
    'detect_form_type',
    'fill_form',
    'extract_form_data',
    'validate_form',
    'register_form_agent',
    'FormType',
    'FormField',
    'FormDetectionResult',
    'FormFillingResult',
    # Action Agent (Track K)
    'ActionAgent',
    'get_action_agent',
    'execute_action',
    'approve_action',
    'reject_action',
    'get_pending_actions',
    'register_action_handler',
    'register_action_agent',
    'ActionType',
    'ActionLevel',
    'ActionStatus',
    'Action',
    'ActionResult',
    # Learning Agent (Track K)
    'LearningAgent',
    'get_learning_agent',
    'learn_preference',
    'get_preference',
    'record_feedback',
    'get_preferred_value',
    'register_learning_agent',
    'UserPreference',
    'UserPattern',
    'Feedback',
    'LearningInsight'
]
