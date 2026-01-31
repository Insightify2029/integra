"""
Button Stylesheet - Dark Theme
==============================
Combines all button properties into QSS.
"""

from .button_background import BUTTON_BACKGROUND
from .button_background_hover import BUTTON_BACKGROUND_HOVER
from .button_background_pressed import BUTTON_BACKGROUND_PRESSED
from .button_background_disabled import BUTTON_BACKGROUND_DISABLED
from .button_text_color import BUTTON_TEXT_COLOR
from .button_border import BUTTON_BORDER
from .button_border_radius import BUTTON_BORDER_RADIUS
from .button_padding import BUTTON_PADDING


def get_button_stylesheet():
    """Get complete button stylesheet."""
    return f"""
        QPushButton {{
            background-color: {BUTTON_BACKGROUND};
            color: {BUTTON_TEXT_COLOR};
            border: {BUTTON_BORDER};
            border-radius: {BUTTON_BORDER_RADIUS};
            padding: {BUTTON_PADDING};
            font-size: 14px;
            font-weight: 500;
        }}
        
        QPushButton:hover {{
            background-color: {BUTTON_BACKGROUND_HOVER};
        }}
        
        QPushButton:pressed {{
            background-color: {BUTTON_BACKGROUND_PRESSED};
        }}
        
        QPushButton:disabled {{
            background-color: {BUTTON_BACKGROUND_DISABLED};
            color: #94a3b8;
        }}
    """
