"""
Settings Dialog
================
Database and application settings.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QFormLayout, QLineEdit, QPushButton, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt

from core.themes import get_stylesheet
from core.database.connection import is_connected
from core.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD


class SettingsDialog(QDialog):
    """Settings configuration dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ الإعدادات")
        self.setMinimumSize(500, 400)
        self.setStyleSheet(get_stylesheet())
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Database group
        db_group = QGroupBox("🗄️ قاعدة البيانات")
        db_layout = QFormLayout(db_group)
        
        self.host_input = QLineEdit(DB_HOST)
        self.port_input = QLineEdit(str(DB_PORT))
        self.name_input = QLineEdit(DB_NAME)
        self.user_input = QLineEdit(DB_USER)
        self.pass_input = QLineEdit(DB_PASSWORD)
        self.pass_input.setEchoMode(QLineEdit.Password)
        
        db_layout.addRow("السيرفر:", self.host_input)
        db_layout.addRow("المنفذ:", self.port_input)
        db_layout.addRow("اسم القاعدة:", self.name_input)
        db_layout.addRow("المستخدم:", self.user_input)
        db_layout.addRow("كلمة المرور:", self.pass_input)
        
        layout.addWidget(db_group)
        
        # Test connection button
        test_btn = QPushButton("🔌 اختبار الاتصال")
        test_btn.clicked.connect(self._test_connection)
        layout.addWidget(test_btn)
        
        # Connection status
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self._update_status()
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 حفظ")
        save_btn.clicked.connect(self._save_settings)
        
        cancel_btn = QPushButton("إلغاء")
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
            QMessageBox.information(self, "نجاح", "✅ الاتصال ناجح!")
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"❌ فشل الاتصال!\n{e}")
        self._update_status()

    def _save_settings(self):
        """Save database settings to .env file."""
        import os
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

            QMessageBox.information(
                self, "تم الحفظ",
                "✅ تم حفظ الإعدادات.\nيُرجى إعادة تشغيل التطبيق لتطبيق التغييرات."
            )
            self.accept()

        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"❌ فشل حفظ الإعدادات!\n{e}")
    
    def _update_status(self):
        """Update connection status label."""
        if is_connected():
            self.status_label.setText("✅ متصل")
            self.status_label.setStyleSheet("color: #10b981;")
        else:
            self.status_label.setText("❌ غير متصل")
            self.status_label.setStyleSheet("color: #ef4444;")
