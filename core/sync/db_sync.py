# -*- coding: utf-8 -*-
"""Database Sync v3.1 - عمليات backup و restore محسّنة"""

import os
import subprocess
import time
from pathlib import Path
from typing import Callable

from .backup_manager import BackupManager, BackupInfo
from .sync_status import SyncResult

CREATE_NO_WINDOW = 0x08000000


class DatabaseSync:
    # زيادة الـ timeout للقواعد الكبيرة
    TIMEOUT_BACKUP = 120   # دقيقتين
    TIMEOUT_RESTORE = 120  # دقيقتين

    # إعدادات قاعدة البيانات
    DB_HOST = "localhost"
    DB_PORT = "5432"
    DB_NAME = "integra"
    DB_USER = "postgres"

    def __init__(self, project_root: Path = None):
        if project_root is None:
            project_root = self._find_project_root()
        self.project_root = project_root
        self.backup_manager = BackupManager(project_root)
        self._db_config = self._load_db_config()

    def _find_project_root(self) -> Path:
        """البحث عن مجلد المشروع بطرق متعددة"""
        # الطريقة 1: من موقع الملف الحالي
        from_file = Path(__file__).parent.parent.parent
        if (from_file / ".env").exists() or (from_file / "main.py").exists():
            return from_file

        # الطريقة 2: من مجلد العمل الحالي
        cwd = Path.cwd()
        if (cwd / ".env").exists() or (cwd / "main.py").exists():
            return cwd

        # الطريقة 3: من sys.path
        import sys
        for p in sys.path:
            path = Path(p)
            if (path / ".env").exists() or (path / "main.py").exists():
                return path

        # الافتراضي: مجلد العمل
        return cwd

    def _load_db_config(self) -> dict:
        """تحميل إعدادات قاعدة البيانات من .env"""
        config = {
            "host": self.DB_HOST,
            "port": self.DB_PORT,
            "name": self.DB_NAME,
            "user": self.DB_USER,
            "password": ""
        }

        # محاولة استخدام python-dotenv أولاً
        try:
            from dotenv import dotenv_values
            env_file = self.project_root / ".env"
            if env_file.exists():
                values = dotenv_values(str(env_file))
                config["password"] = values.get("DB_PASSWORD", "")
                config["host"] = values.get("DB_HOST", config["host"])
                config["port"] = values.get("DB_PORT", config["port"])
                config["name"] = values.get("DB_NAME", config["name"])
                config["user"] = values.get("DB_USER", config["user"])
                return config
        except ImportError:
            pass

        # قراءة يدوية من .env
        env_file = self.project_root / ".env"
        if env_file.exists():
            try:
                # محاولة قراءة بترميزات مختلفة
                content = None
                for encoding in ["utf-8", "utf-8-sig", "cp1256", "latin-1"]:
                    try:
                        with open(env_file, "r", encoding=encoding) as f:
                            content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue

                if content:
                    for line in content.splitlines():
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            if key == "DB_PASSWORD":
                                config["password"] = value
                            elif key == "DB_HOST":
                                config["host"] = value
                            elif key == "DB_PORT":
                                config["port"] = value
                            elif key == "DB_NAME":
                                config["name"] = value
                            elif key == "DB_USER":
                                config["user"] = value
            except Exception:
                pass

        return config

    def _get_env(self) -> dict:
        """تجهيز environment variables مع الباسورد"""
        env = os.environ.copy()
        # PGPASSWORD هو الطريقة الموثوقة لتمرير الباسورد
        if self._db_config["password"]:
            env["PGPASSWORD"] = self._db_config["password"]
        return env

    def _setup_pgpass(self) -> bool:
        """إنشاء ملف pgpass كبديل (Windows)"""
        try:
            if os.name == 'nt':  # Windows
                appdata = os.environ.get('APPDATA', '')
                pgpass_dir = Path(appdata) / 'postgresql'
                pgpass_file = pgpass_dir / 'pgpass.conf'
            else:  # Linux/Mac
                pgpass_file = Path.home() / '.pgpass'

            # إنشاء المجلد إذا لم يكن موجوداً
            pgpass_file.parent.mkdir(parents=True, exist_ok=True)

            # كتابة الملف
            cfg = self._db_config
            line = f"{cfg['host']}:{cfg['port']}:{cfg['name']}:{cfg['user']}:{cfg['password']}\n"

            with open(pgpass_file, 'w', encoding='utf-8') as f:
                f.write(line)

            # تعيين الصلاحيات (Linux/Mac فقط)
            if os.name != 'nt':
                os.chmod(pgpass_file, 0o600)

            return True
        except Exception:
            return False
    
    def backup(self, on_progress: Callable[[int, str], None] = None) -> SyncResult:
        start_time = time.time()

        if on_progress:
            on_progress(5, "جاري البحث عن pg_dump...")

        pg_dump = self.backup_manager.find_pg_tool("pg_dump")
        if not pg_dump:
            return SyncResult(operation="backup", success=False,
                              message="pg_dump غير موجود",
                              duration_ms=int((time.time() - start_time) * 1000))

        if on_progress:
            on_progress(10, "جاري تجهيز النسخة...")

        # إعداد pgpass كبديل للـ PGPASSWORD
        self._setup_pgpass()

        backup_path = self.backup_manager.generate_backup_path()
        cfg = self._db_config

        try:
            if on_progress:
                on_progress(20, "جاري نسخ قاعدة البيانات...")

            # استخدام المعلمات الكاملة للاتصال
            cmd = [
                pg_dump,
                "-h", cfg["host"],
                "-p", cfg["port"],
                "-U", cfg["user"],
                "-d", cfg["name"],
                "--no-password",  # لا تسأل عن الباسورد (استخدم PGPASSWORD)
                "--clean",
                "--if-exists",
                "-f", str(backup_path)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.TIMEOUT_BACKUP,
                env=self._get_env(),
                creationflags=CREATE_NO_WINDOW
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
                error_msg = result.stderr.strip()[:100] or "فشل النسخ"
                return SyncResult(operation="backup", success=False,
                                  message=error_msg,
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
            on_progress(5, "جاري البحث عن psql...")

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

        # إعداد pgpass
        self._setup_pgpass()
        cfg = self._db_config

        if on_progress:
            on_progress(20, f"جاري استعادة ({backup_info.formatted_size})...")

        try:
            cmd = [
                psql,
                "-h", cfg["host"],
                "-p", cfg["port"],
                "-U", cfg["user"],
                "-d", cfg["name"],
                "--no-password",
                "--quiet",
                "-f", str(backup_info.filepath)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.TIMEOUT_RESTORE,
                env=self._get_env(),
                creationflags=CREATE_NO_WINDOW
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
