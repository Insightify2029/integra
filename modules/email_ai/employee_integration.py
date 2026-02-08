"""
G6: Employee Integration
=========================
ربط الإيميلات بالموظفين.

Features:
- ربط الإيميل بملف الموظف تلقائياً
- سجل المراسلات لكل موظف
- تحليل تفاعلات الموظفين
- AI يعرف المرسل ويقترح إجراءات
- ملف إيميل شامل لكل موظف
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import re
import threading

from core.logging import app_logger

try:
    from core.email import Email
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    Email = None

try:
    from core.database import select_all, select_one
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

from .email_assistant import (
    get_email_assistant,
    DetailedEmailAnalysis,
    EmailClassification,
)


@dataclass
class EmployeeEmailProfile:
    """ملف إيميل شامل لموظف"""
    employee_id: int
    employee_name: str = ""
    employee_email: str = ""
    department: str = ""

    # Stats
    total_emails: int = 0
    sent_count: int = 0
    received_count: int = 0
    unread_count: int = 0

    # Recent activity
    last_email_date: Optional[datetime] = None
    last_email_subject: str = ""

    # Patterns
    avg_response_time_hours: Optional[float] = None
    most_active_hour: Optional[int] = None
    common_subjects: List[str] = field(default_factory=list)
    common_categories: Dict[str, int] = field(default_factory=dict)

    # AI Insights
    communication_score: float = 0.0  # 0-10
    relationship_summary: str = ""
    suggested_actions: List[str] = field(default_factory=list)

    # Email history
    recent_emails: List[Dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "employee_id": self.employee_id,
            "employee_name": self.employee_name,
            "employee_email": self.employee_email,
            "department": self.department,
            "total_emails": self.total_emails,
            "sent_count": self.sent_count,
            "received_count": self.received_count,
            "unread_count": self.unread_count,
            "last_email_date": self.last_email_date.isoformat() if self.last_email_date else None,
            "last_email_subject": self.last_email_subject,
            "avg_response_time_hours": self.avg_response_time_hours,
            "most_active_hour": self.most_active_hour,
            "common_subjects": self.common_subjects,
            "common_categories": self.common_categories,
            "communication_score": self.communication_score,
            "relationship_summary": self.relationship_summary,
            "suggested_actions": self.suggested_actions,
        }


@dataclass
class EmailEmployeeMatch:
    """تطابق إيميل مع موظف"""
    email_id: str
    employee_id: int
    employee_name: str
    match_type: str  # exact_email, name_match, domain_match
    confidence: float = 0.0


class EmployeeEmailLinker:
    """
    رابط الإيميلات بالموظفين (G6)

    يربط الإيميلات بملفات الموظفين ويوفر تحليلات.

    Usage:
        linker = get_employee_email_linker()
        match = linker.find_employee_for_email(email)
        profile = linker.get_employee_email_profile(employee_id, emails)
        interactions = linker.analyze_interactions(emails)
    """

    _instance: Optional['EmployeeEmailLinker'] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._employee_cache: Dict[str, Dict] = {}
        self._email_to_employee: Dict[str, int] = {}
        self._cache_lock = threading.Lock()
        self._assistant = get_email_assistant()

        self._initialized = True
        app_logger.info("EmployeeEmailLinker (G6) initialized")

    def refresh_employee_cache(self):
        """تحديث cache الموظفين من قاعدة البيانات."""
        if not DB_AVAILABLE:
            app_logger.warning("Database not available for employee lookup")
            return

        try:
            columns, rows = select_all(
                """
                SELECT e.id, e.name_ar, e.name_en, e.email,
                       d.name_ar as department_name
                FROM employees e
                LEFT JOIN departments d ON e.department_id = d.id
                WHERE e.email IS NOT NULL AND e.email != ''
                """,
            )

            if not rows:
                return

            col_map = {col: idx for idx, col in enumerate(columns)}

            with self._cache_lock:
                self._employee_cache.clear()
                self._email_to_employee.clear()

                for row in rows:
                    emp_id = row[col_map['id']]
                    emp_email = (row[col_map.get('email', 3)] or "").lower().strip()
                    emp_name_ar = row[col_map.get('name_ar', 1)] or ""
                    emp_name_en = row[col_map.get('name_en', 2)] or ""
                    department = row[col_map.get('department_name', 4)] or ""

                    if emp_email:
                        self._employee_cache[emp_email] = {
                            "id": emp_id,
                            "name_ar": emp_name_ar,
                            "name_en": emp_name_en,
                            "email": emp_email,
                            "department": department,
                        }
                        self._email_to_employee[emp_email] = emp_id

            app_logger.info(f"Employee cache refreshed: {len(self._employee_cache)} employees")

        except Exception as e:
            app_logger.error(f"Failed to refresh employee cache: {e}")

    def find_employee_for_email(
        self, email: 'Email'
    ) -> Optional[EmailEmployeeMatch]:
        """
        البحث عن الموظف المرتبط بإيميل.

        يستخدم عدة استراتيجيات:
        1. مطابقة البريد الإلكتروني بالضبط
        2. مطابقة الاسم
        3. مطابقة النطاق (domain)
        """
        if not email:
            return None

        # Ensure cache is loaded
        if not self._employee_cache:
            self.refresh_employee_cache()

        sender_email = (email.sender_email or "").lower().strip()
        sender_name = (email.sender_name or "").lower().strip()

        # Strategy 1: Exact email match
        with self._cache_lock:
            emp_id = self._email_to_employee.get(sender_email)
            if emp_id:
                emp = self._employee_cache.get(sender_email, {})
                return EmailEmployeeMatch(
                    email_id=email.entry_id,
                    employee_id=emp_id,
                    employee_name=emp.get("name_ar", ""),
                    match_type="exact_email",
                    confidence=1.0,
                )

        # Strategy 2: Name match
        if sender_name:
            match = self._match_by_name(email.entry_id, sender_name)
            if match:
                return match

        # Strategy 3: Domain match (for company emails)
        if sender_email and '@' in sender_email:
            match = self._match_by_domain(email.entry_id, sender_email, sender_name)
            if match:
                return match

        # Also check recipients for sent emails
        for recipient in email.to:
            recipient_lower = recipient.lower().strip()
            with self._cache_lock:
                emp_id = self._email_to_employee.get(recipient_lower)
                if emp_id:
                    emp = self._employee_cache.get(recipient_lower, {})
                    return EmailEmployeeMatch(
                        email_id=email.entry_id,
                        employee_id=emp_id,
                        employee_name=emp.get("name_ar", ""),
                        match_type="exact_email",
                        confidence=1.0,
                    )

        return None

    def link_emails_to_employees(
        self, emails: List['Email']
    ) -> Dict[int, List['Email']]:
        """
        ربط قائمة إيميلات بالموظفين.

        Returns:
            Dict mapping employee_id → list of related emails
        """
        employee_emails: Dict[int, List['Email']] = defaultdict(list)

        for email in emails:
            match = self.find_employee_for_email(email)
            if match:
                employee_emails[match.employee_id].append(email)

        return dict(employee_emails)

    def get_employee_email_profile(
        self, employee_id: int, emails: List['Email']
    ) -> EmployeeEmailProfile:
        """
        الحصول على ملف إيميل شامل لموظف.

        Args:
            employee_id: معرف الموظف
            emails: كل الإيميلات المتاحة
        """
        # Get employee info
        emp_info = self._get_employee_info(employee_id)
        if not emp_info:
            return EmployeeEmailProfile(employee_id=employee_id)

        emp_email = emp_info.get("email", "").lower()

        # Filter relevant emails
        emp_emails = []
        for email in emails:
            sender = (email.sender_email or "").lower()
            recipients = [r.lower() for r in (email.to or [])]

            if sender == emp_email or emp_email in recipients:
                emp_emails.append(email)

        # Build profile
        profile = EmployeeEmailProfile(
            employee_id=employee_id,
            employee_name=emp_info.get("name_ar", ""),
            employee_email=emp_email,
            department=emp_info.get("department", ""),
            total_emails=len(emp_emails),
        )

        if not emp_emails:
            return profile

        # Count sent/received
        for email in emp_emails:
            if (email.sender_email or "").lower() == emp_email:
                profile.sent_count += 1
            else:
                profile.received_count += 1
            if not email.is_read:
                profile.unread_count += 1

        # Last email
        sorted_emails = sorted(
            emp_emails,
            key=lambda e: e.received_time or e.sent_time or datetime.min,
            reverse=True,
        )
        if sorted_emails:
            last = sorted_emails[0]
            profile.last_email_date = last.received_time or last.sent_time
            profile.last_email_subject = last.subject or ""

        # Common subjects
        subjects = Counter(e.subject for e in emp_emails if e.subject)
        profile.common_subjects = [s for s, _ in subjects.most_common(5)]

        # Most active hour
        hours = Counter(
            (e.received_time or e.sent_time).hour
            for e in emp_emails
            if e.received_time or e.sent_time
        )
        if hours:
            profile.most_active_hour = hours.most_common(1)[0][0]

        # AI classification distribution
        for email in emp_emails[:50]:
            analysis = self._assistant.analyze(email)
            cat = analysis.classification.label_ar
            profile.common_categories[cat] = profile.common_categories.get(cat, 0) + 1

        # Recent emails
        for email in sorted_emails[:10]:
            profile.recent_emails.append({
                "id": email.entry_id,
                "subject": email.subject,
                "date": (email.received_time or email.sent_time or datetime.min).isoformat(),
                "is_sent": (email.sender_email or "").lower() == emp_email,
                "is_read": email.is_read,
            })

        # Communication score (based on activity)
        if profile.total_emails > 20:
            profile.communication_score = min(10.0, profile.total_emails / 10.0)
        elif profile.total_emails > 5:
            profile.communication_score = 5.0
        else:
            profile.communication_score = float(profile.total_emails)

        return profile

    def analyze_interactions(
        self, emails: List['Email']
    ) -> Dict:
        """
        تحليل تفاعلات الإيميل بين الموظفين.

        Returns:
            Dict with interaction analytics
        """
        # Link all emails
        employee_emails = self.link_emails_to_employees(emails)

        interactions = {
            "total_linked_employees": len(employee_emails),
            "total_linked_emails": sum(len(v) for v in employee_emails.values()),
            "unlinked_emails": len(emails) - sum(len(v) for v in employee_emails.values()),
            "employees": [],
        }

        for emp_id, emp_mail_list in employee_emails.items():
            emp_info = self._get_employee_info(emp_id)
            if emp_info:
                interactions["employees"].append({
                    "id": emp_id,
                    "name": emp_info.get("name_ar", ""),
                    "department": emp_info.get("department", ""),
                    "email_count": len(emp_mail_list),
                })

        # Sort by email count
        interactions["employees"].sort(
            key=lambda e: e["email_count"], reverse=True
        )

        return interactions

    def suggest_actions_for_sender(
        self, email: 'Email'
    ) -> List[Dict]:
        """
        اقتراح إجراءات بناءً على المرسل.

        AI يعرف المرسل ويقترح إجراءات مناسبة.
        """
        actions = []

        match = self.find_employee_for_email(email)
        analysis = self._assistant.analyze(email)

        if match:
            # The sender is a known employee
            emp_info = self._get_employee_info(match.employee_id)
            emp_name = emp_info.get("name_ar", "") if emp_info else ""
            department = emp_info.get("department", "") if emp_info else ""

            actions.append({
                "id": "view_employee",
                "label": f"عرض ملف {emp_name}",
                "action_type": "navigate",
                "params": {"module": "employees", "employee_id": match.employee_id},
            })

            actions.append({
                "id": "view_email_history",
                "label": f"سجل المراسلات مع {emp_name}",
                "action_type": "navigate",
                "params": {"module": "email_ai", "view": "employee_emails",
                           "employee_id": match.employee_id},
            })

            # Classification-based actions
            if analysis.classification == EmailClassification.HR_REQUEST:
                actions.append({
                    "id": "open_hr_form",
                    "label": "فتح نموذج HR",
                    "action_type": "function",
                    "params": {"action": "open_hr_form", "employee_id": match.employee_id},
                })

            if analysis.classification == EmailClassification.FINANCIAL:
                actions.append({
                    "id": "view_payroll",
                    "label": "عرض مستحقات الموظف",
                    "action_type": "navigate",
                    "params": {"module": "mostahaqat", "employee_id": match.employee_id},
                })
        else:
            # Unknown sender
            actions.append({
                "id": "add_contact",
                "label": f"إضافة {email.sender_name} كجهة اتصال",
                "action_type": "function",
                "params": {"action": "add_contact",
                           "name": email.sender_name,
                           "email": email.sender_email},
            })

        # Common actions
        if analysis.tasks:
            actions.append({
                "id": "create_tasks",
                "label": f"إنشاء {len(analysis.tasks)} مهمة",
                "action_type": "function",
                "params": {"action": "create_tasks", "email_id": email.entry_id},
            })

        if analysis.meetings:
            actions.append({
                "id": "add_meeting",
                "label": "إضافة للتقويم",
                "action_type": "function",
                "params": {"action": "add_to_calendar", "email_id": email.entry_id},
            })

        return actions

    def get_employee_correspondents(
        self, employee_id: int, emails: List['Email']
    ) -> List[Dict]:
        """الحصول على قائمة المراسلين لموظف."""
        emp_info = self._get_employee_info(employee_id)
        if not emp_info:
            return []

        emp_email = emp_info.get("email", "").lower()
        correspondents: Dict[str, Dict] = {}

        for email in emails:
            sender = (email.sender_email or "").lower()
            recipients = [r.lower() for r in (email.to or [])]

            if sender == emp_email:
                # Employee sent this email
                for recipient in recipients:
                    if recipient not in correspondents:
                        correspondents[recipient] = {
                            "email": recipient, "name": "", "sent": 0, "received": 0
                        }
                    correspondents[recipient]["sent"] += 1
            elif emp_email in recipients:
                # Employee received this email
                if sender not in correspondents:
                    correspondents[sender] = {
                        "email": sender,
                        "name": email.sender_name or sender,
                        "sent": 0, "received": 0,
                    }
                correspondents[sender]["received"] += 1
                if not correspondents[sender]["name"] or correspondents[sender]["name"] == sender:
                    correspondents[sender]["name"] = email.sender_name or sender

        result = list(correspondents.values())
        result.sort(key=lambda c: c["sent"] + c["received"], reverse=True)
        return result[:20]

    # --- Private methods ---

    def _get_employee_info(self, employee_id: int) -> Optional[Dict]:
        """الحصول على بيانات موظف."""
        # Check cache first
        with self._cache_lock:
            for emp_data in self._employee_cache.values():
                if emp_data.get("id") == employee_id:
                    return emp_data

        # Try database
        if not DB_AVAILABLE:
            return None

        try:
            columns, row = select_one(
                """
                SELECT e.id, e.name_ar, e.name_en, e.email,
                       d.name_ar as department_name
                FROM employees e
                LEFT JOIN departments d ON e.department_id = d.id
                WHERE e.id = %s
                """,
                (employee_id,),
            )

            if row:
                col_map = {col: idx for idx, col in enumerate(columns)}
                return {
                    "id": row[col_map['id']],
                    "name_ar": row[col_map.get('name_ar', 1)] or "",
                    "name_en": row[col_map.get('name_en', 2)] or "",
                    "email": (row[col_map.get('email', 3)] or "").lower(),
                    "department": row[col_map.get('department_name', 4)] or "",
                }
        except Exception as e:
            app_logger.error(f"Failed to get employee info: {e}")

        return None

    def _match_by_name(
        self, email_id: str, sender_name: str
    ) -> Optional[EmailEmployeeMatch]:
        """مطابقة بالاسم."""
        with self._cache_lock:
            for emp_email, emp_data in self._employee_cache.items():
                name_ar = (emp_data.get("name_ar") or "").lower()
                name_en = (emp_data.get("name_en") or "").lower()

                # Check if sender name contains employee name or vice versa
                if name_ar and (name_ar in sender_name or sender_name in name_ar):
                    return EmailEmployeeMatch(
                        email_id=email_id,
                        employee_id=emp_data["id"],
                        employee_name=emp_data.get("name_ar", ""),
                        match_type="name_match",
                        confidence=0.7,
                    )
                if name_en and (name_en in sender_name or sender_name in name_en):
                    return EmailEmployeeMatch(
                        email_id=email_id,
                        employee_id=emp_data["id"],
                        employee_name=emp_data.get("name_ar", ""),
                        match_type="name_match",
                        confidence=0.6,
                    )
        return None

    def _match_by_domain(
        self, email_id: str, sender_email: str, sender_name: str
    ) -> Optional[EmailEmployeeMatch]:
        """مطابقة بنطاق البريد."""
        sender_domain = sender_email.split('@')[-1] if '@' in sender_email else ''
        if not sender_domain:
            return None

        # Check if any employee shares the same domain
        with self._cache_lock:
            for emp_email, emp_data in self._employee_cache.items():
                emp_domain = emp_email.split('@')[-1] if '@' in emp_email else ''
                if emp_domain and emp_domain == sender_domain:
                    # Same domain - possible match with low confidence
                    return EmailEmployeeMatch(
                        email_id=email_id,
                        employee_id=emp_data["id"],
                        employee_name=emp_data.get("name_ar", ""),
                        match_type="domain_match",
                        confidence=0.3,
                    )
        return None


# Singleton
_linker: Optional[EmployeeEmailLinker] = None
_linker_lock = threading.Lock()


def get_employee_email_linker() -> EmployeeEmailLinker:
    """Get singleton EmployeeEmailLinker."""
    global _linker
    with _linker_lock:
        if _linker is None:
            _linker = EmployeeEmailLinker()
        return _linker
