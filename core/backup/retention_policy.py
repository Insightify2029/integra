# -*- coding: utf-8 -*-
"""
Retention Policy
================
GFS (Grandfather-Father-Son) backup retention strategy.

Features:
  - Daily backups (Son) - keep last N days
  - Weekly backups (Father) - keep last N weeks
  - Monthly backups (Grandfather) - keep last N months
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RetentionPolicy:
    """
    Simple retention policy based on age.

    Attributes:
        max_age_days: Maximum age of backups to keep
        max_count: Maximum number of backups to keep (0 = unlimited)
    """
    max_age_days: int = 30
    max_count: int = 0

    def get_files_to_delete(
        self,
        files: List[Dict],
        current_time: datetime = None
    ) -> List[Dict]:
        """
        Determine which files should be deleted.

        Args:
            files: List of dicts with 'path' and 'timestamp' keys
            current_time: Current time (default: now)

        Returns:
            List of files to delete
        """
        if not files:
            return []

        current_time = current_time or datetime.now()
        cutoff = current_time - timedelta(days=self.max_age_days)

        # Sort by timestamp (newest first)
        sorted_files = sorted(files, key=lambda f: f['timestamp'], reverse=True)

        to_delete = []

        for i, file_info in enumerate(sorted_files):
            # Keep if within max_count (if set)
            if self.max_count > 0 and i < self.max_count:
                continue

            # Delete if older than max_age
            if file_info['timestamp'] < cutoff:
                to_delete.append(file_info)

        return to_delete


@dataclass
class GFSPolicy:
    """
    Grandfather-Father-Son retention policy.

    Keeps:
      - Daily backups for `daily_retention` days
      - Weekly backups for `weekly_retention` weeks
      - Monthly backups for `monthly_retention` months

    Attributes:
        daily_retention: Days to keep daily backups
        weekly_retention: Weeks to keep weekly backups
        monthly_retention: Months to keep monthly backups
        weekly_day: Day of week for weekly (0=Monday, 6=Sunday)
        monthly_day: Day of month for monthly backup
    """
    daily_retention: int = 7
    weekly_retention: int = 4
    monthly_retention: int = 12
    weekly_day: int = 6  # Sunday
    monthly_day: int = 1  # First of month

    def categorize_backup(
        self,
        timestamp: datetime
    ) -> str:
        """
        Categorize a backup as daily, weekly, or monthly.

        Args:
            timestamp: Backup timestamp

        Returns:
            Category: "monthly", "weekly", or "daily"
        """
        # Check monthly first (highest priority)
        if timestamp.day == self.monthly_day:
            return "monthly"

        # Check weekly
        if timestamp.weekday() == self.weekly_day:
            return "weekly"

        return "daily"

    def get_files_to_delete(
        self,
        files: List[Dict],
        current_time: datetime = None
    ) -> List[Dict]:
        """
        Determine which files should be deleted using GFS strategy.

        Args:
            files: List of dicts with 'path' and 'timestamp' keys
            current_time: Current time (default: now)

        Returns:
            List of files to delete
        """
        if not files:
            return []

        current_time = current_time or datetime.now()

        # Categorize all files
        daily = []
        weekly = []
        monthly = []

        for file_info in files:
            category = self.categorize_backup(file_info['timestamp'])
            if category == "monthly":
                monthly.append(file_info)
            elif category == "weekly":
                weekly.append(file_info)
            else:
                daily.append(file_info)

        to_delete = []

        # Apply retention to each category
        daily_cutoff = current_time - timedelta(days=self.daily_retention)
        weekly_cutoff = current_time - timedelta(weeks=self.weekly_retention)
        monthly_cutoff = current_time - timedelta(days=self.monthly_retention * 30)

        for file_info in daily:
            if file_info['timestamp'] < daily_cutoff:
                to_delete.append(file_info)

        for file_info in weekly:
            if file_info['timestamp'] < weekly_cutoff:
                to_delete.append(file_info)

        for file_info in monthly:
            if file_info['timestamp'] < monthly_cutoff:
                to_delete.append(file_info)

        return to_delete

    def get_retention_summary(self) -> Dict:
        """Get a summary of retention settings."""
        return {
            "daily": f"{self.daily_retention} days",
            "weekly": f"{self.weekly_retention} weeks",
            "monthly": f"{self.monthly_retention} months",
            "weekly_day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][self.weekly_day],
            "monthly_day": self.monthly_day
        }
