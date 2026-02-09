"""
Module Card English Title
=========================
The English name in the module card.
"""

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt

from core.themes import (
    get_current_palette, get_font,
    FONT_SIZE_LARGE, FONT_FAMILY_ENGLISH
)


def create_card_title_english(text: str):
    """
    Create the English title label.

    Args:
        text: English text

    Returns:
        QLabel: The title label
    """
    palette = get_current_palette()

    title = QLabel(text)
    title.setFont(get_font(FONT_SIZE_LARGE, family=FONT_FAMILY_ENGLISH))
    title.setAlignment(Qt.AlignCenter)
    title.setStyleSheet(f"color: {palette['text_muted']}; background: transparent;")

    return title
