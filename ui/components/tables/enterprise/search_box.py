"""
Search Box
==========
Smart search box with debounce. Styling handled by centralized theme system.
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit
)
from PyQt5.QtCore import pyqtSignal, QTimer


class SearchBox(QWidget):
    """
    Smart search box with debounce.
    App-level QSS handles QLineEdit styling automatically.

    Signals:
        search_changed(str): Emitted when search text changes (debounced)
        search_submitted(str): Emitted when Enter is pressed
    """

    # Signals
    search_changed = pyqtSignal(str)
    search_submitted = pyqtSignal(str)

    def __init__(self, parent=None, debounce_ms: int = 300):
        super().__init__(parent)

        self._debounce_ms = debounce_ms
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._emit_search)

        self._setup_ui()
        # App-level QSS handles QLineEdit styling

    def _setup_ui(self):
        """Setup UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Search input
        self._input = QLineEdit()
        self._input.setPlaceholderText("\U0001f50d \u0628\u062d\u062b...")
        self._input.setClearButtonEnabled(True)
        self._input.textChanged.connect(self._on_text_changed)
        self._input.returnPressed.connect(self._on_return_pressed)
        layout.addWidget(self._input)

    def _on_text_changed(self, text: str):
        """Handle text change with debounce."""
        self._debounce_timer.stop()
        self._debounce_timer.start(self._debounce_ms)

    def _on_return_pressed(self):
        """Handle Enter key."""
        self._debounce_timer.stop()
        text = self._input.text()
        self.search_submitted.emit(text)
        self.search_changed.emit(text)

    def _emit_search(self):
        """Emit search signal after debounce."""
        text = self._input.text()
        self.search_changed.emit(text)

    # ===================================================================
    # Public API
    # ===================================================================

    def get_text(self) -> str:
        """Get current search text."""
        return self._input.text()

    def set_text(self, text: str):
        """Set search text."""
        self._input.setText(text)

    def clear(self):
        """Clear search box."""
        self._input.clear()

    def set_placeholder(self, text: str):
        """Set placeholder text."""
        self._input.setPlaceholderText(text)

    def set_focus(self):
        """Set focus to search input."""
        self._input.setFocus()
