"""
Column Chooser
==============
Dialog to choose visible columns. Styling handled by centralized theme system.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QCheckBox,
    QPushButton, QLabel, QScrollArea, QWidget, QFrame
)
from PyQt5.QtCore import pyqtSignal

from core.themes import get_font, FONT_SIZE_SUBTITLE, FONT_SIZE_BODY, FONT_WEIGHT_BOLD


class ColumnChooser(QDialog):
    """
    Dialog to choose visible columns.

    Signals:
        columns_changed(list): List of (column_index, visible) tuples
    """

    columns_changed = pyqtSignal(list)

    def __init__(self, columns: list, hidden_columns: list = None, parent=None):
        super().__init__(parent)

        self._columns = columns
        self._hidden = hidden_columns or []
        self._checkboxes = []

        self._setup_ui()
        # App-level QSS handles dialog, checkbox, button styling

    def _setup_ui(self):
        """Setup dialog UI."""
        self.setWindowTitle("\U0001f4ca \u0627\u062e\u062a\u064a\u0627\u0631 \u0627\u0644\u0623\u0639\u0645\u062f\u0629")
        self.setMinimumSize(350, 400)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title = QLabel("\u0627\u062e\u062a\u0631 \u0627\u0644\u0623\u0639\u0645\u062f\u0629 \u0627\u0644\u0645\u0631\u0627\u062f \u0639\u0631\u0636\u0647\u0627:")
        title.setFont(get_font(FONT_SIZE_SUBTITLE, FONT_WEIGHT_BOLD))
        layout.addWidget(title)

        # Scroll area for checkboxes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(10)

        # Create checkbox for each column
        for i, col in enumerate(self._columns):
            cb = QCheckBox(col)
            cb.setChecked(i not in self._hidden)
            cb.setFont(get_font(FONT_SIZE_BODY))
            cb.column_index = i
            self._checkboxes.append(cb)
            scroll_layout.addWidget(cb)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Quick actions
        actions_layout = QHBoxLayout()

        select_all_btn = QPushButton("\u2611\ufe0f \u062a\u062d\u062f\u064a\u062f \u0627\u0644\u0643\u0644")
        select_all_btn.setProperty("cssClass", "secondary")
        select_all_btn.clicked.connect(self._select_all)
        actions_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("\u2610 \u0625\u0644\u063a\u0627\u0621 \u0627\u0644\u0643\u0644")
        deselect_all_btn.setProperty("cssClass", "secondary")
        deselect_all_btn.clicked.connect(self._deselect_all)
        actions_layout.addWidget(deselect_all_btn)

        layout.addLayout(actions_layout)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("\u0625\u0644\u063a\u0627\u0621")
        cancel_btn.setProperty("cssClass", "secondary")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        apply_btn = QPushButton("\u2705 \u062a\u0637\u0628\u064a\u0642")
        apply_btn.clicked.connect(self._apply)
        buttons_layout.addWidget(apply_btn)

        layout.addLayout(buttons_layout)

    def _select_all(self):
        """Select all columns."""
        for cb in self._checkboxes:
            cb.setChecked(True)

    def _deselect_all(self):
        """Deselect all columns."""
        for cb in self._checkboxes:
            cb.setChecked(False)

    def _apply(self):
        """Apply changes."""
        changes = []
        for cb in self._checkboxes:
            changes.append((cb.column_index, cb.isChecked()))

        self.columns_changed.emit(changes)
        self.accept()

    def get_hidden_columns(self) -> list:
        """Get list of hidden column indices."""
        hidden = []
        for cb in self._checkboxes:
            if not cb.isChecked():
                hidden.append(cb.column_index)
        return hidden
