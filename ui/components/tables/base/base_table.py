"""
Base Table Widget
=================
Reusable table component.
"""

from PyQt5.QtWidgets import QTableWidget, QAbstractItemView
from PyQt5.QtCore import Qt

from core.themes import get_current_theme
from core.themes.dark.components.table import get_table_stylesheet as get_dark_table
from core.themes.light.components.table import get_table_stylesheet as get_light_table


class BaseTable(QTableWidget):
    """
    Base table widget with styling.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_table()
    
    def _setup_table(self):
        """Setup table settings."""
        # Selection
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        
        # Appearance
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.setSortingEnabled(True)
        self.setAlternatingRowColors(False)  # As requested by user
        
        # Apply theme
        self._apply_theme()
    
    def _apply_theme(self):
        """Apply current theme to table."""
        theme = get_current_theme()
        if theme == 'dark':
            self.setStyleSheet(get_dark_table())
        else:
            self.setStyleSheet(get_light_table())
    
    def set_columns(self, columns: list):
        """
        Set table columns.
        
        Args:
            columns: List of column headers
        """
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
    
    def set_data(self, data: list):
        """
        Set table data.
        
        Args:
            data: List of row tuples
        """
        from PyQt5.QtWidgets import QTableWidgetItem
        
        self.setRowCount(len(data))
        
        for row_idx, row_data in enumerate(data):
            for col_idx, value in enumerate(row_data):
                item = QTableWidgetItem(str(value) if value else "")
                item.setTextAlignment(Qt.AlignCenter)
                self.setItem(row_idx, col_idx, item)
        
        self.resizeColumnsToContents()
    
    def filter_rows(self, text: str):
        """
        Filter table rows by text.
        
        Args:
            text: Search text
        """
        text = text.lower()
        for row in range(self.rowCount()):
            match = False
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.setRowHidden(row, not match)
