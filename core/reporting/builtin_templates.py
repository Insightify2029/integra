"""
Built-in Report Templates
=========================
Pre-defined templates for common INTEGRA reports and forms.

Templates included:
- Employee List Report
- Salary Report
- Department Report
- Employee Form
- Invoice Template
- Summary Cards
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from core.logging import app_logger


class TemplateCategory(Enum):
    """Template categories."""
    REPORT = "report"
    FORM = "form"
    INVOICE = "invoice"
    LETTER = "letter"
    SUMMARY = "summary"


@dataclass
class TemplateInfo:
    """Template metadata."""

    name: str
    title_ar: str
    title_en: str
    description_ar: str
    description_en: str
    category: TemplateCategory
    template_file: str
    icon: str = "📄"
    preview_image: str = ""
    required_fields: List[str] = None
    optional_fields: List[str] = None
    default_config: Dict[str, Any] = None

    def __post_init__(self):
        self.required_fields = self.required_fields or []
        self.optional_fields = self.optional_fields or []
        self.default_config = self.default_config or {}


# Built-in templates registry
BUILTIN_TEMPLATES: Dict[str, TemplateInfo] = {
    # Reports
    "employee_list": TemplateInfo(
        name="employee_list",
        title_ar="تقرير قائمة الموظفين",
        title_en="Employee List Report",
        description_ar="تقرير شامل بقائمة الموظفين مع تفاصيل كاملة",
        description_en="Comprehensive employee list report with full details",
        category=TemplateCategory.REPORT,
        template_file="reports/employee_list.html",
        icon="👥",
        required_fields=["employees"],
        optional_fields=[
            "show_photo", "show_company", "show_salary",
            "show_salary_summary", "departments_count", "filters"
        ],
        default_config={
            "show_photo": False,
            "show_company": True,
            "show_salary": True,
            "show_salary_summary": True
        }
    ),

    "salary_report": TemplateInfo(
        name="salary_report",
        title_ar="تقرير الرواتب",
        title_en="Salary Report",
        description_ar="تقرير تفصيلي للرواتب مع ملخص وتوزيع حسب الأقسام",
        description_en="Detailed salary report with summary and department breakdown",
        category=TemplateCategory.REPORT,
        template_file="reports/salary_report.html",
        icon="💰",
        required_fields=["employees", "total_salaries"],
        optional_fields=[
            "total_basic", "total_housing", "total_transport",
            "average_salary", "department_breakdown", "period"
        ],
        default_config={
            "total_basic": 0,
            "total_housing": 0,
            "total_transport": 0
        }
    ),

    "department_report": TemplateInfo(
        name="department_report",
        title_ar="تقرير الأقسام",
        title_en="Department Report",
        description_ar="تقرير تفصيلي لكل قسم مع إحصائيات الموظفين",
        description_en="Detailed department report with employee statistics",
        category=TemplateCategory.REPORT,
        template_file="reports/department_report.html",
        icon="🏢",
        required_fields=["departments"],
        optional_fields=[
            "show_salary", "show_summary",
            "total_employees", "total_salaries", "average_salary"
        ],
        default_config={
            "show_salary": True,
            "show_summary": True
        }
    ),

    # Forms
    "employee_form": TemplateInfo(
        name="employee_form",
        title_ar="نموذج بيانات الموظف",
        title_en="Employee Data Form",
        description_ar="نموذج عرض بيانات الموظف الكاملة",
        description_en="Employee complete data display form",
        category=TemplateCategory.FORM,
        template_file="forms/employee_form.html",
        icon="📋",
        required_fields=["employee"],
        optional_fields=["show_financial", "title", "subtitle"],
        default_config={
            "show_financial": True,
            "title": "نموذج بيانات الموظف",
            "subtitle": "معلومات الموظف الكاملة"
        }
    ),

    # Invoice
    "invoice": TemplateInfo(
        name="invoice",
        title_ar="فاتورة",
        title_en="Invoice",
        description_ar="قالب فاتورة مبيعات أو خدمات",
        description_en="Sales or services invoice template",
        category=TemplateCategory.INVOICE,
        template_file="reports/invoice.html",
        icon="🧾",
        required_fields=["invoice"],
        optional_fields=["company_logo", "company_info"],
        default_config={}
    ),

    # Summary
    "summary_cards": TemplateInfo(
        name="summary_cards",
        title_ar="بطاقات ملخص",
        title_en="Summary Cards",
        description_ar="عرض بطاقات ملخص مع إحصائيات",
        description_en="Display summary cards with statistics",
        category=TemplateCategory.SUMMARY,
        template_file="reports/summary_cards.html",
        icon="📊",
        required_fields=["cards"],
        optional_fields=["details"],
        default_config={}
    ),

    # Table Report (Generic)
    "table_report": TemplateInfo(
        name="table_report",
        title_ar="تقرير جدولي",
        title_en="Table Report",
        description_ar="تقرير جدولي عام قابل للتخصيص",
        description_en="Generic customizable table report",
        category=TemplateCategory.REPORT,
        template_file="reports/table_report.html",
        icon="📑",
        required_fields=["columns", "data"],
        optional_fields=["show_totals"],
        default_config={
            "show_totals": False
        }
    )
}


def get_template_info(name: str) -> Optional[TemplateInfo]:
    """
    Get template information by name.

    Args:
        name: Template name

    Returns:
        TemplateInfo or None
    """
    return BUILTIN_TEMPLATES.get(name)


def get_templates_by_category(category: TemplateCategory) -> List[TemplateInfo]:
    """
    Get all templates in a category.

    Args:
        category: Template category

    Returns:
        List of TemplateInfo
    """
    return [
        info for info in BUILTIN_TEMPLATES.values()
        if info.category == category
    ]


def get_all_templates() -> Dict[str, TemplateInfo]:
    """Get all available templates."""
    return BUILTIN_TEMPLATES.copy()


def list_template_names() -> List[str]:
    """Get list of template names."""
    return list(BUILTIN_TEMPLATES.keys())


def get_template_path(name: str) -> Optional[Path]:
    """
    Get full path to template file.

    Args:
        name: Template name

    Returns:
        Path to template file or None
    """
    info = BUILTIN_TEMPLATES.get(name)
    if not info:
        return None

    base_path = Path(__file__).parent / "templates"
    return base_path / info.template_file


def validate_template_data(name: str, data: Dict[str, Any]) -> tuple:
    """
    Validate data for a template.

    Args:
        name: Template name
        data: Data dictionary

    Returns:
        Tuple of (is_valid, missing_fields)
    """
    info = BUILTIN_TEMPLATES.get(name)
    if not info:
        return False, ["Unknown template"]

    missing = [
        field for field in info.required_fields
        if field not in data
    ]

    return len(missing) == 0, missing


def prepare_template_data(
    name: str,
    data: Dict[str, Any],
    use_defaults: bool = True
) -> Dict[str, Any]:
    """
    Prepare data for template rendering.

    Args:
        name: Template name
        data: User-provided data
        use_defaults: Apply default config values

    Returns:
        Prepared data dictionary
    """
    info = BUILTIN_TEMPLATES.get(name)
    if not info:
        return data

    result = {}

    # Apply defaults first
    if use_defaults and info.default_config:
        result.update(info.default_config)

    # Apply user data
    result.update(data)

    return result


# Template quick access functions
def create_employee_list_report(
    employees: List[Dict],
    show_salary: bool = True,
    show_company: bool = True,
    filters: List[Dict] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create data for employee list report.

    Args:
        employees: List of employee dictionaries
        show_salary: Show salary column
        show_company: Show company column
        filters: Applied filters info
        **kwargs: Additional template variables

    Returns:
        Template data dictionary
    """
    departments = set(e.get("department") for e in employees if e.get("department"))

    return prepare_template_data("employee_list", {
        "employees": employees,
        "show_salary": show_salary,
        "show_company": show_company,
        "show_salary_summary": show_salary,
        "departments_count": len(departments),
        "filters": filters or [],
        **kwargs
    })


def create_salary_report(
    employees: List[Dict],
    period: Dict = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create data for salary report.

    Args:
        employees: List of employee dictionaries
        period: Report period info
        **kwargs: Additional template variables

    Returns:
        Template data dictionary
    """
    # Calculate totals
    total_basic = sum(float(e.get("basic_salary", 0) or 0) for e in employees)
    total_housing = sum(float(e.get("housing_allowance", 0) or 0) for e in employees)
    total_transport = sum(float(e.get("transport_allowance", 0) or 0) for e in employees)
    total_other = sum(float(e.get("other_allowances", 0) or 0) for e in employees)
    total_deductions = sum(float(e.get("deductions", 0) or 0) for e in employees)
    total_net = sum(float(e.get("net_salary", 0) or 0) for e in employees)

    total_salaries = total_net if total_net else total_basic + total_housing + total_transport

    # Calculate department breakdown
    dept_totals = {}
    for emp in employees:
        dept = emp.get("department", "أخرى")
        if dept not in dept_totals:
            dept_totals[dept] = 0
        dept_totals[dept] += float(emp.get("net_salary", 0) or emp.get("basic_salary", 0) or 0)

    department_breakdown = [
        {"name": dept, "total": total}
        for dept, total in sorted(dept_totals.items(), key=lambda x: -x[1])
    ]

    return prepare_template_data("salary_report", {
        "employees": employees,
        "total_salaries": total_salaries,
        "total_basic": total_basic,
        "total_housing": total_housing,
        "total_transport": total_transport,
        "average_salary": total_salaries / len(employees) if employees else 0,
        "department_breakdown": department_breakdown,
        "period": period,
        **kwargs
    })


def create_department_report(
    departments: List[Dict],
    show_salary: bool = True,
    show_summary: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Create data for department report.

    Args:
        departments: List of department dictionaries with employees
        show_salary: Show salary information
        show_summary: Show summary section
        **kwargs: Additional template variables

    Returns:
        Template data dictionary
    """
    total_employees = sum(len(d.get("employees", [])) for d in departments)
    total_salaries = sum(
        sum(float(e.get("salary", 0) or 0) for e in d.get("employees", []))
        for d in departments
    )

    # Calculate percentages
    for dept in departments:
        dept_salary = sum(
            float(e.get("salary", 0) or 0)
            for e in dept.get("employees", [])
        )
        dept["percentage"] = (dept_salary / total_salaries * 100) if total_salaries else 0

    return prepare_template_data("department_report", {
        "departments": departments,
        "show_salary": show_salary,
        "show_summary": show_summary,
        "total_employees": total_employees,
        "total_salaries": total_salaries,
        "average_salary": total_salaries / total_employees if total_employees else 0,
        **kwargs
    })


def create_employee_form(
    employee: Dict,
    show_financial: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Create data for employee form.

    Args:
        employee: Employee dictionary
        show_financial: Show financial information
        **kwargs: Additional template variables

    Returns:
        Template data dictionary
    """
    # Calculate total salary if not present
    if "total_salary" not in employee:
        employee["total_salary"] = sum([
            float(employee.get("basic_salary", 0) or 0),
            float(employee.get("housing_allowance", 0) or 0),
            float(employee.get("transport_allowance", 0) or 0),
            float(employee.get("other_allowances", 0) or 0)
        ])

    return prepare_template_data("employee_form", {
        "employee": employee,
        "show_financial": show_financial,
        **kwargs
    })
