# -*- coding: utf-8 -*-
"""
Auto-Save System
================
Periodic auto-save of unsaved form data.

Features:
  - QTimer-based periodic saves
  - Per-form draft storage
  - Configurable interval
  - Automatic cleanup

Usage:
    # In a form/window
    from core.recovery import get_auto_save

    auto_save = get_auto_save()

    # Save draft when data changes
    auto_save.save_draft("employee_form", {
        "name_ar": "...",
        "phone": "..."
    })

    # Check for existing draft on form open
    draft = auto_save.get_draft("employee_form")
    if draft:
        # Ask user if they want to restore
        pass

    # Clear draft after successful save
    auto_save.clear_draft("employee_form")
"""

from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
import json

from PyQt5.QtCore import QObject, QTimer, pyqtSignal


class AutoSave(QObject):
    """
    Auto-save manager for form drafts.

    Signals:
        draft_saved(form_id): Draft was saved
        draft_restored(form_id, data): Draft was restored
    """

    # Signals
    draft_saved = pyqtSignal(str)
    draft_restored = pyqtSignal(str, dict)

    # Configuration
    DEFAULT_INTERVAL_SECONDS = 60
    MAX_DRAFT_AGE_HOURS = 24
    DRAFTS_DIR = Path.home() / ".integra" / "drafts"

    def __init__(self, interval_seconds: int = None):
        """
        Initialize auto-save manager.

        Args:
            interval_seconds: Save interval (default: 60 seconds)
        """
        super().__init__()

        self._interval = interval_seconds or self.DEFAULT_INTERVAL_SECONDS
        self._pending_drafts: Dict[str, Dict[str, Any]] = {}
        self._timer: Optional[QTimer] = None
        self._enabled = False

        # Ensure drafts directory exists
        self.DRAFTS_DIR.mkdir(parents=True, exist_ok=True)

    def start(self):
        """Start the auto-save timer."""
        if self._timer is None:
            self._timer = QTimer()
            self._timer.timeout.connect(self._save_all_pending)

        self._timer.start(self._interval * 1000)
        self._enabled = True

    def stop(self):
        """Stop the auto-save timer."""
        if self._timer:
            self._timer.stop()
        self._enabled = False

    @property
    def is_running(self) -> bool:
        """Check if auto-save is running."""
        return self._enabled

    def set_interval(self, seconds: int):
        """Change the auto-save interval."""
        self._interval = seconds
        if self._timer and self._enabled:
            self._timer.setInterval(seconds * 1000)

    def save_draft(self, form_id: str, data: Dict[str, Any], immediate: bool = False):
        """
        Queue or immediately save a draft.

        Args:
            form_id: Unique identifier for the form
            data: Form data to save
            immediate: Save immediately instead of waiting for timer
        """
        self._pending_drafts[form_id] = {
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "form_id": form_id
        }

        if immediate:
            self._save_draft_to_file(form_id)

    def get_draft(self, form_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a saved draft for a form.

        Args:
            form_id: Form identifier

        Returns:
            Draft data or None if not found/expired
        """
        # Check pending drafts first
        if form_id in self._pending_drafts:
            return self._pending_drafts[form_id]["data"]

        # Check file
        draft_file = self.DRAFTS_DIR / f"{form_id}.json"
        if not draft_file.exists():
            return None

        try:
            with open(draft_file, "r", encoding="utf-8") as f:
                draft = json.load(f)

            # Check if draft is expired
            timestamp = datetime.fromisoformat(draft["timestamp"])
            age = datetime.now() - timestamp

            if age > timedelta(hours=self.MAX_DRAFT_AGE_HOURS):
                # Draft expired, clean up
                draft_file.unlink()
                return None

            return draft["data"]

        except (json.JSONDecodeError, KeyError, ValueError):
            return None

    def has_draft(self, form_id: str) -> bool:
        """Check if a draft exists for a form."""
        if form_id in self._pending_drafts:
            return True

        draft_file = self.DRAFTS_DIR / f"{form_id}.json"
        return draft_file.exists()

    def clear_draft(self, form_id: str):
        """
        Clear a draft (after successful save).

        Args:
            form_id: Form identifier
        """
        # Remove from pending
        if form_id in self._pending_drafts:
            del self._pending_drafts[form_id]

        # Remove file
        draft_file = self.DRAFTS_DIR / f"{form_id}.json"
        if draft_file.exists():
            draft_file.unlink()

    def clear_all_drafts(self):
        """Clear all drafts."""
        self._pending_drafts.clear()

        for draft_file in self.DRAFTS_DIR.glob("*.json"):
            try:
                draft_file.unlink()
            except Exception:
                pass

    def get_all_drafts(self) -> List[Dict[str, Any]]:
        """
        Get all available drafts.

        Returns:
            List of draft info (form_id, timestamp)
        """
        drafts = []

        # From files
        for draft_file in self.DRAFTS_DIR.glob("*.json"):
            try:
                with open(draft_file, "r", encoding="utf-8") as f:
                    draft = json.load(f)

                timestamp = datetime.fromisoformat(draft["timestamp"])
                age = datetime.now() - timestamp

                if age <= timedelta(hours=self.MAX_DRAFT_AGE_HOURS):
                    drafts.append({
                        "form_id": draft["form_id"],
                        "timestamp": draft["timestamp"],
                        "age_minutes": int(age.total_seconds() / 60)
                    })
            except Exception:
                pass

        return drafts

    def cleanup_old_drafts(self):
        """Remove expired drafts."""
        for draft_file in self.DRAFTS_DIR.glob("*.json"):
            try:
                with open(draft_file, "r", encoding="utf-8") as f:
                    draft = json.load(f)

                timestamp = datetime.fromisoformat(draft["timestamp"])
                age = datetime.now() - timestamp

                if age > timedelta(hours=self.MAX_DRAFT_AGE_HOURS):
                    draft_file.unlink()
            except Exception:
                # Remove corrupted files too
                try:
                    draft_file.unlink()
                except Exception:
                    pass

    def _save_all_pending(self):
        """Save all pending drafts (called by timer)."""
        for form_id in list(self._pending_drafts.keys()):
            self._save_draft_to_file(form_id)

    def _save_draft_to_file(self, form_id: str):
        """Save a single draft to file."""
        if form_id not in self._pending_drafts:
            return

        draft_file = self.DRAFTS_DIR / f"{form_id}.json"

        try:
            with open(draft_file, "w", encoding="utf-8") as f:
                json.dump(self._pending_drafts[form_id], f, ensure_ascii=False, indent=2)

            self.draft_saved.emit(form_id)

        except Exception as e:
            print(f"Failed to save draft for {form_id}: {e}")


# Singleton instance
_auto_save: Optional[AutoSave] = None


def get_auto_save() -> AutoSave:
    """Get the global AutoSave instance."""
    global _auto_save
    if _auto_save is None:
        _auto_save = AutoSave()
    return _auto_save


# Convenience functions

def save_draft(form_id: str, data: Dict[str, Any], immediate: bool = False):
    """Save a draft for a form."""
    get_auto_save().save_draft(form_id, data, immediate)


def get_draft(form_id: str) -> Optional[Dict[str, Any]]:
    """Get a draft for a form."""
    return get_auto_save().get_draft(form_id)


def clear_drafts(form_id: str = None):
    """Clear drafts (specific or all)."""
    if form_id:
        get_auto_save().clear_draft(form_id)
    else:
        get_auto_save().clear_all_drafts()
