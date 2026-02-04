# core/backup/backup_manager.py
"""
INTEGRA - نظام النسخ الاحتياطي المتقدم
======================================

نظام نسخ احتياطي متكامل مع استراتيجية GFS (Grandfather-Father-Son).

الميزات:
- نسخ احتياطي تلقائي مجدول
- استراتيجية GFS للاحتفاظ (يومي/أسبوعي/شهري)
- ضغط النسخ الاحتياطية
- التحقق من سلامة النسخ (checksum)
- تنظيف تلقائي للنسخ القديمة
- تكامل مع APScheduler

الاستخدام:
    from core.backup import get_backup_manager, backup_now

    # نسخة فورية
    result = backup_now()
    print(f"Backup: {result.file_path}")

    # جدولة النسخ الاحتياطي
    manager = get_backup_manager()
    manager.schedule_daily_backup(hour=2)  # 2 صباحاً
    manager.schedule_weekly_backup(day="sunday", hour=3)
    manager.schedule_monthly_backup(day=1, hour=4)

    # استعادة
    from core.backup import restore_backup
    restore_backup("/path/to/backup.sql")
"""

import os
import subprocess
import hashlib
import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import threading

from PyQt5.QtCore import QObject, pyqtSignal

# Try importing scheduler
try:
    from core.scheduler import get_scheduler, schedule_cron
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False


# ============================================================
# Constants
# ============================================================

BACKUP_DIR = Path(__file__).parent.parent.parent / "backups" / "database"
BACKUP_METADATA_FILE = BACKUP_DIR / "backup_metadata.json"

# GFS Retention Policy (default)
DEFAULT_DAILY_RETENTION = 7      # آخر 7 أيام
DEFAULT_WEEKLY_RETENTION = 4     # آخر 4 أسابيع
DEFAULT_MONTHLY_RETENTION = 12   # آخر 12 شهر


# ============================================================
# Data Classes
# ============================================================

class BackupType(Enum):
    """أنواع النسخ الاحتياطية"""
    MANUAL = "manual"       # يدوي
    DAILY = "daily"         # يومي (Son)
    WEEKLY = "weekly"       # أسبوعي (Father)
    MONTHLY = "monthly"     # شهري (Grandfather)
    ON_DEMAND = "on_demand" # عند الطلب


@dataclass
class BackupResult:
    """نتيجة عملية النسخ الاحتياطي"""
    success: bool
    file_path: Optional[str]
    file_size: int
    checksum: Optional[str]
    backup_type: str
    created_at: datetime
    duration_seconds: float
    error_message: Optional[str] = None


@dataclass
class BackupInfo:
    """معلومات نسخة احتياطية"""
    file_path: str
    file_name: str
    file_size: int
    checksum: str
    backup_type: str
    created_at: str
    database_name: str


# ============================================================
# Backup Signals
# ============================================================

class BackupSignals(QObject):
    """إشارات للتكامل مع الواجهة"""
    backup_started = pyqtSignal(str)           # backup_type
    backup_completed = pyqtSignal(str, bool)   # file_path, success
    backup_error = pyqtSignal(str)             # error_message
    restore_started = pyqtSignal(str)          # file_path
    restore_completed = pyqtSignal(bool)       # success
    cleanup_completed = pyqtSignal(int)        # deleted_count


# ============================================================
# Retention Policy
# ============================================================

@dataclass
class RetentionPolicy:
    """سياسة الاحتفاظ بالنسخ"""
    daily_count: int = DEFAULT_DAILY_RETENTION
    weekly_count: int = DEFAULT_WEEKLY_RETENTION
    monthly_count: int = DEFAULT_MONTHLY_RETENTION

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'RetentionPolicy':
        return cls(**data)


# ============================================================
# Backup Manager
# ============================================================

class BackupManager:
    """
    مدير النسخ الاحتياطي

    يوفر واجهة موحدة لإدارة النسخ الاحتياطية.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._signals = BackupSignals()
        self._retention = RetentionPolicy()
        self._metadata: Dict[str, BackupInfo] = {}

        # إنشاء مجلد النسخ
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        # تحميل metadata
        self._load_metadata()

    @property
    def signals(self) -> BackupSignals:
        """الإشارات للتكامل مع UI"""
        return self._signals

    @property
    def retention_policy(self) -> RetentionPolicy:
        """سياسة الاحتفاظ"""
        return self._retention

    def set_retention_policy(self, policy: RetentionPolicy):
        """تعيين سياسة الاحتفاظ"""
        self._retention = policy
        self._save_metadata()

    # ============================================================
    # Backup Operations
    # ============================================================

    def create_backup(
        self,
        backup_type: BackupType = BackupType.MANUAL,
        compress: bool = True,
        verify: bool = True
    ) -> BackupResult:
        """
        إنشاء نسخة احتياطية

        Args:
            backup_type: نوع النسخة
            compress: ضغط النسخة
            verify: التحقق من صحة النسخة

        Returns:
            BackupResult مع تفاصيل العملية
        """
        start_time = datetime.now()
        self._signals.backup_started.emit(backup_type.value)

        try:
            # الحصول على إعدادات قاعدة البيانات
            db_config = self._get_db_config()

            # توليد اسم الملف
            timestamp = start_time.strftime("%Y-%m-%d_%H-%M-%S")
            ext = ".dump" if compress else ".sql"
            filename = f"backup_{backup_type.value}_{timestamp}{ext}"
            file_path = BACKUP_DIR / filename

            # تنفيذ pg_dump
            cmd = self._build_pg_dump_command(
                db_config,
                str(file_path),
                compress=compress
            )

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 دقائق
            )

            if result.returncode != 0:
                raise Exception(f"pg_dump failed: {result.stderr}")

            # التحقق من الملف
            if not file_path.exists():
                raise Exception("Backup file not created")

            file_size = file_path.stat().st_size

            # حساب checksum
            checksum = None
            if verify:
                checksum = self._calculate_checksum(str(file_path))

            # حفظ metadata
            info = BackupInfo(
                file_path=str(file_path),
                file_name=filename,
                file_size=file_size,
                checksum=checksum or "",
                backup_type=backup_type.value,
                created_at=start_time.isoformat(),
                database_name=db_config.get('database', 'integra')
            )
            self._metadata[filename] = info
            self._save_metadata()

            duration = (datetime.now() - start_time).total_seconds()

            self._signals.backup_completed.emit(str(file_path), True)

            return BackupResult(
                success=True,
                file_path=str(file_path),
                file_size=file_size,
                checksum=checksum,
                backup_type=backup_type.value,
                created_at=start_time,
                duration_seconds=duration
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            self._signals.backup_error.emit(error_msg)
            self._signals.backup_completed.emit("", False)

            return BackupResult(
                success=False,
                file_path=None,
                file_size=0,
                checksum=None,
                backup_type=backup_type.value,
                created_at=start_time,
                duration_seconds=duration,
                error_message=error_msg
            )

    def restore_backup(
        self,
        file_path: str,
        verify_checksum: bool = True
    ) -> Tuple[bool, str]:
        """
        استعادة نسخة احتياطية

        Args:
            file_path: مسار ملف النسخة
            verify_checksum: التحقق من checksum قبل الاستعادة

        Returns:
            (success, message)
        """
        self._signals.restore_started.emit(file_path)

        try:
            path = Path(file_path)

            if not path.exists():
                raise Exception(f"File not found: {file_path}")

            # التحقق من checksum
            if verify_checksum:
                filename = path.name
                if filename in self._metadata:
                    stored_checksum = self._metadata[filename].checksum
                    if stored_checksum:
                        current_checksum = self._calculate_checksum(file_path)
                        if current_checksum != stored_checksum:
                            raise Exception("Checksum mismatch - file may be corrupted")

            # الحصول على إعدادات قاعدة البيانات
            db_config = self._get_db_config()

            # تحديد نوع الاستعادة
            is_compressed = file_path.endswith('.dump')

            if is_compressed:
                # pg_restore for compressed dumps
                cmd = self._build_pg_restore_command(db_config, file_path)
            else:
                # psql for plain SQL
                cmd = self._build_psql_command(db_config, file_path)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30 دقيقة
            )

            if result.returncode != 0:
                raise Exception(f"Restore failed: {result.stderr}")

            self._signals.restore_completed.emit(True)
            return True, "Restore completed successfully"

        except Exception as e:
            error_msg = str(e)
            self._signals.restore_completed.emit(False)
            return False, error_msg

    # ============================================================
    # Scheduling
    # ============================================================

    def schedule_daily_backup(self, hour: int = 2, minute: int = 0) -> bool:
        """جدولة نسخ يومي"""
        if not SCHEDULER_AVAILABLE:
            return False

        return schedule_cron(
            func=lambda: self.create_backup(BackupType.DAILY),
            job_id="integra_daily_backup",
            description="نسخ احتياطي يومي",
            hour=str(hour),
            minute=str(minute)
        )

    def schedule_weekly_backup(
        self,
        day_of_week: str = "sun",
        hour: int = 3,
        minute: int = 0
    ) -> bool:
        """جدولة نسخ أسبوعي"""
        if not SCHEDULER_AVAILABLE:
            return False

        return schedule_cron(
            func=lambda: self.create_backup(BackupType.WEEKLY),
            job_id="integra_weekly_backup",
            description="نسخ احتياطي أسبوعي",
            day_of_week=day_of_week,
            hour=str(hour),
            minute=str(minute)
        )

    def schedule_monthly_backup(
        self,
        day: int = 1,
        hour: int = 4,
        minute: int = 0
    ) -> bool:
        """جدولة نسخ شهري"""
        if not SCHEDULER_AVAILABLE:
            return False

        return schedule_cron(
            func=lambda: self.create_backup(BackupType.MONTHLY),
            job_id="integra_monthly_backup",
            description="نسخ احتياطي شهري",
            day=str(day),
            hour=str(hour),
            minute=str(minute)
        )

    # ============================================================
    # Cleanup (GFS Retention)
    # ============================================================

    def cleanup_old_backups(self) -> int:
        """
        تنظيف النسخ القديمة حسب سياسة GFS

        Returns:
            عدد النسخ المحذوفة
        """
        deleted_count = 0

        # تجميع النسخ حسب النوع
        backups_by_type: Dict[str, List[BackupInfo]] = {
            'daily': [],
            'weekly': [],
            'monthly': [],
            'manual': [],
            'on_demand': []
        }

        for info in self._metadata.values():
            btype = info.backup_type
            if btype in backups_by_type:
                backups_by_type[btype].append(info)

        # ترتيب حسب التاريخ (الأحدث أولاً)
        for btype in backups_by_type:
            backups_by_type[btype].sort(
                key=lambda x: x.created_at,
                reverse=True
            )

        # تطبيق سياسة الاحتفاظ
        to_delete = []

        # يومي
        if len(backups_by_type['daily']) > self._retention.daily_count:
            to_delete.extend(
                backups_by_type['daily'][self._retention.daily_count:]
            )

        # أسبوعي
        if len(backups_by_type['weekly']) > self._retention.weekly_count:
            to_delete.extend(
                backups_by_type['weekly'][self._retention.weekly_count:]
            )

        # شهري
        if len(backups_by_type['monthly']) > self._retention.monthly_count:
            to_delete.extend(
                backups_by_type['monthly'][self._retention.monthly_count:]
            )

        # حذف الملفات
        for info in to_delete:
            try:
                path = Path(info.file_path)
                if path.exists():
                    path.unlink()
                if info.file_name in self._metadata:
                    del self._metadata[info.file_name]
                deleted_count += 1
            except Exception:
                pass

        self._save_metadata()
        self._signals.cleanup_completed.emit(deleted_count)

        return deleted_count

    # ============================================================
    # Listing & Info
    # ============================================================

    def list_backups(self, backup_type: Optional[BackupType] = None) -> List[BackupInfo]:
        """قائمة النسخ الاحتياطية"""
        backups = list(self._metadata.values())

        if backup_type:
            backups = [b for b in backups if b.backup_type == backup_type.value]

        # ترتيب بالأحدث أولاً
        backups.sort(key=lambda x: x.created_at, reverse=True)

        return backups

    def get_backup_info(self, file_path: str) -> Optional[BackupInfo]:
        """الحصول على معلومات نسخة"""
        filename = Path(file_path).name
        return self._metadata.get(filename)

    def get_latest_backup(
        self,
        backup_type: Optional[BackupType] = None
    ) -> Optional[BackupInfo]:
        """الحصول على أحدث نسخة"""
        backups = self.list_backups(backup_type)
        return backups[0] if backups else None

    def get_stats(self) -> Dict:
        """إحصائيات النسخ الاحتياطي"""
        backups = list(self._metadata.values())

        total_size = sum(b.file_size for b in backups)

        return {
            "total_backups": len(backups),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "daily_count": len([b for b in backups if b.backup_type == 'daily']),
            "weekly_count": len([b for b in backups if b.backup_type == 'weekly']),
            "monthly_count": len([b for b in backups if b.backup_type == 'monthly']),
            "manual_count": len([b for b in backups if b.backup_type == 'manual']),
        }

    def verify_backup(self, file_path: str) -> Tuple[bool, str]:
        """التحقق من صحة نسخة احتياطية"""
        try:
            path = Path(file_path)

            if not path.exists():
                return False, "File not found"

            filename = path.name
            if filename not in self._metadata:
                return False, "Backup not in registry"

            stored_checksum = self._metadata[filename].checksum
            if not stored_checksum:
                return True, "No checksum stored - cannot verify"

            current_checksum = self._calculate_checksum(file_path)

            if current_checksum == stored_checksum:
                return True, "Checksum verified - backup is valid"
            else:
                return False, "Checksum mismatch - backup may be corrupted"

        except Exception as e:
            return False, f"Verification error: {e}"

    # ============================================================
    # Internal Methods
    # ============================================================

    def _get_db_config(self) -> Dict:
        """الحصول على إعدادات قاعدة البيانات"""
        try:
            from core.config import (
                DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
            )
            return {
                'host': DB_HOST,
                'port': str(DB_PORT),
                'database': DB_NAME,
                'user': DB_USER,
                'password': DB_PASSWORD
            }
        except ImportError:
            # Default values
            return {
                'host': 'localhost',
                'port': '5432',
                'database': 'integra',
                'user': 'postgres',
                'password': ''
            }

    def _build_pg_dump_command(
        self,
        config: Dict,
        output_path: str,
        compress: bool = True
    ) -> List[str]:
        """بناء أمر pg_dump"""
        cmd = ['pg_dump']

        cmd.extend(['-h', config['host']])
        cmd.extend(['-p', config['port']])
        cmd.extend(['-U', config['user']])
        cmd.extend(['-d', config['database']])

        if compress:
            cmd.extend(['-Fc'])  # Custom format (compressed)
        else:
            cmd.extend(['-Fp'])  # Plain SQL

        cmd.extend(['-f', output_path])

        # Set password via environment
        os.environ['PGPASSWORD'] = config.get('password', '')

        return cmd

    def _build_pg_restore_command(
        self,
        config: Dict,
        input_path: str
    ) -> List[str]:
        """بناء أمر pg_restore"""
        cmd = ['pg_restore']

        cmd.extend(['-h', config['host']])
        cmd.extend(['-p', config['port']])
        cmd.extend(['-U', config['user']])
        cmd.extend(['-d', config['database']])
        cmd.extend(['--clean'])  # Drop objects before creating
        cmd.extend(['--if-exists'])  # Don't error if objects don't exist
        cmd.append(input_path)

        os.environ['PGPASSWORD'] = config.get('password', '')

        return cmd

    def _build_psql_command(
        self,
        config: Dict,
        input_path: str
    ) -> List[str]:
        """بناء أمر psql"""
        cmd = ['psql']

        cmd.extend(['-h', config['host']])
        cmd.extend(['-p', config['port']])
        cmd.extend(['-U', config['user']])
        cmd.extend(['-d', config['database']])
        cmd.extend(['-f', input_path])

        os.environ['PGPASSWORD'] = config.get('password', '')

        return cmd

    def _calculate_checksum(self, file_path: str) -> str:
        """حساب checksum للملف"""
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

    def _load_metadata(self):
        """تحميل metadata"""
        if BACKUP_METADATA_FILE.exists():
            try:
                with open(BACKUP_METADATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for name, info_dict in data.get('backups', {}).items():
                    self._metadata[name] = BackupInfo(**info_dict)

                if 'retention' in data:
                    self._retention = RetentionPolicy.from_dict(data['retention'])

            except Exception:
                pass

    def _save_metadata(self):
        """حفظ metadata"""
        try:
            data = {
                'backups': {
                    name: asdict(info)
                    for name, info in self._metadata.items()
                },
                'retention': self._retention.to_dict()
            }

            with open(BACKUP_METADATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception:
            pass


# ============================================================
# Singleton Access
# ============================================================

_backup_manager: Optional[BackupManager] = None


def get_backup_manager() -> BackupManager:
    """
    الحصول على مدير النسخ الاحتياطي

    Returns:
        BackupManager singleton instance
    """
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupManager()
    return _backup_manager


# ============================================================
# Convenience Functions
# ============================================================

def backup_now(
    backup_type: BackupType = BackupType.MANUAL,
    compress: bool = True
) -> BackupResult:
    """
    إنشاء نسخة احتياطية فوراً

    Example:
        result = backup_now()
        if result.success:
            print(f"Backup saved: {result.file_path}")
    """
    return get_backup_manager().create_backup(backup_type, compress)


def restore_backup(file_path: str, verify: bool = True) -> Tuple[bool, str]:
    """
    استعادة نسخة احتياطية

    Example:
        success, msg = restore_backup("/path/to/backup.dump")
    """
    return get_backup_manager().restore_backup(file_path, verify)


def list_backups(backup_type: Optional[BackupType] = None) -> List[BackupInfo]:
    """قائمة النسخ الاحتياطية"""
    return get_backup_manager().list_backups(backup_type)


def get_latest_backup() -> Optional[BackupInfo]:
    """الحصول على أحدث نسخة"""
    return get_backup_manager().get_latest_backup()


def cleanup_backups() -> int:
    """تنظيف النسخ القديمة"""
    return get_backup_manager().cleanup_old_backups()


def verify_backup(file_path: str) -> Tuple[bool, str]:
    """التحقق من صحة نسخة"""
    return get_backup_manager().verify_backup(file_path)
