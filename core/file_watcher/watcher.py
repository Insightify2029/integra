# core/file_watcher/watcher.py
"""
INTEGRA - نظام مراقبة الملفات (watchdog)
=========================================

نظام مراقبة ملفات متكامل مع PyQt5 للكشف عن الملفات الجديدة والتغييرات.

الميزات:
- مراقبة مجلدات متعددة
- Debouncing لتجنب الأحداث المتكررة
- Stability detection للتأكد من اكتمال الملف
- تكامل مع PyQt5 عبر signals
- دعم فلترة الملفات حسب الامتداد

الاستخدام:
    from core.file_watcher import FileWatcher, watch_folder

    # الطريقة البسيطة
    watcher = watch_folder(
        path="/path/to/folder",
        on_file_created=handle_new_file,
        extensions=[".xlsx", ".csv"]
    )

    # الطريقة المتقدمة
    watcher = FileWatcher()
    watcher.signals.file_created.connect(handle_new_file)
    watcher.add_watch("/path/to/folder", extensions=[".xlsx"])
    watcher.start()
"""

import os
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Set, Callable, Dict
from dataclasses import dataclass

try:
    from watchdog.observers import Observer
    from watchdog.events import (
        FileSystemEventHandler,
        FileCreatedEvent,
        FileModifiedEvent,
        FileDeletedEvent,
        FileMovedEvent,
        DirCreatedEvent,
        DirDeletedEvent,
        DirMovedEvent
    )
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = object

from PyQt5.QtCore import QObject, pyqtSignal, QTimer


# ============================================================
# Constants
# ============================================================

DEFAULT_DEBOUNCE_SECONDS = 1.0
DEFAULT_STABILITY_SECONDS = 2.0
DEFAULT_STABILITY_CHECK_INTERVAL = 0.5


# ============================================================
# Data Classes
# ============================================================

@dataclass
class FileEvent:
    """معلومات حدث الملف"""
    path: str
    event_type: str  # created, modified, deleted, moved
    timestamp: datetime
    size: Optional[int] = None
    is_directory: bool = False
    dest_path: Optional[str] = None  # for moved events


# ============================================================
# Watcher Signals (for UI integration)
# ============================================================

class WatcherSignals(QObject):
    """إشارات للتكامل مع الواجهة"""
    file_created = pyqtSignal(str)          # file_path
    file_modified = pyqtSignal(str)         # file_path
    file_deleted = pyqtSignal(str)          # file_path
    file_moved = pyqtSignal(str, str)       # src_path, dest_path
    file_stable = pyqtSignal(str)           # file_path (file is ready)
    dir_created = pyqtSignal(str)           # dir_path
    dir_deleted = pyqtSignal(str)           # dir_path
    error = pyqtSignal(str, str)            # path, error_message
    watcher_started = pyqtSignal()
    watcher_stopped = pyqtSignal()


# ============================================================
# Event Handler
# ============================================================

class INTEGRAEventHandler(FileSystemEventHandler):
    """
    معالج أحداث الملفات مع debouncing و stability detection
    """

    def __init__(
        self,
        signals: WatcherSignals,
        extensions: Optional[List[str]] = None,
        debounce_seconds: float = DEFAULT_DEBOUNCE_SECONDS,
        stability_seconds: float = DEFAULT_STABILITY_SECONDS,
        ignore_directories: bool = False
    ):
        super().__init__()
        self.signals = signals
        self.extensions = set(ext.lower() for ext in (extensions or []))
        self.debounce_seconds = debounce_seconds
        self.stability_seconds = stability_seconds
        self.ignore_directories = ignore_directories

        # Debouncing
        self._last_events: Dict[str, float] = {}
        self._lock = threading.Lock()

        # Stability tracking
        self._pending_files: Dict[str, float] = {}  # path -> last_size
        self._stability_thread: Optional[threading.Thread] = None
        self._running = True

        # بدء مراقبة الاستقرار
        self._start_stability_monitor()

    def _should_process(self, path: str) -> bool:
        """هل يجب معالجة هذا الملف؟"""
        if not self.extensions:
            return True
        ext = Path(path).suffix.lower()
        return ext in self.extensions

    def _is_debounced(self, path: str) -> bool:
        """هل هذا الحدث مكرر (debounced)؟"""
        now = time.time()
        with self._lock:
            last_time = self._last_events.get(path, 0)
            if now - last_time < self.debounce_seconds:
                return True
            self._last_events[path] = now
            return False

    def _start_stability_monitor(self):
        """بدء مراقبة استقرار الملفات"""
        def monitor():
            while self._running:
                time.sleep(DEFAULT_STABILITY_CHECK_INTERVAL)
                self._check_file_stability()

        self._stability_thread = threading.Thread(target=monitor, daemon=True)
        self._stability_thread.start()

    def _check_file_stability(self):
        """فحص استقرار الملفات المعلقة"""
        now = time.time()
        stable_files = []

        with self._lock:
            for path, (last_size, last_check) in list(self._pending_files.items()):
                try:
                    if not os.path.exists(path):
                        del self._pending_files[path]
                        continue

                    current_size = os.path.getsize(path)

                    if current_size == last_size:
                        # الحجم ثابت
                        if now - last_check >= self.stability_seconds:
                            stable_files.append(path)
                            del self._pending_files[path]
                    else:
                        # الحجم تغير - تحديث
                        self._pending_files[path] = (current_size, now)

                except Exception:
                    # الملف غير متاح
                    if path in self._pending_files:
                        del self._pending_files[path]

        # إرسال إشارات للملفات المستقرة
        for path in stable_files:
            self.signals.file_stable.emit(path)

    def _add_pending_file(self, path: str):
        """إضافة ملف للمراقبة حتى يستقر"""
        try:
            size = os.path.getsize(path)
            with self._lock:
                self._pending_files[path] = (size, time.time())
        except Exception:
            pass

    def stop(self):
        """إيقاف المراقبة"""
        self._running = False

    # ============================================================
    # Event Handlers
    # ============================================================

    def on_created(self, event):
        """معالج إنشاء ملف/مجلد"""
        if event.is_directory:
            if not self.ignore_directories:
                self.signals.dir_created.emit(event.src_path)
            return

        if not self._should_process(event.src_path):
            return

        if self._is_debounced(event.src_path):
            return

        self.signals.file_created.emit(event.src_path)
        self._add_pending_file(event.src_path)

    def on_modified(self, event):
        """معالج تعديل ملف"""
        if event.is_directory:
            return

        if not self._should_process(event.src_path):
            return

        if self._is_debounced(event.src_path):
            return

        self.signals.file_modified.emit(event.src_path)

        # تحديث مراقبة الاستقرار
        self._add_pending_file(event.src_path)

    def on_deleted(self, event):
        """معالج حذف ملف/مجلد"""
        if event.is_directory:
            if not self.ignore_directories:
                self.signals.dir_deleted.emit(event.src_path)
            return

        if not self._should_process(event.src_path):
            return

        self.signals.file_deleted.emit(event.src_path)

        # إزالة من المراقبة
        with self._lock:
            if event.src_path in self._pending_files:
                del self._pending_files[event.src_path]

    def on_moved(self, event):
        """معالج نقل ملف/مجلد"""
        if event.is_directory:
            return

        if not self._should_process(event.src_path) and not self._should_process(event.dest_path):
            return

        self.signals.file_moved.emit(event.src_path, event.dest_path)


# ============================================================
# File Watcher
# ============================================================

class FileWatcher:
    """
    مراقب الملفات الرئيسي

    يوفر واجهة موحدة لمراقبة مجلدات متعددة.
    """

    def __init__(self):
        if not WATCHDOG_AVAILABLE:
            raise ImportError("watchdog غير متاح - pip install watchdog")

        self._observer: Optional[Observer] = None
        self._signals = WatcherSignals()
        self._handlers: Dict[str, INTEGRAEventHandler] = {}
        self._running = False

    @property
    def signals(self) -> WatcherSignals:
        """الإشارات للتكامل مع UI"""
        return self._signals

    @property
    def is_running(self) -> bool:
        """هل المراقبة تعمل؟"""
        return self._running

    def add_watch(
        self,
        path: str,
        extensions: Optional[List[str]] = None,
        recursive: bool = False,
        debounce_seconds: float = DEFAULT_DEBOUNCE_SECONDS,
        stability_seconds: float = DEFAULT_STABILITY_SECONDS,
        ignore_directories: bool = False
    ) -> bool:
        """
        إضافة مجلد للمراقبة

        Args:
            path: مسار المجلد
            extensions: قائمة الامتدادات للمراقبة (مثل [".xlsx", ".csv"])
            recursive: مراقبة المجلدات الفرعية
            debounce_seconds: تجاهل الأحداث المتكررة خلال هذه الفترة
            stability_seconds: انتظار استقرار الملف قبل إرسال file_stable
            ignore_directories: تجاهل أحداث المجلدات

        Returns:
            True إذا تمت الإضافة بنجاح
        """
        path = os.path.abspath(path)

        if not os.path.isdir(path):
            self._signals.error.emit(path, f"المجلد غير موجود: {path}")
            return False

        if path in self._handlers:
            return True  # موجود مسبقاً

        handler = INTEGRAEventHandler(
            signals=self._signals,
            extensions=extensions,
            debounce_seconds=debounce_seconds,
            stability_seconds=stability_seconds,
            ignore_directories=ignore_directories
        )

        self._handlers[path] = handler

        if self._observer and self._running:
            self._observer.schedule(handler, path, recursive=recursive)

        return True

    def remove_watch(self, path: str) -> bool:
        """إزالة مجلد من المراقبة"""
        path = os.path.abspath(path)

        if path not in self._handlers:
            return False

        handler = self._handlers.pop(path)
        handler.stop()

        # Observer doesn't have a direct unschedule by path
        # It will be cleaned up on restart
        return True

    def start(self) -> bool:
        """بدء المراقبة"""
        if self._running:
            return True

        try:
            self._observer = Observer()

            for path, handler in self._handlers.items():
                self._observer.schedule(handler, path, recursive=False)

            self._observer.start()
            self._running = True
            self._signals.watcher_started.emit()

            return True

        except Exception as e:
            self._signals.error.emit("", f"خطأ في بدء المراقبة: {e}")
            return False

    def stop(self):
        """إيقاف المراقبة"""
        if not self._running:
            return

        # إيقاف كل المعالجات
        for handler in self._handlers.values():
            handler.stop()

        # إيقاف المراقب
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None

        self._running = False
        self._signals.watcher_stopped.emit()

    def get_watched_paths(self) -> List[str]:
        """الحصول على قائمة المجلدات المراقبة"""
        return list(self._handlers.keys())


# ============================================================
# Singleton Access
# ============================================================

_file_watcher: Optional[FileWatcher] = None


def get_file_watcher() -> FileWatcher:
    """
    الحصول على مراقب الملفات

    Returns:
        FileWatcher singleton instance
    """
    global _file_watcher
    if _file_watcher is None:
        _file_watcher = FileWatcher()
    return _file_watcher


def is_watchdog_available() -> bool:
    """
    هل مكتبة watchdog متاحة؟

    Returns:
        True إذا كانت المكتبة مثبتة
    """
    return WATCHDOG_AVAILABLE


# ============================================================
# Convenience Functions
# ============================================================

def watch_folder(
    path: str,
    on_file_created: Optional[Callable[[str], None]] = None,
    on_file_stable: Optional[Callable[[str], None]] = None,
    on_file_modified: Optional[Callable[[str], None]] = None,
    on_file_deleted: Optional[Callable[[str], None]] = None,
    extensions: Optional[List[str]] = None,
    recursive: bool = False
) -> FileWatcher:
    """
    مراقبة مجلد بطريقة مبسطة

    Args:
        path: مسار المجلد
        on_file_created: callback عند إنشاء ملف
        on_file_stable: callback عند استقرار الملف (جاهز للمعالجة)
        on_file_modified: callback عند تعديل ملف
        on_file_deleted: callback عند حذف ملف
        extensions: قائمة الامتدادات للمراقبة
        recursive: مراقبة المجلدات الفرعية

    Returns:
        FileWatcher instance

    Example:
        watcher = watch_folder(
            "/path/to/imports",
            on_file_stable=process_import_file,
            extensions=[".xlsx", ".csv"]
        )
    """
    watcher = FileWatcher()

    if on_file_created:
        watcher.signals.file_created.connect(on_file_created)
    if on_file_stable:
        watcher.signals.file_stable.connect(on_file_stable)
    if on_file_modified:
        watcher.signals.file_modified.connect(on_file_modified)
    if on_file_deleted:
        watcher.signals.file_deleted.connect(on_file_deleted)

    watcher.add_watch(path, extensions=extensions, recursive=recursive)
    watcher.start()

    return watcher


def stop_all_watchers():
    """إيقاف كل المراقبين"""
    global _file_watcher
    if _file_watcher:
        _file_watcher.stop()
        _file_watcher = None
