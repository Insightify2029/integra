"""
INTEGRA Theme System
====================
Centralized theme module providing:
- 24 color themes (16 dark + 8 light)
- 10 UI styles (Modern, Fluent, Flat, Glass, Neumorphism, Rounded, Compact, Classic, Elegant, Bold)
- Persistent preferences (saved to theme_settings.json)
- Application-level theming (one call, all widgets inherit)
- Real-time switching (change theme/style, all windows update instantly)

Quick Start:
    # In main.py (once at startup):
    from core.themes import apply_theme_to_app
    apply_theme_to_app(app)

    # Runtime switching:
    from core.themes import switch_theme, switch_style
    switch_theme("tokyo_night")
    switch_style("flat")

    # Access current palette for custom widgets:
    from core.themes import get_current_palette
    palette = get_current_palette()
    color = palette["primary"]
"""

from .theme_manager import (
    # Initialization
    apply_theme_to_app,

    # Getters
    get_current_theme,
    get_current_style,
    get_current_palette,
    get_available_themes,
    get_available_styles,
    get_theme_display_name,
    get_theme_icon,
    get_theme_category,
    get_theme_primary_color,
    is_dark_theme,

    # Setters (in-memory)
    set_current_theme,
    set_current_style,

    # Stylesheet
    get_stylesheet,

    # Runtime switching (with persistence)
    switch_theme,
    switch_style,
    switch_theme_and_style,

    # Backward compatibility
    apply_theme,
)

from .theme_palettes import get_palette, THEME_PALETTES
from .theme_styles import get_style, get_style_display_name, get_style_description, STYLE_DEFINITIONS
from .theme_fonts import (
    FONT_FAMILY_ARABIC,
    FONT_FAMILY_ENGLISH,
    FONT_SIZE_TINY,
    FONT_SIZE_SMALL,
    FONT_SIZE_BODY,
    FONT_SIZE_SUBTITLE,
    FONT_SIZE_TITLE,
    FONT_SIZE_HEADING,
    FONT_SIZE_DISPLAY,
    FONT_SIZE_LOGO,
    FONT_SIZE_MODULE_ICON,
    FONT_SIZE_NORMAL,
    FONT_SIZE_LARGE,
    FONT_SIZE_XLARGE,
    FONT_WEIGHT_NORMAL,
    FONT_WEIGHT_MEDIUM,
    FONT_WEIGHT_BOLD,
    get_font,
    get_app_font,
    get_scaled_size,
)

__all__ = [
    # App-level
    'apply_theme_to_app',

    # Getters
    'get_current_theme',
    'get_current_style',
    'get_current_palette',
    'get_available_themes',
    'get_available_styles',
    'get_theme_display_name',
    'get_theme_icon',
    'get_theme_category',
    'get_theme_primary_color',
    'is_dark_theme',

    # Setters
    'set_current_theme',
    'set_current_style',

    # Stylesheet
    'get_stylesheet',

    # Runtime switching
    'switch_theme',
    'switch_style',
    'switch_theme_and_style',

    # Backward compat
    'apply_theme',

    # Palettes
    'get_palette',
    'THEME_PALETTES',

    # Styles
    'get_style',
    'get_style_display_name',
    'get_style_description',
    'STYLE_DEFINITIONS',

    # Fonts
    'FONT_FAMILY_ARABIC',
    'FONT_FAMILY_ENGLISH',
    'FONT_SIZE_TINY',
    'FONT_SIZE_SMALL',
    'FONT_SIZE_BODY',
    'FONT_SIZE_SUBTITLE',
    'FONT_SIZE_TITLE',
    'FONT_SIZE_HEADING',
    'FONT_SIZE_DISPLAY',
    'FONT_SIZE_LOGO',
    'FONT_SIZE_MODULE_ICON',
    'FONT_SIZE_NORMAL',
    'FONT_SIZE_LARGE',
    'FONT_SIZE_XLARGE',
    'FONT_WEIGHT_NORMAL',
    'FONT_WEIGHT_MEDIUM',
    'FONT_WEIGHT_BOLD',
    'get_font',
    'get_app_font',
    'get_scaled_size',
]
