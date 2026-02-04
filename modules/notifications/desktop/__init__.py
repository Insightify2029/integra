"""
Desktop Notifications
"""

from .desktop_notifier import (
    DesktopNotifier,
    get_desktop_notifier,
    send_desktop_notification,
    is_desktop_notifications_available,
)

__all__ = [
    "DesktopNotifier",
    "get_desktop_notifier",
    "send_desktop_notification",
    "is_desktop_notifications_available",
]
