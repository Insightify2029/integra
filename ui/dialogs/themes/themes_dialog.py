"""
Themes Dialog
=============
Theme selection dialog.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.themes import (
    get_stylesheet, get_current_theme, set_current_theme,
    get_available_themes, get_theme_display_name
)


class ThemesDialog(QDialog):
    """Theme selection dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎨 اختيار الثيم")
        self.setMinimumSize(400, 300)
        self.setStyleSheet(get_stylesheet())
        
        self.selected_theme = get_current_theme()
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("اختر الثيم المفضل:")
        title.setFont(QFont("Cairo", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Theme options
        self.button_group = QButtonGroup(self)
        
        for theme in get_available_themes():
            radio = QRadioButton(get_theme_display_name(theme))
            radio.setFont(QFont("Cairo", 14))
            radio.theme_name = theme
            
            if theme == self.selected_theme:
                radio.setChecked(True)
            
            radio.toggled.connect(lambda checked, t=theme: self._on_theme_selected(t) if checked else None)
            
            self.button_group.addButton(radio)
            layout.addWidget(radio)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        apply_btn = QPushButton("✅ تطبيق")
        apply_btn.clicked.connect(self._apply_theme)
        
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(apply_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def _on_theme_selected(self, theme):
        """Handle theme selection."""
        self.selected_theme = theme
    
    def _apply_theme(self):
        """Apply selected theme."""
        set_current_theme(self.selected_theme)
        self.accept()
    
    def get_selected_theme(self):
        """Get the selected theme name."""
        return self.selected_theme
