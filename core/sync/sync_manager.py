# -*- coding: utf-8 -*-
"""
Sync Manager v3.1 - المدير الرئيسي لنظام المزامنة
==================================================
إصلاح شامل:
- بدون __new__ singleton (يسبب مشاكل مع QObject)
- SyncWorker يقبل mode (v2) + sync_type (v3)
- get_sync_manager() هو الطريقة الوحيدة للـ singleton
"""

from pathlib import Path
from typing import Optional
from datetime import datetime

from PyQt5.QtCore import QObject, QThread, pyqtSignal, QTimer

from .sync_config import load_sync_config, save_sync_config
from .sync_status import SyncStatus
from .backup_manager import BackupManager, BackupInfo
from .db_sync import DatabaseSync
from .git_sync import GitSync


# ═══════════════════════════════════════════════════════════════
# SyncWorker - يشتغل في thread منفصل
# ═══════════════════════════════════════════════════════════════

class SyncWorker(QThread):
    """
    Worker thread for sync operations.
    
    Backward compatible:
        SyncWorker(mode="pull")              ← v2 style
        SyncWorker(sync_type="git_pull")     ← v3 style
        SyncWorker("startup")               ← positional
    """
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    # Map v2 names → v3 names
    _MODE_MAP = {
        "pull": "startup",
        "push": "shutdown",
        "full": "shutdown",
        "sync": "db_only",
    }

    def __init__(self, sync_type: str = None, sync_manager=None, mode: str = None):
        super().__init__()

        # Backward compat: v2 used 'mode', v3 uses 'sync_type'
        if sync_type is None and mode is not None:
            sync_type = self._MODE_MAP.get(mode, mode)
        elif sync_type is None:
            sync_type = "startup"

        self.sync_type = sync_type
        self._sync_manager = sync_manager  # resolved lazily in run()

    def run(self):
        try:
            # Lazy resolve: get singleton only when thread starts
            sm = self._sync_manager
            if sm is None:
                sm = get_sync_manager()

            if self.sync_type == "startup":
                result = sm._do_startup_sync(self.progress.emit)
            elif self.sync_type == "shutdown":
                result = sm._do_shutdown_sync(self.progress.emit)
            elif self.sync_type == "db_only":
                result = sm._do_db_sync(self.progress.emit)
            elif self.sync_type in ("git_pull",):
                result = sm._do_git_pull(self.progress.emit)
            elif self.sync_type in ("git_push",):
                result = sm._do_git_push(self.progress.emit)
            else:
                result = (False, f"نوع مزامنة غير معروف: {self.sync_type}")

            self.finished.emit(result[0], result[1])
        except Exception as e:
            self.finished.emit(False, f"خطأ: {e}")


# ═══════════════════════════════════════════════════════════════
# SyncManager - المدير الرئيسي (بدون __new__)
# ═══════════════════════════════════════════════════════════════

class SyncManager(QObject):
    """
    Sync Manager - singleton via get_sync_manager().
    
    ملاحظة مهمة:
        لا تستخدم SyncManager() مباشرة
        استخدم get_sync_manager() بدلاً منها
    """
    sync_started = pyqtSignal(str)
    sync_progress = pyqtSignal(int, str)
    sync_finished = pyqtSignal(bool, str)
    status_changed = pyqtSignal(str)

    def __init__(self, project_root: Path = None, parent=None):
        super().__init__(parent)

        if project_root is None:
            project_root = Path(__file__).parent.parent.parent

        self.project_root = project_root
        self.config = load_sync_config()
        self.status = SyncStatus()

        self.backup_manager = BackupManager(project_root)
        self.db_sync = DatabaseSync(project_root)
        self.git_sync = GitSync(project_root)

        self._worker: Optional[SyncWorker] = None

        self._auto_timer = QTimer(self)
        self._auto_timer.timeout.connect(self._on_auto_sync)
        self._setup_auto_sync()

    # ───────────────────────────────────────────────
    # Auto sync
    # ───────────────────────────────────────────────

    def _setup_auto_sync(self):
        if self.config.get("auto_sync_enabled", False):
            hours = self.config.get("auto_sync_interval_hours", 2)
            interval_ms = hours * 60 * 60 * 1000
            self._auto_timer.start(interval_ms)
        else:
            self._auto_timer.stop()

    def _on_auto_sync(self):
        if not self.status.is_syncing:
            self.sync_database()

    # ───────────────────────────────────────────────
    # Public API
    # ───────────────────────────────────────────────

    def startup_sync(self, on_progress=None, on_finished=None, blocking=True):
        if not self.config.get("sync_on_startup", True):
            if on_finished:
                on_finished(True, "المزامنة معطلة")
            return

        if blocking:
            result = self._do_startup_sync(on_progress)
            if on_finished:
                on_finished(result[0], result[1])
        else:
            self._start_worker("startup", on_progress, on_finished)

    def shutdown_sync(self, on_progress=None, on_finished=None):
        self._start_worker("shutdown", on_progress, on_finished)

    def sync_database(self, on_progress=None, on_finished=None):
        self._start_worker("db_only", on_progress, on_finished)

    def git_pull(self, on_progress=None, on_finished=None):
        self._start_worker("git_pull", on_progress, on_finished)

    def git_push(self, on_progress=None, on_finished=None):
        self._start_worker("git_push", on_progress, on_finished)

    def restore_backup(self, backup_info: BackupInfo, on_progress=None) -> tuple:
        result = self.db_sync.restore(backup_info, on_progress)
        return result.success, result.message

    def list_backups(self):
        return self.backup_manager.list_backups()

    def get_latest_backup(self):
        return self.backup_manager.get_latest_backup()

    def cleanup_old_backups(self):
        retention = self.config.get("backup_retention_days", 30)
        return self.backup_manager.cleanup_old_backups(retention)

    def update_config(self, **kwargs):
        for key, value in kwargs.items():
            self.config[key] = value
        save_sync_config(self.config)
        self._setup_auto_sync()

    @property
    def is_syncing(self) -> bool:
        return self.status.is_syncing

    @property
    def last_sync_time(self) -> str:
        return self.config.get("last_sync_time", "")

    # ───────────────────────────────────────────────
    # Worker management
    # ───────────────────────────────────────────────

    def _start_worker(self, sync_type, on_progress, on_finished):
        if self._worker and self._worker.isRunning():
            return

        self.status.start()
        self.sync_started.emit(sync_type)
        self.status_changed.emit("syncing")

        self._worker = SyncWorker(sync_type=sync_type, sync_manager=self)

        if on_progress:
            self._worker.progress.connect(on_progress)
        self._worker.progress.connect(self.sync_progress.emit)

        def on_done(success, summary):
            self.status.finish()
            self._update_last_sync(sync_type)
            self.status_changed.emit("success" if success else "error")
            self.sync_finished.emit(success, summary)
            if on_finished:
                on_finished(success, summary)

        self._worker.finished.connect(on_done)
        self._worker.start()

    def _update_last_sync(self, sync_type):
        self.config["last_sync_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.config["last_sync_type"] = sync_type
        save_sync_config(self.config)

    # ───────────────────────────────────────────────
    # Sync operations (run in worker thread)
    # ───────────────────────────────────────────────

    def _do_startup_sync(self, on_progress) -> tuple:
        if on_progress:
            on_progress(0, "جاري تزامن قاعدة البيانات...")
        result = self.db_sync.quick_restore(on_progress)
        self.status.add_result(
            result.operation, result.success,
            result.message, result.duration_ms
        )
        return result.success, result.message

    def _do_shutdown_sync(self, on_progress) -> tuple:
        results = []

        if on_progress:
            on_progress(0, "جاري حفظ قاعدة البيانات...")

        def db_progress(p, m):
            if on_progress:
                on_progress(int(p * 0.5), m)

        result = self.db_sync.backup(db_progress)
        results.append(result)
        self.status.add_result(
            result.operation, result.success,
            result.message, result.duration_ms
        )

        if on_progress:
            on_progress(50, "جاري رفع البيانات...")

        def git_progress(p, m):
            if on_progress:
                on_progress(50 + int(p * 0.5), m)

        result = self.git_sync.push(on_progress=git_progress)
        results.append(result)
        self.status.add_result(
            result.operation, result.success,
            result.message, result.duration_ms
        )

        all_success = all(r.success for r in results)
        total_ms = sum(r.duration_ms for r in results)

        if all_success:
            return True, f"تمت المزامنة ({total_ms}ms)"
        else:
            failed = [r for r in results if not r.success]
            return False, f"فشل: {failed[0].message}"

    def _do_db_sync(self, on_progress) -> tuple:
        result = self.db_sync.backup(on_progress)
        if not result.success:
            return False, result.message
        self.git_sync.push()
        return True, "تمت المزامنة"

    def _do_git_pull(self, on_progress) -> tuple:
        result = self.git_sync.pull(on_progress)
        return result.success, result.message

    def _do_git_push(self, on_progress) -> tuple:
        result = self.git_sync.push(on_progress=on_progress)
        return result.success, result.message


# ═══════════════════════════════════════════════════════════════
# Singleton accessor (الطريقة الآمنة الوحيدة)
# ═══════════════════════════════════════════════════════════════

_sync_manager: Optional[SyncManager] = None


def get_sync_manager(project_root: Path = None) -> SyncManager:
    """Get or create the singleton SyncManager instance."""
    global _sync_manager
    if _sync_manager is None:
        _sync_manager = SyncManager(project_root)
    return _sync_manager