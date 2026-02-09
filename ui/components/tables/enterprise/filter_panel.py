"""
Filter Panel
============
Smart filter panel for tables. Styling handled by centralized theme system.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QLineEdit, QPushButton, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal

from core.themes import get_current_palette, get_font, FONT_SIZE_SUBTITLE, FONT_SIZE_SMALL, FONT_WEIGHT_BOLD


class FilterItem(QWidget):
    """Single filter item for a column."""

    filter_changed = pyqtSignal(int, str)  # column_index, filter_text
    removed = pyqtSignal(int)  # column_index

    def __init__(self, column_index: int, column_name: str, parent=None):
        super().__init__(parent)

        self._column_index = column_index
        self._column_name = column_name

        self._setup_ui()

    def _setup_ui(self):
        """Setup UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # Column label
        label = QLabel(f"{self._column_name}:")
        label.setFont(get_font(FONT_SIZE_SMALL))
        label.setFixedWidth(100)
        layout.addWidget(label)

        # Filter input
        self._input = QLineEdit()
        self._input.setPlaceholderText("\u0627\u0643\u062a\u0628 \u0644\u0644\u062a\u0635\u0641\u064a\u0629...")
        self._input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._input)

        # Remove button
        remove_btn = QPushButton("\u2715")
        remove_btn.setFixedSize(30, 30)
        remove_btn.setCursor(Qt.PointingHandCursor)
        remove_btn.setProperty("cssClass", "danger")
        remove_btn.clicked.connect(lambda: self.removed.emit(self._column_index))
        layout.addWidget(remove_btn)

    def _on_text_changed(self, text: str):
        """Handle text change."""
        self.filter_changed.emit(self._column_index, text)

    def get_filter_text(self) -> str:
        """Get current filter text."""
        return self._input.text()

    def clear(self):
        """Clear filter."""
        self._input.clear()


class FilterPanel(QWidget):
    """
    Panel for managing column filters.
    Styling handled by centralized theme system (app-level QSS).

    Signals:
        filter_changed(int, str): Column filter changed
        filters_cleared(): All filters cleared
    """

    filter_changed = pyqtSignal(int, str)
    filters_cleared = pyqtSignal()

    def __init__(self, columns: list, parent=None):
        super().__init__(parent)

        self._columns = columns
        self._filter_items = {}  # column_index: FilterItem

        self._setup_ui()
        # App-level QSS handles widget styling

    def _setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("\U0001f53d \u062a\u0635\u0641\u064a\u0629 \u0645\u062a\u0642\u062f\u0645\u0629")
        title.setFont(get_font(FONT_SIZE_SUBTITLE, FONT_WEIGHT_BOLD))
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Clear all button
        clear_btn = QPushButton("\U0001f5d1\ufe0f \u0645\u0633\u062d \u0627\u0644\u0643\u0644")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setProperty("cssClass", "secondary")
        clear_btn.clicked.connect(self._clear_all)
        header_layout.addWidget(clear_btn)

        layout.addLayout(header_layout)

        # Add filter dropdown
        add_layout = QHBoxLayout()

        add_label = QLabel("\u0625\u0636\u0627\u0641\u0629 \u062a\u0635\u0641\u064a\u0629:")
        add_layout.addWidget(add_label)

        self._column_combo = QComboBox()
        self._column_combo.addItem("-- \u0627\u062e\u062a\u0631 \u0639\u0645\u0648\u062f --")
        for i, col in enumerate(self._columns):
            self._column_combo.addItem(col, i)
        self._column_combo.currentIndexChanged.connect(self._add_filter)
        add_layout.addWidget(self._column_combo)

        add_layout.addStretch()

        layout.addLayout(add_layout)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        # Filters area
        self._filters_layout = QVBoxLayout()
        self._filters_layout.setSpacing(5)
        layout.addLayout(self._filters_layout)

        # No filters label
        palette = get_current_palette()
        self._no_filters_label = QLabel("\u0644\u0627 \u062a\u0648\u062c\u062f \u062a\u0635\u0641\u064a\u0627\u062a \u0646\u0634\u0637\u0629")
        self._no_filters_label.setAlignment(Qt.AlignCenter)
        self._no_filters_label.setStyleSheet(f"color: {palette['text_muted']};")
        self._filters_layout.addWidget(self._no_filters_label)

        layout.addStretch()

    def _add_filter(self, index: int):
        """Add a new filter."""
        if index <= 0:
            return

        column_index = self._column_combo.itemData(index)
        column_name = self._column_combo.itemText(index)

        # Check if already exists
        if column_index in self._filter_items:
            self._column_combo.setCurrentIndex(0)
            return

        # Hide no filters label
        self._no_filters_label.setVisible(False)

        # Create filter item
        item = FilterItem(column_index, column_name)
        item.filter_changed.connect(self._on_filter_changed)
        item.removed.connect(self._remove_filter)

        self._filter_items[column_index] = item
        self._filters_layout.insertWidget(self._filters_layout.count() - 1, item)

        # Reset combo
        self._column_combo.setCurrentIndex(0)

    def _remove_filter(self, column_index: int):
        """Remove a filter."""
        if column_index not in self._filter_items:
            return

        item = self._filter_items.pop(column_index)
        item.deleteLater()

        # Emit cleared filter
        self.filter_changed.emit(column_index, "")

        # Show no filters label if empty
        if not self._filter_items:
            self._no_filters_label.setVisible(True)

    def _on_filter_changed(self, column_index: int, text: str):
        """Handle filter change."""
        self.filter_changed.emit(column_index, text)

    def _clear_all(self):
        """Clear all filters."""
        for column_index in list(self._filter_items.keys()):
            self._remove_filter(column_index)

        self.filters_cleared.emit()

    def get_active_filters(self) -> dict:
        """Get all active filters as dict."""
        filters = {}
        for col_idx, item in self._filter_items.items():
            text = item.get_filter_text()
            if text:
                filters[col_idx] = text
        return filters
