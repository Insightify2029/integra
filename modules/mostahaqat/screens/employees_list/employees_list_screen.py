"""
Employees List Screen
=====================
شاشة قائمة الموظفين - تستخدم الجدول فائق التطور

Features:
- Enterprise-grade table
- Double-click to open employee profile
- Search, filter, export
- Add new employee button
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import pyqtSignal

from ui.components.tables.enterprise import EnterpriseTableWidget
from core.database.queries import select_all


class EmployeesListScreen(QWidget):
    """
    Employees List Screen.
    Shows all employees in an enterprise-grade table.
    
    Signals:
        employee_selected(dict): Employee double-clicked
        add_employee_clicked(): Add button clicked
    """
    
    employee_selected = pyqtSignal(dict)
    add_employee_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Setup screen UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(0)
        
        # Enterprise Table
        self._table = EnterpriseTableWidget()
        self._table.set_title("👥 قائمة الموظفين")
        self._table.set_search_placeholder("🔍 بحث بالاسم أو الكود...")
        self._table.show_add_button(True, "➕ إضافة موظف")
        
        # Set columns
        columns = [
            "الكود",
            "الاسم بالعربي",
            "الاسم بالإنجليزي", 
            "الجنسية",
            "القسم",
            "الوظيفة",
            "البنك",
            "IBAN",
            "تاريخ التعيين",
            "الشركة",
            "الحالة"
        ]
        
        keys = [
            "employee_code",
            "name_ar",
            "name_en",
            "nationality",
            "department",
            "job_title",
            "bank",
            "iban",
            "hire_date",
            "company",
            "status"
        ]
        
        self._table.set_columns(columns, keys)
        
        # Connect signals
        self._table.row_double_clicked.connect(self.employee_selected.emit)
        self._table.add_clicked.connect(self.add_employee_clicked.emit)
        
        layout.addWidget(self._table)
    
    def _load_data(self):
        """Load employees from database."""
        query = """
        SELECT 
            e.employee_code,
            e.name_ar,
            e.name_en,
            n.name_ar as nationality,
            d.name_en as department,
            j.name_ar as job_title,
            b.name_en as bank,
            e.iban,
            e.hire_date,
            c.name_en as company,
            s.name_ar as status,
            e.id
        FROM employees e
        LEFT JOIN nationalities n ON e.nationality_id = n.id
        LEFT JOIN departments d ON e.department_id = d.id
        LEFT JOIN job_titles j ON e.job_title_id = j.id
        LEFT JOIN banks b ON e.bank_id = b.id
        LEFT JOIN companies c ON e.company_id = c.id
        LEFT JOIN employee_statuses s ON e.status_id = s.id
        ORDER BY e.employee_code
        """
        
        columns, rows = select_all(query)
        
        if rows:
            # Convert to list of dicts
            data = []
            for row in rows:
                data.append({
                    'employee_code': row[0],
                    'name_ar': row[1],
                    'name_en': row[2],
                    'nationality': row[3],
                    'department': row[4],
                    'job_title': row[5],
                    'bank': row[6],
                    'iban': row[7],
                    'hire_date': row[8],
                    'company': row[9],
                    'status': row[10],
                    'id': row[11]  # Hidden, for reference
                })
            
            self._table.set_data(data)
    
    def refresh(self):
        """Refresh employee list."""
        self._load_data()
    
    def get_selected_employee(self) -> dict:
        """Get currently selected employee."""
        return self._table.get_selected_row()
