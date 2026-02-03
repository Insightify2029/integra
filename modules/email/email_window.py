"""
Email Window
============
Main window for the Email module.
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QSplitter, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer

from ui.windows.base import BaseWindow
from ui.components.email import EmailPanel
from core.email import is_outlook_available, get_outlook
from core.logging import app_logger


class EmailWindow(BaseWindow):
    """
    Main Email Module Window.

    Features:
    - Email list with folders
    - Email viewer
    - AI analysis integration
    - Outlook Classic connection
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📧 البريد الإلكتروني - INTEGRA")
        self.setMinimumSize(1200, 700)

        self._setup_ui()
        self._check_outlook()

    def _setup_ui(self):
        """Setup the window UI."""
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Email Panel
        self.email_panel = EmailPanel()
        layout.addWidget(self.email_panel)

    def _check_outlook(self):
        """Check Outlook connection and load emails."""
        if is_outlook_available():
            # Load emails after window is shown
            QTimer.singleShot(500, self._load_emails)
        else:
            self._show_outlook_warning()

    def _load_emails(self):
        """Load emails from Outlook."""
        try:
            self.email_panel.load_emails()
        except Exception as e:
            app_logger.error(f"Failed to load emails: {e}")

    def _show_outlook_warning(self):
        """Show warning if Outlook is not available."""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("تنبيه")
        msg.setText("لم يتم الاتصال بـ Outlook")
        msg.setInformativeText(
            "تأكد من أن:\n"
            "1. Outlook Classic مثبت على الجهاز\n"
            "2. Outlook مفتوح ومسجل الدخول\n"
            "3. مكتبة pywin32 مثبتة"
        )
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Retry)
        msg.setDefaultButton(QMessageBox.Retry)

        result = msg.exec_()

        if result == QMessageBox.Retry:
            # Try to connect again
            outlook = get_outlook()
            if outlook.connect():
                self._load_emails()
            else:
                self._show_outlook_warning()

    def closeEvent(self, event):
        """Handle window close."""
        event.accept()
