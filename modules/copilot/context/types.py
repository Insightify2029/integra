"""
Context Types
=============
Data types for application context tracking.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class ScreenType(Enum):
    """Types of application screens."""
    LAUNCHER = "launcher"
    MODULE = "module"
    DIALOG = "dialog"
    SETTINGS = "settings"
    FORM = "form"
    LIST = "list"
    REPORT = "report"
    DASHBOARD = "dashboard"
    UNKNOWN = "unknown"


class ActionType(Enum):
    """Types of user actions."""
    NAVIGATE = "navigate"
    SELECT = "select"
    EDIT = "edit"
    CREATE = "create"
    DELETE = "delete"
    SEARCH = "search"
    FILTER = "filter"
    EXPORT = "export"
    IMPORT = "import"
    PRINT = "print"
    SAVE = "save"
    CANCEL = "cancel"
    UNKNOWN = "unknown"


@dataclass
class ScreenContext:
    """Context about the current screen."""
    screen_type: ScreenType = ScreenType.UNKNOWN
    screen_id: str = ""
    screen_title: str = ""
    module_id: Optional[str] = None
    module_name: Optional[str] = None
    parent_screen: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "screen_type": self.screen_type.value,
            "screen_id": self.screen_id,
            "screen_title": self.screen_title,
            "module_id": self.module_id,
            "module_name": self.module_name,
            "parent_screen": self.parent_screen,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class SelectionContext:
    """Context about current selection."""
    has_selection: bool = False
    selection_type: str = ""  # "row", "cell", "text", "item"
    selected_ids: List[str] = field(default_factory=list)
    selected_data: Dict[str, Any] = field(default_factory=dict)
    selection_text: str = ""
    table_name: Optional[str] = None
    column_name: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "has_selection": self.has_selection,
            "selection_type": self.selection_type,
            "selected_ids": self.selected_ids,
            "selected_data": self.selected_data,
            "selection_text": self.selection_text,
            "table_name": self.table_name,
            "column_name": self.column_name,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class UserAction:
    """A recorded user action."""
    action_type: ActionType
    target: str = ""  # What was acted upon
    value: Any = None  # The value (if applicable)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "action_type": self.action_type.value,
            "target": self.target,
            "value": str(self.value) if self.value else None,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class AppContext:
    """Complete application context."""
    screen: ScreenContext = field(default_factory=ScreenContext)
    selection: SelectionContext = field(default_factory=SelectionContext)
    recent_actions: List[UserAction] = field(default_factory=list)
    session_start: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "screen": self.screen.to_dict(),
            "selection": self.selection.to_dict(),
            "recent_actions": [a.to_dict() for a in self.recent_actions[-10:]],
            "session_start": self.session_start.isoformat(),
            "user_id": self.user_id,
            "metadata": self.metadata
        }

    def to_prompt_context(self) -> str:
        """Convert to text suitable for AI prompt."""
        parts = []

        # Screen info
        if self.screen.screen_title:
            parts.append(f"الشاشة الحالية: {self.screen.screen_title}")
        if self.screen.module_name:
            parts.append(f"الموديول: {self.screen.module_name}")

        # Selection info
        if self.selection.has_selection:
            if self.selection.selection_text:
                parts.append(f"النص المحدد: {self.selection.selection_text[:200]}")
            elif self.selection.selected_ids:
                parts.append(f"العناصر المحددة: {len(self.selection.selected_ids)} عنصر")
            if self.selection.table_name:
                parts.append(f"الجدول: {self.selection.table_name}")

        # Recent actions
        if self.recent_actions:
            recent = self.recent_actions[-3:]
            actions_text = ", ".join(a.action_type.value for a in recent)
            parts.append(f"الإجراءات الأخيرة: {actions_text}")

        if parts:
            return "# سياق التطبيق:\n" + "\n".join(f"- {p}" for p in parts)
        return ""

    def add_action(self, action: UserAction, max_actions: int = 50) -> None:
        """Add a user action to the history."""
        self.recent_actions.append(action)
        if len(self.recent_actions) > max_actions:
            self.recent_actions = self.recent_actions[-max_actions:]
