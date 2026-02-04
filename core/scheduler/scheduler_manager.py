# core/scheduler/scheduler_manager.py
"""
INTEGRA - نظام الجدولة (APScheduler)
=====================================

نظام جدولة متكامل مع PyQt5 لتشغيل المهام بشكل دوري أو في أوقات محددة.

الميزات:
- تكامل كامل مع PyQt5 event loop
- دعم المهام الدورية (interval) والمجدولة (cron)
- معالجة المهام الفائتة (misfire handling)
- إدارة مركزية للمهام المجدولة
- حفظ حالة المهام في ملف JSON

الاستخدام:
    from core.scheduler import get_scheduler, schedule_job, schedule_interval

    # مهمة دورية كل 5 دقائق
    schedule_interval(
        my_function,
        minutes=5,
        job_id="my_task",
        args=(arg1,)
    )

    # مهمة يومية الساعة 9 صباحاً
    from core.scheduler import schedule_cron
    schedule_cron(
        daily_report,
        hour=9,
        minute=0,
        job_id="daily_report"
    )

    # إيقاف مهمة
    from core.scheduler import remove_job
    remove_job("my_task")
"""

import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, Any, Dict, List
from dataclasses import dataclass, asdict
from enum import Enum

try:
    from apscheduler.schedulers.qt import QtScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.date import DateTrigger
    from apscheduler.events import (
        EVENT_JOB_EXECUTED,
        EVENT_JOB_ERROR,
        EVENT_JOB_MISSED,
        EVENT_JOB_ADDED,
        EVENT_JOB_REMOVED
    )
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    QtScheduler = None

from PyQt5.QtCore import QObject, pyqtSignal


# ============================================================
# Constants
# ============================================================

SCHEDULER_CONFIG_FILE = Path(__file__).parent.parent.parent / "scheduler_config.json"
DEFAULT_MISFIRE_GRACE_TIME = 60 * 5  # 5 دقائق


# ============================================================
# Data Classes
# ============================================================

class JobType(Enum):
    """أنواع المهام المجدولة"""
    INTERVAL = "interval"  # كل فترة زمنية
    CRON = "cron"          # جدول cron
    DATE = "date"          # تاريخ محدد


@dataclass
class ScheduledJob:
    """معلومات المهمة المجدولة"""
    job_id: str
    job_type: str
    description: str
    next_run: Optional[str] = None
    last_run: Optional[str] = None
    run_count: int = 0
    error_count: int = 0
    enabled: bool = True


# ============================================================
# Scheduler Signals (for UI integration)
# ============================================================

class SchedulerSignals(QObject):
    """إشارات للتكامل مع الواجهة"""
    job_executed = pyqtSignal(str, object)     # job_id, result
    job_error = pyqtSignal(str, str)           # job_id, error_message
    job_missed = pyqtSignal(str)               # job_id
    job_added = pyqtSignal(str)                # job_id
    job_removed = pyqtSignal(str)              # job_id
    scheduler_started = pyqtSignal()
    scheduler_stopped = pyqtSignal()


# ============================================================
# Scheduler Manager
# ============================================================

class SchedulerManager:
    """
    مدير الجدولة المركزي

    يوفر واجهة موحدة لإدارة المهام المجدولة في التطبيق.
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
        self._scheduler: Optional[QtScheduler] = None
        self._signals = SchedulerSignals()
        self._job_stats: Dict[str, ScheduledJob] = {}
        self._running = False

        # تحميل الإعدادات المحفوظة
        self._load_config()

    @property
    def signals(self) -> SchedulerSignals:
        """الإشارات للتكامل مع UI"""
        return self._signals

    @property
    def is_running(self) -> bool:
        """هل الجدولة تعمل؟"""
        return self._running and self._scheduler is not None

    def start(self) -> bool:
        """
        بدء نظام الجدولة

        Returns:
            True إذا بدأ بنجاح
        """
        if not APSCHEDULER_AVAILABLE:
            print("⚠️ APScheduler غير متاح - pip install apscheduler")
            return False

        if self._running:
            return True

        try:
            # إنشاء الـ scheduler
            self._scheduler = QtScheduler(
                job_defaults={
                    'coalesce': True,  # دمج المهام الفائتة
                    'max_instances': 1,  # نسخة واحدة من كل مهمة
                    'misfire_grace_time': DEFAULT_MISFIRE_GRACE_TIME
                }
            )

            # ربط الأحداث
            self._scheduler.add_listener(
                self._on_job_executed,
                EVENT_JOB_EXECUTED
            )
            self._scheduler.add_listener(
                self._on_job_error,
                EVENT_JOB_ERROR
            )
            self._scheduler.add_listener(
                self._on_job_missed,
                EVENT_JOB_MISSED
            )
            self._scheduler.add_listener(
                self._on_job_added,
                EVENT_JOB_ADDED
            )
            self._scheduler.add_listener(
                self._on_job_removed,
                EVENT_JOB_REMOVED
            )

            # بدء التشغيل
            self._scheduler.start()
            self._running = True
            self._signals.scheduler_started.emit()

            return True

        except Exception as e:
            print(f"❌ خطأ في بدء الجدولة: {e}")
            return False

    def stop(self, wait: bool = True):
        """
        إيقاف نظام الجدولة

        Args:
            wait: انتظار انتهاء المهام الجارية
        """
        if self._scheduler and self._running:
            self._scheduler.shutdown(wait=wait)
            self._running = False
            self._save_config()
            self._signals.scheduler_stopped.emit()

    def add_interval_job(
        self,
        func: Callable,
        job_id: str,
        description: str = "",
        seconds: int = 0,
        minutes: int = 0,
        hours: int = 0,
        days: int = 0,
        args: tuple = None,
        kwargs: dict = None,
        start_immediately: bool = False
    ) -> bool:
        """
        إضافة مهمة دورية

        Args:
            func: الدالة المراد تنفيذها
            job_id: معرف فريد للمهمة
            description: وصف المهمة
            seconds/minutes/hours/days: الفترة الزمنية
            args: arguments للدالة
            kwargs: keyword arguments للدالة
            start_immediately: تنفيذ فوري ثم بدء الدورة

        Returns:
            True إذا تمت الإضافة بنجاح
        """
        if not self._ensure_running():
            return False

        try:
            trigger = IntervalTrigger(
                seconds=seconds,
                minutes=minutes,
                hours=hours,
                days=days
            )

            self._scheduler.add_job(
                func,
                trigger=trigger,
                id=job_id,
                name=description or job_id,
                args=args or (),
                kwargs=kwargs or {},
                replace_existing=True
            )

            # حفظ معلومات المهمة
            self._job_stats[job_id] = ScheduledJob(
                job_id=job_id,
                job_type=JobType.INTERVAL.value,
                description=description or job_id
            )

            # تنفيذ فوري إذا مطلوب
            if start_immediately:
                self._scheduler.get_job(job_id).modify(next_run_time=datetime.now())

            return True

        except Exception as e:
            print(f"❌ خطأ في إضافة المهمة الدورية: {e}")
            return False

    def add_cron_job(
        self,
        func: Callable,
        job_id: str,
        description: str = "",
        year: str = None,
        month: str = None,
        day: str = None,
        week: str = None,
        day_of_week: str = None,
        hour: str = None,
        minute: str = None,
        second: str = "0",
        args: tuple = None,
        kwargs: dict = None
    ) -> bool:
        """
        إضافة مهمة بجدول cron

        Args:
            func: الدالة المراد تنفيذها
            job_id: معرف فريد للمهمة
            description: وصف المهمة
            cron fields: حقول cron (year, month, day, etc.)
            args/kwargs: معاملات الدالة

        Returns:
            True إذا تمت الإضافة بنجاح

        Examples:
            # كل يوم الساعة 9 صباحاً
            add_cron_job(func, "daily", hour="9", minute="0")

            # كل يوم أحد الساعة 10
            add_cron_job(func, "weekly", day_of_week="sun", hour="10")

            # أول كل شهر
            add_cron_job(func, "monthly", day="1", hour="0")
        """
        if not self._ensure_running():
            return False

        try:
            trigger = CronTrigger(
                year=year,
                month=month,
                day=day,
                week=week,
                day_of_week=day_of_week,
                hour=hour,
                minute=minute,
                second=second
            )

            self._scheduler.add_job(
                func,
                trigger=trigger,
                id=job_id,
                name=description or job_id,
                args=args or (),
                kwargs=kwargs or {},
                replace_existing=True
            )

            # حفظ معلومات المهمة
            self._job_stats[job_id] = ScheduledJob(
                job_id=job_id,
                job_type=JobType.CRON.value,
                description=description or job_id
            )

            return True

        except Exception as e:
            print(f"❌ خطأ في إضافة مهمة cron: {e}")
            return False

    def add_date_job(
        self,
        func: Callable,
        job_id: str,
        run_date: datetime,
        description: str = "",
        args: tuple = None,
        kwargs: dict = None
    ) -> bool:
        """
        إضافة مهمة لتنفيذ في تاريخ محدد

        Args:
            func: الدالة المراد تنفيذها
            job_id: معرف فريد للمهمة
            run_date: تاريخ ووقت التنفيذ
            description: وصف المهمة
            args/kwargs: معاملات الدالة

        Returns:
            True إذا تمت الإضافة بنجاح
        """
        if not self._ensure_running():
            return False

        try:
            trigger = DateTrigger(run_date=run_date)

            self._scheduler.add_job(
                func,
                trigger=trigger,
                id=job_id,
                name=description or job_id,
                args=args or (),
                kwargs=kwargs or {},
                replace_existing=True
            )

            # حفظ معلومات المهمة
            self._job_stats[job_id] = ScheduledJob(
                job_id=job_id,
                job_type=JobType.DATE.value,
                description=description or job_id
            )

            return True

        except Exception as e:
            print(f"❌ خطأ في إضافة مهمة بتاريخ: {e}")
            return False

    def remove_job(self, job_id: str) -> bool:
        """
        حذف مهمة مجدولة

        Args:
            job_id: معرف المهمة

        Returns:
            True إذا تم الحذف بنجاح
        """
        if not self._scheduler:
            return False

        try:
            self._scheduler.remove_job(job_id)
            if job_id in self._job_stats:
                del self._job_stats[job_id]
            return True
        except Exception:
            return False

    def pause_job(self, job_id: str) -> bool:
        """إيقاف مهمة مؤقتاً"""
        if not self._scheduler:
            return False
        try:
            self._scheduler.pause_job(job_id)
            if job_id in self._job_stats:
                self._job_stats[job_id].enabled = False
            return True
        except Exception:
            return False

    def resume_job(self, job_id: str) -> bool:
        """استئناف مهمة متوقفة"""
        if not self._scheduler:
            return False
        try:
            self._scheduler.resume_job(job_id)
            if job_id in self._job_stats:
                self._job_stats[job_id].enabled = True
            return True
        except Exception:
            return False

    def run_job_now(self, job_id: str) -> bool:
        """تنفيذ مهمة فوراً (خارج الجدول)"""
        if not self._scheduler:
            return False
        try:
            job = self._scheduler.get_job(job_id)
            if job:
                job.modify(next_run_time=datetime.now())
                return True
            return False
        except Exception:
            return False

    def get_jobs(self) -> List[ScheduledJob]:
        """الحصول على قائمة المهام المجدولة"""
        if not self._scheduler:
            return []

        jobs = []
        for job in self._scheduler.get_jobs():
            stats = self._job_stats.get(job.id, ScheduledJob(
                job_id=job.id,
                job_type="unknown",
                description=job.name
            ))

            stats.next_run = str(job.next_run_time) if job.next_run_time else None
            jobs.append(stats)

        return jobs

    def get_job(self, job_id: str) -> Optional[ScheduledJob]:
        """الحصول على معلومات مهمة محددة"""
        if not self._scheduler:
            return None

        job = self._scheduler.get_job(job_id)
        if job:
            stats = self._job_stats.get(job_id, ScheduledJob(
                job_id=job_id,
                job_type="unknown",
                description=job.name
            ))
            stats.next_run = str(job.next_run_time) if job.next_run_time else None
            return stats
        return None

    # ============================================================
    # Event Handlers
    # ============================================================

    def _on_job_executed(self, event):
        """معالج حدث تنفيذ مهمة"""
        job_id = event.job_id
        if job_id in self._job_stats:
            self._job_stats[job_id].run_count += 1
            self._job_stats[job_id].last_run = str(datetime.now())
        self._signals.job_executed.emit(job_id, event.retval)

    def _on_job_error(self, event):
        """معالج حدث خطأ في مهمة"""
        job_id = event.job_id
        if job_id in self._job_stats:
            self._job_stats[job_id].error_count += 1
        error_msg = str(event.exception) if event.exception else "Unknown error"
        self._signals.job_error.emit(job_id, error_msg)

    def _on_job_missed(self, event):
        """معالج حدث تفويت مهمة"""
        self._signals.job_missed.emit(event.job_id)

    def _on_job_added(self, event):
        """معالج حدث إضافة مهمة"""
        self._signals.job_added.emit(event.job_id)

    def _on_job_removed(self, event):
        """معالج حدث حذف مهمة"""
        self._signals.job_removed.emit(event.job_id)

    # ============================================================
    # Internal Methods
    # ============================================================

    def _ensure_running(self) -> bool:
        """التأكد من أن الجدولة تعمل"""
        if not self._running:
            return self.start()
        return True

    def _load_config(self):
        """تحميل إعدادات المهام"""
        if SCHEDULER_CONFIG_FILE.exists():
            try:
                with open(SCHEDULER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for job_data in data.get('jobs', []):
                        self._job_stats[job_data['job_id']] = ScheduledJob(**job_data)
            except Exception:
                pass

    def _save_config(self):
        """حفظ إعدادات المهام"""
        try:
            data = {
                'jobs': [asdict(job) for job in self._job_stats.values()]
            }
            with open(SCHEDULER_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


# ============================================================
# Singleton Access
# ============================================================

_scheduler_manager: Optional[SchedulerManager] = None


def get_scheduler() -> SchedulerManager:
    """
    الحصول على مدير الجدولة

    Returns:
        SchedulerManager singleton instance
    """
    global _scheduler_manager
    if _scheduler_manager is None:
        _scheduler_manager = SchedulerManager()
    return _scheduler_manager


def is_scheduler_available() -> bool:
    """
    هل مكتبة APScheduler متاحة؟

    Returns:
        True إذا كانت المكتبة مثبتة
    """
    return APSCHEDULER_AVAILABLE


# ============================================================
# Convenience Functions
# ============================================================

def schedule_interval(
    func: Callable,
    job_id: str,
    description: str = "",
    seconds: int = 0,
    minutes: int = 0,
    hours: int = 0,
    days: int = 0,
    args: tuple = None,
    kwargs: dict = None,
    start_immediately: bool = False
) -> bool:
    """
    جدولة مهمة دورية

    مثال:
        schedule_interval(sync_data, "sync", minutes=30)
    """
    return get_scheduler().add_interval_job(
        func=func,
        job_id=job_id,
        description=description,
        seconds=seconds,
        minutes=minutes,
        hours=hours,
        days=days,
        args=args,
        kwargs=kwargs,
        start_immediately=start_immediately
    )


def schedule_cron(
    func: Callable,
    job_id: str,
    description: str = "",
    hour: str = None,
    minute: str = "0",
    day_of_week: str = None,
    day: str = None,
    month: str = None,
    args: tuple = None,
    kwargs: dict = None
) -> bool:
    """
    جدولة مهمة بجدول cron

    مثال:
        # كل يوم الساعة 9 صباحاً
        schedule_cron(daily_report, "daily", hour="9")

        # كل أحد الساعة 10
        schedule_cron(weekly_backup, "weekly", day_of_week="sun", hour="10")
    """
    return get_scheduler().add_cron_job(
        func=func,
        job_id=job_id,
        description=description,
        hour=hour,
        minute=minute,
        day_of_week=day_of_week,
        day=day,
        month=month,
        args=args,
        kwargs=kwargs
    )


def schedule_once(
    func: Callable,
    job_id: str,
    run_date: datetime,
    description: str = "",
    args: tuple = None,
    kwargs: dict = None
) -> bool:
    """
    جدولة مهمة لمرة واحدة

    مثال:
        from datetime import datetime, timedelta
        schedule_once(send_reminder, "reminder", datetime.now() + timedelta(hours=1))
    """
    return get_scheduler().add_date_job(
        func=func,
        job_id=job_id,
        run_date=run_date,
        description=description,
        args=args,
        kwargs=kwargs
    )


def remove_job(job_id: str) -> bool:
    """حذف مهمة مجدولة"""
    return get_scheduler().remove_job(job_id)


def pause_job(job_id: str) -> bool:
    """إيقاف مهمة مؤقتاً"""
    return get_scheduler().pause_job(job_id)


def resume_job(job_id: str) -> bool:
    """استئناف مهمة متوقفة"""
    return get_scheduler().resume_job(job_id)


def run_job_now(job_id: str) -> bool:
    """تنفيذ مهمة فوراً"""
    return get_scheduler().run_job_now(job_id)


def get_scheduled_jobs() -> List[ScheduledJob]:
    """الحصول على قائمة المهام المجدولة"""
    return get_scheduler().get_jobs()


def start_scheduler() -> bool:
    """بدء نظام الجدولة"""
    return get_scheduler().start()


def stop_scheduler(wait: bool = True):
    """إيقاف نظام الجدولة"""
    get_scheduler().stop(wait=wait)
