"""
Themes Module
=============
Contains dark and light themes.
"""

from .current_theme import get_current_theme, set_current_theme
from .theme_manager import (
    get_available_themes,
    get_theme_display_name,
    get_theme_icon,
    get_theme_category,
    get_theme_primary_color,
    get_stylesheet,
    apply_theme,
    switch_theme
)

__all__ = [
    'get_current_theme',
    'set_current_theme',
    'get_available_themes',
    'get_theme_display_name',
    'get_theme_icon',
    'get_theme_category',
    'get_theme_primary_color',
    'get_stylesheet',
    'apply_theme',
    'switch_theme'
]
