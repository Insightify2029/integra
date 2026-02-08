"""
INTEGRA - Advanced AI-Powered Email Module (Track G)
=====================================================
تحويل موديول الإيميل إلى مساعد ذكي متكامل.

Components:
- G1: AI Email Assistant (email_assistant.py)
- G2: Smart Notifications (smart_notifications.py)
- G3: Email Compose AI (compose_ai.py)
- G4: Email Search & Analytics (search_analytics.py)
- G5: Auto-Actions (auto_actions.py)
- G6: Employee Integration (employee_integration.py)
"""

from .email_assistant import (
    EmailAssistant,
    get_email_assistant,
    DetailedEmailAnalysis,
    EmailClassification,
)

from .smart_notifications import (
    EmailNotificationManager,
    get_email_notification_manager,
)

from .compose_ai import (
    ComposeAI,
    get_compose_ai,
    ReplyTone,
)

from .search_analytics import (
    EmailSearchEngine,
    get_email_search_engine,
    EmailAnalytics,
    get_email_analytics,
)

from .auto_actions import (
    AutoActionEngine,
    get_auto_action_engine,
    EmailRule,
    RuleCondition,
    RuleAction,
)

from .employee_integration import (
    EmployeeEmailLinker,
    get_employee_email_linker,
)

__all__ = [
    # G1
    'EmailAssistant', 'get_email_assistant',
    'DetailedEmailAnalysis', 'EmailClassification',
    # G2
    'EmailNotificationManager', 'get_email_notification_manager',
    # G3
    'ComposeAI', 'get_compose_ai', 'ReplyTone',
    # G4
    'EmailSearchEngine', 'get_email_search_engine',
    'EmailAnalytics', 'get_email_analytics',
    # G5
    'AutoActionEngine', 'get_auto_action_engine',
    'EmailRule', 'RuleCondition', 'RuleAction',
    # G6
    'EmployeeEmailLinker', 'get_employee_email_linker',
]
