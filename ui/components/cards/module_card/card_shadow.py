"""
Module Card Shadow Effect
=========================
Drop shadow effect for the card.
"""

from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor


def create_card_shadow(blur_radius=25, x_offset=0, y_offset=8, opacity=80):
    """
    Create shadow effect for the card.
    
    Args:
        blur_radius: Shadow blur amount
        x_offset: Horizontal offset
        y_offset: Vertical offset
        opacity: Shadow opacity (0-255)
    
    Returns:
        QGraphicsDropShadowEffect: The shadow effect
    """
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur_radius)
    shadow.setXOffset(x_offset)
    shadow.setYOffset(y_offset)
    shadow.setColor(QColor(0, 0, 0, opacity))
    
    return shadow
