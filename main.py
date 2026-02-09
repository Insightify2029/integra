"""
INTEGRA - Integrated Management System
=======================================
Entry Point
Version: 4.0.0

Optimized startup:
1. Show splash screen instantly (minimal imports)
2. Initialize core systems in parallel with splash
3. Connect database in background
4. Show main window ASAP
"""

import sys
import os
import atexit

# Ensure logs directory exists (before anything else)
_logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(_logs_dir, exist_ok=True)

# Redirect streams for pythonw (headless) mode
_opened_streams = []
if sys.stderr is None:
    sys.stderr = open(os.path.join(_logs_dir, "stderr.log"), "w", encoding="utf-8")
    _opened_streams.append(sys.stderr)
if sys.stdout is None:
    sys.stdout = open(os.path.join(_logs_dir, "stdout.log"), "w", encoding="utf-8")
    _opened_streams.append(sys.stdout)


def _close_streams():
    for stream in _opened_streams:
        try:
            stream.close()
        except Exception:
            pass


atexit.register(_close_streams)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont


def main():
    """Application entry point with optimized startup."""
    app = QApplication(sys.argv)

    # Set default font immediately (fast)
    font = QFont("Cairo", 11)
    app.setFont(font)

    app.setApplicationName("INTEGRA")
    app.setApplicationVersion("4.0.0")
    app.setOrganizationName("INTEGRA")

    # ── Step 1: Show splash screen INSTANTLY ──
    from ui.windows.splash import IntegraSplashScreen
    splash = IntegraSplashScreen()
    splash.show()
    splash.set_progress(5, "جاري تهيئة النظام")

    # ── Step 2: Initialize logging (loguru only, rich deferred) ──
    from core.logging import setup_logging
    setup_logging(debug_mode=True)
    splash.set_progress(25, "تم تحميل نظام السجلات")

    # ── Step 3: Install exception handler (lightweight - no widget imports) ──
    from core.error_handling import install_exception_handler
    install_exception_handler()
    splash.set_progress(40, "تم تهيئة معالج الأخطاء")

    # ── Step 4: Initialize task manager ──
    from core.threading import get_task_manager, shutdown_task_manager
    get_task_manager()
    app.aboutToQuit.connect(lambda: shutdown_task_manager(wait=True, timeout_ms=5000))
    splash.set_progress(55, "تم تهيئة مدير المهام")

    # ── Step 5: Connect to database ──
    splash.set_progress(65, "جاري الاتصال بقاعدة البيانات")
    from core.database.connection import connect
    try:
        connect()
        splash.set_progress(80, "تم الاتصال بقاعدة البيانات")
    except Exception:
        splash.set_progress(80, "تعذر الاتصال - سيتم المحاولة لاحقاً")

    # ── Step 6: Load main window ──
    splash.set_progress(90, "جاري تحميل الواجهة الرئيسية")

    from ui.windows.launcher import LauncherWindow
    window = LauncherWindow()

    splash.set_progress(100, "اكتمل التحميل")

    # ── Step 7: Show window, close splash ──
    window.show()
    splash.finish()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
