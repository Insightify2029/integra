# -*- coding: utf-8 -*-
"""
File Watcher
============
Core file system monitoring using watchdog.

Features:
  - Watch directories for file changes
  - Filter by file patterns (*.xlsx, *.csv, etc.)
  - Debouncing to handle multiple rapid events
  - PyQt5 signal integration
"""

from typing import Optional, List, Callable, Set
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import threading
import time

from PyQt5.QtCore import QObject, pyqtSignal

from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler,
    FileCreatedEvent,
    FileModifiedEvent,
    FileDeletedEvent,
    FileMovedEvent,
)


class EventType(Enum):
    """File event types."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


@dataclass
class FileEvent:
    """
    File system event data.

    Attributes:
        path: Path to the affected file
        event_type: Type of event
        timestamp: When event occurred
        dest_path: Destination path (for move events)
    """
    path: Path
    event_type: EventType
    timestamp: datetime
    dest_path: Optional[Path] = None

    @property
    def filename(self) -> str:
        """Get just the filename."""
        return self.path.name

    @property
    def extension(self) -> str:
        """Get file extension (lowercase, without dot)."""
        return self.path.suffix.lower().lstrip(".")


class _WatchdogHandler(FileSystemEventHandler):
    """Internal watchdog event handler."""

    def __init__(
        self,
        callback: Callable[[FileEvent], None],
        patterns: List[str] = None,
        ignore_directories: bool = True,
        debounce_seconds: float = 1.0
    ):
        super().__init__()
        self._callback = callback
        self._patterns = patterns or ["*"]
        self._ignore_dirs = ignore_directories
        self._debounce = debounce_seconds

        # Debouncing state
        self._last_events: dict = {}
        self._lock = threading.Lock()

    def _matches_pattern(self, path: Path) -> bool:
        """Check if path matches any watched pattern."""
        if "*" in self._patterns:
            return True

        name = path.name.lower()
        for pattern in self._patterns:
            pattern = pattern.lower()
            if pattern.startswith("*."):
                # Extension pattern
                ext = pattern[1:]  # .xlsx
                if name.endswith(ext):
                    return True
            elif pattern in name:
                return True

        return False

    def _should_process(self, path: str) -> bool:
        """Check debouncing - return True if event should be processed."""
        with self._lock:
            now = time.time()
            last_time = self._last_events.get(path, 0)

            if now - last_time < self._debounce:
                return False

            self._last_events[path] = now
            return True

    def _handle_event(self, event, event_type: EventType, dest_path: Path = None):
        """Process a file system event."""
        if self._ignore_dirs and event.is_directory:
            return

        path = Path(event.src_path)

        if not self._matches_pattern(path):
            return

        if not self._should_process(event.src_path):
            return

        file_event = FileEvent(
            path=path,
            event_type=event_type,
            timestamp=datetime.now(),
            dest_path=dest_path
        )

        self._callback(file_event)

    def on_created(self, event):
        self._handle_event(event, EventType.CREATED)

    def on_modified(self, event):
        self._handle_event(event, EventType.MODIFIED)

    def on_deleted(self, event):
        self._handle_event(event, EventType.DELETED)

    def on_moved(self, event):
        dest = Path(event.dest_path) if hasattr(event, 'dest_path') else None
        self._handle_event(event, EventType.MOVED, dest)


class FileWatcher(QObject):
    """
    File system watcher with PyQt5 integration.

    Signals:
        file_created(FileEvent): New file detected
        file_modified(FileEvent): File was modified
        file_deleted(FileEvent): File was deleted
        file_moved(FileEvent): File was moved/renamed
        error(str): Error occurred

    Usage:
        watcher = FileWatcher()

        # Watch a directory
        watcher.watch("/path/to/folder", patterns=["*.xlsx", "*.csv"])

        # Connect to signals
        watcher.file_created.connect(on_new_file)

        # Start watching
        watcher.start()
    """

    # Signals
    file_created = pyqtSignal(object)  # FileEvent
    file_modified = pyqtSignal(object)
    file_deleted = pyqtSignal(object)
    file_moved = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, debounce_seconds: float = 1.0):
        """
        Initialize file watcher.

        Args:
            debounce_seconds: Minimum time between events for same file
        """
        super().__init__()

        self._observer = Observer()
        self._watches: dict = {}  # path -> watch handle
        self._debounce = debounce_seconds
        self._running = False

    def watch(
        self,
        path: str | Path,
        patterns: List[str] = None,
        recursive: bool = False
    ) -> bool:
        """
        Add a directory to watch.

        Args:
            path: Directory path to watch
            patterns: File patterns to watch (e.g., ["*.xlsx", "*.csv"])
            recursive: Watch subdirectories

        Returns:
            True if watch was added
        """
        path = Path(path)

        if not path.exists():
            self.error.emit(f"Path does not exist: {path}")
            return False

        if not path.is_dir():
            self.error.emit(f"Path is not a directory: {path}")
            return False

        path_str = str(path)
        if path_str in self._watches:
            return True  # Already watching

        handler = _WatchdogHandler(
            callback=self._on_event,
            patterns=patterns,
            debounce_seconds=self._debounce
        )

        try:
            watch = self._observer.schedule(handler, path_str, recursive=recursive)
            self._watches[path_str] = watch
            return True
        except Exception as e:
            self.error.emit(f"Failed to watch {path}: {e}")
            return False

    def unwatch(self, path: str | Path) -> bool:
        """
        Stop watching a directory.

        Args:
            path: Directory to stop watching

        Returns:
            True if watch was removed
        """
        path_str = str(Path(path))

        if path_str not in self._watches:
            return False

        watch = self._watches.pop(path_str)
        self._observer.unschedule(watch)
        return True

    def start(self):
        """Start the file watcher."""
        if not self._running:
            self._observer.start()
            self._running = True

    def stop(self):
        """Stop the file watcher."""
        if self._running:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._running = False

    @property
    def is_running(self) -> bool:
        """Check if watcher is running."""
        return self._running

    @property
    def watched_paths(self) -> List[str]:
        """Get list of watched paths."""
        return list(self._watches.keys())

    def _on_event(self, event: FileEvent):
        """Handle file event and emit appropriate signal."""
        if event.event_type == EventType.CREATED:
            self.file_created.emit(event)
        elif event.event_type == EventType.MODIFIED:
            self.file_modified.emit(event)
        elif event.event_type == EventType.DELETED:
            self.file_deleted.emit(event)
        elif event.event_type == EventType.MOVED:
            self.file_moved.emit(event)


# Singleton instance
_file_watcher: Optional[FileWatcher] = None


def get_file_watcher() -> FileWatcher:
    """Get the global FileWatcher instance."""
    global _file_watcher
    if _file_watcher is None:
        _file_watcher = FileWatcher()
    return _file_watcher
