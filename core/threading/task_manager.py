# core/threading/task_manager.py
"""
INTEGRA - مدير المهام الخلفية (Task Manager)
=============================================
إدارة مركزية لكل المهام اللي بتشتغل في الخلفية.

المميزات:
- Thread pool موحد (بدل ما كل حتة تعمل threads)
- تتبع المهام الشغالة
- إلغاء مهمة أو كل المهام
- إحصائيات الأداء

الاستخدام:
    from core.threading import get_task_manager, Worker

    # الحصول على المدير (singleton)
    tm = get_task_manager()

    # إضافة مهمة
    worker = Worker(my_function)
    tm.submit(worker)

    # أو مباشرة
    tm.run(my_function, args=(1, 2), on_finished=handle_result)

    # إلغاء كل المهام
    tm.cancel_all()

    # إحصائيات
    print(f"مهام شغالة: {tm.active_count}")
"""

from typing import Callable, Dict, List, Optional, Tuple
from PyQt5.QtCore import QObject, QThreadPool, pyqtSignal

from core.threading.worker import Worker


class TaskManager(QObject):
    """
    مدير المهام الخلفية - Singleton

    بيدير thread pool مشترك لكل التطبيق.
    بيتتبع المهام الشغالة وبيسمح بإلغائها.
    """

    # إشارات عامة
    task_started = pyqtSignal(str)      # task_id
    task_finished = pyqtSignal(str)     # task_id
    task_error = pyqtSignal(str, str)   # task_id, error_message
    all_tasks_completed = pyqtSignal()  # كل المهام خلصت

    def __init__(self, max_threads: int = None):
        """
        إنشاء مدير المهام

        Args:
            max_threads: الحد الأقصى للـ threads (افتراضي: عدد الـ CPU cores)
        """
        super().__init__()

        # Thread Pool
        self._pool = QThreadPool.globalInstance()
        if max_threads:
            self._pool.setMaxThreadCount(max_threads)

        # تتبع المهام
        self._active_workers: Dict[str, Worker] = {}
        self._completed_count = 0
        self._error_count = 0

        # تسجيل البدء
        try:
            from core.logging import app_logger
            app_logger.info(
                f"مدير المهام جاهز | "
                f"الحد الأقصى: {self._pool.maxThreadCount()} threads"
            )
        except ImportError:
            pass

    # ══════════════════════════════════════════════════════════
    # إضافة وتشغيل المهام
    # ══════════════════════════════════════════════════════════

    def submit(self, worker: Worker) -> str:
        """
        إضافة Worker للتنفيذ

        Args:
            worker: الـ Worker المراد تنفيذه

        Returns:
            task_id للمتابعة
        """
        task_id = str(worker.task_id)

        # ربط الإشارات للتتبع
        worker.signals.started.connect(lambda: self._on_task_started(task_id))
        worker.signals.finished.connect(lambda r: self._on_task_finished(task_id, r))
        worker.signals.error.connect(lambda t, m, tb: self._on_task_error(task_id, t, m, tb))
        worker.signals.cancelled.connect(lambda: self._on_task_cancelled(task_id))

        # حفظ وتشغيل
        self._active_workers[task_id] = worker
        self._pool.start(worker)

        return task_id

    def run(
        self,
        fn: Callable,
        args: Tuple = (),
        kwargs: dict = None,
        on_started: Callable = None,
        on_finished: Callable = None,
        on_error: Callable = None,
        on_progress: Callable = None,
        use_progress: bool = False,
        task_name: str = None
    ) -> str:
        """
        تشغيل دالة في الخلفية مباشرة

        Args:
            fn: الدالة
            args: الـ arguments
            kwargs: الـ keyword arguments
            on_started: callback عند البدء
            on_finished: callback عند النجاح (result)
            on_error: callback عند الخطأ (error_type, message, traceback)
            on_progress: callback للتقدم (percentage, message)
            use_progress: هل الدالة تستخدم progress_callback
            task_name: اسم المهمة

        Returns:
            task_id للمتابعة

        مثال:
            tm = get_task_manager()
            task_id = tm.run(
                save_to_database,
                args=(data,),
                on_finished=lambda ok: show_message("تم الحفظ"),
                on_error=lambda t, m, tb: show_error(m)
            )
        """
        worker = Worker(
            fn=fn,
            args=args,
            kwargs=kwargs,
            use_progress=use_progress or (on_progress is not None),
            task_name=task_name
        )

        if on_started:
            worker.signals.started.connect(on_started)
        if on_finished:
            worker.signals.finished.connect(on_finished)
        if on_error:
            worker.signals.error.connect(on_error)
        if on_progress:
            worker.signals.progress.connect(on_progress)

        return self.submit(worker)

    # ══════════════════════════════════════════════════════════
    # التتبع والتحكم
    # ══════════════════════════════════════════════════════════

    def cancel(self, task_id: str) -> bool:
        """
        إلغاء مهمة معينة

        Args:
            task_id: معرّف المهمة

        Returns:
            True لو المهمة موجودة وتم طلب الإلغاء
        """
        worker = self._active_workers.get(str(task_id))
        if worker:
            worker.cancel()
            return True
        return False

    def cancel_all(self):
        """إلغاء كل المهام الشغالة"""
        for worker in self._active_workers.values():
            worker.cancel()

        try:
            from core.logging import app_logger
            app_logger.info(f"تم طلب إلغاء {len(self._active_workers)} مهمة")
        except ImportError:
            pass

    def wait_for_all(self, timeout_ms: int = None) -> bool:
        """
        انتظار انتهاء كل المهام

        Args:
            timeout_ms: الحد الأقصى للانتظار (بالميلي ثانية)

        Returns:
            True لو كل المهام خلصت
        """
        if timeout_ms:
            return self._pool.waitForDone(timeout_ms)
        else:
            return self._pool.waitForDone()

    def get_worker(self, task_id: str) -> Optional[Worker]:
        """الحصول على Worker بالـ ID"""
        return self._active_workers.get(str(task_id))

    # ══════════════════════════════════════════════════════════
    # الخصائص والإحصائيات
    # ══════════════════════════════════════════════════════════

    @property
    def active_count(self) -> int:
        """عدد المهام الشغالة حالياً"""
        return len(self._active_workers)

    @property
    def completed_count(self) -> int:
        """عدد المهام المكتملة"""
        return self._completed_count

    @property
    def error_count(self) -> int:
        """عدد المهام اللي فشلت"""
        return self._error_count

    @property
    def max_threads(self) -> int:
        """الحد الأقصى للـ threads"""
        return self._pool.maxThreadCount()

    @property
    def active_threads(self) -> int:
        """عدد الـ threads الشغالة"""
        return self._pool.activeThreadCount()

    def get_stats(self) -> dict:
        """إحصائيات شاملة"""
        return {
            "active_tasks": self.active_count,
            "completed_tasks": self._completed_count,
            "error_tasks": self._error_count,
            "max_threads": self.max_threads,
            "active_threads": self.active_threads,
        }

    def get_active_tasks(self) -> List[dict]:
        """قائمة المهام الشغالة"""
        return [
            {
                "task_id": task_id,
                "task_name": worker.task_name,
                "is_running": worker.is_running,
                "is_cancelled": worker.is_cancelled,
            }
            for task_id, worker in self._active_workers.items()
        ]

    # ══════════════════════════════════════════════════════════
    # Callbacks داخلية
    # ══════════════════════════════════════════════════════════

    def _on_task_started(self, task_id: str):
        """يُستدعى لما مهمة تبدأ"""
        self.task_started.emit(task_id)

        try:
            from core.logging import app_logger
            worker = self._active_workers.get(task_id)
            if worker:
                app_logger.debug(f"بدء مهمة: [{worker.task_name}] (ID: {task_id})")
        except ImportError:
            pass

    def _on_task_finished(self, task_id: str, result):
        """يُستدعى لما مهمة تخلص بنجاح"""
        self._completed_count += 1
        self._remove_worker(task_id)
        self.task_finished.emit(task_id)
        self._check_all_completed()

        try:
            from core.logging import app_logger
            app_logger.debug(f"اكتملت مهمة: (ID: {task_id})")
        except ImportError:
            pass

    def _on_task_error(self, task_id: str, error_type: str, message: str, tb: str):
        """يُستدعى لما مهمة تفشل"""
        self._error_count += 1
        self._remove_worker(task_id)
        self.task_error.emit(task_id, message)
        self._check_all_completed()

        try:
            from core.logging import app_logger
            app_logger.error(f"فشلت مهمة (ID: {task_id}): {error_type}: {message}")
        except ImportError:
            pass

    def _on_task_cancelled(self, task_id: str):
        """يُستدعى لما مهمة تتلغى"""
        self._remove_worker(task_id)
        self._check_all_completed()

        try:
            from core.logging import app_logger
            app_logger.info(f"تم إلغاء مهمة: (ID: {task_id})")
        except ImportError:
            pass

    def _remove_worker(self, task_id: str):
        """إزالة worker من القائمة"""
        self._active_workers.pop(str(task_id), None)

    def _check_all_completed(self):
        """التحقق من اكتمال كل المهام"""
        if self.active_count == 0:
            self.all_tasks_completed.emit()

    # ══════════════════════════════════════════════════════════
    # التنظيف
    # ══════════════════════════════════════════════════════════

    def shutdown(self, wait: bool = True, timeout_ms: int = 5000):
        """
        إيقاف مدير المهام

        Args:
            wait: هل ننتظر المهام تخلص
            timeout_ms: الحد الأقصى للانتظار
        """
        # إلغاء كل المهام
        self.cancel_all()

        # انتظار
        if wait:
            self._pool.waitForDone(timeout_ms)

        try:
            from core.logging import app_logger
            app_logger.info(
                f"مدير المهام - إيقاف | "
                f"مكتملة: {self._completed_count} | "
                f"أخطاء: {self._error_count}"
            )
        except ImportError:
            pass


# ══════════════════════════════════════════════════════════════
# Singleton
# ══════════════════════════════════════════════════════════════

_task_manager: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """
    الحصول على مدير المهام (Singleton)

    مثال:
        tm = get_task_manager()
        tm.run(my_function, on_finished=handle_result)
    """
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager


def shutdown_task_manager(wait: bool = True, timeout_ms: int = 5000):
    """إيقاف مدير المهام - يُستدعى عند إغلاق التطبيق"""
    global _task_manager
    if _task_manager:
        _task_manager.shutdown(wait, timeout_ms)
        _task_manager = None
