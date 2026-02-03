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
from PyQt5.QtWidgets import QApplication, QMessageBox, QTextEdit, QVBoxLayout, QDialog, QPushButton, QHBoxLayout, QLabel


# محاولة استيراد الـ logger (لو A1 مركّب)
try:
    from core.logging.app_logger import app_logger as logger
    _has_logger = True
except ImportError:
    _has_logger = False


def _log_error(message):
    """تسجيل الخطأ - في اللوج لو متاح، أو print"""
    if _has_logger:
        logger.critical(message)
    else:
        print(f"[CRITICAL] {message}", file=sys.stderr)


class ErrorDialog(QDialog):
    """
    نافذة عرض الخطأ للمستخدم
    - رسالة مختصرة واضحة
    - زر "التفاصيل" لعرض المعلومات التقنية
    - زر "نسخ" لنسخ التفاصيل
    """

    def __init__(self, error_type, error_message, full_traceback, parent=None):
        super().__init__(parent)
        self.setWindowTitle("خطأ في البرنامج")
        self.setMinimumWidth(500)
        self.setMinimumHeight(200)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        layout = QVBoxLayout(self)

        # ─── الرسالة المختصرة ───
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

        # ─── التفاصيل التقنية (مخفية افتراضياً) ───
        self.details_text = QTextEdit()
        self.details_text.setPlainText(full_traceback)
        self.details_text.setReadOnly(True)
        self.details_text.setStyleSheet(
            "font-family: Consolas, monospace; font-size: 10px; "
            "background: #1e1e1e; color: #ccc; padding: 5px;"
        )
        self.details_text.setMaximumHeight(200)
        self.details_text.hide()
        layout.addWidget(self.details_text)

        # ─── الأزرار ───
        btn_layout = QHBoxLayout()

        self.toggle_btn = QPushButton("عرض التفاصيل ▼")
        self.toggle_btn.clicked.connect(self._toggle_details)
        self.toggle_btn.setStyleSheet("padding: 6px 12px;")
        btn_layout.addWidget(self.toggle_btn)

        copy_btn = QPushButton("نسخ التفاصيل")
        copy_btn.clicked.connect(self._copy_details)
        copy_btn.setStyleSheet("padding: 6px 12px;")
        btn_layout.addWidget(copy_btn)

        btn_layout.addStretch()

        ok_btn = QPushButton("موافق")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setStyleSheet("padding: 6px 20px; font-weight: bold;")
        ok_btn.setDefault(True)
        btn_layout.addWidget(ok_btn)

        layout.addLayout(btn_layout)

        self._full_traceback = full_traceback

    def _toggle_details(self):
        if self.details_text.isVisible():
            self.details_text.hide()
            self.toggle_btn.setText("عرض التفاصيل ▼")
        else:
            self.details_text.show()
            self.toggle_btn.setText("إخفاء التفاصيل ▲")

    def _copy_details(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self._full_traceback)
        self.toggle_btn.setText("✅ تم النسخ!")


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
        if _has_logger:
            logger.info("معالج الأخطاء الشامل - تم التركيب ✅")

    def _handle_exception(self, exc_type, exc_value, exc_traceback):
        """يتنادى تلقائياً لما يحصل أي خطأ غير معالج"""

        # KeyboardInterrupt (Ctrl+C) نسيبه يشتغل عادي
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # تجميع التفاصيل
        error_type = exc_type.__name__
        error_message = str(exc_value)
        full_traceback = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

        # إضافة timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_report = (
            f"═══ INTEGRA Error Report ═══\n"
            f"Time: {timestamp}\n"
            f"Type: {error_type}\n"
            f"Message: {error_message}\n"
            f"{'─' * 40}\n"
            f"{full_traceback}"
        )

        # 1) تسجيل في اللوج
        _log_error(f"خطأ غير معالج: {error_type}: {error_message}\n{full_traceback}")

        # 2) عرض للمستخدم (عبر signal عشان نكون في الـ main thread)
        try:
            if QApplication.instance():
                self._exception_signal.emit(error_type, error_message, full_report)
        except Exception:
            # لو حتى عرض الرسالة فشل، على الأقل الخطأ متسجل في اللوج
            print(f"[CRITICAL] {full_report}", file=sys.stderr)

    def _show_error_dialog(self, error_type, error_message, full_traceback):
        """عرض نافذة الخطأ"""
        try:
            dialog = ErrorDialog(error_type, error_message, full_traceback)
            dialog.exec_()
        except Exception:
            # Fallback لو الـ dialog نفسه فشل
            QMessageBox.critical(
                None,
                "خطأ",
                f"{error_type}: {error_message}\n\nالتفاصيل في ملف اللوج."
            )


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
