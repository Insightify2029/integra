"""
Theme Manager
=============
Central orchestrator for the INTEGRA theme system.
Manages theme+style selection, application, switching, and persistence.

Usage:
    # At startup (in main.py):
    from core.themes import apply_theme_to_app
    apply_theme_to_app(app)

    # Switch theme at runtime (applies to all windows instantly):
    from core.themes import switch_theme
    switch_theme("tokyo_night")

    # Switch style at runtime:
    from core.themes import switch_style
    switch_style("flat")
"""

import threading

from .theme_palettes import THEME_PALETTES, get_palette, get_all_theme_names
from .theme_styles import STYLE_DEFINITIONS, get_style, get_all_style_names
from .theme_generator import generate_stylesheet
from .theme_fonts import get_app_font
from .theme_persistence import (
    load_settings, save_theme_and_style,
    save_theme_choice, save_style_choice,
)

# ─── Thread-safe state ──────────────────────────────
_lock = threading.Lock()
_current_theme: str = "dark"
_current_style: str = "modern"
_initialized: bool = False


# ═══════════════════════════════════════════════════════
#  INITIALIZATION
# ═══════════════════════════════════════════════════════

def _ensure_initialized():
    """Load saved preferences on first access."""
    global _current_theme, _current_style, _initialized
    if _initialized:
        return
    with _lock:
        if _initialized:
            return
        settings = load_settings()
        theme = settings.get("current_theme", "dark")
        style = settings.get("current_style", "modern")
        if theme in THEME_PALETTES:
            _current_theme = theme
        if style in STYLE_DEFINITIONS:
            _current_style = style
        _initialized = True


# ═══════════════════════════════════════════════════════
#  GETTERS
# ═══════════════════════════════════════════════════════

def get_current_theme() -> str:
    """Get the current active theme name."""
    _ensure_initialized()
    return _current_theme


def get_current_style() -> str:
    """Get the current active style name."""
    _ensure_initialized()
    return _current_style


def get_current_palette() -> dict:
    """Get the current theme's color palette."""
    _ensure_initialized()
    return get_palette(_current_theme)


def get_available_themes() -> list:
    """Get list of all available theme names."""
    return get_all_theme_names()


def get_available_styles() -> list:
    """Get list of all available style names."""
    return get_all_style_names()


def get_theme_display_name(theme_name: str) -> str:
    """Get display name for a theme."""
    palette = THEME_PALETTES.get(theme_name)
    return palette["display_name"] if palette else theme_name


def get_theme_icon(theme_name: str) -> str:
    """Get icon for a theme."""
    palette = THEME_PALETTES.get(theme_name)
    return palette.get("icon", "fa5s.palette") if palette else "fa5s.palette"


def get_theme_category(theme_name: str) -> str:
    """Get category (dark/light) for a theme."""
    palette = THEME_PALETTES.get(theme_name)
    return palette.get("category", "dark") if palette else "dark"


def get_theme_primary_color(theme_name: str) -> str:
    """Get primary color for a theme."""
    palette = THEME_PALETTES.get(theme_name)
    return palette.get("primary", "#2563eb") if palette else "#2563eb"


def is_dark_theme() -> bool:
    """Check if current theme is dark."""
    _ensure_initialized()
    palette = get_palette(_current_theme)
    return palette.get("is_dark", True)


# ═══════════════════════════════════════════════════════
#  SETTERS
# ═══════════════════════════════════════════════════════

def set_current_theme(theme_name: str) -> bool:
    """Set current theme (in-memory). Returns True on success."""
    global _current_theme
    _ensure_initialized()
    if theme_name in THEME_PALETTES:
        with _lock:
            _current_theme = theme_name
        return True
    return False


def set_current_style(style_name: str) -> bool:
    """Set current style (in-memory). Returns True on success."""
    global _current_style
    _ensure_initialized()
    if style_name in STYLE_DEFINITIONS:
        with _lock:
            _current_style = style_name
        return True
    return False


# ═══════════════════════════════════════════════════════
#  STYLESHEET
# ═══════════════════════════════════════════════════════

def get_stylesheet(theme_name: str = None, style_name: str = None) -> str:
    """
    Get the complete QSS stylesheet.
    Uses current theme/style if not specified.
    """
    _ensure_initialized()
    t = theme_name or _current_theme
    st = style_name or _current_style
    return generate_stylesheet(t, st)


# ═══════════════════════════════════════════════════════
#  APPLICATION-LEVEL OPERATIONS
# ═══════════════════════════════════════════════════════

def apply_theme_to_app(app) -> None:
    """
    Apply the saved theme+style to a QApplication instance.
    Call this once at startup. All widgets inherit automatically.
    """
    _ensure_initialized()
    style = get_style(_current_style)
    font = get_app_font(scale=style.get("font_scale", 1.0))
    app.setFont(font)
    qss = generate_stylesheet(_current_theme, _current_style)
    app.setStyleSheet(qss)


def switch_theme(theme_name: str) -> bool:
    """
    Switch theme at runtime. Updates all open windows instantly.
    Also saves the choice to disk.
    """
    if not set_current_theme(theme_name):
        return False
    save_theme_choice(theme_name)
    _refresh_app()
    return True


def switch_style(style_name: str) -> bool:
    """
    Switch style at runtime. Updates all open windows instantly.
    Also saves the choice to disk.
    """
    if not set_current_style(style_name):
        return False
    save_style_choice(style_name)
    _refresh_app()
    return True


def switch_theme_and_style(theme_name: str, style_name: str) -> bool:
    """Switch both theme and style at runtime."""
    _ensure_initialized()
    t_ok = theme_name in THEME_PALETTES
    s_ok = style_name in STYLE_DEFINITIONS
    if not (t_ok and s_ok):
        return False
    with _lock:
        global _current_theme, _current_style
        _current_theme = theme_name
        _current_style = style_name
    save_theme_and_style(theme_name, style_name)
    _refresh_app()
    return True


def apply_theme(widget, theme_name: str = None) -> None:
    """
    Apply theme to a specific widget (backward-compatible).
    Prefer apply_theme_to_app() for global application.
    """
    _ensure_initialized()
    qss = get_stylesheet(theme_name)
    widget.setStyleSheet(qss)
    if theme_name:
        set_current_theme(theme_name)


# ═══════════════════════════════════════════════════════
#  INTERNAL
# ═══════════════════════════════════════════════════════

def _refresh_app() -> None:
    """Re-apply stylesheet to QApplication to update all widgets."""
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app is not None:
            style = get_style(_current_style)
            font = get_app_font(scale=style.get("font_scale", 1.0))
            app.setFont(font)
            qss = generate_stylesheet(_current_theme, _current_style)
            app.setStyleSheet(qss)
    except Exception:
        pass
