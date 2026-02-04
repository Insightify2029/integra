"""
Designer Module
===============
Visual designers for reports and forms in INTEGRA.

Includes:
- Report Designer: WYSIWYG report editor
- Form Builder: Drag & drop form creator

Usage:
    # Open Report Designer
    from modules.designer.report_designer import ReportDesignerWindow

    designer = ReportDesignerWindow()
    designer.show()

    # Open Form Builder
    from modules.designer.form_builder import FormBuilderWindow

    builder = FormBuilderWindow()
    builder.show()
"""

from .report_designer import (
    ReportDesignerWindow,
    DesignCanvas,
    ElementPalette,
    PropertyPanel
)

from .form_builder import (
    FormBuilderWindow,
    FormCanvas,
    WidgetToolbox,
    FormPropertyEditor,
    DataBindingManager
)


__all__ = [
    # Report Designer
    'ReportDesignerWindow',
    'DesignCanvas',
    'ElementPalette',
    'PropertyPanel',
    # Form Builder
    'FormBuilderWindow',
    'FormCanvas',
    'WidgetToolbox',
    'FormPropertyEditor',
    'DataBindingManager'
]
