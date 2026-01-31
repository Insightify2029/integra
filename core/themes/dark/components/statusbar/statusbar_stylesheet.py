"""
Statusbar Stylesheet - Dark Theme
=================================
"""

STATUSBAR_BACKGROUND = "#1e293b"
STATUSBAR_TEXT = "#94a3b8"
STATUSBAR_BORDER = "1px solid #334155"


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
