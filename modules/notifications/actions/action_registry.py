"""
INTEGRA - Action Registry
المحور J4: سجل الإجراءات

يحتفظ بقائمة الإجراءات المتاحة وكيفية تنفيذها
"""

from dataclasses import dataclass
from typing import Callable, Optional, Any
from enum import Enum

from core.logging import app_logger


class ActionType(Enum):
    """أنواع الإجراءات"""
    NAVIGATE = "navigate"     # الانتقال إلى شاشة
    API = "api"               # استدعاء API
    FUNCTION = "function"     # تنفيذ دالة
    OPEN_URL = "open_url"     # فتح رابط
    COPY = "copy"             # نسخ نص
    DISMISS = "dismiss"       # إغلاق الإشعار


@dataclass
class ActionDefinition:
    """تعريف إجراء"""
    id: str                                      # معرف فريد
    name: str                                    # الاسم
    action_type: ActionType                      # النوع
    handler: Optional[Callable] = None           # الدالة المنفذة
    description: Optional[str] = None            # الوصف
    icon: Optional[str] = None                   # الأيقونة
    requires_confirmation: bool = False          # يحتاج تأكيد


class ActionRegistry:
    """
    سجل الإجراءات

    Singleton يحتفظ بكل الإجراءات المسجلة
    """

    _instance = None
    _actions: dict[str, ActionDefinition] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._actions = {}
            cls._instance._register_default_actions()
        return cls._instance

    def _register_default_actions(self):
        """تسجيل الإجراءات الافتراضية"""

        # إجراءات التنقل
        self.register(ActionDefinition(
            id="navigate_email",
            name="فتح الإيميل",
            action_type=ActionType.NAVIGATE,
            icon="fa5s.envelope",
            description="الانتقال إلى شاشة الإيميل",
        ))

        self.register(ActionDefinition(
            id="navigate_task",
            name="فتح المهمة",
            action_type=ActionType.NAVIGATE,
            icon="fa5s.tasks",
            description="الانتقال إلى شاشة المهام",
        ))

        self.register(ActionDefinition(
            id="navigate_employee",
            name="فتح ملف الموظف",
            action_type=ActionType.NAVIGATE,
            icon="fa5s.user",
            description="الانتقال إلى ملف الموظف",
        ))

        self.register(ActionDefinition(
            id="navigate_calendar",
            name="فتح التقويم",
            action_type=ActionType.NAVIGATE,
            icon="fa5s.calendar-alt",
            description="الانتقال إلى التقويم",
        ))

        # إجراءات الإيميل
        self.register(ActionDefinition(
            id="reply_email",
            name="رد على الإيميل",
            action_type=ActionType.FUNCTION,
            icon="fa5s.reply",
            description="فتح نافذة الرد على الإيميل",
        ))

        self.register(ActionDefinition(
            id="forward_email",
            name="إعادة توجيه",
            action_type=ActionType.FUNCTION,
            icon="fa5s.share",
            description="إعادة توجيه الإيميل",
        ))

        # إجراءات المهام
        self.register(ActionDefinition(
            id="create_task",
            name="إنشاء مهمة",
            action_type=ActionType.FUNCTION,
            icon="fa5s.plus",
            description="إنشاء مهمة جديدة من الإشعار",
        ))

        self.register(ActionDefinition(
            id="complete_task",
            name="إكمال المهمة",
            action_type=ActionType.FUNCTION,
            icon="fa5s.check",
            description="تحديد المهمة كمكتملة",
            requires_confirmation=True,
        ))

        # إجراءات عامة
        self.register(ActionDefinition(
            id="dismiss",
            name="إغلاق",
            action_type=ActionType.DISMISS,
            icon="fa5s.times",
            description="إغلاق الإشعار",
        ))

        self.register(ActionDefinition(
            id="snooze",
            name="تأجيل",
            action_type=ActionType.FUNCTION,
            icon="fa5s.clock",
            description="تأجيل الإشعار",
        ))

        self.register(ActionDefinition(
            id="archive",
            name="أرشفة",
            action_type=ActionType.FUNCTION,
            icon="fa5s.archive",
            description="أرشفة الإشعار",
        ))

        self.register(ActionDefinition(
            id="copy_content",
            name="نسخ المحتوى",
            action_type=ActionType.COPY,
            icon="fa5s.copy",
            description="نسخ محتوى الإشعار",
        ))

        app_logger.debug(f"Registered {len(self._actions)} default actions")

    def register(self, action: ActionDefinition):
        """
        تسجيل إجراء جديد

        Args:
            action: تعريف الإجراء
        """
        self._actions[action.id] = action
        app_logger.debug(f"Registered action: {action.id}")

    def unregister(self, action_id: str):
        """
        إلغاء تسجيل إجراء

        Args:
            action_id: معرف الإجراء
        """
        if action_id in self._actions:
            del self._actions[action_id]

    def get(self, action_id: str) -> Optional[ActionDefinition]:
        """
        الحصول على تعريف إجراء

        Args:
            action_id: معرف الإجراء

        Returns:
            تعريف الإجراء أو None
        """
        return self._actions.get(action_id)

    def get_all(self) -> list[ActionDefinition]:
        """
        الحصول على كل الإجراءات المسجلة

        Returns:
            قائمة الإجراءات
        """
        return list(self._actions.values())

    def get_by_type(self, action_type: ActionType) -> list[ActionDefinition]:
        """
        الحصول على الإجراءات حسب النوع

        Args:
            action_type: نوع الإجراء

        Returns:
            قائمة الإجراءات
        """
        return [a for a in self._actions.values() if a.action_type == action_type]

    def set_handler(self, action_id: str, handler: Callable):
        """
        تعيين دالة معالجة لإجراء

        Args:
            action_id: معرف الإجراء
            handler: الدالة المعالجة
        """
        if action_id in self._actions:
            self._actions[action_id].handler = handler
        else:
            app_logger.warning(f"Action {action_id} not found in registry")


def get_registry() -> ActionRegistry:
    """الحصول على سجل الإجراءات"""
    return ActionRegistry()
