"""
Auto-Save System
================
Automatic periodic saving of unsaved data to prevent data loss.

Features:
- Periodic auto-save using QTimer
- Saves form data to recovery files
- Configurable save interval
- Integration with recovery manager

Usage:
    from core.recovery import AutoSaveManager

    # Create manager for a form
    auto_save = AutoSaveManager(
        form_id="edit_employee_123",
        save_callback=self.get_form_data,
        interval_seconds=60
    )

    # Start auto-save
    auto_save.start()

    # Manual save
    auto_save.save_now()

    # Stop when form is saved
    auto_save.stop()
    auto_save.clear_recovery()
"""

import json
import os
from datetime import datetime
from typing import Callable, Optional, Any, Dict
from pathlib import Path

from PyQt5.QtCore import QTimer, QObject, pyqtSignal

from core.logging import app_logger


# Default configuration
DEFAULT_INTERVAL_SECONDS = 60
RECOVERY_DIR = Path("recovery_data")


class AutoSaveManager(QObject):
    """
    Manages automatic saving of form data.

    Signals:
        saved: Emitted when data is saved (recovery_file_path)
        save_failed: Emitted when save fails (error_message)
    """

    saved = pyqtSignal(str)
    save_failed = pyqtSignal(str)

    def __init__(
        self,
        form_id: str,
        save_callback: Callable[[], Dict[str, Any]],
        interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
        parent: Optional[QObject] = None
    ):
        """
        Initialize auto-save manager.

        Args:
            form_id: Unique identifier for the form (e.g., "edit_employee_123")
            save_callback: Function that returns form data as dict
            interval_seconds: Auto-save interval in seconds
            parent: Parent QObject
        """
        super().__init__(parent)

        self.form_id = form_id
        self.save_callback = save_callback
        self.interval_seconds = interval_seconds

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._auto_save)

        self._recovery_dir = RECOVERY_DIR
        self._ensure_recovery_dir()

        self._last_saved_data = None
        self._is_running = False

        app_logger.debug(f"AutoSaveManager created for {form_id}")

    def _ensure_recovery_dir(self) -> None:
        """Ensure recovery directory exists."""
        try:
            self._recovery_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            app_logger.error(f"Failed to create recovery dir: {e}")

    def start(self) -> None:
        """Start auto-save timer."""
        if self._is_running:
            return

        self._timer.start(self.interval_seconds * 1000)
        self._is_running = True
        app_logger.info(
            f"Auto-save started for {self.form_id} "
            f"(interval: {self.interval_seconds}s)"
        )

    def stop(self) -> None:
        """Stop auto-save timer."""
        if not self._is_running:
            return

        self._timer.stop()
        self._is_running = False
        app_logger.info(f"Auto-save stopped for {self.form_id}")

    def save_now(self) -> bool:
        """
        Perform immediate save.

        Returns:
            True if saved successfully, False otherwise
        """
        return self._auto_save()

    def _auto_save(self) -> bool:
        """Internal auto-save handler."""
        try:
            # Get current data
            current_data = self.save_callback()

            if current_data is None:
                return False

            # Check if data changed
            if current_data == self._last_saved_data:
                app_logger.debug(f"No changes to save for {self.form_id}")
                return True

            # Save to recovery file
            recovery_file = self._get_recovery_file_path()

            recovery_data = {
                "form_id": self.form_id,
                "timestamp": datetime.now().isoformat(),
                "data": current_data
            }

            with open(recovery_file, 'w', encoding='utf-8') as f:
                json.dump(recovery_data, f, ensure_ascii=False, indent=2)

            self._last_saved_data = current_data
            app_logger.info(f"Auto-saved {self.form_id} to {recovery_file}")
            self.saved.emit(str(recovery_file))
            return True

        except Exception as e:
            error_msg = f"Auto-save failed for {self.form_id}: {e}"
            app_logger.error(error_msg)
            self.save_failed.emit(error_msg)
            return False

    def _get_recovery_file_path(self) -> Path:
        """Get path for recovery file."""
        # Sanitize form_id for filename
        safe_id = self.form_id.replace("/", "_").replace("\\", "_")
        return self._recovery_dir / f"{safe_id}.recovery.json"

    def has_recovery_data(self) -> bool:
        """Check if recovery data exists for this form."""
        recovery_file = self._get_recovery_file_path()
        return recovery_file.exists()

    def get_recovery_data(self) -> Optional[Dict[str, Any]]:
        """
        Get saved recovery data.

        Returns:
            Recovery data dict or None if not available
        """
        try:
            recovery_file = self._get_recovery_file_path()

            if not recovery_file.exists():
                return None

            with open(recovery_file, 'r', encoding='utf-8') as f:
                recovery_data = json.load(f)

            return recovery_data.get("data")

        except Exception as e:
            app_logger.error(f"Failed to read recovery data: {e}")
            return None

    def get_recovery_timestamp(self) -> Optional[datetime]:
        """
        Get timestamp of last recovery save.

        Returns:
            Datetime of last save or None
        """
        try:
            recovery_file = self._get_recovery_file_path()

            if not recovery_file.exists():
                return None

            with open(recovery_file, 'r', encoding='utf-8') as f:
                recovery_data = json.load(f)

            timestamp_str = recovery_data.get("timestamp")
            if timestamp_str:
                return datetime.fromisoformat(timestamp_str)
            return None

        except Exception as e:
            app_logger.error(f"Failed to read recovery timestamp: {e}")
            return None

    def clear_recovery(self) -> bool:
        """
        Clear recovery data (call after successful save).

        Returns:
            True if cleared, False otherwise
        """
        try:
            recovery_file = self._get_recovery_file_path()

            if recovery_file.exists():
                recovery_file.unlink()
                app_logger.info(f"Cleared recovery for {self.form_id}")

            self._last_saved_data = None
            return True

        except Exception as e:
            app_logger.error(f"Failed to clear recovery: {e}")
            return False

    @property
    def is_running(self) -> bool:
        """Check if auto-save is running."""
        return self._is_running

    def set_interval(self, seconds: int) -> None:
        """Update auto-save interval."""
        self.interval_seconds = seconds
        if self._is_running:
            self._timer.setInterval(seconds * 1000)


def get_all_recovery_files() -> list:
    """
    Get list of all recovery files.

    Returns:
        List of recovery file info dicts
    """
    recovery_files = []

    try:
        if not RECOVERY_DIR.exists():
            return []

        for file_path in RECOVERY_DIR.glob("*.recovery.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                recovery_files.append({
                    "file_path": str(file_path),
                    "form_id": data.get("form_id", "unknown"),
                    "timestamp": data.get("timestamp"),
                    "size": file_path.stat().st_size
                })
            except Exception:
                continue

    except Exception as e:
        app_logger.error(f"Failed to list recovery files: {e}")

    return recovery_files


def clear_all_recovery_files() -> int:
    """
    Clear all recovery files.

    Returns:
        Number of files deleted
    """
    count = 0

    try:
        if not RECOVERY_DIR.exists():
            return 0

        for file_path in RECOVERY_DIR.glob("*.recovery.json"):
            try:
                file_path.unlink()
                count += 1
            except Exception:
                continue

        app_logger.info(f"Cleared {count} recovery files")

    except Exception as e:
        app_logger.error(f"Failed to clear recovery files: {e}")

    return count
