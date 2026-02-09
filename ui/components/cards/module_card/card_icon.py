"""
Module Card Icon
================
The emoji icon in the module card.
"""

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt

from core.themes import get_font, FONT_SIZE_MODULE_ICON


def create_card_icon(icon_text: str):
    """
    Create the card icon label.

    Args:
        icon_text: Emoji icon string

    Returns:
        QLabel: The icon label
    """
    icon = QLabel(icon_text)
    icon.setFont(get_font(FONT_SIZE_MODULE_ICON))
    icon.setAlignment(Qt.AlignCenter)
    icon.setStyleSheet("background: transparent;")

    return icon
