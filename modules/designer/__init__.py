"""
Designer Module
===============
Visual designers for reports and forms in INTEGRA.

Includes:
- Report Designer: WYSIWYG report editor
- Form Builder: Drag & drop form creator (Phase 2 enhanced)
- Template Library: Pre-built form templates

Usage:
    # Open Report Designer
    from modules.designer.report_designer import ReportDesignerWindow

    designer = ReportDesignerWindow()
    designer.show()

    # Open Form Builder
    from modules.designer.form_builder import FormBuilderWindow

    builder = FormBuilderWindow()
    builder.show()

    # Browse templates
    from modules.designer.templates import get_template_manager

    tm = get_template_manager()
    templates = tm.get_all_templates()
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

from .templates import (
    TemplateManager,
    get_template_manager,
    TemplateInfo
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
    'DataBindingManager',
    # Templates
    'TemplateManager',
    'get_template_manager',
    'TemplateInfo',
]
