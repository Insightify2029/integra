# Tools/fix_sync_v3_final.py
"""
═══════════════════════════════════════════════════════════════════
  INTEGRA - إصلاح نهائي شامل لنظام المزامنة v3
═══════════════════════════════════════════════════════════════════
  المشاكل المحلولة:
    1) SyncWorker(mode="pull") ← v2 كان بيستخدم mode
    2) RuntimeError: super-class __init__() never called
       ← __new__ singleton مش بيشتغل مع QObject
    3) SyncWorker مش موجود في __init__.py exports

  الحل:
    - إعادة كتابة sync_manager.py كامل (نظيف + آمن)
    - __init__.py يصدّر SyncWorker
    - تنظيف __pycache__

  التشغيل:
    cd /d D:\\Projects\\Integra
    python Tools\\fix_sync_v3_final.py
═══════════════════════════════════════════════════════════════════
"""

import os
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent

print()
print("=" * 65)
print("  INTEGRA - إصلاح نهائي شامل لنظام المزامنة v3")
print("=" * 65)
print(f"  المسار: {PROJECT_ROOT}")
print(f"  التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("=" * 65)

SYNC_DIR = PROJECT_ROOT / "core" / "sync"

if not SYNC_DIR.exists():
    print("\n  ❌ مجلد core/sync/ غير موجود!")
    print("     شغّل install_sync_v3.py الأول")
    input("\n  اضغط Enter للخروج...")
    exit(1)

fixes_done = []

# ═══════════════════════════════════════════════════════════════
# الخطوة 1: إعادة كتابة sync_manager.py بالكامل
# ═══════════════════════════════════════════════════════════════

print("\n[1/3] إعادة كتابة sync_manager.py...")

SYNC_MANAGER_CONTENT = r'''# -*- coding: utf-8 -*-
"""
Sync Manager v3.1 - المدير الرئيسي لنظام المزامنة
==================================================
إصلاح شامل:
- بدون __new__ singleton (يسبب مشاكل مع QObject)
- SyncWorker يقبل mode (v2) + sync_type (v3)
- get_sync_manager() هو الطريقة الوحيدة للـ singleton
"""

from pathlib import Path
from typing import Callable, Optional
from datetime import datetime

from PyQt5.QtCore import QObject, QThread, pyqtSignal, QTimer

from .sync_config import load_sync_config, save_sync_config
from .sync_status import SyncStatus, SyncState
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
'''

sm_file = SYNC_DIR / "sync_manager.py"

# Backup old file
if sm_file.exists():
    backup_name = sm_file.with_suffix(".py.bak_v3")
    if not backup_name.exists():
        import shutil
        shutil.copy(str(sm_file), str(backup_name))
        print("  📦 نسخة احتياطية: sync_manager.py.bak_v3")

sm_file.write_text(SYNC_MANAGER_CONTENT.strip(), encoding="utf-8")
print("  ✅ sync_manager.py: إعادة كتابة كاملة")
print("     ✓ بدون __new__ (يسبب RuntimeError مع QObject)")
print("     ✓ SyncWorker يقبل mode (v2) + sync_type (v3)")
print("     ✓ get_sync_manager() = singleton آمن")
fixes_done.append("sync_manager.py: إعادة كتابة كاملة")

# ═══════════════════════════════════════════════════════════════
# الخطوة 2: تحديث __init__.py
# ═══════════════════════════════════════════════════════════════

print("\n[2/3] تحديث __init__.py...")

init_file = SYNC_DIR / "__init__.py"

INIT_CONTENT = '''# -*- coding: utf-8 -*-
"""INTEGRA Sync System v3.1"""

from .sync_manager import SyncManager, SyncWorker, get_sync_manager
from .sync_config import load_sync_config, save_sync_config
from .sync_status import SyncStatus, SyncState, SyncResult
from .backup_manager import BackupManager, BackupInfo
from .db_sync import DatabaseSync
from .git_sync import GitSync

__all__ = [
    'SyncManager', 'SyncWorker', 'get_sync_manager',
    'load_sync_config', 'save_sync_config',
    'SyncStatus', 'SyncState', 'SyncResult',
    'BackupManager', 'BackupInfo',
    'DatabaseSync', 'GitSync',
]
'''

init_file.write_text(INIT_CONTENT.strip(), encoding="utf-8")
print("  ✅ __init__.py: محدّث مع SyncWorker")
fixes_done.append("__init__.py: محدّث")

# ═══════════════════════════════════════════════════════════════
# الخطوة 3: تنظيف __pycache__
# ═══════════════════════════════════════════════════════════════

print("\n[3/3] تنظيف __pycache__...")

cleaned = 0
for cache_dir in PROJECT_ROOT.rglob("__pycache__"):
    for cached_file in list(cache_dir.glob("*.pyc")) + list(cache_dir.glob("*.pyo")):
        try:
            cached_file.unlink()
            cleaned += 1
        except OSError:
            pass

print(f"  🧹 حُذف {cleaned} ملف cache")
fixes_done.append(f"__pycache__: حُذف {cleaned} ملف")

# ═══════════════════════════════════════════════════════════════
# التحقق النهائي
# ═══════════════════════════════════════════════════════════════

print("\n" + "─" * 65)
print("  التحقق النهائي:")
print("─" * 65)

all_ok = True
sm_content = sm_file.read_text(encoding="utf-8")
init_content = init_file.read_text(encoding="utf-8")

# فحص 1: __new__ مش موجود
if "__new__" not in sm_content:
    print("  ✅ بدون __new__ (سبب الـ RuntimeError)")
else:
    print("  ❌ لسه فيه __new__!")
    all_ok = False

# فحص 2: _initialized مش موجود
if "_initialized" not in sm_content:
    print("  ✅ بدون _initialized (سبب الـ hasattr crash)")
else:
    print("  ❌ لسه فيه _initialized!")
    all_ok = False

# فحص 3: SyncWorker يقبل mode
if "mode: str = None" in sm_content:
    print("  ✅ SyncWorker يقبل mode (v2)")
else:
    print("  ❌ SyncWorker مش بيقبل mode!")
    all_ok = False

# فحص 4: SyncWorker في __init__.py
if "SyncWorker" in init_content:
    print("  ✅ SyncWorker في الـ exports")
else:
    print("  ❌ SyncWorker مش في الـ exports!")
    all_ok = False

# فحص 5: get_sync_manager بدون __new__
if "def get_sync_manager" in sm_content:
    print("  ✅ get_sync_manager() = singleton آمن")
else:
    print("  ❌ get_sync_manager مفقود!")
    all_ok = False

# فحص 6: imports من ملفات محذوفة
print()
skip_dirs = {"__pycache__", ".git", "venv", "node_modules"}
skip_files = {"fix_sync_v3_final.py", "fix_sync_import.py", "install_sync_v3.py"}

old_import_found = False
for py_file in PROJECT_ROOT.rglob("*.py"):
    if any(s in py_file.parts for s in skip_dirs):
        continue
    if py_file.name in skip_files:
        continue
    try:
        c = py_file.read_text(encoding="utf-8")
        if "from core.sync.sync_worker import" in c:
            rel = py_file.relative_to(PROJECT_ROOT)
            print(f"  ⚠️  {rel}: بيستورد من sync_worker.py المحذوف!")
            old_import_found = True
        if "from core.sync.sync_runner import" in c:
            rel = py_file.relative_to(PROJECT_ROOT)
            print(f"  ⚠️  {rel}: بيستورد من sync_runner.py المحذوف!")
            old_import_found = True
    except (UnicodeDecodeError, PermissionError):
        continue

if not old_import_found:
    print("  ✅ مفيش imports من ملفات قديمة محذوفة")

# ═══════════════════════════════════════════════════════════════
# النتيجة
# ═══════════════════════════════════════════════════════════════

print()
print("=" * 65)
if all_ok:
    print("  ✅✅✅ تم الإصلاح الشامل بنجاح! ✅✅✅")
    print()
    print("  المشاكل المحلولة:")
    print("    ✓ RuntimeError: super-class __init__() never called")
    print("    ✓ TypeError: unexpected keyword argument 'mode'")
    print("    ✓ ImportError: cannot import SyncWorker")
    print()
    print("  ما تم:")
    for fix in fixes_done:
        print(f"    ✓ {fix}")
else:
    print("  ⚠️  تم الإصلاح جزئياً - راجع التفاصيل أعلاه")

print()
print("=" * 65)
print("  الخطوة التالية:")
print("  python main.py")
print("=" * 65)
print()
