# -*- coding: utf-8 -*-
"""
Threading Module
================
Background Processing System with QThreadPool + Worker Pattern

Components:
  - BaseWorker: Base class for all background workers
  - TaskManager: Central task management
  - TaskResult: Standardized result container
"""

from .worker import BaseWorker, TaskResult, WorkerState
from .task_manager import TaskManager, get_task_manager

__all__ = [
    "BaseWorker",
    "TaskResult",
    "WorkerState",
    "TaskManager",
    "get_task_manager",
]
