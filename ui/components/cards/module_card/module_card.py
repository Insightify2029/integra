"""
Module Card Widget
==================
Complete module card component with QtAwesome icon support.
"""

from PyQt5.QtWidgets import QFrame, QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap

from core.themes import get_current_palette, get_font, FONT_SIZE_SUBTITLE, FONT_WEIGHT_BOLD
from core.utils.icons import icon as qta_icon, QTAWESOME_AVAILABLE

from .card_layout import create_card_layout
from .card_shadow import create_card_shadow
from .card_style import get_card_style

# Mapping: module_id -> QtAwesome icon name
MODULE_ICON_MAP = {
    'mostahaqat': 'fa5s.users',
    'costing': 'fa5s.chart-bar',
    'logistics': 'fa5s.truck',
    'custody': 'fa5s.key',
    'insurance': 'fa5s.shield-alt',
    'email': 'fa5s.envelope',
    'designer': 'fa5s.drafting-compass',
    'calendar': 'fa5s.calendar-alt',
    'dashboard': 'fa5s.tachometer-alt',
    'bi': 'fa5s.chart-pie',
    'copilot': 'fa5s.robot',
    'time_intelligence': 'fa5s.clock',
    'file_manager': 'fa5s.folder-open',
    'device_manager': 'fa5s.print',
    'desktop_apps': 'fa5s.comments',
    'tasks': 'fa5s.tasks',
    'notifications': 'fa5s.bell',
}


class ModuleCard(QFrame):
    """
    Clickable module card widget.
    
    Signals:
        clicked: Emitted when card is clicked, passes module_id
    """
    
    clicked = pyqtSignal(str)
    
    def __init__(self, module_info: dict, parent=None):
        """
        Initialize module card.
        
        Args:
            module_info: Dictionary with keys:
                - id: Module identifier
                - name_ar: Arabic name
                - name_en: English name
                - icon: Emoji icon
                - color: Accent color
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.module_id = module_info['id']
        self.module_info = module_info
        self.card_width = 220
        self.card_height = 200
        
        self._setup_ui()
    
    def _get_fitting_font_size(self, text, font_family, max_width, max_size=28, min_size=14):
        """Calculate font size that fits within max_width."""
        from PyQt5.QtGui import QFontMetrics
        
        for size in range(max_size, min_size - 1, -1):
            font = QFont(font_family, size, QFont.Bold)
            metrics = QFontMetrics(font)
            text_width = metrics.horizontalAdvance(text)
            if text_width <= max_width:
                return size
        return min_size
    
    def _setup_ui(self):
        """Setup the card UI."""
        # Container settings
        self.setFixedSize(self.card_width, self.card_height)
        self.setCursor(Qt.PointingHandCursor)
        
        # Apply style - NO BORDERS AT ALL
        self.setStyleSheet(get_card_style(self.module_info['color']))
        
        # Apply shadow
        self.setGraphicsEffect(create_card_shadow())
        
        # Create layout
        layout = create_card_layout()
        self.setLayout(layout)
        
        # Get Arabic text
        ar_text = self.module_info['name_ar']
        text_len = len(ar_text.replace(' ', ''))  # Count without spaces
        
        # Calculate font size based on text length (characters)
        if text_len <= 5:
            ar_font_size = 30
        elif text_len <= 7:
            ar_font_size = 26
        elif text_len <= 10:
            ar_font_size = 22
        else:
            ar_font_size = 18
        
        # Add title (Arabic) - TOP - FLEXIBLE FONT SIZE
        title_ar = QLabel(ar_text)
        title_ar.setFont(QFont("Cairo", ar_font_size, QFont.Bold))
        title_ar.setAlignment(Qt.AlignCenter)
        p = get_current_palette()
        title_ar.setStyleSheet(f"color: {p['primary']}; background: transparent; border: none;")
        title_ar.setWordWrap(True)
        layout.addWidget(title_ar)
        
        # Add icon - MIDDLE (QtAwesome if available, emoji fallback)
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("background: transparent; border: none;")

        qta_name = MODULE_ICON_MAP.get(self.module_id)
        if QTAWESOME_AVAILABLE and qta_name:
            pixmap = qta_icon(qta_name, color=p['primary']).pixmap(56, 56)
            icon_label.setPixmap(pixmap)
            icon_label.setFixedSize(64, 64)
        else:
            icon_label.setText(self.module_info['icon'])
            icon_label.setFont(get_font(48))

        layout.addWidget(icon_label)
        
        # Add title (English) - BOTTOM
        title_en = QLabel(self.module_info['name_en'])
        title_en.setFont(get_font(FONT_SIZE_SUBTITLE))
        title_en.setAlignment(Qt.AlignCenter)
        title_en.setStyleSheet(f"color: {p['text_muted']}; background: transparent; border: none;")
        layout.addWidget(title_en)
    
    def mousePressEvent(self, event):
        """Handle mouse press."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.module_id)
    
    def enterEvent(self, event):
        """Handle mouse enter."""
        # Could add hover animation here
        pass
    
    def leaveEvent(self, event):
        """Handle mouse leave."""
        # Could add leave animation here
        pass
