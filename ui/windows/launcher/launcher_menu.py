"""
Launcher Menu Bar
=================
Menu bar for the launcher window with QtAwesome icons.
"""

from PyQt5.QtWidgets import QAction

from core.utils.icons import icon


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
    # Main Menu (القائمة)
    # ═══════════════════════════════════════════════
    main_menu = menubar.addMenu("القائمة")
    main_menu.setIcon(icon('fa5s.bars', color='default'))

    # Settings
    actions['settings'] = QAction(icon('fa5s.cog', color='default'), "الإعدادات", window)
    main_menu.addAction(actions['settings'])

    # Themes
    actions['themes'] = QAction(icon('fa5s.palette', color='info'), "الثيمات", window)
    main_menu.addAction(actions['themes'])

    main_menu.addSeparator()

    # Exit
    actions['exit'] = QAction(icon('fa5s.sign-out-alt', color='danger'), "خروج", window)
    actions['exit'].setShortcut("Ctrl+Q")
    main_menu.addAction(actions['exit'])

    return actions
