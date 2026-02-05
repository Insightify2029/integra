"""
AI Copilot Module
=================
Integrated AI assistant for INTEGRA.

Components:
- Knowledge Engine (N1): Index and search application knowledge
- Chat Interface (N2): Sidebar and floating window
- Context Awareness (N3): Track current screen, selection, activity
- Action Sandbox (N4): Preview actions before applying
- Approval Workflow (N5): User confirmation for changes
- Learning System (N6): Learn from user behavior
- Audit & History (N7): Track all AI interactions
"""

from .knowledge import get_knowledge_engine
from .context import get_context_manager
from .sandbox import get_action_sandbox
from .approval import get_approval_manager
from .learning import get_learning_system
from .history import get_history_manager

__all__ = [
    "get_knowledge_engine",
    "get_context_manager",
    "get_action_sandbox",
    "get_approval_manager",
    "get_learning_system",
    "get_history_manager"
]
