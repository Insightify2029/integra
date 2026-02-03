# -*- coding: utf-8 -*-
"""
Scheduler Module
================
APScheduler integration for scheduled tasks.

Components:
  - SchedulerManager: Central scheduler with PyQt5 integration
  - Job management utilities
"""

from .scheduler_manager import (
    SchedulerManager,
    get_scheduler,
    schedule_job,
    schedule_interval,
    schedule_cron,
    remove_job,
)

__all__ = [
    "SchedulerManager",
    "get_scheduler",
    "schedule_job",
    "schedule_interval",
    "schedule_cron",
    "remove_job",
]
