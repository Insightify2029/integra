"""
Launcher Window - Professional ERP Design
==========================================
Main application launcher with professional top navigation,
grouped module menus, and clean dashboard layout.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QGridLayout, QToolButton,
    QMenu, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QColor, QCursor, QPixmap

import os

from ui.windows.base import BaseWindow
from ui.dialogs import SettingsDialog, ThemesDialog

from .launcher_statusbar import LauncherStatusBar

from core.config.app import APP_VERSION
from core.config.modules import get_enabled_modules
from core.database.connection import connect, disconnect
from core.themes import (
    get_stylesheet, get_current_palette, is_dark_theme,
    get_font, FONT_SIZE_TINY, FONT_SIZE_SMALL, FONT_SIZE_BODY,
    FONT_SIZE_SUBTITLE, FONT_SIZE_TITLE, FONT_SIZE_HEADING,
    FONT_SIZE_DISPLAY, FONT_SIZE_MODULE_ICON,
    FONT_WEIGHT_BOLD, FONT_FAMILY_ARABIC,
)
from core.utils.icons import icon as qta_icon, QTAWESOME_AVAILABLE
from ui.components.notifications import toast_info


# ─── Module grouping for professional menu ─────────────────────
MODULE_GROUPS = [
    {
        'id': 'hr',
        'name_ar': 'الموارد البشرية',
        'icon': 'fa5s.users',
        'color': '#2563eb',
        'modules': ['mostahaqat', 'time_intelligence'],
    },
    {
        'id': 'finance',
        'name_ar': 'المالية',
        'icon': 'fa5s.coins',
        'color': '#10b981',
        'modules': ['costing', 'insurance', 'custody'],
    },
    {
        'id': 'operations',
        'name_ar': 'العمليات',
        'icon': 'fa5s.cogs',
        'color': '#f59e0b',
        'modules': ['logistics', 'calendar', 'dashboard'],
    },
    {
        'id': 'tools',
        'name_ar': 'الأدوات الذكية',
        'icon': 'fa5s.magic',
        'color': '#8b5cf6',
        'modules': ['email', 'designer', 'bi', 'copilot'],
    },
    {
        'id': 'system',
        'name_ar': 'النظام',
        'icon': 'fa5s.server',
        'color': '#06b6d4',
        'modules': ['file_manager', 'device_manager', 'desktop_apps'],
    },
]

# QtAwesome icon mapping per module
MODULE_ICON_MAP = {
    'mostahaqat': 'fa5s.users',
    'costing': 'fa5s.chart-bar',
    'logistics': 'fa5s.truck',
    'custody': 'fa5s.key',
    'insurance': 'fa5s.shield-alt',
    'email': 'fa5s.envelope',
    'designer': 'fa5s.drafting-compass',
    'calendar': 'fa5s.calendar-alt',
    'dashboard': 'fa5s.tachometer-alt',
    'bi': 'fa5s.chart-pie',
    'copilot': 'fa5s.robot',
    'time_intelligence': 'fa5s.clock',
    'file_manager': 'fa5s.folder-open',
    'device_manager': 'fa5s.print',
    'desktop_apps': 'fa5s.th-large',
}


class LauncherWindow(BaseWindow):
    """Professional ERP-style launcher window."""

    _open_windows = {}

    def __init__(self):
        super().__init__()
        self._modules_map = {}
        for m in get_enabled_modules():
            self._modules_map[m['id']] = m

        self._setup_ui()
        self.showMaximized()

    # ═══════════════════════════════════════════════════════
    # UI Setup
    # ═══════════════════════════════════════════════════════

    def _setup_ui(self):
        """Build the complete professional UI."""
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 1) Top navigation bar
        root.addWidget(self._build_top_nav())

        # 2) Thin accent line
        palette = get_current_palette()
        accent = QFrame()
        accent.setFixedHeight(2)
        accent.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
            f" stop:0 transparent, stop:0.2 {palette['primary']},"
            f" stop:0.8 {palette['primary_hover']}, stop:1 transparent);"
        )
        root.addWidget(accent)

        # 3) Center area - Logo only
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setAlignment(Qt.AlignCenter)

        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)
        logo_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', '..', '..', 'resources', 'icons', 'integra.png'
        )
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                int(280), int(280),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            logo_label.setPixmap(scaled)
        else:
            logo_label.setText("INTEGRA")
            logo_label.setFont(get_font(FONT_SIZE_DISPLAY + 20, FONT_WEIGHT_BOLD))
            logo_label.setStyleSheet(f"color: {palette['primary']};")
        logo_label.setStyleSheet("background: transparent;")
        center_layout.addWidget(logo_label)

        root.addWidget(center_widget, 1)

        # 4) Status bar
        self.status_bar = LauncherStatusBar()
        self.setStatusBar(self.status_bar)

    # ─── Top Navigation Bar ──────────────────────────────────

    def _build_top_nav(self):
        """Build the professional top navigation bar."""
        palette = get_current_palette()
        bg = palette['bg_sidebar']
        border_c = palette['border']
        text_c = palette['text_primary']
        muted_c = palette['text_muted']
        hover_bg = palette['bg_hover']

        nav = QWidget()
        nav.setFixedHeight(52)
        nav.setObjectName("topNav")
        nav.setStyleSheet(f"""
            QWidget#topNav {{
                background: {bg};
                border-bottom: 1px solid {border_c};
            }}
        """)

        layout = QHBoxLayout(nav)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(0)

        # ── Brand / Logo ──
        brand = QLabel("INTEGRA")
        brand.setFont(get_font(FONT_SIZE_TITLE, FONT_WEIGHT_BOLD))
        brand.setStyleSheet(
            f"color: {palette['primary']}; letter-spacing: 4px;"
            f" padding: 0 20px 0 4px; background: transparent;"
        )
        layout.addWidget(brand)

        # ── Separator ──
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedHeight(28)
        sep.setStyleSheet(f"color: {border_c};")
        layout.addWidget(sep)

        layout.addSpacing(8)

        # ── Module Group Menus ──
        btn_style = f"""
            QToolButton {{
                color: {text_c};
                background: transparent;
                border: none;
                padding: 8px 14px;
                border-radius: 6px;
                font-family: {FONT_FAMILY_ARABIC};
                font-size: {FONT_SIZE_SMALL}pt;
            }}
            QToolButton:hover {{
                background: {hover_bg};
            }}
            QToolButton::menu-indicator {{ image: none; }}
        """

        menu_qss = self._get_menu_stylesheet()

        for group in MODULE_GROUPS:
            btn = QToolButton()
            btn.setText(f"  {group['name_ar']}  ")
            btn.setFont(get_font(FONT_SIZE_SMALL))
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setPopupMode(QToolButton.InstantPopup)
            btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

            if QTAWESOME_AVAILABLE:
                btn.setIcon(qta_icon(group['icon'], color=group['color']))
                btn.setIconSize(QSize(16, 16))

            btn.setStyleSheet(btn_style)

            menu = QMenu(btn)
            menu.setStyleSheet(menu_qss)

            for mid in group['modules']:
                mod = self._modules_map.get(mid)
                if not mod:
                    continue
                ic = qta_icon(
                    MODULE_ICON_MAP.get(mid, 'fa5s.cube'),
                    color=mod['color']
                ) if QTAWESOME_AVAILABLE else None
                act = menu.addAction(f"  {mod['name_ar']}")
                if ic:
                    act.setIcon(ic)
                act.setData(mid)
                act.triggered.connect(
                    lambda checked, m=mid: self._open_module(m)
                )

            btn.setMenu(menu)
            layout.addWidget(btn)

        layout.addStretch()

        # ── Right side: Settings + Theme ──
        right_btn_style = f"""
            QToolButton {{
                background: transparent;
                border: none;
                padding: 8px;
                border-radius: 6px;
            }}
            QToolButton:hover {{
                background: {hover_bg};
            }}
        """

        settings_btn = QToolButton()
        settings_btn.setToolTip("الإعدادات")
        settings_btn.setCursor(QCursor(Qt.PointingHandCursor))
        if QTAWESOME_AVAILABLE:
            settings_btn.setIcon(qta_icon('fa5s.cog', color=muted_c))
            settings_btn.setIconSize(QSize(18, 18))
        else:
            settings_btn.setText("⚙")
        settings_btn.setStyleSheet(right_btn_style)
        settings_btn.clicked.connect(self._show_settings)
        layout.addWidget(settings_btn)

        theme_btn = QToolButton()
        theme_btn.setToolTip("تغيير الثيم")
        theme_btn.setCursor(QCursor(Qt.PointingHandCursor))
        if QTAWESOME_AVAILABLE:
            theme_btn.setIcon(qta_icon('fa5s.palette', color=muted_c))
            theme_btn.setIconSize(QSize(18, 18))
        else:
            theme_btn.setText("🎨")
        theme_btn.setStyleSheet(right_btn_style)
        theme_btn.clicked.connect(self._show_themes)
        layout.addWidget(theme_btn)

        return nav

    def _get_menu_stylesheet(self) -> str:
        """Get dropdown menu stylesheet using palette colors."""
        palette = get_current_palette()
        return f"""
            QMenu {{
                background: {palette['bg_card']};
                border: 1px solid {palette['border']};
                border-radius: 8px;
                padding: 6px;
            }}
            QMenu::item {{
                color: {palette['text_primary']};
                padding: 10px 24px 10px 12px;
                border-radius: 6px;
                font-family: {FONT_FAMILY_ARABIC};
                font-size: {FONT_SIZE_SUBTITLE - 3}pt;
            }}
            QMenu::item:selected {{
                background: {palette['bg_hover']};
                color: {palette['primary']};
            }}
            QMenu::separator {{
                height: 1px;
                background: {palette['border']};
                margin: 4px 8px;
            }}
        """

    # ─── Welcome Section ─────────────────────────────────────

    def _build_welcome_section(self, parent_layout):
        """Build the welcome header area."""
        palette = get_current_palette()

        section = QWidget()
        lay = QVBoxLayout(section)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        title = QLabel("مرحباً بك في INTEGRA")
        title.setFont(get_font(FONT_SIZE_HEADING, FONT_WEIGHT_BOLD))
        title.setStyleSheet(f"color: {palette['text_primary']}; background: transparent;")
        lay.addWidget(title)

        subtitle = QLabel(
            "اختر أحد الموديولات للبدء، أو استخدم القوائم في الأعلى للتنقل السريع"
        )
        subtitle.setFont(get_font(FONT_SIZE_SUBTITLE - 3))
        subtitle.setStyleSheet(f"color: {palette['text_muted']}; background: transparent;")
        lay.addWidget(subtitle)

        parent_layout.addWidget(section)

    # ─── Module Grid ─────────────────────────────────────────

    def _build_module_grid(self, parent_layout):
        """Build module cards grid grouped by category."""
        for group in MODULE_GROUPS:
            group_mods = [
                self._modules_map[mid]
                for mid in group['modules']
                if mid in self._modules_map
            ]
            if not group_mods:
                continue

            # Group header
            header = QLabel(f"  {group['name_ar']}")
            header.setFont(get_font(FONT_SIZE_SUBTITLE - 1, FONT_WEIGHT_BOLD))
            header.setStyleSheet(
                f"color: {group['color']}; background: transparent; padding-top: 8px;"
            )
            parent_layout.addWidget(header)

            # Separator line
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFixedHeight(1)
            line.setStyleSheet(f"background: {group['color']}40;")
            parent_layout.addWidget(line)

            # Cards grid
            grid_widget = QWidget()
            grid = QGridLayout(grid_widget)
            grid.setContentsMargins(0, 8, 0, 8)
            grid.setSpacing(16)

            cols = 5
            for i, mod in enumerate(group_mods):
                card = self._create_module_card(mod, group['color'])
                grid.addWidget(card, i // cols, i % cols)

            # Fill remaining columns so cards stay left-aligned
            remaining = len(group_mods) % cols
            if remaining > 0:
                last_row = (len(group_mods) - 1) // cols
                for j in range(remaining, cols):
                    spacer = QWidget()
                    spacer.setSizePolicy(
                        QSizePolicy.Expanding, QSizePolicy.Preferred
                    )
                    grid.addWidget(spacer, last_row, j)

            parent_layout.addWidget(grid_widget)

    def _create_module_card(self, mod: dict, group_color: str) -> QFrame:
        """Create a single professional module card."""
        palette = get_current_palette()
        card_bg = palette['bg_card']
        card_hover = palette['bg_hover']
        text_c = palette['text_primary']
        muted_c = palette['text_muted']
        border_c = palette['border']
        accent = mod.get('color', group_color)

        card = QFrame()
        card.setObjectName("moduleCard")
        card.setCursor(QCursor(Qt.PointingHandCursor))
        card.setFixedSize(200, 140)
        card.setStyleSheet(f"""
            QFrame#moduleCard {{
                background: {card_bg};
                border: 1px solid {border_c};
                border-radius: 12px;
            }}
            QFrame#moduleCard:hover {{
                background: {card_hover};
                border: 1px solid {accent};
            }}
            QFrame#moduleCard QLabel {{
                background: transparent;
                border: none;
            }}
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 40 if palette['is_dark'] else 20))
        card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 14)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignCenter)

        # Icon
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignCenter)
        qta_name = MODULE_ICON_MAP.get(mod['id'])
        if QTAWESOME_AVAILABLE and qta_name:
            pixmap = qta_icon(qta_name, color=accent).pixmap(36, 36)
            icon_label.setPixmap(pixmap)
        else:
            icon_label.setText(mod.get('icon', ''))
            icon_label.setFont(get_font(FONT_SIZE_DISPLAY))
        icon_label.setFixedHeight(42)
        layout.addWidget(icon_label)

        # Arabic name
        name_ar = QLabel(mod['name_ar'])
        name_ar.setFont(get_font(FONT_SIZE_BODY, FONT_WEIGHT_BOLD))
        name_ar.setAlignment(Qt.AlignCenter)
        name_ar.setStyleSheet(f"color: {text_c};")
        name_ar.setWordWrap(True)
        layout.addWidget(name_ar)

        # English name
        name_en = QLabel(mod['name_en'])
        name_en.setFont(get_font(FONT_SIZE_TINY))
        name_en.setAlignment(Qt.AlignCenter)
        name_en.setStyleSheet(f"color: {muted_c};")
        layout.addWidget(name_en)

        # Click handler
        card.mousePressEvent = lambda event, mid=mod['id']: (
            self._open_module(mid) if event.button() == Qt.LeftButton else None
        )

        return card

    # ═══════════════════════════════════════════════════════
    # Actions
    # ═══════════════════════════════════════════════════════

    def _show_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec_()

    def _show_themes(self):
        dialog = ThemesDialog(self)
        if dialog.exec_():
            self.setStyleSheet(get_stylesheet())
            QTimer.singleShot(50, self._rebuild_ui)
            for window in self._open_windows.values():
                if window and window.isVisible():
                    window.setStyleSheet(get_stylesheet())

    def _rebuild_ui(self):
        """Rebuild UI after theme change."""
        old_central = self.centralWidget()
        self._setup_ui()
        if old_central:
            old_central.deleteLater()

    def _open_module(self, module_id: str):
        """Open a module window."""
        # Clean up closed windows
        closed = [
            k for k, w in self._open_windows.items()
            if w is None or not w.isVisible()
        ]
        for k in closed:
            w = self._open_windows.pop(k, None)
            if w is not None:
                w.deleteLater()

        if module_id in self._open_windows:
            window = self._open_windows[module_id]
            if window and window.isVisible():
                window.activateWindow()
                window.raise_()
                return

        if module_id == "mostahaqat":
            from modules.mostahaqat import MostahaqatWindow
            window = MostahaqatWindow()
            window.show()
            self._open_windows[module_id] = window
        elif module_id == "email":
            from modules.email import EmailWindow
            window = EmailWindow()
            window.show()
            self._open_windows[module_id] = window
        elif module_id == "bi":
            from ui.dialogs.bi_settings import BISettingsDialog
            dialog = BISettingsDialog(self)
            dialog.exec_()
        elif module_id == "copilot":
            from modules.copilot.window import CopilotMainWindow
            window = CopilotMainWindow()
            window.show()
            self._open_windows[module_id] = window
        elif module_id == "time_intelligence":
            from modules.time_intelligence import TimeIntelligenceWindow
            window = TimeIntelligenceWindow()
            window.show()
            self._open_windows[module_id] = window
        elif module_id == "file_manager":
            from modules.file_manager import FileManagerWindow
            window = FileManagerWindow()
            window.show()
            self._open_windows[module_id] = window
        elif module_id == "device_manager":
            from modules.device_manager import DeviceManagerWindow
            window = DeviceManagerWindow()
            window.show()
            self._open_windows[module_id] = window
        elif module_id == "desktop_apps":
            from modules.desktop_apps import DesktopAppsWindow
            window = DesktopAppsWindow()
            window.show()
            self._open_windows[module_id] = window
        else:
            toast_info(self, "قريباً", f"موديول {module_id} قيد التطوير")

    def closeEvent(self, event):
        """Clean shutdown."""
        for window in self._open_windows.values():
            if window:
                window.close()
                window.deleteLater()
        self._open_windows.clear()

        try:
            disconnect()
        except Exception:
            pass

        event.accept()
