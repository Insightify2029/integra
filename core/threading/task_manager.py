# -*- coding: utf-8 -*-
"""
Task Manager
============
Central management for background tasks using QThreadPool.

Features:
  - Singleton pattern for global access
  - Task tracking and monitoring
  - Graceful shutdown with timeout
  - Task statistics

Usage:
    from core.threading import get_task_manager, BaseWorker

    manager = get_task_manager()
    manager.submit(my_worker)

    # Check active tasks
    print(manager.active_count)

    # Shutdown (wait for tasks)
    manager.shutdown(wait=True, timeout_ms=5000)
"""

from typing import Dict, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field

from PyQt5.QtCore import QObject, QThreadPool, pyqtSignal

from .worker import BaseWorker, WorkerState


@dataclass
class TaskStats:
    """Statistics for task manager."""
    total_submitted: int = 0
    total_completed: int = 0
    total_failed: int = 0
    total_cancelled: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_completed + self.total_failed == 0:
            return 100.0
        return (self.total_completed / (self.total_completed + self.total_failed)) * 100


class TaskManager(QObject):
    """
    Central manager for background tasks.

    Signals:
        task_started(worker_id, name): Worker started
        task_finished(worker_id, success): Worker completed
        all_tasks_completed(): All queued tasks finished
    """

    # Signals
    task_started = pyqtSignal(str, str)  # worker_id, name
    task_finished = pyqtSignal(str, bool)  # worker_id, success
    all_tasks_completed = pyqtSignal()

    def __init__(self, max_threads: Optional[int] = None):
        """
        Initialize task manager.

        Args:
            max_threads: Maximum concurrent threads (None = auto based on CPU)
        """
        super().__init__()
        self._pool = QThreadPool.globalInstance()

        if max_threads is not None:
            self._pool.setMaxThreadCount(max_threads)

        self._active_workers: Dict[str, BaseWorker] = {}
        self._stats = TaskStats()
        self._shutdown_requested = False

    @property
    def max_threads(self) -> int:
        """Maximum number of concurrent threads."""
        return self._pool.maxThreadCount()

    @max_threads.setter
    def max_threads(self, value: int):
        """Set maximum concurrent threads."""
        self._pool.setMaxThreadCount(value)

    @property
    def active_count(self) -> int:
        """Number of currently running tasks."""
        return self._pool.activeThreadCount()

    @property
    def queued_count(self) -> int:
        """Number of tasks waiting in queue."""
        return len(self._active_workers) - self.active_count

    @property
    def stats(self) -> TaskStats:
        """Get task statistics."""
        return self._stats

    def submit(self, worker: BaseWorker, priority: int = 0) -> str:
        """
        Submit a worker for execution.

        Args:
            worker: The worker to execute
            priority: Execution priority (higher = sooner)

        Returns:
            Worker ID for tracking
        """
        if self._shutdown_requested:
            raise RuntimeError("TaskManager is shutting down, cannot submit new tasks")

        # Connect signals for tracking
        worker.signals.started.connect(self._on_worker_started)
        worker.signals.finished.connect(
            lambda result, w=worker: self._on_worker_finished(w, result)
        )

        # Track worker
        self._active_workers[worker.worker_id] = worker
        self._stats.total_submitted += 1

        # Start execution
        self._pool.start(worker, priority)

        return worker.worker_id

    def submit_func(self, func: Callable, *args, name: str = "Task",
                    priority: int = 0, **kwargs) -> str:
        """
        Submit a function for background execution.

        Args:
            func: Function to execute
            *args: Function arguments
            name: Task name for tracking
            priority: Execution priority
            **kwargs: Function keyword arguments

        Returns:
            Worker ID for tracking
        """
        from .worker import SimpleWorker
        worker = SimpleWorker(func, *args, name=name, **kwargs)
        return self.submit(worker, priority)

    def cancel(self, worker_id: str) -> bool:
        """
        Request cancellation of a task.

        Args:
            worker_id: The worker ID to cancel

        Returns:
            True if cancellation was requested, False if worker not found
        """
        worker = self._active_workers.get(worker_id)
        if worker:
            worker.cancel()
            self._stats.total_cancelled += 1
            return True
        return False

    def cancel_all(self):
        """Request cancellation of all active tasks."""
        for worker in self._active_workers.values():
            worker.cancel()

    def get_worker(self, worker_id: str) -> Optional[BaseWorker]:
        """Get a worker by ID."""
        return self._active_workers.get(worker_id)

    def get_active_workers(self) -> List[BaseWorker]:
        """Get list of all active workers."""
        return [
            w for w in self._active_workers.values()
            if w.state in (WorkerState.PENDING, WorkerState.RUNNING)
        ]

    def wait_for_done(self, timeout_ms: int = -1) -> bool:
        """
        Wait for all tasks to complete.

        Args:
            timeout_ms: Maximum wait time (-1 = infinite)

        Returns:
            True if all tasks completed, False if timeout
        """
        return self._pool.waitForDone(timeout_ms)

    def shutdown(self, wait: bool = True, timeout_ms: int = 5000):
        """
        Shutdown the task manager.

        Args:
            wait: Whether to wait for tasks to complete
            timeout_ms: Maximum wait time if wait=True
        """
        self._shutdown_requested = True

        # Request cancellation of all pending tasks
        self.cancel_all()

        if wait:
            self._pool.waitForDone(timeout_ms)

        self._active_workers.clear()

    def _on_worker_started(self, worker_id: str):
        """Handle worker start."""
        worker = self._active_workers.get(worker_id)
        if worker:
            self.task_started.emit(worker_id, worker.name)

    def _on_worker_finished(self, worker: BaseWorker, result):
        """Handle worker completion."""
        worker_id = worker.worker_id

        # Update stats
        if result.success:
            self._stats.total_completed += 1
        else:
            self._stats.total_failed += 1

        # Emit signal
        self.task_finished.emit(worker_id, result.success)

        # Remove from tracking (after a delay to allow result retrieval)
        if worker_id in self._active_workers:
            del self._active_workers[worker_id]

        # Check if all tasks completed
        if len(self._active_workers) == 0:
            self.all_tasks_completed.emit()


# Singleton instance
_task_manager: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """
    Get the global TaskManager instance (singleton).

    Returns:
        The global TaskManager instance
    """
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager


def reset_task_manager():
    """Reset the global TaskManager (for testing)."""
    global _task_manager
    if _task_manager is not None:
        _task_manager.shutdown(wait=True, timeout_ms=1000)
    _task_manager = None
