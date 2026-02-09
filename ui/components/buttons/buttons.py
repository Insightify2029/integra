"""
Button Components
=================
Styled button widgets. Styling handled by centralized theme system.
Use cssClass property to select variant: "secondary", "danger", "success", "ghost".
"""

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt


class PrimaryButton(QPushButton):
    """Primary action button. Uses default QPushButton theme styling."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)


class SecondaryButton(QPushButton):
    """Secondary action button."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setProperty("cssClass", "secondary")
        self.setCursor(Qt.PointingHandCursor)


class DangerButton(QPushButton):
    """Danger/Delete action button."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setProperty("cssClass", "danger")
        self.setCursor(Qt.PointingHandCursor)
