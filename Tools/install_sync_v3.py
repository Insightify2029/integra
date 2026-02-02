# Tools/install_sync_v3.py
"""
═══════════════════════════════════════════════════════════════════
  INTEGRA - تثبيت نظام المزامنة v3
═══════════════════════════════════════════════════════════════════
  cd /d D:\\Projects\\Integra
  python Tools\\install_sync_v3.py
═══════════════════════════════════════════════════════════════════
"""

import os
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent

print()
print("=" * 65)
print("  INTEGRA - تثبيت نظام المزامنة v3")
print("=" * 65)
print(f"  المسار: {PROJECT_ROOT}")
print(f"  التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("=" * 65)

# ═══════════════════════════════════════════════════════════════
# إنشاء المجلدات
# ═══════════════════════════════════════════════════════════════

dirs_to_create = [
    PROJECT_ROOT / "core" / "sync",
    PROJECT_ROOT / "backups" / "database",
    PROJECT_ROOT / "ui" / "components" / "progress",
]

for d in dirs_to_create:
    d.mkdir(parents=True, exist_ok=True)

print("\n[OK] المجلدات: تم إنشاؤها")

# ═══════════════════════════════════════════════════════════════
# 1. sync_config.py
# ═══════════════════════════════════════════════════════════════

SYNC_CONFIG = '''# -*- coding: utf-8 -*-
"""Sync Configuration v3 - تحميل وحفظ إعدادات المزامنة"""

import json
from pathlib import Path

_CONFIG_FILE = Path(__file__).parent.parent.parent / "sync_settings.json"

_DEFAULTS = {
    "sync_on_startup": True,
    "sync_on_exit_ask": True,
    "auto_sync_enabled": False,
    "auto_sync_interval_hours": 2,
    "last_sync_time": "",
    "last_sync_type": "",
    "backup_retention_days": 30,
}


def load_sync_config() -> dict:
    if _CONFIG_FILE.exists():
        try:
            with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            return {**_DEFAULTS, **config}
        except Exception:
            pass
    return dict(_DEFAULTS)


def save_sync_config(config: dict) -> bool:
    try:
        with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def get_config_value(key: str, default=None):
    config = load_sync_config()
    return config.get(key, default if default is not None else _DEFAULTS.get(key))


def set_config_value(key: str, value) -> bool:
    config = load_sync_config()
    config[key] = value
    return save_sync_config(config)
'''

(PROJECT_ROOT / "core" / "sync" / "sync_config.py").write_text(SYNC_CONFIG, encoding="utf-8")
print("[OK] 1/7 sync_config.py")

# ═══════════════════════════════════════════════════════════════
# 2. sync_status.py
# ═══════════════════════════════════════════════════════════════

SYNC_STATUS = '''# -*- coding: utf-8 -*-
"""Sync Status v3 - حالة المزامنة الموحدة"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


class SyncState(Enum):
    IDLE = "idle"
    SYNCING = "syncing"
    SUCCESS = "success"
    ERROR = "error"
    OFFLINE = "offline"
    PARTIAL = "partial"


@dataclass
class SyncResult:
    operation: str
    success: bool
    message: str
    duration_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SyncStatus:
    state: SyncState = SyncState.IDLE
    current_operation: str = ""
    progress_percent: int = 0
    progress_message: str = ""
    results: List[SyncResult] = field(default_factory=list)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    
    @property
    def is_syncing(self) -> bool:
        return self.state == SyncState.SYNCING
    
    @property
    def total_duration_ms(self) -> int:
        if self.started_at and self.finished_at:
            return int((self.finished_at - self.started_at).total_seconds() * 1000)
        return 0
    
    @property
    def all_success(self) -> bool:
        return all(r.success for r in self.results)
    
    @property
    def has_errors(self) -> bool:
        return any(not r.success for r in self.results)
    
    def add_result(self, operation: str, success: bool, message: str, duration_ms: int = 0):
        self.results.append(SyncResult(operation=operation, success=success,
                                        message=message, duration_ms=duration_ms))
    
    def start(self):
        self.state = SyncState.SYNCING
        self.started_at = datetime.now()
        self.results = []
        self.progress_percent = 0
    
    def finish(self):
        self.finished_at = datetime.now()
        if not self.results:
            self.state = SyncState.IDLE
        elif self.all_success:
            self.state = SyncState.SUCCESS
        elif self.has_errors and any(r.success for r in self.results):
            self.state = SyncState.PARTIAL
        else:
            self.state = SyncState.ERROR
        self.progress_percent = 100
    
    def get_summary(self) -> str:
        if self.state == SyncState.SUCCESS:
            return f"تمت المزامنة ({self.total_duration_ms}ms)"
        elif self.state == SyncState.PARTIAL:
            errors = [r for r in self.results if not r.success]
            return f"اكتملت جزئياً ({len(errors)} أخطاء)"
        elif self.state == SyncState.ERROR:
            return "فشلت المزامنة"
        elif self.state == SyncState.OFFLINE:
            return "لا يوجد اتصال"
        return ""
'''

(PROJECT_ROOT / "core" / "sync" / "sync_status.py").write_text(SYNC_STATUS, encoding="utf-8")
print("[OK] 2/7 sync_status.py")

# ═══════════════════════════════════════════════════════════════
# 3. backup_manager.py
# ═══════════════════════════════════════════════════════════════

BACKUP_MANAGER = '''# -*- coding: utf-8 -*-
"""Backup Manager v3 - إدارة ملفات النسخ الاحتياطي"""

import os
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class BackupInfo:
    filepath: Path
    filename: str
    timestamp: datetime
    size_bytes: int
    size_kb: float
    
    @property
    def age_days(self) -> int:
        return (datetime.now() - self.timestamp).days
    
    @property
    def formatted_time(self) -> str:
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    
    @property
    def formatted_size(self) -> str:
        if self.size_kb < 1024:
            return f"{self.size_kb:.1f} KB"
        return f"{self.size_kb/1024:.2f} MB"


class BackupManager:
    BACKUP_DIR_NAME = "backups/database"
    BACKUP_PREFIX = "backup_"
    BACKUP_EXT = ".sql"
    DATE_FORMAT = "%Y-%m-%d_%H-%M-%S"
    
    def __init__(self, project_root: Path = None):
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent
        self.project_root = project_root
        self.backup_dir = project_root / self.BACKUP_DIR_NAME
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._pg_dump_path: Optional[str] = None
        self._psql_path: Optional[str] = None
    
    def generate_backup_path(self) -> Path:
        timestamp = datetime.now().strftime(self.DATE_FORMAT)
        filename = f"{self.BACKUP_PREFIX}{timestamp}{self.BACKUP_EXT}"
        return self.backup_dir / filename
    
    def list_backups(self) -> List[BackupInfo]:
        backups = []
        pattern = f"{self.BACKUP_PREFIX}*{self.BACKUP_EXT}"
        for filepath in self.backup_dir.glob(pattern):
            try:
                filename = filepath.stem
                date_str = filename.replace(self.BACKUP_PREFIX, "")
                # Handle migrated files
                if "_migrated" in date_str:
                    date_str = date_str.replace("_migrated", "")
                timestamp = datetime.strptime(date_str, self.DATE_FORMAT)
                size_bytes = filepath.stat().st_size
                backups.append(BackupInfo(
                    filepath=filepath, filename=filepath.name,
                    timestamp=timestamp, size_bytes=size_bytes,
                    size_kb=size_bytes / 1024
                ))
            except (ValueError, OSError):
                continue
        backups.sort(key=lambda x: x.timestamp, reverse=True)
        return backups
    
    def get_latest_backup(self) -> Optional[BackupInfo]:
        backups = self.list_backups()
        return backups[0] if backups else None
    
    def get_backup_by_filename(self, filename: str) -> Optional[BackupInfo]:
        for backup in self.list_backups():
            if backup.filename == filename:
                return backup
        return None
    
    def calculate_file_hash(self, filepath: Path) -> str:
        if not filepath.exists():
            return ""
        hasher = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def cleanup_old_backups(self, retention_days: int = 30) -> Tuple[int, int]:
        backups = self.list_backups()
        now = datetime.now()
        deleted = 0
        kept = 0
        daily_backups = {}
        for backup in backups:
            date_key = backup.timestamp.date()
            if date_key not in daily_backups:
                daily_backups[date_key] = []
            daily_backups[date_key].append(backup)
        
        for date_key, day_backups in daily_backups.items():
            age_days = (now.date() - date_key).days
            if age_days <= 7:
                kept += len(day_backups)
            elif age_days <= retention_days:
                kept += 1
                for backup in day_backups[1:]:
                    try:
                        backup.filepath.unlink()
                        deleted += 1
                    except OSError:
                        pass
            else:
                for backup in day_backups:
                    try:
                        backup.filepath.unlink()
                        deleted += 1
                    except OSError:
                        pass
        return deleted, kept
    
    def find_pg_tool(self, tool_name: str) -> str:
        if tool_name == "pg_dump" and self._pg_dump_path:
            return self._pg_dump_path
        if tool_name == "psql" and self._psql_path:
            return self._psql_path
        
        exe_name = f"{tool_name}.exe"
        for version in ["17", "16", "15", "14"]:
            path = rf"C:\\Program Files\\PostgreSQL\\{version}\\bin\\{exe_name}"
            if os.path.exists(path):
                if tool_name == "pg_dump":
                    self._pg_dump_path = path
                else:
                    self._psql_path = path
                return path
        
        try:
            result = subprocess.run(["where", tool_name], capture_output=True,
                                    text=True, timeout=5, creationflags=0x08000000)
            if result.returncode == 0:
                path = result.stdout.strip().split("\\n")[0]
                if tool_name == "pg_dump":
                    self._pg_dump_path = path
                else:
                    self._psql_path = path
                return path
        except Exception:
            pass
        return ""
'''

(PROJECT_ROOT / "core" / "sync" / "backup_manager.py").write_text(BACKUP_MANAGER, encoding="utf-8")
print("[OK] 3/7 backup_manager.py")

# ═══════════════════════════════════════════════════════════════
# 4. db_sync.py
# ═══════════════════════════════════════════════════════════════

DB_SYNC = '''# -*- coding: utf-8 -*-
"""Database Sync v3 - عمليات backup و restore"""

import os
import subprocess
import time
from pathlib import Path
from typing import Callable, Optional
from datetime import datetime

from .backup_manager import BackupManager, BackupInfo
from .sync_status import SyncResult

CREATE_NO_WINDOW = 0x08000000


class DatabaseSync:
    TIMEOUT_BACKUP = 10
    TIMEOUT_RESTORE = 10
    
    def __init__(self, project_root: Path = None):
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent
        self.project_root = project_root
        self.backup_manager = BackupManager(project_root)
        self._db_password = self._load_db_password()
    
    def _load_db_password(self) -> str:
        env_file = self.project_root / ".env"
        if env_file.exists():
            try:
                with open(env_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("DB_PASSWORD="):
                            return line.split("=", 1)[1]
            except Exception:
                pass
        return ""
    
    def _get_env(self) -> dict:
        env = os.environ.copy()
        env["PGPASSWORD"] = self._db_password
        return env
    
    def backup(self, on_progress: Callable[[int, str], None] = None) -> SyncResult:
        start_time = time.time()
        
        if on_progress:
            on_progress(10, "جاري البحث عن pg_dump...")
        
        pg_dump = self.backup_manager.find_pg_tool("pg_dump")
        if not pg_dump:
            return SyncResult(operation="backup", success=False,
                              message="pg_dump غير موجود",
                              duration_ms=int((time.time() - start_time) * 1000))
        
        if on_progress:
            on_progress(20, "جاري تجهيز النسخة...")
        
        backup_path = self.backup_manager.generate_backup_path()
        
        try:
            if on_progress:
                on_progress(40, "جاري نسخ قاعدة البيانات...")
            
            result = subprocess.run(
                [pg_dump, "-U", "postgres", "-d", "integra",
                 "--clean", "--if-exists", "-f", str(backup_path)],
                capture_output=True, text=True, timeout=self.TIMEOUT_BACKUP,
                env=self._get_env(), creationflags=CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                if on_progress:
                    on_progress(90, "جاري التحقق...")
                
                size_kb = backup_path.stat().st_size / 1024
                duration_ms = int((time.time() - start_time) * 1000)
                
                if on_progress:
                    on_progress(100, f"تم النسخ ({size_kb:.0f} KB)")
                
                return SyncResult(operation="backup", success=True,
                                  message=f"تم النسخ ({size_kb:.0f} KB)",
                                  duration_ms=duration_ms)
            else:
                return SyncResult(operation="backup", success=False,
                                  message=result.stderr.strip()[:100] or "فشل",
                                  duration_ms=int((time.time() - start_time) * 1000))
        
        except subprocess.TimeoutExpired:
            return SyncResult(operation="backup", success=False,
                              message=f"انتهى الوقت ({self.TIMEOUT_BACKUP}s)",
                              duration_ms=self.TIMEOUT_BACKUP * 1000)
        except Exception as e:
            return SyncResult(operation="backup", success=False,
                              message=str(e)[:100],
                              duration_ms=int((time.time() - start_time) * 1000))
    
    def restore(self, backup_info: BackupInfo = None,
                on_progress: Callable[[int, str], None] = None) -> SyncResult:
        start_time = time.time()
        
        if on_progress:
            on_progress(10, "جاري البحث عن psql...")
        
        psql = self.backup_manager.find_pg_tool("psql")
        if not psql:
            return SyncResult(operation="restore", success=False,
                              message="psql غير موجود",
                              duration_ms=int((time.time() - start_time) * 1000))
        
        if backup_info is None:
            backup_info = self.backup_manager.get_latest_backup()
        
        if backup_info is None:
            return SyncResult(operation="restore", success=True,
                              message="لا توجد نسخ احتياطية",
                              duration_ms=int((time.time() - start_time) * 1000))
        
        if not backup_info.filepath.exists():
            return SyncResult(operation="restore", success=False,
                              message="ملف الـ backup غير موجود",
                              duration_ms=int((time.time() - start_time) * 1000))
        
        if on_progress:
            on_progress(30, f"جاري استعادة ({backup_info.formatted_size})...")
        
        try:
            result = subprocess.run(
                [psql, "-U", "postgres", "-d", "integra",
                 "-f", str(backup_info.filepath), "--quiet"],
                capture_output=True, text=True, timeout=self.TIMEOUT_RESTORE,
                env=self._get_env(), creationflags=CREATE_NO_WINDOW
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            stderr = result.stderr.strip()
            error_lines = [line for line in stderr.split('\\n')
                          if line.strip() and 'NOTICE' not in line
                          and 'does not exist' not in line
                          and 'already exists' not in line]
            
            if on_progress:
                on_progress(100, "تمت الاستعادة")
            
            if result.returncode == 0 or not error_lines:
                return SyncResult(operation="restore", success=True,
                                  message=f"تمت الاستعادة ({backup_info.formatted_size})",
                                  duration_ms=duration_ms)
            else:
                return SyncResult(operation="restore", success=True,
                                  message=f"تمت مع {len(error_lines)} تحذيرات",
                                  duration_ms=duration_ms)
        
        except subprocess.TimeoutExpired:
            return SyncResult(operation="restore", success=False,
                              message=f"انتهى الوقت ({self.TIMEOUT_RESTORE}s)",
                              duration_ms=self.TIMEOUT_RESTORE * 1000)
        except Exception as e:
            return SyncResult(operation="restore", success=False,
                              message=str(e)[:100],
                              duration_ms=int((time.time() - start_time) * 1000))
    
    def quick_restore(self, on_progress: Callable[[int, str], None] = None) -> SyncResult:
        return self.restore(on_progress=on_progress)
'''

(PROJECT_ROOT / "core" / "sync" / "db_sync.py").write_text(DB_SYNC, encoding="utf-8")
print("[OK] 4/7 db_sync.py")

# ═══════════════════════════════════════════════════════════════
# 5. git_sync.py
# ═══════════════════════════════════════════════════════════════

GIT_SYNC = '''# -*- coding: utf-8 -*-
"""Git Sync v3 - عمليات Git (يدوي فقط)"""

import subprocess
import time
from pathlib import Path
from typing import Callable
from datetime import datetime

from .sync_status import SyncResult

CREATE_NO_WINDOW = 0x08000000


class GitSync:
    TIMEOUT_PULL = 15
    TIMEOUT_PUSH = 15
    TIMEOUT_QUICK = 5
    
    def __init__(self, project_root: Path = None):
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent
        self.project_root = project_root
    
    def _run_git(self, args: list, timeout: int) -> tuple:
        try:
            result = subprocess.run(
                ["git"] + args, capture_output=True, text=True,
                timeout=timeout, cwd=str(self.project_root),
                creationflags=CREATE_NO_WINDOW
            )
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "", f"انتهى الوقت ({timeout}s)"
        except FileNotFoundError:
            return False, "", "Git غير مثبت"
        except Exception as e:
            return False, "", str(e)
    
    def pull(self, on_progress: Callable[[int, str], None] = None) -> SyncResult:
        start_time = time.time()
        
        if on_progress:
            on_progress(20, "جاري جلب التحديثات...")
        
        success, stdout, stderr = self._run_git(["pull"], self.TIMEOUT_PULL)
        duration_ms = int((time.time() - start_time) * 1000)
        
        if success:
            if on_progress:
                on_progress(100, "تم جلب التحديثات")
            
            if "Already up to date" in stdout:
                message = "لا توجد تحديثات جديدة"
            else:
                message = "تم جلب التحديثات"
            
            return SyncResult(operation="git_pull", success=True,
                              message=message, duration_ms=duration_ms)
        else:
            return SyncResult(operation="git_pull", success=False,
                              message=stderr[:100] or "فشل", duration_ms=duration_ms)
    
    def push(self, commit_message: str = None,
             on_progress: Callable[[int, str], None] = None) -> SyncResult:
        start_time = time.time()
        
        if commit_message is None:
            commit_message = f"Sync {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        if on_progress:
            on_progress(20, "جاري إضافة الملفات...")
        self._run_git(["add", "--all"], self.TIMEOUT_QUICK)
        
        if on_progress:
            on_progress(40, "جاري حفظ التغييرات...")
        self._run_git(["commit", "-m", commit_message], self.TIMEOUT_QUICK)
        
        if on_progress:
            on_progress(60, "جاري رفع التحديثات...")
        success, stdout, stderr = self._run_git(["push"], self.TIMEOUT_PUSH)
        duration_ms = int((time.time() - start_time) * 1000)
        
        if success or "Everything up-to-date" in stderr:
            if on_progress:
                on_progress(100, "تم رفع التحديثات")
            return SyncResult(operation="git_push", success=True,
                              message="تم رفع التحديثات", duration_ms=duration_ms)
        else:
            return SyncResult(operation="git_push", success=False,
                              message=stderr[:100] or "فشل", duration_ms=duration_ms)
    
    def check_connection(self) -> bool:
        success, _, _ = self._run_git(["ls-remote", "--exit-code", "-h"], 5)
        return success
'''

(PROJECT_ROOT / "core" / "sync" / "git_sync.py").write_text(GIT_SYNC, encoding="utf-8")
print("[OK] 5/7 git_sync.py")

# ═══════════════════════════════════════════════════════════════
# 6. sync_manager.py
# ═══════════════════════════════════════════════════════════════

SYNC_MANAGER = '''# -*- coding: utf-8 -*-
"""Sync Manager v3 - المدير الرئيسي لنظام المزامنة"""

from pathlib import Path
from typing import Callable, Optional
from datetime import datetime

from PyQt5.QtCore import QObject, QThread, pyqtSignal, QTimer

from .sync_config import load_sync_config, save_sync_config
from .sync_status import SyncStatus, SyncState
from .backup_manager import BackupManager, BackupInfo
from .db_sync import DatabaseSync
from .git_sync import GitSync


class SyncWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, sync_type: str, sync_manager):
        super().__init__()
        self.sync_type = sync_type
        self.sync_manager = sync_manager
    
    def run(self):
        try:
            if self.sync_type == "startup":
                result = self.sync_manager._do_startup_sync(self.progress.emit)
            elif self.sync_type == "shutdown":
                result = self.sync_manager._do_shutdown_sync(self.progress.emit)
            elif self.sync_type == "db_only":
                result = self.sync_manager._do_db_sync(self.progress.emit)
            elif self.sync_type == "git_pull":
                result = self.sync_manager._do_git_pull(self.progress.emit)
            elif self.sync_type == "git_push":
                result = self.sync_manager._do_git_push(self.progress.emit)
            else:
                result = (False, "نوع مزامنة غير معروف")
            self.finished.emit(result[0], result[1])
        except Exception as e:
            self.finished.emit(False, f"خطأ: {e}")


class SyncManager(QObject):
    sync_started = pyqtSignal(str)
    sync_progress = pyqtSignal(int, str)
    sync_finished = pyqtSignal(bool, str)
    status_changed = pyqtSignal(str)
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, project_root: Path = None):
        if hasattr(self, '_initialized'):
            return
        super().__init__()
        
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent
        
        self.project_root = project_root
        self.config = load_sync_config()
        self.status = SyncStatus()
        
        self.backup_manager = BackupManager(project_root)
        self.db_sync = DatabaseSync(project_root)
        self.git_sync = GitSync(project_root)
        
        self._worker: Optional[SyncWorker] = None
        self._auto_timer = QTimer()
        self._auto_timer.timeout.connect(self._on_auto_sync)
        self._setup_auto_sync()
        
        self._initialized = True
    
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
    
    def startup_sync(self, on_progress: Callable[[int, str], None] = None,
                     on_finished: Callable[[bool, str], None] = None,
                     blocking: bool = True):
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
    
    def shutdown_sync(self, on_progress: Callable[[int, str], None] = None,
                      on_finished: Callable[[bool, str], None] = None):
        self._start_worker("shutdown", on_progress, on_finished)
    
    def sync_database(self, on_progress: Callable[[int, str], None] = None,
                      on_finished: Callable[[bool, str], None] = None):
        self._start_worker("db_only", on_progress, on_finished)
    
    def git_pull(self, on_progress: Callable[[int, str], None] = None,
                 on_finished: Callable[[bool, str], None] = None):
        self._start_worker("git_pull", on_progress, on_finished)
    
    def git_push(self, on_progress: Callable[[int, str], None] = None,
                 on_finished: Callable[[bool, str], None] = None):
        self._start_worker("git_push", on_progress, on_finished)
    
    def restore_backup(self, backup_info: BackupInfo,
                       on_progress: Callable[[int, str], None] = None) -> tuple:
        return self.db_sync.restore(backup_info, on_progress).success, ""
    
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
    
    def _start_worker(self, sync_type: str, on_progress, on_finished):
        if self._worker and self._worker.isRunning():
            return
        
        self.status.start()
        self.sync_started.emit(sync_type)
        self.status_changed.emit("syncing")
        
        self._worker = SyncWorker(sync_type, self)
        
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
    
    def _update_last_sync(self, sync_type: str):
        self.config["last_sync_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.config["last_sync_type"] = sync_type
        save_sync_config(self.config)
    
    def _do_startup_sync(self, on_progress) -> tuple:
        if on_progress:
            on_progress(0, "جاري تزامن قاعدة البيانات...")
        result = self.db_sync.quick_restore(on_progress)
        self.status.add_result(result.operation, result.success,
                               result.message, result.duration_ms)
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
        self.status.add_result(result.operation, result.success,
                               result.message, result.duration_ms)
        
        if on_progress:
            on_progress(50, "جاري رفع البيانات...")
        
        def git_progress(p, m):
            if on_progress:
                on_progress(50 + int(p * 0.5), m)
        
        result = self.git_sync.push(on_progress=git_progress)
        results.append(result)
        self.status.add_result(result.operation, result.success,
                               result.message, result.duration_ms)
        
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


_sync_manager: Optional[SyncManager] = None


def get_sync_manager() -> SyncManager:
    global _sync_manager
    if _sync_manager is None:
        _sync_manager = SyncManager()
    return _sync_manager
'''

(PROJECT_ROOT / "core" / "sync" / "sync_manager.py").write_text(SYNC_MANAGER, encoding="utf-8")
print("[OK] 6/7 sync_manager.py")

# ═══════════════════════════════════════════════════════════════
# 7. progress_dialog.py
# ═══════════════════════════════════════════════════════════════

PROGRESS_DIALOG = '''# -*- coding: utf-8 -*-
"""Progress Dialog v3 - Progress Bar موحد لكل البرنامج"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QPushButton
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
import time


class ProgressDialog(QDialog):
    cancelled = pyqtSignal()
    
    BAR_COLOR = "#00E676"
    BAR_BG = "#424242"
    TEXT_COLOR = "#FFFFFF"
    BG_COLOR = "#2D2D2D"
    
    def __init__(self, title: str = "جاري التحميل...", parent=None,
                 show_cancel: bool = False, show_time: bool = True,
                 min_width: int = 400):
        super().__init__(parent)
        
        self.setWindowTitle("INTEGRA")
        self.setMinimumWidth(min_width)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        self.setModal(True)
        
        self._start_time = time.time()
        self._show_time = show_time
        self._last_percent = 0
        
        self._setup_ui(title, show_cancel)
        self._apply_style()
    
    def _setup_ui(self, title: str, show_cancel: bool):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 20, 25, 20)
        
        self._title_label = QLabel(title)
        self._title_label.setAlignment(Qt.AlignCenter)
        font = QFont("Cairo", 12, QFont.Bold)
        self._title_label.setFont(font)
        layout.addWidget(self._title_label)
        
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setFormat("%p%")
        self._progress_bar.setMinimumHeight(25)
        layout.addWidget(self._progress_bar)
        
        info_layout = QHBoxLayout()
        self._message_label = QLabel("")
        self._message_label.setAlignment(Qt.AlignLeft)
        info_layout.addWidget(self._message_label)
        info_layout.addStretch()
        self._time_label = QLabel("")
        self._time_label.setAlignment(Qt.AlignRight)
        info_layout.addWidget(self._time_label)
        layout.addLayout(info_layout)
        
        if show_cancel:
            self._cancel_btn = QPushButton("إلغاء")
            self._cancel_btn.clicked.connect(self._on_cancel)
            layout.addWidget(self._cancel_btn, alignment=Qt.AlignCenter)
        else:
            self._cancel_btn = None
    
    def _apply_style(self):
        self.setStyleSheet(f"""
            QDialog {{ background-color: {self.BG_COLOR}; }}
            QLabel {{ color: {self.TEXT_COLOR}; }}
            QProgressBar {{
                border: none; border-radius: 12px;
                background-color: {self.BAR_BG};
                text-align: center; color: {self.TEXT_COLOR};
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                border-radius: 12px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.BAR_COLOR}, stop:1 #69F0AE);
            }}
            QPushButton {{
                background-color: #616161; color: white;
                border: none; border-radius: 5px;
                padding: 8px 20px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #757575; }}
        """)
    
    def set_progress(self, percent: int, message: str = ""):
        percent = max(0, min(100, percent))
        self._progress_bar.setValue(percent)
        
        if message:
            self._message_label.setText(message)
        
        if self._show_time and percent > 0:
            elapsed = time.time() - self._start_time
            if percent < 100:
                estimated_total = elapsed / (percent / 100)
                remaining = estimated_total - elapsed
                if remaining > 0:
                    self._time_label.setText(f"الوقت المتبقي: {remaining:.0f} ثانية")
                else:
                    self._time_label.setText("")
            else:
                self._time_label.setText(f"انتهى في {elapsed:.1f} ثانية")
        
        self._last_percent = percent
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()
    
    def set_title(self, title: str):
        self._title_label.setText(title)
    
    def set_message(self, message: str):
        self._message_label.setText(message)
    
    def _on_cancel(self):
        self.cancelled.emit()
        self.close()
    
    def finish_success(self, message: str = "تم بنجاح!"):
        self.set_progress(100, message)
        QTimer.singleShot(500, self.accept)
    
    def finish_error(self, message: str = "حدث خطأ"):
        self._title_label.setText("خطأ: " + message)
        self._progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #F44336; }")
        if self._cancel_btn:
            self._cancel_btn.setText("إغلاق")
        else:
            QTimer.singleShot(2000, self.reject)


class QuickProgress:
    def __init__(self, title: str, parent=None):
        self.dialog = ProgressDialog(title, parent)
    
    def __enter__(self):
        self.dialog.show()
        return self.dialog
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.dialog.finish_success()
        else:
            self.dialog.finish_error(str(exc_val))
        return False
'''

progress_dir = PROJECT_ROOT / "ui" / "components" / "progress"
progress_dir.mkdir(parents=True, exist_ok=True)
(progress_dir / "progress_dialog.py").write_text(PROGRESS_DIALOG, encoding="utf-8")
(progress_dir / "__init__.py").write_text(
    "from .progress_dialog import ProgressDialog, QuickProgress\n",
    encoding="utf-8"
)
print("[OK] 7/7 progress_dialog.py")

# ═══════════════════════════════════════════════════════════════
# __init__.py للـ sync
# ═══════════════════════════════════════════════════════════════

SYNC_INIT = '''# -*- coding: utf-8 -*-
"""INTEGRA Sync System v3"""

from .sync_manager import SyncManager, get_sync_manager
from .sync_config import load_sync_config, save_sync_config
from .sync_status import SyncStatus, SyncState, SyncResult
from .backup_manager import BackupManager, BackupInfo
from .db_sync import DatabaseSync
from .git_sync import GitSync

__all__ = [
    'SyncManager', 'get_sync_manager',
    'load_sync_config', 'save_sync_config',
    'SyncStatus', 'SyncState', 'SyncResult',
    'BackupManager', 'BackupInfo',
    'DatabaseSync', 'GitSync',
]
'''

(PROJECT_ROOT / "core" / "sync" / "__init__.py").write_text(SYNC_INIT, encoding="utf-8")

# ═══════════════════════════════════════════════════════════════
# حذف الملفات القديمة
# ═══════════════════════════════════════════════════════════════

old_files = [
    PROJECT_ROOT / "core" / "sync" / "sync_runner.py",
    PROJECT_ROOT / "core" / "sync" / "sync_worker.py",
]

for f in old_files:
    if f.exists():
        f.unlink()
        print(f"[DEL] {f.name}")

# ═══════════════════════════════════════════════════════════════
# نقل الـ backups القديمة
# ═══════════════════════════════════════════════════════════════

import shutil

old_backup_locations = [
    PROJECT_ROOT / "database_backup.sql",
    PROJECT_ROOT / "Updates" / "integra_v2.1" / "database_backup.sql",
]

backup_dir = PROJECT_ROOT / "backups" / "database"

for old_backup in old_backup_locations:
    if old_backup.exists():
        new_name = f"backup_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_migrated.sql"
        new_path = backup_dir / new_name
        shutil.copy(str(old_backup), str(new_path))
        print(f"[MIGRATE] {old_backup.name} -> {new_name}")

# ═══════════════════════════════════════════════════════════════
# النتيجة
# ═══════════════════════════════════════════════════════════════

print()
print("=" * 65)
print("  تم تثبيت نظام المزامنة v3 بنجاح!")
print("=" * 65)
print()
print("  الملفات:")
print("  ---------")
print("  core/sync/sync_manager.py")
print("  core/sync/db_sync.py")
print("  core/sync/git_sync.py")
print("  core/sync/backup_manager.py")
print("  core/sync/sync_config.py")
print("  core/sync/sync_status.py")
print("  ui/components/progress/progress_dialog.py")
print()
print("  backups/database/  <- مجلد الـ backups الجديد")
print()
print("=" * 65)
print("  الخطوة التالية: تشغيل البرنامج للاختبار")
print("  python main.py")
print("=" * 65)
