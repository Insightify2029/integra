# -*- coding: utf-8 -*-
"""
Sync Worker - v2
================
تشغيل المزامنة في thread منفصل (عشان الواجهة متقفش)
يدعم 3 أوضاع: pull / push / full
"""

from PyQt5.QtCore import QThread, pyqtSignal
from .sync_runner import run_sync_pull, run_sync_push, run_sync_full


class SyncWorker(QThread):
    """
    Worker thread للمزامنة.

    Args:
        mode: "pull" / "push" / "full"

    Signals:
        finished(bool, list): نتيجة المزامنة (نجاح, سجل العمليات)
        log_message(str): رسالة لحظية أثناء المزامنة
    """

    finished = pyqtSignal(bool, list)
    log_message = pyqtSignal(str)

    def __init__(self, mode: str = "push", parent=None):
        super().__init__(parent)
        self._mode = mode

    def run(self):
        """تنفيذ المزامنة حسب الوضع."""
        try:
            if self._mode == "pull":
                success, logs = run_sync_pull()
            elif self._mode == "full":
                success, logs = run_sync_full()
            else:
                success, logs = run_sync_push()

            self.finished.emit(success, logs)
        except Exception as e:
            self.finished.emit(False, [f"\u274c Error: {e}"])
