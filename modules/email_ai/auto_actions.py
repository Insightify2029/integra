"""
G5: Auto-Actions
=================
إجراءات تلقائية للإيميلات.

Features:
- نقل تلقائي للمجلدات حسب القواعد
- أرشفة ذكية للإيميلات القديمة
- متابعة تلقائية للإيميلات بدون رد
- تذكير بالرد على الإيميلات المعلقة
- قواعد مخصصة (rules engine)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Dict, List, Optional
import json
import os
import threading

from core.logging import app_logger

try:
    from core.email import Email
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    Email = None

from .email_assistant import (
    get_email_assistant,
    EmailClassification,
    DetailedEmailAnalysis,
)


class ConditionField(Enum):
    """حقول الشرط"""
    SENDER_EMAIL = "sender_email"
    SENDER_NAME = "sender_name"
    SUBJECT = "subject"
    BODY = "body"
    HAS_ATTACHMENTS = "has_attachments"
    IMPORTANCE = "importance"
    CLASSIFICATION = "classification"
    IS_READ = "is_read"
    FOLDER = "folder"
    RECEIVED_AGE_DAYS = "received_age_days"


class ConditionOperator(Enum):
    """عوامل المقارنة"""
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    IS_TRUE = "is_true"
    IS_FALSE = "is_false"
    IN_LIST = "in_list"


class ActionType(Enum):
    """أنواع الإجراءات"""
    MOVE_TO_FOLDER = "move_to_folder"
    MARK_AS_READ = "mark_as_read"
    MARK_AS_FLAGGED = "mark_as_flagged"
    ADD_CATEGORY = "add_category"
    CREATE_TASK = "create_task"
    CREATE_NOTIFICATION = "create_notification"
    SEND_AUTO_REPLY = "send_auto_reply"
    ARCHIVE = "archive"
    FORWARD = "forward"
    LOG_ACTION = "log_action"

    @property
    def label_ar(self) -> str:
        labels = {
            "move_to_folder": "نقل إلى مجلد",
            "mark_as_read": "تحديد كمقروء",
            "mark_as_flagged": "تحديد بعلامة",
            "add_category": "إضافة تصنيف",
            "create_task": "إنشاء مهمة",
            "create_notification": "إرسال إشعار",
            "send_auto_reply": "إرسال رد تلقائي",
            "archive": "أرشفة",
            "forward": "تحويل",
            "log_action": "تسجيل في السجل",
        }
        return labels.get(self.value, "إجراء")


@dataclass
class RuleCondition:
    """شرط قاعدة"""
    field: ConditionField
    operator: ConditionOperator
    value: str = ""

    def evaluate(self, email: 'Email', analysis: Optional[DetailedEmailAnalysis] = None) -> bool:
        """تقييم الشرط على إيميل."""
        field_value = self._get_field_value(email, analysis)

        if field_value is None:
            return False

        op = self.operator

        if op == ConditionOperator.IS_TRUE:
            return bool(field_value)
        if op == ConditionOperator.IS_FALSE:
            return not bool(field_value)

        str_value = str(field_value).lower()
        compare_value = self.value.lower()

        if op == ConditionOperator.CONTAINS:
            return compare_value in str_value
        if op == ConditionOperator.NOT_CONTAINS:
            return compare_value not in str_value
        if op == ConditionOperator.EQUALS:
            return str_value == compare_value
        if op == ConditionOperator.NOT_EQUALS:
            return str_value != compare_value
        if op == ConditionOperator.STARTS_WITH:
            return str_value.startswith(compare_value)
        if op == ConditionOperator.ENDS_WITH:
            return str_value.endswith(compare_value)
        if op == ConditionOperator.IN_LIST:
            items = [i.strip().lower() for i in self.value.split(',')]
            return str_value in items

        # Numeric comparisons
        try:
            num_field = float(str_value)
            num_compare = float(compare_value)
            if op == ConditionOperator.GREATER_THAN:
                return num_field > num_compare
            if op == ConditionOperator.LESS_THAN:
                return num_field < num_compare
        except (ValueError, TypeError):
            pass

        return False

    def _get_field_value(self, email: 'Email', analysis: Optional[DetailedEmailAnalysis]):
        """الحصول على قيمة الحقل."""
        f = self.field

        if f == ConditionField.SENDER_EMAIL:
            return email.sender_email or ""
        if f == ConditionField.SENDER_NAME:
            return email.sender_name or ""
        if f == ConditionField.SUBJECT:
            return email.subject or ""
        if f == ConditionField.BODY:
            return (email.body or "")[:2000]
        if f == ConditionField.HAS_ATTACHMENTS:
            return email.has_attachments
        if f == ConditionField.IMPORTANCE:
            return email.importance.value if email.importance else 1
        if f == ConditionField.IS_READ:
            return email.is_read
        if f == ConditionField.FOLDER:
            return email.folder_name or ""
        if f == ConditionField.CLASSIFICATION:
            if analysis:
                return analysis.classification.value
            return ""
        if f == ConditionField.RECEIVED_AGE_DAYS:
            if email.received_time:
                return (datetime.now() - email.received_time).days
            return 0

        return None

    def to_dict(self) -> dict:
        return {
            "field": self.field.value,
            "operator": self.operator.value,
            "value": self.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'RuleCondition':
        return cls(
            field=ConditionField(data["field"]),
            operator=ConditionOperator(data["operator"]),
            value=data.get("value", ""),
        )


@dataclass
class RuleAction:
    """إجراء قاعدة"""
    action_type: ActionType
    params: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "action_type": self.action_type.value,
            "params": self.params,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'RuleAction':
        return cls(
            action_type=ActionType(data["action_type"]),
            params=data.get("params", {}),
        )


@dataclass
class EmailRule:
    """قاعدة إيميل"""
    id: str
    name: str
    name_ar: str = ""
    description: str = ""
    is_enabled: bool = True
    conditions: List[RuleCondition] = field(default_factory=list)
    actions: List[RuleAction] = field(default_factory=list)
    match_all: bool = True  # True = AND, False = OR
    priority: int = 0
    created_at: Optional[datetime] = None
    run_count: int = 0
    last_run: Optional[datetime] = None

    def matches(self, email: 'Email', analysis: Optional[DetailedEmailAnalysis] = None) -> bool:
        """فحص تطابق القاعدة مع إيميل."""
        if not self.is_enabled or not self.conditions:
            return False

        results = [c.evaluate(email, analysis) for c in self.conditions]

        if self.match_all:
            return all(results)
        return any(results)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "name_ar": self.name_ar,
            "description": self.description,
            "is_enabled": self.is_enabled,
            "conditions": [c.to_dict() for c in self.conditions],
            "actions": [a.to_dict() for a in self.actions],
            "match_all": self.match_all,
            "priority": self.priority,
            "run_count": self.run_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'EmailRule':
        return cls(
            id=data["id"],
            name=data["name"],
            name_ar=data.get("name_ar", ""),
            description=data.get("description", ""),
            is_enabled=data.get("is_enabled", True),
            conditions=[RuleCondition.from_dict(c) for c in data.get("conditions", [])],
            actions=[RuleAction.from_dict(a) for a in data.get("actions", [])],
            match_all=data.get("match_all", True),
            priority=data.get("priority", 0),
            run_count=data.get("run_count", 0),
        )


@dataclass
class ActionResult:
    """نتيجة تنفيذ إجراء"""
    rule_id: str
    email_id: str
    action_type: ActionType
    success: bool
    message: str = ""
    executed_at: Optional[datetime] = None


class AutoActionEngine:
    """
    محرك الإجراءات التلقائية (G5)

    يُنفذ قواعد على الإيميلات تلقائياً.

    Usage:
        engine = get_auto_action_engine()
        engine.add_rule(rule)
        results = engine.process_emails(emails)
        engine.save_rules()
    """

    _instance: Optional['AutoActionEngine'] = None
    _lock = threading.Lock()

    RULES_FILE = "data/email_rules.json"

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._rules: List[EmailRule] = []
        self._rules_lock = threading.Lock()
        self._action_handlers: Dict[ActionType, Callable] = {}
        self._action_log: List[ActionResult] = []
        self._log_lock = threading.Lock()

        self._register_default_handlers()
        self._load_rules()
        self._create_default_rules()

        self._initialized = True
        app_logger.info("AutoActionEngine (G5) initialized")

    def add_rule(self, rule: EmailRule):
        """إضافة قاعدة."""
        with self._rules_lock:
            # Remove existing with same ID
            self._rules = [r for r in self._rules if r.id != rule.id]
            self._rules.append(rule)
            self._rules.sort(key=lambda r: r.priority, reverse=True)

    def remove_rule(self, rule_id: str) -> bool:
        """حذف قاعدة."""
        with self._rules_lock:
            before = len(self._rules)
            self._rules = [r for r in self._rules if r.id != rule_id]
            return len(self._rules) < before

    def get_rules(self) -> List[EmailRule]:
        """الحصول على كل القواعد."""
        with self._rules_lock:
            return list(self._rules)

    def get_rule(self, rule_id: str) -> Optional[EmailRule]:
        """الحصول على قاعدة بالمعرف."""
        with self._rules_lock:
            for rule in self._rules:
                if rule.id == rule_id:
                    return rule
        return None

    def process_emails(
        self, emails: List['Email']
    ) -> List[ActionResult]:
        """
        تطبيق القواعد على قائمة إيميلات.

        Returns:
            قائمة نتائج الإجراءات
        """
        results = []
        assistant = get_email_assistant()

        with self._rules_lock:
            rules = list(self._rules)

        for email in emails:
            analysis = assistant.analyze(email)

            for rule in rules:
                if not rule.is_enabled:
                    continue

                try:
                    if rule.matches(email, analysis):
                        rule_results = self._execute_rule(rule, email, analysis)
                        results.extend(rule_results)
                        rule.run_count += 1
                        rule.last_run = datetime.now()
                except Exception as e:
                    app_logger.error(
                        f"Rule {rule.id} failed on email {email.entry_id}: {e}"
                    )

        # Log results
        with self._log_lock:
            self._action_log.extend(results)

        return results

    def process_single_email(
        self, email: 'Email'
    ) -> List[ActionResult]:
        """تطبيق القواعد على إيميل واحد."""
        return self.process_emails([email])

    def check_follow_ups_needed(
        self,
        sent_emails: List['Email'],
        all_emails: List['Email'],
        hours_threshold: int = 48,
    ) -> List[Dict]:
        """فحص الإيميلات التي تحتاج متابعة."""
        follow_ups = []
        cutoff = datetime.now() - timedelta(hours=hours_threshold)

        # Build set of conversations with replies
        replied_conversations = {
            e.conversation_id
            for e in all_emails
            if e.conversation_id and e.folder_name
            and 'inbox' in e.folder_name.lower()
        }

        for email in sent_emails:
            if not email.sent_time or email.sent_time > cutoff:
                continue

            if email.conversation_id and email.conversation_id not in replied_conversations:
                days_since = (datetime.now() - email.sent_time).days
                follow_ups.append({
                    "email_id": email.entry_id,
                    "subject": email.subject,
                    "recipients": email.to,
                    "sent_date": email.sent_time.isoformat(),
                    "days_since": days_since,
                })

        return follow_ups

    def smart_archive(
        self,
        emails: List['Email'],
        age_days: int = 30,
        exclude_flagged: bool = True,
        exclude_unread: bool = True,
    ) -> List[str]:
        """اقتراح إيميلات للأرشفة."""
        candidates = []
        cutoff = datetime.now() - timedelta(days=age_days)

        for email in emails:
            dt = email.received_time or email.sent_time
            if not dt or dt >= cutoff:
                continue

            if exclude_flagged and email.is_flagged:
                continue
            if exclude_unread and not email.is_read:
                continue

            candidates.append(email.entry_id)

        return candidates

    def save_rules(self):
        """حفظ القواعد في ملف."""
        with self._rules_lock:
            data = [r.to_dict() for r in self._rules]

        rules_dir = os.path.dirname(self.RULES_FILE)
        if rules_dir:
            os.makedirs(rules_dir, exist_ok=True)

        try:
            with open(self.RULES_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            app_logger.info(f"Saved {len(data)} email rules")
        except Exception as e:
            app_logger.error(f"Failed to save rules: {e}")

    def get_action_log(self, limit: int = 100) -> List[ActionResult]:
        """الحصول على سجل الإجراءات."""
        with self._log_lock:
            log = list(self._action_log)
        log.sort(key=lambda r: r.executed_at or datetime.min, reverse=True)
        return log[:limit]

    # --- Private methods ---

    def _load_rules(self):
        """تحميل القواعد من ملف."""
        if not os.path.exists(self.RULES_FILE):
            return

        try:
            with open(self.RULES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)

            with self._rules_lock:
                self._rules = [EmailRule.from_dict(d) for d in data]
                self._rules.sort(key=lambda r: r.priority, reverse=True)

            app_logger.info(f"Loaded {len(self._rules)} email rules")
        except Exception as e:
            app_logger.error(f"Failed to load rules: {e}")

    def _create_default_rules(self):
        """إنشاء قواعد افتراضية."""
        with self._rules_lock:
            if self._rules:
                return

        # Rule 1: Archive newsletters
        self.add_rule(EmailRule(
            id="default_archive_newsletters",
            name="Archive Newsletters",
            name_ar="أرشفة النشرات الإخبارية",
            description="أرشفة الإيميلات التي تحتوي على رابط إلغاء اشتراك",
            conditions=[
                RuleCondition(
                    field=ConditionField.BODY,
                    operator=ConditionOperator.CONTAINS,
                    value="unsubscribe",
                ),
                RuleCondition(
                    field=ConditionField.IS_READ,
                    operator=ConditionOperator.IS_TRUE,
                ),
            ],
            actions=[
                RuleAction(
                    action_type=ActionType.ADD_CATEGORY,
                    params={"category": "newsletter"},
                ),
            ],
            match_all=True,
            priority=10,
        ))

        # Rule 2: Flag urgent
        self.add_rule(EmailRule(
            id="default_flag_urgent",
            name="Flag Urgent Emails",
            name_ar="تحديد الإيميلات العاجلة",
            description="تحديد الإيميلات العاجلة بعلامة",
            conditions=[
                RuleCondition(
                    field=ConditionField.CLASSIFICATION,
                    operator=ConditionOperator.EQUALS,
                    value="work_urgent",
                ),
            ],
            actions=[
                RuleAction(action_type=ActionType.MARK_AS_FLAGGED),
                RuleAction(
                    action_type=ActionType.CREATE_NOTIFICATION,
                    params={"priority": "urgent"},
                ),
            ],
            match_all=True,
            priority=100,
        ))

        # Rule 3: Create tasks from task requests
        self.add_rule(EmailRule(
            id="default_create_tasks",
            name="Create Tasks from Emails",
            name_ar="إنشاء مهام من الإيميلات",
            description="إنشاء مهام تلقائياً من إيميلات طلبات المهام",
            conditions=[
                RuleCondition(
                    field=ConditionField.CLASSIFICATION,
                    operator=ConditionOperator.EQUALS,
                    value="task_request",
                ),
            ],
            actions=[
                RuleAction(
                    action_type=ActionType.CREATE_TASK,
                    params={"auto_create": True},
                ),
                RuleAction(
                    action_type=ActionType.CREATE_NOTIFICATION,
                    params={"priority": "high"},
                ),
            ],
            match_all=True,
            priority=80,
        ))

    def _register_default_handlers(self):
        """تسجيل معالجات الإجراءات الافتراضية."""
        self._action_handlers = {
            ActionType.MARK_AS_READ: self._handler_mark_read,
            ActionType.MARK_AS_FLAGGED: self._handler_mark_flagged,
            ActionType.ADD_CATEGORY: self._handler_add_category,
            ActionType.CREATE_NOTIFICATION: self._handler_create_notification,
            ActionType.CREATE_TASK: self._handler_create_task,
            ActionType.ARCHIVE: self._handler_archive,
            ActionType.LOG_ACTION: self._handler_log,
        }

    def _execute_rule(
        self,
        rule: EmailRule,
        email: 'Email',
        analysis: Optional[DetailedEmailAnalysis],
    ) -> List[ActionResult]:
        """تنفيذ إجراءات قاعدة."""
        results = []

        for action in rule.actions:
            handler = self._action_handlers.get(action.action_type)
            if handler:
                try:
                    success, message = handler(email, action.params, analysis)
                    results.append(ActionResult(
                        rule_id=rule.id,
                        email_id=email.entry_id,
                        action_type=action.action_type,
                        success=success,
                        message=message,
                        executed_at=datetime.now(),
                    ))
                except Exception as e:
                    app_logger.error(f"Action handler failed: {e}")
                    results.append(ActionResult(
                        rule_id=rule.id,
                        email_id=email.entry_id,
                        action_type=action.action_type,
                        success=False,
                        message=str(e),
                        executed_at=datetime.now(),
                    ))
            else:
                app_logger.warning(f"No handler for action: {action.action_type}")

        return results

    # --- Action handlers ---

    def _handler_mark_read(
        self, email: 'Email', params: Dict, analysis: Optional[DetailedEmailAnalysis]
    ) -> tuple:
        email.is_read = True
        return True, f"تم تحديد {email.entry_id} كمقروء"

    def _handler_mark_flagged(
        self, email: 'Email', params: Dict, analysis: Optional[DetailedEmailAnalysis]
    ) -> tuple:
        email.is_flagged = True
        return True, f"تم تحديد {email.entry_id} بعلامة"

    def _handler_add_category(
        self, email: 'Email', params: Dict, analysis: Optional[DetailedEmailAnalysis]
    ) -> tuple:
        category = params.get("category", "general")
        if category not in email.categories:
            email.categories.append(category)
        return True, f"تم إضافة التصنيف '{category}' للإيميل {email.entry_id}"

    def _handler_create_notification(
        self, email: 'Email', params: Dict, analysis: Optional[DetailedEmailAnalysis]
    ) -> tuple:
        try:
            from .smart_notifications import get_email_notification_manager
            manager = get_email_notification_manager()
            manager.process_new_emails([email])
            return True, f"تم إنشاء إشعار للإيميل {email.entry_id}"
        except Exception as e:
            return False, f"فشل إنشاء الإشعار: {e}"

    def _handler_create_task(
        self, email: 'Email', params: Dict, analysis: Optional[DetailedEmailAnalysis]
    ) -> tuple:
        task_title = email.subject or "مهمة من إيميل"
        app_logger.info(
            f"Task creation requested: '{task_title}' from email {email.entry_id}"
        )
        return True, f"تم طلب إنشاء مهمة: {task_title}"

    def _handler_archive(
        self, email: 'Email', params: Dict, analysis: Optional[DetailedEmailAnalysis]
    ) -> tuple:
        app_logger.info(f"Archive requested for email {email.entry_id}")
        return True, f"تم طلب أرشفة الإيميل {email.entry_id}"

    def _handler_log(
        self, email: 'Email', params: Dict, analysis: Optional[DetailedEmailAnalysis]
    ) -> tuple:
        message = params.get("message", f"Rule triggered on {email.entry_id}")
        app_logger.info(f"Email rule log: {message}")
        return True, message


# Singleton
_engine: Optional[AutoActionEngine] = None
_engine_lock = threading.Lock()


def get_auto_action_engine() -> AutoActionEngine:
    """Get singleton AutoActionEngine."""
    global _engine
    with _engine_lock:
        if _engine is None:
            _engine = AutoActionEngine()
        return _engine
