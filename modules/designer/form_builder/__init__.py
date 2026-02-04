"""
Form Builder Module
===================
Visual form builder for INTEGRA.

Features:
- Drag & drop form design
- Widget toolbox with all common controls
- Property editor
- Data binding to database tables
- Validation rules
- Form preview
- Save/Load form templates

Usage:
    from modules.designer.form_builder import FormBuilderWindow

    # Open form builder
    builder = FormBuilderWindow()
    builder.show()

    # Open with existing form
    builder = FormBuilderWindow(form_path="templates/employee_form.json")
    builder.show()
"""

from .form_builder_window import FormBuilderWindow
from .form_canvas import FormCanvas, FormWidget, WidgetType
from .widget_toolbox import WidgetToolbox
from .property_editor import FormPropertyEditor
from .data_binding import DataBindingManager, FieldBinding


__all__ = [
    'FormBuilderWindow',
    'FormCanvas',
    'FormWidget',
    'WidgetType',
    'WidgetToolbox',
    'FormPropertyEditor',
    'DataBindingManager',
    'FieldBinding'
]
