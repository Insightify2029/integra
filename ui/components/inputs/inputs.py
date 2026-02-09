"""
Input Components
================
Styled input widgets. Styling handled by centralized theme system.
Standard QLineEdit and QComboBox styling comes from app-level QSS.
Only override for genuinely custom shapes (e.g. rounded search input).
"""

from PyQt5.QtWidgets import QLineEdit, QComboBox

from core.themes import get_current_palette


class TextInput(QLineEdit):
    """Styled text input. Uses app-level QSS for base styling."""

    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        # App-level QSS handles QLineEdit styling


class SearchInput(QLineEdit):
    """Search input with rounded corners (custom override)."""

    def __init__(self, placeholder: str = "\U0001f50d \u0628\u062d\u062b...", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self._setup()

    def _setup(self):
        palette = get_current_palette()
        # Override only the border-radius for the rounded search style
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {palette['bg_input']};
                color: {palette['text_primary']};
                border: 1px solid {palette['border']};
                border-radius: 20px;
                padding: 10px 20px;
            }}
            QLineEdit:focus {{
                border: 2px solid {palette['border_focus']};
            }}
        """)


class StyledComboBox(QComboBox):
    """Styled combo box. Uses app-level QSS for base styling."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # App-level QSS handles QComboBox styling
