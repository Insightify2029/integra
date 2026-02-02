# -*- coding: utf-8 -*-
"""Backup Manager v3 - إدارة ملفات النسخ الاحتياطي"""

import os
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class BackupInfo:
    filepath: Path
    filename: str
    timestamp: datetime
    size_bytes: int
    size_kb: float
    
    @property
    def age_days(self) -> int:
        return (datetime.now() - self.timestamp).days
    
    @property
    def formatted_time(self) -> str:
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    
    @property
    def formatted_size(self) -> str:
        if self.size_kb < 1024:
            return f"{self.size_kb:.1f} KB"
        return f"{self.size_kb/1024:.2f} MB"


class BackupManager:
    BACKUP_DIR_NAME = "backups/database"
    BACKUP_PREFIX = "backup_"
    BACKUP_EXT = ".sql"
    DATE_FORMAT = "%Y-%m-%d_%H-%M-%S"
    
    def __init__(self, project_root: Path = None):
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent
        self.project_root = project_root
        self.backup_dir = project_root / self.BACKUP_DIR_NAME
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._pg_dump_path: Optional[str] = None
        self._psql_path: Optional[str] = None
    
    def generate_backup_path(self) -> Path:
        timestamp = datetime.now().strftime(self.DATE_FORMAT)
        filename = f"{self.BACKUP_PREFIX}{timestamp}{self.BACKUP_EXT}"
        return self.backup_dir / filename
    
    def list_backups(self) -> List[BackupInfo]:
        backups = []
        pattern = f"{self.BACKUP_PREFIX}*{self.BACKUP_EXT}"
        for filepath in self.backup_dir.glob(pattern):
            try:
                filename = filepath.stem
                date_str = filename.replace(self.BACKUP_PREFIX, "")
                # Handle migrated files
                if "_migrated" in date_str:
                    date_str = date_str.replace("_migrated", "")
                timestamp = datetime.strptime(date_str, self.DATE_FORMAT)
                size_bytes = filepath.stat().st_size
                backups.append(BackupInfo(
                    filepath=filepath, filename=filepath.name,
                    timestamp=timestamp, size_bytes=size_bytes,
                    size_kb=size_bytes / 1024
                ))
            except (ValueError, OSError):
                continue
        backups.sort(key=lambda x: x.timestamp, reverse=True)
        return backups
    
    def get_latest_backup(self) -> Optional[BackupInfo]:
        backups = self.list_backups()
        return backups[0] if backups else None
    
    def get_backup_by_filename(self, filename: str) -> Optional[BackupInfo]:
        for backup in self.list_backups():
            if backup.filename == filename:
                return backup
        return None
    
    def calculate_file_hash(self, filepath: Path) -> str:
        if not filepath.exists():
            return ""
        hasher = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def cleanup_old_backups(self, retention_days: int = 30) -> Tuple[int, int]:
        backups = self.list_backups()
        now = datetime.now()
        deleted = 0
        kept = 0
        daily_backups = {}
        for backup in backups:
            date_key = backup.timestamp.date()
            if date_key not in daily_backups:
                daily_backups[date_key] = []
            daily_backups[date_key].append(backup)
        
        for date_key, day_backups in daily_backups.items():
            age_days = (now.date() - date_key).days
            if age_days <= 7:
                kept += len(day_backups)
            elif age_days <= retention_days:
                kept += 1
                for backup in day_backups[1:]:
                    try:
                        backup.filepath.unlink()
                        deleted += 1
                    except OSError:
                        pass
            else:
                for backup in day_backups:
                    try:
                        backup.filepath.unlink()
                        deleted += 1
                    except OSError:
                        pass
        return deleted, kept
    
    def find_pg_tool(self, tool_name: str) -> str:
        if tool_name == "pg_dump" and self._pg_dump_path:
            return self._pg_dump_path
        if tool_name == "psql" and self._psql_path:
            return self._psql_path
        
        exe_name = f"{tool_name}.exe"
        for version in ["17", "16", "15", "14"]:
            path = rf"C:\Program Files\PostgreSQL\{version}\bin\{exe_name}"
            if os.path.exists(path):
                if tool_name == "pg_dump":
                    self._pg_dump_path = path
                else:
                    self._psql_path = path
                return path
        
        try:
            result = subprocess.run(["where", tool_name], capture_output=True,
                                    text=True, timeout=5, creationflags=0x08000000)
            if result.returncode == 0:
                path = result.stdout.strip().split("\n")[0]
                if tool_name == "pg_dump":
                    self._pg_dump_path = path
                else:
                    self._psql_path = path
                return path
        except Exception:
            pass
        return ""
