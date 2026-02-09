"""
Current Theme
=============
Stores the current active theme.
"""

# Current active theme: 'dark' or 'light'
CURRENT_THEME = "dark"


def get_current_theme():
    """Get current theme name."""
    return CURRENT_THEME


def set_current_theme(theme_name):
    """Set current theme name."""
    global CURRENT_THEME
    from .theme_palettes import THEME_PALETTES
    if theme_name in THEME_PALETTES:
        CURRENT_THEME = theme_name
        return True
    return False
