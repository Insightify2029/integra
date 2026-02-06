"""
Button Components
=================
Styled button widgets.
"""

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.themes import get_current_theme


class PrimaryButton(QPushButton):
    """Primary action button."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self._setup()

    def _setup(self):
        self.setFont(QFont("Cairo", 13))
        self.setCursor(Qt.ArrowCursor)
        
        self.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3b82f6;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
            }
        """)


class SecondaryButton(QPushButton):
    """Secondary action button."""
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self._setup()
    
    def _setup(self):
        theme = get_current_theme()
        self.setFont(QFont("Cairo", 13))
        
        if theme == 'dark':
            self.setStyleSheet("""
                QPushButton {
                    background-color: #334155;
                    color: #f1f5f9;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                }
                QPushButton:hover {
                    background-color: #475569;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #e2e8f0;
                    color: #1e293b;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                }
                QPushButton:hover {
                    background-color: #cbd5e1;
                }
            """)


class DangerButton(QPushButton):
    """Danger/Delete action button."""
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self._setup()
    
    def _setup(self):
        self.setFont(QFont("Cairo", 13))
        self.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
