"""
Scrollbar Stylesheet - Dark Theme
=================================
"""

SCROLLBAR_BACKGROUND = "#1e293b"
SCROLLBAR_HANDLE = "#475569"
SCROLLBAR_HANDLE_HOVER = "#2563eb"


def get_scrollbar_stylesheet():
    """Get complete scrollbar stylesheet."""
    return f"""
        QScrollBar:vertical {{
            background-color: {SCROLLBAR_BACKGROUND};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {SCROLLBAR_HANDLE};
            border-radius: 6px;
            min-height: 30px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {SCROLLBAR_HANDLE_HOVER};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar:horizontal {{
            background-color: {SCROLLBAR_BACKGROUND};
            height: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {SCROLLBAR_HANDLE};
            border-radius: 6px;
            min-width: 30px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {SCROLLBAR_HANDLE_HOVER};
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
    """
