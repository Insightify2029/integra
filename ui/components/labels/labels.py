"""
Label Components
================
Styled label widgets. Styling handled by centralized theme system.
"""

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt

from core.themes import (
    get_current_palette, get_font,
    FONT_SIZE_HEADING, FONT_SIZE_SUBTITLE, FONT_SIZE_TITLE,
    FONT_SIZE_LOGO, FONT_WEIGHT_BOLD
)


class TitleLabel(QLabel):
    """Large title label."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self._setup()

    def _setup(self):
        palette = get_current_palette()
        self.setFont(get_font(FONT_SIZE_HEADING, FONT_WEIGHT_BOLD))
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(f"color: {palette['text_primary']}; background: transparent;")


class LogoLabel(QLabel):
    """Extra large logo label."""

    def __init__(self, text: str = "INTEGRA", parent=None):
        super().__init__(text, parent)
        self._setup()

    def _setup(self):
        palette = get_current_palette()
        self.setFont(get_font(FONT_SIZE_LOGO, FONT_WEIGHT_BOLD))
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(f"color: {palette['primary']}; background: transparent; letter-spacing: 8px;")


class SubtitleLabel(QLabel):
    """Subtitle label."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self._setup()

    def _setup(self):
        palette = get_current_palette()
        self.setFont(get_font(FONT_SIZE_SUBTITLE))
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(f"color: {palette['text_secondary']}; background: transparent;")


class SectionLabel(QLabel):
    """Section header label."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self._setup()

    def _setup(self):
        palette = get_current_palette()
        self.setFont(get_font(FONT_SIZE_TITLE, FONT_WEIGHT_BOLD))
        self.setStyleSheet(f"color: {palette['accent']}; background: transparent;")
