"""
Theme Persistence
=================
Save and load theme + style preferences to a JSON file.
Thread-safe with lock protection.
"""

import json
import os
import threading

from core.logging import app_logger

_lock = threading.Lock()
_SETTINGS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "theme_settings.json",
)

_DEFAULT_SETTINGS = {
    "current_theme": "dark",
    "current_style": "modern",
    "font_scale": 1.0,
}


def load_settings() -> dict:
    """Load theme settings from file. Returns defaults if file doesn't exist."""
    with _lock:
        try:
            if os.path.exists(_SETTINGS_FILE):
                with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Merge with defaults for any missing keys
                settings = {**_DEFAULT_SETTINGS, **data}
                return settings
        except Exception as e:
            app_logger.warning(f"Failed to load theme settings: {e}")
        return dict(_DEFAULT_SETTINGS)


def save_settings(settings: dict) -> bool:
    """Save theme settings to file. Returns True on success."""
    with _lock:
        try:
            # Merge with current file to preserve unknown keys
            current = {}
            if os.path.exists(_SETTINGS_FILE):
                try:
                    with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
                        current = json.load(f)
                except Exception:
                    pass
            current.update(settings)
            with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(current, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            app_logger.error(f"Failed to save theme settings: {e}")
            return False


def get_saved_theme() -> str:
    """Get the saved theme name."""
    return load_settings().get("current_theme", "dark")


def get_saved_style() -> str:
    """Get the saved style name."""
    return load_settings().get("current_style", "modern")


def save_theme_choice(theme_name: str) -> bool:
    """Save the selected theme."""
    return save_settings({"current_theme": theme_name})


def save_style_choice(style_name: str) -> bool:
    """Save the selected style."""
    return save_settings({"current_style": style_name})


def save_theme_and_style(theme_name: str, style_name: str) -> bool:
    """Save both theme and style."""
    return save_settings({
        "current_theme": theme_name,
        "current_style": style_name,
    })
