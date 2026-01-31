"""
Card Stylesheet - Dark Theme
============================
"""

CARD_BACKGROUND = "#1e293b"
CARD_BORDER = "2px solid #334155"
CARD_BORDER_RADIUS = "16px"
CARD_PADDING = "25px"


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
            background-color: #334155;
        }}
    """


def get_stat_card_stylesheet(accent_color="#2563eb"):
    """Get stat card stylesheet with accent color."""
    return f"""
        QFrame {{
            background-color: {CARD_BACKGROUND};
            border: 1px solid #334155;
            border-radius: 12px;
            border-left: 4px solid {accent_color};
        }}
        
        QFrame:hover {{
            border-color: {accent_color};
        }}
    """
