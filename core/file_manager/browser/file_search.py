"""
File Search
===========
Advanced file search with content search and filtering.
"""

from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from core.logging import app_logger
from .file_browser import FileInfo


class FileSearch:
    """Advanced file search engine."""

    def __init__(self):
        self._max_results = 500

    def search(self, query: str, path: str = None,
               include_content: bool = False,
               extensions: List[str] = None,
               min_size: int = None,
               max_size: int = None,
               modified_after: datetime = None,
               modified_before: datetime = None) -> List[FileInfo]:
        """
        Search for files.

        Args:
            query: Search query (filename search)
            path: Directory to search in
            include_content: Also search in file contents
            extensions: Filter by extensions (e.g., ['.pdf', '.xlsx'])
            min_size: Minimum file size in bytes
            max_size: Maximum file size in bytes
            modified_after: Only files modified after this date
            modified_before: Only files modified before this date

        Returns:
            List of matching FileInfo
        """
        target = Path(path) if path else Path.home()
        results = []

        try:
            for item in target.rglob("*"):
                if len(results) >= self._max_results:
                    break

                try:
                    # Extension filter
                    if extensions and item.is_file():
                        if item.suffix.lower() not in extensions:
                            continue

                    stat = item.stat()

                    # Size filters
                    if item.is_file():
                        if min_size is not None and stat.st_size < min_size:
                            continue
                        if max_size is not None and stat.st_size > max_size:
                            continue

                    # Date filters
                    modified = datetime.fromtimestamp(stat.st_mtime)
                    if modified_after and modified < modified_after:
                        continue
                    if modified_before and modified > modified_before:
                        continue

                    # Name search
                    if query.lower() in item.name.lower():
                        results.append(_to_file_info(item, stat))
                        continue

                    # Content search
                    if include_content and item.is_file():
                        if item.suffix in _TEXT_EXTENSIONS and stat.st_size < 5 * 1024 * 1024:
                            try:
                                content = item.read_text(encoding='utf-8', errors='ignore')
                                if query.lower() in content.lower():
                                    results.append(_to_file_info(item, stat))
                            except Exception:
                                pass

                except (PermissionError, OSError):
                    continue

        except PermissionError:
            app_logger.warning(f"Permission denied while searching: {target}")

        return results

    def search_by_extension(self, extension: str,
                            path: str = None) -> List[FileInfo]:
        """
        Find all files with a specific extension.

        Args:
            extension: File extension (e.g., '.pdf', 'pdf')
            path: Search directory

        Returns:
            List of matching files
        """
        if not extension.startswith('.'):
            extension = '.' + extension

        target = Path(path) if path else Path.home()
        results = []

        try:
            for item in target.rglob(f"*{extension}"):
                if len(results) >= self._max_results:
                    break
                try:
                    stat = item.stat()
                    results.append(_to_file_info(item, stat))
                except (PermissionError, OSError):
                    continue
        except PermissionError:
            pass

        return results

    def find_large_files(self, path: str = None,
                         min_size_mb: float = 100) -> List[FileInfo]:
        """
        Find large files.

        Args:
            path: Search directory
            min_size_mb: Minimum size in MB

        Returns:
            List of large files, sorted by size descending
        """
        min_bytes = int(min_size_mb * 1024 * 1024)
        results = self.search("", path=path, min_size=min_bytes)
        results.sort(key=lambda f: f.size, reverse=True)
        return results

    def find_duplicates(self, path: str = None,
                        by: str = "name") -> Dict[str, List[FileInfo]]:
        """
        Find duplicate files.

        Args:
            path: Search directory
            by: 'name' (same filename) or 'size' (same size)

        Returns:
            Dict mapping key to list of duplicate files
        """
        target = Path(path) if path else Path.home()
        groups: Dict[str, List[FileInfo]] = {}

        try:
            for item in target.rglob("*"):
                if not item.is_file():
                    continue

                try:
                    stat = item.stat()
                    if by == "name":
                        key = item.name
                    elif by == "size":
                        key = str(stat.st_size)
                    else:
                        continue

                    if key not in groups:
                        groups[key] = []
                    groups[key].append(_to_file_info(item, stat))

                except (PermissionError, OSError):
                    continue

        except PermissionError:
            pass

        # Only return groups with actual duplicates
        return {k: v for k, v in groups.items() if len(v) > 1}


# Text file extensions for content search
_TEXT_EXTENSIONS = {
    '.txt', '.md', '.py', '.js', '.json', '.xml', '.html', '.htm',
    '.css', '.csv', '.sql', '.yaml', '.yml', '.ini', '.cfg', '.conf',
    '.log', '.bat', '.sh', '.ps1', '.toml', '.env',
}


def _to_file_info(path: Path, stat=None) -> FileInfo:
    """Convert Path to FileInfo."""
    if stat is None:
        stat = path.stat()

    return FileInfo(
        name=path.name,
        path=str(path),
        is_dir=path.is_dir(),
        size=stat.st_size if path.is_file() else 0,
        modified=datetime.fromtimestamp(stat.st_mtime),
        extension=path.suffix.lower() if path.is_file() else "",
    )
