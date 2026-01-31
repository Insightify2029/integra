"""
Menu Stylesheet - Dark Theme
============================
"""

MENU_BACKGROUND = "#1e293b"
MENU_TEXT_COLOR = "#f1f5f9"
MENU_ITEM_HOVER = "#2563eb"
MENU_ITEM_SELECTED = "#1d4ed8"
MENU_BORDER = "1px solid #334155"


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
        }}
        
        QMenuBar::item:pressed {{
            background-color: {MENU_ITEM_SELECTED};
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
        }}
        
        QMenu::separator {{
            height: 1px;
            background-color: #334155;
            margin: 5px 10px;
        }}
    """
