"""
Base Window Initialization
==========================
"""

from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtGui import QFont

from core.config.app import APP_NAME, APP_VERSION, APP_SUBTITLE
from core.config.window import WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT
from core.themes import get_stylesheet
from core.themes.dark.fonts import FONT_FAMILY_ARABIC, FONT_SIZE_NORMAL


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
    
    # Apply theme
    window.setStyleSheet(get_stylesheet())
    
    # Set font
    font = QFont(FONT_FAMILY_ARABIC, FONT_SIZE_NORMAL)
    window.setFont(font)
