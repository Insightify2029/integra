"""
Label Components
================
Styled label widgets.
"""

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.themes import get_current_theme


class TitleLabel(QLabel):
    """Large title label."""
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self._setup()
    
    def _setup(self):
        theme = get_current_theme()
        self.setFont(QFont("Cairo", 24, QFont.Bold))
        self.setAlignment(Qt.AlignCenter)
        
        color = "#f1f5f9" if theme == 'dark' else "#1e293b"
        self.setStyleSheet(f"color: {color}; background: transparent;")


class LogoLabel(QLabel):
    """Extra large logo label."""
    
    def __init__(self, text: str = "INTEGRA", parent=None):
        super().__init__(text, parent)
        self._setup()
    
    def _setup(self):
        self.setFont(QFont("Segoe UI", 72, QFont.Bold))
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("color: #2563eb; background: transparent; letter-spacing: 8px;")


class SubtitleLabel(QLabel):
    """Subtitle label."""
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self._setup()
    
    def _setup(self):
        theme = get_current_theme()
        self.setFont(QFont("Cairo", 14))
        self.setAlignment(Qt.AlignCenter)
        
        color = "#94a3b8" if theme == 'dark' else "#64748b"
        self.setStyleSheet(f"color: {color}; background: transparent;")


class SectionLabel(QLabel):
    """Section header label."""
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self._setup()
    
    def _setup(self):
        self.setFont(QFont("Cairo", 16, QFont.Bold))
        self.setStyleSheet("color: #06b6d4; background: transparent;")
