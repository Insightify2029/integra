"""
Menu Stylesheet - Light Theme
=============================
"""

MENU_BACKGROUND = "#ffffff"
MENU_TEXT_COLOR = "#1e293b"
MENU_ITEM_HOVER = "#2563eb"
MENU_BORDER = "1px solid #e2e8f0"


def get_menu_stylesheet():
    """Get complete menu stylesheet."""
    return f"""
        QMenuBar {{
            background-color: {MENU_BACKGROUND};
            color: {MENU_TEXT_COLOR};
            font-size: 14px;
            font-weight: 500;
            padding: 5px;
            border-bottom: {MENU_BORDER};
        }}
        
        QMenuBar::item {{
            padding: 8px 15px;
            border-radius: 5px;
            margin: 2px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {MENU_ITEM_HOVER};
            color: white;
        }}
        
        QMenu {{
            background-color: {MENU_BACKGROUND};
            color: {MENU_TEXT_COLOR};
            border: {MENU_BORDER};
            border-radius: 8px;
            padding: 5px;
        }}
        
        QMenu::item {{
            padding: 10px 30px;
            border-radius: 5px;
            margin: 2px;
        }}
        
        QMenu::item:selected {{
            background-color: {MENU_ITEM_HOVER};
            color: white;
        }}
        
        QMenu::separator {{
            height: 1px;
            background-color: #e2e8f0;
            margin: 5px 10px;
        }}
    """
