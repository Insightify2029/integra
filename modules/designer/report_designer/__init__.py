"""
Report Designer Module
======================
Visual WYSIWYG report designer for INTEGRA.

Features:
- Drag & Drop design interface
- Live preview
- Multiple report bands (Header, Detail, Footer)
- Rich element palette (Text, Tables, Charts, Images)
- Property panel for element customization
- Template save/load
- Export to PDF, Excel, Word

Usage:
    from modules.designer.report_designer import ReportDesignerWindow

    # Open designer
    designer = ReportDesignerWindow()
    designer.show()

    # Open with template
    designer = ReportDesignerWindow(template_path="templates/employee_report.json")
    designer.show()
"""

from .report_designer_window import ReportDesignerWindow
from .design_canvas import DesignCanvas, CanvasElement, ReportBand
from .element_palette import ElementPalette, ElementType
from .property_panel import PropertyPanel


__all__ = [
    'ReportDesignerWindow',
    'DesignCanvas',
    'CanvasElement',
    'ReportBand',
    'ElementPalette',
    'ElementType',
    'PropertyPanel'
]
