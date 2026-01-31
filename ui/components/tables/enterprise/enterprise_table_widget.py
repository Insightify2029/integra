"""
Enterprise Table Widget (Complete)
==================================
الجدول فائق التطور - الويدجت الكامل
يجمع كل المكونات في ويدجت واحد سهل الاستخدام

Usage / طريقة الاستخدام:
    table = EnterpriseTableWidget()
    table.set_title("قائمة الموظفين")
    table.set_columns(["الكود", "الاسم", "القسم"], ["code", "name", "dept"])
    table.set_data(employees_data)
    table.row_double_clicked.connect(self.on_employee_selected)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from .enterprise_table import EnterpriseTable
from .table_toolbar import TableToolbar
from .filter_panel import FilterPanel
from .column_chooser import ColumnChooser
from .export_manager import ExportManager


class EnterpriseTableWidget(QWidget):
    """
    Complete Enterprise Table Widget.
    Combines toolbar, table, and filter panel.
    
    Signals:
        row_double_clicked(dict): Row double-clicked
        row_selected(dict): Row selected
        selection_changed(list): Selection changed
        add_clicked(): Add button clicked
    """
    
    # Signals
    row_double_clicked = pyqtSignal(dict)
    row_selected = pyqtSignal(dict)
    selection_changed = pyqtSignal(list)
    add_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._columns = []
        self._column_keys = []
        self._show_filter_panel = False
        
        self._setup_ui()
        self._setup_connections()
    
    def _setup_ui(self):
        """Setup widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        self._toolbar = TableToolbar()
        layout.addWidget(self._toolbar)
        
        # Content area (table + filter panel)
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Table
        self._table = EnterpriseTable()
        content_layout.addWidget(self._table, 1)
        
        # Filter panel (hidden by default)
        self._filter_panel = FilterPanel([])
        self._filter_panel.setVisible(False)
        self._filter_panel.setFixedWidth(350)
        content_layout.addWidget(self._filter_panel)
        
        layout.addLayout(content_layout, 1)
    
    def _setup_connections(self):
        """Setup signal connections."""
        # Toolbar signals
        self._toolbar.search_changed.connect(self._on_search)
        self._toolbar.filter_clicked.connect(self._toggle_filter_panel)
        self._toolbar.columns_clicked.connect(self._show_column_chooser)
        self._toolbar.export_clicked.connect(self._show_export_dialog)
        self._toolbar.refresh_clicked.connect(self._refresh)
        self._toolbar.add_clicked.connect(self.add_clicked.emit)
        
        # Table signals
        self._table.row_double_clicked.connect(self.row_double_clicked.emit)
        self._table.row_selected.connect(self.row_selected.emit)
        self._table.selection_changed.connect(self.selection_changed.emit)
        
        # Filter panel signals
        self._filter_panel.filter_changed.connect(self._on_column_filter)
        self._filter_panel.filters_cleared.connect(self._on_filters_cleared)
    
    # ═══════════════════════════════════════════════════════════════
    # Public API
    # ═══════════════════════════════════════════════════════════════
    
    def set_title(self, title: str):
        """Set table title."""
        self._toolbar.set_title(title)
    
    def set_columns(self, columns: list, keys: list = None):
        """
        Set table columns.
        
        Args:
            columns: Display names
            keys: Data keys (optional)
        """
        self._columns = columns
        self._column_keys = keys or columns
        self._table.set_columns(columns, keys)
        
        # Update filter panel
        self._filter_panel = FilterPanel(columns)
        self._filter_panel.setVisible(self._show_filter_panel)
        self._filter_panel.setFixedWidth(350)
        self._filter_panel.filter_changed.connect(self._on_column_filter)
        self._filter_panel.filters_cleared.connect(self._on_filters_cleared)
    
    def set_data(self, data: list):
        """Set table data."""
        self._table.set_data(data)
        self._update_row_count()
    
    def get_selected_rows(self) -> list:
        """Get selected rows."""
        return self._table.get_selected_rows()
    
    def get_selected_row(self) -> dict:
        """Get single selected row."""
        return self._table.get_selected_row()
    
    def get_all_data(self) -> list:
        """Get all data."""
        return self._table.get_all_data()
    
    def refresh(self):
        """Refresh table."""
        self._table.refresh()
        self._update_row_count()
    
    def clear_selection(self):
        """Clear selection."""
        self._table.clear_selection()
    
    def show_add_button(self, show: bool = True, text: str = "➕ إضافة"):
        """Show/hide add button."""
        self._toolbar.show_add_button(show)
        self._toolbar.set_add_button_text(text)
    
    def set_search_placeholder(self, text: str):
        """Set search placeholder."""
        self._toolbar.set_search_placeholder(text)
    
    # ═══════════════════════════════════════════════════════════════
    # Private Methods
    # ═══════════════════════════════════════════════════════════════
    
    def _update_row_count(self):
        """Update row count in toolbar."""
        total = self._table.get_row_count()
        visible = self._table.get_visible_row_count()
        self._toolbar.set_row_count(total, visible)
    
    def _on_search(self, text: str):
        """Handle search."""
        self._table.filter(text)
        self._update_row_count()
    
    def _toggle_filter_panel(self):
        """Toggle filter panel visibility."""
        self._show_filter_panel = not self._show_filter_panel
        self._filter_panel.setVisible(self._show_filter_panel)
    
    def _show_column_chooser(self):
        """Show column chooser dialog."""
        hidden = []
        for i in range(self._table.get_column_count()):
            if self._table.is_column_hidden(i):
                hidden.append(i)
        
        dialog = ColumnChooser(self._columns, hidden, self)
        dialog.columns_changed.connect(self._apply_column_visibility)
        dialog.exec_()
    
    def _apply_column_visibility(self, changes: list):
        """Apply column visibility changes."""
        for col_idx, visible in changes:
            if visible:
                self._table.show_column(col_idx)
            else:
                self._table.hide_column(col_idx)
    
    def _show_export_dialog(self):
        """Show export dialog."""
        data = self._table.get_all_data()
        if not data:
            from ui.dialogs import show_warning
            show_warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return
        
        dialog = ExportManager(data, self._columns, self)
        dialog.exec_()
    
    def _refresh(self):
        """Refresh table."""
        self._table.refresh()
        self._update_row_count()
    
    def _on_column_filter(self, column: int, text: str):
        """Handle column filter."""
        self._table.filter_column(column, text)
        self._update_row_count()
    
    def _on_filters_cleared(self):
        """Handle filters cleared."""
        self._table.clear_filters()
        self._update_row_count()
