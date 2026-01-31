"""
Module Card Layout
==================
Arranges elements in the module card.
"""

from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtCore import Qt


def create_card_layout():
    """
    Create the card layout.
    
    Returns:
        QVBoxLayout: The layout
    """
    layout = QVBoxLayout()
    layout.setContentsMargins(15, 20, 15, 20)
    layout.setSpacing(10)
    layout.setAlignment(Qt.AlignCenter)
    
    return layout
