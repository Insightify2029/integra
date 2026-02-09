"""
Stat Card Widget
================
Statistics card component. Styling handled by centralized theme system.
"""

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel

from core.themes import get_current_palette, get_font, FONT_SIZE_DISPLAY, FONT_WEIGHT_BOLD


class StatCard(QFrame):
    """Statistics display card."""

    def __init__(self, icon: str, value, label: str, color: str = "", parent=None):
        """
        Initialize stat card.

        Args:
            icon: Emoji icon
            value: The statistic value
            label: Description label
            color: Accent color (uses palette primary if empty)
        """
        super().__init__(parent)

        self.icon = icon
        self.value = value
        self.label = label

        palette = get_current_palette()
        self.color = color or palette['primary']

        self._setup_ui()

    def _setup_ui(self):
        """Setup the card UI."""
        palette = get_current_palette()

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {palette['bg_card']};
                border: 1px solid {palette['border']};
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
        icon_label.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(icon_label)

        # Value
        value_label = QLabel(str(self.value))
        value_label.setFont(get_font(FONT_SIZE_DISPLAY, FONT_WEIGHT_BOLD))
        value_label.setStyleSheet(f"color: {self.color}; background: transparent; border: none;")
        layout.addWidget(value_label)

        # Label
        text_label = QLabel(self.label)
        text_label.setStyleSheet(f"color: {palette['text_muted']}; background: transparent; border: none;")
        layout.addWidget(text_label)
