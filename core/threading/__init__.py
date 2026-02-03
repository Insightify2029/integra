# core/threading/__init__.py
"""
INTEGRA - نظام المهام الخلفية
==============================

بيسمح لك تشغّل عمليات طويلة في الخلفية بدون ما تعلّق الواجهة.

الاستخدام البسيط:
    from core.threading import run_in_background

    run_in_background(
        save_to_database,
        args=(data,),
        on_finished=lambda ok: print("تم!"),
        on_error=lambda t, m, tb: print(f"خطأ: {m}")
    )

الاستخدام المتقدم:
    from core.threading import Worker, get_task_manager

    # إنشاء worker
    worker = Worker(my_function, args=(1, 2))
    worker.signals.progress.connect(update_progress_bar)
    worker.signals.finished.connect(handle_result)
    worker.start()

    # أو عبر المدير
    tm = get_task_manager()
    task_id = tm.run(my_function, on_finished=handle_result)
    tm.cancel(task_id)  # إلغاء

مع Progress:
    def heavy_task(progress_callback, items):
        for i, item in enumerate(items):
            process(item)
            progress_callback(int((i+1)/len(items)*100), f"معالجة {i+1}/{len(items)}")
        return "تم"

    worker = Worker(heavy_task, args=(my_items,), use_progress=True)
    worker.signals.progress.connect(lambda p, msg: progress_bar.setValue(p))
    worker.start()
"""

from core.threading.worker import (
    Worker,
    WorkerSignals,
    run_in_background,
)

from core.threading.task_manager import (
    TaskManager,
    get_task_manager,
    shutdown_task_manager,
)


__all__ = [
    # Worker
    "Worker",
    "WorkerSignals",
    "run_in_background",

    # Task Manager
    "TaskManager",
    "get_task_manager",
    "shutdown_task_manager",
]
