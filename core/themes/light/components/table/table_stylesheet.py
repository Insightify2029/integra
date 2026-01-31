"""
Table Stylesheet - Light Theme
==============================
White background + Black borders + Black text
As requested by user.
"""

TABLE_BACKGROUND = "#ffffff"
TABLE_TEXT_COLOR = "#000000"
TABLE_BORDER = "1px solid #000000"
TABLE_HEADER_BACKGROUND = "#f1f5f9"
TABLE_HEADER_TEXT = "#000000"
TABLE_ROW_SELECTED = "#2563eb"
TABLE_ROW_HOVER = "#f1f5f9"
TABLE_GRIDLINE = "#000000"


def get_table_stylesheet():
    """Get complete table stylesheet."""
    return f"""
        QTableWidget, QTableView {{
            background-color: {TABLE_BACKGROUND};
            color: {TABLE_TEXT_COLOR};
            border: {TABLE_BORDER};
            border-radius: 4px;
            gridline-color: {TABLE_GRIDLINE};
            font-size: 13px;
        }}
        
        QTableWidget::item, QTableView::item {{
            padding: 10px;
            border: 1px solid {TABLE_GRIDLINE};
        }}
        
        QTableWidget::item:selected, QTableView::item:selected {{
            background-color: {TABLE_ROW_SELECTED};
            color: white;
        }}
        
        QTableWidget::item:hover, QTableView::item:hover {{
            background-color: {TABLE_ROW_HOVER};
        }}
        
        QHeaderView::section {{
            background-color: {TABLE_HEADER_BACKGROUND};
            color: {TABLE_HEADER_TEXT};
            font-weight: 600;
            font-size: 13px;
            padding: 12px;
            border: 1px solid {TABLE_GRIDLINE};
        }}
    """
