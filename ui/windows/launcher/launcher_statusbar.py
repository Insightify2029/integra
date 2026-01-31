"""
Launcher Status Bar
===================
Status bar for the launcher window.
"""

from PyQt5.QtWidgets import QStatusBar, QLabel
from PyQt5.QtCore import QTimer

from core.config.app import APP_VERSION
from core.database.connection import is_connected


class LauncherStatusBar(QStatusBar):
    """Status bar with connection indicator."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._start_monitoring()
    
    def _setup_ui(self):
        """Setup status bar UI."""
        # Connection status (left)
        self.connection_label = QLabel()
        self.addWidget(self.connection_label)
        self._update_connection_status()
        
        # Version (right)
        version_label = QLabel(f"INTEGRA v{APP_VERSION}")
        self.addPermanentWidget(version_label)
    
    def _start_monitoring(self):
        """Start connection monitoring."""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_connection_status)
        self.timer.start(5000)  # Check every 5 seconds
    
    def _update_connection_status(self):
        """Update connection status display."""
        if is_connected():
            self.connection_label.setText("✅ متصل")
            self.connection_label.setStyleSheet("color: #10b981; font-weight: bold;")
        else:
            self.connection_label.setText("❌ غير متصل")
            self.connection_label.setStyleSheet("color: #ef4444; font-weight: bold;")
