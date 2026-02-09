"""
Base Window Initialization
==========================
"""

from PyQt5.QtWidgets import QMainWindow

from core.config.app import APP_NAME, APP_SUBTITLE
from core.config.window import WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT


def init_window(window: QMainWindow, title_suffix=""):
    """
    Initialize a window with standard settings.

    Args:
        window: QMainWindow instance
        title_suffix: Optional suffix for window title
    """
    # Set title
    title = f"{APP_NAME} - {APP_SUBTITLE}"
    if title_suffix:
        title = f"{APP_NAME} - {title_suffix}"
    window.setWindowTitle(title)

    # Set minimum size
    window.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

    # Theme is applied at QApplication level - no need to set per-window
