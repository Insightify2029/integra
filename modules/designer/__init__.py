"""
Designer Module
===============
Visual designers for reports and forms in INTEGRA.

Includes:
- Report Designer: WYSIWYG report editor
- Form Builder: Drag & drop form creator (Phase 2 enhanced)
- Template Library: Pre-built form templates
- Live Editor: In-place visual editing of rendered forms (Phase 3)

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

    # Enable live editing on a rendered form
    renderer.enable_live_edit()  # or Ctrl+Shift+E
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

from .live_editor import (
    LiveEditOverlay,
    SelectionHandles,
    HandlePosition,
    SnapGuideEngine,
    PropertyPopup,
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
    # Live Editor (Phase 3)
    'LiveEditOverlay',
    'SelectionHandles',
    'HandlePosition',
    'SnapGuideEngine',
    'PropertyPopup',
]
