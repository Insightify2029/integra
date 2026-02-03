"""
Launcher Window
===============
Main application launcher window.
Sync system is DISABLED - will be implemented later.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout

from ui.windows.base import BaseWindow
from ui.dialogs import SettingsDialog, ThemesDialog

from .launcher_menu import create_launcher_menu
from .launcher_header import create_launcher_header
from .launcher_cards_area import LauncherCardsArea
from .launcher_statusbar import LauncherStatusBar

from core.database.connection import connect
from core.themes import get_stylesheet


class LauncherWindow(BaseWindow):
    """
    Main launcher window.
    Shows module cards and provides navigation.
    """

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
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = create_launcher_header()
        layout.addWidget(header)

        # Cards area
        self.cards_area = LauncherCardsArea()
        layout.addWidget(self.cards_area, 1)

        layout.addStretch()

        # Menu bar
        self.menu_actions = create_launcher_menu(self)

        # Status bar
        self.status_bar = LauncherStatusBar()
        self.setStatusBar(self.status_bar)

    def _setup_connections(self):
        """Setup signal connections."""
        self.menu_actions['settings'].triggered.connect(self._show_settings)
        self.menu_actions['themes'].triggered.connect(self._show_themes)
        self.menu_actions['exit'].triggered.connect(self.close)

        self.cards_area.module_clicked.connect(self._open_module)

    # ═══════════════════════════════════════════════════════
    # Other Methods
    # ═══════════════════════════════════════════════════════

    def _show_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec_()

    def _show_themes(self):
        dialog = ThemesDialog(self)
        if dialog.exec_():
            self.setStyleSheet(get_stylesheet())
            for window in self._open_windows.values():
                if window and window.isVisible():
                    window.setStyleSheet(get_stylesheet())

    def _open_module(self, module_id):
        if module_id in self._open_windows:
            window = self._open_windows[module_id]
            if window and window.isVisible():
                window.activateWindow()
                window.raise_()
                return

        if module_id == "mostahaqat":
            from modules.mostahaqat import MostahaqatWindow
            window = MostahaqatWindow()
            window.show()
            self._open_windows[module_id] = window
        else:
            from ui.dialogs import show_info
            show_info(self, "قريباً", f"موديول {module_id} قيد التطوير")

    def closeEvent(self, event):
        """إغلاق البرنامج."""
        # إغلاق النوافذ المفتوحة
        for window in self._open_windows.values():
            if window:
                window.close()

        event.accept()
