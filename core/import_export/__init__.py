"""
Import/Export Module
====================
Tools for importing and exporting data in various formats.

Supported formats:
- Excel (.xlsx, .xls) - read
- CSV (.csv) - read
- Word (.docx) - write
- PDF (.pdf) - read

Usage:
    # Excel Import
    from core.import_export import ExcelImporter, read_excel

    importer = ExcelImporter("data.xlsx")
    data = importer.read_all()

    # Or simple function
    data, errors = read_excel("data.xlsx")

    # Word Export
    from core.import_export import WordExporter, create_employee_report

    doc = WordExporter("report.docx")
    doc.add_heading("التقرير")
    doc.add_table(data)
    doc.save()

    # Or simple function
    create_employee_report(employee, "report.docx")

    # PDF Read
    from core.import_export import PDFReader, read_pdf_text

    reader = PDFReader("document.pdf")
    text = reader.extract_text()
    tables = reader.extract_tables()

    # Or simple function
    text, errors = read_pdf_text("document.pdf")
"""

# Excel Import
from .excel_importer import (
    ExcelImporter,
    read_excel,
    get_excel_preview
)

# Word Export
from .word_exporter import (
    WordExporter,
    create_employee_report,
    create_employees_list_report
)

# PDF Read
from .pdf_reader import (
    PDFReader,
    read_pdf_text,
    read_pdf_tables
)


__all__ = [
    # Excel
    'ExcelImporter',
    'read_excel',
    'get_excel_preview',
    # Word
    'WordExporter',
    'create_employee_report',
    'create_employees_list_report',
    # PDF
    'PDFReader',
    'read_pdf_text',
    'read_pdf_tables'
]
