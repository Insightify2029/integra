# -*- coding: utf-8 -*-
"""
Backup Manager
==============
Advanced database backup with compression and verification.

Features:
  - pg_dump compressed backups (-Fc format)
  - Checksum verification
  - GFS retention policy
  - Scheduled backups integration
"""

from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import subprocess
import hashlib
import os
import json

from .retention_policy import GFSPolicy, RetentionPolicy


class BackupType(Enum):
    """Backup types."""
    FULL = "full"
    SCHEMA_ONLY = "schema"
    DATA_ONLY = "data"


@dataclass
class BackupInfo:
    """
    Information about a backup file.

    Attributes:
        path: Full path to backup file
        timestamp: When backup was created
        size_bytes: File size
        backup_type: Type of backup
        checksum: SHA256 checksum
        database: Database name
        compressed: Whether backup is compressed
    """
    path: Path
    timestamp: datetime
    size_bytes: int
    backup_type: BackupType = BackupType.FULL
    checksum: Optional[str] = None
    database: str = "integra"
    compressed: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def size_mb(self) -> float:
        """Size in megabytes."""
        return self.size_bytes / (1024 * 1024)

    @property
    def filename(self) -> str:
        """Just the filename."""
        return self.path.name

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "path": str(self.path),
            "timestamp": self.timestamp.isoformat(),
            "size_bytes": self.size_bytes,
            "backup_type": self.backup_type.value,
            "checksum": self.checksum,
            "database": self.database,
            "compressed": self.compressed,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "BackupInfo":
        """Create from dictionary."""
        return cls(
            path=Path(data["path"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            size_bytes=data["size_bytes"],
            backup_type=BackupType(data.get("backup_type", "full")),
            checksum=data.get("checksum"),
            database=data.get("database", "integra"),
            compressed=data.get("compressed", True),
            metadata=data.get("metadata", {})
        )


class BackupManager:
    """
    Database backup manager.

    Usage:
        manager = BackupManager()

        # Create backup
        info = manager.create_backup()

        # List backups
        backups = manager.list_backups()

        # Restore backup
        manager.restore_backup(backup_path)

        # Cleanup old backups
        manager.cleanup()
    """

    DEFAULT_BACKUP_DIR = Path(__file__).parent.parent.parent / "backups" / "database"
    METADATA_FILE = "backup_metadata.json"

    def __init__(
        self,
        backup_dir: Path = None,
        database: str = "integra",
        user: str = "postgres",
        retention_policy: GFSPolicy = None
    ):
        """
        Initialize backup manager.

        Args:
            backup_dir: Directory for backups
            database: Database name
            user: Database user
            retention_policy: Retention policy (default: GFS)
        """
        self.backup_dir = backup_dir or self.DEFAULT_BACKUP_DIR
        self.database = database
        self.user = user
        self.retention_policy = retention_policy or GFSPolicy()

        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(
        self,
        backup_type: BackupType = BackupType.FULL,
        compress: bool = True,
        comment: str = None
    ) -> Tuple[bool, Optional[BackupInfo], str]:
        """
        Create a database backup.

        Args:
            backup_type: Type of backup
            compress: Use compression (pg_dump -Fc)
            comment: Optional comment for metadata

        Returns:
            (success, backup_info, message)
        """
        timestamp = datetime.now()
        filename = f"backup_{timestamp.strftime('%Y-%m-%d_%H-%M-%S')}"

        if compress:
            filename += ".dump"  # Custom format (compressed)
            format_flag = "-Fc"
        else:
            filename += ".sql"
            format_flag = "-Fp"

        backup_path = self.backup_dir / filename

        # Find pg_dump
        pg_dump = self._find_pg_tool("pg_dump")
        if not pg_dump:
            return False, None, "pg_dump not found"

        # Build command
        cmd = [pg_dump, "-U", self.user, "-d", self.database, format_flag]

        if backup_type == BackupType.SCHEMA_ONLY:
            cmd.append("--schema-only")
        elif backup_type == BackupType.DATA_ONLY:
            cmd.append("--data-only")

        cmd.extend(["-f", str(backup_path)])

        # Set password from environment
        env = os.environ.copy()
        password = self._get_db_password()
        if password:
            env["PGPASSWORD"] = password

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes
                env=env
            )

            if result.returncode != 0:
                return False, None, f"pg_dump failed: {result.stderr[:200]}"

            # Get file info
            size = backup_path.stat().st_size
            checksum = self._calculate_checksum(backup_path)

            info = BackupInfo(
                path=backup_path,
                timestamp=timestamp,
                size_bytes=size,
                backup_type=backup_type,
                checksum=checksum,
                database=self.database,
                compressed=compress,
                metadata={"comment": comment} if comment else {}
            )

            # Save metadata
            self._save_metadata(info)

            return True, info, f"Backup created: {filename} ({info.size_mb:.2f} MB)"

        except subprocess.TimeoutExpired:
            return False, None, "Backup timed out (5 minutes)"
        except Exception as e:
            return False, None, f"Backup error: {e}"

    def restore_backup(
        self,
        backup_path: Path,
        target_database: str = None
    ) -> Tuple[bool, str]:
        """
        Restore a database from backup.

        Args:
            backup_path: Path to backup file
            target_database: Target database (default: same as backup)

        Returns:
            (success, message)
        """
        backup_path = Path(backup_path)
        if not backup_path.exists():
            return False, f"Backup file not found: {backup_path}"

        target_database = target_database or self.database

        # Determine if compressed
        is_compressed = backup_path.suffix == ".dump"

        if is_compressed:
            # Use pg_restore for custom format
            tool = self._find_pg_tool("pg_restore")
            if not tool:
                return False, "pg_restore not found"

            cmd = [
                tool, "-U", self.user,
                "-d", target_database,
                "--clean", "--if-exists",
                str(backup_path)
            ]
        else:
            # Use psql for SQL format
            tool = self._find_pg_tool("psql")
            if not tool:
                return False, "psql not found"

            cmd = [
                tool, "-U", self.user,
                "-d", target_database,
                "-f", str(backup_path)
            ]

        env = os.environ.copy()
        password = self._get_db_password()
        if password:
            env["PGPASSWORD"] = password

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes
                env=env
            )

            # pg_restore may return warnings but still succeed
            if result.returncode != 0 and "error" in result.stderr.lower():
                return False, f"Restore failed: {result.stderr[:200]}"

            return True, "Database restored successfully"

        except subprocess.TimeoutExpired:
            return False, "Restore timed out (10 minutes)"
        except Exception as e:
            return False, f"Restore error: {e}"

    def verify_backup(self, backup_path: Path) -> Tuple[bool, str]:
        """
        Verify a backup file integrity.

        Args:
            backup_path: Path to backup file

        Returns:
            (is_valid, message)
        """
        backup_path = Path(backup_path)
        if not backup_path.exists():
            return False, "Backup file not found"

        # Check file size
        if backup_path.stat().st_size == 0:
            return False, "Backup file is empty"

        # Load stored checksum
        metadata = self._load_metadata()
        stored_info = metadata.get(str(backup_path))

        if stored_info and stored_info.get("checksum"):
            current_checksum = self._calculate_checksum(backup_path)
            if current_checksum != stored_info["checksum"]:
                return False, "Checksum mismatch - file may be corrupted"

        # For compressed backups, try to list contents
        if backup_path.suffix == ".dump":
            pg_restore = self._find_pg_tool("pg_restore")
            if pg_restore:
                try:
                    result = subprocess.run(
                        [pg_restore, "-l", str(backup_path)],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if result.returncode != 0:
                        return False, "Backup file appears corrupted"
                except Exception:
                    pass

        return True, "Backup file is valid"

    def list_backups(self) -> List[BackupInfo]:
        """
        List all available backups.

        Returns:
            List of BackupInfo, sorted by timestamp (newest first)
        """
        backups = []
        metadata = self._load_metadata()

        for path in self.backup_dir.glob("backup_*"):
            if path.is_file() and path.suffix in (".dump", ".sql"):
                stored = metadata.get(str(path))

                if stored:
                    info = BackupInfo.from_dict(stored)
                else:
                    # Parse timestamp from filename
                    try:
                        ts_str = path.stem.replace("backup_", "")
                        timestamp = datetime.strptime(ts_str, "%Y-%m-%d_%H-%M-%S")
                    except ValueError:
                        timestamp = datetime.fromtimestamp(path.stat().st_mtime)

                    info = BackupInfo(
                        path=path,
                        timestamp=timestamp,
                        size_bytes=path.stat().st_size,
                        compressed=path.suffix == ".dump"
                    )

                backups.append(info)

        return sorted(backups, key=lambda b: b.timestamp, reverse=True)

    def cleanup(self, dry_run: bool = False) -> Tuple[int, List[str]]:
        """
        Remove old backups according to retention policy.

        Args:
            dry_run: If True, only report what would be deleted

        Returns:
            (deleted_count, list of deleted files)
        """
        backups = self.list_backups()

        files = [
            {"path": b.path, "timestamp": b.timestamp}
            for b in backups
        ]

        to_delete = self.retention_policy.get_files_to_delete(files)
        deleted = []

        for file_info in to_delete:
            path = file_info["path"]
            if not dry_run:
                try:
                    path.unlink()
                    deleted.append(str(path))
                except Exception:
                    pass
            else:
                deleted.append(str(path))

        return len(deleted), deleted

    def get_latest_backup(self) -> Optional[BackupInfo]:
        """Get the most recent backup."""
        backups = self.list_backups()
        return backups[0] if backups else None

    def get_backup_stats(self) -> Dict:
        """Get backup statistics."""
        backups = self.list_backups()

        if not backups:
            return {"count": 0, "total_size_mb": 0}

        total_size = sum(b.size_bytes for b in backups)
        oldest = min(b.timestamp for b in backups)
        newest = max(b.timestamp for b in backups)

        return {
            "count": len(backups),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "oldest": oldest.isoformat(),
            "newest": newest.isoformat(),
            "retention": self.retention_policy.get_retention_summary()
        }

    def _calculate_checksum(self, path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _save_metadata(self, info: BackupInfo):
        """Save backup metadata."""
        metadata = self._load_metadata()
        metadata[str(info.path)] = info.to_dict()

        metadata_path = self.backup_dir / self.METADATA_FILE
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    def _load_metadata(self) -> Dict:
        """Load backup metadata."""
        metadata_path = self.backup_dir / self.METADATA_FILE
        if not metadata_path.exists():
            return {}

        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _find_pg_tool(self, tool_name: str) -> Optional[str]:
        """Find PostgreSQL tool path."""
        if tool_name not in ("pg_dump", "pg_restore", "psql"):
            return None

        exe_name = f"{tool_name}.exe" if os.name == 'nt' else tool_name

        # Search known paths (Windows)
        if os.name == 'nt':
            for version in ["17", "16", "15", "14"]:
                path = rf"C:\Program Files\PostgreSQL\{version}\bin\{exe_name}"
                if os.path.exists(path):
                    return path

        # Try PATH
        try:
            result = subprocess.run(
                ["which", tool_name] if os.name != 'nt' else ["where", tool_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip().split("\n")[0]
        except Exception:
            pass

        return None

    def _get_db_password(self) -> Optional[str]:
        """Get database password from .env file."""
        env_file = Path(__file__).parent.parent.parent / ".env"
        if env_file.exists():
            try:
                with open(env_file, "r") as f:
                    for line in f:
                        if line.startswith("DB_PASSWORD="):
                            return line.split("=", 1)[1].strip()
            except Exception:
                pass
        return None


# Singleton instance
_backup_manager: Optional[BackupManager] = None


def get_backup_manager() -> BackupManager:
    """Get the global BackupManager instance."""
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupManager()
    return _backup_manager
