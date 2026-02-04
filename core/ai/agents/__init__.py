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
    'AlertSignals'
]
