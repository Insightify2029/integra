"""
Module Card Arabic Title
========================
The Arabic name in the module card.
"""

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.themes.dark.fonts import FONT_FAMILY_ARABIC, FONT_SIZE_TITLE, FONT_WEIGHT_BOLD


def create_card_title_arabic(text: str, color: str = "#2563eb"):
    """
    Create the Arabic title label.
    
    Args:
        text: Arabic text
        color: Text color
    
    Returns:
        QLabel: The title label
    """
    title = QLabel(text)
    title.setFont(QFont(FONT_FAMILY_ARABIC, FONT_SIZE_TITLE, FONT_WEIGHT_BOLD))
    title.setAlignment(Qt.AlignCenter)
    title.setStyleSheet(f"color: {color}; background: transparent;")
    title.setWordWrap(True)
    
    return title
