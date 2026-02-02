"""
INTEGRA - Integrated Management System
=======================================
Entry Point
Version: 2.1.0
"""

import sys
import os

# التأكد إن مجلد logs موجود (مهم قبل أي حاجة)
_logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(_logs_dir, exist_ok=True)

# إخفاء الكونسول: لو مفيش stderr (pythonw) نوجهه لملف
if sys.stderr is None:
    sys.stderr = open(os.path.join(_logs_dir, "stderr.log"), "w", encoding="utf-8")
if sys.stdout is None:
    sys.stdout = open(os.path.join(_logs_dir, "stdout.log"), "w", encoding="utf-8")

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from core.logging import setup_logging

setup_logging(debug_mode=True)


def main():
    """Application entry point."""
    app = QApplication(sys.argv)

    # تركيب معالج الأخطاء (لازم يكون بعد QApplication)
    from core.error_handling import install_exception_handler
    install_exception_handler()

    # Set application info
    app.setApplicationName("INTEGRA")
    app.setApplicationVersion("2.1.0")
    app.setOrganizationName("INTEGRA")

    # Set default font
    font = QFont("Cairo", 11)
    app.setFont(font)

    # Import and show launcher
    from ui.windows.launcher import LauncherWindow

    window = LauncherWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
