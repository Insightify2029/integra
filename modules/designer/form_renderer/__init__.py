"""
FormRenderer Package for INTEGRA.

Converts .iform JSON definitions into working PyQt5 forms.

Usage::

    from modules.designer.form_renderer import FormRenderer

    renderer = FormRenderer()
    renderer.load_form("path/to/form.iform")
    renderer.set_record(table="employees", record_id=123)
    renderer.saved.connect(on_saved)
    renderer.cancelled.connect(on_cancelled)
"""

from modules.designer.form_renderer.form_renderer import FormRenderer
from modules.designer.form_renderer.widget_factory import (
    WidgetFactory,
    get_widget_value,
    set_widget_value,
    connect_change_signal,
)
from modules.designer.form_renderer.layout_engine import LayoutEngine
from modules.designer.form_renderer.validation_engine import (
    ValidationEngine,
    ValidationError,
)
from modules.designer.form_renderer.form_data_bridge import FormDataBridge
from modules.designer.form_renderer.form_state_manager import (
    FormStateManager,
    FormState,
)

__all__ = [
    "FormRenderer",
    "WidgetFactory",
    "LayoutEngine",
    "ValidationEngine",
    "ValidationError",
    "FormDataBridge",
    "FormStateManager",
    "FormState",
    "get_widget_value",
    "set_widget_value",
    "connect_change_signal",
]
