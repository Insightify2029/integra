"""
Light Theme Collector
=====================
Combines all light theme stylesheets into one.
"""

from .colors import BACKGROUND_MAIN, TEXT_PRIMARY
from .components import (
    get_button_stylesheet,
    get_table_stylesheet,
    get_input_stylesheet,
    get_menu_stylesheet,
    get_toolbar_stylesheet,
    get_statusbar_stylesheet,
    get_scrollbar_stylesheet,
    get_dialog_stylesheet
)


def get_complete_stylesheet():
    """Get complete light theme stylesheet."""
    
    base = f"""
        QMainWindow, QWidget {{
            background-color: {BACKGROUND_MAIN};
        }}
        
        QLabel {{
            color: {TEXT_PRIMARY};
            background: transparent;
        }}
    """
    
    return (
        base +
        get_button_stylesheet() +
        get_table_stylesheet() +
        get_input_stylesheet() +
        get_menu_stylesheet() +
        get_toolbar_stylesheet() +
        get_statusbar_stylesheet() +
        get_scrollbar_stylesheet() +
        get_dialog_stylesheet()
    )
