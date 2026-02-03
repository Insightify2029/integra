# -*- coding: utf-8 -*-
"""
Base Worker
===========
QRunnable-based worker for background tasks with progress signals.

Usage:
    class MyWorker(BaseWorker):
        def run_task(self):
            self.report_progress(50, "Processing...")
            # ... do work ...
            return TaskResult(success=True, data=result)

    worker = MyWorker()
    worker.signals.progress.connect(on_progress)
    worker.signals.finished.connect(on_finished)
    get_task_manager().submit(worker)
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime
import traceback
import uuid

from PyQt5.QtCore import QObject, QRunnable, pyqtSignal


class WorkerState(Enum):
    """Worker lifecycle states."""
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class TaskResult:
    """
    Standardized result container for worker tasks.

    Attributes:
        success: Whether the task completed successfully
        data: The result data (if successful)
        error: Error message (if failed)
        error_details: Full traceback or additional error info
    """
    success: bool
    data: Any = None
    error: Optional[str] = None
    error_details: Optional[str] = None

    @classmethod
    def ok(cls, data: Any = None) -> "TaskResult":
        """Create a successful result."""
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str, details: Optional[str] = None) -> "TaskResult":
        """Create a failed result."""
        return cls(success=False, error=error, error_details=details)


class WorkerSignals(QObject):
    """
    Signals for worker communication with UI thread.

    Signals:
        started: Emitted when worker begins execution
        progress: (percent: int, message: str) - Progress updates
        finished: (result: TaskResult) - Task completion
        error: (error: str) - Error occurred
    """
    started = pyqtSignal(str)  # worker_id
    progress = pyqtSignal(int, str)  # percent (0-100), message
    finished = pyqtSignal(object)  # TaskResult
    error = pyqtSignal(str)  # error message


class BaseWorker(QRunnable):
    """
    Base class for background workers.

    Subclasses must implement run_task() method.

    Attributes:
        worker_id: Unique identifier
        name: Human-readable name
        state: Current execution state
        signals: Qt signals for communication
    """

    def __init__(self, name: str = "Worker"):
        super().__init__()
        self.worker_id = str(uuid.uuid4())[:8]
        self.name = name
        self.state = WorkerState.PENDING
        self.signals = WorkerSignals()
        self._cancelled = False
        self._started_at: Optional[datetime] = None
        self._finished_at: Optional[datetime] = None

        # Auto-delete after completion
        self.setAutoDelete(True)

    def run(self):
        """
        QRunnable entry point. Do not override.
        Override run_task() instead.
        """
        self.state = WorkerState.RUNNING
        self._started_at = datetime.now()
        self.signals.started.emit(self.worker_id)

        try:
            if self._cancelled:
                self.state = WorkerState.CANCELLED
                self.signals.finished.emit(
                    TaskResult.fail("Task cancelled before start")
                )
                return

            # Run the actual task
            result = self.run_task()

            if not isinstance(result, TaskResult):
                # Wrap non-TaskResult returns
                result = TaskResult.ok(result)

            self._finished_at = datetime.now()
            self.state = WorkerState.COMPLETED if result.success else WorkerState.FAILED
            self.signals.finished.emit(result)

        except Exception as e:
            self._finished_at = datetime.now()
            self.state = WorkerState.FAILED
            error_msg = str(e)
            error_details = traceback.format_exc()

            self.signals.error.emit(error_msg)
            self.signals.finished.emit(
                TaskResult.fail(error_msg, error_details)
            )

    def run_task(self) -> TaskResult:
        """
        Override this method to implement task logic.

        Returns:
            TaskResult with success/failure and data
        """
        raise NotImplementedError("Subclasses must implement run_task()")

    def cancel(self):
        """Request cancellation. Task should check is_cancelled periodically."""
        self._cancelled = True
        self.state = WorkerState.CANCELLED

    @property
    def is_cancelled(self) -> bool:
        """Check if cancellation was requested."""
        return self._cancelled

    def report_progress(self, percent: int, message: str = ""):
        """
        Report progress to UI.

        Args:
            percent: Progress percentage (0-100)
            message: Optional status message
        """
        # Clamp to valid range
        percent = max(0, min(100, percent))
        self.signals.progress.emit(percent, message)

    @property
    def duration_seconds(self) -> Optional[float]:
        """Get task duration in seconds (if completed)."""
        if self._started_at and self._finished_at:
            return (self._finished_at - self._started_at).total_seconds()
        return None

    def __repr__(self):
        return f"<{self.__class__.__name__}({self.worker_id}) state={self.state.name}>"


class SimpleWorker(BaseWorker):
    """
    Worker that executes a callable function.

    Usage:
        def my_task(progress_callback):
            progress_callback(50, "Working...")
            return "result"

        worker = SimpleWorker(my_task, name="My Task")
        get_task_manager().submit(worker)
    """

    def __init__(self, func: callable, *args, name: str = "SimpleWorker", **kwargs):
        """
        Create a worker that runs a function.

        Args:
            func: The function to run (can accept progress_callback as first arg)
            *args: Arguments to pass to the function
            name: Worker name
            **kwargs: Keyword arguments to pass to the function
        """
        super().__init__(name=name)
        self._func = func
        self._args = args
        self._kwargs = kwargs

    def run_task(self) -> TaskResult:
        """Execute the wrapped function."""
        try:
            # Try to call with progress callback
            import inspect
            sig = inspect.signature(self._func)
            params = list(sig.parameters.keys())

            if params and params[0] == "progress_callback":
                result = self._func(self.report_progress, *self._args, **self._kwargs)
            else:
                result = self._func(*self._args, **self._kwargs)

            return TaskResult.ok(result)
        except Exception as e:
            return TaskResult.fail(str(e), traceback.format_exc())
