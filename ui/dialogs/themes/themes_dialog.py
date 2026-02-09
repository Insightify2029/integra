"""
Themes Dialog
=============
Theme selection dialog with color preview cards.
Supports 24 themes organized by category (dark/light).
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QScrollArea, QWidget
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QCursor

from core.themes import (
    get_stylesheet, get_current_theme, set_current_theme,
    get_available_themes, get_theme_display_name,
    get_theme_category
)
from core.themes.theme_palettes import get_palette
from core.utils.icons import icon
from ui.components.fluent import FluentPrimaryButton, FluentButton


class ThemesDialog(QDialog):
    """Theme selection dialog with visual previews."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("اختيار الثيم")
        self.setWindowIcon(icon('fa5s.palette', color='info'))
        self.setMinimumSize(700, 550)
        self.setStyleSheet(get_stylesheet())

        self.selected_theme = get_current_theme()
        self._cards = {}
        self._setup_ui()

    def _setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        is_dark = get_palette(get_current_theme())["is_dark"]
        text_c = "#f1f5f9" if is_dark else "#1e293b"
        muted_c = "#94a3b8" if is_dark else "#64748b"

        # Title
        title = QLabel("اختر الثيم المفضل")
        title.setFont(QFont("Cairo", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color: {text_c}; background: transparent;")
        layout.addWidget(title)

        # Scrollable area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        # Dark themes section
        dark_themes = [t for t in get_available_themes() if get_theme_category(t) == "dark"]
        if dark_themes:
            section_label = QLabel("  الثيمات الداكنة")
            section_label.setFont(QFont("Cairo", 13, QFont.Bold))
            section_label.setStyleSheet(f"color: {muted_c}; background: transparent;")
            content_layout.addWidget(section_label)
            content_layout.addWidget(self._build_theme_grid(dark_themes))

        # Light themes section
        light_themes = [t for t in get_available_themes() if get_theme_category(t) == "light"]
        if light_themes:
            content_layout.addSpacing(8)
            section_label = QLabel("  الثيمات الفاتحة")
            section_label.setFont(QFont("Cairo", 13, QFont.Bold))
            section_label.setStyleSheet(f"color: {muted_c}; background: transparent;")
            content_layout.addWidget(section_label)
            content_layout.addWidget(self._build_theme_grid(light_themes))

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        apply_btn = FluentPrimaryButton()
        apply_btn.setText("تطبيق")
        apply_btn.setIcon(icon('fa5s.check', color='#ffffff'))
        apply_btn.setIconSize(QSize(16, 16))
        apply_btn.clicked.connect(self._apply_theme)

        cancel_btn = FluentButton()
        cancel_btn.setText("إلغاء")
        cancel_btn.setIcon(icon('fa5s.times', color='danger'))
        cancel_btn.setIconSize(QSize(16, 16))
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(apply_btn)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

    def _build_theme_grid(self, theme_names):
        """Build grid of theme preview cards."""
        grid_widget = QWidget()
        grid_widget.setStyleSheet("background: transparent;")
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 4, 0, 4)
        grid.setSpacing(12)

        cols = 4
        for i, theme_name in enumerate(theme_names):
            card = self._create_theme_card(theme_name)
            grid.addWidget(card, i // cols, i % cols)

        return grid_widget

    def _create_theme_card(self, theme_name):
        """Create a visual preview card for a theme."""
        palette = get_palette(theme_name)
        is_selected = theme_name == self.selected_theme

        card = QFrame()
        card.setObjectName(f"themeCard_{theme_name}")
        card.setCursor(QCursor(Qt.PointingHandCursor))
        card.setFixedSize(150, 110)

        border_color = palette["primary"] if is_selected else palette.get("border", "#333")
        border_width = 2 if is_selected else 1

        card.setStyleSheet(f"""
            QFrame#themeCard_{theme_name} {{
                background: {palette['bg_main']};
                border: {border_width}px solid {border_color};
                border-radius: 10px;
            }}
            QFrame#themeCard_{theme_name} QLabel {{
                background: transparent;
                border: none;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # Color swatches row
        swatch_layout = QHBoxLayout()
        swatch_layout.setSpacing(4)
        for color_key in ["primary", "accent", "success", "warning", "danger"]:
            swatch = QFrame()
            swatch.setFixedSize(18, 18)
            swatch.setStyleSheet(
                f"background: {palette[color_key]}; border-radius: 4px; border: none;"
            )
            swatch_layout.addWidget(swatch)
        swatch_layout.addStretch()
        layout.addLayout(swatch_layout)

        # Simulated content preview
        preview = QFrame()
        preview.setFixedHeight(28)
        preview.setStyleSheet(
            f"background: {palette['bg_card']}; border-radius: 4px; border: none;"
        )
        layout.addWidget(preview)

        # Theme name
        name_label = QLabel(palette["display_name"])
        name_label.setFont(QFont("Cairo", 9, QFont.Bold))
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet(f"color: {palette['text_primary']};")
        layout.addWidget(name_label)

        # Selection indicator
        if is_selected:
            check = QLabel("  \u2713")
            check.setFont(QFont("Cairo", 10, QFont.Bold))
            check.setStyleSheet(f"color: {palette['primary']};")
            check.setAlignment(Qt.AlignRight)
            check.setParent(card)
            check.move(int(card.width() - 30), 4)
            check.resize(26, 20)

        # Click handler
        card.mousePressEvent = lambda event, t=theme_name: self._select_theme(t)
        self._cards[theme_name] = card

        return card

    def _select_theme(self, theme_name):
        """Handle theme card click."""
        old = self.selected_theme
        self.selected_theme = theme_name

        # Update old card style
        if old in self._cards and old != theme_name:
            old_palette = get_palette(old)
            old_card = self._cards[old]
            old_card.setStyleSheet(f"""
                QFrame#themeCard_{old} {{
                    background: {old_palette['bg_main']};
                    border: 1px solid {old_palette.get('border', '#333')};
                    border-radius: 10px;
                }}
                QFrame#themeCard_{old} QLabel {{
                    background: transparent;
                    border: none;
                }}
            """)

        # Update new card style
        if theme_name in self._cards:
            new_palette = get_palette(theme_name)
            new_card = self._cards[theme_name]
            new_card.setStyleSheet(f"""
                QFrame#themeCard_{theme_name} {{
                    background: {new_palette['bg_main']};
                    border: 2px solid {new_palette['primary']};
                    border-radius: 10px;
                }}
                QFrame#themeCard_{theme_name} QLabel {{
                    background: transparent;
                    border: none;
                }}
            """)

    def _apply_theme(self):
        """Apply selected theme."""
        set_current_theme(self.selected_theme)
        self.accept()

    def get_selected_theme(self):
        """Get the selected theme name."""
        return self.selected_theme
