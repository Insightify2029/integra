"""
INTEGRA - Task Repository
مستودع بيانات المهام
المحور H

التاريخ: 4 فبراير 2026
"""

import json
from datetime import datetime, date
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path

from core.database import (
    select_all, select_one,
    insert, insert_returning_id,
    update, update_returning_count,
    delete, delete_returning_count,
    get_scalar, get_count
)
from core.logging import app_logger

from ..models import (
    Task, TaskStatus, TaskPriority, TaskCategory,
    ChecklistItem, TaskAttachment, TaskComment,
    RecurrencePattern, AIAnalysis, TaskStatistics
)


class TaskRepository:
    """
    مستودع المهام - CRUD Operations

    يوفر كل العمليات الأساسية للتعامل مع المهام في قاعدة البيانات.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ═══════════════════════════════════════════════════════════════
    # إعداد قاعدة البيانات
    # ═══════════════════════════════════════════════════════════════

    def setup_schema(self) -> bool:
        """
        إنشاء جداول المهام في قاعدة البيانات

        Returns:
            True إذا نجح الإعداد
        """
        try:
            sql_file = Path(__file__).parent.parent.parent.parent / "core" / "database" / "tables" / "tasks.sql"
            if sql_file.exists():
                sql_content = sql_file.read_text(encoding="utf-8")
                from core.database.connection import get_connection
                conn = get_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute(sql_content)
                    conn.commit()
                    cursor.close()
                    app_logger.info("Tasks schema created successfully")
                    return True
            else:
                app_logger.error(f"Tasks SQL file not found: {sql_file}")
                return False
        except Exception as e:
            app_logger.error(f"Failed to setup tasks schema: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════
    # القراءة - Read Operations
    # ═══════════════════════════════════════════════════════════════

    def get_all(
        self,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        category: Optional[str] = None,
        assigned_to: Optional[int] = None,
        employee_id: Optional[int] = None,
        is_recurring: Optional[bool] = None,
        search: Optional[str] = None,
        order_by: str = "due_date",
        order_dir: str = "ASC",
        limit: int = 100,
        offset: int = 0
    ) -> List[Task]:
        """
        جلب كل المهام مع فلترة

        Args:
            status: فلترة حسب الحالة
            priority: فلترة حسب الأولوية
            category: فلترة حسب التصنيف
            assigned_to: فلترة حسب المكلف
            employee_id: فلترة حسب الموظف المرتبط
            is_recurring: فلترة المهام المتكررة
            search: البحث في العنوان والوصف
            order_by: ترتيب حسب العمود
            order_dir: اتجاه الترتيب (ASC/DESC)
            limit: عدد النتائج
            offset: بداية النتائج

        Returns:
            قائمة المهام
        """
        try:
            conditions = []
            params = []

            if status:
                conditions.append("status = %s")
                params.append(status.value)

            if priority:
                conditions.append("priority = %s")
                params.append(priority.value)

            if category:
                conditions.append("category = %s")
                params.append(category)

            if assigned_to is not None:
                conditions.append("assigned_to = %s")
                params.append(assigned_to)

            if employee_id is not None:
                conditions.append("employee_id = %s")
                params.append(employee_id)

            if is_recurring is not None:
                conditions.append("is_recurring = %s")
                params.append(is_recurring)

            if search:
                conditions.append("(title ILIKE %s OR description ILIKE %s)")
                search_pattern = f"%{search}%"
                params.extend([search_pattern, search_pattern])

            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

            # التحقق من صحة order_by
            valid_columns = ["id", "title", "status", "priority", "due_date", "created_at", "updated_at"]
            if order_by not in valid_columns:
                order_by = "due_date"

            order_dir = "DESC" if order_dir.upper() == "DESC" else "ASC"

            query = f"""
                SELECT * FROM task_overview
                {where_clause}
                ORDER BY
                    CASE priority
                        WHEN 'urgent' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'normal' THEN 3
                        WHEN 'low' THEN 4
                    END,
                    {order_by} {order_dir} NULLS LAST
                LIMIT %s OFFSET %s
            """
            params.extend([limit, offset])

            columns, rows = select_all(query, tuple(params))
            if not rows:
                return []

            return [Task.from_row(row, columns) for row in rows]

        except Exception as e:
            app_logger.error(f"Failed to get tasks: {e}")
            return []

    def get_by_id(self, task_id: int) -> Optional[Task]:
        """جلب مهمة بالمعرف"""
        try:
            columns, row = select_one(
                "SELECT * FROM task_overview WHERE id = %s",
                (task_id,)
            )
            if not row:
                return None

            task = Task.from_row(row, columns)

            # جلب قائمة التحقق
            task.checklist = self.get_checklist(task_id)

            # جلب المرفقات
            task.attachments = self.get_attachments(task_id)

            # جلب التعليقات
            task.comments = self.get_comments(task_id)

            return task

        except Exception as e:
            app_logger.error(f"Failed to get task {task_id}: {e}")
            return None

    def get_by_status(self, status: TaskStatus, limit: int = 50) -> List[Task]:
        """جلب المهام حسب الحالة"""
        return self.get_all(status=status, limit=limit)

    def get_due_today(self) -> List[Task]:
        """جلب المهام المستحقة اليوم"""
        try:
            columns, rows = select_all(
                "SELECT * FROM tasks_due_today"
            )
            if not rows:
                return []
            return [Task.from_row(row, columns) for row in rows]
        except Exception as e:
            app_logger.error(f"Failed to get tasks due today: {e}")
            return []

    def get_overdue(self) -> List[Task]:
        """جلب المهام المتأخرة"""
        try:
            columns, rows = select_all(
                "SELECT * FROM tasks_overdue"
            )
            if not rows:
                return []
            return [Task.from_row(row, columns) for row in rows]
        except Exception as e:
            app_logger.error(f"Failed to get overdue tasks: {e}")
            return []

    def get_statistics(self) -> TaskStatistics:
        """جلب إحصائيات المهام"""
        try:
            columns, row = select_one("SELECT * FROM task_statistics")
            if not row:
                return TaskStatistics()
            return TaskStatistics.from_row(row, columns)
        except Exception as e:
            app_logger.error(f"Failed to get task statistics: {e}")
            return TaskStatistics()

    def get_by_employee(self, employee_id: int, include_completed: bool = False) -> List[Task]:
        """جلب مهام موظف معين"""
        if include_completed:
            return self.get_all(employee_id=employee_id)
        # Return PENDING and IN_PROGRESS tasks (exclude COMPLETED and CANCELLED)
        all_tasks = self.get_all(employee_id=employee_id)
        return [
            t for t in all_tasks
            if t.status not in (TaskStatus.COMPLETED, TaskStatus.CANCELLED)
        ]

    def get_recurring(self) -> List[Task]:
        """جلب المهام المتكررة"""
        return self.get_all(is_recurring=True)

    def get_by_source_email(self, email_id: str) -> List[Task]:
        """جلب المهام المرتبطة بإيميل معين"""
        try:
            columns, rows = select_all(
                "SELECT * FROM task_overview WHERE source_email_id = %s",
                (email_id,)
            )
            if not rows:
                return []
            return [Task.from_row(row, columns) for row in rows]
        except Exception as e:
            app_logger.error(f"Failed to get tasks by email {email_id}: {e}")
            return []

    def get_by_due_date(self, target_date) -> List[Task]:
        """جلب المهام المستحقة في تاريخ معين"""
        try:
            columns, rows = select_all(
                "SELECT * FROM task_overview WHERE due_date::date = %s",
                (target_date,)
            )
            if not rows:
                return []
            return [Task.from_row(row, columns) for row in rows]
        except Exception as e:
            app_logger.error(f"Failed to get tasks by due date {target_date}: {e}")
            return []

    def get_by_due_date_range(self, start_date, end_date) -> List[Task]:
        """جلب المهام المستحقة في فترة زمنية"""
        try:
            columns, rows = select_all(
                "SELECT * FROM task_overview WHERE due_date::date BETWEEN %s AND %s",
                (start_date, end_date)
            )
            if not rows:
                return []
            return [Task.from_row(row, columns) for row in rows]
        except Exception as e:
            app_logger.error(f"Failed to get tasks by date range: {e}")
            return []

    def search(self, query: str, limit: int = 50) -> List[Task]:
        """البحث في المهام"""
        return self.get_all(search=query, limit=limit)

    # ═══════════════════════════════════════════════════════════════
    # الإنشاء - Create Operations
    # ═══════════════════════════════════════════════════════════════

    def create(self, task: Task) -> Optional[int]:
        """
        إنشاء مهمة جديدة

        Args:
            task: نموذج المهمة

        Returns:
            معرف المهمة الجديدة أو None
        """
        try:
            task_id = insert_returning_id(
                """
                INSERT INTO tasks (
                    title, description, status, priority, category,
                    parent_task_id, source_email_id, employee_id, assigned_to,
                    due_date, reminder_date, start_date,
                    is_recurring, recurrence_pattern, next_occurrence,
                    ai_analysis, ai_suggested_action, ai_priority_score,
                    tags, metadata, created_by
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s
                )
                """,
                (
                    task.title,
                    task.description,
                    task.status.value,
                    task.priority.value,
                    task.category,
                    task.parent_task_id,
                    task.source_email_id,
                    task.employee_id,
                    task.assigned_to,
                    task.due_date,
                    task.reminder_date,
                    task.start_date,
                    task.is_recurring,
                    json.dumps(task.recurrence_pattern.to_dict()) if task.recurrence_pattern else None,
                    task.next_occurrence,
                    json.dumps(task.ai_analysis.to_dict()) if task.ai_analysis else None,
                    task.ai_suggested_action,
                    task.ai_priority_score,
                    task.tags or [],
                    json.dumps(task.metadata) if task.metadata else None,
                    task.created_by
                )
            )

            if task_id:
                app_logger.info(f"Task created: {task_id} - {task.title}")

                # إضافة عناصر قائمة التحقق
                for item in task.checklist:
                    self.add_checklist_item(task_id, item.title, item.sort_order)

            return task_id

        except Exception as e:
            app_logger.error(f"Failed to create task: {e}")
            return None

    def create_from_email(
        self,
        email_id: str,
        title: str,
        description: str,
        ai_analysis: Optional[AIAnalysis] = None
    ) -> Optional[int]:
        """
        إنشاء مهمة من إيميل

        Args:
            email_id: معرف الإيميل
            title: عنوان المهمة
            description: وصف المهمة
            ai_analysis: تحليل AI

        Returns:
            معرف المهمة
        """
        task = Task(
            title=title,
            description=description,
            source_email_id=email_id,
            status=TaskStatus.PENDING,
            priority=ai_analysis.suggested_priority if ai_analysis else TaskPriority.NORMAL,
            category=ai_analysis.suggested_category.value if ai_analysis and ai_analysis.suggested_category else "general",
            ai_analysis=ai_analysis,
            ai_suggested_action=ai_analysis.suggested_action if ai_analysis else None
        )
        return self.create(task)

    # ═══════════════════════════════════════════════════════════════
    # التحديث - Update Operations
    # ═══════════════════════════════════════════════════════════════

    def update(self, task: Task) -> bool:
        """
        تحديث مهمة

        Args:
            task: نموذج المهمة المحدثة

        Returns:
            True إذا نجح التحديث
        """
        if not task.id:
            return False

        try:
            count = update_returning_count(
                """
                UPDATE tasks SET
                    title = %s,
                    description = %s,
                    status = %s,
                    priority = %s,
                    category = %s,
                    parent_task_id = %s,
                    employee_id = %s,
                    assigned_to = %s,
                    due_date = %s,
                    reminder_date = %s,
                    start_date = %s,
                    is_recurring = %s,
                    recurrence_pattern = %s,
                    next_occurrence = %s,
                    ai_analysis = %s,
                    ai_suggested_action = %s,
                    ai_priority_score = %s,
                    tags = %s,
                    metadata = %s,
                    updated_by = %s
                WHERE id = %s
                """,
                (
                    task.title,
                    task.description,
                    task.status.value,
                    task.priority.value,
                    task.category,
                    task.parent_task_id,
                    task.employee_id,
                    task.assigned_to,
                    task.due_date,
                    task.reminder_date,
                    task.start_date,
                    task.is_recurring,
                    json.dumps(task.recurrence_pattern.to_dict()) if task.recurrence_pattern else None,
                    task.next_occurrence,
                    json.dumps(task.ai_analysis.to_dict()) if task.ai_analysis else None,
                    task.ai_suggested_action,
                    task.ai_priority_score,
                    task.tags or [],
                    json.dumps(task.metadata) if task.metadata else None,
                    task.updated_by,
                    task.id
                )
            )

            if count > 0:
                app_logger.info(f"Task updated: {task.id}")
                return True
            return False

        except Exception as e:
            app_logger.error(f"Failed to update task {task.id}: {e}")
            return False

    def change_status(
        self,
        task_id: int,
        new_status: TaskStatus,
        user_id: Optional[int] = None
    ) -> bool:
        """
        تغيير حالة المهمة

        Args:
            task_id: معرف المهمة
            new_status: الحالة الجديدة
            user_id: معرف المستخدم

        Returns:
            True إذا نجح التحديث
        """
        try:
            count = update_returning_count(
                """
                UPDATE tasks
                SET status = %s, updated_by = %s
                WHERE id = %s
                """,
                (new_status.value, user_id, task_id)
            )

            if count > 0:
                app_logger.info(f"Task {task_id} status changed to {new_status.value}")
                return True
            return False

        except Exception as e:
            app_logger.error(f"Failed to change task status: {e}")
            return False

    def change_priority(
        self,
        task_id: int,
        new_priority: TaskPriority,
        user_id: Optional[int] = None
    ) -> bool:
        """تغيير أولوية المهمة"""
        try:
            count = update_returning_count(
                """
                UPDATE tasks
                SET priority = %s, updated_by = %s
                WHERE id = %s
                """,
                (new_priority.value, user_id, task_id)
            )
            return count > 0
        except Exception as e:
            app_logger.error(f"Failed to change task priority: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════
    # الحذف - Delete Operations
    # ═══════════════════════════════════════════════════════════════

    def delete(self, task_id: int) -> bool:
        """
        حذف مهمة

        Args:
            task_id: معرف المهمة

        Returns:
            True إذا نجح الحذف
        """
        try:
            count = delete_returning_count(
                "DELETE FROM tasks WHERE id = %s",
                (task_id,)
            )

            if count > 0:
                app_logger.info(f"Task deleted: {task_id}")
                return True
            return False

        except Exception as e:
            app_logger.error(f"Failed to delete task {task_id}: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════
    # قائمة التحقق - Checklist Operations
    # ═══════════════════════════════════════════════════════════════

    def get_checklist(self, task_id: int) -> List[ChecklistItem]:
        """جلب قائمة التحقق لمهمة"""
        try:
            columns, rows = select_all(
                """
                SELECT * FROM task_checklist
                WHERE task_id = %s
                ORDER BY sort_order, id
                """,
                (task_id,)
            )
            if not rows:
                return []

            items = []
            for row in rows:
                data = dict(zip(columns, row))
                items.append(ChecklistItem(
                    id=data.get("id"),
                    task_id=data.get("task_id"),
                    title=data.get("title", ""),
                    is_completed=data.get("is_completed", False),
                    completed_at=data.get("completed_at"),
                    sort_order=data.get("sort_order", 0),
                    created_at=data.get("created_at")
                ))
            return items

        except Exception as e:
            app_logger.error(f"Failed to get checklist: {e}")
            return []

    def add_checklist_item(
        self,
        task_id: int,
        title: str,
        sort_order: int = 0
    ) -> Optional[int]:
        """إضافة عنصر لقائمة التحقق"""
        try:
            item_id = insert_returning_id(
                """
                INSERT INTO task_checklist (task_id, title, sort_order)
                VALUES (%s, %s, %s)
                """,
                (task_id, title, sort_order)
            )
            return item_id
        except Exception as e:
            app_logger.error(f"Failed to add checklist item: {e}")
            return None

    def toggle_checklist_item(self, item_id: int) -> bool:
        """تبديل حالة عنصر قائمة التحقق"""
        try:
            count = update_returning_count(
                """
                UPDATE task_checklist
                SET is_completed = NOT is_completed,
                    completed_at = CASE WHEN is_completed THEN NULL ELSE NOW() END
                WHERE id = %s
                """,
                (item_id,)
            )
            return count > 0
        except Exception as e:
            app_logger.error(f"Failed to toggle checklist item: {e}")
            return False

    def delete_checklist_item(self, item_id: int) -> bool:
        """حذف عنصر من قائمة التحقق"""
        try:
            count = delete_returning_count(
                "DELETE FROM task_checklist WHERE id = %s",
                (item_id,)
            )
            return count > 0
        except Exception as e:
            app_logger.error(f"Failed to delete checklist item: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════
    # المرفقات - Attachment Operations
    # ═══════════════════════════════════════════════════════════════

    def get_attachments(self, task_id: int) -> List[TaskAttachment]:
        """جلب مرفقات مهمة"""
        try:
            columns, rows = select_all(
                "SELECT * FROM task_attachments WHERE task_id = %s ORDER BY created_at DESC",
                (task_id,)
            )
            if not rows:
                return []

            attachments = []
            for row in rows:
                data = dict(zip(columns, row))
                attachments.append(TaskAttachment(
                    id=data.get("id"),
                    task_id=data.get("task_id"),
                    file_name=data.get("file_name", ""),
                    file_path=data.get("file_path", ""),
                    file_size=data.get("file_size"),
                    file_type=data.get("file_type"),
                    created_at=data.get("created_at")
                ))
            return attachments

        except Exception as e:
            app_logger.error(f"Failed to get attachments: {e}")
            return []

    def add_attachment(
        self,
        task_id: int,
        file_name: str,
        file_path: str,
        file_size: Optional[int] = None,
        file_type: Optional[str] = None
    ) -> Optional[int]:
        """إضافة مرفق"""
        try:
            att_id = insert_returning_id(
                """
                INSERT INTO task_attachments (task_id, file_name, file_path, file_size, file_type)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (task_id, file_name, file_path, file_size, file_type)
            )
            return att_id
        except Exception as e:
            app_logger.error(f"Failed to add attachment: {e}")
            return None

    def delete_attachment(self, attachment_id: int) -> bool:
        """حذف مرفق"""
        try:
            count = delete_returning_count(
                "DELETE FROM task_attachments WHERE id = %s",
                (attachment_id,)
            )
            return count > 0
        except Exception as e:
            app_logger.error(f"Failed to delete attachment: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════
    # التعليقات - Comment Operations
    # ═══════════════════════════════════════════════════════════════

    def get_comments(self, task_id: int) -> List[TaskComment]:
        """جلب تعليقات مهمة"""
        try:
            columns, rows = select_all(
                "SELECT * FROM task_comments WHERE task_id = %s ORDER BY created_at DESC",
                (task_id,)
            )
            if not rows:
                return []

            comments = []
            for row in rows:
                data = dict(zip(columns, row))
                comments.append(TaskComment(
                    id=data.get("id"),
                    task_id=data.get("task_id"),
                    content=data.get("content", ""),
                    created_by=data.get("created_by"),
                    created_at=data.get("created_at"),
                    updated_at=data.get("updated_at")
                ))
            return comments

        except Exception as e:
            app_logger.error(f"Failed to get comments: {e}")
            return []

    def add_comment(
        self,
        task_id: int,
        content: str,
        user_id: Optional[int] = None
    ) -> Optional[int]:
        """إضافة تعليق"""
        try:
            comment_id = insert_returning_id(
                """
                INSERT INTO task_comments (task_id, content, created_by)
                VALUES (%s, %s, %s)
                """,
                (task_id, content, user_id)
            )
            return comment_id
        except Exception as e:
            app_logger.error(f"Failed to add comment: {e}")
            return None

    def delete_comment(self, comment_id: int) -> bool:
        """حذف تعليق"""
        try:
            count = delete_returning_count(
                "DELETE FROM task_comments WHERE id = %s",
                (comment_id,)
            )
            return count > 0
        except Exception as e:
            app_logger.error(f"Failed to delete comment: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════
    # التصنيفات - Category Operations
    # ═══════════════════════════════════════════════════════════════

    def get_categories(self) -> List[Dict[str, Any]]:
        """جلب تصنيفات المهام"""
        try:
            columns, rows = select_all(
                "SELECT * FROM task_categories WHERE is_active = TRUE ORDER BY sort_order"
            )
            if not rows:
                return []

            return [dict(zip(columns, row)) for row in rows]

        except Exception as e:
            app_logger.error(f"Failed to get categories: {e}")
            return []


# ═══════════════════════════════════════════════════════════════
# Singleton & Quick Access Functions
# ═══════════════════════════════════════════════════════════════

_repository: Optional[TaskRepository] = None


def get_task_repository() -> TaskRepository:
    """الحصول على instance المستودع"""
    global _repository
    if _repository is None:
        _repository = TaskRepository()
    return _repository


# Quick access functions
def get_all_tasks(**kwargs) -> List[Task]:
    """جلب كل المهام"""
    return get_task_repository().get_all(**kwargs)


def get_task_by_id(task_id: int) -> Optional[Task]:
    """جلب مهمة بالمعرف"""
    return get_task_repository().get_by_id(task_id)


def get_tasks_by_status(status: TaskStatus, limit: int = 50) -> List[Task]:
    """جلب المهام حسب الحالة"""
    return get_task_repository().get_by_status(status, limit)


def get_tasks_due_today() -> List[Task]:
    """جلب المهام المستحقة اليوم"""
    return get_task_repository().get_due_today()


def get_overdue_tasks() -> List[Task]:
    """جلب المهام المتأخرة"""
    return get_task_repository().get_overdue()


def get_tasks_by_source_email(email_id: str) -> List[Task]:
    """جلب المهام المرتبطة بإيميل"""
    return get_task_repository().get_by_source_email(email_id)


def get_tasks_by_due_date(target_date) -> List[Task]:
    """جلب المهام المستحقة في تاريخ معين"""
    return get_task_repository().get_by_due_date(target_date)


def get_tasks_by_due_date_range(start_date, end_date) -> List[Task]:
    """جلب المهام المستحقة في فترة زمنية"""
    return get_task_repository().get_by_due_date_range(start_date, end_date)


def get_task_statistics() -> TaskStatistics:
    """جلب إحصائيات المهام"""
    return get_task_repository().get_statistics()


def create_task(task: Task) -> Optional[int]:
    """إنشاء مهمة"""
    return get_task_repository().create(task)


def update_task(task: Task) -> bool:
    """تحديث مهمة"""
    return get_task_repository().update(task)


def delete_task(task_id: int) -> bool:
    """حذف مهمة"""
    return get_task_repository().delete(task_id)


def change_task_status(task_id: int, new_status: TaskStatus, user_id: Optional[int] = None) -> bool:
    """تغيير حالة المهمة"""
    return get_task_repository().change_status(task_id, new_status, user_id)


def add_checklist_item(task_id: int, title: str, sort_order: int = 0) -> Optional[int]:
    """إضافة عنصر لقائمة التحقق"""
    return get_task_repository().add_checklist_item(task_id, title, sort_order)


def toggle_checklist_item(item_id: int) -> bool:
    """تبديل حالة عنصر قائمة التحقق"""
    return get_task_repository().toggle_checklist_item(item_id)


def delete_checklist_item(item_id: int) -> bool:
    """حذف عنصر من قائمة التحقق"""
    return get_task_repository().delete_checklist_item(item_id)


def setup_tasks_schema() -> bool:
    """إعداد جداول المهام"""
    return get_task_repository().setup_schema()
