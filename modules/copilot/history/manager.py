"""
History Manager
===============
Manages history and audit trail for AI interactions.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import Counter
import threading
import json
import os

from PyQt5.QtCore import QObject, pyqtSignal

from core.logging import app_logger
from .types import HistoryEntry, ConversationSession, HistoryStats, EntryType


class HistoryManager(QObject):
    """
    History and Audit Manager.

    Features:
    - Conversation history
    - Action audit trail
    - Search and filter
    - Statistics
    - Export functionality

    Usage:
        manager = get_history_manager()
        manager.initialize()

        # Start a session
        session = manager.start_session()

        # Record entries
        manager.record_query("كيف أضيف موظف؟")
        manager.record_response("يمكنك إضافة موظف...")

        # Search history
        results = manager.search("موظف")

        # Get stats
        stats = manager.get_stats()
    """

    _instance = None
    _lock = threading.Lock()

    # Signals
    session_started = pyqtSignal(object)  # ConversationSession
    session_ended = pyqtSignal(object)  # ConversationSession
    entry_added = pyqtSignal(object)  # HistoryEntry

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
        self._sessions: Dict[str, ConversationSession] = {}
        self._current_session: Optional[ConversationSession] = None
        self._all_entries: List[HistoryEntry] = []
        self._data_path: Optional[str] = None
        self._ready = False
        self._init_lock = threading.RLock()

        # Settings
        self._max_sessions = 100
        self._max_entries_per_session = 500
        self._retention_days = 30

        self._obj_initialized = True

    def initialize(self, data_path: Optional[str] = None) -> bool:
        """Initialize the history manager."""
        with self._init_lock:
            if self._ready:
                return True

            try:
                self._data_path = data_path or self._get_default_data_path()
                self._load_data()
                self._ready = True
                app_logger.info("History manager initialized")
                return True
            except Exception as e:
                app_logger.error(f"Failed to initialize history manager: {e}")
                return False

    def _get_default_data_path(self) -> str:
        """Get default data storage path."""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        data_dir = os.path.join(base_dir, "data", "copilot")
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, "history.json")

    def is_ready(self) -> bool:
        """Check if manager is ready."""
        return self._ready

    def start_session(
        self,
        title: str = "",
        screen_context: str = "",
        module_context: str = ""
    ) -> ConversationSession:
        """
        Start a new conversation session.

        Args:
            title: Session title
            screen_context: Starting screen
            module_context: Starting module

        Returns:
            ConversationSession
        """
        # End current session if exists
        if self._current_session and self._current_session.is_active:
            self.end_session()

        session = ConversationSession(
            title=title or f"جلسة {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            started_from_screen=screen_context,
            started_from_module=module_context
        )

        self._sessions[session.id] = session
        self._current_session = session

        app_logger.info(f"Started history session: {session.id}")
        self.session_started.emit(session)

        return session

    def end_session(self, session_id: Optional[str] = None) -> bool:
        """
        End a conversation session.

        Args:
            session_id: Session ID (or current session if None)

        Returns:
            True if ended
        """
        session = None
        if session_id:
            session = self._sessions.get(session_id)
        elif self._current_session:
            session = self._current_session

        if not session or not session.is_active:
            return False

        session.end_session()

        if session == self._current_session:
            self._current_session = None

        self._save_data()

        app_logger.info(f"Ended history session: {session.id}")
        self.session_ended.emit(session)

        return True

    def get_current_session(self) -> ConversationSession:
        """Get or create current session."""
        if not self._current_session or not self._current_session.is_active:
            self.start_session()
        return self._current_session

    def record_entry(
        self,
        entry_type: EntryType,
        content: str,
        summary: str = "",
        action_id: Optional[str] = None,
        screen_context: str = "",
        module_context: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> HistoryEntry:
        """
        Record a history entry.

        Args:
            entry_type: Type of entry
            content: Entry content
            summary: Brief summary
            action_id: Related action ID
            screen_context: Screen context
            module_context: Module context
            metadata: Additional metadata
            tags: Tags for the entry

        Returns:
            HistoryEntry
        """
        session = self.get_current_session()

        entry = HistoryEntry(
            entry_type=entry_type,
            session_id=session.id,
            content=content,
            summary=summary or content[:100],
            action_id=action_id,
            screen_context=screen_context,
            module_context=module_context,
            metadata=metadata or {},
            tags=tags or []
        )

        session.add_entry(entry)
        self._all_entries.append(entry)

        # Trim if needed
        if len(session.entries) > self._max_entries_per_session:
            session.entries = session.entries[-self._max_entries_per_session:]

        self.entry_added.emit(entry)

        return entry

    def record_query(self, query: str, **kwargs) -> HistoryEntry:
        """Record a user query."""
        return self.record_entry(EntryType.QUERY, query, **kwargs)

    def record_response(self, response: str, **kwargs) -> HistoryEntry:
        """Record an AI response."""
        return self.record_entry(EntryType.RESPONSE, response, **kwargs)

    def record_action(
        self,
        action_type: str,
        action_id: str,
        description: str,
        **kwargs
    ) -> HistoryEntry:
        """Record an action."""
        entry_type_map = {
            "requested": EntryType.ACTION_REQUESTED,
            "approved": EntryType.ACTION_APPROVED,
            "rejected": EntryType.ACTION_REJECTED,
            "executed": EntryType.ACTION_EXECUTED
        }
        entry_type = entry_type_map.get(action_type, EntryType.ACTION_REQUESTED)

        return self.record_entry(
            entry_type,
            description,
            action_id=action_id,
            **kwargs
        )

    def record_error(self, error: str, **kwargs) -> HistoryEntry:
        """Record an error."""
        return self.record_entry(EntryType.ERROR, error, **kwargs)

    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get a specific session."""
        return self._sessions.get(session_id)

    def get_all_sessions(self) -> List[ConversationSession]:
        """Get all sessions."""
        return list(self._sessions.values())

    def get_recent_sessions(self, limit: int = 10) -> List[ConversationSession]:
        """Get recent sessions."""
        sorted_sessions = sorted(
            self._sessions.values(),
            key=lambda s: s.started_at,
            reverse=True
        )
        return sorted_sessions[:limit]

    def search(
        self,
        query: str,
        entry_types: Optional[List[EntryType]] = None,
        session_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50
    ) -> List[HistoryEntry]:
        """
        Search history entries.

        Args:
            query: Search query
            entry_types: Filter by entry types
            session_id: Filter by session
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum results

        Returns:
            List of matching entries
        """
        query_lower = query.lower()
        results = []

        entries = self._all_entries
        if session_id and session_id in self._sessions:
            entries = self._sessions[session_id].entries

        for entry in entries:
            # Filter by type
            if entry_types and entry.entry_type not in entry_types:
                continue

            # Filter by date
            if start_date and entry.created_at < start_date:
                continue
            if end_date and entry.created_at > end_date:
                continue

            # Search in content
            if query_lower in entry.content.lower():
                results.append(entry)
            elif query_lower in entry.summary.lower():
                results.append(entry)
            elif any(query_lower in tag.lower() for tag in entry.tags):
                results.append(entry)

            if len(results) >= limit:
                break

        return results

    def get_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> HistoryStats:
        """
        Get history statistics.

        Args:
            start_date: Period start
            end_date: Period end

        Returns:
            HistoryStats
        """
        start = start_date or datetime.now() - timedelta(days=30)
        end = end_date or datetime.now()

        # Filter sessions in period
        sessions_in_period = [
            s for s in self._sessions.values()
            if start <= s.started_at <= end
        ]

        # Calculate stats
        total_queries = sum(s.query_count for s in sessions_in_period)
        total_actions = sum(s.action_count for s in sessions_in_period)
        total_errors = sum(s.error_count for s in sessions_in_period)
        total_entries = sum(len(s.entries) for s in sessions_in_period)

        # Average session length
        avg_length = 0.0
        if sessions_in_period:
            lengths = []
            for s in sessions_in_period:
                if s.ended_at:
                    lengths.append((s.ended_at - s.started_at).total_seconds())
            if lengths:
                avg_length = sum(lengths) / len(lengths)

        # Most common queries
        query_counter = Counter()
        for session in sessions_in_period:
            for entry in session.entries:
                if entry.entry_type == EntryType.QUERY:
                    # Normalize and count
                    normalized = entry.content[:50].strip()
                    query_counter[normalized] += 1

        most_common = [q for q, _ in query_counter.most_common(5)]

        return HistoryStats(
            total_sessions=len(sessions_in_period),
            total_entries=total_entries,
            total_queries=total_queries,
            total_actions=total_actions,
            total_errors=total_errors,
            avg_session_length=avg_length,
            most_common_queries=most_common,
            period_start=start,
            period_end=end
        )

    def export_session(self, session_id: str, format: str = "text") -> str:
        """
        Export a session.

        Args:
            session_id: Session ID
            format: Export format (text, json, markdown)

        Returns:
            Exported content
        """
        session = self._sessions.get(session_id)
        if not session:
            return ""

        if format == "json":
            return json.dumps(session.to_dict(), ensure_ascii=False, indent=2)

        elif format == "markdown":
            lines = [
                f"# {session.title}",
                f"",
                f"- **بداية**: {session.started_at.strftime('%Y-%m-%d %H:%M')}",
                f"- **نهاية**: {session.ended_at.strftime('%Y-%m-%d %H:%M') if session.ended_at else 'جارية'}",
                f"- **الاستفسارات**: {session.query_count}",
                f"- **الإجراءات**: {session.action_count}",
                f"",
                "## المحادثة",
                ""
            ]

            for entry in session.entries:
                if entry.entry_type == EntryType.QUERY:
                    lines.append(f"**المستخدم**: {entry.content}")
                elif entry.entry_type == EntryType.RESPONSE:
                    lines.append(f"**المساعد**: {entry.content}")
                elif entry.entry_type == EntryType.ACTION_EXECUTED:
                    lines.append(f"**إجراء**: {entry.content}")
                lines.append("")

            return "\n".join(lines)

        else:  # text
            return session.get_conversation_text()

    def cleanup_old_sessions(self, days: Optional[int] = None):
        """Remove sessions older than retention period."""
        retention = days or self._retention_days
        cutoff = datetime.now() - timedelta(days=retention)

        to_remove = [
            sid for sid, session in self._sessions.items()
            if session.started_at < cutoff and not session.is_active
        ]

        for sid in to_remove:
            del self._sessions[sid]

        self._save_data()
        app_logger.info(f"Cleaned up {len(to_remove)} old sessions")

    def _load_data(self):
        """Load history data from disk."""
        if not self._data_path or not os.path.exists(self._data_path):
            return

        try:
            with open(self._data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for session_data in data.get("sessions", []):
                session = ConversationSession(
                    id=session_data["id"],
                    title=session_data.get("title", ""),
                    summary=session_data.get("summary", ""),
                    query_count=session_data.get("query_count", 0),
                    response_count=session_data.get("response_count", 0),
                    action_count=session_data.get("action_count", 0),
                    error_count=session_data.get("error_count", 0),
                    started_from_screen=session_data.get("started_from_screen", ""),
                    started_from_module=session_data.get("started_from_module", ""),
                    started_at=datetime.fromisoformat(session_data["started_at"]),
                    ended_at=datetime.fromisoformat(session_data["ended_at"]) if session_data.get("ended_at") else None,
                    is_active=session_data.get("is_active", False)
                )

                # Load entries
                for entry_data in session_data.get("entries", []):
                    entry = HistoryEntry.from_dict(entry_data)
                    session.entries.append(entry)
                    self._all_entries.append(entry)

                self._sessions[session.id] = session

            app_logger.debug(f"Loaded {len(self._sessions)} history sessions")

        except Exception as e:
            app_logger.error(f"Error loading history data: {e}")

    def _save_data(self):
        """Save history data to disk."""
        if not self._data_path:
            return

        try:
            # Keep only recent sessions
            recent_sessions = sorted(
                self._sessions.values(),
                key=lambda s: s.started_at,
                reverse=True
            )[:self._max_sessions]

            data = {
                "version": 1,
                "saved_at": datetime.now().isoformat(),
                "sessions": []
            }

            for session in recent_sessions:
                session_data = session.to_dict()
                session_data["entries"] = [e.to_dict() for e in session.entries[-100:]]
                data["sessions"].append(session_data)

            with open(self._data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            app_logger.error(f"Error saving history data: {e}")

    def clear(self):
        """Clear all history."""
        self._sessions.clear()
        self._all_entries.clear()
        self._current_session = None

        if self._data_path and os.path.exists(self._data_path):
            os.remove(self._data_path)


# Singleton instance
_manager: Optional[HistoryManager] = None


def get_history_manager() -> HistoryManager:
    """Get the singleton history manager instance."""
    global _manager
    if _manager is None:
        _manager = HistoryManager()
    return _manager


def record_query(query: str, **kwargs) -> HistoryEntry:
    """Record a query (convenience function)."""
    manager = get_history_manager()
    if not manager.is_ready():
        manager.initialize()
    return manager.record_query(query, **kwargs)


def record_response(response: str, **kwargs) -> HistoryEntry:
    """Record a response (convenience function)."""
    manager = get_history_manager()
    if not manager.is_ready():
        manager.initialize()
    return manager.record_response(response, **kwargs)
