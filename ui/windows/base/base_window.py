"""
Base Window
===========
Base class for all application windows.
"""

from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import Qt

from .window_init import init_window
from .window_size import center_window, maximize_window


class BaseWindow(QMainWindow):
    """
    Base window class.
    All windows should inherit from this.
    """
    
    def __init__(self, title_suffix="", parent=None):
        super().__init__(parent)
        
        # Initialize window
        init_window(self, title_suffix)
        
        # Set window flags for independent window
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowCloseButtonHint |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint
        )
    
    def show_centered(self):
        """Show window centered on screen."""
        self.show()
        center_window(self)
    
    def show_maximized(self):
        """Show window maximized."""
        maximize_window(self)
