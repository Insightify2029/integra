"""
Theme Fonts
============
Centralized font system for INTEGRA.
Single source of truth for all font families, sizes, and weights.
"""

from PyQt5.QtGui import QFont

# ─── Font Families ───────────────────────────────────
FONT_FAMILY_ARABIC = "Cairo"
FONT_FAMILY_ENGLISH = "Arial"
FONT_FAMILY_MONO = "Consolas"
FONT_FAMILY_FALLBACK = "Sans-Serif"

# ─── Font Sizes (base values before style scaling) ───
FONT_SIZE_TINY = 9
FONT_SIZE_SMALL = 11
FONT_SIZE_BODY = 13
FONT_SIZE_SUBTITLE = 15
FONT_SIZE_TITLE = 18
FONT_SIZE_HEADING = 22
FONT_SIZE_DISPLAY = 28
FONT_SIZE_LOGO = 56
FONT_SIZE_MODULE_ICON = 32

# ─── Font Weights ────────────────────────────────────
FONT_WEIGHT_LIGHT = QFont.Light        # 25
FONT_WEIGHT_NORMAL = QFont.Normal      # 50
FONT_WEIGHT_MEDIUM = QFont.Medium      # 57
FONT_WEIGHT_DEMIBOLD = QFont.DemiBold  # 63
FONT_WEIGHT_BOLD = QFont.Bold          # 75

# ─── Backward Compatibility ─────────────────────────
FONT_SIZE_NORMAL = FONT_SIZE_BODY
FONT_SIZE_LARGE = FONT_SIZE_SUBTITLE
FONT_SIZE_XLARGE = FONT_SIZE_TITLE


def get_font(
    size: int = FONT_SIZE_BODY,
    weight: int = FONT_WEIGHT_NORMAL,
    family: str = FONT_FAMILY_ARABIC,
    scale: float = 1.0,
) -> QFont:
    """
    Create a QFont with the given parameters.

    Args:
        size: Base font size in points.
        weight: Font weight (use FONT_WEIGHT_* constants).
        family: Font family name.
        scale: Scale factor from the active style (e.g. 0.9 for Compact).

    Returns:
        Configured QFont instance.
    """
    scaled_size = max(7, int(size * scale))
    font = QFont(family, scaled_size)
    font.setWeight(weight)
    return font


def get_app_font(scale: float = 1.0) -> QFont:
    """Get the default application font."""
    return get_font(FONT_SIZE_BODY, FONT_WEIGHT_NORMAL, FONT_FAMILY_ARABIC, scale)


def get_scaled_size(size: int, scale: float = 1.0) -> int:
    """Scale a font size. Ensures minimum of 7."""
    return max(7, int(size * scale))
