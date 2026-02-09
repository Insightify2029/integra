"""
Themes & Styles Dialog
======================
Comprehensive dialog for selecting UI Style and Color Theme.
- Style tab: 10 UI styles with visual previews
- Theme tab: 24 color themes organized by dark/light
- Real-time preview and instant application
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QScrollArea, QWidget, QTabWidget,
    QPushButton,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QCursor

from core.themes import (
    get_current_theme, get_current_style,
    get_available_themes, get_available_styles,
    get_theme_display_name, get_theme_category,
    get_style_display_name, get_style_description,
    switch_theme_and_style,
    get_current_palette, get_palette,
    get_font,
    FONT_SIZE_TINY, FONT_SIZE_SMALL, FONT_SIZE_BODY,
    FONT_SIZE_SUBTITLE, FONT_SIZE_TITLE,
    FONT_WEIGHT_BOLD, FONT_WEIGHT_NORMAL,
)
from core.themes.theme_styles import STYLE_DEFINITIONS
from core.utils.icons import icon


class ThemesDialog(QDialog):
    """Theme and Style selection dialog with visual previews."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("المظهر والأنماط")
        self.setWindowIcon(icon('fa5s.palette', color='info'))
        self.setMinimumSize(800, 620)

        self.selected_theme = get_current_theme()
        self.selected_style = get_current_style()
        self._theme_cards = {}
        self._style_cards = {}
        self._setup_ui()

    def _setup_ui(self):
        """Setup dialog UI with tabs for Style and Theme."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        p = get_current_palette()

        # Title
        title = QLabel("تخصيص المظهر")
        title.setFont(get_font(FONT_SIZE_TITLE, FONT_WEIGHT_BOLD))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("اختر نمط الواجهة ولون الثيم المفضل")
        subtitle.setFont(get_font(FONT_SIZE_BODY))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"color: {p['text_secondary']};")
        layout.addWidget(subtitle)

        # Tab Widget
        tabs = QTabWidget()
        tabs.setFont(get_font(FONT_SIZE_BODY, FONT_WEIGHT_BOLD))

        # Style Tab
        style_tab = self._build_style_tab()
        tabs.addTab(style_tab, icon('fa5s.layer-group', color='info'), "  النمط (Style)")

        # Theme Tab
        theme_tab = self._build_theme_tab()
        tabs.addTab(theme_tab, icon('fa5s.palette', color='info'), "  الألوان (Theme)")

        layout.addWidget(tabs, 1)

        # Current selection info
        self._info_label = QLabel()
        self._info_label.setAlignment(Qt.AlignCenter)
        self._info_label.setFont(get_font(FONT_SIZE_SMALL))
        self._update_info_label()
        layout.addWidget(self._info_label)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        apply_btn = QPushButton("  تطبيق")
        apply_btn.setIcon(icon('fa5s.check', color='#ffffff'))
        apply_btn.setIconSize(QSize(16, 16))
        apply_btn.setCursor(QCursor(Qt.PointingHandCursor))
        apply_btn.clicked.connect(self._apply_selection)

        cancel_btn = QPushButton("  إلغاء")
        cancel_btn.setProperty("cssClass", "secondary")
        cancel_btn.setIcon(icon('fa5s.times', color='danger'))
        cancel_btn.setIconSize(QSize(16, 16))
        cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(apply_btn)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

    # ─── Style Tab ───────────────────────────────────

    def _build_style_tab(self):
        """Build the style selection tab."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        grid = QGridLayout(content)
        grid.setContentsMargins(12, 12, 12, 12)
        grid.setSpacing(14)

        cols = 3
        for i, style_name in enumerate(get_available_styles()):
            card = self._create_style_card(style_name)
            grid.addWidget(card, i // cols, i % cols)

        # Fill remaining cells
        remaining = cols - (len(get_available_styles()) % cols)
        if remaining < cols:
            for j in range(remaining):
                spacer = QWidget()
                grid.addWidget(spacer, len(get_available_styles()) // cols,
                             len(get_available_styles()) % cols + j)

        grid.setRowStretch(grid.rowCount(), 1)
        scroll.setWidget(content)
        return scroll

    def _create_style_card(self, style_name: str):
        """Create a visual preview card for a UI style."""
        style_def = STYLE_DEFINITIONS[style_name]
        p = get_current_palette()
        is_selected = style_name == self.selected_style

        card = QFrame()
        card.setObjectName(f"styleCard_{style_name}")
        card.setCursor(QCursor(Qt.PointingHandCursor))
        card.setFixedHeight(140)
        card.setMinimumWidth(200)

        border_color = p["primary"] if is_selected else p["border"]
        border_width = 2 if is_selected else 1

        card.setStyleSheet(f"""
            QFrame#styleCard_{style_name} {{
                background: {p['bg_card']};
                border: {border_width}px solid {border_color};
                border-radius: 12px;
            }}
            QFrame#styleCard_{style_name} QLabel {{
                background: transparent;
                border: none;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        # Style name
        name_label = QLabel(style_def["display_name"])
        name_label.setFont(get_font(FONT_SIZE_BODY, FONT_WEIGHT_BOLD))
        layout.addWidget(name_label)

        # Description
        desc_label = QLabel(style_def.get("description", ""))
        desc_label.setFont(get_font(FONT_SIZE_SMALL))
        desc_label.setStyleSheet(f"color: {p['text_secondary']};")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Visual preview row - simulate the style shape
        preview_layout = QHBoxLayout()
        preview_layout.setSpacing(6)

        r = style_def["border_radius_md"]
        # Mini button preview
        btn_preview = QFrame()
        btn_preview.setFixedSize(60, 24)
        btn_preview.setStyleSheet(
            f"background: {p['primary']}; border-radius: {min(r, 12)}px; border: none;"
        )
        preview_layout.addWidget(btn_preview)

        # Mini input preview
        input_preview = QFrame()
        input_preview.setFixedSize(80, 24)
        r_sm = style_def["border_radius_sm"]
        input_preview.setStyleSheet(
            f"background: {p['bg_input']}; border: 1px solid {p['border']}; "
            f"border-radius: {min(r_sm, 8)}px;"
        )
        preview_layout.addWidget(input_preview)

        # Mini card preview
        card_preview = QFrame()
        card_preview.setFixedSize(50, 24)
        r_lg = style_def["border_radius_lg"]
        card_preview.setStyleSheet(
            f"background: {p['bg_hover']}; border-radius: {min(r_lg, 10)}px; border: none;"
        )
        preview_layout.addWidget(card_preview)
        preview_layout.addStretch()

        layout.addLayout(preview_layout)

        # Selection check
        if is_selected:
            check = QLabel(" \u2713")
            check.setFont(get_font(FONT_SIZE_BODY, FONT_WEIGHT_BOLD))
            check.setStyleSheet(f"color: {p['primary']};")
            check.setAlignment(Qt.AlignRight)
            check.setParent(card)
            check.move(int(card.minimumWidth() - 30), 8)
            check.resize(26, 20)

        card.mousePressEvent = lambda event, sn=style_name: self._select_style(sn)
        self._style_cards[style_name] = card
        return card

    def _select_style(self, style_name: str):
        """Handle style card selection."""
        old = self.selected_style
        self.selected_style = style_name
        p = get_current_palette()

        if old in self._style_cards and old != style_name:
            old_card = self._style_cards[old]
            old_card.setStyleSheet(f"""
                QFrame#styleCard_{old} {{
                    background: {p['bg_card']};
                    border: 1px solid {p['border']};
                    border-radius: 12px;
                }}
                QFrame#styleCard_{old} QLabel {{
                    background: transparent; border: none;
                }}
            """)

        if style_name in self._style_cards:
            new_card = self._style_cards[style_name]
            new_card.setStyleSheet(f"""
                QFrame#styleCard_{style_name} {{
                    background: {p['bg_card']};
                    border: 2px solid {p['primary']};
                    border-radius: 12px;
                }}
                QFrame#styleCard_{style_name} QLabel {{
                    background: transparent; border: none;
                }}
            """)

        self._update_info_label()

    # ─── Theme Tab ───────────────────────────────────

    def _build_theme_tab(self):
        """Build the theme selection tab."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(14)

        p = get_current_palette()

        # Dark themes
        dark_themes = [t for t in get_available_themes() if get_theme_category(t) == "dark"]
        if dark_themes:
            label = QLabel("  الثيمات الداكنة")
            label.setFont(get_font(FONT_SIZE_BODY, FONT_WEIGHT_BOLD))
            label.setStyleSheet(f"color: {p['text_secondary']};")
            content_layout.addWidget(label)
            content_layout.addWidget(self._build_theme_grid(dark_themes))

        # Light themes
        light_themes = [t for t in get_available_themes() if get_theme_category(t) == "light"]
        if light_themes:
            content_layout.addSpacing(8)
            label = QLabel("  الثيمات الفاتحة")
            label.setFont(get_font(FONT_SIZE_BODY, FONT_WEIGHT_BOLD))
            label.setStyleSheet(f"color: {p['text_secondary']};")
            content_layout.addWidget(label)
            content_layout.addWidget(self._build_theme_grid(light_themes))

        content_layout.addStretch()
        scroll.setWidget(content)
        return scroll

    def _build_theme_grid(self, theme_names: list):
        """Build grid of theme preview cards."""
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 4, 0, 4)
        grid.setSpacing(10)

        cols = 4
        for i, theme_name in enumerate(theme_names):
            card = self._create_theme_card(theme_name)
            grid.addWidget(card, i // cols, i % cols)

        return grid_widget

    def _create_theme_card(self, theme_name: str):
        """Create a visual preview card for a color theme."""
        palette = get_palette(theme_name)
        is_selected = theme_name == self.selected_theme

        card = QFrame()
        card.setObjectName(f"themeCard_{theme_name}")
        card.setCursor(QCursor(Qt.PointingHandCursor))
        card.setFixedSize(155, 115)

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
        name_label.setFont(get_font(FONT_SIZE_TINY, FONT_WEIGHT_BOLD))
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet(f"color: {palette['text_primary']};")
        layout.addWidget(name_label)

        # Selection indicator
        if is_selected:
            check = QLabel("  \u2713")
            check.setFont(get_font(FONT_SIZE_SMALL, FONT_WEIGHT_BOLD))
            check.setStyleSheet(f"color: {palette['primary']};")
            check.setAlignment(Qt.AlignRight)
            check.setParent(card)
            check.move(int(card.width() - 30), 4)
            check.resize(26, 20)

        card.mousePressEvent = lambda event, t=theme_name: self._select_theme(t)
        self._theme_cards[theme_name] = card
        return card

    def _select_theme(self, theme_name: str):
        """Handle theme card selection."""
        old = self.selected_theme
        self.selected_theme = theme_name

        if old in self._theme_cards and old != theme_name:
            old_palette = get_palette(old)
            old_card = self._theme_cards[old]
            old_card.setStyleSheet(f"""
                QFrame#themeCard_{old} {{
                    background: {old_palette['bg_main']};
                    border: 1px solid {old_palette.get('border', '#333')};
                    border-radius: 10px;
                }}
                QFrame#themeCard_{old} QLabel {{
                    background: transparent; border: none;
                }}
            """)

        if theme_name in self._theme_cards:
            new_palette = get_palette(theme_name)
            new_card = self._theme_cards[theme_name]
            new_card.setStyleSheet(f"""
                QFrame#themeCard_{theme_name} {{
                    background: {new_palette['bg_main']};
                    border: 2px solid {new_palette['primary']};
                    border-radius: 10px;
                }}
                QFrame#themeCard_{theme_name} QLabel {{
                    background: transparent; border: none;
                }}
            """)

        self._update_info_label()

    # ─── Common ──────────────────────────────────────

    def _update_info_label(self):
        """Update the current selection display."""
        p = get_current_palette()
        style_display = get_style_display_name(self.selected_style)
        theme_display = get_theme_display_name(self.selected_theme)
        self._info_label.setText(
            f"الاختيار الحالي:  النمط: {style_display}  |  الألوان: {theme_display}"
        )
        self._info_label.setStyleSheet(f"color: {p['text_secondary']};")

    def _apply_selection(self):
        """Apply selected theme and style."""
        switch_theme_and_style(self.selected_theme, self.selected_style)
        self.accept()

    def get_selected_theme(self) -> str:
        """Get the selected theme name."""
        return self.selected_theme

    def get_selected_style(self) -> str:
        """Get the selected style name."""
        return self.selected_style
