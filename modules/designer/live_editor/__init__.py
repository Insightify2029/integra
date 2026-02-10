"""
Live Editor Package for INTEGRA Form System.

Provides in-place visual editing of rendered forms, allowing users
to drag, resize, and modify form widgets without leaving the form view.

Usage::

    from modules.designer.live_editor import LiveEditOverlay

    overlay = LiveEditOverlay(form_renderer)
    overlay.activate(
        form_def=form_definition,
        form_path="path/to/form.iform",
        widget_map=renderer._widget_map,
        scroll_area=renderer._scroll_area,
        content_widget=renderer._content_widget,
    )

    # Or via FormRenderer shortcut:
    renderer.enable_live_edit()

Components:
- LiveEditOverlay: Main overlay controller
- SelectionHandles: Visual resize/move handles
- PropertyPopup: Quick property editor popup
- SnapGuideEngine: Smart alignment guides
"""

from modules.designer.live_editor.live_edit_overlay import LiveEditOverlay
from modules.designer.live_editor.selection_handles import (
    SelectionHandles,
    HandlePosition,
)
from modules.designer.live_editor.snap_guides import (
    SnapGuideEngine,
    SnapGuide,
    SnapResult,
)
from modules.designer.live_editor.property_popup import PropertyPopup

__all__ = [
    "LiveEditOverlay",
    "SelectionHandles",
    "HandlePosition",
    "SnapGuideEngine",
    "SnapGuide",
    "SnapResult",
    "PropertyPopup",
]
