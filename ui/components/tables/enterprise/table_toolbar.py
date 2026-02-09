"""
Table Toolbar
=============
Enterprise table toolbar. Styling handled by centralized theme system.
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel,
    QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize

from core.themes import (
    get_current_palette, get_font,
    FONT_SIZE_TITLE, FONT_SIZE_SMALL, FONT_WEIGHT_BOLD
)
from core.utils.icons import icon
from .search_box import SearchBox


class TableToolbar(QWidget):
    """
    Toolbar for Enterprise Table.
    Contains search, filters, and action buttons.
    App-level QSS handles QPushButton and QLabel styling.

    Signals:
        search_changed(str): Search text changed
        filter_clicked(): Filter button clicked
        columns_clicked(): Column chooser button clicked
        export_clicked(): Export button clicked
        refresh_clicked(): Refresh button clicked
        add_clicked(): Add new item clicked
    """

    # Signals
    search_changed = pyqtSignal(str)
    filter_clicked = pyqtSignal()
    columns_clicked = pyqtSignal()
    export_clicked = pyqtSignal()
    refresh_clicked = pyqtSignal()
    add_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._show_add_button = False
        self._title = ""

        self._setup_ui()
        self._apply_toolbar_style()

    def _setup_ui(self):
        """Setup toolbar UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)

        # Title label
        self._title_label = QLabel()
        self._title_label.setFont(get_font(FONT_SIZE_TITLE, FONT_WEIGHT_BOLD))
        layout.addWidget(self._title_label)

        # Spacer
        layout.addStretch()

        # Row count label
        self._count_label = QLabel()
        self._count_label.setFont(get_font(FONT_SIZE_SMALL))
        layout.addWidget(self._count_label)

        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.VLine)
        sep1.setFixedWidth(1)
        layout.addWidget(sep1)

        # Search box
        self._search_box = SearchBox()
        self._search_box.setFixedWidth(300)
        self._search_box.search_changed.connect(self.search_changed.emit)
        layout.addWidget(self._search_box)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.VLine)
        sep2.setFixedWidth(1)
        layout.addWidget(sep2)

        # Action buttons with QtAwesome icons
        self._filter_btn = self._create_button(
            "\u062a\u0635\u0641\u064a\u0629", self.filter_clicked.emit,
            btn_icon=icon('fa5s.filter', color='info')
        )
        layout.addWidget(self._filter_btn)

        self._columns_btn = self._create_button(
            "\u0627\u0644\u0623\u0639\u0645\u062f\u0629", self.columns_clicked.emit,
            btn_icon=icon('fa5s.columns', color='info')
        )
        layout.addWidget(self._columns_btn)

        self._export_btn = self._create_button(
            "\u062a\u0635\u062f\u064a\u0631", self.export_clicked.emit,
            btn_icon=icon('fa5s.file-export', color='success')
        )
        layout.addWidget(self._export_btn)

        self._refresh_btn = self._create_button(
            "\u062a\u062d\u062f\u064a\u062b", self.refresh_clicked.emit,
            btn_icon=icon('fa5s.sync-alt', color='info')
        )
        layout.addWidget(self._refresh_btn)

        # Add button (optional)
        self._add_btn = self._create_button(
            "\u0625\u0636\u0627\u0641\u0629", self.add_clicked.emit, primary=True,
            btn_icon=icon('fa5s.plus', color='#ffffff')
        )
        self._add_btn.setVisible(False)
        layout.addWidget(self._add_btn)

    def _create_button(self, text: str, callback, primary: bool = False,
                       btn_icon=None) -> QPushButton:
        """Create a toolbar button with optional QtAwesome icon."""
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(callback)
        if not primary:
            btn.setProperty("cssClass", "secondary")
        return btn

    def _apply_toolbar_style(self):
        """Apply minimal toolbar-specific styling (border-bottom only)."""
        palette = get_current_palette()
        # Only set the toolbar container border; buttons/labels inherit from app-level QSS
        self.setStyleSheet(f"""
            TableToolbar {{
                background-color: {palette['bg_card']};
                border-bottom: 1px solid {palette['border']};
            }}
        """)
        self._count_label.setStyleSheet(f"color: {palette['text_muted']};")

    # ===================================================================
    # Public API
    # ===================================================================

    def set_title(self, title: str):
        """Set toolbar title."""
        self._title = title
        self._title_label.setText(title)

    def set_row_count(self, total: int, visible: int = None):
        """Set row count display."""
        if visible is not None and visible != total:
            self._count_label.setText(f"\u0639\u0631\u0636 {visible} \u0645\u0646 {total}")
        else:
            self._count_label.setText(f"\u0625\u062c\u0645\u0627\u0644\u064a: {total}")

    def show_add_button(self, show: bool = True):
        """Show or hide add button."""
        self._show_add_button = show
        self._add_btn.setVisible(show)

    def set_add_button_text(self, text: str):
        """Set add button text."""
        self._add_btn.setText(text)

    def get_search_text(self) -> str:
        """Get current search text."""
        return self._search_box.get_text()

    def clear_search(self):
        """Clear search box."""
        self._search_box.clear()

    def set_search_placeholder(self, text: str):
        """Set search placeholder text."""
        self._search_box.set_placeholder(text)
