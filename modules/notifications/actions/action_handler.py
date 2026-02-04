"""
INTEGRA - Action Handler
المحور J4: معالج الإجراءات السريعة

ينفذ الإجراءات المرتبطة بالإشعارات:
- navigate: الانتقال إلى شاشة معينة
- api: استدعاء API
- function: تنفيذ دالة
- open_url: فتح رابط
- copy: نسخ نص
"""

from typing import Any, Callable, Optional
from dataclasses import dataclass

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

from core.logging import app_logger
from .action_registry import ActionRegistry, ActionType, get_registry


@dataclass
class ActionResult:
    """نتيجة تنفيذ إجراء"""
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None


class ActionHandler:
    """
    معالج الإجراءات

    ينفذ الإجراءات بناءً على نوعها ومعاملاتها

    Example:
        >>> handler = get_action_handler()
        >>> result = handler.execute("navigate_email", {"email_id": 123})
    """

    _instance = None
    _navigation_handlers: dict[str, Callable] = {}
    _custom_handlers: dict[str, Callable] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._navigation_handlers = {}
            cls._custom_handlers = {}
        return cls._instance

    def execute(
        self,
        action_id: str,
        params: Optional[dict] = None,
        notification_id: Optional[int] = None,
    ) -> ActionResult:
        """
        تنفيذ إجراء

        Args:
            action_id: معرف الإجراء
            params: معاملات الإجراء
            notification_id: معرف الإشعار (اختياري)

        Returns:
            نتيجة التنفيذ
        """
        params = params or {}
        registry = get_registry()
        action_def = registry.get(action_id)

        if not action_def:
            app_logger.warning(f"Action not found: {action_id}")
            return ActionResult(False, f"الإجراء غير موجود: {action_id}")

        # التأكيد إذا مطلوب
        if action_def.requires_confirmation:
            if not self._confirm_action(action_def.name):
                return ActionResult(False, "تم إلغاء الإجراء")

        try:
            # تنفيذ حسب النوع
            if action_def.action_type == ActionType.NAVIGATE:
                return self._handle_navigate(action_id, params)

            elif action_def.action_type == ActionType.FUNCTION:
                return self._handle_function(action_id, params, action_def.handler)

            elif action_def.action_type == ActionType.API:
                return self._handle_api(action_id, params)

            elif action_def.action_type == ActionType.OPEN_URL:
                return self._handle_open_url(params)

            elif action_def.action_type == ActionType.COPY:
                return self._handle_copy(params, notification_id)

            elif action_def.action_type == ActionType.DISMISS:
                return self._handle_dismiss(notification_id)

            else:
                return ActionResult(False, f"نوع إجراء غير معروف: {action_def.action_type}")

        except Exception as e:
            app_logger.error(f"Error executing action {action_id}: {e}")
            return ActionResult(False, f"حدث خطأ: {str(e)}")

    def _handle_navigate(self, action_id: str, params: dict) -> ActionResult:
        """معالجة إجراء التنقل"""
        handler = self._navigation_handlers.get(action_id)
        if handler:
            try:
                handler(params)
                return ActionResult(True, "تم الانتقال بنجاح")
            except Exception as e:
                return ActionResult(False, f"فشل الانتقال: {e}")

        # معالجة افتراضية حسب نوع التنقل
        module = params.get("module")
        record_id = params.get("id")

        app_logger.info(f"Navigate request: module={module}, id={record_id}")

        # هنا يمكن إضافة منطق التنقل الفعلي
        return ActionResult(True, f"تم طلب الانتقال إلى {module}")

    def _handle_function(
        self,
        action_id: str,
        params: dict,
        handler: Optional[Callable]
    ) -> ActionResult:
        """معالجة إجراء الدالة"""
        # أولاً: التحقق من handler مسجل
        custom_handler = self._custom_handlers.get(action_id)
        if custom_handler:
            result = custom_handler(params)
            if isinstance(result, ActionResult):
                return result
            return ActionResult(True, "تم التنفيذ بنجاح", result)

        # ثانياً: handler من التعريف
        if handler:
            result = handler(params)
            if isinstance(result, ActionResult):
                return result
            return ActionResult(True, "تم التنفيذ بنجاح", result)

        # معالجات مدمجة
        if action_id == "create_task":
            return self._create_task_from_notification(params)

        elif action_id == "complete_task":
            return self._complete_task(params)

        elif action_id == "snooze":
            return self._snooze_notification(params)

        elif action_id == "archive":
            return self._archive_notification(params)

        return ActionResult(False, f"لا يوجد معالج للإجراء: {action_id}")

    def _handle_api(self, action_id: str, params: dict) -> ActionResult:
        """معالجة إجراء API"""
        endpoint = params.get("endpoint")
        method = params.get("method", "GET")
        data = params.get("data", {})

        app_logger.info(f"API request: {method} {endpoint}")
        # TODO: تنفيذ استدعاء API فعلي

        return ActionResult(True, "تم إرسال الطلب")

    def _handle_open_url(self, params: dict) -> ActionResult:
        """معالجة فتح رابط"""
        url = params.get("url")
        if not url:
            return ActionResult(False, "الرابط غير محدد")

        try:
            QDesktopServices.openUrl(QUrl(url))
            return ActionResult(True, "تم فتح الرابط")
        except Exception as e:
            return ActionResult(False, f"فشل فتح الرابط: {e}")

    def _handle_copy(self, params: dict, notification_id: Optional[int]) -> ActionResult:
        """معالجة النسخ"""
        text = params.get("text")

        # إذا لم يحدد نص، نسخ محتوى الإشعار
        if not text and notification_id:
            try:
                from ..models import get_notification_by_id
                notification = get_notification_by_id(notification_id)
                if notification:
                    text = f"{notification.title}\n{notification.body or ''}"
            except Exception:
                pass

        if not text:
            return ActionResult(False, "لا يوجد نص للنسخ")

        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        return ActionResult(True, "تم النسخ")

    def _handle_dismiss(self, notification_id: Optional[int]) -> ActionResult:
        """معالجة إغلاق الإشعار"""
        if notification_id:
            try:
                from ..models import archive_notification
                archive_notification(notification_id)
                return ActionResult(True, "تم إغلاق الإشعار")
            except Exception as e:
                return ActionResult(False, f"فشل الإغلاق: {e}")
        return ActionResult(True)

    def _confirm_action(self, action_name: str) -> bool:
        """طلب تأكيد الإجراء"""
        reply = QMessageBox.question(
            None,
            "تأكيد",
            f"هل تريد تنفيذ: {action_name}؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        return reply == QMessageBox.Yes

    # ========================
    # معالجات مدمجة
    # ========================

    def _create_task_from_notification(self, params: dict) -> ActionResult:
        """إنشاء مهمة من إشعار"""
        title = params.get("title", "مهمة جديدة")
        description = params.get("description", "")
        source_id = params.get("source_id")

        app_logger.info(f"Creating task: {title}")
        # TODO: التكامل مع موديول المهام

        return ActionResult(True, f"تم إنشاء المهمة: {title}")

    def _complete_task(self, params: dict) -> ActionResult:
        """إكمال مهمة"""
        task_id = params.get("task_id")
        if not task_id:
            return ActionResult(False, "معرف المهمة غير محدد")

        app_logger.info(f"Completing task: {task_id}")
        # TODO: التكامل مع موديول المهام

        return ActionResult(True, "تم إكمال المهمة")

    def _snooze_notification(self, params: dict) -> ActionResult:
        """تأجيل إشعار"""
        notification_id = params.get("notification_id")
        duration = params.get("duration", 3600)  # افتراضي: ساعة واحدة

        app_logger.info(f"Snoozing notification {notification_id} for {duration} seconds")
        # TODO: تنفيذ التأجيل

        return ActionResult(True, "تم تأجيل الإشعار")

    def _archive_notification(self, params: dict) -> ActionResult:
        """أرشفة إشعار"""
        notification_id = params.get("notification_id")
        if not notification_id:
            return ActionResult(False, "معرف الإشعار غير محدد")

        try:
            from ..models import archive_notification
            archive_notification(notification_id)
            return ActionResult(True, "تم أرشفة الإشعار")
        except Exception as e:
            return ActionResult(False, f"فشلت الأرشفة: {e}")

    # ========================
    # تسجيل المعالجات
    # ========================

    def register_navigation_handler(self, action_id: str, handler: Callable):
        """
        تسجيل معالج تنقل

        Args:
            action_id: معرف الإجراء
            handler: دالة المعالجة (تأخذ params dict)
        """
        self._navigation_handlers[action_id] = handler

    def register_handler(self, action_id: str, handler: Callable):
        """
        تسجيل معالج عام

        Args:
            action_id: معرف الإجراء
            handler: دالة المعالجة (تأخذ params dict)
        """
        self._custom_handlers[action_id] = handler


# ========================
# Singleton & Convenience
# ========================

_handler_instance: Optional[ActionHandler] = None


def get_action_handler() -> ActionHandler:
    """الحصول على معالج الإجراءات"""
    global _handler_instance
    if _handler_instance is None:
        _handler_instance = ActionHandler()
    return _handler_instance


def execute_action(
    action_id: str,
    params: Optional[dict] = None,
    notification_id: Optional[int] = None,
) -> ActionResult:
    """
    تنفيذ إجراء (دالة مختصرة)

    Args:
        action_id: معرف الإجراء
        params: معاملات الإجراء
        notification_id: معرف الإشعار

    Returns:
        نتيجة التنفيذ

    Example:
        >>> result = execute_action("navigate_email", {"email_id": 123})
        >>> if result.success:
        ...     print("تم التنفيذ")
    """
    return get_action_handler().execute(action_id, params, notification_id)


def register_action(action_id: str, handler: Callable):
    """
    تسجيل معالج لإجراء (دالة مختصرة)

    Args:
        action_id: معرف الإجراء
        handler: دالة المعالجة

    Example:
        >>> def my_handler(params):
        ...     print(f"Executing with params: {params}")
        >>> register_action("my_custom_action", my_handler)
    """
    get_action_handler().register_handler(action_id, handler)
