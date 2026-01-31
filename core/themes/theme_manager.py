"""
Theme Manager
=============
Manages switching between themes.
"""

from .current_theme import get_current_theme, set_current_theme
from .dark import get_complete_stylesheet as get_dark_stylesheet
from .light import get_complete_stylesheet as get_light_stylesheet


def get_available_themes():
    """Get list of available themes."""
    return ['dark', 'light']


def get_theme_display_name(theme_name):
    """Get display name for theme."""
    names = {
        'dark': '🌙 داكن (Dark)',
        'light': '☀️ فاتح (Light)'
    }
    return names.get(theme_name, theme_name)


def get_stylesheet(theme_name=None):
    """
    Get stylesheet for specified theme.
    If no theme specified, uses current theme.
    """
    if theme_name is None:
        theme_name = get_current_theme()
    
    if theme_name == 'dark':
        return get_dark_stylesheet()
    elif theme_name == 'light':
        return get_light_stylesheet()
    else:
        return get_dark_stylesheet()  # Default to dark


def apply_theme(widget, theme_name=None):
    """
    Apply theme to a widget.
    If no theme specified, uses current theme.
    """
    stylesheet = get_stylesheet(theme_name)
    widget.setStyleSheet(stylesheet)
    
    if theme_name:
        set_current_theme(theme_name)


def switch_theme():
    """Switch between dark and light themes."""
    current = get_current_theme()
    new_theme = 'light' if current == 'dark' else 'dark'
    set_current_theme(new_theme)
    return new_theme
