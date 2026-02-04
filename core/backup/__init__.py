# core/backup/__init__.py
"""
INTEGRA - نظام النسخ الاحتياطي المتقدم
======================================

نظام نسخ احتياطي متكامل مع استراتيجية GFS (Grandfather-Father-Son).

النسخ الفوري:
    from core.backup import backup_now, restore_backup

    # نسخة احتياطية فورية
    result = backup_now()
    if result.success:
        print(f"تم الحفظ: {result.file_path}")

    # استعادة
    success, msg = restore_backup("/path/to/backup.dump")

الجدولة التلقائية:
    from core.backup import get_backup_manager

    manager = get_backup_manager()
    manager.schedule_daily_backup(hour=2)      # 2 صباحاً
    manager.schedule_weekly_backup(day="sun")  # كل أحد
    manager.schedule_monthly_backup(day=1)     # أول كل شهر

سياسة الاحتفاظ GFS:
    - يومي (Son): آخر 7 نسخ
    - أسبوعي (Father): آخر 4 نسخ
    - شهري (Grandfather): آخر 12 نسخة

    # تغيير السياسة
    from core.backup import RetentionPolicy
    policy = RetentionPolicy(daily_count=14, weekly_count=8, monthly_count=24)
    manager.set_retention_policy(policy)

    # تنظيف النسخ القديمة
    from core.backup import cleanup_backups
    deleted = cleanup_backups()

التحقق من صحة النسخ:
    from core.backup import verify_backup
    valid, msg = verify_backup("/path/to/backup.dump")
"""

from .backup_manager import (
    # Manager
    BackupManager,
    get_backup_manager,

    # Data Classes
    BackupResult,
    BackupInfo,
    BackupType,
    RetentionPolicy,
    BackupSignals,

    # Convenience Functions
    backup_now,
    restore_backup,
    list_backups,
    get_latest_backup,
    cleanup_backups,
    verify_backup,

    # Constants
    BACKUP_DIR,
    DEFAULT_DAILY_RETENTION,
    DEFAULT_WEEKLY_RETENTION,
    DEFAULT_MONTHLY_RETENTION,
)

__all__ = [
    # Manager
    'BackupManager',
    'get_backup_manager',

    # Data Classes
    'BackupResult',
    'BackupInfo',
    'BackupType',
    'RetentionPolicy',
    'BackupSignals',

    # Convenience Functions
    'backup_now',
    'restore_backup',
    'list_backups',
    'get_latest_backup',
    'cleanup_backups',
    'verify_backup',

    # Constants
    'BACKUP_DIR',
    'DEFAULT_DAILY_RETENTION',
    'DEFAULT_WEEKLY_RETENTION',
    'DEFAULT_MONTHLY_RETENTION',
]
