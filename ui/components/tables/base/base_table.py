"""
Base Table Widget
=================
Reusable table component. Styling handled by centralized theme system.
"""

from PyQt5.QtWidgets import QTableWidget, QAbstractItemView
from PyQt5.QtCore import Qt


class BaseTable(QTableWidget):
    """
    Base table widget with styling.
    App-level QSS handles QTableWidget styling automatically.
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

        # Theme is applied at QApplication level - no per-widget stylesheet needed

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
