# core/error_handling/exception_hook.py
"""
INTEGRA - معالج الأخطاء الشامل
================================
بيمسك أي خطأ غير متوقع في البرنامج ويعمل 3 حاجات:
1. يسجله في اللوج (التفاصيل الكاملة)
2. يعرض رسالة واضحة للمستخدم
3. يمنع البرنامج من الإغلاق المفاجئ

المشكلة اللي بيحلها:
  PyQt5 بيبلع الأخطاء في الـ slots و virtual methods بصمت.
  يعني ممكن يحصل خطأ ومتعرفش - البرنامج يتصرف غريب بس.

الاستخدام:
  من core/error_handling import install_exception_handler
  install_exception_handler()  # مرة واحدة في main.py
"""

import sys
import traceback
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import QApplication

# Heavy widget imports (QDialog, QTextEdit, QPushButton, etc.)
# deferred to _show_error_dialog() - only loaded when error occurs


def _log_error(message):
    """تسجيل الخطأ - في اللوج لو متاح، أو print"""
    try:
        from core.logging.app_logger import app_logger
        app_logger.critical(message)
    except ImportError:
        print(f"[CRITICAL] {message}", file=sys.stderr)


def _show_error_dialog_impl(error_type, error_message, full_traceback):
    """عرض نافذة الخطأ - widget imports happen here (lazy)."""
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel,
        QPushButton, QTextEdit, QMessageBox
    )

    try:
        dialog = QDialog()
        dialog.setWindowTitle("خطأ في البرنامج")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(200)
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)

        layout = QVBoxLayout(dialog)

        icon_label = QLabel("⚠️  حدث خطأ غير متوقع")
        icon_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c; padding: 5px;")
        layout.addWidget(icon_label)

        msg = QLabel(f"النوع: {error_type}\nالرسالة: {error_message}")
        msg.setStyleSheet("font-size: 12px; padding: 5px; background: #2d2d2d; color: #ddd; border-radius: 4px;")
        msg.setWordWrap(True)
        msg.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(msg)

        note = QLabel("البرنامج لسه شغال. التفاصيل الكاملة متسجلة في ملف اللوج.")
        note.setStyleSheet("font-size: 11px; color: #888; padding: 3px;")
        layout.addWidget(note)

        details_text = QTextEdit()
        details_text.setPlainText(full_traceback)
        details_text.setReadOnly(True)
        details_text.setStyleSheet(
            "font-family: Consolas, monospace; font-size: 10px; "
            "background: #1e1e1e; color: #ccc; padding: 5px;"
        )
        details_text.setMaximumHeight(200)
        details_text.hide()
        layout.addWidget(details_text)

        btn_layout = QHBoxLayout()

        toggle_btn = QPushButton("عرض التفاصيل ▼")

        def _toggle():
            if details_text.isVisible():
                details_text.hide()
                toggle_btn.setText("عرض التفاصيل ▼")
            else:
                details_text.show()
                toggle_btn.setText("إخفاء التفاصيل ▲")

        toggle_btn.clicked.connect(_toggle)
        toggle_btn.setStyleSheet("padding: 6px 12px;")
        btn_layout.addWidget(toggle_btn)

        copy_btn = QPushButton("نسخ التفاصيل")
        copy_btn.clicked.connect(
            lambda: (QApplication.clipboard().setText(full_traceback),
                     toggle_btn.setText("✅ تم النسخ!"))
        )
        copy_btn.setStyleSheet("padding: 6px 12px;")
        btn_layout.addWidget(copy_btn)

        btn_layout.addStretch()

        ok_btn = QPushButton("موافق")
        ok_btn.clicked.connect(dialog.accept)
        ok_btn.setStyleSheet("padding: 6px 20px; font-weight: bold;")
        ok_btn.setDefault(True)
        btn_layout.addWidget(ok_btn)

        layout.addLayout(btn_layout)

        dialog.exec_()
    except Exception:
        QMessageBox.critical(
            None,
            "خطأ",
            f"{error_type}: {error_message}\n\nالتفاصيل في ملف اللوج."
        )


class ExceptionHandler(QObject):
    """
    معالج الأخطاء الرئيسي
    - بيمسك أي خطأ غير معالج (sys.excepthook)
    - بيستخدم signal/slot عشان يعرض الـ dialog من الـ main thread
    """

    _exception_signal = pyqtSignal(str, str, str)

    def __init__(self):
        super().__init__()
        self._exception_signal.connect(self._show_error_dialog)

    def install(self):
        """تركيب المعالج - يمسك كل الأخطاء غير المعالجة"""
        sys.excepthook = self._handle_exception
        try:
            from core.logging.app_logger import app_logger
            app_logger.info("معالج الأخطاء الشامل - تم التركيب ✅")
        except ImportError:
            pass

    def _handle_exception(self, exc_type, exc_value, exc_traceback):
        """يتنادى تلقائياً لما يحصل أي خطأ غير معالج"""

        # KeyboardInterrupt (Ctrl+C) نسيبه يشتغل عادي
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        error_type = exc_type.__name__
        error_message = str(exc_value)
        full_traceback = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_report = (
            f"═══ INTEGRA Error Report ═══\n"
            f"Time: {timestamp}\n"
            f"Type: {error_type}\n"
            f"Message: {error_message}\n"
            f"{'─' * 40}\n"
            f"{full_traceback}"
        )

        _log_error(f"خطأ غير معالج: {error_type}: {error_message}\n{full_traceback}")

        try:
            if QApplication.instance():
                self._exception_signal.emit(error_type, error_message, full_report)
        except Exception:
            print(f"[CRITICAL] {full_report}", file=sys.stderr)

    def _show_error_dialog(self, error_type, error_message, full_traceback):
        """عرض نافذة الخطأ"""
        _show_error_dialog_impl(error_type, error_message, full_traceback)


# ──────────────────────────────────────────────
# المتغير العام (Singleton)
# ──────────────────────────────────────────────
_handler = None


def install_exception_handler():
    """
    تركيب معالج الأخطاء - يُستدعى مرة واحدة في main.py

    الاستخدام:
        from core.error_handling import install_exception_handler
        install_exception_handler()
    """
    global _handler
    if _handler is None:
        _handler = ExceptionHandler()
        _handler.install()
    return _handler
