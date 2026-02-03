"""
Employees List Table
====================
Table widget for displaying employees.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from ui.components.tables import BaseTable
from ui.components.inputs import SearchInput, StyledComboBox
from ui.components.labels import SectionLabel

from ..queries import get_all_employees


class EmployeesListTable(QWidget):
    """Employees list with table and filters."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Header row
        header = QHBoxLayout()
        
        # Title
        title = SectionLabel("📋 قائمة الموظفين")
        header.addWidget(title)
        
        header.addStretch()
        
        # Filter combo
        self.filter_combo = StyledComboBox()
        self.filter_combo.addItems(["الكل", "نشط", "غير نشط"])
        self.filter_combo.setFixedWidth(150)
        header.addWidget(self.filter_combo)
        
        # Search
        self.search_input = SearchInput("🔍 بحث...")
        self.search_input.setFixedWidth(300)
        self.search_input.textChanged.connect(self._on_search)
        header.addWidget(self.search_input)
        
        layout.addLayout(header)
        
        # Table
        self.table = BaseTable()
        layout.addWidget(self.table)
    
    def _load_data(self):
        """Load employees data."""
        columns, rows = get_all_employees()
        
        if columns and rows:
            self.table.set_columns(columns)
            self.table.set_data(rows)
    
    def _on_search(self, text):
        """Handle search input."""
        self.table.filter_rows(text)
    
    def refresh(self):
        """Refresh the data."""
        self._load_data()
