"""
Context Manager
===============
Manages application context for AI Copilot.
"""

from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
import threading

from PyQt5.QtCore import QObject, pyqtSignal

from core.logging import app_logger
from .types import AppContext, ScreenContext, SelectionContext, UserAction, ScreenType, ActionType
from .tracker import ContextTracker


class ContextManager(QObject):
    """
    Central context manager for AI Copilot.

    Features:
    - Centralized context tracking
    - Context persistence
    - Context-aware suggestions
    - Integration with AI system

    Usage:
        manager = get_context_manager()
        manager.initialize()

        # Get current context
        context = manager.get_context()

        # Get context for AI prompt
        prompt_context = manager.get_prompt_context()
    """

    _instance = None
    _lock = threading.Lock()

    # Signals
    context_updated = pyqtSignal(object)  # AppContext

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._obj_initialized = False
        return cls._instance

    def __init__(self):
        if hasattr(self, '_obj_initialized') and self._obj_initialized:
            return

        super().__init__()
        self._tracker: Optional[ContextTracker] = None
        self._ready = False
        self._context_listeners: List[Callable[[AppContext], None]] = []
        self._init_lock = threading.RLock()

        self._obj_initialized = True

    def initialize(self) -> bool:
        """Initialize the context manager."""
        with self._init_lock:
            if self._ready:
                return True

            try:
                self._tracker = ContextTracker()
                self._tracker.context_changed.connect(self._on_context_changed)
                self._tracker.start()

                self._ready = True
                app_logger.info("Context manager initialized")
                return True

            except Exception as e:
                app_logger.error(f"Failed to initialize context manager: {e}")
                return False

    def shutdown(self) -> None:
        """Shutdown the context manager."""
        if self._tracker:
            self._tracker.stop()
        self._ready = False

    def is_ready(self) -> bool:
        """Check if manager is ready."""
        return self._ready

    def get_context(self) -> AppContext:
        """Get the current application context."""
        if not self._tracker:
            return AppContext()
        return self._tracker.context

    def get_prompt_context(self) -> str:
        """Get context formatted for AI prompt."""
        context = self.get_context()
        return context.to_prompt_context()

    def get_context_dict(self) -> Dict[str, Any]:
        """Get context as dictionary."""
        return self.get_context().to_dict()

    def update_screen(
        self,
        screen_type: ScreenType,
        screen_id: str,
        screen_title: str,
        module_id: Optional[str] = None,
        module_name: Optional[str] = None,
        **metadata
    ) -> None:
        """Update the current screen context."""
        if self._tracker:
            self._tracker.update_screen(
                screen_type=screen_type,
                screen_id=screen_id,
                screen_title=screen_title,
                module_id=module_id,
                module_name=module_name,
                **metadata
            )

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
        """Update the current selection context."""
        if self._tracker:
            self._tracker.update_selection(
                has_selection=has_selection,
                selection_type=selection_type,
                selected_ids=selected_ids,
                selected_data=selected_data,
                selection_text=selection_text,
                table_name=table_name,
                column_name=column_name
            )

    def clear_selection(self) -> None:
        """Clear the current selection."""
        if self._tracker:
            self._tracker.clear_selection()

    def record_action(
        self,
        action_type: ActionType,
        target: str = "",
        value: any = None,
        **metadata
    ) -> None:
        """Record a user action."""
        if self._tracker:
            self._tracker.record_action(
                action_type=action_type,
                target=target,
                value=value,
                **metadata
            )

    def get_recent_actions(self, count: int = 10) -> List[UserAction]:
        """Get recent user actions."""
        if not self._tracker:
            return []
        return self._tracker.get_recent_actions(count)

    def add_listener(self, callback: Callable[[AppContext], None]) -> None:
        """Add a context change listener."""
        if callback not in self._context_listeners:
            self._context_listeners.append(callback)

    def remove_listener(self, callback: Callable[[AppContext], None]) -> None:
        """Remove a context change listener."""
        if callback in self._context_listeners:
            self._context_listeners.remove(callback)

    def _on_context_changed(self, context: AppContext) -> None:
        """Handle context changes."""
        self.context_updated.emit(context)

        # Notify listeners
        for listener in self._context_listeners:
            try:
                listener(context)
            except Exception as e:
                app_logger.error(f"Error in context listener: {e}")

    def get_context_summary(self) -> str:
        """Get a brief summary of the current context."""
        context = self.get_context()

        parts = []
        if context.screen.screen_title:
            parts.append(context.screen.screen_title)
        if context.screen.module_name:
            parts.append(f"({context.screen.module_name})")
        if context.selection.has_selection:
            parts.append(f"- {len(context.selection.selected_ids)} محدد")

        return " ".join(parts) if parts else "لا يوجد سياق"


# Singleton instance
_manager: Optional[ContextManager] = None


def get_context_manager() -> ContextManager:
    """Get the singleton context manager instance."""
    global _manager
    if _manager is None:
        _manager = ContextManager()
    return _manager


def initialize_context() -> bool:
    """Initialize context tracking (convenience function)."""
    return get_context_manager().initialize()


def get_current_context() -> AppContext:
    """Get current context (convenience function)."""
    manager = get_context_manager()
    if not manager.is_ready():
        manager.initialize()
    return manager.get_context()


def get_prompt_context() -> str:
    """Get context for AI prompt (convenience function)."""
    manager = get_context_manager()
    if not manager.is_ready():
        manager.initialize()
    return manager.get_prompt_context()
