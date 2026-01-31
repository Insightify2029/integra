"""
Module Card English Title
=========================
The English name in the module card.
"""

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.themes.dark.fonts import FONT_FAMILY_ENGLISH, FONT_SIZE_LARGE


def create_card_title_english(text: str):
    """
    Create the English title label.
    
    Args:
        text: English text
    
    Returns:
        QLabel: The title label
    """
    title = QLabel(text)
    title.setFont(QFont(FONT_FAMILY_ENGLISH, FONT_SIZE_LARGE))
    title.setAlignment(Qt.AlignCenter)
    title.setStyleSheet("color: #64748b; background: transparent;")
    
    return title
