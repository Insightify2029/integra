"""
INTEGRA - Notifications Module
المحور J: نظام الإشعارات الذكي

مركز إشعارات موحد يربط كل الموديولات

الاستخدام:
    >>> from modules.notifications import (
    ...     notify, get_notifications, get_unread_count,
    ...     NotificationType, NotificationPriority,
    ... )
    >>>
    >>> # إنشاء إشعار
    >>> notify("إيميل جديد", "وصل إيميل من HR", NotificationType.EMAIL)
    >>>
    >>> # جلب الإشعارات
    >>> notifications = get_notifications(limit=10)
    >>>
    >>> # عدد غير المقروءة
    >>> count = get_unread_count()
"""

# Models
from .models.notification_models import (
    Notification,
    NotificationType,
    NotificationPriority,
    NotificationAction,
    NotificationSettings,
    create_notification,
    get_notifications,
    get_unread_count,
    mark_as_read,
    mark_all_as_read,
    archive_notification,
    delete_notification,
    get_notification_by_id,
    notify,
)

# Widgets
from .widgets.notification_bell import NotificationBell, create_notification_bell
from .widgets.notification_popup import NotificationPopup
from .widgets.notification_card import NotificationCard

# Screens
from .screens.notification_center import NotificationCenterScreen

# Actions
from .actions.action_handler import (
    ActionHandler,
    get_action_handler,
    execute_action,
    register_action,
)
from .actions.action_registry import ActionRegistry, ActionType, ActionDefinition

# AI
from .ai.priority_detector import (
    PriorityDetector,
    PriorityAnalysis,
    NotificationCategory,
    get_priority_detector,
    detect_priority,
    analyze_notification,
)

# Desktop
from .desktop.desktop_notifier import (
    DesktopNotifier,
    get_desktop_notifier,
    send_desktop_notification,
    is_desktop_notifications_available,
)

__all__ = [
    # Models
    "Notification",
    "NotificationType",
    "NotificationPriority",
    "NotificationAction",
    "NotificationSettings",
    # Model Functions
    "create_notification",
    "get_notifications",
    "get_unread_count",
    "mark_as_read",
    "mark_all_as_read",
    "archive_notification",
    "delete_notification",
    "get_notification_by_id",
    "notify",
    # Widgets
    "NotificationBell",
    "create_notification_bell",
    "NotificationPopup",
    "NotificationCard",
    # Screens
    "NotificationCenterScreen",
    # Actions
    "ActionHandler",
    "get_action_handler",
    "execute_action",
    "register_action",
    "ActionRegistry",
    "ActionType",
    "ActionDefinition",
    # AI
    "PriorityDetector",
    "PriorityAnalysis",
    "NotificationCategory",
    "get_priority_detector",
    "detect_priority",
    "analyze_notification",
    # Desktop
    "DesktopNotifier",
    "get_desktop_notifier",
    "send_desktop_notification",
    "is_desktop_notifications_available",
]
