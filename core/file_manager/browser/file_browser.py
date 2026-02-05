"""
File Browser
============
Advanced file browser with favorites, recent files, and tag support.
"""

import os
import shutil
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

from core.logging import app_logger


@dataclass
class FileInfo:
    """Information about a file or directory."""
    name: str
    path: str
    is_dir: bool
    size: int
    modified: datetime
    extension: str
    tags: List[str] = field(default_factory=list)

    @property
    def size_formatted(self) -> str:
        """Human-readable file size."""
        if self.is_dir:
            return ""
        return _format_size(self.size)

    @property
    def icon(self) -> str:
        """File type icon."""
        if self.is_dir:
            return "folder"
        ext_icons = {
            '.pdf': 'pdf', '.doc': 'word', '.docx': 'word',
            '.xls': 'excel', '.xlsx': 'excel', '.csv': 'excel',
            '.png': 'image', '.jpg': 'image', '.jpeg': 'image',
            '.gif': 'image', '.bmp': 'image', '.webp': 'image',
            '.txt': 'text', '.md': 'text', '.json': 'text',
            '.py': 'code', '.js': 'code', '.html': 'code',
            '.zip': 'archive', '.rar': 'archive', '.7z': 'archive',
            '.mp3': 'audio', '.wav': 'audio', '.mp4': 'video',
        }
        return ext_icons.get(self.extension, 'file')


class FileBrowser:
    """Advanced file browser."""

    def __init__(self):
        self.current_path = Path.home()
        self.favorites: List[str] = []
        self.recent_files: List[str] = []
        self.file_tags: Dict[str, List[str]] = {}
        self._max_recent = 50

    def list_directory(self, path: str = None) -> List[FileInfo]:
        """
        List contents of a directory.

        Args:
            path: Directory path (uses current_path if None)

        Returns:
            Sorted list of FileInfo (directories first, then files)
        """
        target = Path(path) if path else self.current_path

        items = []
        try:
            for item in target.iterdir():
                try:
                    stat = item.stat()
                    items.append(FileInfo(
                        name=item.name,
                        path=str(item),
                        is_dir=item.is_dir(),
                        size=stat.st_size if item.is_file() else 0,
                        modified=datetime.fromtimestamp(stat.st_mtime),
                        extension=item.suffix.lower() if item.is_file() else "",
                        tags=self.file_tags.get(str(item), []),
                    ))
                except (PermissionError, OSError):
                    continue
        except PermissionError:
            app_logger.warning(f"Permission denied: {target}")

        # Sort: directories first, then alphabetically
        items.sort(key=lambda x: (not x.is_dir, x.name.lower()))
        return items

    def navigate(self, path: str) -> bool:
        """
        Navigate to a directory.

        Args:
            path: Target directory

        Returns:
            True if navigation successful
        """
        new_path = Path(path)
        if new_path.is_dir():
            self.current_path = new_path
            return True
        return False

    def go_up(self) -> bool:
        """Navigate to parent directory."""
        parent = self.current_path.parent
        if parent != self.current_path:
            self.current_path = parent
            return True
        return False

    def go_home(self):
        """Navigate to home directory."""
        self.current_path = Path.home()

    # ═══════════════════════════════════════════════════════
    # File Operations
    # ═══════════════════════════════════════════════════════

    def copy(self, source: str, dest: str) -> bool:
        """Copy a file or directory."""
        src = Path(source)
        dst = Path(dest)

        try:
            if src.is_file():
                shutil.copy2(src, dst)
            else:
                shutil.copytree(src, dst)
            return True
        except Exception as e:
            app_logger.error(f"Copy failed: {e}")
            return False

    def move(self, source: str, dest: str) -> bool:
        """Move a file or directory."""
        try:
            shutil.move(source, dest)
            return True
        except Exception as e:
            app_logger.error(f"Move failed: {e}")
            return False

    def delete(self, path: str, to_trash: bool = True) -> bool:
        """
        Delete a file or directory.

        Args:
            path: File/directory to delete
            to_trash: Move to trash instead of permanent deletion

        Returns:
            True if successful
        """
        p = Path(path)
        try:
            if to_trash:
                try:
                    from send2trash import send2trash
                    send2trash(path)
                    return True
                except ImportError:
                    app_logger.warning("send2trash not available, deleting permanently")

            if p.is_file():
                p.unlink()
            else:
                shutil.rmtree(p)
            return True
        except Exception as e:
            app_logger.error(f"Delete failed: {e}")
            return False

    def create_folder(self, name: str, parent: str = None) -> bool:
        """
        Create a new folder.

        Args:
            name: Folder name
            parent: Parent directory (uses current_path if None)

        Returns:
            True if successful
        """
        base = Path(parent) if parent else self.current_path
        try:
            (base / name).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            app_logger.error(f"Create folder failed: {e}")
            return False

    def rename(self, old_path: str, new_name: str) -> bool:
        """
        Rename a file or directory.

        Args:
            old_path: Current path
            new_name: New name (not full path)

        Returns:
            True if successful
        """
        try:
            p = Path(old_path)
            new_path = p.parent / new_name
            p.rename(new_path)
            return True
        except Exception as e:
            app_logger.error(f"Rename failed: {e}")
            return False

    # ═══════════════════════════════════════════════════════
    # Tags
    # ═══════════════════════════════════════════════════════

    def add_tag(self, file_path: str, tag: str):
        """Add a tag to a file."""
        if file_path not in self.file_tags:
            self.file_tags[file_path] = []
        if tag not in self.file_tags[file_path]:
            self.file_tags[file_path].append(tag)

    def remove_tag(self, file_path: str, tag: str):
        """Remove a tag from a file."""
        if file_path in self.file_tags:
            if tag in self.file_tags[file_path]:
                self.file_tags[file_path].remove(tag)

    def get_tags(self, file_path: str) -> List[str]:
        """Get tags for a file."""
        return self.file_tags.get(file_path, [])

    def find_by_tag(self, tag: str) -> List[str]:
        """Find all files with a specific tag."""
        return [
            path for path, tags in self.file_tags.items()
            if tag in tags
        ]

    # ═══════════════════════════════════════════════════════
    # Favorites & Recent
    # ═══════════════════════════════════════════════════════

    def add_to_favorites(self, path: str):
        """Add a path to favorites."""
        if path not in self.favorites:
            self.favorites.append(path)

    def remove_from_favorites(self, path: str):
        """Remove a path from favorites."""
        if path in self.favorites:
            self.favorites.remove(path)

    def get_favorites(self) -> List[str]:
        """Get favorite paths."""
        return self.favorites.copy()

    def add_to_recent(self, file_path: str):
        """Add to recent files list."""
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        self.recent_files.insert(0, file_path)
        self.recent_files = self.recent_files[:self._max_recent]

    def get_recent(self, limit: int = 20) -> List[str]:
        """Get recent files."""
        return self.recent_files[:limit]

    # ═══════════════════════════════════════════════════════
    # Info
    # ═══════════════════════════════════════════════════════

    def get_directory_stats(self, path: str = None) -> Dict:
        """
        Get statistics for a directory.

        Args:
            path: Directory path (uses current_path if None)

        Returns:
            Dict with file count, folder count, total size
        """
        target = Path(path) if path else self.current_path

        file_count = 0
        folder_count = 0
        total_size = 0

        try:
            for item in target.iterdir():
                try:
                    if item.is_file():
                        file_count += 1
                        total_size += item.stat().st_size
                    elif item.is_dir():
                        folder_count += 1
                except (PermissionError, OSError):
                    continue
        except PermissionError:
            pass

        return {
            "path": str(target),
            "files": file_count,
            "folders": folder_count,
            "total_size": total_size,
            "total_size_formatted": _format_size(total_size),
        }


def _format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
