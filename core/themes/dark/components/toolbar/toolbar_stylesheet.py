"""
Toolbar Stylesheet - Dark Theme
===============================
"""

TOOLBAR_BACKGROUND = "#1e293b"
TOOLBAR_BUTTON_HOVER = "#334155"
TOOLBAR_BUTTON_PRESSED = "#2563eb"


def get_toolbar_stylesheet():
    """Get complete toolbar stylesheet."""
    return f"""
        QToolBar {{
            background-color: {TOOLBAR_BACKGROUND};
            border: none;
            padding: 5px;
            spacing: 5px;
        }}
        
        QToolBar QToolButton {{
            background-color: transparent;
            color: #f1f5f9;
            border: none;
            border-radius: 5px;
            padding: 8px 15px;
            font-size: 13px;
            font-weight: 500;
        }}
        
        QToolBar QToolButton:hover {{
            background-color: {TOOLBAR_BUTTON_HOVER};
        }}
        
        QToolBar QToolButton:pressed {{
            background-color: {TOOLBAR_BUTTON_PRESSED};
        }}
    """
