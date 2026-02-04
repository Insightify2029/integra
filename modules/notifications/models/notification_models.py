"""
INTEGRA - Notification Models
المحور J1: نماذج البيانات للإشعارات

يوفر:
- Notification: نموذج الإشعار
- NotificationType: أنواع الإشعارات
- NotificationPriority: أولويات الإشعارات
- NotificationAction: إجراءات الإشعار
- CRUD operations: إنشاء، قراءة، تحديث، حذف
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import json

from core.logging import app_logger


class NotificationType(Enum):
    """أنواع الإشعارات"""
    EMAIL = "email"           # إشعار من الإيميل
    TASK = "task"             # إشعار من المهام
    CALENDAR = "calendar"     # إشعار من التقويم
    SYSTEM = "system"         # إشعار نظام
    AI = "ai"                 # إشعار من الذكاء الاصطناعي
    ALERT = "alert"           # تنبيه مهم

    @property
    def icon(self) -> str:
        """أيقونة النوع"""
        icons = {
            "email": "fa5s.envelope",
            "task": "fa5s.tasks",
            "calendar": "fa5s.calendar-alt",
            "system": "fa5s.cog",
            "ai": "fa5s.robot",
            "alert": "fa5s.exclamation-triangle",
        }
        return icons.get(self.value, "fa5s.bell")

    @property
    def color(self) -> str:
        """لون النوع"""
        colors = {
            "email": "#3498db",     # أزرق
            "task": "#2ecc71",      # أخضر
            "calendar": "#9b59b6",  # بنفسجي
            "system": "#95a5a6",    # رمادي
            "ai": "#f39c12",        # برتقالي
            "alert": "#e74c3c",     # أحمر
        }
        return colors.get(self.value, "#3498db")

    @property
    def label_ar(self) -> str:
        """التسمية بالعربي"""
        labels = {
            "email": "إيميل",
            "task": "مهمة",
            "calendar": "تقويم",
            "system": "نظام",
            "ai": "ذكاء اصطناعي",
            "alert": "تنبيه",
        }
        return labels.get(self.value, "إشعار")


class NotificationPriority(Enum):
    """أولويات الإشعارات"""
    URGENT = "urgent"   # عاجل جداً
    HIGH = "high"       # مهم
    NORMAL = "normal"   # عادي
    LOW = "low"         # منخفض

    @property
    def color(self) -> str:
        """لون الأولوية"""
        colors = {
            "urgent": "#e74c3c",  # أحمر
            "high": "#f39c12",    # برتقالي
            "normal": "#3498db",  # أزرق
            "low": "#95a5a6",     # رمادي
        }
        return colors.get(self.value, "#3498db")

    @property
    def label_ar(self) -> str:
        """التسمية بالعربي"""
        labels = {
            "urgent": "عاجل",
            "high": "مهم",
            "normal": "عادي",
            "low": "منخفض",
        }
        return labels.get(self.value, "عادي")

    @property
    def sort_order(self) -> int:
        """ترتيب للفرز"""
        orders = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
        return orders.get(self.value, 2)


@dataclass
class NotificationAction:
    """إجراء متاح على الإشعار"""
    id: str                     # معرف الإجراء
    label: str                  # النص المعروض
    action_type: str            # نوع الإجراء: navigate, api, function
    icon: Optional[str] = None  # أيقونة (اختيارية)
    params: dict = field(default_factory=dict)  # معاملات الإجراء
    is_primary: bool = False    # هل هو الإجراء الرئيسي

    def to_dict(self) -> dict:
        """تحويل إلى dictionary"""
        return {
            "id": self.id,
            "label": self.label,
            "action_type": self.action_type,
            "icon": self.icon,
            "params": self.params,
            "is_primary": self.is_primary,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NotificationAction":
        """إنشاء من dictionary"""
        return cls(
            id=data.get("id", ""),
            label=data.get("label", ""),
            action_type=data.get("action_type", "navigate"),
            icon=data.get("icon"),
            params=data.get("params", {}),
            is_primary=data.get("is_primary", False),
        )


@dataclass
class Notification:
    """نموذج الإشعار"""
    id: Optional[int] = None
    title: str = ""
    body: Optional[str] = None

    notification_type: NotificationType = NotificationType.SYSTEM
    priority: NotificationPriority = NotificationPriority.NORMAL

    # المصدر
    source_module: Optional[str] = None
    source_id: Optional[int] = None
    source_type: Optional[str] = None

    # الحالة
    is_read: bool = False
    is_archived: bool = False
    is_pinned: bool = False

    # الإجراءات
    actions: list[NotificationAction] = field(default_factory=list)

    # بيانات إضافية
    metadata: dict = field(default_factory=dict)

    # تحليل AI
    ai_priority_score: Optional[float] = None
    ai_category: Optional[str] = None
    ai_suggested_action: Optional[str] = None

    # المستخدم
    user_id: Optional[int] = None

    # التواريخ
    created_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    def __post_init__(self):
        """تحويل الأنواع إذا لزم الأمر"""
        if isinstance(self.notification_type, str):
            self.notification_type = NotificationType(self.notification_type)
        if isinstance(self.priority, str):
            self.priority = NotificationPriority(self.priority)

    @property
    def is_urgent(self) -> bool:
        """هل الإشعار عاجل"""
        return self.priority == NotificationPriority.URGENT

    @property
    def time_ago(self) -> str:
        """الوقت المنقضي منذ الإنشاء"""
        if not self.created_at:
            return ""
        try:
            from core.utils import format_time_ago
            return format_time_ago(self.created_at)
        except ImportError:
            return str(self.created_at)

    @property
    def type_icon(self) -> str:
        """أيقونة النوع"""
        return self.notification_type.icon

    @property
    def type_color(self) -> str:
        """لون النوع"""
        return self.notification_type.color

    @property
    def priority_color(self) -> str:
        """لون الأولوية"""
        return self.priority.color

    def get_primary_action(self) -> Optional[NotificationAction]:
        """الحصول على الإجراء الرئيسي"""
        for action in self.actions:
            if action.is_primary:
                return action
        return self.actions[0] if self.actions else None

    def to_dict(self) -> dict:
        """تحويل إلى dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "notification_type": self.notification_type.value,
            "priority": self.priority.value,
            "source_module": self.source_module,
            "source_id": self.source_id,
            "source_type": self.source_type,
            "is_read": self.is_read,
            "is_archived": self.is_archived,
            "is_pinned": self.is_pinned,
            "actions": [a.to_dict() for a in self.actions],
            "metadata": self.metadata,
            "ai_priority_score": self.ai_priority_score,
            "ai_category": self.ai_category,
            "ai_suggested_action": self.ai_suggested_action,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Notification":
        """إنشاء من dictionary"""
        actions = []
        if "actions" in data and data["actions"]:
            actions_data = data["actions"]
            if isinstance(actions_data, str):
                actions_data = json.loads(actions_data)
            actions = [NotificationAction.from_dict(a) for a in actions_data]

        metadata = data.get("metadata", {})
        if isinstance(metadata, str):
            metadata = json.loads(metadata)

        return cls(
            id=data.get("id"),
            title=data.get("title", ""),
            body=data.get("body"),
            notification_type=data.get("notification_type", "system"),
            priority=data.get("priority", "normal"),
            source_module=data.get("source_module"),
            source_id=data.get("source_id"),
            source_type=data.get("source_type"),
            is_read=data.get("is_read", False),
            is_archived=data.get("is_archived", False),
            is_pinned=data.get("is_pinned", False),
            actions=actions,
            metadata=metadata,
            ai_priority_score=data.get("ai_priority_score"),
            ai_category=data.get("ai_category"),
            ai_suggested_action=data.get("ai_suggested_action"),
            user_id=data.get("user_id"),
            created_at=_parse_datetime(data.get("created_at")),
            read_at=_parse_datetime(data.get("read_at")),
            expires_at=_parse_datetime(data.get("expires_at")),
        )

    @classmethod
    def from_db_row(cls, columns: list, row: tuple) -> "Notification":
        """إنشاء من صف قاعدة البيانات"""
        data = dict(zip(columns, row))
        return cls.from_dict(data)


@dataclass
class NotificationSettings:
    """إعدادات الإشعارات للمستخدم"""
    user_id: Optional[int] = None

    # إعدادات عامة
    notifications_enabled: bool = True
    sound_enabled: bool = True
    desktop_notifications: bool = True

    # فلترة حسب النوع
    email_notifications: bool = True
    task_notifications: bool = True
    calendar_notifications: bool = True
    system_notifications: bool = True
    ai_notifications: bool = True

    # فلترة حسب الأولوية
    show_low_priority: bool = True
    show_normal_priority: bool = True
    show_high_priority: bool = True
    show_urgent_priority: bool = True

    # وضع التركيز
    focus_mode_enabled: bool = False
    focus_mode_start: Optional[str] = None  # HH:MM
    focus_mode_end: Optional[str] = None    # HH:MM
    focus_mode_allow_urgent: bool = True

    # الأصوات
    sound_file: str = "default"

    # التنظيف التلقائي
    auto_archive_days: int = 30
    auto_delete_days: int = 90


# ============================================================
# Helper Functions
# ============================================================

def _parse_datetime(value) -> Optional[datetime]:
    """تحويل قيمة إلى datetime"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


# ============================================================
# Database Operations
# ============================================================

def _get_db():
    """الحصول على اتصال قاعدة البيانات"""
    try:
        from core.database import select_all, select_one, insert_returning_id, update, delete
        return select_all, select_one, insert_returning_id, update, delete
    except ImportError:
        app_logger.error("Could not import database module")
        return None, None, None, None, None


def create_notification(notification: Notification) -> Optional[int]:
    """
    إنشاء إشعار جديد

    Args:
        notification: كائن الإشعار

    Returns:
        معرف الإشعار الجديد أو None
    """
    select_all, select_one, insert_returning_id, update, delete = _get_db()
    if not insert_returning_id:
        return None

    try:
        actions_json = json.dumps([a.to_dict() for a in notification.actions], ensure_ascii=False)
        metadata_json = json.dumps(notification.metadata, ensure_ascii=False)

        query = """
            INSERT INTO notifications (
                title, body, notification_type, priority,
                source_module, source_id, source_type,
                is_read, is_archived, is_pinned,
                actions, metadata,
                ai_priority_score, ai_category, ai_suggested_action,
                user_id, expires_at
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s::jsonb, %s::jsonb,
                %s, %s, %s,
                %s, %s
            ) RETURNING id
        """

        notification_id = insert_returning_id(query, (
            notification.title,
            notification.body,
            notification.notification_type.value,
            notification.priority.value,
            notification.source_module,
            notification.source_id,
            notification.source_type,
            notification.is_read,
            notification.is_archived,
            notification.is_pinned,
            actions_json,
            metadata_json,
            notification.ai_priority_score,
            notification.ai_category,
            notification.ai_suggested_action,
            notification.user_id,
            notification.expires_at,
        ))

        app_logger.info(f"Created notification: {notification.title} (ID: {notification_id})")
        return notification_id

    except Exception as e:
        app_logger.error(f"Error creating notification: {e}")
        return None


def get_notifications(
    user_id: Optional[int] = None,
    notification_type: Optional[NotificationType] = None,
    priority: Optional[NotificationPriority] = None,
    is_read: Optional[bool] = None,
    is_archived: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> list[Notification]:
    """
    جلب الإشعارات

    Args:
        user_id: معرف المستخدم (اختياري)
        notification_type: نوع الإشعار (اختياري)
        priority: الأولوية (اختياري)
        is_read: حالة القراءة (اختياري)
        is_archived: هل مؤرشف
        limit: الحد الأقصى
        offset: البداية

    Returns:
        قائمة الإشعارات
    """
    select_all, select_one, insert_returning_id, update, delete = _get_db()
    if not select_all:
        return []

    try:
        conditions = ["deleted_at IS NULL", "is_archived = %s"]
        params = [is_archived]

        if user_id is not None:
            conditions.append("(user_id = %s OR user_id IS NULL)")
            params.append(user_id)

        if notification_type is not None:
            conditions.append("notification_type = %s")
            params.append(notification_type.value if isinstance(notification_type, NotificationType) else notification_type)

        if priority is not None:
            conditions.append("priority = %s")
            params.append(priority.value if isinstance(priority, NotificationPriority) else priority)

        if is_read is not None:
            conditions.append("is_read = %s")
            params.append(is_read)

        query = f"""
            SELECT * FROM notifications
            WHERE {' AND '.join(conditions)}
            ORDER BY
                is_pinned DESC,
                CASE priority
                    WHEN 'urgent' THEN 0
                    WHEN 'high' THEN 1
                    WHEN 'normal' THEN 2
                    WHEN 'low' THEN 3
                END,
                created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])

        columns, rows = select_all(query, tuple(params))
        if not rows:
            return []

        return [Notification.from_db_row(columns, row) for row in rows]

    except Exception as e:
        app_logger.error(f"Error getting notifications: {e}")
        return []


def get_notification_by_id(notification_id: int) -> Optional[Notification]:
    """
    جلب إشعار بمعرفه

    Args:
        notification_id: معرف الإشعار

    Returns:
        الإشعار أو None
    """
    select_all, select_one, insert_returning_id, update, delete = _get_db()
    if not select_one:
        return None

    try:
        query = "SELECT * FROM notifications WHERE id = %s AND deleted_at IS NULL"
        columns, row = select_one(query, (notification_id,))
        if row:
            return Notification.from_db_row(columns, row)
        return None
    except Exception as e:
        app_logger.error(f"Error getting notification {notification_id}: {e}")
        return None


def get_unread_count(user_id: Optional[int] = None) -> int:
    """
    حساب عدد الإشعارات غير المقروءة

    Args:
        user_id: معرف المستخدم (اختياري)

    Returns:
        عدد الإشعارات غير المقروءة
    """
    select_all, select_one, insert_returning_id, update, delete = _get_db()
    if not select_one:
        return 0

    try:
        if user_id is not None:
            query = """
                SELECT COUNT(*) FROM notifications
                WHERE is_read = FALSE AND is_archived = FALSE AND deleted_at IS NULL
                AND (user_id = %s OR user_id IS NULL)
            """
            columns, row = select_one(query, (user_id,))
        else:
            query = """
                SELECT COUNT(*) FROM notifications
                WHERE is_read = FALSE AND is_archived = FALSE AND deleted_at IS NULL
            """
            columns, row = select_one(query, ())

        return row[0] if row else 0
    except Exception as e:
        app_logger.error(f"Error getting unread count: {e}")
        return 0


def mark_as_read(notification_id: int) -> bool:
    """
    تحديد إشعار كمقروء

    Args:
        notification_id: معرف الإشعار

    Returns:
        نجاح العملية
    """
    select_all, select_one, insert_returning_id, update, delete = _get_db()
    if not update:
        return False

    try:
        query = """
            UPDATE notifications
            SET is_read = TRUE, read_at = CURRENT_TIMESTAMP
            WHERE id = %s AND deleted_at IS NULL
        """
        update(query, (notification_id,))
        app_logger.debug(f"Marked notification {notification_id} as read")
        return True
    except Exception as e:
        app_logger.error(f"Error marking notification as read: {e}")
        return False


def mark_all_as_read(user_id: Optional[int] = None) -> int:
    """
    تحديد كل الإشعارات كمقروءة

    Args:
        user_id: معرف المستخدم (اختياري)

    Returns:
        عدد الإشعارات المحدثة
    """
    select_all, select_one, insert_returning_id, update, delete = _get_db()
    if not update:
        return 0

    try:
        if user_id is not None:
            query = """
                UPDATE notifications
                SET is_read = TRUE, read_at = CURRENT_TIMESTAMP
                WHERE is_read = FALSE AND deleted_at IS NULL
                AND (user_id = %s OR user_id IS NULL)
            """
            update(query, (user_id,))
        else:
            query = """
                UPDATE notifications
                SET is_read = TRUE, read_at = CURRENT_TIMESTAMP
                WHERE is_read = FALSE AND deleted_at IS NULL
            """
            update(query, ())

        app_logger.info("Marked all notifications as read")
        return 1  # TODO: Return actual count
    except Exception as e:
        app_logger.error(f"Error marking all as read: {e}")
        return 0


def archive_notification(notification_id: int) -> bool:
    """
    أرشفة إشعار

    Args:
        notification_id: معرف الإشعار

    Returns:
        نجاح العملية
    """
    select_all, select_one, insert_returning_id, update, delete = _get_db()
    if not update:
        return False

    try:
        query = """
            UPDATE notifications
            SET is_archived = TRUE
            WHERE id = %s AND deleted_at IS NULL
        """
        update(query, (notification_id,))
        app_logger.debug(f"Archived notification {notification_id}")
        return True
    except Exception as e:
        app_logger.error(f"Error archiving notification: {e}")
        return False


def delete_notification(notification_id: int, hard_delete: bool = False) -> bool:
    """
    حذف إشعار

    Args:
        notification_id: معرف الإشعار
        hard_delete: حذف نهائي أم ناعم

    Returns:
        نجاح العملية
    """
    select_all, select_one, insert_returning_id, update, delete_func = _get_db()

    try:
        if hard_delete:
            if not delete_func:
                return False
            query = "DELETE FROM notifications WHERE id = %s"
            delete_func(query, (notification_id,))
        else:
            if not update:
                return False
            query = """
                UPDATE notifications
                SET deleted_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """
            update(query, (notification_id,))

        app_logger.debug(f"Deleted notification {notification_id} (hard={hard_delete})")
        return True
    except Exception as e:
        app_logger.error(f"Error deleting notification: {e}")
        return False


# ============================================================
# Convenience Functions
# ============================================================

def notify(
    title: str,
    body: Optional[str] = None,
    notification_type: NotificationType = NotificationType.SYSTEM,
    priority: NotificationPriority = NotificationPriority.NORMAL,
    source_module: Optional[str] = None,
    source_id: Optional[int] = None,
    actions: Optional[list[NotificationAction]] = None,
    user_id: Optional[int] = None,
) -> Optional[int]:
    """
    دالة سريعة لإنشاء إشعار

    Args:
        title: عنوان الإشعار
        body: محتوى الإشعار
        notification_type: نوع الإشعار
        priority: الأولوية
        source_module: الموديول المصدر
        source_id: معرف السجل المصدر
        actions: الإجراءات المتاحة
        user_id: معرف المستخدم

    Returns:
        معرف الإشعار أو None

    Example:
        >>> notify("تم حفظ الموظف", "تم حفظ بيانات الموظف بنجاح")
        >>> notify("إيميل جديد", "وصل إيميل من HR", NotificationType.EMAIL, NotificationPriority.HIGH)
    """
    notification = Notification(
        title=title,
        body=body,
        notification_type=notification_type,
        priority=priority,
        source_module=source_module,
        source_id=source_id,
        actions=actions or [],
        user_id=user_id,
    )
    return create_notification(notification)
