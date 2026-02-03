# core/threading/worker.py
"""
INTEGRA - نظام المهام الخلفية (Worker)
======================================
بيسمح لك تشغّل أي كود في الخلفية بدون ما يعلّق الواجهة.

المشكلة اللي بيحلها:
  لو عملت عملية طويلة (حفظ، تحميل، حساب) في الـ main thread،
  البرنامج يتجمد لحد ما تخلص.

الاستخدام البسيط:
    from core.threading import Worker

    def my_task():
        # عملية طويلة
        return "النتيجة"

    worker = Worker(my_task)
    worker.signals.finished.connect(lambda result: print(result))
    worker.start()

الاستخدام مع progress:
    def my_task(progress_callback):
        for i in range(100):
            # شغل...
            progress_callback(i + 1, f"جاري المعالجة {i+1}%")
        return "تم"

    worker = Worker(my_task, use_progress=True)
    worker.signals.progress.connect(lambda p, msg: print(f"{p}%: {msg}"))
    worker.signals.finished.connect(lambda result: print(result))
    worker.start()
"""

import sys
import traceback
from typing import Any, Callable, Optional, Tuple
from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot


# ══════════════════════════════════════════════════════════════
# الـ Signals - للتواصل مع الـ UI
# ══════════════════════════════════════════════════════════════

class WorkerSignals(QObject):
    """
    إشارات الـ Worker للتواصل مع الـ UI

    - started: بدأ الشغل
    - progress: تقدم (نسبة، رسالة)
    - finished: خلص بنجاح (النتيجة)
    - error: حصل خطأ (نوع الخطأ، الرسالة، التفاصيل)
    - cancelled: تم الإلغاء
    """
    started = pyqtSignal()
    progress = pyqtSignal(int, str)  # (percentage, message)
    finished = pyqtSignal(object)     # (result)
    error = pyqtSignal(str, str, str) # (error_type, message, traceback)
    cancelled = pyqtSignal()


# ══════════════════════════════════════════════════════════════
# الـ Worker - ينفذ المهمة في الخلفية
# ══════════════════════════════════════════════════════════════

class Worker(QRunnable):
    """
    Worker موحد لتنفيذ المهام في الخلفية

    المميزات:
    - يشتغل في thread منفصل (ما يعلّقش الـ UI)
    - يدعم progress callback
    - يدعم الإلغاء
    - يمسك الأخطاء ويبلّغ عنها
    - يدعم تمرير arguments

    مثال:
        # بدون arguments
        worker = Worker(my_function)

        # مع arguments
        worker = Worker(my_function, args=(1, 2), kwargs={"name": "test"})

        # مع progress
        def task(progress_callback, data):
            for i, item in enumerate(data):
                process(item)
                progress_callback(int((i+1)/len(data)*100), f"Processing {i+1}")
            return "Done"

        worker = Worker(task, use_progress=True, args=(my_data,))
    """

    def __init__(
        self,
        fn: Callable,
        args: Tuple = (),
        kwargs: dict = None,
        use_progress: bool = False,
        task_id: str = None,
        task_name: str = None
    ):
        """
        إنشاء Worker جديد

        Args:
            fn: الدالة المراد تنفيذها
            args: الـ positional arguments
            kwargs: الـ keyword arguments
            use_progress: لو True، يمرر progress_callback كأول argument
            task_id: معرّف المهمة (اختياري)
            task_name: اسم المهمة للعرض (اختياري)
        """
        super().__init__()

        self.fn = fn
        self.args = args
        self.kwargs = kwargs or {}
        self.use_progress = use_progress
        self.task_id = task_id or id(self)
        self.task_name = task_name or fn.__name__ if hasattr(fn, '__name__') else "مهمة"

        self.signals = WorkerSignals()
        self._is_cancelled = False
        self._is_running = False

        # خيارات إضافية
        self.setAutoDelete(True)

    @pyqtSlot()
    def run(self):
        """تنفيذ المهمة - يُستدعى تلقائياً من الـ ThreadPool"""
        self._is_running = True
        self.signals.started.emit()

        try:
            # تجهيز الـ arguments
            if self.use_progress:
                # أول argument هو الـ progress callback
                result = self.fn(self._progress_callback, *self.args, **self.kwargs)
            else:
                result = self.fn(*self.args, **self.kwargs)

            # التحقق من الإلغاء قبل إرسال النتيجة
            if self._is_cancelled:
                self.signals.cancelled.emit()
            else:
                self.signals.finished.emit(result)

        except Exception as e:
            # التقاط أي خطأ
            error_type = type(e).__name__
            error_message = str(e)
            error_traceback = traceback.format_exc()

            self.signals.error.emit(error_type, error_message, error_traceback)

            # تسجيل الخطأ لو الـ logger متاح
            try:
                from core.logging import app_logger
                app_logger.error(
                    f"خطأ في Worker [{self.task_name}]: {error_type}: {error_message}\n"
                    f"{error_traceback}"
                )
            except ImportError:
                pass

        finally:
            self._is_running = False

    def _progress_callback(self, percentage: int, message: str = ""):
        """
        Callback لتحديث التقدم
        يُمرر للدالة لو use_progress=True
        """
        if not self._is_cancelled:
            self.signals.progress.emit(percentage, message)

    def cancel(self):
        """
        طلب إلغاء المهمة
        ملاحظة: الإلغاء الفعلي يعتمد على الدالة نفسها
        """
        self._is_cancelled = True

    @property
    def is_cancelled(self) -> bool:
        """هل تم طلب الإلغاء؟"""
        return self._is_cancelled

    @property
    def is_running(self) -> bool:
        """هل المهمة شغالة؟"""
        return self._is_running

    def start(self):
        """
        بدء تنفيذ المهمة
        اختصار لـ TaskManager().submit(self)
        """
        from core.threading.task_manager import get_task_manager
        get_task_manager().submit(self)


# ══════════════════════════════════════════════════════════════
# اختصارات سريعة
# ══════════════════════════════════════════════════════════════

def run_in_background(
    fn: Callable,
    args: Tuple = (),
    kwargs: dict = None,
    on_finished: Callable = None,
    on_error: Callable = None,
    on_progress: Callable = None,
    use_progress: bool = False,
    task_name: str = None
) -> Worker:
    """
    اختصار سريع لتشغيل دالة في الخلفية

    مثال:
        def save_data(data):
            # عملية طويلة
            return True

        run_in_background(
            save_data,
            args=(my_data,),
            on_finished=lambda ok: print("تم الحفظ" if ok else "فشل"),
            on_error=lambda t, m, tb: print(f"خطأ: {m}")
        )

    Args:
        fn: الدالة
        args: الـ arguments
        kwargs: الـ keyword arguments
        on_finished: callback عند النجاح (result)
        on_error: callback عند الخطأ (error_type, message, traceback)
        on_progress: callback للتقدم (percentage, message)
        use_progress: هل الدالة تستخدم progress_callback
        task_name: اسم المهمة

    Returns:
        الـ Worker (للتحكم فيه لو محتاج)
    """
    worker = Worker(
        fn=fn,
        args=args,
        kwargs=kwargs,
        use_progress=use_progress or (on_progress is not None),
        task_name=task_name
    )

    if on_finished:
        worker.signals.finished.connect(on_finished)

    if on_error:
        worker.signals.error.connect(on_error)

    if on_progress:
        worker.signals.progress.connect(on_progress)

    worker.start()
    return worker
