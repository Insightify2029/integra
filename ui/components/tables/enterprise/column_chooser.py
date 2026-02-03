"""
Column Chooser
==============
نافذة اختيار الأعمدة المعروضة
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QCheckBox,
    QPushButton, QLabel, QScrollArea, QWidget, QFrame
)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont

from core.themes import get_current_theme, get_stylesheet


class ColumnChooser(QDialog):
    """
    Dialog to choose visible columns.
    
    Signals:
        columns_changed(list): List of (column_index, visible) tuples
    """
    
    columns_changed = pyqtSignal(list)
    
    def __init__(self, columns: list, hidden_columns: list = None, parent=None):
        super().__init__(parent)
        
        self._columns = columns
        self._hidden = hidden_columns or []
        self._checkboxes = []
        
        self._setup_ui()
        self._apply_theme()
    
    def _setup_ui(self):
        """Setup dialog UI."""
        self.setWindowTitle("📊 اختيار الأعمدة")
        self.setMinimumSize(350, 400)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("اختر الأعمدة المراد عرضها:")
        title.setFont(QFont("Cairo", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Scroll area for checkboxes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(10)
        
        # Create checkbox for each column
        for i, col in enumerate(self._columns):
            cb = QCheckBox(col)
            cb.setChecked(i not in self._hidden)
            cb.setFont(QFont("Cairo", 12))
            cb.column_index = i
            self._checkboxes.append(cb)
            scroll_layout.addWidget(cb)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Quick actions
        actions_layout = QHBoxLayout()
        
        select_all_btn = QPushButton("☑️ تحديد الكل")
        select_all_btn.clicked.connect(self._select_all)
        actions_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("☐ إلغاء الكل")
        deselect_all_btn.clicked.connect(self._deselect_all)
        actions_layout.addWidget(deselect_all_btn)
        
        layout.addLayout(actions_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("✅ تطبيق")
        apply_btn.setProperty("primary", True)
        apply_btn.clicked.connect(self._apply)
        buttons_layout.addWidget(apply_btn)
        
        layout.addLayout(buttons_layout)
    
    def _apply_theme(self):
        """Apply current theme."""
        self.setStyleSheet(get_stylesheet())
        
        theme = get_current_theme()
        
        if theme == 'dark':
            self.setStyleSheet(self.styleSheet() + """
                QDialog {
                    background-color: #1e293b;
                }
                
                QLabel {
                    color: #f1f5f9;
                }
                
                QCheckBox {
                    color: #f1f5f9;
                    spacing: 10px;
                    padding: 8px;
                    border-radius: 6px;
                }
                
                QCheckBox:hover {
                    background-color: #334155;
                }
                
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    border-radius: 4px;
                    border: 2px solid #475569;
                    background-color: #0f172a;
                }
                
                QCheckBox::indicator:checked {
                    background-color: #2563eb;
                    border-color: #2563eb;
                }
                
                QPushButton {
                    background-color: #334155;
                    color: #f1f5f9;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-size: 13px;
                }
                
                QPushButton:hover {
                    background-color: #475569;
                }
                
                QPushButton[primary="true"] {
                    background-color: #2563eb;
                }
                
                QPushButton[primary="true"]:hover {
                    background-color: #1d4ed8;
                }
                
                QScrollArea {
                    background-color: transparent;
                }
            """)
        else:
            self.setStyleSheet(self.styleSheet() + """
                QDialog {
                    background-color: #ffffff;
                }
                
                QLabel {
                    color: #1e293b;
                }
                
                QCheckBox {
                    color: #1e293b;
                    spacing: 10px;
                    padding: 8px;
                    border-radius: 6px;
                }
                
                QCheckBox:hover {
                    background-color: #f1f5f9;
                }
                
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    border-radius: 4px;
                    border: 2px solid #cbd5e1;
                    background-color: #ffffff;
                }
                
                QCheckBox::indicator:checked {
                    background-color: #2563eb;
                    border-color: #2563eb;
                }
                
                QPushButton {
                    background-color: #e2e8f0;
                    color: #1e293b;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-size: 13px;
                }
                
                QPushButton:hover {
                    background-color: #cbd5e1;
                }
                
                QPushButton[primary="true"] {
                    background-color: #2563eb;
                    color: #ffffff;
                }
                
                QPushButton[primary="true"]:hover {
                    background-color: #1d4ed8;
                }
            """)
    
    def _select_all(self):
        """Select all columns."""
        for cb in self._checkboxes:
            cb.setChecked(True)
    
    def _deselect_all(self):
        """Deselect all columns."""
        for cb in self._checkboxes:
            cb.setChecked(False)
    
    def _apply(self):
        """Apply changes."""
        changes = []
        for cb in self._checkboxes:
            changes.append((cb.column_index, cb.isChecked()))
        
        self.columns_changed.emit(changes)
        self.accept()
    
    def get_hidden_columns(self) -> list:
        """Get list of hidden column indices."""
        hidden = []
        for cb in self._checkboxes:
            if not cb.isChecked():
                hidden.append(cb.column_index)
        return hidden
