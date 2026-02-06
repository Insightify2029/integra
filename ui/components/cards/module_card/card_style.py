"""
Module Card Style
=================
Generates stylesheet for the module card.
"""

from core.themes import get_current_theme


def get_card_style(accent_color="#2563eb"):
    """
    Get stylesheet for module card.
    
    Args:
        accent_color: The module's accent color
    
    Returns:
        str: QSS stylesheet
    """
    theme = get_current_theme()

    if theme == 'dark':
        return f"""
            QFrame {{
                background-color: #1e293b;
                border: 2px solid transparent;
                border-radius: 20px;
            }}
            QFrame:hover {{
                background-color: #334155;
                border: 2px solid {accent_color};
            }}
            QFrame QLabel {{
                border: none;
                background: transparent;
                padding: 0px;
                margin: 0px;
            }}
        """
    else:
        return f"""
            QFrame {{
                background-color: #ffffff;
                border: 2px solid transparent;
                border-radius: 20px;
            }}
            QFrame:hover {{
                background-color: #f1f5f9;
                border: 2px solid {accent_color};
            }}
            QFrame QLabel {{
                border: none;
                background: transparent;
                padding: 0px;
                margin: 0px;
            }}
        """
