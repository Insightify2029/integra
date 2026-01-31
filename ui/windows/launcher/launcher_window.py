"""
Launcher Window
===============
Main application launcher window.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt

from ui.windows.base import BaseWindow
from ui.dialogs import SettingsDialog, ThemesDialog

from .launcher_menu import create_launcher_menu
from .launcher_header import create_launcher_header
from .launcher_cards_area import LauncherCardsArea
from .launcher_statusbar import LauncherStatusBar

from core.database.connection import connect
from core.themes import get_stylesheet, apply_theme


class LauncherWindow(BaseWindow):
    """
    Main launcher window.
    Shows module cards and provides navigation.
    """
    
    # Store references to open module windows
    _open_windows = {}
    
    def __init__(self):
        super().__init__()
        
        # Connect to database
        connect()
        
        # Setup UI
        self._setup_ui()
        self._setup_connections()
        
        # Maximize on start
        self.showMaximized()
    
    def _setup_ui(self):
        """Setup the window UI."""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header (INTEGRA logo)
        header = create_launcher_header()
        layout.addWidget(header)
        
        # Cards area
        self.cards_area = LauncherCardsArea()
        layout.addWidget(self.cards_area, 1)
        
        # Spacer
        layout.addStretch()
        
        # Menu bar
        self.menu_actions = create_launcher_menu(self)
        
        # Status bar
        self.status_bar = LauncherStatusBar()
        self.setStatusBar(self.status_bar)
    
    def _setup_connections(self):
        """Setup signal connections."""
        # Menu actions
        self.menu_actions['settings'].triggered.connect(self._show_settings)
        self.menu_actions['themes'].triggered.connect(self._show_themes)
        self.menu_actions['exit'].triggered.connect(self.close)
        
        # Module cards
        self.cards_area.module_clicked.connect(self._open_module)
    
    def _show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self)
        dialog.exec_()
    
    def _show_themes(self):
        """Show themes dialog."""
        dialog = ThemesDialog(self)
        if dialog.exec_():
            # Refresh theme
            self.setStyleSheet(get_stylesheet())
            
            # Refresh all open windows
            for window in self._open_windows.values():
                if window and window.isVisible():
                    window.setStyleSheet(get_stylesheet())
    
    def _open_module(self, module_id):
        """
        Open a module window.
        
        Args:
            module_id: The module identifier
        """
        # Check if already open
        if module_id in self._open_windows:
            window = self._open_windows[module_id]
            if window and window.isVisible():
                window.activateWindow()
                window.raise_()
                return
        
        # Open new window based on module
        if module_id == 'mostahaqat':
            from modules.mostahaqat import MostahaqatWindow
            window = MostahaqatWindow()
            window.show()
            self._open_windows[module_id] = window
        else:
            # Module not implemented yet
            from ui.dialogs import show_info
            show_info(self, "قريباً", f"موديول {module_id} قيد التطوير")
    
    def closeEvent(self, event):
        """Handle window close."""
        # Close all module windows
        for window in self._open_windows.values():
            if window:
                window.close()
        
        event.accept()
