# -*- coding: utf-8 -*-
"""
BI Export Scheduler
===================
Scheduled automatic export of BI data for Power BI.

This module provides:
- Daily scheduled exports
- Custom schedule configuration
- Export monitoring and notifications

Author: Mohamed
Version: 1.0.0
Date: February 2026
"""

from datetime import datetime, time, timedelta
from typing import Optional, Callable, List
from dataclasses import dataclass
from enum import Enum
import threading

from core.logging import app_logger


class ExportFrequency(Enum):
    """Export frequency options."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MANUAL = "manual"


@dataclass
class ScheduleConfig:
    """Configuration for scheduled exports."""
    enabled: bool = False
    frequency: ExportFrequency = ExportFrequency.DAILY
    time_of_day: time = time(6, 0)  # 6:00 AM
    day_of_week: int = 0  # Monday (0-6)
    export_format: str = "csv"  # "csv" or "excel"
    views_to_export: List[str] = None  # None = all views

    def __post_init__(self):
        if self.views_to_export is None:
            self.views_to_export = []


class ExportScheduler:
    """
    Manages scheduled export jobs for BI data.

    Uses threading.Timer for lightweight scheduling without
    external dependencies like APScheduler.
    """

    def __init__(self):
        """Initialize the scheduler."""
        self._config = ScheduleConfig()
        self._timer: Optional[threading.Timer] = None
        self._running = False
        self._lock = threading.Lock()
        self._last_export: Optional[datetime] = None
        self._on_export_complete: Optional[Callable] = None
        self._on_export_error: Optional[Callable] = None

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        with self._lock:
            return self._running

    @property
    def config(self) -> ScheduleConfig:
        """Get current schedule configuration."""
        return self._config

    @property
    def last_export(self) -> Optional[datetime]:
        """Get the time of last export."""
        return self._last_export

    def configure(
        self,
        enabled: bool = True,
        frequency: ExportFrequency = ExportFrequency.DAILY,
        time_of_day: time = time(6, 0),
        export_format: str = "csv",
        views: Optional[List[str]] = None
    ) -> None:
        """
        Configure the export schedule.

        Args:
            enabled: Enable/disable scheduled exports
            frequency: How often to export
            time_of_day: Time of day for daily exports
            export_format: "csv" or "excel"
            views: List of views to export (None for all)
        """
        self._config = ScheduleConfig(
            enabled=enabled,
            frequency=frequency,
            time_of_day=time_of_day,
            export_format=export_format,
            views_to_export=views or []
        )

        app_logger.info(f"Export scheduler configured: {frequency.value} at {time_of_day}")

        # Restart scheduler if running
        if self._running:
            self.stop()
            self.start()

    def set_callbacks(
        self,
        on_complete: Optional[Callable] = None,
        on_error: Optional[Callable] = None
    ) -> None:
        """Set callback functions for export events."""
        self._on_export_complete = on_complete
        self._on_export_error = on_error

    def start(self) -> bool:
        """Start the scheduler."""
        if not self._config.enabled:
            app_logger.info("Export scheduler is disabled")
            return False

        with self._lock:
            if self._running:
                return True
            self._running = True

        self._schedule_next_export()
        app_logger.info("Export scheduler started")
        return True

    def stop(self) -> None:
        """Stop the scheduler."""
        with self._lock:
            self._running = False
            if self._timer:
                self._timer.cancel()
                self._timer = None
        app_logger.info("Export scheduler stopped")

    def _schedule_next_export(self) -> None:
        """Schedule the next export based on configuration."""
        with self._lock:
            if not self._running:
                return

            # Calculate seconds until next export
            now = datetime.now()
            seconds_until_export = self._calculate_seconds_until_next(now)

            if seconds_until_export <= 0:
                seconds_until_export = 60  # Minimum 1 minute

            # Schedule timer
            self._timer = threading.Timer(seconds_until_export, self._execute_export)
            self._timer.daemon = True
            self._timer.start()

        next_time = datetime.fromtimestamp(now.timestamp() + seconds_until_export)
        app_logger.debug(f"Next export scheduled for: {next_time}")

    def _calculate_seconds_until_next(self, now: datetime) -> float:
        """Calculate seconds until next scheduled export."""
        if self._config.frequency == ExportFrequency.HOURLY:
            # Next hour
            next_run = now.replace(minute=0, second=0, microsecond=0)
            next_run = next_run + timedelta(hours=1)
            return (next_run - now).total_seconds()

        elif self._config.frequency == ExportFrequency.DAILY:
            # Today or tomorrow at scheduled time
            scheduled_time = self._config.time_of_day
            next_run = now.replace(
                hour=scheduled_time.hour,
                minute=scheduled_time.minute,
                second=0,
                microsecond=0
            )
            if next_run <= now:
                # Already passed today, schedule for tomorrow
                from datetime import timedelta
                next_run += timedelta(days=1)
            return (next_run - now).total_seconds()

        elif self._config.frequency == ExportFrequency.WEEKLY:
            # Next occurrence of scheduled day and time
            from datetime import timedelta
            scheduled_time = self._config.time_of_day
            days_ahead = self._config.day_of_week - now.weekday()
            if days_ahead < 0:  # Target day already happened this week
                days_ahead += 7
            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(
                hour=scheduled_time.hour,
                minute=scheduled_time.minute,
                second=0,
                microsecond=0
            )
            if next_run <= now:
                next_run += timedelta(weeks=1)
            return (next_run - now).total_seconds()

        else:
            # Manual - no automatic scheduling
            return 86400 * 365  # 1 year (effectively never)

    def _execute_export(self) -> None:
        """Execute the scheduled export."""
        with self._lock:
            if not self._running:
                return

        app_logger.info("Starting scheduled BI export")

        try:
            from .data_exporter import get_bi_exporter

            exporter = get_bi_exporter()

            if self._config.export_format == "excel":
                if self._config.views_to_export:
                    result = exporter.export_to_excel(self._config.views_to_export)
                else:
                    result = exporter.export_all_views_excel()
            else:
                if self._config.views_to_export:
                    results = [exporter.export_to_csv(v) for v in self._config.views_to_export]
                else:
                    results = exporter.export_all_views_csv()
                result = results[0] if results else None

            self._last_export = datetime.now()

            if result and result.success:
                app_logger.info(f"Scheduled export completed: {result.row_count} rows")
                if self._on_export_complete:
                    self._on_export_complete(result)
            else:
                error = result.error if result else "Unknown error"
                app_logger.error(f"Scheduled export failed: {error}")
                if self._on_export_error:
                    self._on_export_error(error)

        except Exception as e:
            app_logger.error(f"Scheduled export error: {e}")
            if self._on_export_error:
                self._on_export_error(str(e))

        finally:
            # Schedule next export
            self._schedule_next_export()

    def export_now(self) -> None:
        """Trigger an immediate export."""
        threading.Thread(target=self._execute_export, daemon=True).start()

    def get_status(self) -> dict:
        """Get scheduler status information."""
        with self._lock:
            running = self._running
        return {
            "enabled": self._config.enabled,
            "running": running,
            "frequency": self._config.frequency.value,
            "time_of_day": self._config.time_of_day.strftime("%H:%M"),
            "export_format": self._config.export_format,
            "last_export": self._last_export.isoformat() if self._last_export else None,
            "views_count": len(self._config.views_to_export) if self._config.views_to_export else "all"
        }


# =============================================================================
# Singleton Instance
# =============================================================================

_scheduler_instance: Optional[ExportScheduler] = None


def get_export_scheduler() -> ExportScheduler:
    """Get the singleton ExportScheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = ExportScheduler()
    return _scheduler_instance
