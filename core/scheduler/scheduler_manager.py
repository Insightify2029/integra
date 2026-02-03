# -*- coding: utf-8 -*-
"""
Scheduler Manager
=================
APScheduler integration with PyQt5 event loop.

Features:
  - Background job scheduling
  - Cron-style scheduling
  - Interval-based scheduling
  - Job persistence (optional)
  - Misfire handling

Usage:
    from core.scheduler import get_scheduler

    scheduler = get_scheduler()
    scheduler.start()

    # Schedule a function to run every hour
    scheduler.add_interval_job(
        my_function,
        hours=1,
        id="hourly_task"
    )

    # Schedule for specific time (cron)
    scheduler.add_cron_job(
        daily_backup,
        hour=2,
        minute=0,
        id="daily_backup"
    )
"""

from typing import Callable, Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass

from PyQt5.QtCore import QObject, pyqtSignal

# Try to import APScheduler
try:
    from apscheduler.schedulers.qt import QtScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.date import DateTrigger
    from apscheduler.events import (
        EVENT_JOB_EXECUTED,
        EVENT_JOB_ERROR,
        EVENT_JOB_MISSED,
    )
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False


@dataclass
class JobInfo:
    """Information about a scheduled job."""
    id: str
    name: str
    trigger_type: str
    next_run: Optional[datetime]
    last_run: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0


class SchedulerManager(QObject):
    """
    Scheduler manager with PyQt5 integration.

    Signals:
        job_executed(job_id, result): Job completed successfully
        job_error(job_id, error): Job failed
        job_missed(job_id): Job was missed (misfire)
    """

    # Signals
    job_executed = pyqtSignal(str, object)
    job_error = pyqtSignal(str, str)
    job_missed = pyqtSignal(str)

    def __init__(self):
        """Initialize scheduler manager."""
        super().__init__()

        self._scheduler = None
        self._running = False
        self._job_stats: Dict[str, JobInfo] = {}

        if APSCHEDULER_AVAILABLE:
            self._scheduler = QtScheduler()
            self._setup_listeners()

    def _setup_listeners(self):
        """Set up event listeners."""
        if not self._scheduler:
            return

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

    def start(self):
        """Start the scheduler."""
        if not APSCHEDULER_AVAILABLE:
            print("APScheduler not available - scheduler disabled")
            return

        if not self._running:
            self._scheduler.start()
            self._running = True

    def stop(self, wait: bool = True):
        """
        Stop the scheduler.

        Args:
            wait: Wait for running jobs to complete
        """
        if self._scheduler and self._running:
            self._scheduler.shutdown(wait=wait)
            self._running = False

    def pause(self):
        """Pause the scheduler (jobs won't run)."""
        if self._scheduler:
            self._scheduler.pause()

    def resume(self):
        """Resume the scheduler."""
        if self._scheduler:
            self._scheduler.resume()

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._running

    def add_interval_job(
        self,
        func: Callable,
        id: str = None,
        name: str = None,
        seconds: int = 0,
        minutes: int = 0,
        hours: int = 0,
        days: int = 0,
        start_date: datetime = None,
        args: tuple = None,
        kwargs: dict = None,
        replace_existing: bool = True
    ) -> Optional[str]:
        """
        Schedule a job to run at fixed intervals.

        Args:
            func: Function to call
            id: Unique job ID (generated if not provided)
            name: Human-readable name
            seconds, minutes, hours, days: Interval components
            start_date: When to start (default: now)
            args: Positional arguments for func
            kwargs: Keyword arguments for func
            replace_existing: Replace if job ID exists

        Returns:
            Job ID
        """
        if not APSCHEDULER_AVAILABLE:
            return None

        job = self._scheduler.add_job(
            func,
            IntervalTrigger(
                seconds=seconds,
                minutes=minutes,
                hours=hours,
                days=days,
                start_date=start_date
            ),
            id=id,
            name=name or (id or func.__name__),
            args=args or (),
            kwargs=kwargs or {},
            replace_existing=replace_existing,
            misfire_grace_time=60  # 1 minute grace period
        )

        self._job_stats[job.id] = JobInfo(
            id=job.id,
            name=job.name,
            trigger_type="interval",
            next_run=job.next_run_time
        )

        return job.id

    def add_cron_job(
        self,
        func: Callable,
        id: str = None,
        name: str = None,
        year: str = None,
        month: str = None,
        day: str = None,
        week: str = None,
        day_of_week: str = None,
        hour: str = None,
        minute: str = None,
        second: str = "0",
        args: tuple = None,
        kwargs: dict = None,
        replace_existing: bool = True
    ) -> Optional[str]:
        """
        Schedule a job using cron-style timing.

        Args:
            func: Function to call
            id: Unique job ID
            name: Human-readable name
            year, month, day, etc.: Cron fields (use "*" for any)
            args: Positional arguments
            kwargs: Keyword arguments
            replace_existing: Replace if exists

        Returns:
            Job ID

        Example:
            # Run at 2:30 AM every day
            add_cron_job(backup, hour=2, minute=30)

            # Run every Monday at 9 AM
            add_cron_job(report, day_of_week="mon", hour=9)
        """
        if not APSCHEDULER_AVAILABLE:
            return None

        job = self._scheduler.add_job(
            func,
            CronTrigger(
                year=year,
                month=month,
                day=day,
                week=week,
                day_of_week=day_of_week,
                hour=hour,
                minute=minute,
                second=second
            ),
            id=id,
            name=name or (id or func.__name__),
            args=args or (),
            kwargs=kwargs or {},
            replace_existing=replace_existing,
            misfire_grace_time=300  # 5 minute grace period for cron
        )

        self._job_stats[job.id] = JobInfo(
            id=job.id,
            name=job.name,
            trigger_type="cron",
            next_run=job.next_run_time
        )

        return job.id

    def add_date_job(
        self,
        func: Callable,
        run_date: datetime,
        id: str = None,
        name: str = None,
        args: tuple = None,
        kwargs: dict = None
    ) -> Optional[str]:
        """
        Schedule a job to run once at a specific time.

        Args:
            func: Function to call
            run_date: When to run
            id: Unique job ID
            name: Human-readable name
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Job ID
        """
        if not APSCHEDULER_AVAILABLE:
            return None

        job = self._scheduler.add_job(
            func,
            DateTrigger(run_date=run_date),
            id=id,
            name=name or (id or func.__name__),
            args=args or (),
            kwargs=kwargs or {}
        )

        self._job_stats[job.id] = JobInfo(
            id=job.id,
            name=job.name,
            trigger_type="date",
            next_run=job.next_run_time
        )

        return job.id

    def remove_job(self, job_id: str) -> bool:
        """
        Remove a scheduled job.

        Args:
            job_id: ID of job to remove

        Returns:
            True if removed
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
        """Pause a specific job."""
        if not self._scheduler:
            return False

        try:
            self._scheduler.pause_job(job_id)
            return True
        except Exception:
            return False

    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job."""
        if not self._scheduler:
            return False

        try:
            self._scheduler.resume_job(job_id)
            return True
        except Exception:
            return False

    def get_job(self, job_id: str) -> Optional[JobInfo]:
        """Get job information."""
        return self._job_stats.get(job_id)

    def get_all_jobs(self) -> List[JobInfo]:
        """Get all scheduled jobs."""
        # Update next run times
        if self._scheduler:
            for job in self._scheduler.get_jobs():
                if job.id in self._job_stats:
                    self._job_stats[job.id].next_run = job.next_run_time

        return list(self._job_stats.values())

    def run_job_now(self, job_id: str) -> bool:
        """
        Run a job immediately (out of schedule).

        Args:
            job_id: Job to run

        Returns:
            True if triggered
        """
        if not self._scheduler:
            return False

        try:
            job = self._scheduler.get_job(job_id)
            if job:
                job.modify(next_run_time=datetime.now())
                return True
        except Exception:
            pass

        return False

    # Event handlers

    def _on_job_executed(self, event):
        """Handle job execution."""
        job_id = event.job_id

        if job_id in self._job_stats:
            self._job_stats[job_id].last_run = datetime.now()
            self._job_stats[job_id].run_count += 1

        self.job_executed.emit(job_id, event.retval)

    def _on_job_error(self, event):
        """Handle job error."""
        job_id = event.job_id
        error = str(event.exception)

        if job_id in self._job_stats:
            self._job_stats[job_id].error_count += 1

        self.job_error.emit(job_id, error)

    def _on_job_missed(self, event):
        """Handle missed job."""
        self.job_missed.emit(event.job_id)


# Singleton instance
_scheduler: Optional[SchedulerManager] = None


def get_scheduler() -> SchedulerManager:
    """Get the global SchedulerManager instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = SchedulerManager()
    return _scheduler


# Convenience functions

def schedule_job(
    func: Callable,
    trigger: str = "interval",
    **kwargs
) -> Optional[str]:
    """
    Schedule a job with specified trigger.

    Args:
        func: Function to call
        trigger: "interval", "cron", or "date"
        **kwargs: Trigger-specific arguments

    Returns:
        Job ID
    """
    scheduler = get_scheduler()

    if trigger == "interval":
        return scheduler.add_interval_job(func, **kwargs)
    elif trigger == "cron":
        return scheduler.add_cron_job(func, **kwargs)
    elif trigger == "date":
        return scheduler.add_date_job(func, **kwargs)

    return None


def schedule_interval(
    func: Callable,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0,
    **kwargs
) -> Optional[str]:
    """Schedule a function to run at intervals."""
    return get_scheduler().add_interval_job(
        func,
        hours=hours,
        minutes=minutes,
        seconds=seconds,
        **kwargs
    )


def schedule_cron(
    func: Callable,
    hour: str = None,
    minute: str = None,
    **kwargs
) -> Optional[str]:
    """Schedule a function using cron timing."""
    return get_scheduler().add_cron_job(
        func,
        hour=hour,
        minute=minute,
        **kwargs
    )


def remove_job(job_id: str) -> bool:
    """Remove a scheduled job."""
    return get_scheduler().remove_job(job_id)
