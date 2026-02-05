"""
Context Tracker
===============
Tracks application events and updates context.
"""

from typing import Optional, Callable, List
from dataclasses import dataclass
from datetime import datetime
import threading

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QWidget, QMainWindow, QApplication

from core.logging import app_logger
from .types import (
    AppContext, ScreenContext, SelectionContext, UserAction,
    ScreenType, ActionType
)


class ContextTracker(QObject):
    """
    Tracks application context by monitoring UI events.

    Features:
    - Screen change detection
    - Selection tracking
    - Action history
    - Event emission for context changes

    Usage:
        tracker = ContextTracker()
        tracker.context_changed.connect(on_context_change)
        tracker.start()
    """

    # Signals
    context_changed = pyqtSignal(object)  # AppContext
    screen_changed = pyqtSignal(object)   # ScreenContext
    selection_changed = pyqtSignal(object)  # SelectionContext
    action_recorded = pyqtSignal(object)  # UserAction

    def __init__(self, parent=None):
        super().__init__(parent)
        self._context = AppContext()
        self._tracking = False
        self._lock = threading.RLock()

        # Registered widgets to track
        self._tracked_widgets: List[QWidget] = []

    @property
    def context(self) -> AppContext:
        """Get current context."""
        with self._lock:
            return self._context

    def start(self) -> None:
        """Start tracking."""
        if self._tracking:
            return

        self._tracking = True
        self._context.session_start = datetime.now()

        # Connect to application focus changes
        app = QApplication.instance()
        if app:
            app.focusChanged.connect(self._on_focus_changed)

        app_logger.debug("Context tracker started")

    def stop(self) -> None:
        """Stop tracking."""
        self._tracking = False

        # Disconnect from application
        app = QApplication.instance()
        if app:
            try:
                app.focusChanged.disconnect(self._on_focus_changed)
            except Exception:
                pass

        app_logger.debug("Context tracker stopped")

    def track_widget(self, widget: QWidget) -> None:
        """Register a widget for tracking."""
        if widget not in self._tracked_widgets:
            self._tracked_widgets.append(widget)

    def untrack_widget(self, widget: QWidget) -> None:
        """Unregister a widget from tracking."""
        if widget in self._tracked_widgets:
            self._tracked_widgets.remove(widget)

    def update_screen(
        self,
        screen_type: ScreenType,
        screen_id: str,
        screen_title: str,
        module_id: Optional[str] = None,
        module_name: Optional[str] = None,
        **metadata
    ) -> None:
        """
        Update the current screen context.

        Args:
            screen_type: Type of screen
            screen_id: Unique screen identifier
            screen_title: Display title
            module_id: Parent module ID
            module_name: Parent module name
            **metadata: Additional metadata
        """
        with self._lock:
            old_screen = self._context.screen.screen_id

            self._context.screen = ScreenContext(
                screen_type=screen_type,
                screen_id=screen_id,
                screen_title=screen_title,
                module_id=module_id,
                module_name=module_name,
                parent_screen=old_screen,
                metadata=metadata
            )

            # Record navigation action
            if old_screen != screen_id:
                self.record_action(
                    ActionType.NAVIGATE,
                    target=screen_id,
                    metadata={"from": old_screen, "to": screen_id}
                )

        self.screen_changed.emit(self._context.screen)
        self.context_changed.emit(self._context)

    def update_selection(
        self,
        has_selection: bool,
        selection_type: str = "",
        selected_ids: Optional[List[str]] = None,
        selected_data: Optional[dict] = None,
        selection_text: str = "",
        table_name: Optional[str] = None,
        column_name: Optional[str] = None
    ) -> None:
        """
        Update the current selection context.

        Args:
            has_selection: Whether there is a selection
            selection_type: Type of selection (row, cell, text, item)
            selected_ids: IDs of selected items
            selected_data: Data of selected items
            selection_text: Selected text content
            table_name: Related table name
            column_name: Related column name
        """
        with self._lock:
            self._context.selection = SelectionContext(
                has_selection=has_selection,
                selection_type=selection_type,
                selected_ids=selected_ids or [],
                selected_data=selected_data or {},
                selection_text=selection_text,
                table_name=table_name,
                column_name=column_name
            )

            if has_selection:
                self.record_action(
                    ActionType.SELECT,
                    target=selection_type,
                    value=len(selected_ids or []),
                    metadata={"table": table_name}
                )

        self.selection_changed.emit(self._context.selection)
        self.context_changed.emit(self._context)

    def clear_selection(self) -> None:
        """Clear the current selection."""
        self.update_selection(has_selection=False)

    def record_action(
        self,
        action_type: ActionType,
        target: str = "",
        value: any = None,
        **metadata
    ) -> None:
        """
        Record a user action.

        Args:
            action_type: Type of action
            target: What was acted upon
            value: The value (if applicable)
            **metadata: Additional metadata
        """
        with self._lock:
            action = UserAction(
                action_type=action_type,
                target=target,
                value=value,
                metadata=metadata
            )
            self._context.add_action(action)

        self.action_recorded.emit(action)

    def get_recent_actions(self, count: int = 10) -> List[UserAction]:
        """Get recent actions."""
        with self._lock:
            return self._context.recent_actions[-count:]

    def _on_focus_changed(self, old_widget: QWidget, new_widget: QWidget) -> None:
        """Handle focus changes."""
        if not self._tracking or not new_widget:
            return

        # Try to determine screen context from the focused widget
        try:
            window = new_widget.window()
            if window and isinstance(window, QMainWindow):
                title = window.windowTitle()
                if title:
                    # Update screen title if it changed
                    if title != self._context.screen.screen_title:
                        self.update_screen(
                            screen_type=self._detect_screen_type(window),
                            screen_id=str(id(window)),
                            screen_title=title
                        )
        except Exception:
            pass

    def _detect_screen_type(self, widget: QWidget) -> ScreenType:
        """Detect screen type from widget."""
        class_name = widget.__class__.__name__.lower()

        if "launcher" in class_name:
            return ScreenType.LAUNCHER
        elif "dialog" in class_name:
            return ScreenType.DIALOG
        elif "settings" in class_name:
            return ScreenType.SETTINGS
        elif "form" in class_name or "edit" in class_name:
            return ScreenType.FORM
        elif "list" in class_name or "table" in class_name:
            return ScreenType.LIST
        elif "report" in class_name:
            return ScreenType.REPORT
        elif "dashboard" in class_name:
            return ScreenType.DASHBOARD
        elif "window" in class_name:
            return ScreenType.MODULE

        return ScreenType.UNKNOWN
