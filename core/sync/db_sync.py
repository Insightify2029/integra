# -*- coding: utf-8 -*-
"""Database Sync v3 - عمليات backup و restore"""

import os
import subprocess
import time
from pathlib import Path
from typing import Callable

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
            error_lines = [line for line in stderr.split('\n')
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
