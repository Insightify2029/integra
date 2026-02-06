"""
INTEGRA - Form AI Agent
وكيل النماذج الذكي
المحور K

يفهم نوع النموذج/المهمة ويملأ الحقول تلقائياً.

التاريخ: 4 فبراير 2026
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re

from core.logging import app_logger

# Try importing orchestration
try:
    from core.ai.orchestration import (
        BaseAgent, AgentCapability, AgentStatus,
        get_agent_registry, register_agent
    )
    ORCHESTRATION_AVAILABLE = True
except ImportError:
    ORCHESTRATION_AVAILABLE = False
    BaseAgent = object
    app_logger.debug("Orchestration not available for form agent")

# Try importing AI service
try:
    from core.ai import get_ai_service, is_ollama_available
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False


class FormType(Enum):
    """أنواع النماذج"""
    VACATION_SETTLEMENT = "vacation_settlement"  # تسوية إجازة
    SALARY_SETTLEMENT = "salary_settlement"      # تسوية راتب
    END_OF_SERVICE = "end_of_service"            # مكافأة نهاية الخدمة
    LEAVE_REQUEST = "leave_request"              # طلب إجازة
    EMPLOYEE_CREATE = "employee_create"          # إنشاء موظف
    EMPLOYEE_UPDATE = "employee_update"          # تحديث موظف
    EXPENSE_CLAIM = "expense_claim"              # مطالبة مصروفات
    SALARY_ADVANCE = "salary_advance"            # سلفة راتب
    CONTRACT_RENEWAL = "contract_renewal"        # تجديد عقد
    WARNING_LETTER = "warning_letter"            # إنذار
    APPRECIATION_LETTER = "appreciation_letter"  # شهادة تقدير
    GENERAL = "general"                          # عام


@dataclass
class FormField:
    """حقل في النموذج"""
    name: str
    label_ar: str
    label_en: str
    field_type: str  # text, number, date, select, checkbox
    value: Any = None
    suggested_value: Any = None
    source: Optional[str] = None  # من أين جاءت القيمة
    confidence: float = 0.0
    required: bool = False
    options: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class FormDetectionResult:
    """نتيجة اكتشاف نوع النموذج"""
    form_type: FormType
    confidence: float
    keywords_found: List[str]
    suggested_form_name: str
    suggested_form_name_ar: str


@dataclass
class FormFillingResult:
    """نتيجة ملء النموذج"""
    form_type: FormType
    fields: List[FormField]
    auto_filled_count: int
    total_fields: int
    data_sources_used: List[str]


class FormAgent(BaseAgent if ORCHESTRATION_AVAILABLE else object):
    """
    وكيل النماذج الذكي

    قدرات:
    - اكتشاف نوع النموذج من النص
    - ملء الحقول تلقائياً
    - استخراج البيانات من الإيميلات
    - التحقق من صحة البيانات
    """

    _instance = None

    # قدرات الوكيل
    AGENT_CAPABILITIES = [
        AgentCapability.FORM_DETECTION,
        AgentCapability.FORM_FILLING,
        AgentCapability.FORM_VALIDATION,
        AgentCapability.DATA_EXTRACTION
    ] if ORCHESTRATION_AVAILABLE else []

    # كلمات مفتاحية لاكتشاف نوع النموذج
    FORM_KEYWORDS = {
        FormType.VACATION_SETTLEMENT: [
            "تسوية إجازة", "تسوية الإجازة", "بدل إجازة",
            "vacation settlement", "leave settlement"
        ],
        FormType.SALARY_SETTLEMENT: [
            "تسوية راتب", "تسوية الراتب", "مستحقات",
            "salary settlement", "final settlement"
        ],
        FormType.END_OF_SERVICE: [
            "نهاية الخدمة", "مكافأة نهاية", "end of service",
            "gratuity", "مستحقات نهاية"
        ],
        FormType.LEAVE_REQUEST: [
            "طلب إجازة", "إجازة سنوية", "إجازة مرضية",
            "leave request", "vacation request"
        ],
        FormType.EXPENSE_CLAIM: [
            "مطالبة مصروفات", "مصروفات", "تعويض",
            "expense claim", "reimbursement"
        ],
        FormType.SALARY_ADVANCE: [
            "سلفة", "سلفة راتب", "salary advance", "loan"
        ],
        FormType.CONTRACT_RENEWAL: [
            "تجديد عقد", "تجديد العقد", "contract renewal"
        ],
        FormType.WARNING_LETTER: [
            "إنذار", "تحذير", "warning", "letter of warning"
        ],
        FormType.APPRECIATION_LETTER: [
            "شهادة تقدير", "خطاب شكر", "appreciation", "certificate"
        ]
    }

    # قوالب الحقول لكل نوع نموذج
    FORM_TEMPLATES = {
        FormType.VACATION_SETTLEMENT: [
            FormField("employee_id", "رقم الموظف", "Employee ID", "number", required=True),
            FormField("employee_name", "اسم الموظف", "Employee Name", "text", required=True),
            FormField("department", "القسم", "Department", "text"),
            FormField("vacation_type", "نوع الإجازة", "Vacation Type", "select"),
            FormField("start_date", "تاريخ البداية", "Start Date", "date", required=True),
            FormField("end_date", "تاريخ النهاية", "End Date", "date", required=True),
            FormField("days_count", "عدد الأيام", "Days Count", "number"),
            FormField("basic_salary", "الراتب الأساسي", "Basic Salary", "number"),
            FormField("housing_allowance", "بدل السكن", "Housing Allowance", "number"),
            FormField("transportation", "بدل المواصلات", "Transportation", "number"),
            FormField("total_amount", "إجمالي المستحق", "Total Amount", "number"),
        ],
        FormType.SALARY_SETTLEMENT: [
            FormField("employee_id", "رقم الموظف", "Employee ID", "number", required=True),
            FormField("employee_name", "اسم الموظف", "Employee Name", "text", required=True),
            FormField("department", "القسم", "Department", "text"),
            FormField("settlement_date", "تاريخ التسوية", "Settlement Date", "date", required=True),
            FormField("last_working_day", "آخر يوم عمل", "Last Working Day", "date"),
            FormField("basic_salary", "الراتب الأساسي", "Basic Salary", "number"),
            FormField("allowances", "البدلات", "Allowances", "number"),
            FormField("deductions", "الخصومات", "Deductions", "number"),
            FormField("vacation_balance", "رصيد الإجازات", "Vacation Balance", "number"),
            FormField("total_amount", "إجمالي المستحق", "Total Amount", "number"),
        ],
        FormType.LEAVE_REQUEST: [
            FormField("employee_id", "رقم الموظف", "Employee ID", "number", required=True),
            FormField("employee_name", "اسم الموظف", "Employee Name", "text", required=True),
            FormField("leave_type", "نوع الإجازة", "Leave Type", "select"),
            FormField("start_date", "من تاريخ", "From Date", "date", required=True),
            FormField("end_date", "إلى تاريخ", "To Date", "date", required=True),
            FormField("days_count", "عدد الأيام", "Days Count", "number"),
            FormField("reason", "السبب", "Reason", "text"),
            FormField("substitute", "البديل", "Substitute", "text"),
        ]
    }

    # أنماط استخراج البيانات من النص
    EXTRACTION_PATTERNS = {
        "employee_number": [
            r"رقم الموظف[:\s]+(\d+)",
            r"employee\s*(?:id|number|#)[:\s]*(\d+)",
            r"EMP[:\s]*(\d+)",
            r"الرقم الوظيفي[:\s]+(\d+)"
        ],
        "employee_name_ar": [
            r"الموظف[:\s]+([أ-ي\s]+)",
            r"اسم الموظف[:\s]+([أ-ي\s]+)",
            r"السيد[/:]?\s*([أ-ي\s]+)",
            r"الأخ[/:]?\s*([أ-ي\s]+)"
        ],
        "date": [
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"(\d{4}[/-]\d{1,2}[/-]\d{1,2})"
        ],
        "days": [
            r"(\d+)\s*(?:يوم|أيام|days?)",
            r"لمدة\s*(\d+)",
            r"عدد الأيام[:\s]+(\d+)"
        ],
        "amount": [
            r"(\d[\d,]*\.?\d*)\s*(?:ر\.س|ريال|SAR|SR)",
            r"المبلغ[:\s]+(\d[\d,]*\.?\d*)",
            r"إجمالي[:\s]+(\d[\d,]*\.?\d*)"
        ]
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return

        if ORCHESTRATION_AVAILABLE:
            super().__init__(
                agent_id="form_agent",
                name="Form Agent",
                name_ar="وكيل النماذج"
            )

        self._initialized = True
        app_logger.info("FormAgent initialized")

    # ═══════════════════════════════════════════════════════════════
    # Orchestration Integration
    # ═══════════════════════════════════════════════════════════════

    @property
    def capabilities(self) -> List:
        """قدرات الوكيل"""
        return self.AGENT_CAPABILITIES

    def can_handle(self, task_type: str, data: Dict[str, Any]) -> bool:
        """هل يمكن للوكيل معالجة هذه المهمة؟"""
        supported_types = [
            "detect_form_type", "fill_form", "validate_form",
            "extract_data", "form_detection", "form_filling",
            "form_validation", "data_extraction"
        ]
        return task_type.lower() in supported_types

    def handle(self, task_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """معالجة المهمة"""
        task_type_lower = task_type.lower()

        if task_type_lower in ["detect_form_type", "form_detection"]:
            text = data.get("text", "")
            result = self.detect_form_type(text)
            return {
                "form_type": result.form_type.value,
                "confidence": result.confidence,
                "keywords_found": result.keywords_found,
                "suggested_name": result.suggested_form_name,
                "suggested_name_ar": result.suggested_form_name_ar
            }

        elif task_type_lower in ["fill_form", "form_filling"]:
            form_type_str = data.get("form_type", "general")
            form_type = FormType(form_type_str) if form_type_str in [ft.value for ft in FormType] else FormType.GENERAL
            text = data.get("text")
            employee_data = data.get("employee_data")
            result = self.fill_form(form_type, text, employee_data)
            return {
                "form_type": result.form_type.value,
                "fields": [
                    {
                        "name": f.name,
                        "label_ar": f.label_ar,
                        "value": f.value,
                        "suggested_value": f.suggested_value,
                        "confidence": f.confidence,
                        "source": f.source
                    }
                    for f in result.fields
                ],
                "auto_filled_count": result.auto_filled_count,
                "total_fields": result.total_fields
            }

        elif task_type_lower in ["extract_data", "data_extraction"]:
            text = data.get("text", "")
            extracted = self.extract_data_from_text(text)
            return {"extracted_data": extracted}

        elif task_type_lower in ["validate_form", "form_validation"]:
            fields = data.get("fields", {})
            form_type_str = data.get("form_type", "general")
            form_type = FormType(form_type_str) if form_type_str in [ft.value for ft in FormType] else FormType.GENERAL
            errors = self.validate_form(form_type, fields)
            return {
                "valid": len(errors) == 0,
                "errors": errors
            }

        else:
            raise ValueError(f"Unsupported task type: {task_type}")

    # ═══════════════════════════════════════════════════════════════
    # Form Detection
    # ═══════════════════════════════════════════════════════════════

    def detect_form_type(self, text: str) -> FormDetectionResult:
        """
        اكتشاف نوع النموذج من النص

        Args:
            text: النص للتحليل

        Returns:
            نتيجة الاكتشاف
        """
        text_lower = text.lower()
        matches: Dict[FormType, List[str]] = {}

        for form_type, keywords in self.FORM_KEYWORDS.items():
            found_keywords = []
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    found_keywords.append(keyword)
            if found_keywords:
                matches[form_type] = found_keywords

        if matches:
            # اختيار النوع الأكثر تطابقاً
            best_type = max(matches, key=lambda ft: len(matches[ft]))
            confidence = min(len(matches[best_type]) / 2, 1.0)
            keywords_found = matches[best_type]

            form_names = {
                FormType.VACATION_SETTLEMENT: ("Vacation Settlement", "تسوية إجازة"),
                FormType.SALARY_SETTLEMENT: ("Salary Settlement", "تسوية راتب"),
                FormType.END_OF_SERVICE: ("End of Service", "مكافأة نهاية الخدمة"),
                FormType.LEAVE_REQUEST: ("Leave Request", "طلب إجازة"),
                FormType.EXPENSE_CLAIM: ("Expense Claim", "مطالبة مصروفات"),
                FormType.SALARY_ADVANCE: ("Salary Advance", "سلفة راتب"),
                FormType.CONTRACT_RENEWAL: ("Contract Renewal", "تجديد عقد"),
                FormType.WARNING_LETTER: ("Warning Letter", "إنذار"),
                FormType.APPRECIATION_LETTER: ("Appreciation Letter", "شهادة تقدير"),
            }

            name_en, name_ar = form_names.get(best_type, ("General Form", "نموذج عام"))

            return FormDetectionResult(
                form_type=best_type,
                confidence=confidence,
                keywords_found=keywords_found,
                suggested_form_name=name_en,
                suggested_form_name_ar=name_ar
            )

        return FormDetectionResult(
            form_type=FormType.GENERAL,
            confidence=0.3,
            keywords_found=[],
            suggested_form_name="General Form",
            suggested_form_name_ar="نموذج عام"
        )

    # ═══════════════════════════════════════════════════════════════
    # Data Extraction
    # ═══════════════════════════════════════════════════════════════

    def extract_data_from_text(self, text: str) -> Dict[str, Any]:
        """
        استخراج البيانات من النص

        Args:
            text: النص للتحليل

        Returns:
            البيانات المستخرجة
        """
        extracted = {}

        for field_name, patterns in self.EXTRACTION_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.UNICODE)
                if match:
                    value = match.group(1).strip()
                    extracted[field_name] = value
                    break

        return extracted

    # ═══════════════════════════════════════════════════════════════
    # Form Filling
    # ═══════════════════════════════════════════════════════════════

    def fill_form(
        self,
        form_type: FormType,
        text: Optional[str] = None,
        employee_data: Optional[Dict[str, Any]] = None
    ) -> FormFillingResult:
        """
        ملء النموذج تلقائياً

        Args:
            form_type: نوع النموذج
            text: النص لاستخراج البيانات منه
            employee_data: بيانات الموظف من قاعدة البيانات

        Returns:
            نتيجة ملء النموذج
        """
        # جلب قالب النموذج
        template_fields = self.FORM_TEMPLATES.get(
            form_type,
            self.FORM_TEMPLATES.get(FormType.LEAVE_REQUEST, [])
        )

        # نسخ الحقول
        fields = [
            FormField(
                name=f.name,
                label_ar=f.label_ar,
                label_en=f.label_en,
                field_type=f.field_type,
                required=f.required,
                options=f.options.copy()
            )
            for f in template_fields
        ]

        # استخراج البيانات من النص
        extracted_data = {}
        if text:
            extracted_data = self.extract_data_from_text(text)

        auto_filled = 0
        data_sources = []

        for field in fields:
            # 1. محاولة الملء من بيانات الموظف
            if employee_data and field.name in employee_data:
                field.suggested_value = employee_data[field.name]
                field.source = "employee_database"
                field.confidence = 0.95
                auto_filled += 1
                if "employee_database" not in data_sources:
                    data_sources.append("employee_database")

            # 2. محاولة الملء من النص المستخرج
            elif field.name in extracted_data:
                field.suggested_value = extracted_data[field.name]
                field.source = "text_extraction"
                field.confidence = 0.7
                auto_filled += 1
                if "text_extraction" not in data_sources:
                    data_sources.append("text_extraction")

            # 3. قيم افتراضية
            elif field.name == "settlement_date":
                field.suggested_value = date.today().isoformat()
                field.source = "default"
                field.confidence = 0.5

        return FormFillingResult(
            form_type=form_type,
            fields=fields,
            auto_filled_count=auto_filled,
            total_fields=len(fields),
            data_sources_used=data_sources
        )

    # ═══════════════════════════════════════════════════════════════
    # Form Validation
    # ═══════════════════════════════════════════════════════════════

    def validate_form(
        self,
        form_type: FormType,
        field_values: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        التحقق من صحة بيانات النموذج

        Args:
            form_type: نوع النموذج
            field_values: قيم الحقول

        Returns:
            قائمة الأخطاء (فارغة إذا صحيح)
        """
        errors = []

        # جلب قالب النموذج
        template_fields = self.FORM_TEMPLATES.get(form_type, [])

        for template_field in template_fields:
            field_name = template_field.name
            value = field_values.get(field_name)

            # التحقق من الحقول المطلوبة
            if template_field.required and (value is None or value == ""):
                errors.append({
                    "field": field_name,
                    "message": f"الحقل '{template_field.label_ar}' مطلوب"
                })
                continue

            # التحقق من نوع البيانات
            if value is not None:
                if template_field.field_type == "number":
                    try:
                        float(value)
                    except (ValueError, TypeError):
                        errors.append({
                            "field": field_name,
                            "message": f"الحقل '{template_field.label_ar}' يجب أن يكون رقماً"
                        })

                elif template_field.field_type == "date":
                    if isinstance(value, str):
                        try:
                            datetime.fromisoformat(value.replace('/', '-'))
                        except ValueError:
                            errors.append({
                                "field": field_name,
                                "message": f"الحقل '{template_field.label_ar}' يجب أن يكون تاريخاً صحيحاً"
                            })

        return errors

    def get_form_template(self, form_type: FormType) -> List[FormField]:
        """جلب قالب النموذج (نسخة عميقة لمنع تعديل القالب الأصلي)"""
        import copy
        return copy.deepcopy(self.FORM_TEMPLATES.get(form_type, []))


# ═══════════════════════════════════════════════════════════════
# Singleton & Quick Access Functions
# ═══════════════════════════════════════════════════════════════

_agent: Optional[FormAgent] = None
_agent_lock = __import__('threading').Lock()


def get_form_agent() -> FormAgent:
    """الحصول على instance الوكيل (thread-safe)"""
    global _agent
    if _agent is None:
        with _agent_lock:
            if _agent is None:
                _agent = FormAgent()
    return _agent


def detect_form_type(text: str) -> FormDetectionResult:
    """اكتشاف نوع النموذج"""
    return get_form_agent().detect_form_type(text)


def fill_form(
    form_type: FormType,
    text: Optional[str] = None,
    employee_data: Optional[Dict[str, Any]] = None
) -> FormFillingResult:
    """ملء النموذج تلقائياً"""
    return get_form_agent().fill_form(form_type, text, employee_data)


def extract_form_data(text: str) -> Dict[str, Any]:
    """استخراج البيانات من النص"""
    return get_form_agent().extract_data_from_text(text)


def validate_form(
    form_type: FormType,
    field_values: Dict[str, Any]
) -> List[Dict[str, str]]:
    """التحقق من صحة النموذج"""
    return get_form_agent().validate_form(form_type, field_values)


def register_form_agent() -> bool:
    """تسجيل وكيل النماذج في منظومة التنسيق"""
    if not ORCHESTRATION_AVAILABLE:
        return False

    try:
        agent = get_form_agent()
        register_agent(
            agent_id="form_agent",
            agent=agent,
            capabilities=agent.AGENT_CAPABILITIES,
            name="Form Agent",
            name_ar="وكيل النماذج",
            description="وكيل ذكي لاكتشاف وملء النماذج تلقائياً",
            priority=10
        )
        app_logger.info("FormAgent registered with orchestration")
        return True
    except Exception as e:
        app_logger.error(f"Failed to register FormAgent: {e}")
        return False
