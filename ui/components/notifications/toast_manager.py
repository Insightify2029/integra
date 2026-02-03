"""
Toast Manager
=============
Modern toast notification system for INTEGRA.
Uses pyqt-toast-notification for non-blocking notifications.

Usage:
    from ui.components.notifications import toast_success, toast_error

    # Simple usage
    toast_success(parent, "تم الحفظ", "تم حفظ بيانات الموظف بنجاح")
    toast_error(parent, "خطأ", "فشل الاتصال بقاعدة البيانات")

    # Or use the manager directly
    from ui.components.notifications import get_toast_manager
    manager = get_toast_manager()
    manager.show_success(parent, "تم", "العملية تمت بنجاح")
"""

from typing import Optional
from PyQt5.QtWidgets import QWidget

try:
    from pyqttoast import Toast, ToastPreset, ToastPosition
    TOAST_AVAILABLE = True
except ImportError:
    TOAST_AVAILABLE = False

from core.logging import app_logger


# Default configuration
DEFAULT_DURATION = 3000  # 3 seconds
DEFAULT_POSITION = ToastPosition.BOTTOM_RIGHT if TOAST_AVAILABLE else None


class ToastManager:
    """
    Centralized toast notification manager.
    Provides consistent notification styling across the application.
    """

    _instance: Optional['ToastManager'] = None

    def __init__(self):
        self.duration = DEFAULT_DURATION
        self.position = DEFAULT_POSITION
        self._enabled = TOAST_AVAILABLE

        if not TOAST_AVAILABLE:
            app_logger.warning("pyqttoast not available. Toast notifications disabled.")

    @classmethod
    def instance(cls) -> 'ToastManager':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def is_available(self) -> bool:
        """Check if toast notifications are available."""
        return self._enabled

    def set_duration(self, duration_ms: int):
        """Set default duration for toasts."""
        self.duration = duration_ms

    def set_position(self, position):
        """Set default position for toasts."""
        if TOAST_AVAILABLE:
            self.position = position

    def show_success(self, parent: QWidget, title: str, message: str,
                     duration: Optional[int] = None):
        """Show success toast notification."""
        self._show_toast(parent, title, message, ToastPreset.SUCCESS, duration)

    def show_error(self, parent: QWidget, title: str, message: str,
                   duration: Optional[int] = None):
        """Show error toast notification."""
        # Errors stay longer by default
        duration = duration or self.duration + 2000
        self._show_toast(parent, title, message, ToastPreset.ERROR, duration)

    def show_warning(self, parent: QWidget, title: str, message: str,
                     duration: Optional[int] = None):
        """Show warning toast notification."""
        self._show_toast(parent, title, message, ToastPreset.WARNING, duration)

    def show_info(self, parent: QWidget, title: str, message: str,
                  duration: Optional[int] = None):
        """Show info toast notification."""
        self._show_toast(parent, title, message, ToastPreset.INFORMATION, duration)

    def _show_toast(self, parent: QWidget, title: str, message: str,
                    preset, duration: Optional[int] = None):
        """Internal method to show toast."""
        if not self._enabled:
            # Fallback to logging
            app_logger.info(f"Toast [{preset}]: {title} - {message}")
            return

        try:
            toast = Toast(parent)
            toast.setDuration(duration or self.duration)
            toast.setTitle(title)
            toast.setText(message)
            toast.applyPreset(preset)

            if self.position:
                toast.setPosition(self.position)

            # RTL support for Arabic
            toast.setTitleFont(toast.getTitleFont())  # Keep default font
            toast.setTextFont(toast.getTextFont())

            toast.show()

        except Exception as e:
            app_logger.error(f"Failed to show toast: {e}")


# Singleton accessor
def get_toast_manager() -> ToastManager:
    """Get the global toast manager instance."""
    return ToastManager.instance()


# Convenience functions for quick access
def toast_success(parent: QWidget, title: str, message: str,
                  duration: Optional[int] = None):
    """
    Show success toast notification.

    Args:
        parent: Parent widget
        title: Toast title (e.g., "تم الحفظ")
        message: Toast message
        duration: Duration in ms (default: 3000)

    Example:
        toast_success(self, "تم", "تم حفظ البيانات بنجاح")
    """
    get_toast_manager().show_success(parent, title, message, duration)


def toast_error(parent: QWidget, title: str, message: str,
                duration: Optional[int] = None):
    """
    Show error toast notification.

    Args:
        parent: Parent widget
        title: Toast title (e.g., "خطأ")
        message: Toast message
        duration: Duration in ms (default: 5000)

    Example:
        toast_error(self, "خطأ", "فشل الاتصال بقاعدة البيانات")
    """
    get_toast_manager().show_error(parent, title, message, duration)


def toast_warning(parent: QWidget, title: str, message: str,
                  duration: Optional[int] = None):
    """
    Show warning toast notification.

    Args:
        parent: Parent widget
        title: Toast title (e.g., "تحذير")
        message: Toast message
        duration: Duration in ms (default: 3000)

    Example:
        toast_warning(self, "تحذير", "بيانات غير مكتملة")
    """
    get_toast_manager().show_warning(parent, title, message, duration)


def toast_info(parent: QWidget, title: str, message: str,
               duration: Optional[int] = None):
    """
    Show info toast notification.

    Args:
        parent: Parent widget
        title: Toast title (e.g., "معلومة")
        message: Toast message
        duration: Duration in ms (default: 3000)

    Example:
        toast_info(self, "معلومة", "يتم تحميل البيانات...")
    """
    get_toast_manager().show_info(parent, title, message, duration)
