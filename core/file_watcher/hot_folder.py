# -*- coding: utf-8 -*-
"""
Hot Folder
==========
Automated file processing pipeline.

Structure:
  - input/     : Drop files here for processing
  - processing/: Files being processed
  - archive/   : Successfully processed files
  - error/     : Failed files

Features:
  - Automatic file detection
  - Stability detection (wait for file to finish copying)
  - Processing pipeline with callbacks
  - Error handling and retry
"""

from typing import Optional, Callable, Dict, List, Any
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import shutil
import time
import threading

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from .watcher import FileWatcher, FileEvent, EventType


class ProcessingStatus(Enum):
    """File processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class ProcessingResult:
    """Result of file processing."""
    success: bool
    message: str = ""
    data: Any = None
    error: Optional[Exception] = None


@dataclass
class HotFolderConfig:
    """
    Hot folder configuration.

    Attributes:
        name: Folder name/identifier
        base_path: Base directory for hot folder
        patterns: File patterns to process
        processor: Callback function for processing
        stability_seconds: Wait time to ensure file is complete
        auto_archive: Move to archive after success
        auto_cleanup_days: Delete archived files after N days (0=never)
    """
    name: str
    base_path: Path
    patterns: List[str] = field(default_factory=lambda: ["*.xlsx", "*.csv"])
    processor: Optional[Callable[[Path], ProcessingResult]] = None
    stability_seconds: float = 2.0
    auto_archive: bool = True
    auto_cleanup_days: int = 30


class HotFolder(QObject):
    """
    Hot folder with automatic file processing.

    Signals:
        file_detected(path): New file detected in input
        processing_started(path): File processing started
        processing_completed(path, result): Processing finished
        error(path, message): Error occurred

    Usage:
        config = HotFolderConfig(
            name="imports",
            base_path=Path("data/imports"),
            patterns=["*.xlsx"],
            processor=my_import_function
        )

        hot_folder = HotFolder(config)
        hot_folder.start()
    """

    # Signals
    file_detected = pyqtSignal(object)  # Path
    processing_started = pyqtSignal(object)
    processing_completed = pyqtSignal(object, object)  # Path, ProcessingResult
    error = pyqtSignal(object, str)

    def __init__(self, config: HotFolderConfig):
        """Initialize hot folder."""
        super().__init__()

        self.config = config
        self._watcher = FileWatcher(debounce_seconds=config.stability_seconds)
        self._pending_files: Dict[str, datetime] = {}
        self._processing_lock = threading.Lock()
        self._running = False

        # Create folder structure
        self._setup_folders()

        # Connect watcher signals
        self._watcher.file_created.connect(self._on_file_created)

    @property
    def input_path(self) -> Path:
        """Input folder path."""
        return self.config.base_path / "input"

    @property
    def processing_path(self) -> Path:
        """Processing folder path."""
        return self.config.base_path / "processing"

    @property
    def archive_path(self) -> Path:
        """Archive folder path."""
        return self.config.base_path / "archive"

    @property
    def error_path(self) -> Path:
        """Error folder path."""
        return self.config.base_path / "error"

    def _setup_folders(self):
        """Create folder structure."""
        for folder in [self.input_path, self.processing_path,
                       self.archive_path, self.error_path]:
            folder.mkdir(parents=True, exist_ok=True)

    def start(self):
        """Start monitoring."""
        if self._running:
            return

        # Watch input folder
        self._watcher.watch(
            self.input_path,
            patterns=self.config.patterns,
            recursive=False
        )
        self._watcher.start()
        self._running = True

        # Process any existing files
        self._process_existing_files()

    def stop(self):
        """Stop monitoring."""
        if self._running:
            self._watcher.stop()
            self._running = False

    def _process_existing_files(self):
        """Process files already in input folder."""
        for pattern in self.config.patterns:
            for file_path in self.input_path.glob(pattern):
                if file_path.is_file():
                    self._queue_file(file_path)

    def _on_file_created(self, event: FileEvent):
        """Handle new file in input folder."""
        if event.path.parent == self.input_path:
            self._queue_file(event.path)

    def _queue_file(self, path: Path):
        """Queue a file for processing after stability check."""
        if not path.exists():
            return

        self.file_detected.emit(path)

        # Wait for file stability (ensure copy is complete)
        QTimer.singleShot(
            int(self.config.stability_seconds * 1000),
            lambda: self._check_and_process(path)
        )

    def _check_and_process(self, path: Path):
        """Check file stability and process."""
        if not path.exists():
            return

        # Check if file size is stable
        try:
            size1 = path.stat().st_size
            time.sleep(0.5)
            size2 = path.stat().st_size

            if size1 != size2:
                # File still being written, retry later
                QTimer.singleShot(2000, lambda: self._check_and_process(path))
                return

            self._process_file(path)

        except Exception as e:
            self.error.emit(path, str(e))

    def _process_file(self, path: Path):
        """Process a file."""
        with self._processing_lock:
            if not path.exists():
                return

            # Move to processing folder
            processing_file = self.processing_path / path.name
            try:
                shutil.move(str(path), str(processing_file))
            except Exception as e:
                self.error.emit(path, f"Failed to move to processing: {e}")
                return

            self.processing_started.emit(processing_file)

            # Process the file
            result = ProcessingResult(success=False, message="No processor configured")

            if self.config.processor:
                try:
                    result = self.config.processor(processing_file)
                except Exception as e:
                    result = ProcessingResult(
                        success=False,
                        message=str(e),
                        error=e
                    )

            # Move to appropriate folder
            if result.success:
                if self.config.auto_archive:
                    dest = self.archive_path / self._get_archive_name(processing_file)
                    shutil.move(str(processing_file), str(dest))
            else:
                dest = self.error_path / processing_file.name
                shutil.move(str(processing_file), str(dest))

            self.processing_completed.emit(processing_file, result)

    def _get_archive_name(self, path: Path) -> str:
        """Generate archive filename with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{path.stem}_{timestamp}{path.suffix}"

    def cleanup_archive(self) -> int:
        """
        Remove old archived files.

        Returns:
            Number of files deleted
        """
        if self.config.auto_cleanup_days <= 0:
            return 0

        cutoff = datetime.now().timestamp() - (self.config.auto_cleanup_days * 86400)
        deleted = 0

        for file_path in self.archive_path.iterdir():
            if file_path.is_file() and file_path.stat().st_mtime < cutoff:
                try:
                    file_path.unlink()
                    deleted += 1
                except Exception:
                    pass

        return deleted

    def get_stats(self) -> Dict:
        """Get folder statistics."""
        def count_files(folder: Path) -> int:
            return sum(1 for f in folder.iterdir() if f.is_file())

        return {
            "input": count_files(self.input_path),
            "processing": count_files(self.processing_path),
            "archive": count_files(self.archive_path),
            "error": count_files(self.error_path),
        }


class HotFolderManager(QObject):
    """
    Manager for multiple hot folders.

    Usage:
        manager = HotFolderManager()

        # Register hot folders
        manager.register("imports", config)
        manager.register("exports", config2)

        # Start all
        manager.start_all()
    """

    def __init__(self):
        super().__init__()
        self._folders: Dict[str, HotFolder] = {}

    def register(self, name: str, config: HotFolderConfig) -> HotFolder:
        """Register a hot folder."""
        config.name = name
        folder = HotFolder(config)
        self._folders[name] = folder
        return folder

    def unregister(self, name: str):
        """Unregister and stop a hot folder."""
        if name in self._folders:
            self._folders[name].stop()
            del self._folders[name]

    def get(self, name: str) -> Optional[HotFolder]:
        """Get a hot folder by name."""
        return self._folders.get(name)

    def start_all(self):
        """Start all hot folders."""
        for folder in self._folders.values():
            folder.start()

    def stop_all(self):
        """Stop all hot folders."""
        for folder in self._folders.values():
            folder.stop()

    def get_all_stats(self) -> Dict[str, Dict]:
        """Get stats for all hot folders."""
        return {
            name: folder.get_stats()
            for name, folder in self._folders.items()
        }


# Singleton instance
_hot_folder_manager: Optional[HotFolderManager] = None


def get_hot_folder_manager() -> HotFolderManager:
    """Get the global HotFolderManager instance."""
    global _hot_folder_manager
    if _hot_folder_manager is None:
        _hot_folder_manager = HotFolderManager()
    return _hot_folder_manager
