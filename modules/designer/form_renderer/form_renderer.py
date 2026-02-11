"""
FormRenderer - Main Orchestrator for INTEGRA Form System.

Renders a form from .iform JSON definition by coordinating:
- WidgetFactory: Creates PyQt5 widgets
- LayoutEngine: Arranges widgets in sections
- ValidationEngine: Validates field values
- FormDataBridge: Loads/saves from database
- FormStateManager: Tracks dirty/undo/redo state

Usage::

    renderer = FormRenderer()
    renderer.load_form("path/to/form.iform")
    renderer.set_record(table="employees", record_id=123)
    renderer.saved.connect(on_form_saved)
    renderer.cancelled.connect(on_form_cancelled)

Follows all 13 mandatory INTEGRA rules:
- Rule #2: Parameterized SQL via FormDataBridge
- Rule #3: Thread-safe state via FormStateManager
- Rule #6: Proper widget lifecycle cleanup
- Rule #7: int() for all Qt size operations
- Rule #9: Error handling with app_logger
- Rule #11: Theme-aware via get_current_palette()
- Rule #13: All DB ops in background threads
"""

from __future__ import annotations

import copy
from typing import Any, Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QPushButton,
    QComboBox,
    QMessageBox,
    QFrame,
    QSizePolicy,
    QShortcut,
)
from core.logging import app_logger
from core.themes import (
    get_current_palette,
    get_font,
    FONT_SIZE_BODY,
    FONT_SIZE_TITLE,
    FONT_WEIGHT_BOLD,
)
from modules.designer.shared.form_schema import (
    validate_form_schema,
    merge_with_defaults,
    load_form_file,
    DEFAULT_FORM_SETTINGS,
)
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

# Lazy import guard for LiveEditOverlay to avoid circular imports (Rule #4: thread-safe)
import threading as _threading

_overlay_lock = _threading.Lock()
_LiveEditOverlay = None


def _get_overlay_class():
    """Lazy import of LiveEditOverlay to avoid circular dependency. Thread-safe (Rule #4)."""
    global _LiveEditOverlay
    with _overlay_lock:
        if _LiveEditOverlay is None:
            from modules.designer.live_editor.live_edit_overlay import LiveEditOverlay
            _LiveEditOverlay = LiveEditOverlay
    return _LiveEditOverlay


class FormRenderer(QWidget):
    """
    Renders a complete form from an .iform JSON definition.

    This is the main widget that users embed in their windows.
    It creates all sub-widgets, manages data binding, validation,
    and provides a clean public API.

    Signals:
        saved(dict): Emitted with the saved data dict.
        cancelled(): Emitted when the user cancels.
        dirty_changed(bool): Emitted when dirty status changes.
        validation_failed(list): Emitted with list of error messages.
        field_changed(str, object): Emitted with (field_id, new_value).
        state_changed(object): Emitted with the new FormState.
    """

    # Signals
    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()
    dirty_changed = pyqtSignal(bool)
    validation_failed = pyqtSignal(list)
    field_changed = pyqtSignal(str, object)
    state_changed = pyqtSignal(object)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("FormRenderer")

        # Sub-components
        self._widget_factory = WidgetFactory()
        self._layout_engine: Optional[LayoutEngine] = None
        self._validation_engine = ValidationEngine()
        self._data_bridge = FormDataBridge(self)
        self._state_manager = FormStateManager(self)

        # Form definition
        self._form_def: Optional[dict[str, Any]] = None
        self._form_path: Optional[str] = None

        # Widget registry: field_id -> (label, widget, field_def)
        self._widget_map: dict[str, tuple[Optional[QLabel], QWidget, dict[str, Any]]] = {}
        # field_id -> widget (just the input widget for quick access)
        self._input_widgets: dict[str, QWidget] = {}
        # Action buttons: action_id -> QPushButton
        self._action_buttons: dict[str, QPushButton] = {}

        # Record info
        self._target_table: Optional[str] = None
        self._record_id: Optional[int] = None

        # UI references
        self._scroll_area: Optional[QScrollArea] = None
        self._content_widget: Optional[QWidget] = None
        self._action_bar: Optional[QWidget] = None
        self._header_widget: Optional[QWidget] = None
        self._main_layout: Optional[QVBoxLayout] = None

        # Combo loading state (Fix: race condition between set_data and combo loading)
        self._combos_loading_count = 0  # Number of combos still loading
        self._combos_loaded = False  # True when all combos have loaded
        self._pending_data: Optional[dict[str, Any]] = None  # Data waiting for combos

        # Live edit overlay (Phase 3)
        self._live_edit_overlay = None  # Created lazily
        self._live_edit_active = False

        # Connect internal signals
        self._state_manager.dirty_changed.connect(self.dirty_changed)
        self._state_manager.state_changed.connect(self.state_changed)
        self._data_bridge.record_loaded.connect(self._on_record_loaded)
        self._data_bridge.record_saved.connect(self._on_record_saved)
        self._data_bridge.combo_data_loaded.connect(self._on_combo_data_loaded)
        self._data_bridge.error_occurred.connect(self._on_bridge_error)

        # Set up unique checker for validation
        self._validation_engine.set_unique_checker(
            self._data_bridge.check_unique_sync
        )

        # Build minimal layout
        self._init_ui()

    # -----------------------------------------------------------------------
    # UI Initialization
    # -----------------------------------------------------------------------

    def _init_ui(self) -> None:
        """Set up the base layout structure."""
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

    # -----------------------------------------------------------------------
    # Public API: Load form
    # -----------------------------------------------------------------------

    def load_form(self, form_path: str) -> bool:
        """
        Load a form definition from a .iform file.

        Args:
            form_path: Path to the .iform JSON file.

        Returns:
            True if loaded successfully, False otherwise.
        """
        form_data, error = load_form_file(form_path)
        if form_data is None:
            app_logger.error(f"Failed to load form: {error}")
            self._show_error(f"خطأ في تحميل النموذج:\n{error}")
            return False

        self._form_path = form_path
        return self.load_form_dict(form_data)

    def load_form_dict(self, form_dict: dict[str, Any]) -> bool:
        """
        Load a form from a dictionary (for embedded forms or testing).

        Args:
            form_dict: Form definition dictionary.

        Returns:
            True if loaded and rendered successfully.
        """
        is_valid, errors = validate_form_schema(form_dict)
        if not is_valid:
            msg = "Schema errors:\n" + "\n".join(f"- {e}" for e in errors)
            app_logger.error(f"Invalid form schema: {msg}")
            self._show_error(f"خطأ في هيكل النموذج:\n{msg}")
            return False

        self._form_def = form_dict
        self._target_table = form_dict.get("target_table")
        self._state_manager.set_state(FormState.LOADING)

        try:
            self._build_ui()
            self._state_manager.set_state(FormState.READY)
            app_logger.info(
                f"Form '{form_dict.get('form_id')}' rendered successfully"
            )
            return True
        except Exception:
            app_logger.error("Error building form UI", exc_info=True)
            self._state_manager.mark_error()
            return False

    # -----------------------------------------------------------------------
    # Public API: Record operations
    # -----------------------------------------------------------------------

    def set_record(self, table: str, record_id: int) -> None:
        """
        Load a record from the database into the form.

        The operation is async – the form will be populated
        when the data arrives via record_loaded signal.

        Args:
            table: Database table name.
            record_id: Primary key value.
        """
        self._target_table = table
        self._record_id = record_id
        self._state_manager.set_state(FormState.LOADING)
        self._data_bridge.load_record(table, record_id)

    def set_record_identity(self, table: str, record_id: int) -> None:
        """
        Set the target table and record ID without loading from DB.

        Use this when you already have the data in memory and just need
        to set the identity for subsequent save operations.

        Args:
            table: Database table name.
            record_id: Primary key value.
        """
        self._target_table = table
        self._record_id = record_id

    def get_combo_display_text(self, field_id: str) -> Optional[str]:
        """
        Get the display text of a combo box field.

        Args:
            field_id: The field identifier.

        Returns:
            The currently displayed text, or None if field not found
            or not a combo box.
        """
        entry = self._widget_map.get(field_id)
        if not entry:
            return None
        _, widget, _ = entry
        if hasattr(widget, 'currentText'):
            text = widget.currentText()
            if text and not text.startswith("--"):
                return text
        return None

    def set_data(self, data: dict[str, Any]) -> None:
        """
        Populate the form with data from a dictionary.

        If combo boxes are still loading, the data is stored as pending
        and will be re-applied once all combos have finished loading.

        Args:
            data: Dict mapping column/field names to values.
        """
        self._state_manager.suppress_tracking()
        try:
            self._populate_fields(data)
            self._state_manager.set_original_values(
                self._collect_values()
            )
        finally:
            self._state_manager.resume_tracking()

        # If combos are still loading, store data so we can re-apply combo
        # values once loading completes (fixes race condition)
        if not self._combos_loaded:
            self._pending_data = copy.deepcopy(data)

    def get_data(self) -> dict[str, Any]:
        """
        Get current form data as a dictionary.

        Returns:
            Dict mapping field_id/column to current values.
        """
        return self._collect_values()

    # -----------------------------------------------------------------------
    # Public API: Validation
    # -----------------------------------------------------------------------

    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate all form fields.

        Skips async rules (e.g. unique checks) to avoid blocking the
        main Qt thread (Rule #13). Unique checks are performed
        asynchronously during the save operation.

        Returns:
            Tuple of (is_valid, error_messages).
        """
        if not self._form_def:
            return True, []

        all_fields = self._get_all_field_defs()
        values = self._collect_values()
        errors = self._validation_engine.validate_all(
            all_fields, values, self._record_id,
            skip_async_rules=True,
        )

        if errors:
            # Show visual errors
            self._validation_engine.clear_all_errors()
            for err in errors:
                widget = self._input_widgets.get(err.field_id)
                if widget:
                    self._validation_engine.show_field_error(
                        err.field_id, widget, err.message
                    )

            # Focus first error
            self._validation_engine.focus_first_error(
                errors, self._input_widgets, self._scroll_area
            )

            messages = [err.message for err in errors]
            self.validation_failed.emit(messages)
            return False, messages

        self._validation_engine.clear_all_errors()
        return True, []

    # -----------------------------------------------------------------------
    # Public API: Save / Cancel / Reset
    # -----------------------------------------------------------------------

    def save(self) -> None:
        """
        Validate and save the form data to the database.

        Emits saved(dict) on success, validation_failed(list) on errors.
        """
        is_valid, errors = self.validate()
        if not is_valid:
            return

        if not self._target_table:
            app_logger.warning("No target table specified for save")
            self._show_error("لم يتم تحديد جدول الحفظ")
            return

        self._state_manager.mark_saving()

        # Collect data mapped to DB columns
        data = self._collect_db_data()

        self._data_bridge.save_record(
            self._target_table, data, self._record_id
        )

    def cancel(self) -> None:
        """
        Cancel editing. If dirty, shows confirmation dialog.
        Emits cancelled() if the user confirms.
        """
        if self._state_manager.is_dirty:
            result = QMessageBox.question(
                self,
                "تأكيد الإلغاء",
                "يوجد تغييرات غير محفوظة. هل تريد الإلغاء؟",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if result != QMessageBox.Yes:
                return

        self.cancelled.emit()

    def reset(self) -> None:
        """Reset the form to its original (loaded) values."""
        values = self._state_manager.reset()
        self._state_manager.suppress_tracking()
        try:
            self._populate_fields(values)
        finally:
            self._state_manager.resume_tracking()
        self._validation_engine.clear_all_errors()

    # -----------------------------------------------------------------------
    # Public API: Field access
    # -----------------------------------------------------------------------

    def get_field_value(self, field_id: str) -> Any:
        """Get the current value of a specific field."""
        entry = self._widget_map.get(field_id)
        if not entry:
            return None
        _, widget, field_def = entry
        return get_widget_value(widget, field_def.get("widget_type", "text_input"))

    def set_field_value(self, field_id: str, value: Any) -> None:
        """Set the value of a specific field."""
        entry = self._widget_map.get(field_id)
        if not entry:
            return
        _, widget, field_def = entry
        set_widget_value(widget, field_def.get("widget_type", "text_input"), value)

    def set_field_visible(self, field_id: str, visible: bool) -> None:
        """Show or hide a field (label + widget)."""
        entry = self._widget_map.get(field_id)
        if not entry:
            return
        label, widget, _ = entry
        widget.setVisible(visible)
        if label:
            label.setVisible(visible)

    def set_field_enabled(self, field_id: str, enabled: bool) -> None:
        """Enable or disable a field."""
        entry = self._widget_map.get(field_id)
        if not entry:
            return
        _, widget, _ = entry
        widget.setEnabled(enabled)

    def is_dirty(self) -> bool:
        """Check if the form has unsaved changes."""
        return self._state_manager.is_dirty

    def get_state(self) -> FormState:
        """Get the current form state."""
        return self._state_manager.state

    # -----------------------------------------------------------------------
    # Public API: Undo / Redo
    # -----------------------------------------------------------------------

    def undo(self) -> None:
        """Undo the last field change."""
        result = self._state_manager.undo()
        if result:
            field_id, value = result
            self._state_manager.suppress_tracking()
            try:
                self.set_field_value(field_id, value)
            finally:
                self._state_manager.resume_tracking()

    def redo(self) -> None:
        """Redo the last undone change."""
        result = self._state_manager.redo()
        if result:
            field_id, value = result
            self._state_manager.suppress_tracking()
            try:
                self.set_field_value(field_id, value)
            finally:
                self._state_manager.resume_tracking()

    # -----------------------------------------------------------------------
    # Public API: Section visibility
    # -----------------------------------------------------------------------

    def set_section_visible(self, section_id: str, visible: bool) -> None:
        """Show or hide a section card."""
        if self._layout_engine:
            self._layout_engine.set_section_visible(section_id, visible)

    # -----------------------------------------------------------------------
    # Public API: Action buttons
    # -----------------------------------------------------------------------

    def get_action_button(self, action_id: str) -> Optional[QPushButton]:
        """Get a reference to an action button by its ID."""
        return self._action_buttons.get(action_id)

    # -----------------------------------------------------------------------
    # Public API: Live edit (Phase 3)
    # -----------------------------------------------------------------------

    def enable_live_edit(self) -> None:
        """
        Enable live editing mode.

        Activates a transparent overlay on top of the form that allows
        visual drag, resize, and property editing of form widgets.
        Changes are saved back to the .iform JSON file.

        Toggle with Ctrl+Shift+E or the toolbar button.
        """
        if self._live_edit_active:
            app_logger.debug("Live edit already active")
            return

        if not self._form_def:
            app_logger.warning("Cannot enable live edit: no form loaded")
            return

        try:
            OverlayClass = _get_overlay_class()

            if self._live_edit_overlay is None:
                self._live_edit_overlay = OverlayClass(self)
                self._live_edit_overlay.edit_saved.connect(self._on_live_edit_saved)
                self._live_edit_overlay.edit_cancelled.connect(self._on_live_edit_cancelled)
                self._live_edit_overlay.form_modified.connect(self._on_live_edit_modified)

            self._live_edit_overlay.activate(
                form_def=self._form_def,
                form_path=self._form_path,
                widget_map=self._widget_map,
                scroll_area=self._scroll_area,
                content_widget=self._content_widget,
            )
            self._live_edit_active = True
            app_logger.info("Live edit mode enabled")

        except Exception:
            app_logger.error("Failed to enable live edit mode", exc_info=True)
            self._show_error("فشل تفعيل وضع التعديل المباشر")

    def disable_live_edit(self) -> None:
        """
        Disable live editing mode.

        If there are unsaved changes, the overlay will prompt the user.
        """
        if not self._live_edit_active or not self._live_edit_overlay:
            return

        self._live_edit_overlay.deactivate()
        self._live_edit_active = False
        app_logger.info("Live edit mode disabled")

    def toggle_live_edit(self) -> None:
        """Toggle live editing mode on/off."""
        if self._live_edit_active:
            self.disable_live_edit()
        else:
            self.enable_live_edit()

    @property
    def is_live_edit_active(self) -> bool:
        """Whether live editing mode is currently active."""
        return self._live_edit_active

    def _on_live_edit_saved(self) -> None:
        """Handle live edit save completion."""
        self._live_edit_active = False
        app_logger.info("Live edit changes saved successfully")

    def _on_live_edit_cancelled(self) -> None:
        """Handle live edit cancellation."""
        self._live_edit_active = False
        app_logger.info("Live edit cancelled")

    def _on_live_edit_modified(self, new_form_def: dict) -> None:
        """Handle form definition modified by live editor."""
        self._form_def = copy.deepcopy(new_form_def)
        app_logger.info("Form definition updated from live editor")

    # -----------------------------------------------------------------------
    # Internal: UI building
    # -----------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Build the complete form UI from the loaded definition."""
        if not self._form_def:
            return

        # Clear existing UI
        self._clear_ui()

        settings = self._form_def.get("settings", {})
        merged_settings = copy.deepcopy(DEFAULT_FORM_SETTINGS)
        # Deep merge: preserve nested dict defaults (e.g. margins)
        for key, value in settings.items():
            if (
                key in merged_settings
                and isinstance(merged_settings[key], dict)
                and isinstance(value, dict)
            ):
                merged_settings[key].update(value)
            else:
                merged_settings[key] = value

        direction = merged_settings.get("direction", "rtl")
        if direction == "rtl":
            self.setLayoutDirection(Qt.RightToLeft)

        self._layout_engine = LayoutEngine(merged_settings)

        # Build header
        self._header_widget = self._build_header()
        if self._header_widget:
            self._main_layout.addWidget(self._header_widget)

        # Create scroll area
        self._scroll_area = QScrollArea(self)
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.NoFrame)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Build all widgets
        self._create_all_widgets()

        # Build section layout
        sections = self._form_def.get("sections", [])
        self._content_widget = self._layout_engine.build_form(
            sections, self._widget_map, self._scroll_area
        )

        # Apply min/max width
        min_w = merged_settings.get("min_width")
        max_w = merged_settings.get("max_width")
        if min_w:
            self._content_widget.setMinimumWidth(int(min_w))
        if max_w:
            self._content_widget.setMaximumWidth(int(max_w))

        self._scroll_area.setWidget(self._content_widget)
        self._main_layout.addWidget(self._scroll_area, 1)

        # Build action bar
        actions = self._form_def.get("actions", [])
        if actions:
            self._action_bar = self._layout_engine.build_action_bar(actions, self)
            self._connect_action_buttons(actions)
            self._main_layout.addWidget(self._action_bar)

        # Load combo data
        self._load_all_combo_data()

        # Apply conditional rules
        self._apply_rules()

    def _build_header(self) -> Optional[QWidget]:
        """Build the form header with title and live edit toggle button."""
        if not self._form_def:
            return None

        title = (
            self._form_def.get("form_name_ar")
            or self._form_def.get("form_name_en", "")
        )
        if not title:
            return None

        header = QWidget(self)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 15, 20, 10)

        title_label = QLabel(title, header)
        title_label.setFont(get_font(size=FONT_SIZE_TITLE, weight=FONT_WEIGHT_BOLD))
        layout.addWidget(title_label)
        layout.addStretch(1)

        # Live edit toggle button
        live_edit_btn = QPushButton("تعديل التصميم", header)
        live_edit_btn.setObjectName("live_edit_toggle")
        live_edit_btn.setFont(get_font(size=FONT_SIZE_BODY))
        live_edit_btn.setCursor(Qt.PointingHandCursor)
        live_edit_btn.setToolTip("تعديل تصميم النموذج مباشرة (Ctrl+Shift+E)")
        live_edit_btn.clicked.connect(lambda: self.toggle_live_edit())

        palette = get_current_palette()
        primary = palette.get("primary", "#3b82f6")
        border = palette.get("border", "#334155")
        text_color = palette.get("text", palette.get("foreground", "#e2e8f0"))
        live_edit_btn.setStyleSheet(
            f"QPushButton {{"
            f"  color: {primary};"
            f"  background: transparent;"
            f"  border: 1px solid {primary};"
            f"  border-radius: 4px;"
            f"  padding: 4px 12px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {primary};"
            f"  color: {palette.get('text_on_primary', '#ffffff')};"
            f"}}"
        )
        layout.addWidget(live_edit_btn)

        # Keyboard shortcut: Ctrl+Shift+E
        shortcut = QShortcut(QKeySequence("Ctrl+Shift+E"), self)
        shortcut.activated.connect(self.toggle_live_edit)

        return header

    def _create_all_widgets(self) -> None:
        """Create widgets for all fields in all sections."""
        if not self._form_def:
            return

        settings = self._form_def.get("settings", {})
        show_required = settings.get("show_required_indicator", True)

        for section in self._form_def.get("sections", []):
            for field_def in section.get("fields", []):
                field_def = merge_with_defaults(field_def)
                field_id = field_def.get("id", "")

                label, widget = self._widget_factory.create(
                    field_def, show_required=show_required
                )

                self._widget_map[field_id] = (label, widget, field_def)
                self._input_widgets[field_id] = widget

                # Connect change signal for dirty tracking
                widget_type = field_def.get("widget_type", "text_input")
                connect_change_signal(
                    widget, widget_type,
                    lambda fid=field_id: self._on_widget_changed(fid),
                )

    def _connect_action_buttons(self, actions: list[dict[str, Any]]) -> None:
        """Connect action buttons to their handlers."""
        if not self._action_bar:
            return

        for action_def in actions:
            action_id = action_def.get("id", "")
            action_type = action_def.get("action", "custom")
            confirm_msg = action_def.get("confirm_message_ar")

            btn = self._action_bar.findChild(QPushButton, f"action_{action_id}")
            if not btn:
                continue

            self._action_buttons[action_id] = btn

            if action_type == "save":
                if confirm_msg:
                    btn.clicked.connect(
                        lambda checked=False, msg=confirm_msg: self._confirm_and_save(msg)
                    )
                else:
                    btn.clicked.connect(lambda checked=False: self.save())

            elif action_type == "cancel":
                btn.clicked.connect(lambda checked=False: self.cancel())

            elif action_type == "delete":
                btn.clicked.connect(lambda checked=False: self._confirm_delete())

            elif action_type in ("navigate", "print"):
                app_logger.info(
                    f"Action type '{action_type}' for button '{action_id}' "
                    f"- connect via get_action_button()"
                )

            # Custom actions are handled by the caller via get_action_button()

    def _load_all_combo_data(self) -> None:
        """Load data for all combo box fields that have query sources."""
        self._combos_loaded = False
        self._combos_loading_count = 0

        for field_id, (_, widget, field_def) in self._widget_map.items():
            if field_def.get("widget_type") != "combo_box":
                continue

            combo_src = field_def.get("combo_source", {})
            if not combo_src or combo_src.get("type") != "query":
                continue

            query = combo_src.get("query", "")
            value_col = combo_src.get("value_column", "id")
            display_col = combo_src.get("display_column", "name_ar")

            if query:
                self._combos_loading_count += 1
                self._data_bridge.load_combo_data(
                    field_id, query, value_col, display_col
                )

        # If no combos need loading, mark as loaded immediately
        if self._combos_loading_count == 0:
            self._combos_loaded = True

    def _apply_rules(self) -> None:
        """Apply conditional logic rules from the form definition."""
        if not self._form_def:
            return

        rules = self._form_def.get("rules", [])
        for rule in rules:
            trigger_field = rule.get("trigger_field", "")
            current_value = self.get_field_value(trigger_field)
            self._execute_rule(rule, current_value)

    # -----------------------------------------------------------------------
    # Internal: Signal handlers
    # -----------------------------------------------------------------------

    def _on_widget_changed(self, field_id: str) -> None:
        """Handle a widget value change."""
        value = self.get_field_value(field_id)
        self._state_manager.on_field_changed(field_id, value)
        self.field_changed.emit(field_id, value)

        # Re-evaluate rules that depend on this field
        self._apply_rules_for_field(field_id)

        # Real-time validation (skip async rules to avoid blocking main thread)
        entry = self._widget_map.get(field_id)
        if entry:
            _, widget, field_def = entry
            errors = self._validation_engine.validate_field(
                field_def, value, self._record_id,
                skip_async_rules=True,
            )
            if errors:
                self._validation_engine.show_field_error(
                    field_id, widget, errors[0].message
                )
            else:
                self._validation_engine.clear_field_error(field_id)

    def _on_record_loaded(self, data: dict[str, Any]) -> None:
        """Handle data loaded from the database."""
        self._state_manager.suppress_tracking()
        try:
            self._populate_fields(data)
            self._state_manager.set_original_values(
                self._collect_values()
            )
        finally:
            self._state_manager.resume_tracking()

    def _on_record_saved(self, record_id: int, data: dict[str, Any]) -> None:
        """Handle successful save."""
        self._record_id = record_id
        self._state_manager.mark_saved()
        self.saved.emit(data)

    def _on_combo_data_loaded(self, field_id: str, items: list) -> None:
        """Populate a combo box with loaded data."""
        widget = self._input_widgets.get(field_id)
        if not isinstance(widget, QComboBox):
            self._combos_loading_count = max(0, self._combos_loading_count - 1)
            self._check_all_combos_loaded()
            return

        # Preserve current selection
        current_data = widget.currentData()

        # Block signals during population
        widget.blockSignals(True)
        try:
            # Keep the default item (index 0) and replace the rest
            while widget.count() > 1:
                widget.removeItem(1)

            for value, display in items:
                widget.addItem(display, value)

            # Restore selection
            if current_data is not None:
                for i in range(widget.count()):
                    if widget.itemData(i) == current_data:
                        widget.setCurrentIndex(i)
                        break
        finally:
            widget.blockSignals(False)

        # Track combo loading progress
        self._combos_loading_count = max(0, self._combos_loading_count - 1)
        self._check_all_combos_loaded()

    def _check_all_combos_loaded(self) -> None:
        """Check if all combos are loaded; if so, re-apply pending data."""
        if self._combos_loading_count > 0:
            return

        self._combos_loaded = True

        # Re-apply pending data to set correct combo selections
        if self._pending_data is not None:
            pending = self._pending_data
            self._pending_data = None
            self._state_manager.suppress_tracking()
            try:
                self._populate_fields(pending)
                self._state_manager.set_original_values(
                    self._collect_values()
                )
            finally:
                self._state_manager.resume_tracking()

    def _on_bridge_error(self, operation: str, message: str) -> None:
        """Handle errors from the data bridge."""
        if operation == "save":
            self._state_manager.mark_error()
        app_logger.error(f"DataBridge error ({operation}): {message}")
        self._show_error(f"خطأ: {message}")

    # -----------------------------------------------------------------------
    # Internal: Data helpers
    # -----------------------------------------------------------------------

    def _populate_fields(self, data: dict[str, Any]) -> None:
        """Set widget values from a data dictionary."""
        for field_id, (_, widget, field_def) in self._widget_map.items():
            binding = field_def.get("data_binding")
            if binding:
                column = binding.get("column", field_id)
                value = data.get(column)
            else:
                value = data.get(field_id)

            if value is not None:
                widget_type = field_def.get("widget_type", "text_input")
                set_widget_value(widget, widget_type, value)

    def _collect_values(self) -> dict[str, Any]:
        """Collect current values from all widgets."""
        values: dict[str, Any] = {}
        for field_id, (_, widget, field_def) in self._widget_map.items():
            widget_type = field_def.get("widget_type", "text_input")
            values[field_id] = get_widget_value(widget, widget_type)
        return values

    def _collect_db_data(self) -> dict[str, Any]:
        """Collect values mapped to database column names."""
        data: dict[str, Any] = {}
        for field_id, (_, widget, field_def) in self._widget_map.items():
            binding = field_def.get("data_binding")
            if not binding:
                continue

            column = binding.get("column", field_id)
            widget_type = field_def.get("widget_type", "text_input")
            value = get_widget_value(widget, widget_type)

            # Skip readonly fields
            props = field_def.get("properties", {})
            if props.get("readonly", False):
                continue

            data[column] = value

        return data

    def _get_all_field_defs(self) -> list[dict[str, Any]]:
        """Get all field definitions from all sections."""
        fields = []
        if self._form_def:
            for section in self._form_def.get("sections", []):
                for field_def in section.get("fields", []):
                    fields.append(merge_with_defaults(field_def))
        return fields

    def _apply_rules_for_field(self, changed_field_id: str) -> None:
        """Re-evaluate rules triggered by a specific field change."""
        if not self._form_def:
            return

        rules = self._form_def.get("rules", [])
        for rule in rules:
            if rule.get("trigger_field") == changed_field_id:
                current_value = self.get_field_value(changed_field_id)
                self._execute_rule(rule, current_value)

    def _execute_rule(
        self, rule: dict[str, Any], current_value: Any
    ) -> None:
        """
        Execute a single conditional rule based on the current trigger value.

        Centralises the rule-action mapping so that _apply_rules and
        _apply_rules_for_field stay consistent.
        """
        trigger_value = rule.get("trigger_value")
        action = rule.get("action", "")
        target = rule.get("target", "")
        should_apply = (current_value == trigger_value)

        if action == "hide_field":
            self.set_field_visible(target, not should_apply)
        elif action == "show_field":
            self.set_field_visible(target, should_apply)
        elif action == "hide_section":
            self.set_section_visible(target, not should_apply)
        elif action == "show_section":
            self.set_section_visible(target, should_apply)
        elif action == "enable_field":
            self.set_field_enabled(target, should_apply)
        elif action == "disable_field":
            self.set_field_enabled(target, not should_apply)
        elif action == "set_value":
            new_value = rule.get("value")
            if should_apply and new_value is not None:
                self.set_field_value(target, new_value)
        elif action == "set_required":
            app_logger.debug(
                f"set_required rule for '{target}' - "
                f"dynamic required not yet implemented"
            )
        else:
            app_logger.warning(f"Unknown rule action '{action}' for target '{target}'")

    # -----------------------------------------------------------------------
    # Internal: Confirm dialogs
    # -----------------------------------------------------------------------

    def _confirm_and_save(self, message: str) -> None:
        """Show confirmation dialog, then save if confirmed."""
        result = QMessageBox.question(
            self,
            "تأكيد الحفظ",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if result == QMessageBox.Yes:
            self.save()

    def _confirm_delete(self) -> None:
        """Confirm and delete the current record."""
        if not self._target_table or not self._record_id:
            return

        result = QMessageBox.warning(
            self,
            "تأكيد الحذف",
            "هل أنت متأكد من حذف هذا السجل؟\nلا يمكن التراجع عن هذا الإجراء.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if result == QMessageBox.Yes:
            self._data_bridge.delete_record(self._target_table, self._record_id)

    # -----------------------------------------------------------------------
    # Internal: Error display
    # -----------------------------------------------------------------------

    def _show_error(self, message: str) -> None:
        """Show an error message to the user."""
        try:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("خطأ")
            msg_box.setText(message)
            msg_box.setTextFormat(Qt.PlainText)
            msg_box.exec_()
        except Exception:
            app_logger.error(f"Could not show error dialog: {message}")

    # -----------------------------------------------------------------------
    # Cleanup
    # -----------------------------------------------------------------------

    def _clear_ui(self) -> None:
        """
        Remove all widgets from the form layout.
        Follows Rule #6: proper widget lifecycle cleanup.
        """
        # Deactivate live edit if active
        if self._live_edit_active and self._live_edit_overlay:
            self._live_edit_overlay.deactivate()
            self._live_edit_active = False

        self._validation_engine.clear_all_errors()

        # Release cached widget references in layout engine (Rule #6)
        if self._layout_engine:
            self._layout_engine.clear()

        # Clear widget map references first, then delete
        self._widget_map.clear()
        self._input_widgets.clear()
        self._action_buttons.clear()

        # Remove children from main layout
        if self._main_layout:
            while self._main_layout.count():
                child = self._main_layout.takeAt(0)
                widget = child.widget()
                if widget:
                    widget.deleteLater()

        self._scroll_area = None
        self._content_widget = None
        self._action_bar = None
        self._header_widget = None
        self._combos_loaded = False
        self._combos_loading_count = 0
        self._pending_data = None

    def closeEvent(self, event) -> None:  # noqa: N802
        """Handle close with unsaved changes check."""
        # Disable live edit first if active
        if self._live_edit_active and self._live_edit_overlay:
            self._live_edit_overlay.deactivate()
            self._live_edit_active = False

        if self._state_manager.is_dirty:
            result = QMessageBox.question(
                self,
                "تغييرات غير محفوظة",
                "يوجد تغييرات غير محفوظة. هل تريد الإغلاق؟",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if result != QMessageBox.Yes:
                event.ignore()
                return

        # Clean up live edit overlay
        if self._live_edit_overlay:
            self._live_edit_overlay.deleteLater()
            self._live_edit_overlay = None

        self._clear_ui()
        super().closeEvent(event)
