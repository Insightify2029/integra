"""
Stat Card Widget
================
Statistics card component.
"""

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt5.QtGui import QFont

from core.themes import get_current_theme


class StatCard(QFrame):
    """Statistics display card."""
    
    def __init__(self, icon: str, value, label: str, color: str = "#2563eb", parent=None):
        """
        Initialize stat card.
        
        Args:
            icon: Emoji icon
            value: The statistic value
            label: Description label
            color: Accent color
        """
        super().__init__(parent)
        
        self.icon = icon
        self.value = value
        self.label = label
        self.color = color
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the card UI."""
        theme = get_current_theme()
        
        if theme == 'dark':
            bg = "#1e293b"
            muted_color = "#94a3b8"
        else:
            bg = "#ffffff"
            muted_color = "#64748b"
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid {"#334155" if theme == "dark" else "#e2e8f0"};
                border-radius: 12px;
                border-left: 4px solid {self.color};
            }}
            QFrame:hover {{
                border-color: {self.color};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Icon
        icon_label = QLabel(self.icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 24))
        icon_label.setStyleSheet("background: transparent;")
        layout.addWidget(icon_label)
        
        # Value
        value_label = QLabel(str(self.value))
        value_label.setFont(QFont("Cairo", 28, QFont.Bold))
        value_label.setStyleSheet(f"color: {self.color}; background: transparent;")
        layout.addWidget(value_label)
        
        # Label
        text_label = QLabel(self.label)
        text_label.setStyleSheet(f"color: {muted_color}; background: transparent;")
        layout.addWidget(text_label)
