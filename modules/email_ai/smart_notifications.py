"""
G2: Smart Notifications
=======================
إشعارات ذكية للإيميلات - تنبيهات عاجلة، ملخص يومي، ربط مع Toast.

Features:
- إشعارات فورية للإيميلات العاجلة
- تنبيه بالمهام المستخرجة من الإيميلات
- ملخص يومي/أسبوعي تلقائي
- ربط مع Toast Notifications (D3)
- تكامل مع نظام الإشعارات الذكي (J)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Dict, List, Optional
import threading
import json

from core.logging import app_logger

try:
    from core.email import Email
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    Email = None

from .email_assistant import (
    EmailAssistant, get_email_assistant,
    DetailedEmailAnalysis, EmailClassification,
)


class EmailNotificationType(Enum):
    """أنواع إشعارات الإيميل"""
    URGENT_EMAIL = "urgent_email"
    NEW_TASK = "new_task"
    MEETING_REQUEST = "meeting_request"
    APPROVAL_NEEDED = "approval_needed"
    HR_REQUEST = "hr_request"
    SUSPICIOUS_EMAIL = "suspicious_email"
    DAILY_SUMMARY = "daily_summary"
    WEEKLY_SUMMARY = "weekly_summary"
    FOLLOW_UP_REMINDER = "follow_up_reminder"
    UNREAD_PILE_UP = "unread_pile_up"

    @property
    def label_ar(self) -> str:
        labels = {
            "urgent_email": "إيميل عاجل",
            "new_task": "مهمة جديدة من إيميل",
            "meeting_request": "طلب اجتماع",
            "approval_needed": "يحتاج اعتماد",
            "hr_request": "طلب HR",
            "suspicious_email": "إيميل مشبوه",
            "daily_summary": "ملخص يومي",
            "weekly_summary": "ملخص أسبوعي",
            "follow_up_reminder": "تذكير متابعة",
            "unread_pile_up": "تراكم إيميلات غير مقروءة",
        }
        return labels.get(self.value, "إشعار")

    @property
    def priority(self) -> str:
        high = {"urgent_email", "suspicious_email", "approval_needed"}
        medium = {"new_task", "meeting_request", "hr_request", "follow_up_reminder"}
        if self.value in high:
            return "urgent"
        if self.value in medium:
            return "high"
        return "normal"


@dataclass
class EmailNotification:
    """إشعار إيميل ذكي"""
    id: Optional[int] = None
    notification_type: EmailNotificationType = EmailNotificationType.URGENT_EMAIL
    title: str = ""
    body: str = ""

    # Source
    email_id: Optional[str] = None
    sender_name: Optional[str] = None
    sender_email: Optional[str] = None

    # Analysis reference
    analysis: Optional[DetailedEmailAnalysis] = None

    # Actions
    actions: List[Dict] = field(default_factory=list)

    # Status
    is_read: bool = False
    is_dismissed: bool = False

    # Timestamps
    created_at: Optional[datetime] = None

    def to_notification_dict(self) -> dict:
        """تحويل إلى dict متوافق مع نظام الإشعارات (J)."""
        return {
            "title": self.title,
            "body": self.body,
            "notification_type": "email",
            "priority": self.notification_type.priority,
            "source_type": "email",
            "source_id": self.email_id,
            "actions": json.dumps(self.actions, ensure_ascii=False),
            "metadata": json.dumps({
                "email_notification_type": self.notification_type.value,
                "sender_name": self.sender_name,
                "sender_email": self.sender_email,
            }, ensure_ascii=False),
            "created_at": (self.created_at or datetime.now()).isoformat(),
        }


class EmailNotificationManager:
    """
    مدير إشعارات الإيميل الذكي (G2)

    يراقب الإيميلات الجديدة ويُنشئ إشعارات ذكية بناءً على التحليل.

    Usage:
        manager = get_email_notification_manager()
        manager.on_notification = my_callback
        notifications = manager.process_new_emails(emails)
    """

    _instance: Optional['EmailNotificationManager'] = None
    _lock = threading.Lock()

    # Thresholds
    UNREAD_PILE_UP_THRESHOLD = 20
    FOLLOW_UP_HOURS = 48

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._assistant = get_email_assistant()
        self._notification_history: List[EmailNotification] = []
        self._history_lock = threading.Lock()
        self._on_notification: Optional[Callable[[EmailNotification], None]] = None
        self._processed_emails: set = set()
        self._initialized = True
        app_logger.info("EmailNotificationManager (G2) initialized")

    @property
    def on_notification(self) -> Optional[Callable]:
        return self._on_notification

    @on_notification.setter
    def on_notification(self, callback: Optional[Callable[[EmailNotification], None]]):
        self._on_notification = callback

    def process_new_emails(
        self, emails: List['Email']
    ) -> List[EmailNotification]:
        """
        معالجة إيميلات جديدة وإنشاء إشعارات.

        Args:
            emails: قائمة الإيميلات الجديدة

        Returns:
            قائمة الإشعارات المُنشأة
        """
        notifications = []

        for email in emails:
            if email.entry_id in self._processed_emails:
                continue

            try:
                email_notifications = self._process_single_email(email)
                notifications.extend(email_notifications)
                self._processed_emails.add(email.entry_id)
            except Exception as e:
                app_logger.error(f"Failed to process email {email.entry_id}: {e}")

        # Store in history
        with self._history_lock:
            self._notification_history.extend(notifications)

        # Fire callbacks
        for notif in notifications:
            self._fire_notification(notif)

        return notifications

    def check_unread_pile_up(self, unread_count: int) -> Optional[EmailNotification]:
        """فحص تراكم الإيميلات غير المقروءة."""
        if unread_count >= self.UNREAD_PILE_UP_THRESHOLD:
            notif = EmailNotification(
                notification_type=EmailNotificationType.UNREAD_PILE_UP,
                title=f"تراكم {unread_count} إيميل غير مقروء",
                body=f"لديك {unread_count} إيميل غير مقروء. يُنصح بمراجعتها.",
                actions=[
                    {"id": "open_inbox", "label": "فتح البريد", "action_type": "navigate",
                     "params": {"module": "email"}, "is_primary": True},
                    {"id": "dismiss", "label": "لاحقاً", "action_type": "dismiss"},
                ],
                created_at=datetime.now(),
            )
            self._fire_notification(notif)
            return notif
        return None

    def check_follow_ups(
        self, sent_emails: List['Email'], received_emails: List['Email']
    ) -> List[EmailNotification]:
        """فحص الإيميلات التي تحتاج متابعة (أرسلتها ولم يُرد عليها)."""
        notifications = []
        cutoff = datetime.now() - timedelta(hours=self.FOLLOW_UP_HOURS)

        received_conversations = {
            e.conversation_id for e in received_emails if e.conversation_id
        }

        for email in sent_emails:
            if not email.sent_time or email.sent_time > cutoff:
                continue

            if email.conversation_id and email.conversation_id not in received_conversations:
                notif = EmailNotification(
                    notification_type=EmailNotificationType.FOLLOW_UP_REMINDER,
                    title=f"لم يتم الرد على: {email.subject}",
                    body=f"أرسلت إيميل إلى {', '.join(email.to)} منذ أكثر من {self.FOLLOW_UP_HOURS} ساعة بدون رد.",
                    email_id=email.entry_id,
                    sender_name=', '.join(email.to),
                    actions=[
                        {"id": "open_email", "label": "فتح الإيميل", "action_type": "navigate",
                         "params": {"module": "email", "email_id": email.entry_id}, "is_primary": True},
                        {"id": "send_follow_up", "label": "إرسال متابعة", "action_type": "function",
                         "params": {"action": "follow_up", "email_id": email.entry_id}},
                        {"id": "dismiss", "label": "تجاهل", "action_type": "dismiss"},
                    ],
                    created_at=datetime.now(),
                )
                notifications.append(notif)

        return notifications

    def generate_daily_summary(
        self, emails: List['Email']
    ) -> Optional[EmailNotification]:
        """توليد ملخص يومي."""
        if not emails:
            return None

        summary = self._assistant.get_daily_summary(emails)

        body_lines = [
            f"إجمالي الإيميلات: {summary['total']}",
            f"عاجل: {summary['urgent']}",
            f"يحتاج إجراء: {summary['requires_action']}",
            f"مهام مستخرجة: {summary['tasks_found']}",
            f"اجتماعات: {summary['meetings_found']}",
        ]

        if summary.get("action_items"):
            body_lines.append("\nالمهام المطلوبة:")
            for item in summary["action_items"][:5]:
                body_lines.append(f"  - {item['task']} (من {item['from']})")

        notif = EmailNotification(
            notification_type=EmailNotificationType.DAILY_SUMMARY,
            title=f"ملخص البريد اليومي ({summary['total']} إيميل)",
            body="\n".join(body_lines),
            actions=[
                {"id": "open_inbox", "label": "فتح البريد", "action_type": "navigate",
                 "params": {"module": "email"}, "is_primary": True},
                {"id": "dismiss", "label": "تم", "action_type": "dismiss"},
            ],
            created_at=datetime.now(),
        )

        self._fire_notification(notif)
        return notif

    def get_notification_history(
        self, limit: int = 50, notification_type: Optional[EmailNotificationType] = None
    ) -> List[EmailNotification]:
        """الحصول على سجل الإشعارات."""
        with self._history_lock:
            history = list(self._notification_history)

        if notification_type:
            history = [n for n in history if n.notification_type == notification_type]

        history.sort(key=lambda n: n.created_at or datetime.min, reverse=True)
        return history[:limit]

    def get_stats(self) -> Dict:
        """إحصائيات الإشعارات."""
        with self._history_lock:
            total = len(self._notification_history)
            unread = sum(1 for n in self._notification_history if not n.is_read)
            by_type = {}
            for n in self._notification_history:
                type_name = n.notification_type.label_ar
                by_type[type_name] = by_type.get(type_name, 0) + 1

        return {
            "total": total,
            "unread": unread,
            "by_type": by_type,
            "processed_emails": len(self._processed_emails),
        }

    # --- Private methods ---

    def _process_single_email(self, email: 'Email') -> List[EmailNotification]:
        """معالجة إيميل واحد وإنشاء إشعارات."""
        notifications = []
        analysis = self._assistant.analyze(email)

        # Urgent email
        if analysis.classification == EmailClassification.WORK_URGENT:
            notifications.append(self._create_urgent_notification(email, analysis))

        # Suspicious email
        if analysis.is_suspicious:
            notifications.append(self._create_suspicious_notification(email, analysis))

        # Tasks found
        if analysis.tasks:
            notifications.append(self._create_task_notification(email, analysis))

        # Meeting request
        if analysis.classification == EmailClassification.MEETING_REQUEST:
            notifications.append(self._create_meeting_notification(email, analysis))

        # Approval needed
        if analysis.classification == EmailClassification.APPROVAL_REQUEST:
            notifications.append(self._create_approval_notification(email, analysis))

        # HR request
        if analysis.classification == EmailClassification.HR_REQUEST:
            notifications.append(self._create_hr_notification(email, analysis))

        return notifications

    def _create_urgent_notification(
        self, email: 'Email', analysis: DetailedEmailAnalysis
    ) -> EmailNotification:
        return EmailNotification(
            notification_type=EmailNotificationType.URGENT_EMAIL,
            title=f"إيميل عاجل: {email.subject}",
            body=analysis.summary,
            email_id=email.entry_id,
            sender_name=email.sender_name,
            sender_email=email.sender_email,
            analysis=analysis,
            actions=[
                {"id": "open_email", "label": "فتح الإيميل", "action_type": "navigate",
                 "params": {"module": "email", "email_id": email.entry_id}, "is_primary": True},
                {"id": "reply", "label": "رد سريع", "action_type": "function",
                 "params": {"action": "quick_reply", "email_id": email.entry_id}},
                {"id": "create_task", "label": "إنشاء مهمة", "action_type": "function",
                 "params": {"action": "create_task", "email_id": email.entry_id}},
            ],
            created_at=datetime.now(),
        )

    def _create_suspicious_notification(
        self, email: 'Email', analysis: DetailedEmailAnalysis
    ) -> EmailNotification:
        return EmailNotification(
            notification_type=EmailNotificationType.SUSPICIOUS_EMAIL,
            title=f"تحذير: إيميل مشبوه من {email.sender_name}",
            body=f"{analysis.suspicious_reason}\n\nالموضوع: {email.subject}",
            email_id=email.entry_id,
            sender_name=email.sender_name,
            sender_email=email.sender_email,
            actions=[
                {"id": "view_email", "label": "عرض بحذر", "action_type": "navigate",
                 "params": {"module": "email", "email_id": email.entry_id}},
                {"id": "mark_spam", "label": "سبام", "action_type": "function",
                 "params": {"action": "mark_spam", "email_id": email.entry_id}},
                {"id": "dismiss", "label": "تجاهل", "action_type": "dismiss"},
            ],
            created_at=datetime.now(),
        )

    def _create_task_notification(
        self, email: 'Email', analysis: DetailedEmailAnalysis
    ) -> EmailNotification:
        task_list = "\n".join(f"  - {t.title}" for t in analysis.tasks[:5])
        return EmailNotification(
            notification_type=EmailNotificationType.NEW_TASK,
            title=f"مهام مستخرجة من إيميل {email.sender_name}",
            body=f"الموضوع: {email.subject}\n\nالمهام:\n{task_list}",
            email_id=email.entry_id,
            sender_name=email.sender_name,
            sender_email=email.sender_email,
            analysis=analysis,
            actions=[
                {"id": "create_tasks", "label": "إنشاء المهام", "action_type": "function",
                 "params": {"action": "create_tasks_from_email", "email_id": email.entry_id},
                 "is_primary": True},
                {"id": "open_email", "label": "فتح الإيميل", "action_type": "navigate",
                 "params": {"module": "email", "email_id": email.entry_id}},
                {"id": "dismiss", "label": "تجاهل", "action_type": "dismiss"},
            ],
            created_at=datetime.now(),
        )

    def _create_meeting_notification(
        self, email: 'Email', analysis: DetailedEmailAnalysis
    ) -> EmailNotification:
        meeting_info = ""
        if analysis.meetings:
            m = analysis.meetings[0]
            parts = [m.title]
            if m.date_hint:
                parts.append(f"التاريخ: {m.date_hint}")
            if m.time_hint:
                parts.append(f"الوقت: {m.time_hint}")
            meeting_info = " | ".join(parts)

        return EmailNotification(
            notification_type=EmailNotificationType.MEETING_REQUEST,
            title=f"طلب اجتماع من {email.sender_name}",
            body=f"{meeting_info}\n\n{analysis.summary}",
            email_id=email.entry_id,
            sender_name=email.sender_name,
            sender_email=email.sender_email,
            actions=[
                {"id": "add_calendar", "label": "إضافة للتقويم", "action_type": "function",
                 "params": {"action": "add_to_calendar", "email_id": email.entry_id},
                 "is_primary": True},
                {"id": "reply_accept", "label": "قبول", "action_type": "function",
                 "params": {"action": "accept_meeting", "email_id": email.entry_id}},
                {"id": "reply_decline", "label": "اعتذار", "action_type": "function",
                 "params": {"action": "decline_meeting", "email_id": email.entry_id}},
            ],
            created_at=datetime.now(),
        )

    def _create_approval_notification(
        self, email: 'Email', analysis: DetailedEmailAnalysis
    ) -> EmailNotification:
        return EmailNotification(
            notification_type=EmailNotificationType.APPROVAL_NEEDED,
            title=f"طلب اعتماد: {email.subject}",
            body=analysis.summary,
            email_id=email.entry_id,
            sender_name=email.sender_name,
            sender_email=email.sender_email,
            actions=[
                {"id": "open_email", "label": "مراجعة الطلب", "action_type": "navigate",
                 "params": {"module": "email", "email_id": email.entry_id}, "is_primary": True},
                {"id": "approve", "label": "اعتماد", "action_type": "function",
                 "params": {"action": "approve", "email_id": email.entry_id}},
                {"id": "reject", "label": "رفض", "action_type": "function",
                 "params": {"action": "reject", "email_id": email.entry_id}},
            ],
            created_at=datetime.now(),
        )

    def _create_hr_notification(
        self, email: 'Email', analysis: DetailedEmailAnalysis
    ) -> EmailNotification:
        return EmailNotification(
            notification_type=EmailNotificationType.HR_REQUEST,
            title=f"طلب HR: {email.subject}",
            body=analysis.summary,
            email_id=email.entry_id,
            sender_name=email.sender_name,
            sender_email=email.sender_email,
            actions=[
                {"id": "open_email", "label": "فتح الإيميل", "action_type": "navigate",
                 "params": {"module": "email", "email_id": email.entry_id}, "is_primary": True},
                {"id": "create_task", "label": "إنشاء مهمة", "action_type": "function",
                 "params": {"action": "create_task", "email_id": email.entry_id}},
            ],
            created_at=datetime.now(),
        )

    def _fire_notification(self, notification: EmailNotification):
        """إرسال الإشعار عبر callback."""
        if self._on_notification:
            try:
                self._on_notification(notification)
            except Exception as e:
                app_logger.error(f"Notification callback error: {e}")

        # Try to use Toast if available
        self._show_toast(notification)

    def _show_toast(self, notification: EmailNotification):
        """عرض Toast notification إذا متوفر."""
        try:
            from ui.components.notifications.toast_manager import get_toast_manager
            toast = get_toast_manager()
            priority_map = {
                "urgent": "error",
                "high": "warning",
                "normal": "info",
            }
            toast_type = priority_map.get(notification.notification_type.priority, "info")
            toast.show(
                title=notification.title,
                message=notification.body[:100],
                toast_type=toast_type,
            )
        except ImportError:
            pass
        except Exception as e:
            app_logger.debug(f"Toast not available: {e}")


# Singleton
_manager: Optional[EmailNotificationManager] = None
_manager_lock = threading.Lock()


def get_email_notification_manager() -> EmailNotificationManager:
    """Get singleton EmailNotificationManager."""
    global _manager
    with _manager_lock:
        if _manager is None:
            _manager = EmailNotificationManager()
        return _manager
