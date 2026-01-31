"""
Input Components
================
Styled input widgets.
"""

from PyQt5.QtWidgets import QLineEdit, QComboBox
from PyQt5.QtGui import QFont

from core.themes import get_current_theme


class TextInput(QLineEdit):
    """Styled text input."""
    
    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self._setup()
    
    def _setup(self):
        theme = get_current_theme()
        self.setFont(QFont("Cairo", 13))
        
        if theme == 'dark':
            self.setStyleSheet("""
                QLineEdit {
                    background-color: #1e293b;
                    color: #f1f5f9;
                    border: 1px solid #334155;
                    border-radius: 6px;
                    padding: 10px;
                }
                QLineEdit:focus {
                    border: 2px solid #2563eb;
                }
            """)
        else:
            self.setStyleSheet("""
                QLineEdit {
                    background-color: #ffffff;
                    color: #1e293b;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    padding: 10px;
                }
                QLineEdit:focus {
                    border: 2px solid #2563eb;
                }
            """)


class SearchInput(QLineEdit):
    """Search input with icon."""
    
    def __init__(self, placeholder: str = "🔍 بحث...", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self._setup()
    
    def _setup(self):
        theme = get_current_theme()
        self.setFont(QFont("Cairo", 13))
        
        if theme == 'dark':
            self.setStyleSheet("""
                QLineEdit {
                    background-color: #1e293b;
                    color: #f1f5f9;
                    border: 1px solid #334155;
                    border-radius: 20px;
                    padding: 10px 20px;
                }
                QLineEdit:focus {
                    border: 2px solid #2563eb;
                }
            """)
        else:
            self.setStyleSheet("""
                QLineEdit {
                    background-color: #ffffff;
                    color: #1e293b;
                    border: 1px solid #cbd5e1;
                    border-radius: 20px;
                    padding: 10px 20px;
                }
                QLineEdit:focus {
                    border: 2px solid #2563eb;
                }
            """)


class StyledComboBox(QComboBox):
    """Styled combo box."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup()
    
    def _setup(self):
        theme = get_current_theme()
        self.setFont(QFont("Cairo", 13))
        
        if theme == 'dark':
            self.setStyleSheet("""
                QComboBox {
                    background-color: #1e293b;
                    color: #f1f5f9;
                    border: 1px solid #334155;
                    border-radius: 6px;
                    padding: 10px;
                }
                QComboBox::drop-down {
                    border: none;
                }
                QComboBox QAbstractItemView {
                    background-color: #1e293b;
                    color: #f1f5f9;
                    selection-background-color: #2563eb;
                }
            """)
        else:
            self.setStyleSheet("""
                QComboBox {
                    background-color: #ffffff;
                    color: #1e293b;
                    border: 1px solid #cbd5e1;
                    border-radius: 6px;
                    padding: 10px;
                }
                QComboBox::drop-down {
                    border: none;
                }
                QComboBox QAbstractItemView {
                    background-color: #ffffff;
                    color: #1e293b;
                    selection-background-color: #2563eb;
                }
            """)
