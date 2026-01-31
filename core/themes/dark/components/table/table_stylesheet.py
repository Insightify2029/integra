"""
Table Stylesheet - Dark Theme
=============================
Combines all table properties into QSS.
"""

from .table_background import TABLE_BACKGROUND
from .table_text_color import TABLE_TEXT_COLOR
from .table_border import TABLE_BORDER
from .table_header_background import TABLE_HEADER_BACKGROUND
from .table_header_text import TABLE_HEADER_TEXT
from .table_row_selected import TABLE_ROW_SELECTED
from .table_row_hover import TABLE_ROW_HOVER
from .table_gridline import TABLE_GRIDLINE


def get_table_stylesheet():
    """Get complete table stylesheet."""
    return f"""
        QTableWidget, QTableView {{
            background-color: {TABLE_BACKGROUND};
            color: {TABLE_TEXT_COLOR};
            border: {TABLE_BORDER};
            border-radius: 8px;
            gridline-color: {TABLE_GRIDLINE};
            font-size: 13px;
        }}
        
        QTableWidget::item, QTableView::item {{
            padding: 10px;
            border-bottom: 1px solid {TABLE_GRIDLINE};
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
            border: none;
            border-bottom: 2px solid #2563eb;
        }}
    """
