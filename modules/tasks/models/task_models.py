"""
INTEGRA - Task Models
موديول المهام - نماذج البيانات
المحور H

التاريخ: 4 فبراير 2026
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Optional, List, Dict, Any
import json


# ═══════════════════════════════════════════════════════════════
# Enums - التعدادات
# ═══════════════════════════════════════════════════════════════

class TaskStatus(Enum):
    """حالات المهمة"""
    PENDING = "pending"           # قيد الانتظار
    IN_PROGRESS = "in_progress"   # قيد التنفيذ
    COMPLETED = "completed"       # مكتمل
    CANCELLED = "cancelled"       # ملغي

    @property
    def label_ar(self) -> str:
        labels = {
            "pending": "قيد الانتظار",
            "in_progress": "قيد التنفيذ",
            "completed": "مكتمل",
            "cancelled": "ملغي"
        }
        return labels.get(self.value, self.value)

    @property
    def color(self) -> str:
        colors = {
            "pending": "#6c757d",      # رمادي
            "in_progress": "#007bff",  # أزرق
            "completed": "#28a745",    # أخضر
            "cancelled": "#dc3545"     # أحمر
        }
        return colors.get(self.value, "#6c757d")


class TaskPriority(Enum):
    """أولويات المهمة"""
    URGENT = "urgent"   # عاجل
    HIGH = "high"       # مرتفع
    NORMAL = "normal"   # عادي
    LOW = "low"         # منخفض

    @property
    def label_ar(self) -> str:
        labels = {
            "urgent": "عاجل",
            "high": "مرتفع",
            "normal": "عادي",
            "low": "منخفض"
        }
        return labels.get(self.value, self.value)

    @property
    def color(self) -> str:
        colors = {
            "urgent": "#dc3545",  # أحمر
            "high": "#fd7e14",    # برتقالي
            "normal": "#007bff",  # أزرق
            "low": "#6c757d"      # رمادي
        }
        return colors.get(self.value, "#6c757d")

    @property
    def sort_order(self) -> int:
        orders = {"urgent": 1, "high": 2, "normal": 3, "low": 4}
        return orders.get(self.value, 3)


class RecurrenceType(Enum):
    """أنماط التكرار"""
    DAILY = "daily"       # يومي
    WEEKLY = "weekly"     # أسبوعي
    MONTHLY = "monthly"   # شهري
    YEARLY = "yearly"     # سنوي

    @property
    def label_ar(self) -> str:
        labels = {
            "daily": "يومي",
            "weekly": "أسبوعي",
            "monthly": "شهري",
            "yearly": "سنوي"
        }
        return labels.get(self.value, self.value)


class TaskCategory(Enum):
    """تصنيفات المهام"""
    GENERAL = "general"       # عام
    HR = "hr"                 # الموارد البشرية
    FINANCE = "finance"       # المالية
    OPERATIONS = "operations" # العمليات
    IT = "it"                 # تقنية المعلومات
    LEGAL = "legal"           # الشؤون القانونية
    ADMIN = "admin"           # الإدارة
    PERSONAL = "personal"     # شخصي

    @property
    def label_ar(self) -> str:
        labels = {
            "general": "عام",
            "hr": "الموارد البشرية",
            "finance": "المالية",
            "operations": "العمليات",
            "it": "تقنية المعلومات",
            "legal": "الشؤون القانونية",
            "admin": "الإدارة",
            "personal": "شخصي"
        }
        return labels.get(self.value, self.value)

    @property
    def color(self) -> str:
        colors = {
            "general": "#6c757d",
            "hr": "#28a745",
            "finance": "#ffc107",
            "operations": "#17a2b8",
            "it": "#6610f2",
            "legal": "#dc3545",
            "admin": "#fd7e14",
            "personal": "#20c997"
        }
        return colors.get(self.value, "#6c757d")


# ═══════════════════════════════════════════════════════════════
# Data Classes - نماذج البيانات
# ═══════════════════════════════════════════════════════════════

@dataclass
class RecurrencePattern:
    """نمط التكرار"""
    type: RecurrenceType
    interval: int = 1                         # كل كم (يوم/أسبوع/شهر)
    days_of_week: Optional[List[str]] = None  # أيام الأسبوع (للأسبوعي)
    day_of_month: Optional[int] = None        # يوم الشهر (للشهري)
    month_of_year: Optional[int] = None       # شهر السنة (للسنوي)
    end_type: str = "never"                   # never, count, date
    end_count: Optional[int] = None           # عدد التكرارات
    end_date: Optional[date] = None           # تاريخ الانتهاء

    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            "type": self.type.value,
            "interval": self.interval,
            "days_of_week": self.days_of_week,
            "day_of_month": self.day_of_month,
            "month_of_year": self.month_of_year,
            "end_type": self.end_type,
            "end_count": self.end_count,
            "end_date": self.end_date.isoformat() if self.end_date else None
        }

    def to_json(self) -> str:
        """تحويل إلى JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecurrencePattern":
        """إنشاء من قاموس"""
        return cls(
            type=RecurrenceType(data.get("type", "daily")),
            interval=data.get("interval", 1),
            days_of_week=data.get("days_of_week"),
            day_of_month=data.get("day_of_month"),
            month_of_year=data.get("month_of_year"),
            end_type=data.get("end_type", "never"),
            end_count=data.get("end_count"),
            end_date=date.fromisoformat(data["end_date"]) if data.get("end_date") else None
        )

    @classmethod
    def from_json(cls, json_str: str) -> "RecurrencePattern":
        """إنشاء من JSON"""
        return cls.from_dict(json.loads(json_str))


@dataclass
class ChecklistItem:
    """عنصر قائمة التحقق"""
    id: Optional[int] = None
    task_id: Optional[int] = None
    title: str = ""
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    sort_order: int = 0
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "title": self.title,
            "is_completed": self.is_completed,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "sort_order": self.sort_order
        }


@dataclass
class TaskAttachment:
    """مرفق المهمة"""
    id: Optional[int] = None
    task_id: Optional[int] = None
    file_name: str = ""
    file_path: str = ""
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "file_type": self.file_type
        }

    @property
    def file_size_formatted(self) -> str:
        """حجم الملف منسق"""
        if not self.file_size:
            return "غير معروف"
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"


@dataclass
class TaskComment:
    """تعليق على المهمة"""
    id: Optional[int] = None
    task_id: Optional[int] = None
    content: str = ""
    created_by: Optional[int] = None
    created_by_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "content": self.content,
            "created_by": self.created_by,
            "created_by_name": self.created_by_name,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class AIAnalysis:
    """تحليل AI للمهمة"""
    suggested_priority: Optional[TaskPriority] = None
    suggested_category: Optional[TaskCategory] = None
    suggested_due_date: Optional[datetime] = None
    suggested_action: Optional[str] = None
    priority_score: float = 0.5  # 0-1
    keywords: List[str] = field(default_factory=list)
    related_employee_ids: List[int] = field(default_factory=list)
    confidence: float = 0.0  # 0-1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "suggested_priority": self.suggested_priority.value if self.suggested_priority else None,
            "suggested_category": self.suggested_category.value if self.suggested_category else None,
            "suggested_due_date": self.suggested_due_date.isoformat() if self.suggested_due_date else None,
            "suggested_action": self.suggested_action,
            "priority_score": self.priority_score,
            "keywords": self.keywords,
            "related_employee_ids": self.related_employee_ids,
            "confidence": self.confidence
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AIAnalysis":
        return cls(
            suggested_priority=TaskPriority(data["suggested_priority"]) if data.get("suggested_priority") else None,
            suggested_category=TaskCategory(data["suggested_category"]) if data.get("suggested_category") else None,
            suggested_due_date=datetime.fromisoformat(data["suggested_due_date"]) if data.get("suggested_due_date") else None,
            suggested_action=data.get("suggested_action"),
            priority_score=data.get("priority_score", 0.5),
            keywords=data.get("keywords", []),
            related_employee_ids=data.get("related_employee_ids", []),
            confidence=data.get("confidence", 0.0)
        )


@dataclass
class Task:
    """نموذج المهمة الرئيسي"""
    # الهوية
    id: Optional[int] = None

    # البيانات الأساسية
    title: str = ""
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    category: Optional[str] = None

    # الروابط
    parent_task_id: Optional[int] = None
    source_email_id: Optional[str] = None
    employee_id: Optional[int] = None
    assigned_to: Optional[int] = None

    # البيانات المرتبطة (للعرض)
    employee_name: Optional[str] = None
    parent_task_title: Optional[str] = None
    category_ar: Optional[str] = None
    category_color: Optional[str] = None

    # التواريخ
    due_date: Optional[datetime] = None
    reminder_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # التكرار
    is_recurring: bool = False
    recurrence_pattern: Optional[RecurrencePattern] = None
    next_occurrence: Optional[date] = None

    # AI
    ai_analysis: Optional[AIAnalysis] = None
    ai_suggested_action: Optional[str] = None
    ai_priority_score: Optional[float] = None

    # البيانات الإضافية
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # العناصر المرتبطة
    checklist: List[ChecklistItem] = field(default_factory=list)
    attachments: List[TaskAttachment] = field(default_factory=list)
    comments: List[TaskComment] = field(default_factory=list)

    # الإحصائيات (للعرض)
    checklist_count: int = 0
    checklist_completed: int = 0
    attachments_count: int = 0
    comments_count: int = 0

    # تتبع التغييرات
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس للحفظ"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "category": self.category,
            "parent_task_id": self.parent_task_id,
            "source_email_id": self.source_email_id,
            "employee_id": self.employee_id,
            "assigned_to": self.assigned_to,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "reminder_date": self.reminder_date.isoformat() if self.reminder_date else None,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "is_recurring": self.is_recurring,
            "recurrence_pattern": self.recurrence_pattern.to_dict() if self.recurrence_pattern else None,
            "next_occurrence": self.next_occurrence.isoformat() if self.next_occurrence else None,
            "ai_analysis": self.ai_analysis.to_dict() if self.ai_analysis else None,
            "ai_suggested_action": self.ai_suggested_action,
            "ai_priority_score": self.ai_priority_score,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_by": self.created_by,
            "updated_by": self.updated_by
        }

    @classmethod
    def from_row(cls, row: tuple, columns: List[str]) -> "Task":
        """إنشاء من صف قاعدة البيانات"""
        data = dict(zip(columns, row))

        task = cls(
            id=data.get("id"),
            title=data.get("title", ""),
            description=data.get("description"),
            status=TaskStatus(data.get("status", "pending")),
            priority=TaskPriority(data.get("priority", "normal")),
            category=data.get("category"),
            parent_task_id=data.get("parent_task_id"),
            source_email_id=data.get("source_email_id"),
            employee_id=data.get("employee_id"),
            assigned_to=data.get("assigned_to"),
            employee_name=data.get("employee_name"),
            parent_task_title=data.get("parent_task_title"),
            category_ar=data.get("category_ar"),
            category_color=data.get("category_color"),
            due_date=data.get("due_date"),
            reminder_date=data.get("reminder_date"),
            start_date=data.get("start_date"),
            completed_at=data.get("completed_at"),
            is_recurring=data.get("is_recurring", False),
            next_occurrence=data.get("next_occurrence"),
            ai_suggested_action=data.get("ai_suggested_action"),
            ai_priority_score=data.get("ai_priority_score"),
            tags=data.get("tags") or [],
            checklist_count=data.get("checklist_count", 0),
            checklist_completed=data.get("checklist_completed", 0),
            attachments_count=data.get("attachments_count", 0),
            comments_count=data.get("comments_count", 0),
            created_by=data.get("created_by"),
            updated_by=data.get("updated_by"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )

        # تحليل JSON
        if data.get("recurrence_pattern"):
            pattern_data = data["recurrence_pattern"]
            if isinstance(pattern_data, str):
                pattern_data = json.loads(pattern_data)
            task.recurrence_pattern = RecurrencePattern.from_dict(pattern_data)

        if data.get("ai_analysis"):
            analysis_data = data["ai_analysis"]
            if isinstance(analysis_data, str):
                analysis_data = json.loads(analysis_data)
            task.ai_analysis = AIAnalysis.from_dict(analysis_data)

        if data.get("metadata"):
            metadata = data["metadata"]
            if isinstance(metadata, str):
                task.metadata = json.loads(metadata)
            else:
                task.metadata = metadata

        return task

    # ═══════════════════════════════════════════════════════════════
    # Properties - الخصائص
    # ═══════════════════════════════════════════════════════════════

    @property
    def is_overdue(self) -> bool:
        """هل المهمة متأخرة؟"""
        if self.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            return False
        if not self.due_date:
            return False
        return datetime.now() > self.due_date

    @property
    def is_due_today(self) -> bool:
        """هل المهمة مستحقة اليوم؟"""
        if not self.due_date:
            return False
        return self.due_date.date() == date.today()

    @property
    def is_due_soon(self) -> bool:
        """هل المهمة مستحقة قريباً (خلال 3 أيام)؟"""
        if not self.due_date:
            return False
        days_until_due = (self.due_date.date() - date.today()).days
        return 0 <= days_until_due <= 3

    @property
    def checklist_progress(self) -> float:
        """نسبة إكمال قائمة التحقق (0-100)"""
        if self.checklist_count == 0:
            return 0
        return (self.checklist_completed / self.checklist_count) * 100

    @property
    def status_label(self) -> str:
        """تسمية الحالة بالعربي"""
        return self.status.label_ar

    @property
    def priority_label(self) -> str:
        """تسمية الأولوية بالعربي"""
        return self.priority.label_ar

    @property
    def due_date_formatted(self) -> str:
        """تاريخ الاستحقاق منسق"""
        if not self.due_date:
            return "غير محدد"

        today = date.today()
        due = self.due_date.date()

        if due == today:
            return "اليوم"
        elif due == today.replace(day=today.day + 1) if today.day < 28 else today:
            return "غداً"
        elif self.is_overdue:
            days = (today - due).days
            return f"متأخر {days} يوم"
        else:
            return self.due_date.strftime("%Y-%m-%d")


@dataclass
class TaskStatistics:
    """إحصائيات المهام"""
    pending_count: int = 0
    in_progress_count: int = 0
    completed_count: int = 0
    cancelled_count: int = 0
    overdue_count: int = 0
    due_today_count: int = 0
    urgent_count: int = 0
    recurring_count: int = 0
    total_count: int = 0

    @property
    def active_count(self) -> int:
        """عدد المهام النشطة"""
        return self.pending_count + self.in_progress_count

    @property
    def completion_rate(self) -> float:
        """نسبة الإكمال"""
        if self.total_count == 0:
            return 0
        return (self.completed_count / self.total_count) * 100

    @classmethod
    def from_row(cls, row: tuple, columns: List[str]) -> "TaskStatistics":
        """إنشاء من صف قاعدة البيانات"""
        data = dict(zip(columns, row))
        return cls(
            pending_count=data.get("pending_count", 0),
            in_progress_count=data.get("in_progress_count", 0),
            completed_count=data.get("completed_count", 0),
            cancelled_count=data.get("cancelled_count", 0),
            overdue_count=data.get("overdue_count", 0),
            due_today_count=data.get("due_today_count", 0),
            urgent_count=data.get("urgent_count", 0),
            recurring_count=data.get("recurring_count", 0),
            total_count=data.get("total_count", 0)
        )
