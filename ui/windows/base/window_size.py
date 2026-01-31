"""
Window Size Utilities
=====================
"""

from PyQt5.QtWidgets import QMainWindow, QApplication


def set_window_size(window: QMainWindow, width: int, height: int):
    """Set window size."""
    window.resize(width, height)


def maximize_window(window: QMainWindow):
    """Maximize window."""
    window.showMaximized()


def center_window(window: QMainWindow):
    """Center window on screen."""
    screen = QApplication.primaryScreen().geometry()
    x = (screen.width() - window.width()) // 2
    y = (screen.height() - window.height()) // 2
    window.move(x, y)


def get_screen_size():
    """Get screen dimensions."""
    screen = QApplication.primaryScreen().geometry()
    return screen.width(), screen.height()
