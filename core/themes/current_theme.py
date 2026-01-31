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
    if theme_name in ['dark', 'light']:
        CURRENT_THEME = theme_name
        return True
    return False
