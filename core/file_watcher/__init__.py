# -*- coding: utf-8 -*-
"""
File Watcher Module
===================
Hot folder monitoring for automatic file import.

Uses watchdog library for cross-platform file system monitoring.

Components:
  - FileWatcher: Core file monitoring
  - HotFolder: Hot folder with processing pipeline
"""

from .watcher import FileWatcher, FileEvent, get_file_watcher
from .hot_folder import HotFolder, HotFolderManager, get_hot_folder_manager

__all__ = [
    "FileWatcher",
    "FileEvent",
    "get_file_watcher",
    "HotFolder",
    "HotFolderManager",
    "get_hot_folder_manager",
]
