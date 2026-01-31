"""
Toolbar Stylesheet - Light Theme
================================
"""

TOOLBAR_BACKGROUND = "#ffffff"
TOOLBAR_BUTTON_HOVER = "#f1f5f9"
TOOLBAR_BUTTON_PRESSED = "#2563eb"


def get_toolbar_stylesheet():
    """Get complete toolbar stylesheet."""
    return f"""
        QToolBar {{
            background-color: {TOOLBAR_BACKGROUND};
            border: none;
            border-bottom: 1px solid #e2e8f0;
            padding: 5px;
            spacing: 5px;
        }}
        
        QToolBar QToolButton {{
            background-color: transparent;
            color: #1e293b;
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
            color: white;
        }}
    """
