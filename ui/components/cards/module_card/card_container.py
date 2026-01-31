"""
Module Card Container
=====================
The outer frame of the module card.
"""

from PyQt5.QtWidgets import QFrame
from PyQt5.QtCore import Qt


def create_card_container(width=300, height=300):
    """
    Create the card container frame.
    
    Args:
        width: Card width
        height: Card height
    
    Returns:
        QFrame: The card container
    """
    container = QFrame()
    container.setFixedSize(width, height)
    container.setCursor(Qt.PointingHandCursor)
    container.setProperty("class", "module-card")
    
    return container
