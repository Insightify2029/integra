"""
Employee Profile Screen
=======================
شاشة ملف الموظف الكاملة

Features:
- All employee data displayed
- Action buttons: Edit, Deactivate, Leave Settlement, End of Service, Overtime
- Professional layout
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGridLayout, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from core.themes import get_current_palette, get_font, FONT_SIZE_TITLE, FONT_SIZE_SUBTITLE, FONT_SIZE_BODY, FONT_SIZE_SMALL, FONT_WEIGHT_BOLD


class InfoCard(QFrame):
    """Card to display info section."""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._title = title
        self._fields = {}
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup card UI."""
        self.setObjectName("infoCard")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel(self._title)
        title_label.setFont(get_font(FONT_SIZE_SUBTITLE, FONT_WEIGHT_BOLD))
        title_label.setObjectName("cardTitle")
        layout.addWidget(title_label)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("cardSeparator")
        layout.addWidget(sep)
        
        # Grid for fields
        self._grid = QGridLayout()
        self._grid.setSpacing(15)
        self._grid.setColumnStretch(1, 1)
        self._grid.setColumnStretch(3, 1)
        layout.addLayout(self._grid)
    
    def add_field(self, label: str, value: str, row: int, col: int = 0):
        """Add a field to the card."""
        # Label
        lbl = QLabel(f"{label}:")
        lbl.setFont(get_font(FONT_SIZE_SMALL))
        lbl.setObjectName("fieldLabel")
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # Value
        val = QLabel(str(value) if value else "-")
        val.setFont(get_font(FONT_SIZE_BODY, FONT_WEIGHT_BOLD))
        val.setObjectName("fieldValue")
        val.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        # Add to grid
        col_offset = col * 2
        self._grid.addWidget(lbl, row, col_offset)
        self._grid.addWidget(val, row, col_offset + 1)
        
        self._fields[label] = val
    
    def update_field(self, label: str, value: str):
        """Update a field value."""
        if label in self._fields:
            self._fields[label].setText(str(value) if value else "-")


class ActionButton(QPushButton):
    """Styled action button."""
    
    def __init__(self, text: str, icon: str = "", color: str = "primary", parent=None):
        super().__init__(f"{icon} {text}" if icon else text, parent)
        self._color = color
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(get_font(FONT_SIZE_BODY))
        self.setMinimumHeight(45)
        self.setProperty("buttonColor", color)


class EmployeeProfileScreen(QWidget):
    """
    Employee Profile Screen.
    Shows complete employee information with action buttons.
    
    Signals:
        edit_clicked(dict): Edit button clicked
        deactivate_clicked(dict): Deactivate button clicked
        leave_settlement_clicked(dict): Leave settlement clicked
        end_of_service_clicked(dict): End of service clicked
        overtime_clicked(dict): Overtime clicked
        back_clicked(): Back button clicked
    """
    
    # Signals
    edit_clicked = pyqtSignal(dict)
    deactivate_clicked = pyqtSignal(dict)
    leave_settlement_clicked = pyqtSignal(dict)
    end_of_service_clicked = pyqtSignal(dict)
    overtime_clicked = pyqtSignal(dict)
    back_clicked = pyqtSignal()
    
    def __init__(self, employee_data: dict = None, parent=None):
        super().__init__(parent)
        
        self._employee = employee_data or {}
        
        self._setup_ui()
        self._apply_theme()
        
        if employee_data:
            self.set_employee(employee_data)
    
    def _setup_ui(self):
        """Setup screen UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header with back button and title
        header = QHBoxLayout()
        
        self._back_btn = QPushButton("→ رجوع")
        self._back_btn.setCursor(Qt.PointingHandCursor)
        self._back_btn.setFont(get_font(FONT_SIZE_BODY))
        self._back_btn.clicked.connect(self.back_clicked.emit)
        header.addWidget(self._back_btn)
        
        self._title_label = QLabel("ملف الموظف")
        self._title_label.setFont(get_font(FONT_SIZE_TITLE, FONT_WEIGHT_BOLD))
        self._title_label.setAlignment(Qt.AlignCenter)
        header.addWidget(self._title_label, 1)
        
        # Spacer for symmetry
        spacer = QWidget()
        spacer.setFixedWidth(80)
        header.addWidget(spacer)
        
        layout.addLayout(header)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(20)
        
        # ═══════════════════════════════════════════════════════════════
        # Basic Info Card
        # ═══════════════════════════════════════════════════════════════
        self._basic_card = InfoCard("📋 البيانات الأساسية")
        self._basic_card.add_field("كود الموظف", "", 0, 0)
        self._basic_card.add_field("الحالة", "", 0, 1)
        self._basic_card.add_field("الاسم بالعربي", "", 1, 0)
        self._basic_card.add_field("الاسم بالإنجليزي", "", 1, 1)
        self._basic_card.add_field("الجنسية", "", 2, 0)
        self._basic_card.add_field("تاريخ التعيين", "", 2, 1)
        scroll_layout.addWidget(self._basic_card)
        
        # ═══════════════════════════════════════════════════════════════
        # Job Info Card
        # ═══════════════════════════════════════════════════════════════
        self._job_card = InfoCard("💼 البيانات الوظيفية")
        self._job_card.add_field("الشركة", "", 0, 0)
        self._job_card.add_field("القسم", "", 0, 1)
        self._job_card.add_field("الوظيفة", "", 1, 0)
        self._job_card.add_field("المدير المباشر", "", 1, 1)
        scroll_layout.addWidget(self._job_card)
        
        # ═══════════════════════════════════════════════════════════════
        # Bank Info Card
        # ═══════════════════════════════════════════════════════════════
        self._bank_card = InfoCard("🏦 البيانات البنكية")
        self._bank_card.add_field("البنك", "", 0, 0)
        self._bank_card.add_field("IBAN", "", 0, 1)
        scroll_layout.addWidget(self._bank_card)
        
        # ═══════════════════════════════════════════════════════════════
        # Action Buttons
        # ═══════════════════════════════════════════════════════════════
        actions_frame = QFrame()
        actions_frame.setObjectName("actionsFrame")
        actions_layout = QHBoxLayout(actions_frame)
        actions_layout.setContentsMargins(20, 20, 20, 20)
        actions_layout.setSpacing(15)
        
        # Edit button
        self._edit_btn = ActionButton("تعديل البيانات", "📝", "primary")
        self._edit_btn.clicked.connect(self._on_edit)
        actions_layout.addWidget(self._edit_btn)
        
        # Leave settlement button
        self._leave_btn = ActionButton("تسوية إجازة", "🏖️", "success")
        self._leave_btn.clicked.connect(self._on_leave_settlement)
        actions_layout.addWidget(self._leave_btn)
        
        # Overtime button
        self._overtime_btn = ActionButton("حساب الإضافي", "⏰", "info")
        self._overtime_btn.clicked.connect(self._on_overtime)
        actions_layout.addWidget(self._overtime_btn)
        
        # End of service button
        self._eos_btn = ActionButton("نهاية الخدمة", "🚪", "warning")
        self._eos_btn.clicked.connect(self._on_end_of_service)
        actions_layout.addWidget(self._eos_btn)
        
        # Deactivate button
        self._deactivate_btn = ActionButton("إيقاف الموظف", "⛔", "danger")
        self._deactivate_btn.clicked.connect(self._on_deactivate)
        actions_layout.addWidget(self._deactivate_btn)
        
        scroll_layout.addWidget(actions_frame)
        
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
    
    def _apply_theme(self):
        """Apply current theme using palette."""
        p = get_current_palette()
        self.setStyleSheet(f"""
            QWidget {{ background-color: {p['bg_main']}; }}
            QLabel {{ color: {p['text_primary']}; background: transparent; }}
            QLabel#fieldLabel {{ color: {p['text_secondary']}; }}
            QLabel#fieldValue {{ color: {p['text_primary']}; }}
            QLabel#cardTitle {{ color: {p['accent']}; }}
            QFrame#infoCard {{ background-color: {p['bg_card']}; border: 1px solid {p['border']}; border-radius: 12px; }}
            QFrame#cardSeparator {{ background-color: {p['border']}; }}
            QFrame#actionsFrame {{ background-color: {p['bg_card']}; border: 1px solid {p['border']}; border-radius: 12px; }}
            QPushButton {{ background-color: {p['bg_card']}; color: {p['text_primary']}; border: none; border-radius: 8px; padding: 12px 24px; font-weight: bold; }}
            QPushButton:hover {{ background-color: {p['bg_hover']}; }}
            QPushButton[buttonColor="primary"] {{ background-color: {p['primary']}; color: {p['text_on_primary']}; }}
            QPushButton[buttonColor="primary"]:hover {{ background-color: {p['primary_hover']}; }}
            QPushButton[buttonColor="success"] {{ background-color: {p['success']}; color: {p['text_on_primary']}; }}
            QPushButton[buttonColor="info"] {{ background-color: {p['info']}; color: {p['text_on_primary']}; }}
            QPushButton[buttonColor="warning"] {{ background-color: {p['warning']}; color: {p['text_on_primary']}; }}
            QPushButton[buttonColor="danger"] {{ background-color: {p['danger']}; color: {p['text_on_primary']}; }}
            QScrollArea {{ background: transparent; border: none; }}
        """)
    
    # ═══════════════════════════════════════════════════════════════
    # Public API
    # ═══════════════════════════════════════════════════════════════
    
    def set_employee(self, data: dict):
        """Set employee data to display."""
        self._employee = data
        
        # Update title
        name = data.get('name_ar', data.get('name_en', 'موظف'))
        self._title_label.setText(f"ملف الموظف: {name}")
        
        # Update basic info
        self._basic_card.update_field("كود الموظف", data.get('employee_code'))
        self._basic_card.update_field("الحالة", data.get('status'))
        self._basic_card.update_field("الاسم بالعربي", data.get('name_ar'))
        self._basic_card.update_field("الاسم بالإنجليزي", data.get('name_en'))
        self._basic_card.update_field("الجنسية", data.get('nationality'))
        self._basic_card.update_field("تاريخ التعيين", data.get('hire_date'))
        
        # Update job info
        self._job_card.update_field("الشركة", data.get('company'))
        self._job_card.update_field("القسم", data.get('department'))
        self._job_card.update_field("الوظيفة", data.get('job_title'))
        self._job_card.update_field("المدير المباشر", data.get('manager', '-'))
        
        # Update bank info
        self._bank_card.update_field("البنك", data.get('bank'))
        self._bank_card.update_field("IBAN", data.get('iban'))
    
    def get_employee(self) -> dict:
        """Get current employee data."""
        return self._employee
    
    # ═══════════════════════════════════════════════════════════════
    # Signal Handlers
    # ═══════════════════════════════════════════════════════════════
    
    def _on_edit(self):
        """Handle edit button click."""
        self.edit_clicked.emit(self._employee)
    
    def _on_deactivate(self):
        """Handle deactivate button click."""
        self.deactivate_clicked.emit(self._employee)
    
    def _on_leave_settlement(self):
        """Handle leave settlement button click."""
        self.leave_settlement_clicked.emit(self._employee)
    
    def _on_end_of_service(self):
        """Handle end of service button click."""
        self.end_of_service_clicked.emit(self._employee)
    
    def _on_overtime(self):
        """Handle overtime button click."""
        self.overtime_clicked.emit(self._employee)
