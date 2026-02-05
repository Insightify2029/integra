"""
Context Awareness System
========================
Tracks current application context for AI assistance.
"""

from .manager import ContextManager, get_context_manager
from .tracker import ContextTracker
from .types import AppContext, ScreenContext, SelectionContext

__all__ = [
    "ContextManager",
    "get_context_manager",
    "ContextTracker",
    "AppContext",
    "ScreenContext",
    "SelectionContext"
]
