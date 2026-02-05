"""
History Types
=============
Data types for the history and audit system.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import uuid


class EntryType(Enum):
    """Types of history entries."""
    CONVERSATION = "conversation"
    QUERY = "query"
    RESPONSE = "response"
    ACTION_REQUESTED = "action_requested"
    ACTION_APPROVED = "action_approved"
    ACTION_REJECTED = "action_rejected"
    ACTION_EXECUTED = "action_executed"
    ERROR = "error"
    SYSTEM = "system"


@dataclass
class HistoryEntry:
    """A single history entry."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entry_type: EntryType = EntryType.SYSTEM
    session_id: str = ""

    # Content
    content: str = ""
    summary: str = ""

    # Related entities
    action_id: Optional[str] = None
    query_id: Optional[str] = None

    # Context
    screen_context: str = ""
    module_context: str = ""

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)

    # User info
    user_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "entry_type": self.entry_type.value,
            "session_id": self.session_id,
            "content": self.content,
            "summary": self.summary,
            "action_id": self.action_id,
            "query_id": self.query_id,
            "screen_context": self.screen_context,
            "module_context": self.module_context,
            "metadata": self.metadata,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "user_id": self.user_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HistoryEntry':
        """Create from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            entry_type=EntryType(data.get("entry_type", "system")),
            session_id=data.get("session_id", ""),
            content=data.get("content", ""),
            summary=data.get("summary", ""),
            action_id=data.get("action_id"),
            query_id=data.get("query_id"),
            screen_context=data.get("screen_context", ""),
            module_context=data.get("module_context", ""),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            user_id=data.get("user_id")
        )


@dataclass
class ConversationSession:
    """A conversation session with the AI."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    summary: str = ""

    # Entries
    entries: List[HistoryEntry] = field(default_factory=list)

    # Stats
    query_count: int = 0
    response_count: int = 0
    action_count: int = 0
    error_count: int = 0

    # Context
    started_from_screen: str = ""
    started_from_module: str = ""

    # Timestamps
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    last_activity: datetime = field(default_factory=datetime.now)

    # Status
    is_active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "entry_count": len(self.entries),
            "query_count": self.query_count,
            "response_count": self.response_count,
            "action_count": self.action_count,
            "error_count": self.error_count,
            "started_from_screen": self.started_from_screen,
            "started_from_module": self.started_from_module,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "last_activity": self.last_activity.isoformat(),
            "is_active": self.is_active
        }

    def add_entry(self, entry: HistoryEntry):
        """Add an entry to the session."""
        entry.session_id = self.id
        self.entries.append(entry)
        self.last_activity = datetime.now()

        # Update stats
        if entry.entry_type == EntryType.QUERY:
            self.query_count += 1
        elif entry.entry_type == EntryType.RESPONSE:
            self.response_count += 1
        elif entry.entry_type in [EntryType.ACTION_REQUESTED, EntryType.ACTION_EXECUTED]:
            self.action_count += 1
        elif entry.entry_type == EntryType.ERROR:
            self.error_count += 1

    def end_session(self):
        """End the session."""
        self.is_active = False
        self.ended_at = datetime.now()

        # Generate summary if not set
        if not self.summary:
            self.summary = self._generate_summary()

    def _generate_summary(self) -> str:
        """Generate a summary of the session."""
        parts = []
        if self.query_count > 0:
            parts.append(f"{self.query_count} استفسار")
        if self.action_count > 0:
            parts.append(f"{self.action_count} إجراء")
        if self.error_count > 0:
            parts.append(f"{self.error_count} خطأ")

        return " | ".join(parts) if parts else "جلسة فارغة"

    def get_conversation_text(self) -> str:
        """Get the full conversation as text."""
        lines = []
        for entry in self.entries:
            if entry.entry_type == EntryType.QUERY:
                lines.append(f"المستخدم: {entry.content}")
            elif entry.entry_type == EntryType.RESPONSE:
                lines.append(f"المساعد: {entry.content}")
        return "\n\n".join(lines)


@dataclass
class HistoryStats:
    """Statistics about history."""
    total_sessions: int = 0
    total_entries: int = 0
    total_queries: int = 0
    total_actions: int = 0
    total_errors: int = 0
    avg_session_length: float = 0.0
    most_common_queries: List[str] = field(default_factory=list)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_sessions": self.total_sessions,
            "total_entries": self.total_entries,
            "total_queries": self.total_queries,
            "total_actions": self.total_actions,
            "total_errors": self.total_errors,
            "avg_session_length": self.avg_session_length,
            "most_common_queries": self.most_common_queries
        }
