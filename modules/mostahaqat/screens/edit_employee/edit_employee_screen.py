# -*- coding: utf-8 -*-
"""
Edit Employee Screen
====================
\u0634\u0627\u0634\u0629 \u062a\u0639\u062f\u064a\u0644 \u0628\u064a\u0627\u0646\u0627\u062a \u0627\u0644\u0645\u0648\u0638\u0641
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGridLayout, QScrollArea,
    QLineEdit, QComboBox, QDateEdit
)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QFont

from core.themes import get_current_theme
from core.database.queries import select_all, update
from ui.components.notifications import toast_success, toast_error, toast_warning


class EditEmployeeScreen(QWidget):
    """Edit Employee Screen."""
    
    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()
    
    def __init__(self, employee_data: dict = None, parent=None):
        super().__init__(parent)
        self._employee = employee_data or {}
        self._dropdowns_data = {}
        self._inputs = {}
        
        self._setup_ui()
        self._apply_theme()
        self._load_dropdowns()
        
        if employee_data:
            self.set_employee(employee_data)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header = QHBoxLayout()
        
        self._back_btn = QPushButton("\u2192 \u0631\u062c\u0648\u0639")
        self._back_btn.setCursor(Qt.PointingHandCursor)
        self._back_btn.setFont(QFont("Cairo", 12))
        self._back_btn.setObjectName("backButton")
        self._back_btn.clicked.connect(self._on_cancel)
        header.addWidget(self._back_btn)
        
        self._title_label = QLabel("\U0001f4dd \u062a\u0639\u062f\u064a\u0644 \u0628\u064a\u0627\u0646\u0627\u062a \u0627\u0644\u0645\u0648\u0638\u0641")
        self._title_label.setFont(QFont("Cairo", 20, QFont.Bold))
        self._title_label.setAlignment(Qt.AlignCenter)
        self._title_label.setObjectName("screenTitle")
        header.addWidget(self._title_label, 1)
        
        spacer = QWidget()
        spacer.setFixedWidth(80)
        header.addWidget(spacer)
        
        layout.addLayout(header)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setObjectName("editScroll")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(20)
        
        # Basic Info Card
        basic_card = self._create_card("\U0001f4cb \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a \u0627\u0644\u0623\u0633\u0627\u0633\u064a\u0629")
        basic_grid = QGridLayout()
        basic_grid.setSpacing(15)
        basic_grid.setColumnStretch(1, 1)
        basic_grid.setColumnStretch(3, 1)
        
        self._inputs['employee_code'] = self._add_input(basic_grid, "\u0643\u0648\u062f \u0627\u0644\u0645\u0648\u0638\u0641", 0, 0, readonly=True)
        self._inputs['status_id'] = self._add_combo(basic_grid, "\u0627\u0644\u062d\u0627\u0644\u0629", 0, 1)
        self._inputs['name_ar'] = self._add_input(basic_grid, "\u0627\u0644\u0627\u0633\u0645 \u0628\u0627\u0644\u0639\u0631\u0628\u064a", 1, 0)
        self._inputs['name_en'] = self._add_input(basic_grid, "\u0627\u0644\u0627\u0633\u0645 \u0628\u0627\u0644\u0625\u0646\u062c\u0644\u064a\u0632\u064a", 1, 1)
        self._inputs['national_id'] = self._add_input(basic_grid, "\u0631\u0642\u0645 \u0627\u0644\u0647\u0648\u064a\u0629", 2, 0)
        self._inputs['nationality_id'] = self._add_combo(basic_grid, "\u0627\u0644\u062c\u0646\u0633\u064a\u0629", 2, 1)
        self._inputs['hire_date'] = self._add_date(basic_grid, "\u062a\u0627\u0631\u064a\u062e \u0627\u0644\u062a\u0639\u064a\u064a\u0646", 3, 0)
        
        basic_card.layout().addLayout(basic_grid)
        scroll_layout.addWidget(basic_card)
        
        # Job Info Card
        job_card = self._create_card("\U0001f4bc \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a \u0627\u0644\u0648\u0638\u064a\u0641\u064a\u0629")
        job_grid = QGridLayout()
        job_grid.setSpacing(15)
        job_grid.setColumnStretch(1, 1)
        job_grid.setColumnStretch(3, 1)
        
        self._inputs['company_id'] = self._add_combo(job_grid, "\u0627\u0644\u0634\u0631\u0643\u0629", 0, 0)
        self._inputs['department_id'] = self._add_combo(job_grid, "\u0627\u0644\u0642\u0633\u0645", 0, 1)
        self._inputs['job_title_id'] = self._add_combo(job_grid, "\u0627\u0644\u0648\u0638\u064a\u0641\u0629", 1, 0)
        
        job_card.layout().addLayout(job_grid)
        scroll_layout.addWidget(job_card)
        
        # Bank Info Card
        bank_card = self._create_card("\U0001f3e6 \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a \u0627\u0644\u0628\u0646\u0643\u064a\u0629")
        bank_grid = QGridLayout()
        bank_grid.setSpacing(15)
        bank_grid.setColumnStretch(1, 1)
        bank_grid.setColumnStretch(3, 1)
        
        self._inputs['bank_id'] = self._add_combo(bank_grid, "\u0627\u0644\u0628\u0646\u0643", 0, 0)
        self._inputs['iban'] = self._add_input(bank_grid, "IBAN", 0, 1)
        
        bank_card.layout().addLayout(bank_grid)
        scroll_layout.addWidget(bank_card)
        
        # Save/Cancel Buttons
        buttons_frame = QFrame()
        buttons_frame.setObjectName("buttonsFrame")
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setContentsMargins(20, 15, 20, 15)
        buttons_layout.setSpacing(15)
        
        buttons_layout.addStretch()
        
        self._cancel_btn = QPushButton("\u274c \u0625\u0644\u063a\u0627\u0621")
        self._cancel_btn.setCursor(Qt.PointingHandCursor)
        self._cancel_btn.setFont(QFont("Cairo", 13))
        self._cancel_btn.setMinimumHeight(50)
        self._cancel_btn.setMinimumWidth(160)
        self._cancel_btn.setProperty("buttonColor", "danger")
        self._cancel_btn.clicked.connect(self._on_cancel)
        buttons_layout.addWidget(self._cancel_btn)
        
        self._save_btn = QPushButton("\u2705 \u062d\u0641\u0638 \u0627\u0644\u062a\u0639\u062f\u064a\u0644\u0627\u062a")
        self._save_btn.setCursor(Qt.PointingHandCursor)
        self._save_btn.setFont(QFont("Cairo", 13, QFont.Bold))
        self._save_btn.setMinimumHeight(50)
        self._save_btn.setMinimumWidth(200)
        self._save_btn.setProperty("buttonColor", "success")
        self._save_btn.clicked.connect(self._on_save)
        buttons_layout.addWidget(self._save_btn)
        
        buttons_layout.addStretch()
        
        scroll_layout.addWidget(buttons_frame)
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
    
    def _create_card(self, title):
        card = QFrame()
        card.setObjectName("editCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 20)
        layout.setSpacing(15)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Cairo", 14, QFont.Bold))
        title_label.setObjectName("cardTitle")
        layout.addWidget(title_label)
        
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("cardSeparator")
        layout.addWidget(sep)
        
        return card
    
    def _add_input(self, grid, label, row, col, readonly=False):
        lbl = QLabel(f"{label}:")
        lbl.setFont(QFont("Cairo", 11))
        lbl.setObjectName("fieldLabel")
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        inp = QLineEdit()
        inp.setFont(QFont("Cairo", 12))
        inp.setMinimumHeight(40)
        inp.setObjectName("fieldInput")
        inp.setPlaceholderText(f"\u0623\u062f\u062e\u0644 {label}")
        
        if readonly:
            inp.setReadOnly(True)
            inp.setObjectName("fieldInputReadonly")
        
        col_offset = col * 2
        grid.addWidget(lbl, row, col_offset)
        grid.addWidget(inp, row, col_offset + 1)
        return inp
    
    def _add_combo(self, grid, label, row, col):
        lbl = QLabel(f"{label}:")
        lbl.setFont(QFont("Cairo", 11))
        lbl.setObjectName("fieldLabel")
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        combo = QComboBox()
        combo.setFont(QFont("Cairo", 12))
        combo.setMinimumHeight(40)
        combo.setObjectName("fieldCombo")
        
        col_offset = col * 2
        grid.addWidget(lbl, row, col_offset)
        grid.addWidget(combo, row, col_offset + 1)
        return combo
    
    def _add_date(self, grid, label, row, col):
        lbl = QLabel(f"{label}:")
        lbl.setFont(QFont("Cairo", 11))
        lbl.setObjectName("fieldLabel")
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        date_edit = QDateEdit()
        date_edit.setFont(QFont("Cairo", 12))
        date_edit.setMinimumHeight(40)
        date_edit.setObjectName("fieldDate")
        date_edit.setCalendarPopup(True)
        date_edit.setDisplayFormat("yyyy-MM-dd")
        date_edit.setDate(QDate.currentDate())
        
        col_offset = col * 2
        grid.addWidget(lbl, row, col_offset)
        grid.addWidget(date_edit, row, col_offset + 1)
        return date_edit
    
    def _load_dropdowns(self):
        self._load_combo(self._inputs['nationality_id'], "SELECT id, name_ar FROM nationalities ORDER BY name_ar", 'nationalities')
        self._load_combo(self._inputs['department_id'], "SELECT id, name_en FROM departments ORDER BY name_en", 'departments')
        self._load_combo(self._inputs['job_title_id'], "SELECT id, name_ar FROM job_titles ORDER BY name_ar", 'job_titles')
        self._load_combo(self._inputs['bank_id'], "SELECT id, name_en FROM banks ORDER BY name_en", 'banks')
        self._load_combo(self._inputs['company_id'], "SELECT id, name_en FROM companies ORDER BY name_en", 'companies')
        self._load_combo(self._inputs['status_id'], "SELECT id, name_ar FROM employee_statuses ORDER BY id", 'statuses')
    
    def _load_combo(self, combo, query, key):
        try:
            columns, rows = select_all(query)
            self._dropdowns_data[key] = {}
            combo.clear()
            combo.addItem("-- \u0627\u062e\u062a\u0631 --", 0)
            for row in rows:
                item_id = row[0]
                item_name = str(row[1]) if row[1] else ""
                combo.addItem(item_name, item_id)
                self._dropdowns_data[key][item_id] = item_name
        except Exception as e:
            print(f"Error loading {key}: {e}")
    
    def set_employee(self, data):
        self._employee = data
        name = data.get('name_ar', data.get('name_en', ''))
        self._title_label.setText(f"\U0001f4dd \u062a\u0639\u062f\u064a\u0644 \u0628\u064a\u0627\u0646\u0627\u062a: {name}")
        
        self._inputs['employee_code'].setText(str(data.get('employee_code', '')))
        self._inputs['name_ar'].setText(str(data.get('name_ar', '')))
        self._inputs['name_en'].setText(str(data.get('name_en', '')))
        self._inputs['national_id'].setText(str(data.get('national_id', '')))
        self._inputs['iban'].setText(str(data.get('iban', '')))
        
        hire_date = data.get('hire_date')
        if hire_date:
            try:
                date_str = str(hire_date)
                if '-' in date_str:
                    parts = date_str.split('-')
                    self._inputs['hire_date'].setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2][:2])))
            except Exception:
                pass
        
        self._select_combo_by_text(self._inputs['nationality_id'], data.get('nationality', ''))
        self._select_combo_by_text(self._inputs['department_id'], data.get('department', ''))
        self._select_combo_by_text(self._inputs['job_title_id'], data.get('job_title', ''))
        self._select_combo_by_text(self._inputs['bank_id'], data.get('bank', ''))
        self._select_combo_by_text(self._inputs['company_id'], data.get('company', ''))
        self._select_combo_by_text(self._inputs['status_id'], data.get('status', ''))
    
    def _select_combo_by_text(self, combo, text):
        if not text:
            return
        text = str(text)
        for i in range(combo.count()):
            if combo.itemText(i) == text:
                combo.setCurrentIndex(i)
                return
    
    def _on_save(self):
        name_ar = self._inputs['name_ar'].text().strip()
        name_en = self._inputs['name_en'].text().strip()
        
        if not name_ar and not name_en:
            toast_warning(self, "تنبيه", "يجب إدخال اسم الموظف!")
            return

        employee_id = self._employee.get('id')
        if not employee_id:
            toast_error(self, "خطأ", "لم يتم تحديد الموظف!")
            return
        
        nationality_id = self._inputs['nationality_id'].currentData()
        department_id = self._inputs['department_id'].currentData()
        job_title_id = self._inputs['job_title_id'].currentData()
        bank_id = self._inputs['bank_id'].currentData()
        company_id = self._inputs['company_id'].currentData()
        status_id = self._inputs['status_id'].currentData()
        national_id = self._inputs['national_id'].text().strip()
        iban = self._inputs['iban'].text().strip()
        hire_date = self._inputs['hire_date'].date().toString("yyyy-MM-dd")
        
        query = """
        UPDATE employees SET
            name_ar = %s, name_en = %s, national_id = %s,
            nationality_id = %s, department_id = %s, job_title_id = %s,
            bank_id = %s, iban = %s, company_id = %s,
            status_id = %s, hire_date = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        
        params = (
            name_ar if name_ar else None,
            name_en if name_en else None,
            national_id if national_id else None,
            nationality_id if nationality_id and nationality_id != 0 else None,
            department_id if department_id and department_id != 0 else None,
            job_title_id if job_title_id and job_title_id != 0 else None,
            bank_id if bank_id and bank_id != 0 else None,
            iban if iban else None,
            company_id if company_id and company_id != 0 else None,
            status_id if status_id and status_id != 0 else None,
            hire_date,
            employee_id
        )
        
        success = update(query, params)
        
        if success:
            toast_success(self, "تم", "تم حفظ التعديلات بنجاح!")
            updated_data = dict(self._employee)
            updated_data['name_ar'] = name_ar
            updated_data['name_en'] = name_en
            updated_data['national_id'] = national_id
            updated_data['iban'] = iban
            updated_data['hire_date'] = hire_date
            updated_data['nationality'] = self._inputs['nationality_id'].currentText()
            updated_data['department'] = self._inputs['department_id'].currentText()
            updated_data['job_title'] = self._inputs['job_title_id'].currentText()
            updated_data['bank'] = self._inputs['bank_id'].currentText()
            updated_data['company'] = self._inputs['company_id'].currentText()
            updated_data['status'] = self._inputs['status_id'].currentText()
            self.saved.emit(updated_data)
        else:
            toast_error(self, "خطأ", "فشل حفظ التعديلات!")
    
    def _on_cancel(self):
        self.cancelled.emit()
    
    def _apply_theme(self):
        theme = get_current_theme()
        
        if theme == 'dark':
            self.setStyleSheet("""
                QWidget { background-color: #0f172a; }
                QLabel { color: #f1f5f9; background: transparent; }
                QLabel#fieldLabel { color: #94a3b8; }
                QLabel#screenTitle { color: #38bdf8; }
                QLabel#cardTitle { color: #06b6d4; }
                QFrame#editCard { background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; }
                QFrame#cardSeparator { background-color: #334155; }
                QFrame#buttonsFrame { background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; }
                QLineEdit, QLineEdit#fieldInput { background-color: #0f172a; color: #f1f5f9; border: 2px solid #334155; border-radius: 8px; padding: 8px 12px; font-size: 13px; }
                QLineEdit:focus { border-color: #06b6d4; }
                QLineEdit#fieldInputReadonly { background-color: #1e293b; color: #64748b; border: 2px solid #1e293b; }
                QComboBox { background-color: #0f172a; color: #f1f5f9; border: 2px solid #334155; border-radius: 8px; padding: 8px 12px; font-size: 13px; }
                QComboBox:focus { border-color: #06b6d4; }
                QComboBox::drop-down { border: none; width: 30px; }
                QComboBox QAbstractItemView { background-color: #1e293b; color: #f1f5f9; border: 1px solid #334155; selection-background-color: #06b6d4; }
                QDateEdit { background-color: #0f172a; color: #f1f5f9; border: 2px solid #334155; border-radius: 8px; padding: 8px 12px; font-size: 13px; }
                QDateEdit:focus { border-color: #06b6d4; }
                QPushButton { background-color: #334155; color: #f1f5f9; border: none; border-radius: 8px; padding: 12px 24px; font-weight: bold; }
                QPushButton:hover { background-color: #475569; }
                QPushButton#backButton { background-color: transparent; color: #94a3b8; border: 1px solid #334155; }
                QPushButton#backButton:hover { background-color: #1e293b; color: #f1f5f9; }
                QPushButton[buttonColor="success"] { background-color: #10b981; }
                QPushButton[buttonColor="success"]:hover { background-color: #059669; }
                QPushButton[buttonColor="danger"] { background-color: #ef4444; }
                QPushButton[buttonColor="danger"]:hover { background-color: #dc2626; }
                QScrollArea { background: transparent; border: none; }
            """)
        else:
            self.setStyleSheet("""
                QWidget { background-color: #f8fafc; }
                QLabel { color: #1e293b; background: transparent; }
                QLabel#fieldLabel { color: #64748b; }
                QLabel#screenTitle { color: #0891b2; }
                QLabel#cardTitle { color: #0891b2; }
                QFrame#editCard { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; }
                QFrame#cardSeparator { background-color: #e2e8f0; }
                QFrame#buttonsFrame { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; }
                QLineEdit { background-color: #ffffff; color: #1e293b; border: 2px solid #e2e8f0; border-radius: 8px; padding: 8px 12px; }
                QLineEdit:focus { border-color: #06b6d4; }
                QLineEdit#fieldInputReadonly { background-color: #f1f5f9; color: #64748b; }
                QComboBox { background-color: #ffffff; color: #1e293b; border: 2px solid #e2e8f0; border-radius: 8px; padding: 8px 12px; }
                QComboBox:focus { border-color: #06b6d4; }
                QDateEdit { background-color: #ffffff; color: #1e293b; border: 2px solid #e2e8f0; border-radius: 8px; padding: 8px 12px; }
                QPushButton { background-color: #e2e8f0; color: #1e293b; border: none; border-radius: 8px; padding: 12px 24px; font-weight: bold; }
                QPushButton:hover { background-color: #cbd5e1; }
                QPushButton#backButton { background-color: transparent; color: #64748b; border: 1px solid #e2e8f0; }
                QPushButton[buttonColor="success"] { background-color: #10b981; color: #ffffff; }
                QPushButton[buttonColor="danger"] { background-color: #ef4444; color: #ffffff; }
                QScrollArea { background: transparent; border: none; }
            """)
