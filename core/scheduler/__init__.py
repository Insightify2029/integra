# core/scheduler/__init__.py
"""
INTEGRA - نظام الجدولة (APScheduler)
=====================================

نظام جدولة متكامل مع PyQt5 لتشغيل المهام بشكل دوري أو في أوقات محددة.

الاستخدام البسيط:
    from core.scheduler import schedule_interval, schedule_cron

    # مهمة كل 30 دقيقة
    schedule_interval(sync_data, "sync", minutes=30)

    # مهمة يومية الساعة 9
    schedule_cron(daily_report, "daily", hour="9")

الاستخدام المتقدم:
    from core.scheduler import get_scheduler

    scheduler = get_scheduler()
    scheduler.start()

    # إضافة مهام
    scheduler.add_interval_job(func, "job_id", minutes=5)
    scheduler.add_cron_job(func, "daily", hour="9", minute="0")

    # التحكم
    scheduler.pause_job("job_id")
    scheduler.resume_job("job_id")
    scheduler.run_job_now("job_id")
    scheduler.remove_job("job_id")

    # الحصول على المهام
    jobs = scheduler.get_jobs()

    # إيقاف
    scheduler.stop()

التكامل مع UI:
    scheduler = get_scheduler()
    scheduler.signals.job_executed.connect(on_job_done)
    scheduler.signals.job_error.connect(on_job_error)
"""

from .scheduler_manager import (
    # Manager
    SchedulerManager,
    get_scheduler,
    is_scheduler_available,

    # Convenience functions
    schedule_interval,
    schedule_cron,
    schedule_once,
    remove_job,
    pause_job,
    resume_job,
    run_job_now,
    get_scheduled_jobs,
    start_scheduler,
    stop_scheduler,

    # Data classes
    ScheduledJob,
    JobType,
    SchedulerSignals,

    # Constants
    SCHEDULER_CONFIG_FILE,
    DEFAULT_MISFIRE_GRACE_TIME,
)

__all__ = [
    # Manager
    'SchedulerManager',
    'get_scheduler',
    'is_scheduler_available',

    # Convenience functions
    'schedule_interval',
    'schedule_cron',
    'schedule_once',
    'remove_job',
    'pause_job',
    'resume_job',
    'run_job_now',
    'get_scheduled_jobs',
    'start_scheduler',
    'stop_scheduler',

    # Data classes
    'ScheduledJob',
    'JobType',
    'SchedulerSignals',

    # Constants
    'SCHEDULER_CONFIG_FILE',
    'DEFAULT_MISFIRE_GRACE_TIME',
]
