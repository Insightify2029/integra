"""
Module Card Style
=================
Generates stylesheet for the module card using centralized palette.
"""

from core.themes import get_current_palette


def get_card_style(accent_color=""):
    """
    Get stylesheet for module card.

    Args:
        accent_color: The module's accent color (uses palette primary if empty)

    Returns:
        str: QSS stylesheet
    """
    palette = get_current_palette()
    accent = accent_color or palette['primary']

    return f"""
        QFrame {{
            background-color: {palette['bg_card']};
            border: 2px solid transparent;
            border-radius: 20px;
        }}
        QFrame:hover {{
            background-color: {palette['bg_hover']};
            border: 2px solid {accent};
        }}
        QFrame QLabel {{
            border: none;
            background: transparent;
            padding: 0px;
            margin: 0px;
        }}
    """
