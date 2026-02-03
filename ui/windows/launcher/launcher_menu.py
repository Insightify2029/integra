"""
Launcher Menu Bar
=================
Menu bar for the launcher window.
"""

from PyQt5.QtWidgets import QAction


def create_launcher_menu(window):
    """
    Create the launcher menu bar.
    
    Args:
        window: The main window
    
    Returns:
        dict: Dictionary of menu actions
    """
    menubar = window.menuBar()
    actions = {}
    
    # ═══════════════════════════════════════════════
    # ☰ Main Menu (القائمة)
    # ═══════════════════════════════════════════════
    main_menu = menubar.addMenu("☰ القائمة")
    
    # Settings
    actions['settings'] = QAction("⚙️ الإعدادات", window)
    main_menu.addAction(actions['settings'])
    
    # Themes
    actions['themes'] = QAction("🎨 الثيمات", window)
    main_menu.addAction(actions['themes'])
    
    main_menu.addSeparator()
    
    # Exit
    actions['exit'] = QAction("🚪 خروج", window)
    actions['exit'].setShortcut("Ctrl+Q")
    main_menu.addAction(actions['exit'])
    
    return actions
