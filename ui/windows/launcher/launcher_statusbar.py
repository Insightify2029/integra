"""
Launcher Status Bar
===================
Status bar for the launcher window with QtAwesome icons.
"""

from PyQt5.QtWidgets import QStatusBar, QLabel, QHBoxLayout, QWidget
from PyQt5.QtCore import QTimer, Qt

from core.config.app import APP_VERSION
from core.database.connection import is_connected
from core.utils.icons import icon


class LauncherStatusBar(QStatusBar):
    """Status bar with connection indicator and QtAwesome icons."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._start_monitoring()

    def _setup_ui(self):
        """Setup status bar UI."""
        # Connection status (left) with icon
        conn_widget = QWidget()
        conn_layout = QHBoxLayout(conn_widget)
        conn_layout.setContentsMargins(4, 0, 4, 0)
        conn_layout.setSpacing(6)

        self._conn_icon = QLabel()
        self._conn_icon.setFixedSize(16, 16)
        conn_layout.addWidget(self._conn_icon)

        self._conn_text = QLabel()
        conn_layout.addWidget(self._conn_text)

        self.addWidget(conn_widget)
        self._update_connection_status()

        # Version (right) with icon
        ver_widget = QWidget()
        ver_layout = QHBoxLayout(ver_widget)
        ver_layout.setContentsMargins(4, 0, 4, 0)
        ver_layout.setSpacing(6)

        ver_icon = QLabel()
        ver_icon.setPixmap(icon('fa5s.code-branch', color='info').pixmap(14, 14))
        ver_layout.addWidget(ver_icon)

        ver_label = QLabel(f"INTEGRA v{APP_VERSION}")
        ver_layout.addWidget(ver_label)

        self.addPermanentWidget(ver_widget)

    def _start_monitoring(self):
        """Start connection monitoring."""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_connection_status)
        self.timer.start(5000)  # Check every 5 seconds

    def _update_connection_status(self):
        """Update connection status display."""
        if is_connected():
            self._conn_icon.setPixmap(
                icon('fa5s.check-circle', color='#10b981').pixmap(14, 14)
            )
            self._conn_text.setText("متصل")
            self._conn_text.setStyleSheet("color: #10b981; font-weight: bold;")
        else:
            self._conn_icon.setPixmap(
                icon('fa5s.times-circle', color='#ef4444').pixmap(14, 14)
            )
            self._conn_text.setText("غير متصل")
            self._conn_text.setStyleSheet("color: #ef4444; font-weight: bold;")
