"""
Mostahaqat Stats Cards
======================
Statistics cards for the module.
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout

from ui.components.cards import StatCard
from core.themes import get_current_palette

from modules.mostahaqat.employees import (
    get_employees_count,
    get_active_employees_count,
    get_nationalities_count,
    get_departments_count,
    get_jobs_count
)


class StatsCardsWidget(QWidget):
    """Widget containing all stats cards."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the widget."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Get stats
        total = get_employees_count()
        active = get_active_employees_count()
        nationalities = get_nationalities_count()
        departments = get_departments_count()
        jobs = get_jobs_count()
        
        # Create cards with palette colors
        p = get_current_palette()
        cards_data = [
            ("👥", total, "إجمالي الموظفين", p['primary']),
            ("✅", active, "الموظفين النشطين", p['success']),
            ("🌍", nationalities, "الجنسيات", p['warning']),
            ("🏢", departments, "الأقسام", p['accent']),
            ("💼", jobs, "الوظائف", p['danger']),
        ]
        
        for icon, value, label, color in cards_data:
            card = StatCard(icon, value, label, color)
            layout.addWidget(card)
    
    def refresh(self):
        """Refresh stats - recreate widget."""
        # Clear existing
        while self.layout().count():
            item = self.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Recreate
        self._setup_ui()
