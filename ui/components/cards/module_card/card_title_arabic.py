"""
Module Card Arabic Title
========================
The Arabic name in the module card.
"""

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt

from core.themes import (
    get_current_palette, get_font,
    FONT_SIZE_TITLE, FONT_WEIGHT_BOLD
)


def create_card_title_arabic(text: str, color: str = ""):
    """
    Create the Arabic title label.

    Args:
        text: Arabic text
        color: Text color (uses palette primary if empty)

    Returns:
        QLabel: The title label
    """
    palette = get_current_palette()
    title_color = color or palette['primary']

    title = QLabel(text)
    title.setFont(get_font(FONT_SIZE_TITLE, FONT_WEIGHT_BOLD))
    title.setAlignment(Qt.AlignCenter)
    title.setStyleSheet(f"color: {title_color}; background: transparent;")
    title.setWordWrap(True)

    return title
