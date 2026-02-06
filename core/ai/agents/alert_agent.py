# core/ai/agents/alert_agent.py
"""
INTEGRA - نظام التنبيهات الذكية (Smart Alerts)
===============================================

وكيل ذكي لتحليل البيانات واكتشاف الأنماط التي تحتاج انتباه.

الميزات:
- كشف العقود المنتهية أو القريبة من الانتهاء
- اكتشاف الرواتب غير الطبيعية
- تتبع المهام المتأخرة
- تنبيهات الإيميلات العاجلة
- تحليل دوري للبيانات

الاستخدام:
    from core.ai.agents import get_alert_agent, check_all_alerts

    # فحص كل التنبيهات
    alerts = check_all_alerts()
    for alert in alerts:
        print(f"[{alert.priority}] {alert.title}: {alert.message}")

    # فحص محدد
    agent = get_alert_agent()
    contract_alerts = agent.check_expiring_contracts(employees)
    salary_alerts = agent.check_salary_anomalies(salaries)
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import threading

from PyQt5.QtCore import QObject, pyqtSignal

# Try importing AI service
try:
    from core.ai import get_ai_service, is_ollama_available
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False


# ============================================================
# Constants
# ============================================================

# Default thresholds
CONTRACT_WARNING_DAYS = 30      # تحذير قبل 30 يوم من انتهاء العقد
CONTRACT_CRITICAL_DAYS = 7      # حرج قبل 7 أيام
SALARY_DEVIATION_THRESHOLD = 2  # انحراف معياري للرواتب
TASK_OVERDUE_HOURS = 24         # مهمة متأخرة بعد 24 ساعة


# ============================================================
# Data Classes
# ============================================================

class AlertPriority(Enum):
    """أولوية التنبيه"""
    CRITICAL = "critical"   # أحمر - فوري
    HIGH = "high"           # برتقالي - مهم
    MEDIUM = "medium"       # أصفر - عادي
    LOW = "low"             # أزرق - معلوماتي


class AlertCategory(Enum):
    """فئة التنبيه"""
    CONTRACT = "contract"         # عقود
    SALARY = "salary"             # رواتب
    TASK = "task"                 # مهام
    EMAIL = "email"               # إيميل
    SYSTEM = "system"             # نظام
    DATA_QUALITY = "data_quality" # جودة البيانات
    SECURITY = "security"         # أمان
    CUSTOM = "custom"             # مخصص


@dataclass
class Alert:
    """تنبيه ذكي"""
    id: str
    title: str
    message: str
    priority: AlertPriority
    category: AlertCategory
    created_at: datetime = field(default_factory=datetime.now)
    source: str = ""                    # مصدر التنبيه
    related_id: Optional[str] = None    # ID مرتبط (موظف، مهمة، الخ)
    related_type: Optional[str] = None  # نوع المرتبط
    action_url: Optional[str] = None    # رابط للإجراء
    action_text: Optional[str] = None   # نص الإجراء
    is_read: bool = False
    is_dismissed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'priority': self.priority.value,
            'category': self.category.value,
            'created_at': self.created_at.isoformat(),
            'source': self.source,
            'related_id': self.related_id,
            'related_type': self.related_type,
            'action_url': self.action_url,
            'action_text': self.action_text,
            'is_read': self.is_read,
            'is_dismissed': self.is_dismissed,
            'metadata': self.metadata
        }


@dataclass
class AlertSummary:
    """ملخص التنبيهات"""
    total: int
    critical: int
    high: int
    medium: int
    low: int
    by_category: Dict[str, int] = field(default_factory=dict)


# ============================================================
# Alert Signals
# ============================================================

class AlertSignals(QObject):
    """إشارات التنبيهات"""
    alert_created = pyqtSignal(object)       # Alert
    alert_dismissed = pyqtSignal(str)        # alert_id
    alerts_updated = pyqtSignal(int)         # total_count
    critical_alert = pyqtSignal(object)      # Alert (for immediate attention)


# ============================================================
# Alert Agent
# ============================================================

class AlertAgent:
    """
    وكيل التنبيهات الذكية

    يحلل البيانات ويكتشف الأنماط التي تحتاج انتباه.
    """

    def __init__(self):
        self._signals = AlertSignals()
        self._alerts: Dict[str, Alert] = {}
        self._alert_counter = 0
        self._lock = threading.Lock()

        # Custom alert handlers
        self._custom_handlers: Dict[str, Callable] = {}

    @property
    def signals(self) -> AlertSignals:
        """الإشارات للتكامل مع UI"""
        return self._signals

    def _generate_id(self) -> str:
        """توليد ID فريد للتنبيه"""
        with self._lock:
            self._alert_counter += 1
            return f"alert_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._alert_counter}"

    def _add_alert(self, alert: Alert):
        """إضافة تنبيه"""
        with self._lock:
            self._alerts[alert.id] = alert
        self._signals.alert_created.emit(alert)
        self._signals.alerts_updated.emit(len(self._alerts))

        if alert.priority == AlertPriority.CRITICAL:
            self._signals.critical_alert.emit(alert)

    # ============================================================
    # Contract Alerts
    # ============================================================

    def check_expiring_contracts(
        self,
        employees: List[Dict],
        warning_days: int = CONTRACT_WARNING_DAYS,
        critical_days: int = CONTRACT_CRITICAL_DAYS
    ) -> List[Alert]:
        """
        فحص العقود المنتهية أو القريبة من الانتهاء

        Args:
            employees: قائمة الموظفين مع contract_end_date
            warning_days: أيام التحذير
            critical_days: أيام الحرج

        Returns:
            قائمة التنبيهات
        """
        alerts = []
        today = datetime.now().date()

        for emp in employees:
            contract_end = emp.get('contract_end_date')
            if not contract_end:
                continue

            # تحويل التاريخ
            if isinstance(contract_end, str):
                try:
                    contract_end = datetime.fromisoformat(contract_end).date()
                except ValueError:
                    continue
            elif isinstance(contract_end, datetime):
                contract_end = contract_end.date()

            days_remaining = (contract_end - today).days

            if days_remaining < 0:
                # منتهي
                alert = Alert(
                    id=self._generate_id(),
                    title="عقد منتهي",
                    message=f"عقد الموظف {emp.get('name', emp.get('id'))} منتهي منذ {abs(days_remaining)} يوم",
                    priority=AlertPriority.CRITICAL,
                    category=AlertCategory.CONTRACT,
                    source="contract_check",
                    related_id=str(emp.get('id')),
                    related_type="employee",
                    action_text="تجديد العقد",
                    metadata={'days_expired': abs(days_remaining)}
                )
            elif days_remaining <= critical_days:
                # حرج
                alert = Alert(
                    id=self._generate_id(),
                    title="عقد ينتهي قريباً",
                    message=f"عقد الموظف {emp.get('name', emp.get('id'))} ينتهي خلال {days_remaining} يوم",
                    priority=AlertPriority.CRITICAL,
                    category=AlertCategory.CONTRACT,
                    source="contract_check",
                    related_id=str(emp.get('id')),
                    related_type="employee",
                    action_text="تجديد العقد",
                    metadata={'days_remaining': days_remaining}
                )
            elif days_remaining <= warning_days:
                # تحذير
                alert = Alert(
                    id=self._generate_id(),
                    title="تذكير تجديد عقد",
                    message=f"عقد الموظف {emp.get('name', emp.get('id'))} ينتهي خلال {days_remaining} يوم",
                    priority=AlertPriority.HIGH,
                    category=AlertCategory.CONTRACT,
                    source="contract_check",
                    related_id=str(emp.get('id')),
                    related_type="employee",
                    action_text="مراجعة العقد",
                    metadata={'days_remaining': days_remaining}
                )
            else:
                continue

            alerts.append(alert)
            self._add_alert(alert)

        return alerts

    # ============================================================
    # Salary Alerts
    # ============================================================

    def check_salary_anomalies(
        self,
        salaries: List[Dict],
        deviation_threshold: float = SALARY_DEVIATION_THRESHOLD
    ) -> List[Alert]:
        """
        فحص الرواتب غير الطبيعية

        Args:
            salaries: قائمة بيانات الرواتب
            deviation_threshold: عتبة الانحراف المعياري

        Returns:
            قائمة التنبيهات
        """
        alerts = []

        if not salaries:
            return alerts

        # حساب المتوسط والانحراف
        amounts = [s.get('amount', 0) for s in salaries if s.get('amount')]
        if not amounts:
            return alerts

        mean_salary = sum(amounts) / len(amounts)
        variance = sum((x - mean_salary) ** 2 for x in amounts) / len(amounts)
        std_dev = variance ** 0.5

        if std_dev == 0:
            return alerts

        for salary in salaries:
            amount = salary.get('amount', 0)
            if not amount:
                continue

            z_score = abs(amount - mean_salary) / std_dev

            if z_score > deviation_threshold:
                direction = "مرتفع" if amount > mean_salary else "منخفض"
                priority = AlertPriority.HIGH if z_score > 3 else AlertPriority.MEDIUM

                alert = Alert(
                    id=self._generate_id(),
                    title=f"راتب {direction} عن المعتاد",
                    message=f"راتب الموظف {salary.get('employee_name', salary.get('employee_id'))} ({amount:,.0f}) {direction} بشكل ملحوظ",
                    priority=priority,
                    category=AlertCategory.SALARY,
                    source="salary_check",
                    related_id=str(salary.get('employee_id')),
                    related_type="employee",
                    action_text="مراجعة الراتب",
                    metadata={
                        'amount': amount,
                        'mean': mean_salary,
                        'z_score': round(z_score, 2)
                    }
                )
                alerts.append(alert)
                self._add_alert(alert)

        return alerts

    # ============================================================
    # Task Alerts
    # ============================================================

    def check_overdue_tasks(
        self,
        tasks: List[Dict],
        overdue_hours: int = TASK_OVERDUE_HOURS
    ) -> List[Alert]:
        """
        فحص المهام المتأخرة

        Args:
            tasks: قائمة المهام مع due_date
            overdue_hours: ساعات التأخير المسموحة

        Returns:
            قائمة التنبيهات
        """
        alerts = []
        now = datetime.now()

        for task in tasks:
            # تجاهل المهام المكتملة
            if task.get('status') in ['completed', 'done', 'مكتمل']:
                continue

            due_date = task.get('due_date')
            if not due_date:
                continue

            # تحويل التاريخ
            if isinstance(due_date, str):
                try:
                    due_date = datetime.fromisoformat(due_date)
                except ValueError:
                    continue

            hours_overdue = (now - due_date).total_seconds() / 3600

            if hours_overdue > 0:
                if hours_overdue > overdue_hours * 3:
                    priority = AlertPriority.CRITICAL
                elif hours_overdue > overdue_hours:
                    priority = AlertPriority.HIGH
                else:
                    priority = AlertPriority.MEDIUM

                alert = Alert(
                    id=self._generate_id(),
                    title="مهمة متأخرة",
                    message=f"المهمة '{task.get('title', task.get('id'))}' متأخرة منذ {int(hours_overdue)} ساعة",
                    priority=priority,
                    category=AlertCategory.TASK,
                    source="task_check",
                    related_id=str(task.get('id')),
                    related_type="task",
                    action_text="فتح المهمة",
                    metadata={'hours_overdue': round(hours_overdue, 1)}
                )
                alerts.append(alert)
                self._add_alert(alert)

        return alerts

    # ============================================================
    # Data Quality Alerts
    # ============================================================

    def check_missing_data(
        self,
        records: List[Dict],
        required_fields: List[str],
        record_type: str = "record"
    ) -> List[Alert]:
        """
        فحص البيانات الناقصة

        Args:
            records: قائمة السجلات
            required_fields: الحقول المطلوبة
            record_type: نوع السجل للعرض

        Returns:
            قائمة التنبيهات
        """
        alerts = []
        missing_count = 0
        missing_details = []

        for record in records:
            missing_fields = []
            for field in required_fields:
                value = record.get(field)
                if value is None or value == '' or value == []:
                    missing_fields.append(field)

            if missing_fields:
                missing_count += 1
                missing_details.append({
                    'id': record.get('id'),
                    'name': record.get('name', record.get('title', 'N/A')),
                    'missing': missing_fields
                })

        if missing_count > 0:
            priority = AlertPriority.HIGH if missing_count > 10 else AlertPriority.MEDIUM

            alert = Alert(
                id=self._generate_id(),
                title=f"بيانات ناقصة في {record_type}",
                message=f"يوجد {missing_count} سجل بحقول ناقصة",
                priority=priority,
                category=AlertCategory.DATA_QUALITY,
                source="data_quality_check",
                action_text="مراجعة البيانات",
                metadata={
                    'missing_count': missing_count,
                    'details': missing_details[:10]  # أول 10 فقط
                }
            )
            alerts.append(alert)
            self._add_alert(alert)

        return alerts

    # ============================================================
    # AI-Powered Alerts (using Ollama)
    # ============================================================

    def analyze_with_ai(
        self,
        data: Dict,
        context: str = "تحليل بيانات"
    ) -> List[Alert]:
        """
        تحليل البيانات بالذكاء الاصطناعي

        Args:
            data: البيانات للتحليل
            context: سياق التحليل

        Returns:
            قائمة التنبيهات المكتشفة
        """
        if not AI_AVAILABLE or not is_ollama_available():
            return []

        alerts = []

        try:
            service = get_ai_service()

            prompt = f"""
            أنت محلل بيانات خبير. حلل البيانات التالية واكتشف أي مشاكل أو أنماط تحتاج انتباه.

            السياق: {context}

            البيانات:
            {json.dumps(data, ensure_ascii=False, indent=2)[:2000]}

            أجب بصيغة JSON فقط كالتالي:
            {{
                "alerts": [
                    {{
                        "title": "عنوان التنبيه",
                        "message": "تفاصيل التنبيه",
                        "priority": "critical|high|medium|low",
                        "category": "الفئة"
                    }}
                ]
            }}
            """

            response = service.chat(prompt)

            # محاولة استخراج JSON
            try:
                # البحث عن JSON في الرد
                start = response.find('{')
                end = response.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = response[start:end]
                    result = json.loads(json_str)

                    for alert_data in result.get('alerts', []):
                        priority_map = {
                            'critical': AlertPriority.CRITICAL,
                            'high': AlertPriority.HIGH,
                            'medium': AlertPriority.MEDIUM,
                            'low': AlertPriority.LOW
                        }

                        alert = Alert(
                            id=self._generate_id(),
                            title=alert_data.get('title', 'تنبيه AI'),
                            message=alert_data.get('message', ''),
                            priority=priority_map.get(
                                alert_data.get('priority', 'medium').lower(),
                                AlertPriority.MEDIUM
                            ),
                            category=AlertCategory.CUSTOM,
                            source="ai_analysis",
                            metadata={'ai_generated': True}
                        )
                        alerts.append(alert)
                        self._add_alert(alert)

            except json.JSONDecodeError:
                pass

        except Exception:
            pass

        return alerts

    # ============================================================
    # Alert Management
    # ============================================================

    def get_alerts(
        self,
        priority: Optional[AlertPriority] = None,
        category: Optional[AlertCategory] = None,
        unread_only: bool = False,
        limit: int = 100
    ) -> List[Alert]:
        """الحصول على التنبيهات"""
        with self._lock:
            alerts = list(self._alerts.values())

        if priority:
            alerts = [a for a in alerts if a.priority == priority]
        if category:
            alerts = [a for a in alerts if a.category == category]
        if unread_only:
            alerts = [a for a in alerts if not a.is_read]

        # ترتيب بالأولوية ثم التاريخ
        priority_order = {
            AlertPriority.CRITICAL: 0,
            AlertPriority.HIGH: 1,
            AlertPriority.MEDIUM: 2,
            AlertPriority.LOW: 3
        }
        alerts.sort(key=lambda a: (priority_order[a.priority], -a.created_at.timestamp()))

        return alerts[:limit]

    def get_summary(self) -> AlertSummary:
        """ملخص التنبيهات"""
        with self._lock:
            alerts = list(self._alerts.values())

        by_category = {}
        for alert in alerts:
            cat = alert.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

        return AlertSummary(
            total=len(alerts),
            critical=len([a for a in alerts if a.priority == AlertPriority.CRITICAL]),
            high=len([a for a in alerts if a.priority == AlertPriority.HIGH]),
            medium=len([a for a in alerts if a.priority == AlertPriority.MEDIUM]),
            low=len([a for a in alerts if a.priority == AlertPriority.LOW]),
            by_category=by_category
        )

    def mark_as_read(self, alert_id: str):
        """تحديد كمقروء"""
        with self._lock:
            if alert_id in self._alerts:
                self._alerts[alert_id].is_read = True

    def dismiss_alert(self, alert_id: str):
        """تجاهل تنبيه"""
        with self._lock:
            if alert_id in self._alerts:
                self._alerts[alert_id].is_dismissed = True
        self._signals.alert_dismissed.emit(alert_id)

    def clear_alerts(self, category: Optional[AlertCategory] = None):
        """مسح التنبيهات"""
        with self._lock:
            if category:
                self._alerts = {
                    k: v for k, v in self._alerts.items()
                    if v.category != category
                }
            else:
                self._alerts.clear()

        self._signals.alerts_updated.emit(len(self._alerts))

    # ============================================================
    # Custom Handlers
    # ============================================================

    def register_handler(self, name: str, handler: Callable):
        """تسجيل معالج مخصص"""
        self._custom_handlers[name] = handler

    def run_custom_check(self, name: str, *args, **kwargs) -> List[Alert]:
        """تشغيل فحص مخصص"""
        if name not in self._custom_handlers:
            return []
        return self._custom_handlers[name](*args, **kwargs)


# ============================================================
# Singleton Access
# ============================================================

_alert_agent: Optional[AlertAgent] = None


def get_alert_agent() -> AlertAgent:
    """
    الحصول على وكيل التنبيهات

    Returns:
        AlertAgent singleton instance
    """
    global _alert_agent
    if _alert_agent is None:
        _alert_agent = AlertAgent()
    return _alert_agent


# ============================================================
# Convenience Functions
# ============================================================

def check_all_alerts(
    employees: Optional[List[Dict]] = None,
    salaries: Optional[List[Dict]] = None,
    tasks: Optional[List[Dict]] = None
) -> List[Alert]:
    """
    فحص كل التنبيهات

    Example:
        alerts = check_all_alerts(employees=emp_list, tasks=task_list)
    """
    agent = get_alert_agent()
    all_alerts = []

    if employees:
        all_alerts.extend(agent.check_expiring_contracts(employees))

    if salaries:
        all_alerts.extend(agent.check_salary_anomalies(salaries))

    if tasks:
        all_alerts.extend(agent.check_overdue_tasks(tasks))

    return all_alerts


def get_critical_alerts() -> List[Alert]:
    """الحصول على التنبيهات الحرجة فقط"""
    return get_alert_agent().get_alerts(priority=AlertPriority.CRITICAL)


def get_alert_summary() -> AlertSummary:
    """ملخص التنبيهات"""
    return get_alert_agent().get_summary()


def create_custom_alert(
    title: str,
    message: str,
    priority: AlertPriority = AlertPriority.MEDIUM,
    category: AlertCategory = AlertCategory.CUSTOM
) -> Alert:
    """
    إنشاء تنبيه مخصص

    Example:
        alert = create_custom_alert(
            "تذكير",
            "موعد الاجتماع بعد ساعة",
            AlertPriority.HIGH
        )
    """
    agent = get_alert_agent()
    alert = Alert(
        id=agent._generate_id(),
        title=title,
        message=message,
        priority=priority,
        category=category,
        source="custom"
    )
    agent._add_alert(alert)
    return alert
