"""
Sandbox Types
=============
Data types for the action sandbox.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from enum import Enum
import uuid


class SandboxState(Enum):
    """State of a sandbox action."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ActionCategory(Enum):
    """Categories of actions."""
    DATA_CREATE = "data_create"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"
    FILE_CREATE = "file_create"
    FILE_UPDATE = "file_update"
    FILE_DELETE = "file_delete"
    SEND_EMAIL = "send_email"
    SEND_NOTIFICATION = "send_notification"
    EXPORT_DATA = "export_data"
    IMPORT_DATA = "import_data"
    SYSTEM_CONFIG = "system_config"
    CUSTOM = "custom"


@dataclass
class ActionChange:
    """A single change within an action."""
    field: str
    old_value: Any
    new_value: Any
    change_type: str = "update"  # update, add, remove

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "old_value": str(self.old_value) if self.old_value is not None else None,
            "new_value": str(self.new_value) if self.new_value is not None else None,
            "change_type": self.change_type
        }


@dataclass
class SandboxAction:
    """
    An action in the sandbox.

    Represents a pending action that can be previewed, modified, approved, or rejected.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    category: ActionCategory = ActionCategory.CUSTOM
    title: str = ""
    description: str = ""
    target_type: str = ""  # e.g., "employee", "report", "email"
    target_id: Optional[str] = None
    target_name: str = ""

    # The actual changes
    changes: List[ActionChange] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)

    # Preview data
    preview_before: str = ""
    preview_after: str = ""

    # State
    state: SandboxState = SandboxState.DRAFT

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    created_by: str = "ai_copilot"

    # Rollback info
    rollback_data: Dict[str, Any] = field(default_factory=dict)
    can_rollback: bool = True

    # Execution
    executor: Optional[Callable] = None
    rollback_executor: Optional[Callable] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "category": self.category.value,
            "title": self.title,
            "description": self.description,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "target_name": self.target_name,
            "changes": [c.to_dict() for c in self.changes],
            "data": self.data,
            "preview_before": self.preview_before,
            "preview_after": self.preview_after,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "created_by": self.created_by,
            "can_rollback": self.can_rollback,
            "error_message": self.error_message
        }

    def add_change(self, field: str, old_value: Any, new_value: Any, change_type: str = "update"):
        """Add a change to the action."""
        self.changes.append(ActionChange(
            field=field,
            old_value=old_value,
            new_value=new_value,
            change_type=change_type
        ))
        self.updated_at = datetime.now()

    def set_preview(self, before: str, after: str):
        """Set preview data."""
        self.preview_before = before
        self.preview_after = after
        self.updated_at = datetime.now()

    def approve(self):
        """Mark action as approved."""
        self.state = SandboxState.APPROVED
        self.approved_at = datetime.now()
        self.updated_at = datetime.now()

    def reject(self):
        """Mark action as rejected."""
        self.state = SandboxState.REJECTED
        self.updated_at = datetime.now()

    def is_destructive(self) -> bool:
        """Check if this is a destructive action."""
        return self.category in [
            ActionCategory.DATA_DELETE,
            ActionCategory.FILE_DELETE
        ]

    def get_summary(self) -> str:
        """Get a brief summary of the action."""
        change_count = len(self.changes)
        return f"{self.title} ({change_count} تغييرات)"


@dataclass
class SandboxSession:
    """A sandbox session containing multiple actions."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    actions: List[SandboxAction] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    description: str = ""
    is_active: bool = True

    def add_action(self, action: SandboxAction):
        """Add an action to the session."""
        self.actions.append(action)

    def get_pending_actions(self) -> List[SandboxAction]:
        """Get actions pending approval."""
        return [a for a in self.actions if a.state == SandboxState.PENDING_APPROVAL]

    def get_action(self, action_id: str) -> Optional[SandboxAction]:
        """Get an action by ID."""
        for action in self.actions:
            if action.id == action_id:
                return action
        return None
