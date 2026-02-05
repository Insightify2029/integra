"""
Copilot Window
==============
Floating window for AI Copilot.
"""

from typing import Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSizeGrip, QFrame
)
from PyQt5.QtCore import Qt, QPoint, QSize, pyqtSignal
from PyQt5.QtGui import QMouseEvent

from .chat_sidebar import CopilotSidebar


class CopilotWindow(QMainWindow):
    """
    Floating AI Copilot Window.

    Features:
    - Draggable title bar
    - Resizable
    - Always on top option
    - Dockable to main window

    Usage:
        window = CopilotWindow()
        window.show()
    """

    closed = pyqtSignal()
    dock_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_position: Optional[QPoint] = None
        self._always_on_top = False

        self.setWindowTitle("المساعد الذكي")
        self.setMinimumSize(380, 500)
        self.resize(400, 600)

        # Remove default title bar
        self.setWindowFlags(
            Qt.Window |
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint
        )

        self._setup_ui()

    def _setup_ui(self):
        """Setup the window UI."""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Custom title bar
        title_bar = self._create_title_bar()
        main_layout.addWidget(title_bar)

        # Copilot sidebar (as main content)
        self.copilot = CopilotSidebar()
        self.copilot.setMaximumWidth(16777215)  # Remove max width limit
        self.copilot.toggle_requested.connect(self._on_dock_requested)
        main_layout.addWidget(self.copilot, 1)

        # Size grip for resizing
        grip_container = QWidget()
        grip_layout = QHBoxLayout(grip_container)
        grip_layout.setContentsMargins(0, 0, 0, 0)
        grip_layout.addStretch()
        grip_layout.addWidget(QSizeGrip(self))
        main_layout.addWidget(grip_container)

        # Apply style
        self.setStyleSheet("""
            CopilotWindow {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
            }
        """)

    def _create_title_bar(self) -> QWidget:
        """Create custom title bar."""
        title_bar = QFrame()
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8b5cf6, stop:1 #6366f1);
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }
        """)

        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(12, 0, 8, 0)

        # Icon and title
        icon = QLabel("🤖")
        icon.setStyleSheet("font-size: 18px;")

        title = QLabel("المساعد الذكي")
        title.setStyleSheet("color: white; font-size: 13px; font-weight: bold;")

        # Window buttons
        btn_style = """
            QPushButton {
                background: transparent;
                color: white;
                border: none;
                font-size: 14px;
                padding: 4px 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.2);
            }
        """

        # Pin button
        self.pin_btn = QPushButton("📌")
        self.pin_btn.setStyleSheet(btn_style)
        self.pin_btn.setToolTip("تثبيت في الأعلى")
        self.pin_btn.clicked.connect(self._toggle_always_on_top)

        # Dock button
        dock_btn = QPushButton("◧")
        dock_btn.setStyleSheet(btn_style)
        dock_btn.setToolTip("تثبيت في الجانب")
        dock_btn.clicked.connect(self._on_dock_requested)

        # Minimize button
        min_btn = QPushButton("─")
        min_btn.setStyleSheet(btn_style)
        min_btn.clicked.connect(self.showMinimized)

        # Close button
        close_btn = QPushButton("✕")
        close_btn.setStyleSheet(btn_style + """
            QPushButton:hover {
                background-color: #ef4444;
            }
        """)
        close_btn.clicked.connect(self.close)

        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(self.pin_btn)
        layout.addWidget(dock_btn)
        layout.addWidget(min_btn)
        layout.addWidget(close_btn)

        return title_bar

    def _toggle_always_on_top(self):
        """Toggle always on top."""
        self._always_on_top = not self._always_on_top

        flags = self.windowFlags()
        if self._always_on_top:
            flags |= Qt.WindowStaysOnTopHint
            self.pin_btn.setText("📍")
        else:
            flags &= ~Qt.WindowStaysOnTopHint
            self.pin_btn.setText("📌")

        # Re-show window with new flags
        self.setWindowFlags(flags)
        self.show()

    def _on_dock_requested(self):
        """Handle dock request."""
        self.dock_requested.emit()
        self.close()

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for dragging."""
        if event.button() == Qt.LeftButton:
            if event.pos().y() < 40:  # Title bar area
                self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for dragging."""
        if event.buttons() == Qt.LeftButton and self._drag_position:
            self.move(event.globalPos() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release."""
        self._drag_position = None

    def closeEvent(self, event):
        """Handle window close."""
        self.closed.emit()
        super().closeEvent(event)

    def send_message(self, text: str):
        """Send a message to the copilot."""
        self.copilot.send_message(text)


# Global window instance
_window: Optional[CopilotWindow] = None


def get_copilot_window() -> CopilotWindow:
    """Get or create the copilot window."""
    global _window
    if _window is None:
        _window = CopilotWindow()
    return _window


def show_copilot_window():
    """Show the copilot window."""
    window = get_copilot_window()
    window.show()
    window.raise_()
    window.activateWindow()


def hide_copilot_window():
    """Hide the copilot window."""
    global _window
    if _window:
        _window.hide()
