"""
Statusbar Stylesheet - Light Theme
==================================
"""

STATUSBAR_BACKGROUND = "#ffffff"
STATUSBAR_TEXT = "#475569"
STATUSBAR_BORDER = "1px solid #e2e8f0"


def get_statusbar_stylesheet():
    """Get complete statusbar stylesheet."""
    return f"""
        QStatusBar {{
            background-color: {STATUSBAR_BACKGROUND};
            color: {STATUSBAR_TEXT};
            border-top: {STATUSBAR_BORDER};
            font-size: 12px;
            padding: 5px;
        }}
    """
