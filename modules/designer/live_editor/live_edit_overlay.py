"""
Live Edit Overlay for INTEGRA Form System.

A transparent overlay widget that sits on top of a rendered form,
enabling visual editing of widget positions, sizes, and properties.

Features:
- Click to select any widget in the form
- Drag to move widgets
- Resize handles for changing widget dimensions
- Snap guides for alignment assistance
- Property popup for quick edits
- Toolbar with save/cancel/undo/redo
- Section reordering via drag
- Double-click for property popup
- Keyboard shortcuts (Delete, Ctrl+Z, Ctrl+Y, Escape)
- Auto-backup of .iform before modifications

Architecture:
- LiveEditOverlay sits as a transparent child of the FormRenderer scroll area
- It intercepts mouse events while letting the form remain visible underneath
- Changes are tracked as an undo stack and saved to .iform JSON on confirm

Follows all 13 INTEGRA mandatory rules:
- Rule #6: Proper widget lifecycle cleanup
- Rule #7: int() for all Qt size operations
- Rule #9: Error handling with app_logger
- Rule #11: Theme-aware colors from get_current_palette()
- Rule #13: File I/O in background threads via run_in_background
"""

from __future__ import annotations

import copy
import os
import shutil
from datetime import datetime
from typing import Any, Optional

from PyQt5.QtCore import Qt, QPoint, QRect, QEvent, pyqtSignal, QTimer
from PyQt5.QtGui import QPainter, QPen, QColor, QKeySequence
from PyQt5.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
    QApplication,
    QMessageBox,
)

from core.threading import run_in_background

from core.logging import app_logger
from core.themes import (
    get_current_palette,
    get_font,
    FONT_SIZE_BODY,
    FONT_SIZE_SMALL,
    FONT_WEIGHT_BOLD,
)
from modules.designer.live_editor.selection_handles import (
    SelectionHandles,
    HandlePosition,
)
from modules.designer.live_editor.snap_guides import (
    SnapGuideEngine,
    SnapResult,
)
from modules.designer.live_editor.property_popup import PropertyPopup
from modules.designer.shared.form_schema import save_form_file, validate_form_schema


# ---------------------------------------------------------------------------
# Undo entry for layout changes
# ---------------------------------------------------------------------------

class _LayoutUndoEntry:
    """Records a single layout change for undo/redo."""
    __slots__ = ("field_id", "property_name", "old_value", "new_value")

    def __init__(
        self,
        field_id: str,
        property_name: str,
        old_value: Any,
        new_value: Any,
    ) -> None:
        self.field_id = field_id
        self.property_name = property_name
        self.old_value = old_value
        self.new_value = new_value


# ---------------------------------------------------------------------------
# Toolbar
# ---------------------------------------------------------------------------

class _LiveEditToolbar(QWidget):
    """Toolbar for live edit mode with save/cancel/undo/redo."""

    save_clicked = pyqtSignal()
    cancel_clicked = pyqtSignal()
    undo_clicked = pyqtSignal()
    redo_clicked = pyqtSignal()
    reset_clicked = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(40)
        self._init_ui()
        self._apply_theme()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(8)

        # Mode indicator
        mode_label = QLabel("وضع التعديل المباشر", self)
        mode_label.setFont(get_font(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD))
        layout.addWidget(mode_label)

        layout.addStretch(1)

        # Undo
        self._undo_btn = QPushButton("تراجع", self)
        self._undo_btn.setFont(get_font(size=FONT_SIZE_SMALL))
        self._undo_btn.setCursor(Qt.PointingHandCursor)
        self._undo_btn.setShortcut(QKeySequence.Undo)
        self._undo_btn.setEnabled(False)
        self._undo_btn.clicked.connect(self.undo_clicked)
        layout.addWidget(self._undo_btn)

        # Redo
        self._redo_btn = QPushButton("إعادة", self)
        self._redo_btn.setFont(get_font(size=FONT_SIZE_SMALL))
        self._redo_btn.setCursor(Qt.PointingHandCursor)
        self._redo_btn.setShortcut(QKeySequence.Redo)
        self._redo_btn.setEnabled(False)
        self._redo_btn.clicked.connect(self.redo_clicked)
        layout.addWidget(self._redo_btn)

        # Separator
        sep = QFrame(self)
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setFixedWidth(1)
        layout.addWidget(sep)

        # Reset
        self._reset_btn = QPushButton("إعادة ضبط", self)
        self._reset_btn.setFont(get_font(size=FONT_SIZE_SMALL))
        self._reset_btn.setCursor(Qt.PointingHandCursor)
        self._reset_btn.clicked.connect(self.reset_clicked)
        layout.addWidget(self._reset_btn)

        # Save
        self._save_btn = QPushButton("حفظ التصميم", self)
        self._save_btn.setFont(get_font(size=FONT_SIZE_SMALL, weight=FONT_WEIGHT_BOLD))
        self._save_btn.setCursor(Qt.PointingHandCursor)
        self._save_btn.clicked.connect(self.save_clicked)
        layout.addWidget(self._save_btn)

        # Cancel
        self._cancel_btn = QPushButton("إلغاء", self)
        self._cancel_btn.setFont(get_font(size=FONT_SIZE_SMALL))
        self._cancel_btn.setCursor(Qt.PointingHandCursor)
        self._cancel_btn.clicked.connect(self.cancel_clicked)
        layout.addWidget(self._cancel_btn)

    def set_undo_enabled(self, enabled: bool) -> None:
        self._undo_btn.setEnabled(enabled)

    def set_redo_enabled(self, enabled: bool) -> None:
        self._redo_btn.setEnabled(enabled)

    def _apply_theme(self) -> None:
        palette = get_current_palette()
        bg = palette.get("surface", "#1e293b")
        border = palette.get("border", "#334155")
        text_color = palette.get("text", palette.get("foreground", "#e2e8f0"))
        primary = palette.get("primary", "#3b82f6")
        danger = palette.get("danger", "#ef4444")

        self.setStyleSheet(
            f"_LiveEditToolbar {{"
            f"  background-color: {bg};"
            f"  border-bottom: 2px solid {primary};"
            f"}}"
            f"QLabel {{"
            f"  color: {primary};"
            f"  background: transparent;"
            f"  border: none;"
            f"}}"
            f"QPushButton {{"
            f"  background-color: {palette.get('background', '#0f172a')};"
            f"  color: {text_color};"
            f"  border: 1px solid {border};"
            f"  border-radius: 4px;"
            f"  padding: 4px 12px;"
            f"  min-height: 24px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {border};"
            f"}}"
            f"QPushButton:disabled {{"
            f"  color: {palette.get('text_muted', '#64748b')};"
            f"  background-color: {palette.get('background', '#0f172a')};"
            f"}}"
        )

        # Save button special styling
        self._save_btn.setStyleSheet(
            f"QPushButton {{"
            f"  background-color: {primary};"
            f"  color: white;"
            f"  border: none;"
            f"  border-radius: 4px;"
            f"  padding: 4px 16px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {palette.get('primary_hover', '#1d4ed8')};"
            f"}}"
        )

        # Cancel button styling
        self._cancel_btn.setStyleSheet(
            f"QPushButton {{"
            f"  color: {danger};"
            f"  border-color: {danger};"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {danger};"
            f"  color: white;"
            f"}}"
        )


# ---------------------------------------------------------------------------
# Main Overlay
# ---------------------------------------------------------------------------

class LiveEditOverlay(QWidget):
    """
    Transparent overlay for live editing form layouts.

    This widget is placed on top of the FormRenderer's scroll area
    content. It intercepts mouse events to allow selection, dragging,
    and resizing of form widgets.

    Signals:
        edit_saved(): Emitted when changes are saved to the .iform file.
        edit_cancelled(): Emitted when editing is cancelled.
        form_modified(dict): Emitted with the modified form definition.
    """

    edit_saved = pyqtSignal()
    edit_cancelled = pyqtSignal()
    form_modified = pyqtSignal(dict)

    def __init__(
        self,
        form_renderer: Any,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("LiveEditOverlay")
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        # Reference to the FormRenderer
        self._renderer = form_renderer

        # Editing state
        self._form_def: Optional[dict[str, Any]] = None
        self._original_form_def: Optional[dict[str, Any]] = None
        self._form_path: Optional[str] = None

        # Widget mapping: field_id -> widget reference
        self._editable_widgets: dict[str, QWidget] = {}
        # field_id -> original geometry (for undo at activation level)
        self._original_geometries: dict[str, QRect] = {}

        # Selection state
        self._selected_field_id: Optional[str] = None

        # Drag state
        self._dragging = False
        self._drag_start_pos: Optional[QPoint] = None
        self._drag_widget_start_rect: Optional[QRect] = None

        # Resize state
        self._resizing = False
        self._resize_handle: HandlePosition = HandlePosition.NONE
        self._resize_start_pos: Optional[QPoint] = None

        # Undo/redo
        self._undo_stack: list[_LayoutUndoEntry] = []
        self._redo_stack: list[_LayoutUndoEntry] = []

        # Sub-components
        self._handles = SelectionHandles()
        self._snap_engine = SnapGuideEngine()
        self._property_popup: Optional[PropertyPopup] = None
        self._current_snap_result: Optional[SnapResult] = None

        # Toolbar
        self._toolbar: Optional[_LiveEditToolbar] = None

        # Re-entrance guard for mouse events
        self._processing_event = False

        # Save-in-progress guard (prevents double Ctrl+S)
        self._saving = False

    # -----------------------------------------------------------------------
    # Activation / Deactivation
    # -----------------------------------------------------------------------

    def activate(
        self,
        form_def: dict[str, Any],
        form_path: Optional[str],
        widget_map: dict[str, tuple],
        scroll_area: Optional[QScrollArea],
        content_widget: Optional[QWidget],
    ) -> None:
        """
        Activate live edit mode.

        Args:
            form_def: The current form definition dict.
            form_path: Path to the .iform file (for saving).
            widget_map: FormRenderer's widget_map (field_id -> (label, widget, field_def)).
            scroll_area: The scroll area containing the form.
            content_widget: The content widget inside scroll_area.
        """
        app_logger.info("Live edit mode activated")

        # Deep copy for independent editing
        self._form_def = copy.deepcopy(form_def)
        self._original_form_def = copy.deepcopy(form_def)
        self._form_path = form_path

        # Build editable widget map
        self._editable_widgets.clear()
        self._original_geometries.clear()

        for field_id, (label, widget, field_def) in widget_map.items():
            self._editable_widgets[field_id] = widget
            self._original_geometries[field_id] = QRect(widget.geometry())

        # Clear undo/redo
        self._undo_stack.clear()
        self._redo_stack.clear()

        # Create auto-backup if form_path exists
        if form_path:
            self._create_backup(form_path)

        # Set up overlay geometry to cover the content widget
        if content_widget:
            self.setParent(content_widget)
            self.setGeometry(content_widget.rect())
            content_widget.installEventFilter(self)

        # Build snap reference rects
        self._rebuild_snap_references()

        # Create toolbar
        self._create_toolbar()

        # Create property popup (Rule #6: pass parent for lifecycle management)
        if self._property_popup is not None:
            self._property_popup.deleteLater()
            self._property_popup = None

        self._property_popup = PropertyPopup(parent=self)
        self._property_popup.property_changed.connect(self._on_popup_property_changed)
        self._property_popup.delete_requested.connect(self._on_delete_field)
        self._property_popup.duplicate_requested.connect(self._on_duplicate_field)
        self._property_popup.advanced_requested.connect(self._on_advanced_properties)

        # Show overlay
        self.show()
        self.raise_()
        self.setFocus()
        self.update()

    def deactivate(self) -> None:
        """Deactivate live edit mode and clean up."""
        app_logger.info("Live edit mode deactivated")

        # Clean up property popup (Rule #6: deleteLater + set to None)
        if self._property_popup:
            self._property_popup.hide_popup()
            self._property_popup.deleteLater()
            self._property_popup = None

        # Remove toolbar
        if self._toolbar:
            self._toolbar.setParent(None)
            self._toolbar.deleteLater()
            self._toolbar = None

        # Clear selection
        self._selected_field_id = None
        self._handles.clear()
        self._snap_engine.clear()

        # Clear state
        self._form_def = None
        self._original_form_def = None
        self._editable_widgets.clear()
        self._original_geometries.clear()
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._dragging = False
        self._resizing = False
        self._current_snap_result = None

        # Remove event filter
        if self.parent():
            self.parent().removeEventFilter(self)

        self.hide()

    def is_active(self) -> bool:
        """Whether live edit mode is currently active."""
        return self._form_def is not None and self.isVisible()

    # -----------------------------------------------------------------------
    # Toolbar
    # -----------------------------------------------------------------------

    def _create_toolbar(self) -> None:
        """Create the live edit toolbar at the top of the renderer."""
        # Rule #6: Remove from layout THEN deleteLater
        renderer = self._renderer
        if self._toolbar:
            if hasattr(renderer, '_main_layout') and renderer._main_layout:
                renderer._main_layout.removeWidget(self._toolbar)
            self._toolbar.deleteLater()
            self._toolbar = None

        # Find the renderer's main layout and insert toolbar at top
        if hasattr(renderer, '_main_layout') and renderer._main_layout:
            self._toolbar = _LiveEditToolbar(renderer)
            renderer._main_layout.insertWidget(0, self._toolbar)

            self._toolbar.save_clicked.connect(self._save_changes)
            self._toolbar.cancel_clicked.connect(self._cancel_changes)
            self._toolbar.undo_clicked.connect(self._undo)
            self._toolbar.redo_clicked.connect(self._redo)
            self._toolbar.reset_clicked.connect(self._reset_all)

    def _update_toolbar_state(self) -> None:
        """Update undo/redo button states."""
        if self._toolbar:
            self._toolbar.set_undo_enabled(len(self._undo_stack) > 0)
            self._toolbar.set_redo_enabled(len(self._redo_stack) > 0)

    # -----------------------------------------------------------------------
    # Backup
    # -----------------------------------------------------------------------

    @staticmethod
    def _create_backup(form_path: str) -> None:
        """
        Create a backup of the .iform file before editing.
        Runs file I/O in background thread (Rule #13).
        """
        if not os.path.exists(form_path):
            return

        def _do_backup() -> str:
            """Background task: copy file and clean old backups."""
            backup_dir = os.path.join(os.path.dirname(form_path), ".backups")
            os.makedirs(backup_dir, exist_ok=True)

            base_name = os.path.basename(form_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{base_name}.{timestamp}.bak"
            backup_path = os.path.join(backup_dir, backup_name)

            shutil.copy2(form_path, backup_path)

            # Clean old backups (keep last 10)
            backups = sorted(
                [
                    f for f in os.listdir(backup_dir)
                    if f.startswith(base_name) and f.endswith(".bak")
                ],
                reverse=True,
            )
            for old_backup in backups[10:]:
                old_path = os.path.join(backup_dir, old_backup)
                try:
                    os.remove(old_path)
                except OSError as exc:
                    app_logger.warning(f"Could not remove old backup {old_path}: {exc}")

            return backup_path

        def _on_backup_done(result: str) -> None:
            app_logger.info(f"Created backup: {result}")

        def _on_backup_error(exc_type, message, traceback) -> None:
            app_logger.warning(f"Could not create backup: {message}")

        run_in_background(
            _do_backup,
            on_finished=_on_backup_done,
            on_error=_on_backup_error,
        )

    # -----------------------------------------------------------------------
    # Snap reference building
    # -----------------------------------------------------------------------

    def _rebuild_snap_references(self, exclude_id: Optional[str] = None) -> None:
        """Rebuild snap engine reference rects from all editable widgets."""
        rects = []
        for fid, widget in self._editable_widgets.items():
            if fid == exclude_id:
                continue
            if widget.isVisible():
                rects.append((fid, widget.geometry()))

        self._snap_engine.set_reference_rects(rects)

        # Set container rect from parent
        if self.parent() and hasattr(self.parent(), 'rect'):
            parent_widget = self.parent()
            if isinstance(parent_widget, QWidget):
                self._snap_engine.set_container_rect(parent_widget.rect())

    # -----------------------------------------------------------------------
    # Selection
    # -----------------------------------------------------------------------

    def _select_widget_at(self, pos: QPoint) -> Optional[str]:
        """Find and select the widget under the given position."""
        # Check widgets in reverse order (top-most first)
        for field_id, widget in reversed(list(self._editable_widgets.items())):
            if not widget.isVisible():
                continue
            if widget.geometry().contains(pos):
                self._select_field(field_id)
                return field_id

        # Clicked empty area - deselect
        self._deselect()
        return None

    def _select_field(self, field_id: str) -> None:
        """Select a specific field by ID."""
        if self._selected_field_id == field_id:
            return

        self._selected_field_id = field_id
        widget = self._editable_widgets.get(field_id)
        if widget:
            self._handles.set_target_rect(widget.geometry())
            self._rebuild_snap_references(exclude_id=field_id)

        self.update()

    def _deselect(self) -> None:
        """Clear the current selection."""
        self._selected_field_id = None
        self._handles.clear()

        if self._property_popup:
            self._property_popup.hide_popup()

        self.update()

    # -----------------------------------------------------------------------
    # Mouse events
    # -----------------------------------------------------------------------

    def mousePressEvent(self, event) -> None:  # noqa: N802
        """Handle mouse press - start selection, drag, or resize."""
        if self._processing_event:
            return
        self._processing_event = True

        try:
            if event.button() != Qt.LeftButton:
                return

            pos = event.pos()

            # Check if clicking on a handle of the selected widget
            if self._selected_field_id:
                handle = self._handles.hit_test(pos)
                if handle != HandlePosition.NONE:
                    self._start_resize(handle, pos)
                    return

            # Check if clicking on a widget
            field_id = self._select_widget_at(pos)
            if field_id:
                self._start_drag(pos)
        finally:
            self._processing_event = False

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        """Handle mouse move - drag, resize, or update cursor."""
        if self._processing_event:
            return
        self._processing_event = True

        try:
            pos = event.pos()

            if self._dragging:
                self._continue_drag(pos)
            elif self._resizing:
                self._continue_resize(pos)
            else:
                # Update cursor based on handle hover
                self._update_hover_cursor(pos)
        finally:
            self._processing_event = False

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        """Handle mouse release - finish drag or resize."""
        if self._processing_event:
            return
        self._processing_event = True

        try:
            if event.button() != Qt.LeftButton:
                return

            if self._dragging:
                self._finish_drag()
            elif self._resizing:
                self._finish_resize()

            self._current_snap_result = None
            self.update()
        finally:
            self._processing_event = False

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        """Double-click to open property popup."""
        if event.button() != Qt.LeftButton:
            return

        pos = event.pos()
        field_id = self._select_widget_at(pos)
        if field_id:
            self._show_property_popup(field_id)

    # -----------------------------------------------------------------------
    # Keyboard events
    # -----------------------------------------------------------------------

    def keyPressEvent(self, event) -> None:  # noqa: N802
        """Handle keyboard shortcuts."""
        key = event.key()
        modifiers = event.modifiers()

        if key == Qt.Key_Escape:
            if self._property_popup and self._property_popup.isVisible():
                self._property_popup.hide_popup()
            else:
                self._cancel_changes()

        elif key == Qt.Key_Delete and self._selected_field_id:
            self._on_delete_field(self._selected_field_id)

        elif key == Qt.Key_Z and modifiers & Qt.ControlModifier:
            if modifiers & Qt.ShiftModifier:
                self._redo()
            else:
                self._undo()

        elif key == Qt.Key_Y and modifiers & Qt.ControlModifier:
            self._redo()

        elif key == Qt.Key_S and modifiers & Qt.ControlModifier:
            self._save_changes()

        elif key == Qt.Key_A and modifiers & Qt.ControlModifier:
            # Select all - not applicable, just ignore
            pass

        else:
            # Arrow keys for nudging selected widget
            if self._selected_field_id:
                nudge = 5 if modifiers & Qt.ShiftModifier else 1
                if key == Qt.Key_Left:
                    self._nudge_selected(-nudge, 0)
                elif key == Qt.Key_Right:
                    self._nudge_selected(nudge, 0)
                elif key == Qt.Key_Up:
                    self._nudge_selected(0, -nudge)
                elif key == Qt.Key_Down:
                    self._nudge_selected(0, nudge)
                else:
                    super().keyPressEvent(event)
            else:
                super().keyPressEvent(event)

    # -----------------------------------------------------------------------
    # Drag operations
    # -----------------------------------------------------------------------

    def _start_drag(self, pos: QPoint) -> None:
        """Start dragging the selected widget."""
        if not self._selected_field_id:
            return

        widget = self._editable_widgets.get(self._selected_field_id)
        if not widget:
            return

        self._dragging = True
        self._drag_start_pos = QPoint(pos)
        self._drag_widget_start_rect = QRect(widget.geometry())
        self.setCursor(Qt.ClosedHandCursor)

    def _continue_drag(self, pos: QPoint) -> None:
        """Continue dragging - move widget to new position with snapping."""
        if not self._selected_field_id or not self._drag_start_pos or not self._drag_widget_start_rect:
            return

        widget = self._editable_widgets.get(self._selected_field_id)
        if not widget:
            return

        delta = pos - self._drag_start_pos
        new_rect = QRect(self._drag_widget_start_rect)
        new_rect.moveTopLeft(
            QPoint(
                new_rect.left() + delta.x(),
                new_rect.top() + delta.y(),
            )
        )

        # Apply snapping
        snap_result = self._snap_engine.calculate_snap(
            new_rect, excluded_id=self._selected_field_id
        )
        if snap_result.snapped_x:
            new_rect.moveLeft(new_rect.left() + snap_result.delta_x)
        if snap_result.snapped_y:
            new_rect.moveTop(new_rect.top() + snap_result.delta_y)

        self._current_snap_result = snap_result

        # Constrain to parent bounds
        if self.parent() and isinstance(self.parent(), QWidget):
            parent_rect = self.parent().rect()
            if new_rect.left() < 0:
                new_rect.moveLeft(0)
            if new_rect.top() < 0:
                new_rect.moveTop(0)
            if new_rect.right() > parent_rect.right():
                new_rect.moveRight(parent_rect.right())
            if new_rect.bottom() > parent_rect.bottom():
                new_rect.moveBottom(parent_rect.bottom())

        # Move widget
        widget.setGeometry(new_rect)
        self._handles.set_target_rect(new_rect)
        self.update()

    def _finish_drag(self) -> None:
        """Finish dragging - record the change."""
        if not self._selected_field_id or not self._drag_widget_start_rect:
            self._dragging = False
            self.setCursor(Qt.ArrowCursor)
            return

        widget = self._editable_widgets.get(self._selected_field_id)
        if widget:
            new_rect = widget.geometry()
            old_rect = self._drag_widget_start_rect

            # Only record if actually moved
            if new_rect.topLeft() != old_rect.topLeft():
                self._record_geometry_change(
                    self._selected_field_id, old_rect, new_rect
                )

        self._dragging = False
        self._drag_start_pos = None
        self._drag_widget_start_rect = None
        self.setCursor(Qt.ArrowCursor)

    # -----------------------------------------------------------------------
    # Resize operations
    # -----------------------------------------------------------------------

    def _start_resize(self, handle: HandlePosition, pos: QPoint) -> None:
        """Start resizing from a handle."""
        if not self._selected_field_id:
            return

        widget = self._editable_widgets.get(self._selected_field_id)
        if not widget:
            return

        self._resizing = True
        self._resize_handle = handle
        self._resize_start_pos = QPoint(pos)
        self._drag_widget_start_rect = QRect(widget.geometry())
        self.setCursor(self._handles.get_cursor(handle))

    def _continue_resize(self, pos: QPoint) -> None:
        """Continue resizing - update widget size."""
        if (
            not self._selected_field_id
            or not self._resize_start_pos
            or not self._drag_widget_start_rect
        ):
            return

        widget = self._editable_widgets.get(self._selected_field_id)
        if not widget:
            return

        delta = pos - self._resize_start_pos
        keep_aspect = bool(QApplication.keyboardModifiers() & Qt.ShiftModifier)

        # Reset to original before calculating new rect
        self._handles.set_target_rect(self._drag_widget_start_rect)
        new_rect = self._handles.calculate_resize(
            self._resize_handle, delta, keep_aspect
        )

        # Apply snapping
        snap_result = self._snap_engine.calculate_snap(
            new_rect, excluded_id=self._selected_field_id
        )
        if snap_result.snapped_x:
            # Adjust the appropriate edge based on handle
            if self._resize_handle in (
                HandlePosition.RIGHT,
                HandlePosition.TOP_RIGHT,
                HandlePosition.BOTTOM_RIGHT,
            ):
                new_rect.setRight(new_rect.right() + snap_result.delta_x)
            elif self._resize_handle in (
                HandlePosition.LEFT,
                HandlePosition.TOP_LEFT,
                HandlePosition.BOTTOM_LEFT,
            ):
                new_rect.setLeft(new_rect.left() + snap_result.delta_x)

        if snap_result.snapped_y:
            if self._resize_handle in (
                HandlePosition.BOTTOM,
                HandlePosition.BOTTOM_LEFT,
                HandlePosition.BOTTOM_RIGHT,
            ):
                new_rect.setBottom(new_rect.bottom() + snap_result.delta_y)
            elif self._resize_handle in (
                HandlePosition.TOP,
                HandlePosition.TOP_LEFT,
                HandlePosition.TOP_RIGHT,
            ):
                new_rect.setTop(new_rect.top() + snap_result.delta_y)

        self._current_snap_result = snap_result

        widget.setGeometry(new_rect)
        self._handles.set_target_rect(new_rect)
        self.update()

    def _finish_resize(self) -> None:
        """Finish resizing - record the change."""
        if not self._selected_field_id or not self._drag_widget_start_rect:
            self._resizing = False
            self._resize_handle = HandlePosition.NONE
            self.setCursor(Qt.ArrowCursor)
            return

        widget = self._editable_widgets.get(self._selected_field_id)
        if widget:
            new_rect = widget.geometry()
            old_rect = self._drag_widget_start_rect

            if new_rect != old_rect:
                self._record_geometry_change(
                    self._selected_field_id, old_rect, new_rect
                )

        self._resizing = False
        self._resize_handle = HandlePosition.NONE
        self._resize_start_pos = None
        self._drag_widget_start_rect = None
        self.setCursor(Qt.ArrowCursor)

    # -----------------------------------------------------------------------
    # Nudge (arrow keys)
    # -----------------------------------------------------------------------

    def _nudge_selected(self, dx: int, dy: int) -> None:
        """Move the selected widget by a small amount."""
        if not self._selected_field_id:
            return

        widget = self._editable_widgets.get(self._selected_field_id)
        if not widget:
            return

        old_rect = QRect(widget.geometry())
        new_rect = QRect(old_rect)
        new_rect.moveTopLeft(QPoint(old_rect.left() + dx, old_rect.top() + dy))

        widget.setGeometry(new_rect)
        self._handles.set_target_rect(new_rect)
        self._record_geometry_change(self._selected_field_id, old_rect, new_rect)
        self.update()

    # -----------------------------------------------------------------------
    # Cursor update
    # -----------------------------------------------------------------------

    def _update_hover_cursor(self, pos: QPoint) -> None:
        """Update cursor based on what's under the mouse."""
        if self._selected_field_id:
            handle = self._handles.hit_test(pos)
            self._handles.set_hovered(handle)

            if handle != HandlePosition.NONE:
                self.setCursor(self._handles.get_cursor(handle))
                self.update()
                return

        # Check if hovering over any widget
        for field_id, widget in self._editable_widgets.items():
            if widget.isVisible() and widget.geometry().contains(pos):
                self.setCursor(Qt.OpenHandCursor)
                self.update()
                return

        self.setCursor(Qt.ArrowCursor)
        self._handles.set_hovered(HandlePosition.NONE)
        self.update()

    # -----------------------------------------------------------------------
    # Property popup
    # -----------------------------------------------------------------------

    def _show_property_popup(self, field_id: str) -> None:
        """Show the property popup for a field."""
        if not self._property_popup or not self._form_def:
            return

        widget = self._editable_widgets.get(field_id)
        if not widget:
            return

        # Find field definition
        field_def = self._find_field_def(field_id)
        if not field_def:
            return

        # Get widget rect in screen coordinates
        widget_rect = QRect(
            widget.mapToGlobal(QPoint(0, 0)),
            widget.size(),
        )
        parent_rect = QRect(
            self.mapToGlobal(QPoint(0, 0)),
            self.size(),
        )

        self._property_popup.show_for_field(
            field_id, field_def, widget_rect, parent_rect
        )

    # -----------------------------------------------------------------------
    # Property change handlers
    # -----------------------------------------------------------------------

    def _on_popup_property_changed(
        self,
        field_id: str,
        prop_name: str,
        value: Any,
    ) -> None:
        """Handle property change from the popup."""
        if not self._form_def:
            return

        widget = self._editable_widgets.get(field_id)
        if not widget:
            return

        old_value = None

        if prop_name == "width":
            old_value = widget.width()
            widget.setFixedWidth(int(value))
        elif prop_name == "height":
            old_value = widget.height()
            widget.setFixedHeight(int(value))
        elif prop_name == "label_ar":
            field_def = self._find_field_def(field_id)
            if field_def:
                old_value = field_def.get("label_ar")
                self._update_field_in_form_def(field_id, "label_ar", value)
        elif prop_name == "readonly":
            field_def = self._find_field_def(field_id)
            if field_def:
                props = field_def.get("properties", {})
                old_value = props.get("readonly", False)
                self._update_field_property(field_id, "readonly", value)
        elif prop_name == "visible":
            field_def = self._find_field_def(field_id)
            if field_def:
                props = field_def.get("properties", {})
                old_value = props.get("visible", True)
                self._update_field_property(field_id, "visible", value)

        # Record undo
        if old_value != value:
            entry = _LayoutUndoEntry(field_id, prop_name, old_value, value)
            self._undo_stack.append(entry)
            self._redo_stack.clear()
            self._update_toolbar_state()

        # Refresh handles
        if prop_name in ("width", "height") and widget:
            self._handles.set_target_rect(widget.geometry())

        self.update()

    def _on_delete_field(self, field_id: str) -> None:
        """Handle field deletion request."""
        result = QMessageBox.question(
            self,
            "تأكيد الحذف",
            "هل تريد حذف هذا الحقل؟\n(الحذف لا يمكن التراجع عنه)",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if result != QMessageBox.Yes:
            return

        # Remove from form definition
        if self._form_def:
            for section in self._form_def.get("sections", []):
                fields = section.get("fields", [])
                for i, field in enumerate(fields):
                    if field.get("id") == field_id:
                        fields.pop(i)
                        break

        # Hide the widget
        widget = self._editable_widgets.get(field_id)
        if widget:
            widget.setVisible(False)

        # Deselect
        if self._selected_field_id == field_id:
            self._deselect()

        # Remove from tracking
        self._editable_widgets.pop(field_id, None)

        if self._property_popup:
            self._property_popup.hide_popup()

        self.update()
        app_logger.info(f"Field '{field_id}' deleted in live edit mode")

    def _on_duplicate_field(self, field_id: str) -> None:
        """Handle field duplication request (logged but not fully implemented)."""
        app_logger.info(
            f"Duplicate requested for field '{field_id}' - "
            f"use the Form Builder for adding new fields"
        )
        QMessageBox.information(
            self,
            "نسخ الحقل",
            "لإضافة حقول جديدة، استخدم مصمم النماذج (Form Builder).\n"
            "وضع التعديل المباشر مخصص لتعديل المواقع والأحجام.",
        )

    def _on_advanced_properties(self, field_id: str) -> None:
        """Handle advanced properties request."""
        app_logger.info(
            f"Advanced properties requested for field '{field_id}' - "
            f"use the Form Builder for detailed editing"
        )
        QMessageBox.information(
            self,
            "خصائص متقدمة",
            "للخصائص المتقدمة، استخدم مصمم النماذج (Form Builder).\n"
            "وضع التعديل المباشر يوفر تعديلات سريعة للتصميم.",
        )

    # -----------------------------------------------------------------------
    # Form definition helpers
    # -----------------------------------------------------------------------

    def _find_field_def(self, field_id: str) -> Optional[dict[str, Any]]:
        """Find a field definition in the form definition by ID."""
        if not self._form_def:
            return None

        for section in self._form_def.get("sections", []):
            for field in section.get("fields", []):
                if field.get("id") == field_id:
                    return field
        return None

    def _update_field_in_form_def(
        self,
        field_id: str,
        key: str,
        value: Any,
    ) -> None:
        """Update a top-level field property in the form definition."""
        field_def = self._find_field_def(field_id)
        if field_def:
            field_def[key] = value

    def _update_field_property(
        self,
        field_id: str,
        prop_name: str,
        value: Any,
    ) -> None:
        """Update a property within the 'properties' dict of a field."""
        field_def = self._find_field_def(field_id)
        if field_def:
            props = field_def.setdefault("properties", {})
            props[prop_name] = value

    def _update_field_layout(
        self,
        field_id: str,
        geometry: QRect,
    ) -> None:
        """Update the layout section of a field definition from widget geometry."""
        field_def = self._find_field_def(field_id)
        if not field_def:
            return

        layout = field_def.setdefault("layout", {})
        layout["width"] = geometry.width()
        layout["height"] = geometry.height()

        # Store absolute position for absolute layout mode
        settings = self._form_def.get("settings", {}) if self._form_def else {}
        if settings.get("layout_mode") == "absolute":
            layout["x"] = geometry.x()
            layout["y"] = geometry.y()

    # -----------------------------------------------------------------------
    # Undo / Redo
    # -----------------------------------------------------------------------

    def _record_geometry_change(
        self,
        field_id: str,
        old_rect: QRect,
        new_rect: QRect,
    ) -> None:
        """Record a geometry change in the undo stack."""
        entry = _LayoutUndoEntry(
            field_id,
            "geometry",
            (old_rect.x(), old_rect.y(), old_rect.width(), old_rect.height()),
            (new_rect.x(), new_rect.y(), new_rect.width(), new_rect.height()),
        )
        self._undo_stack.append(entry)
        self._redo_stack.clear()
        self._update_toolbar_state()

        # Update form definition
        self._update_field_layout(field_id, new_rect)

    def _undo(self) -> None:
        """Undo the last layout change."""
        if not self._undo_stack:
            return

        entry = self._undo_stack.pop()
        self._redo_stack.append(entry)

        self._apply_undo_entry(entry, use_old_value=True)
        self._update_toolbar_state()
        self.update()

    def _redo(self) -> None:
        """Redo the last undone change."""
        if not self._redo_stack:
            return

        entry = self._redo_stack.pop()
        self._undo_stack.append(entry)

        self._apply_undo_entry(entry, use_old_value=False)
        self._update_toolbar_state()
        self.update()

    def _apply_undo_entry(
        self,
        entry: _LayoutUndoEntry,
        use_old_value: bool,
    ) -> None:
        """Apply an undo/redo entry."""
        value = entry.old_value if use_old_value else entry.new_value
        widget = self._editable_widgets.get(entry.field_id)

        if entry.property_name == "geometry":
            if widget and isinstance(value, tuple) and len(value) == 4:
                rect = QRect(int(value[0]), int(value[1]), int(value[2]), int(value[3]))
                widget.setGeometry(rect)
                self._update_field_layout(entry.field_id, rect)
                if self._selected_field_id == entry.field_id:
                    self._handles.set_target_rect(rect)

        elif entry.property_name == "width":
            if widget and isinstance(value, (int, float)):
                widget.setFixedWidth(int(value))
                if self._selected_field_id == entry.field_id:
                    self._handles.set_target_rect(widget.geometry())

        elif entry.property_name == "height":
            if widget and isinstance(value, (int, float)):
                widget.setFixedHeight(int(value))
                if self._selected_field_id == entry.field_id:
                    self._handles.set_target_rect(widget.geometry())

        elif entry.property_name == "label_ar":
            self._update_field_in_form_def(entry.field_id, "label_ar", value)

        elif entry.property_name in ("readonly", "visible"):
            self._update_field_property(entry.field_id, entry.property_name, value)

    def _reset_all(self) -> None:
        """Reset all widgets to their original positions."""
        result = QMessageBox.question(
            self,
            "إعادة ضبط",
            "هل تريد إرجاع جميع التغييرات إلى الحالة الأصلية؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if result != QMessageBox.Yes:
            return

        for field_id, orig_rect in self._original_geometries.items():
            widget = self._editable_widgets.get(field_id)
            if widget:
                widget.setGeometry(orig_rect)

        self._form_def = copy.deepcopy(self._original_form_def)
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._update_toolbar_state()
        self._deselect()
        self.update()

        app_logger.info("Live edit: all changes reset")

    # -----------------------------------------------------------------------
    # Save / Cancel
    # -----------------------------------------------------------------------

    def _save_changes(self) -> None:
        """Save the modified form definition to the .iform file (Rule #13: async)."""
        if not self._form_def:
            return

        if self._saving:
            app_logger.debug("Save already in progress, ignoring duplicate request")
            return
        self._saving = True

        # Update all field layouts from current widget geometries
        for field_id, widget in self._editable_widgets.items():
            if widget.isVisible():
                self._update_field_layout(field_id, widget.geometry())

        if self._form_path:
            # Validate schema before background save to get immediate feedback
            is_valid, errors = validate_form_schema(self._form_def)
            if not is_valid:
                self._saving = False
                msg = "خطأ في هيكل النموذج:\n" + "\n".join(f"- {e}" for e in errors)
                app_logger.error(f"Cannot save invalid form: {msg}")
                QMessageBox.critical(self, "خطأ في الحفظ", msg)
                return

            # Deep copy for thread safety - background thread gets its own copy
            form_data_copy = copy.deepcopy(self._form_def)
            form_path = self._form_path

            def _do_save() -> bool:
                """Background: write JSON to disk."""
                success, error = save_form_file(form_path, form_data_copy)
                if not success:
                    raise RuntimeError(error)
                return True

            def _on_save_done(result: bool) -> None:
                self._saving = False
                app_logger.info(f"Live edit changes saved to {form_path}")
                self.form_modified.emit(form_data_copy)
                self.edit_saved.emit()
                self.deactivate()

            def _on_save_error(exc_type, message, traceback) -> None:
                self._saving = False
                app_logger.error(f"Failed to save live edit changes: {message}")
                QMessageBox.critical(
                    self,
                    "خطأ في الحفظ",
                    f"فشل حفظ التغييرات:\n{message}",
                )

            run_in_background(
                _do_save,
                on_finished=_on_save_done,
                on_error=_on_save_error,
            )
        else:
            # No file path - just emit the modified definition
            self.form_modified.emit(self._form_def)
            self.edit_saved.emit()
            self.deactivate()

    def _cancel_changes(self) -> None:
        """Cancel live editing and revert all changes."""
        if self._undo_stack:
            result = QMessageBox.question(
                self,
                "تأكيد الإلغاء",
                "يوجد تغييرات غير محفوظة. هل تريد الإلغاء؟",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if result != QMessageBox.Yes:
                return

        # Restore original geometries
        for field_id, orig_rect in self._original_geometries.items():
            widget = self._editable_widgets.get(field_id)
            if widget:
                widget.setGeometry(orig_rect)
                widget.setVisible(True)

        self.edit_cancelled.emit()
        self.deactivate()

    # -----------------------------------------------------------------------
    # Painting
    # -----------------------------------------------------------------------

    def paintEvent(self, event) -> None:  # noqa: N802
        """Draw selection handles, snap guides, and widget outlines."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        try:
            # Draw outlines around all editable widgets
            self._paint_widget_outlines(painter)

            # Draw selection handles
            self._handles.paint(painter)

            # Draw snap guides
            if self._current_snap_result and (self._dragging or self._resizing):
                self._snap_engine.paint_guides(
                    painter, self._current_snap_result.guides
                )

        finally:
            painter.end()

    def _paint_widget_outlines(self, painter: QPainter) -> None:
        """Draw thin outlines around all editable widgets."""
        palette = get_current_palette()
        outline_color = QColor(palette.get("border", "#334155"))
        outline_color.setAlpha(80)

        pen = QPen(outline_color, 1, Qt.DotLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        for field_id, widget in self._editable_widgets.items():
            if not widget.isVisible():
                continue
            if field_id == self._selected_field_id:
                continue  # Selected widget has handles instead

            rect = widget.geometry()
            painter.drawRect(rect)

    # -----------------------------------------------------------------------
    # Event filter (for parent resize tracking)
    # -----------------------------------------------------------------------

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        """Track parent widget resize to update overlay geometry."""
        if obj == self.parent() and event.type() == QEvent.Resize:
            parent_widget = self.parent()
            if isinstance(parent_widget, QWidget):
                self.setGeometry(parent_widget.rect())
        return False
