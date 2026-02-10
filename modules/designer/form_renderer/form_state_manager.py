"""
Form State Manager for INTEGRA FormRenderer.

Tracks the lifecycle state of a form and manages:
- Dirty tracking (which fields have changed)
- Form states (LOADING, READY, DIRTY, SAVING, SAVED, ERROR)
- Undo/Redo at the field level
- Reset to original values
- Unsaved-changes confirmation on close

Thread-safe with threading.Lock (Rule #3).
"""

from __future__ import annotations

import copy
import threading
from enum import Enum, auto
from typing import Any, Optional

from PyQt5.QtCore import QObject, pyqtSignal

from core.logging import app_logger


class FormState(Enum):
    """Possible states of a form."""
    LOADING = auto()
    READY = auto()
    DIRTY = auto()
    SAVING = auto()
    SAVED = auto()
    ERROR = auto()


class _UndoEntry:
    """A single undo/redo record for a field change."""
    __slots__ = ("field_id", "old_value", "new_value")

    def __init__(self, field_id: str, old_value: Any, new_value: Any) -> None:
        self.field_id = field_id
        self.old_value = old_value
        self.new_value = new_value


class FormStateManager(QObject):
    """
    Manages form state transitions and dirty tracking.

    Signals:
        state_changed(FormState): Emitted when the form state changes.
        dirty_changed(bool): Emitted when dirty status changes.
        field_dirty_changed(str, bool): Emitted with (field_id, is_dirty).
    """

    state_changed = pyqtSignal(object)       # FormState
    dirty_changed = pyqtSignal(bool)
    field_dirty_changed = pyqtSignal(str, bool)

    MAX_UNDO_HISTORY = 100

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._lock = threading.Lock()
        self._state: FormState = FormState.LOADING
        self._original_values: dict[str, Any] = {}
        self._current_values: dict[str, Any] = {}
        self._dirty_fields: set[str] = set()
        self._undo_stack: list[_UndoEntry] = []
        self._redo_stack: list[_UndoEntry] = []
        self._suppress_tracking = False

    # -----------------------------------------------------------------------
    # State management
    # -----------------------------------------------------------------------

    @property
    def state(self) -> FormState:
        """Current form state."""
        with self._lock:
            return self._state

    def set_state(self, new_state: FormState) -> None:
        """Transition to a new state."""
        with self._lock:
            if self._state == new_state:
                return
            old_state = self._state
            self._state = new_state

        app_logger.debug(f"Form state: {old_state.name} -> {new_state.name}")
        self.state_changed.emit(new_state)

    @property
    def is_dirty(self) -> bool:
        """Whether any fields have been modified."""
        with self._lock:
            return len(self._dirty_fields) > 0

    @property
    def dirty_fields(self) -> set[str]:
        """Set of field IDs that have been modified."""
        with self._lock:
            return set(self._dirty_fields)

    # -----------------------------------------------------------------------
    # Original values (set when form data is loaded)
    # -----------------------------------------------------------------------

    def set_original_values(self, values: dict[str, Any]) -> None:
        """
        Set the original (clean) values. This is called after
        loading data from the database.
        """
        with self._lock:
            self._original_values = copy.deepcopy(values)
            self._current_values = copy.deepcopy(values)
            self._dirty_fields.clear()
            self._undo_stack.clear()
            self._redo_stack.clear()

        self.dirty_changed.emit(False)
        self.set_state(FormState.READY)

    def get_original_value(self, field_id: str) -> Any:
        """Get the original value for a field."""
        with self._lock:
            return self._original_values.get(field_id)

    def get_original_values(self) -> dict[str, Any]:
        """Get all original values."""
        with self._lock:
            return copy.deepcopy(self._original_values)

    # -----------------------------------------------------------------------
    # Current values tracking
    # -----------------------------------------------------------------------

    def get_current_value(self, field_id: str) -> Any:
        """Get the current value for a field."""
        with self._lock:
            return self._current_values.get(field_id)

    def get_current_values(self) -> dict[str, Any]:
        """Get all current values."""
        with self._lock:
            return copy.deepcopy(self._current_values)

    def on_field_changed(self, field_id: str, new_value: Any) -> None:
        """
        Called when a field value changes. Updates dirty tracking
        and undo stack.

        Args:
            field_id: The field that changed.
            new_value: The new value.
        """
        if self._suppress_tracking:
            return

        with self._lock:
            old_value = self._current_values.get(field_id)

            # Avoid duplicate entries for same value
            if old_value == new_value:
                return

            # Record undo
            entry = _UndoEntry(field_id, old_value, new_value)
            self._undo_stack.append(entry)
            if len(self._undo_stack) > self.MAX_UNDO_HISTORY:
                self._undo_stack.pop(0)

            # Clear redo on new change
            self._redo_stack.clear()

            # Update current value
            self._current_values[field_id] = new_value

            # Check if dirty
            original = self._original_values.get(field_id)
            was_dirty = field_id in self._dirty_fields

            if new_value == original:
                self._dirty_fields.discard(field_id)
            else:
                self._dirty_fields.add(field_id)

            is_now_dirty = field_id in self._dirty_fields
            any_dirty = len(self._dirty_fields) > 0

        # Emit signals outside the lock
        if was_dirty != is_now_dirty:
            self.field_dirty_changed.emit(field_id, is_now_dirty)

        # Update form state
        if any_dirty and self._state not in (FormState.SAVING,):
            self.set_state(FormState.DIRTY)
            self.dirty_changed.emit(True)
        elif not any_dirty and self._state == FormState.DIRTY:
            self.set_state(FormState.READY)
            self.dirty_changed.emit(False)

    # -----------------------------------------------------------------------
    # Undo / Redo
    # -----------------------------------------------------------------------

    @property
    def can_undo(self) -> bool:
        with self._lock:
            return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        with self._lock:
            return len(self._redo_stack) > 0

    def undo(self) -> Optional[tuple[str, Any]]:
        """
        Undo the last field change.

        Returns:
            Tuple of (field_id, value_to_restore), or None if nothing to undo.
        """
        with self._lock:
            if not self._undo_stack:
                return None

            entry = self._undo_stack.pop()
            self._redo_stack.append(entry)

            self._current_values[entry.field_id] = entry.old_value

            # Recalculate dirty
            original = self._original_values.get(entry.field_id)
            if entry.old_value == original:
                self._dirty_fields.discard(entry.field_id)
            else:
                self._dirty_fields.add(entry.field_id)

            any_dirty = len(self._dirty_fields) > 0

        # Update state
        if any_dirty:
            self.set_state(FormState.DIRTY)
        else:
            self.set_state(FormState.READY)

        self.dirty_changed.emit(any_dirty)
        return entry.field_id, entry.old_value

    def redo(self) -> Optional[tuple[str, Any]]:
        """
        Redo the last undone change.

        Returns:
            Tuple of (field_id, value_to_apply), or None if nothing to redo.
        """
        with self._lock:
            if not self._redo_stack:
                return None

            entry = self._redo_stack.pop()
            self._undo_stack.append(entry)

            self._current_values[entry.field_id] = entry.new_value

            original = self._original_values.get(entry.field_id)
            if entry.new_value == original:
                self._dirty_fields.discard(entry.field_id)
            else:
                self._dirty_fields.add(entry.field_id)

            any_dirty = len(self._dirty_fields) > 0

        if any_dirty:
            self.set_state(FormState.DIRTY)
        else:
            self.set_state(FormState.READY)

        self.dirty_changed.emit(any_dirty)
        return entry.field_id, entry.new_value

    # -----------------------------------------------------------------------
    # Reset
    # -----------------------------------------------------------------------

    def reset(self) -> dict[str, Any]:
        """
        Reset all fields to their original values.

        Returns:
            Dict of original values to apply to widgets.
        """
        with self._lock:
            self._current_values = copy.deepcopy(self._original_values)
            self._dirty_fields.clear()
            self._undo_stack.clear()
            self._redo_stack.clear()
            values = copy.deepcopy(self._original_values)

        self.set_state(FormState.READY)
        self.dirty_changed.emit(False)
        return values

    # -----------------------------------------------------------------------
    # Suppression (used when setting values programmatically)
    # -----------------------------------------------------------------------

    def suppress_tracking(self) -> None:
        """Temporarily suppress dirty tracking (e.g., during data load)."""
        self._suppress_tracking = True

    def resume_tracking(self) -> None:
        """Resume dirty tracking."""
        self._suppress_tracking = False

    # -----------------------------------------------------------------------
    # Save lifecycle helpers
    # -----------------------------------------------------------------------

    def mark_saving(self) -> None:
        """Mark the form as currently saving."""
        self.set_state(FormState.SAVING)

    def mark_saved(self) -> None:
        """
        Mark the form as saved successfully.
        The current values become the new original values.
        """
        with self._lock:
            self._original_values = copy.deepcopy(self._current_values)
            self._dirty_fields.clear()
            self._undo_stack.clear()
            self._redo_stack.clear()

        self.set_state(FormState.SAVED)
        self.dirty_changed.emit(False)

    def mark_error(self) -> None:
        """Mark the form as having an error."""
        self.set_state(FormState.ERROR)

    # -----------------------------------------------------------------------
    # Changed data (for saving)
    # -----------------------------------------------------------------------

    def get_changed_data(self) -> dict[str, Any]:
        """
        Get only the fields that have been changed from their
        original values. Useful for UPDATE queries.
        """
        with self._lock:
            changed = {}
            for field_id in self._dirty_fields:
                changed[field_id] = self._current_values.get(field_id)
            return changed
