"""
INTEGRA - Email Task Integration
تكامل الإيميل مع المهام
المحور H

ينشئ مهام من الإيميلات ويربطها.

التاريخ: 4 فبراير 2026
"""

from datetime import datetime
from typing import Optional, Dict, Any

from ..models import Task, TaskStatus, TaskPriority, TaskCategory, AIAnalysis
from ..repository import create_task, get_task_by_id

from core.logging import app_logger


class EmailTaskIntegration:
    """
    تكامل الإيميل مع المهام

    ينشئ مهام من الإيميلات ويربط بينهما.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def create_from_email(
        self,
        email_id: str,
        subject: str,
        body: str,
        sender_email: Optional[str] = None,
        sender_name: Optional[str] = None,
        ai_analysis: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """
        إنشاء مهمة من إيميل

        Args:
            email_id: معرف الإيميل
            subject: موضوع الإيميل
            body: نص الإيميل
            sender_email: بريد المرسل
            sender_name: اسم المرسل
            ai_analysis: تحليل AI (إذا متوفر)

        Returns:
            معرف المهمة الجديدة
        """
        try:
            # Build task title
            title = f"📧 {subject}"
            if len(title) > 200:
                title = title[:197] + "..."

            # Build description
            description_parts = []
            if sender_name or sender_email:
                description_parts.append(f"من: {sender_name or ''} <{sender_email or ''}>")
            description_parts.append("")
            description_parts.append("--- محتوى الإيميل ---")
            description_parts.append(body[:1000] if body else "")
            if len(body or "") > 1000:
                description_parts.append("... [محتوى مختصر]")

            description = "\n".join(description_parts)

            # Determine priority and category from AI analysis
            priority = TaskPriority.NORMAL
            category = "general"
            suggested_action = None

            if ai_analysis:
                if ai_analysis.get("priority"):
                    try:
                        priority = TaskPriority(ai_analysis["priority"])
                    except ValueError:
                        pass

                if ai_analysis.get("category"):
                    category = ai_analysis["category"]

                suggested_action = ai_analysis.get("suggested_action")

            # Create task
            task = Task(
                title=title,
                description=description,
                status=TaskStatus.PENDING,
                priority=priority,
                category=category,
                source_email_id=email_id,
                ai_suggested_action=suggested_action,
                metadata={
                    "source": "email",
                    "sender_email": sender_email,
                    "sender_name": sender_name,
                    "original_subject": subject,
                }
            )

            # Create AI analysis if provided
            if ai_analysis:
                task.ai_analysis = AIAnalysis(
                    suggested_priority=priority,
                    suggested_category=TaskCategory(category) if category in [c.value for c in TaskCategory] else None,
                    suggested_action=suggested_action,
                    keywords=ai_analysis.get("keywords", []),
                    confidence=ai_analysis.get("confidence", 0.0)
                )

            task_id = create_task(task)

            if task_id:
                app_logger.info(f"Created task {task_id} from email {email_id}")

            return task_id

        except Exception as e:
            app_logger.error(f"Failed to create task from email: {e}")
            return None

    def link_task_to_email(
        self,
        task_id: int,
        email_id: str
    ) -> bool:
        """
        ربط مهمة موجودة بإيميل

        Args:
            task_id: معرف المهمة
            email_id: معرف الإيميل

        Returns:
            True إذا نجحت العملية
        """
        try:
            from ..repository import update_task

            task = get_task_by_id(task_id)
            if not task:
                return False

            task.source_email_id = email_id
            return update_task(task)

        except Exception as e:
            app_logger.error(f"Failed to link task to email: {e}")
            return False

    def get_tasks_by_email(self, email_id: str):
        """
        جلب المهام المرتبطة بإيميل

        Args:
            email_id: معرف الإيميل

        Returns:
            قائمة المهام
        """
        try:
            from ..repository import get_tasks_by_source_email

            return get_tasks_by_source_email(email_id)

        except Exception as e:
            app_logger.error(f"Failed to get tasks by email: {e}")
            return []


# ═══════════════════════════════════════════════════════════════
# Singleton & Quick Access Functions
# ═══════════════════════════════════════════════════════════════

_integration: Optional[EmailTaskIntegration] = None


def get_email_task_integration() -> EmailTaskIntegration:
    """الحصول على instance التكامل"""
    global _integration
    if _integration is None:
        _integration = EmailTaskIntegration()
    return _integration


def create_task_from_email(
    email_id: str,
    subject: str,
    body: str,
    sender_email: Optional[str] = None,
    sender_name: Optional[str] = None,
    ai_analysis: Optional[Dict[str, Any]] = None
) -> Optional[int]:
    """إنشاء مهمة من إيميل"""
    return get_email_task_integration().create_from_email(
        email_id, subject, body, sender_email, sender_name, ai_analysis
    )
