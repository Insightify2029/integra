"""
Theme Manager
=============
Manages switching between themes.
Supports original dark/light themes + all palette-based themes.
"""

from .current_theme import get_current_theme, set_current_theme
from .theme_palettes import THEME_PALETTES, get_all_theme_names
from .theme_generator import generate_stylesheet

# Keep original themes as fallback
from .dark import get_complete_stylesheet as get_dark_stylesheet
from .light import get_complete_stylesheet as get_light_stylesheet


def get_available_themes():
    """Get list of available themes."""
    return get_all_theme_names()


def get_theme_display_name(theme_name):
    """Get display name for theme."""
    palette = THEME_PALETTES.get(theme_name)
    if palette:
        return palette["display_name"]
    return theme_name


def get_theme_icon(theme_name):
    """Get icon name for theme."""
    palette = THEME_PALETTES.get(theme_name)
    if palette:
        return palette.get("icon", "fa5s.palette")
    return "fa5s.palette"


def get_theme_category(theme_name):
    """Get category (dark/light) for theme."""
    palette = THEME_PALETTES.get(theme_name)
    if palette:
        return palette.get("category", "dark")
    return "dark"


def get_theme_primary_color(theme_name):
    """Get primary color for theme (used for preview)."""
    palette = THEME_PALETTES.get(theme_name)
    if palette:
        return palette.get("primary", "#2563eb")
    return "#2563eb"


def get_stylesheet(theme_name=None):
    """
    Get stylesheet for specified theme.
    If no theme specified, uses current theme.
    """
    if theme_name is None:
        theme_name = get_current_theme()

    # Use original collectors for dark/light for backward compatibility
    if theme_name == 'dark':
        return get_dark_stylesheet()
    elif theme_name == 'light':
        return get_light_stylesheet()

    # Use generator for all other themes
    if theme_name in THEME_PALETTES:
        return generate_stylesheet(theme_name)

    return get_dark_stylesheet()


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
