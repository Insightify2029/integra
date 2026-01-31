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
from PyQt5.QtGui import QFont

from core.themes import get_stylesheet
from core.database.connection import is_connected


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
        
        self.host_input = QLineEdit("localhost")
        self.port_input = QLineEdit("5432")
        self.name_input = QLineEdit("integra")
        self.user_input = QLineEdit("postgres")
        self.pass_input = QLineEdit()
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
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def _test_connection(self):
        """Test database connection."""
        if is_connected():
            QMessageBox.information(self, "نجاح", "✅ الاتصال ناجح!")
        else:
            QMessageBox.warning(self, "خطأ", "❌ فشل الاتصال!")
        self._update_status()
    
    def _update_status(self):
        """Update connection status label."""
        if is_connected():
            self.status_label.setText("✅ متصل")
            self.status_label.setStyleSheet("color: #10b981;")
        else:
            self.status_label.setText("❌ غير متصل")
            self.status_label.setStyleSheet("color: #ef4444;")
