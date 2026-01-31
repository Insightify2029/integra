"""
Card Stylesheet - Light Theme
=============================
"""

CARD_BACKGROUND = "#ffffff"
CARD_BORDER = "2px solid #e2e8f0"
CARD_BORDER_RADIUS = "16px"


def get_card_stylesheet(accent_color="#2563eb"):
    """Get card stylesheet with optional accent color."""
    return f"""
        QFrame[class="module-card"] {{
            background-color: {CARD_BACKGROUND};
            border: {CARD_BORDER};
            border-radius: {CARD_BORDER_RADIUS};
        }}
        
        QFrame[class="module-card"]:hover {{
            border-color: {accent_color};
            background-color: #f8fafc;
        }}
    """


def get_stat_card_stylesheet(accent_color="#2563eb"):
    """Get stat card stylesheet with accent color."""
    return f"""
        QFrame {{
            background-color: {CARD_BACKGROUND};
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            border-left: 4px solid {accent_color};
        }}
        
        QFrame:hover {{
            border-color: {accent_color};
        }}
    """
