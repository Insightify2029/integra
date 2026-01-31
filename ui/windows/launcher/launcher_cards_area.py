"""
Launcher Cards Area
===================
The area containing module cards.
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal

from core.config.modules import get_enabled_modules
from ui.components.cards import ModuleCard


class LauncherCardsArea(QWidget):
    """
    Widget containing all module cards.
    
    Signals:
        module_clicked: Emitted when a module card is clicked
    """
    
    module_clicked = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the cards area."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignCenter)
        
        # Create cards for enabled modules
        modules = get_enabled_modules()
        
        for module in modules:
            card = ModuleCard(module)
            card.clicked.connect(self._on_card_clicked)
            layout.addWidget(card)
    
    def _on_card_clicked(self, module_id):
        """Handle card click."""
        self.module_clicked.emit(module_id)
