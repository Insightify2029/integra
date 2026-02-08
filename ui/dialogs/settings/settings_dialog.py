"""
Settings Dialog
================
Database and application settings with modern UI.
Uses QtAwesome icons, Fluent widgets, and toast notifications.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QFormLayout, QLabel
)
from PyQt5.QtCore import Qt, QSize

from core.themes import get_stylesheet
from core.database.connection import is_connected
from core.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from core.utils.icons import icon
from ui.components.fluent import (
    FluentLineEdit, FluentPrimaryButton, FluentButton
)
from ui.components.notifications import toast_success, toast_error


class SettingsDialog(QDialog):
    """Settings configuration dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("الإعدادات")
        self.setWindowIcon(icon('fa5s.cog', color='default'))
        self.setMinimumSize(500, 400)
        self.setStyleSheet(get_stylesheet())

        self._setup_ui()

    def _setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Database group
        db_group = QGroupBox("  قاعدة البيانات")
        db_group.setIcon = None  # QGroupBox doesn't have setIcon
        db_layout = QFormLayout(db_group)

        self.host_input = FluentLineEdit()
        self.host_input.setText(DB_HOST)
        self.port_input = FluentLineEdit()
        self.port_input.setText(str(DB_PORT))
        self.name_input = FluentLineEdit()
        self.name_input.setText(DB_NAME)
        self.user_input = FluentLineEdit()
        self.user_input.setText(DB_USER)
        self.pass_input = FluentLineEdit()
        self.pass_input.setText(DB_PASSWORD)
        self.pass_input.setEchoMode(FluentLineEdit.Password)

        db_layout.addRow("السيرفر:", self.host_input)
        db_layout.addRow("المنفذ:", self.port_input)
        db_layout.addRow("اسم القاعدة:", self.name_input)
        db_layout.addRow("المستخدم:", self.user_input)
        db_layout.addRow("كلمة المرور:", self.pass_input)

        layout.addWidget(db_group)

        # Test connection button
        test_btn = FluentButton()
        test_btn.setText("اختبار الاتصال")
        test_btn.setIcon(icon('fa5s.plug', color='info'))
        test_btn.setIconSize(QSize(16, 16))
        test_btn.clicked.connect(self._test_connection)
        layout.addWidget(test_btn)

        # Connection status with icon
        status_widget = QHBoxLayout()
        self._status_icon = QLabel()
        self._status_icon.setFixedSize(18, 18)
        status_widget.addStretch()
        status_widget.addWidget(self._status_icon)
        self._status_text = QLabel()
        self._status_text.setAlignment(Qt.AlignCenter)
        status_widget.addWidget(self._status_text)
        status_widget.addStretch()
        self._update_status()
        layout.addLayout(status_widget)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()

        save_btn = FluentPrimaryButton()
        save_btn.setText("حفظ")
        save_btn.setIcon(icon('fa5s.save', color='#ffffff'))
        save_btn.setIconSize(QSize(16, 16))
        save_btn.clicked.connect(self._save_settings)

        cancel_btn = FluentButton()
        cancel_btn.setText("إلغاء")
        cancel_btn.setIcon(icon('fa5s.times', color='danger'))
        cancel_btn.setIconSize(QSize(16, 16))
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def _test_connection(self):
        """Test database connection using current form inputs."""
        import psycopg2

        params = {
            "host": self.host_input.text().strip(),
            "port": self.port_input.text().strip(),
            "database": self.name_input.text().strip(),
            "user": self.user_input.text().strip(),
            "password": self.pass_input.text(),
        }

        try:
            conn = psycopg2.connect(**params, connect_timeout=5)
            conn.close()
            toast_success(self, "نجاح", "الاتصال ناجح!")
        except Exception as e:
            toast_error(self, "خطأ", f"فشل الاتصال!\n{e}")
        self._update_status()

    def _save_settings(self):
        """Save database settings to .env file."""
        from pathlib import Path

        env_path = Path(__file__).resolve().parents[3] / ".env"

        settings = {
            "DB_HOST": self.host_input.text().strip(),
            "DB_PORT": self.port_input.text().strip(),
            "DB_NAME": self.name_input.text().strip(),
            "DB_USER": self.user_input.text().strip(),
            "DB_PASSWORD": self.pass_input.text(),
        }

        try:
            # Read existing .env lines (preserve non-DB settings)
            existing_lines = []
            if env_path.exists():
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        key = line.split("=", 1)[0].strip() if "=" in line else ""
                        if key not in settings:
                            existing_lines.append(line)

            # Write updated .env
            with open(env_path, "w", encoding="utf-8") as f:
                for line in existing_lines:
                    f.write(line)
                for key, value in settings.items():
                    f.write(f"{key}={value}\n")

            toast_success(
                self, "تم الحفظ",
                "تم حفظ الإعدادات. يُرجى إعادة تشغيل التطبيق لتطبيق التغييرات."
            )
            self.accept()

        except Exception as e:
            toast_error(self, "خطأ", f"فشل حفظ الإعدادات!\n{e}")

    def _update_status(self):
        """Update connection status label."""
        if is_connected():
            self._status_icon.setPixmap(
                icon('fa5s.check-circle', color='#10b981').pixmap(16, 16)
            )
            self._status_text.setText("متصل")
            self._status_text.setStyleSheet("color: #10b981; font-weight: bold;")
        else:
            self._status_icon.setPixmap(
                icon('fa5s.times-circle', color='#ef4444').pixmap(16, 16)
            )
            self._status_text.setText("غير متصل")
            self._status_text.setStyleSheet("color: #ef4444; font-weight: bold;")
