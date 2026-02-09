"""
Enterprise Table Widget
=======================
Enterprise-Grade Table

Features:
- Double-click to open details
- Multi-column sorting
- Live search
- Smart filtering
- Export (Excel/PDF/CSV)
- Column visibility toggle
- Multi-select for bulk operations
- RTL Support
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableView,
    QHeaderView, QAbstractItemView, QMenu, QAction,
    QStyledItemDelegate, QStyle, QApplication
)
from PyQt5.QtCore import (
    Qt, pyqtSignal, QSortFilterProxyModel, QModelIndex
)
from PyQt5.QtGui import (
    QStandardItemModel, QStandardItem,
    QColor
)

from core.themes import get_current_palette


class EnterpriseTableDelegate(QStyledItemDelegate):
    """
    Custom delegate for table cells.
    Handles cell styling and rendering using palette colors.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        """Custom paint for cells."""
        palette = get_current_palette()

        hover_color = QColor(palette['bg_hover'])
        selected_color = QColor(palette['selection_bg'])

        # Highlight on hover
        if option.state & QStyle.State_MouseOver:
            painter.fillRect(option.rect, hover_color)

        # Selected row
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, selected_color)

        super().paint(painter, option, index)


class EnterpriseFilterProxy(QSortFilterProxyModel):
    """
    Advanced filter proxy for enterprise table.
    Supports multi-column filtering.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._filters = {}  # column_index: filter_text
        self._global_filter = ""

    def set_global_filter(self, text: str):
        """Set global filter (searches all columns)."""
        self._global_filter = text.lower()
        self.invalidateFilter()

    def set_column_filter(self, column: int, text: str):
        """Set filter for specific column."""
        if text:
            self._filters[column] = text.lower()
        elif column in self._filters:
            del self._filters[column]
        self.invalidateFilter()

    def clear_filters(self):
        """Clear all filters."""
        self._filters.clear()
        self._global_filter = ""
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        """Check if row matches filters."""
        model = self.sourceModel()

        # Global filter - search all columns
        if self._global_filter:
            match = False
            for col in range(model.columnCount()):
                index = model.index(source_row, col, source_parent)
                data = model.data(index)
                if data and self._global_filter in str(data).lower():
                    match = True
                    break
            if not match:
                return False

        # Column-specific filters
        for col, filter_text in self._filters.items():
            index = model.index(source_row, col, source_parent)
            data = model.data(index)
            if not data or filter_text not in str(data).lower():
                return False

        return True


class EnterpriseTable(QWidget):
    """
    Enterprise-Grade Table Widget.

    Signals:
        row_double_clicked(dict): Emitted when row is double-clicked
        row_selected(dict): Emitted when row is selected
        selection_changed(list): Emitted when selection changes
        data_changed(): Emitted when data is modified
    """

    # Signals
    row_double_clicked = pyqtSignal(dict)
    row_selected = pyqtSignal(dict)
    selection_changed = pyqtSignal(list)
    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Data
        self._columns = []
        self._data = []
        self._column_keys = []  # Internal column identifiers

        # Models
        self._model = QStandardItemModel()
        self._proxy = EnterpriseFilterProxy()
        self._proxy.setSourceModel(self._model)

        # Setup UI
        self._setup_ui()
        self._setup_connections()
        # App-level QSS handles QTableView styling automatically

    def _setup_ui(self):
        """Setup the table UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Table View
        self._table = QTableView()
        self._table.setModel(self._proxy)

        # Selection
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.ExtendedSelection)

        # Appearance
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self._table.setSortingEnabled(True)
        self._table.setAlternatingRowColors(False)
        self._table.setShowGrid(True)

        # Enable mouse tracking for hover effects
        self._table.setMouseTracking(True)
        self._table.viewport().setMouseTracking(True)

        # Set delegate
        self._delegate = EnterpriseTableDelegate(self._table)
        self._table.setItemDelegate(self._delegate)

        # Context menu
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)

        layout.addWidget(self._table)

    def _setup_connections(self):
        """Setup signal connections."""
        # Double click
        self._table.doubleClicked.connect(self._on_double_click)

        # Selection changed
        self._table.selectionModel().selectionChanged.connect(self._on_selection_changed)

        # Context menu
        self._table.customContextMenuRequested.connect(self._show_context_menu)

    # ===================================================================
    # Public API
    # ===================================================================

    def set_columns(self, columns: list, keys: list = None):
        """
        Set table columns.

        Args:
            columns: List of column display names
            keys: List of column keys (for data access)
        """
        self._columns = columns
        self._column_keys = keys or columns
        self._model.setHorizontalHeaderLabels(columns)

    def set_data(self, data: list):
        """
        Set table data.

        Args:
            data: List of dictionaries or tuples
        """
        self._data = data
        self._model.removeRows(0, self._model.rowCount())

        for row_data in data:
            row_items = []

            if isinstance(row_data, dict):
                for key in self._column_keys:
                    value = row_data.get(key, "")
                    item = QStandardItem(str(value) if value is not None else "")
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setEditable(False)
                    row_items.append(item)
            else:
                # Tuple or list
                for value in row_data:
                    item = QStandardItem(str(value) if value is not None else "")
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setEditable(False)
                    row_items.append(item)

            self._model.appendRow(row_items)

        # Auto-resize columns
        self._table.resizeColumnsToContents()

        # Set minimum column width
        for col in range(self._model.columnCount()):
            if self._table.columnWidth(col) < 100:
                self._table.setColumnWidth(col, 100)

    def get_selected_rows(self) -> list:
        """Get list of selected row data as dictionaries."""
        selected = []
        for index in self._table.selectionModel().selectedRows():
            source_index = self._proxy.mapToSource(index)
            row = source_index.row()
            if row < len(self._data):
                selected.append(self._data[row])
        return selected

    def get_selected_row(self) -> dict:
        """Get single selected row data."""
        rows = self.get_selected_rows()
        return rows[0] if rows else None

    def filter(self, text: str):
        """Apply global filter."""
        self._proxy.set_global_filter(text)

    def filter_column(self, column: int, text: str):
        """Apply filter to specific column."""
        self._proxy.set_column_filter(column, text)

    def clear_filters(self):
        """Clear all filters."""
        self._proxy.clear_filters()

    def refresh(self):
        """Refresh table display."""
        self._proxy.invalidate()
        self._table.viewport().update()

    def get_row_count(self) -> int:
        """Get total row count."""
        return self._model.rowCount()

    def get_visible_row_count(self) -> int:
        """Get visible (filtered) row count."""
        return self._proxy.rowCount()

    def select_row(self, row: int):
        """Select a specific row."""
        index = self._proxy.index(row, 0)
        self._table.selectRow(index.row())

    def clear_selection(self):
        """Clear current selection."""
        self._table.clearSelection()

    def hide_column(self, column: int):
        """Hide a column."""
        self._table.hideColumn(column)

    def show_column(self, column: int):
        """Show a hidden column."""
        self._table.showColumn(column)

    def is_column_hidden(self, column: int) -> bool:
        """Check if column is hidden."""
        return self._table.isColumnHidden(column)

    def get_column_count(self) -> int:
        """Get column count."""
        return self._model.columnCount()

    def get_all_data(self) -> list:
        """Get all table data."""
        return self._data.copy()

    # ===================================================================
    # Private Methods
    # ===================================================================

    def _on_double_click(self, index: QModelIndex):
        """Handle double click on row."""
        source_index = self._proxy.mapToSource(index)
        row = source_index.row()

        if row < len(self._data):
            row_data = self._data[row]
            if isinstance(row_data, dict):
                self.row_double_clicked.emit(row_data)
            else:
                # Convert tuple to dict
                data_dict = {}
                for i, key in enumerate(self._column_keys):
                    if i < len(row_data):
                        data_dict[key] = row_data[i]
                self.row_double_clicked.emit(data_dict)

    def _on_selection_changed(self, selected, deselected):
        """Handle selection change."""
        rows = self.get_selected_rows()
        self.selection_changed.emit(rows)

        if len(rows) == 1:
            self.row_selected.emit(rows[0])

    def _show_context_menu(self, position):
        """Show context menu."""
        menu = QMenu(self)

        # Get selected rows
        selected = self.get_selected_rows()

        if selected:
            # Open action
            open_action = QAction("\U0001f4c2 \u0641\u062a\u062d", self)
            open_action.triggered.connect(lambda: self.row_double_clicked.emit(selected[0]))
            menu.addAction(open_action)

            menu.addSeparator()

            # Copy action
            copy_action = QAction("\U0001f4cb \u0646\u0633\u062e", self)
            copy_action.setShortcut("Ctrl+C")
            copy_action.triggered.connect(self._copy_selected)
            menu.addAction(copy_action)

        menu.addSeparator()

        # Select all
        select_all = QAction("\u2611\ufe0f \u062a\u062d\u062f\u064a\u062f \u0627\u0644\u0643\u0644", self)
        select_all.setShortcut("Ctrl+A")
        select_all.triggered.connect(self._table.selectAll)
        menu.addAction(select_all)

        menu.exec_(self._table.viewport().mapToGlobal(position))

    def _copy_selected(self):
        """Copy selected rows to clipboard."""
        selected = self.get_selected_rows()
        if not selected:
            return

        # Build text
        lines = []

        # Header
        lines.append("\t".join(self._columns))

        # Data
        for row in selected:
            if isinstance(row, dict):
                values = [str(row.get(k, "")) for k in self._column_keys]
            else:
                values = [str(v) for v in row]
            lines.append("\t".join(values))

        text = "\n".join(lines)

        # Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
