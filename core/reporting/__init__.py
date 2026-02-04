"""
Reporting Module
================
Professional report generation and export system for INTEGRA.

Features:
- PDF generation with ReportLab and WeasyPrint
- Excel reports with openpyxl
- Word documents with python-docx
- Template-based reports with Jinja2
- RTL and Arabic support
- Charts and graphs
- Data binding

Usage:
    # Quick report generation
    from core.reporting import generate_report, ReportFormat

    generate_report(
        data=employees,
        template="employee_list",
        output_path="report.pdf",
        format=ReportFormat.PDF
    )

    # Report Engine
    from core.reporting import ReportEngine, ReportConfig

    engine = ReportEngine()
    config = ReportConfig(
        title="تقرير الموظفين",
        subtitle="كشف رواتب شهر يناير",
        paper_size="A4",
        orientation="portrait"
    )
    engine.create_report(data, config, "report.pdf")

    # PDF Generator
    from core.reporting import PDFGenerator

    pdf = PDFGenerator()
    pdf.add_header("تقرير الموظفين")
    pdf.add_table(data, headers=["الاسم", "الراتب", "القسم"])
    pdf.save("report.pdf")

    # Excel Generator
    from core.reporting import ExcelGenerator

    excel = ExcelGenerator()
    excel.add_sheet("الموظفين", data)
    excel.add_chart("رسم بياني", chart_type="bar")
    excel.save("report.xlsx")
"""

from enum import Enum
from typing import TYPE_CHECKING

# Report format enum
class ReportFormat(Enum):
    """Supported report formats."""
    PDF = "pdf"
    EXCEL = "xlsx"
    WORD = "docx"
    HTML = "html"
    CSV = "csv"


# Report Engine
from .report_engine import (
    ReportEngine,
    ReportConfig,
    ReportSection,
    ReportElement,
    get_report_engine
)

# PDF Generator
from .pdf_generator import (
    PDFGenerator,
    PDFConfig,
    create_pdf_report,
    PDF_AVAILABLE
)

# Excel Generator
from .excel_generator import (
    ExcelGenerator,
    ExcelConfig,
    create_excel_report,
    EXCEL_AVAILABLE
)

# Word Generator
from .word_generator import (
    WordGenerator,
    WordConfig,
    create_word_report,
    WORD_AVAILABLE
)

# Template Engine
from .template_engine import (
    TemplateEngine,
    TemplateConfig,
    TemplateSource,
    get_template_engine,
    render_template,
    render_string_template
)

# Custom Filters
from .filters import TEMPLATE_FILTERS

# Data Binding
from .data_binding import (
    DataBindingManager,
    DataSourceConfig,
    DataSourceType,
    FieldBinding,
    FilterCondition,
    SortOrder,
    SortDirection,
    AggregationType,
    get_data_binding_manager,
    create_employee_source,
    create_department_source,
    create_company_source
)

# Preview & Print
from .preview import (
    ReportPreviewWindow,
    PrintConfig,
    PrintSettingsDialog,
    PreviewMode,
    preview_html,
    preview_file,
    print_html
)

# Built-in Templates
from .builtin_templates import (
    TemplateCategory,
    TemplateInfo,
    BUILTIN_TEMPLATES,
    get_template_info,
    get_templates_by_category,
    get_all_templates,
    list_template_names,
    get_template_path,
    validate_template_data,
    prepare_template_data,
    create_employee_list_report,
    create_salary_report,
    create_department_report,
    create_employee_form
)


# Convenience functions
def generate_report(
    data,
    template: str = None,
    output_path: str = None,
    format: ReportFormat = ReportFormat.PDF,
    config: ReportConfig = None,
    **kwargs
) -> bool:
    """
    Generate a report in the specified format.

    Args:
        data: Report data (list of dicts or dict)
        template: Template name (optional)
        output_path: Output file path
        format: Report format (PDF, Excel, Word, etc.)
        config: Report configuration
        **kwargs: Additional format-specific options

    Returns:
        True if successful
    """
    engine = get_report_engine()

    if config is None:
        config = ReportConfig()

    config.output_format = format

    if template:
        config.template_name = template

    return engine.generate(data, output_path, config, **kwargs)


__all__ = [
    # Enums
    'ReportFormat',
    # Report Engine
    'ReportEngine',
    'ReportConfig',
    'ReportSection',
    'ReportElement',
    'get_report_engine',
    # PDF
    'PDFGenerator',
    'PDFConfig',
    'create_pdf_report',
    'PDF_AVAILABLE',
    # Excel
    'ExcelGenerator',
    'ExcelConfig',
    'create_excel_report',
    'EXCEL_AVAILABLE',
    # Word
    'WordGenerator',
    'WordConfig',
    'create_word_report',
    'WORD_AVAILABLE',
    # Template Engine
    'TemplateEngine',
    'TemplateConfig',
    'TemplateSource',
    'get_template_engine',
    'render_template',
    'render_string_template',
    'TEMPLATE_FILTERS',
    # Data Binding
    'DataBindingManager',
    'DataSourceConfig',
    'DataSourceType',
    'FieldBinding',
    'FilterCondition',
    'SortOrder',
    'SortDirection',
    'AggregationType',
    'get_data_binding_manager',
    'create_employee_source',
    'create_department_source',
    'create_company_source',
    # Preview & Print
    'ReportPreviewWindow',
    'PrintConfig',
    'PrintSettingsDialog',
    'PreviewMode',
    'preview_html',
    'preview_file',
    'print_html',
    # Built-in Templates
    'TemplateCategory',
    'TemplateInfo',
    'BUILTIN_TEMPLATES',
    'get_template_info',
    'get_templates_by_category',
    'get_all_templates',
    'list_template_names',
    'get_template_path',
    'validate_template_data',
    'prepare_template_data',
    'create_employee_list_report',
    'create_salary_report',
    'create_department_report',
    'create_employee_form',
    # Functions
    'generate_report'
]
