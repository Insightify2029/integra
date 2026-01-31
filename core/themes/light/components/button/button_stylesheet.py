"""
Button Stylesheet - Light Theme
===============================
"""

BUTTON_BACKGROUND = "#2563eb"
BUTTON_BACKGROUND_HOVER = "#3b82f6"
BUTTON_BACKGROUND_PRESSED = "#1d4ed8"
BUTTON_BACKGROUND_DISABLED = "#cbd5e1"
BUTTON_TEXT_COLOR = "#ffffff"
BUTTON_BORDER = "none"
BUTTON_BORDER_RADIUS = "8px"
BUTTON_PADDING = "12px 24px"


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
            color: #64748b;
        }}
    """
