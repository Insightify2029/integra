"""
INTEGRA - Desktop Notifier
المحور J6: إشعارات سطح المكتب

يرسل إشعارات Windows native:
- Windows 10/11 Toast Notifications
- صوت تنبيه قابل للتخصيص
- دعم وضع التركيز (Do Not Disturb)
"""

import sys
import threading
from dataclasses import dataclass
from typing import Optional, Callable
from enum import Enum

from core.logging import app_logger


class NotificationSound(Enum):
    """أصوات الإشعارات"""
    DEFAULT = "default"
    NONE = "none"
    MAIL = "mail"
    REMINDER = "reminder"
    SMS = "sms"


@dataclass
class DesktopNotificationConfig:
    """إعدادات الإشعارات"""
    enabled: bool = True
    sound_enabled: bool = True
    sound_type: NotificationSound = NotificationSound.DEFAULT
    duration_seconds: int = 5
    focus_mode: bool = False
    allow_urgent_in_focus: bool = True


class DesktopNotifier:
    """
    مرسل إشعارات سطح المكتب

    يدعم:
    - Windows 10/11 Toast Notifications
    - Fallback إلى PyQt5 QSystemTrayIcon
    """

    _instance = None
    _backend = None
    _config: DesktopNotificationConfig = None
    _on_click_callback: Optional[Callable] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._config = DesktopNotificationConfig()
            cls._instance._detect_backend()
        return cls._instance

    def _detect_backend(self):
        """اكتشاف الطريقة المتاحة للإشعارات"""
        if sys.platform == "win32":
            # محاولة استخدام win10toast
            try:
                from win10toast import ToastNotifier
                self._backend = "win10toast"
                self._toaster = ToastNotifier()
                app_logger.debug("Using win10toast for desktop notifications")
                return
            except ImportError:
                pass

            # محاولة استخدام windows-toasts
            try:
                from windows_toasts import Toast, ToastDisplayImage, WindowsToaster
                self._backend = "windows_toasts"
                app_logger.debug("Using windows-toasts for desktop notifications")
                return
            except ImportError:
                pass

            # محاولة استخدام plyer
            try:
                from plyer import notification as plyer_notification
                self._backend = "plyer"
                app_logger.debug("Using plyer for desktop notifications")
                return
            except ImportError:
                pass

        # Fallback إلى PyQt5
        try:
            from PyQt5.QtWidgets import QSystemTrayIcon
            self._backend = "pyqt5"
            app_logger.debug("Using PyQt5 QSystemTrayIcon for notifications")
        except ImportError:
            self._backend = None
            app_logger.warning("No desktop notification backend available")

    @property
    def is_available(self) -> bool:
        """هل الإشعارات متاحة"""
        return self._backend is not None

    @property
    def config(self) -> DesktopNotificationConfig:
        """الحصول على الإعدادات"""
        return self._config

    def configure(self, **kwargs):
        """
        تكوين الإعدادات

        Args:
            enabled: تفعيل/تعطيل
            sound_enabled: تفعيل الصوت
            sound_type: نوع الصوت
            duration_seconds: مدة العرض
            focus_mode: وضع التركيز
            allow_urgent_in_focus: السماح للعاجل في وضع التركيز
        """
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)

    def set_on_click(self, callback: Callable[[int], None]):
        """
        تعيين callback عند النقر على الإشعار

        Args:
            callback: دالة تأخذ notification_id
        """
        self._on_click_callback = callback

    def send(
        self,
        title: str,
        message: str,
        notification_id: Optional[int] = None,
        icon_path: Optional[str] = None,
        is_urgent: bool = False,
        duration: Optional[int] = None,
        on_click: Optional[Callable] = None,
    ) -> bool:
        """
        إرسال إشعار

        Args:
            title: عنوان الإشعار
            message: محتوى الإشعار
            notification_id: معرف الإشعار
            icon_path: مسار الأيقونة
            is_urgent: هل عاجل
            duration: مدة العرض بالثواني
            on_click: دالة عند النقر

        Returns:
            نجاح الإرسال
        """
        # التحقق من الإعدادات
        if not self._config.enabled:
            return False

        if not self.is_available:
            app_logger.warning("Desktop notifications not available")
            return False

        # التحقق من وضع التركيز
        if self._config.focus_mode:
            if not is_urgent or not self._config.allow_urgent_in_focus:
                app_logger.debug("Notification blocked by focus mode")
                return False

        duration = duration or self._config.duration_seconds

        try:
            if self._backend == "win10toast":
                return self._send_win10toast(title, message, icon_path, duration, on_click)
            elif self._backend == "windows_toasts":
                return self._send_windows_toasts(title, message, icon_path, duration)
            elif self._backend == "plyer":
                return self._send_plyer(title, message, icon_path, duration)
            elif self._backend == "pyqt5":
                return self._send_pyqt5(title, message, duration)
            else:
                return False
        except Exception as e:
            app_logger.error(f"Error sending desktop notification: {e}")
            return False

    def _send_win10toast(
        self,
        title: str,
        message: str,
        icon_path: Optional[str],
        duration: int,
        on_click: Optional[Callable],
    ) -> bool:
        """إرسال عبر win10toast"""
        def send_threaded():
            try:
                self._toaster.show_toast(
                    title=title,
                    msg=message,
                    icon_path=icon_path,
                    duration=duration,
                    threaded=False,
                    callback_on_click=on_click or self._on_click_callback,
                )
            except Exception as e:
                app_logger.error(f"win10toast error: {e}")

        # تشغيل في thread منفصل لتجنب blocking
        thread = threading.Thread(target=send_threaded, daemon=True)
        thread.start()
        return True

    def _send_windows_toasts(
        self,
        title: str,
        message: str,
        icon_path: Optional[str],
        duration: int,
    ) -> bool:
        """إرسال عبر windows-toasts"""
        try:
            from windows_toasts import Toast, WindowsToaster

            toaster = WindowsToaster("INTEGRA")
            toast = Toast()
            toast.text_fields = [title, message]

            if icon_path:
                from windows_toasts import ToastDisplayImage
                toast.AddImage(ToastDisplayImage.fromPath(icon_path))

            toaster.show_toast(toast)
            return True
        except Exception as e:
            app_logger.error(f"windows-toasts error: {e}")
            return False

    def _send_plyer(
        self,
        title: str,
        message: str,
        icon_path: Optional[str],
        duration: int,
    ) -> bool:
        """إرسال عبر plyer"""
        try:
            from plyer import notification as plyer_notification

            plyer_notification.notify(
                title=title,
                message=message,
                app_name="INTEGRA",
                app_icon=icon_path,
                timeout=duration,
            )
            return True
        except Exception as e:
            app_logger.error(f"plyer error: {e}")
            return False

    def _send_pyqt5(
        self,
        title: str,
        message: str,
        duration: int,
    ) -> bool:
        """إرسال عبر PyQt5 QSystemTrayIcon"""
        try:
            from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu
            from PyQt5.QtGui import QIcon

            app = QApplication.instance()
            if not app:
                return False

            # البحث عن أو إنشاء system tray icon
            for widget in app.allWidgets():
                if isinstance(widget, QSystemTrayIcon):
                    widget.showMessage(
                        title,
                        message,
                        QSystemTrayIcon.Information,
                        duration * 1000,
                    )
                    return True

            # إنشاء tray icon مؤقت
            tray = QSystemTrayIcon()
            tray.setIcon(app.style().standardIcon(app.style().SP_MessageBoxInformation))
            tray.setVisible(True)
            tray.showMessage(title, message, QSystemTrayIcon.Information, duration * 1000)

            # حذف بعد الانتهاء
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(duration * 1000 + 1000, tray.deleteLater)

            return True
        except Exception as e:
            app_logger.error(f"PyQt5 notification error: {e}")
            return False

    def play_sound(self, sound_type: Optional[NotificationSound] = None):
        """
        تشغيل صوت إشعار

        Args:
            sound_type: نوع الصوت
        """
        if not self._config.sound_enabled:
            return

        sound_type = sound_type or self._config.sound_type

        if sound_type == NotificationSound.NONE:
            return

        try:
            if sys.platform == "win32":
                import winsound
                if sound_type == NotificationSound.MAIL:
                    winsound.PlaySound("SystemNotification", winsound.SND_ALIAS)
                else:
                    winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
        except Exception as e:
            app_logger.debug(f"Could not play notification sound: {e}")


# ========================
# Singleton & Convenience
# ========================

_notifier_instance: Optional[DesktopNotifier] = None


def get_desktop_notifier() -> DesktopNotifier:
    """الحصول على مرسل الإشعارات"""
    global _notifier_instance
    if _notifier_instance is None:
        _notifier_instance = DesktopNotifier()
    return _notifier_instance


def is_desktop_notifications_available() -> bool:
    """هل إشعارات سطح المكتب متاحة"""
    return get_desktop_notifier().is_available


def send_desktop_notification(
    title: str,
    message: str,
    notification_id: Optional[int] = None,
    is_urgent: bool = False,
) -> bool:
    """
    إرسال إشعار سطح مكتب (دالة مختصرة)

    Args:
        title: العنوان
        message: المحتوى
        notification_id: معرف الإشعار
        is_urgent: هل عاجل

    Returns:
        نجاح الإرسال

    Example:
        >>> send_desktop_notification("إيميل جديد", "وصل إيميل من HR")
        >>> send_desktop_notification("تنبيه عاجل!", "اجتماع الآن", is_urgent=True)
    """
    notifier = get_desktop_notifier()
    return notifier.send(
        title=title,
        message=message,
        notification_id=notification_id,
        is_urgent=is_urgent,
    )
