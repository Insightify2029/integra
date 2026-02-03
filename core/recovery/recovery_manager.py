# -*- coding: utf-8 -*-
"""
Recovery Manager
================
Crash recovery and session restoration.

Features:
  - Detect unclean shutdown
  - Restore last session state
  - Recovery wizard UI helper
"""

from typing import Any, Dict, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
import json
import os

from PyQt5.QtCore import QObject, pyqtSignal


@dataclass
class RecoveryData:
    """
    Recovery data container.

    Attributes:
        session_id: Unique session identifier
        crash_time: When the crash occurred (if any)
        open_windows: List of windows that were open
        unsaved_changes: Dict of form_id -> unsaved data
        last_module: Last active module
    """
    session_id: str
    crash_time: Optional[datetime] = None
    open_windows: List[str] = field(default_factory=list)
    unsaved_changes: Dict[str, Any] = field(default_factory=dict)
    last_module: Optional[str] = None
    user_id: Optional[int] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "crash_time": self.crash_time.isoformat() if self.crash_time else None,
            "open_windows": self.open_windows,
            "unsaved_changes": self.unsaved_changes,
            "last_module": self.last_module,
            "user_id": self.user_id
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "RecoveryData":
        """Create from dictionary."""
        return cls(
            session_id=data.get("session_id", ""),
            crash_time=datetime.fromisoformat(data["crash_time"]) if data.get("crash_time") else None,
            open_windows=data.get("open_windows", []),
            unsaved_changes=data.get("unsaved_changes", {}),
            last_module=data.get("last_module"),
            user_id=data.get("user_id")
        )


class RecoveryManager(QObject):
    """
    Crash recovery manager.

    Maintains session state and detects crashes.

    Signals:
        recovery_available(RecoveryData): Recovery data found from crash
        session_started(session_id): New session started
    """

    # Signals
    recovery_available = pyqtSignal(object)  # RecoveryData
    session_started = pyqtSignal(str)

    # Files
    STATE_FILE = Path.home() / ".integra" / "session_state.json"
    LOCK_FILE = Path.home() / ".integra" / "session.lock"

    def __init__(self):
        """Initialize recovery manager."""
        super().__init__()

        self._session_id: Optional[str] = None
        self._current_state: Optional[RecoveryData] = None

        # Ensure directory exists
        self.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    def check_for_recovery(self) -> Optional[RecoveryData]:
        """
        Check if there's recovery data from a previous crash.

        Returns:
            RecoveryData if crash detected, None otherwise
        """
        # Check for lock file (indicates unclean shutdown)
        if not self.LOCK_FILE.exists():
            return None

        # Check for state file
        if not self.STATE_FILE.exists():
            # Lock exists but no state - clean up
            self._remove_lock()
            return None

        try:
            with open(self.STATE_FILE, "r", encoding="utf-8") as f:
                state_data = json.load(f)

            recovery = RecoveryData.from_dict(state_data)
            recovery.crash_time = datetime.now()  # Mark when we detected

            # Don't remove files yet - let user decide
            return recovery

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Failed to read recovery data: {e}")
            # Corrupted state - clean up
            self._cleanup()
            return None

    def start_session(self, user_id: int = None) -> str:
        """
        Start a new session.

        Creates lock file and initializes state.

        Args:
            user_id: Current user ID (optional)

        Returns:
            Session ID
        """
        import uuid
        self._session_id = str(uuid.uuid4())[:8]

        self._current_state = RecoveryData(
            session_id=self._session_id,
            user_id=user_id
        )

        # Create lock file
        self._create_lock()

        # Save initial state
        self._save_state()

        self.session_started.emit(self._session_id)
        return self._session_id

    def end_session(self, clean: bool = True):
        """
        End the current session.

        Args:
            clean: If True, removes recovery files (normal shutdown)
        """
        if clean:
            self._cleanup()

        self._session_id = None
        self._current_state = None

    def update_state(
        self,
        open_windows: List[str] = None,
        last_module: str = None,
        unsaved_changes: Dict[str, Any] = None
    ):
        """
        Update session state.

        Called periodically and when state changes.

        Args:
            open_windows: List of open window IDs
            last_module: Currently active module
            unsaved_changes: Dict of unsaved form data
        """
        if self._current_state is None:
            return

        if open_windows is not None:
            self._current_state.open_windows = open_windows

        if last_module is not None:
            self._current_state.last_module = last_module

        if unsaved_changes is not None:
            self._current_state.unsaved_changes.update(unsaved_changes)

        self._save_state()

    def record_window_open(self, window_id: str):
        """Record that a window was opened."""
        if self._current_state and window_id not in self._current_state.open_windows:
            self._current_state.open_windows.append(window_id)
            self._save_state()

    def record_window_close(self, window_id: str):
        """Record that a window was closed."""
        if self._current_state and window_id in self._current_state.open_windows:
            self._current_state.open_windows.remove(window_id)
            self._save_state()

    def record_unsaved_change(self, form_id: str, data: Any):
        """Record unsaved changes for a form."""
        if self._current_state:
            self._current_state.unsaved_changes[form_id] = data
            self._save_state()

    def clear_unsaved_change(self, form_id: str):
        """Clear unsaved changes for a form (after save)."""
        if self._current_state and form_id in self._current_state.unsaved_changes:
            del self._current_state.unsaved_changes[form_id]
            self._save_state()

    def discard_recovery(self):
        """
        Discard recovery data (user chose not to restore).
        """
        self._cleanup()

    @property
    def session_id(self) -> Optional[str]:
        """Get current session ID."""
        return self._session_id

    @property
    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes."""
        return bool(
            self._current_state and
            self._current_state.unsaved_changes
        )

    def _save_state(self):
        """Save current state to file."""
        if self._current_state is None:
            return

        try:
            with open(self.STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self._current_state.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save session state: {e}")

    def _create_lock(self):
        """Create session lock file."""
        try:
            with open(self.LOCK_FILE, "w") as f:
                f.write(self._session_id or "")
        except Exception:
            pass

    def _remove_lock(self):
        """Remove session lock file."""
        try:
            if self.LOCK_FILE.exists():
                self.LOCK_FILE.unlink()
        except Exception:
            pass

    def _cleanup(self):
        """Clean up all recovery files."""
        self._remove_lock()

        try:
            if self.STATE_FILE.exists():
                self.STATE_FILE.unlink()
        except Exception:
            pass


# Singleton instance
_recovery_manager: Optional[RecoveryManager] = None


def get_recovery_manager() -> RecoveryManager:
    """Get the global RecoveryManager instance."""
    global _recovery_manager
    if _recovery_manager is None:
        _recovery_manager = RecoveryManager()
    return _recovery_manager
