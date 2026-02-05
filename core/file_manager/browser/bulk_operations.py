"""
Bulk Operations
===============
Batch file operations: rename, move, copy, delete.
"""

import re
import shutil
from pathlib import Path
from typing import List, Dict, Optional

from core.logging import app_logger


class BulkOperations:
    """Batch file operations."""

    @staticmethod
    def bulk_rename(files: List[str], pattern: str = None,
                    replacement: str = None,
                    prefix: str = None,
                    suffix: str = None,
                    numbering: bool = False,
                    start_number: int = 1) -> List[Dict]:
        """
        Rename multiple files.

        Args:
            files: List of file paths
            pattern: Regex pattern to replace in filename
            replacement: Replacement string for pattern
            prefix: Prefix to add to filename
            suffix: Suffix to add before extension
            numbering: Add sequential numbers
            start_number: Starting number for numbering

        Returns:
            List of result dicts
        """
        results = []

        for i, file_path in enumerate(files, start_number):
            path = Path(file_path)
            old_name = path.stem
            ext = path.suffix

            new_name = old_name

            if pattern and replacement is not None:
                new_name = re.sub(pattern, replacement, new_name)

            if prefix:
                new_name = prefix + new_name

            if suffix:
                new_name = new_name + suffix

            if numbering:
                new_name = f"{new_name}_{i:03d}"

            new_path = path.parent / f"{new_name}{ext}"

            try:
                path.rename(new_path)
                results.append({
                    "old": str(path),
                    "new": str(new_path),
                    "success": True,
                })
            except Exception as e:
                results.append({
                    "old": str(path),
                    "error": str(e),
                    "success": False,
                })

        return results

    @staticmethod
    def bulk_copy(files: List[str], dest_folder: str) -> List[Dict]:
        """
        Copy multiple files to a destination folder.

        Args:
            files: List of source file paths
            dest_folder: Destination directory

        Returns:
            List of result dicts
        """
        Path(dest_folder).mkdir(parents=True, exist_ok=True)
        results = []

        for file_path in files:
            src = Path(file_path)
            dst = Path(dest_folder) / src.name

            try:
                if src.is_file():
                    shutil.copy2(src, dst)
                else:
                    shutil.copytree(src, dst)
                results.append({
                    "file": str(src),
                    "dest": str(dst),
                    "success": True,
                })
            except Exception as e:
                results.append({
                    "file": str(src),
                    "error": str(e),
                    "success": False,
                })

        return results

    @staticmethod
    def bulk_move(files: List[str], dest_folder: str) -> List[Dict]:
        """
        Move multiple files to a destination folder.

        Args:
            files: List of source file paths
            dest_folder: Destination directory

        Returns:
            List of result dicts
        """
        Path(dest_folder).mkdir(parents=True, exist_ok=True)
        results = []

        for file_path in files:
            try:
                shutil.move(file_path, dest_folder)
                results.append({
                    "file": file_path,
                    "dest": dest_folder,
                    "success": True,
                })
            except Exception as e:
                results.append({
                    "file": file_path,
                    "error": str(e),
                    "success": False,
                })

        return results

    @staticmethod
    def bulk_delete(files: List[str], to_trash: bool = True) -> List[Dict]:
        """
        Delete multiple files.

        Args:
            files: List of file paths
            to_trash: Move to trash instead of permanent deletion

        Returns:
            List of result dicts
        """
        results = []

        for file_path in files:
            p = Path(file_path)
            try:
                if to_trash:
                    try:
                        from send2trash import send2trash
                        send2trash(file_path)
                    except ImportError:
                        if p.is_file():
                            p.unlink()
                        else:
                            shutil.rmtree(p)
                else:
                    if p.is_file():
                        p.unlink()
                    else:
                        shutil.rmtree(p)

                results.append({"file": file_path, "success": True})
            except Exception as e:
                results.append({
                    "file": file_path,
                    "error": str(e),
                    "success": False,
                })

        return results
