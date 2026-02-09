"""
Theme Generator
===============
Generates complete QSS stylesheets by combining a color palette + a UI style.
This is the core engine that produces the final stylesheet applied to QApplication.
"""

from .theme_palettes import get_palette
from .theme_styles import get_style
from .theme_fonts import (
    FONT_FAMILY_ARABIC, FONT_FAMILY_ENGLISH,
    FONT_SIZE_TINY, FONT_SIZE_SMALL, FONT_SIZE_BODY,
    FONT_SIZE_SUBTITLE, FONT_SIZE_TITLE,
    get_scaled_size,
)


def generate_stylesheet(theme_name: str, style_name: str = "modern") -> str:
    """
    Generate a complete QSS stylesheet by combining a palette and a style.

    Args:
        theme_name: Color theme key from THEME_PALETTES.
        style_name: UI style key from STYLE_DEFINITIONS.

    Returns:
        Complete QSS string ready to apply via QApplication.setStyleSheet().
    """
    p = get_palette(theme_name)
    s = get_style(style_name)
    return _build_qss(p, s)


def _build_qss(p: dict, s: dict) -> str:
    """Build complete QSS from palette + style."""
    return (
        _base_qss(p, s)
        + _label_qss(p, s)
        + _button_qss(p, s)
        + _input_qss(p, s)
        + _combobox_qss(p, s)
        + _checkbox_radio_qss(p, s)
        + _spinbox_qss(p, s)
        + _table_qss(p, s)
        + _tree_list_qss(p, s)
        + _tab_qss(p, s)
        + _menu_qss(p, s)
        + _toolbar_qss(p, s)
        + _statusbar_qss(p, s)
        + _scrollbar_qss(p, s)
        + _dialog_qss(p, s)
        + _groupbox_qss(p, s)
        + _frame_qss(p, s)
        + _scrollarea_qss(p, s)
        + _progressbar_qss(p, s)
        + _slider_qss(p, s)
        + _splitter_qss(p, s)
        + _tooltip_qss(p, s)
        + _calendar_qss(p, s)
        + _dateedit_qss(p, s)
    )


# ─── Helper ──────────────────────────────────────────

def _fs(base_size: int, s: dict) -> int:
    """Get scaled font size."""
    return get_scaled_size(base_size, s.get("font_scale", 1.0))


def _font_stack() -> str:
    """CSS font-family stack."""
    return f'"{FONT_FAMILY_ARABIC}", "{FONT_FAMILY_ENGLISH}", sans-serif'


# ─── QSS Sections ───────────────────────────────────

def _base_qss(p: dict, s: dict) -> str:
    return f"""
        /* ═══ Base ═══ */
        QMainWindow, QWidget {{
            background-color: {p['bg_main']};
            color: {p['text_primary']};
            font-family: {_font_stack()};
            font-size: {_fs(FONT_SIZE_BODY, s)}px;
        }}
    """


def _label_qss(p: dict, s: dict) -> str:
    return f"""
        /* ═══ Labels ═══ */
        QLabel {{
            color: {p['text_primary']};
            background: transparent;
            font-family: {_font_stack()};
        }}
    """


def _button_qss(p: dict, s: dict) -> str:
    r = s['border_radius_md']
    bw = s['border_width']
    return f"""
        /* ═══ Buttons ═══ */
        QPushButton {{
            background-color: {p['primary']};
            color: {p['text_on_primary']};
            border: {bw}px solid {p['primary']};
            border-radius: {r}px;
            padding: {s['padding_md']};
            font-size: {_fs(FONT_SIZE_BODY, s)}px;
            font-weight: 500;
            font-family: {_font_stack()};
            min-height: {s['button_height'] - 16}px;
        }}
        QPushButton:hover {{
            background-color: {p['primary_hover']};
            border-color: {p['primary_hover']};
        }}
        QPushButton:pressed {{
            background-color: {p['primary_pressed']};
            border-color: {p['primary_pressed']};
        }}
        QPushButton:disabled {{
            background-color: {p['disabled_bg']};
            color: {p['disabled_text']};
            border-color: {p['border']};
        }}
        QPushButton:focus {{
            border: {s['border_width_focus']}px solid {p['border_focus']};
        }}

        /* Secondary buttons */
        QPushButton[cssClass="secondary"] {{
            background-color: {p['bg_card']};
            color: {p['text_primary']};
            border: {bw}px solid {p['border']};
        }}
        QPushButton[cssClass="secondary"]:hover {{
            background-color: {p['bg_hover']};
            border-color: {p['border_light']};
        }}

        /* Danger buttons */
        QPushButton[cssClass="danger"] {{
            background-color: {p['danger']};
            color: {p['text_on_primary']};
            border-color: {p['danger']};
        }}
        QPushButton[cssClass="danger"]:hover {{
            background-color: {_darken(p['danger'], 15)};
        }}

        /* Success buttons */
        QPushButton[cssClass="success"] {{
            background-color: {p['success']};
            color: {p['text_on_primary']};
            border-color: {p['success']};
        }}
        QPushButton[cssClass="success"]:hover {{
            background-color: {_darken(p['success'], 15)};
        }}

        /* Ghost/flat buttons */
        QPushButton[cssClass="ghost"] {{
            background-color: transparent;
            color: {p['primary']};
            border: none;
        }}
        QPushButton[cssClass="ghost"]:hover {{
            background-color: {p['primary_light']};
        }}
    """


def _input_qss(p: dict, s: dict) -> str:
    r = s['border_radius_sm']
    bw = s['border_width']
    return f"""
        /* ═══ Inputs ═══ */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {p['bg_input']};
            color: {p['text_primary']};
            border: {bw}px solid {p['border']};
            border-radius: {r}px;
            padding: {s['padding_input']};
            font-size: {_fs(FONT_SIZE_BODY, s)}px;
            font-family: {_font_stack()};
            selection-background-color: {p['selection_bg']};
            selection-color: {p['selection_text']};
        }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: {s['border_width_focus']}px solid {p['border_focus']};
        }}
        QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover {{
            border-color: {p['border_light']};
        }}
        QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
            background-color: {p['disabled_bg']};
            color: {p['disabled_text']};
        }}
        QLineEdit[readOnly="true"] {{
            background-color: {p['bg_main']};
        }}
    """


def _combobox_qss(p: dict, s: dict) -> str:
    r = s['border_radius_sm']
    bw = s['border_width']
    return f"""
        /* ═══ ComboBox ═══ */
        QComboBox {{
            background-color: {p['bg_input']};
            color: {p['text_primary']};
            border: {bw}px solid {p['border']};
            border-radius: {r}px;
            padding: {s['padding_input']};
            font-size: {_fs(FONT_SIZE_BODY, s)}px;
            font-family: {_font_stack()};
            min-height: {s['input_height'] - 16}px;
        }}
        QComboBox:hover {{
            border-color: {p['border_light']};
        }}
        QComboBox:focus {{
            border: {s['border_width_focus']}px solid {p['border_focus']};
        }}
        QComboBox::drop-down {{
            border: none;
            padding-right: 10px;
            width: 20px;
        }}
        QComboBox::down-arrow {{
            width: 12px;
            height: 12px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {p['bg_card']};
            color: {p['text_primary']};
            border: {bw}px solid {p['border']};
            border-radius: {r}px;
            selection-background-color: {p['selection_bg']};
            selection-color: {p['selection_text']};
            padding: {s['spacing_xs']}px;
            outline: none;
        }}
        QComboBox QAbstractItemView::item {{
            padding: {s['item_padding']};
            border-radius: {s['menu_item_radius']}px;
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: {p['bg_hover']};
        }}
        QComboBox:disabled {{
            background-color: {p['disabled_bg']};
            color: {p['disabled_text']};
        }}
    """


def _checkbox_radio_qss(p: dict, s: dict) -> str:
    r = s['border_radius_sm']
    return f"""
        /* ═══ CheckBox & RadioButton ═══ */
        QCheckBox, QRadioButton {{
            color: {p['text_primary']};
            spacing: {s['spacing_sm']}px;
            font-size: {_fs(FONT_SIZE_BODY, s)}px;
            font-family: {_font_stack()};
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: {s['border_width']}px solid {p['border_light']};
            border-radius: {min(r, 4)}px;
            background-color: {p['bg_input']};
        }}
        QCheckBox::indicator:checked {{
            background-color: {p['primary']};
            border-color: {p['primary']};
        }}
        QCheckBox::indicator:hover {{
            border-color: {p['primary']};
        }}
        QRadioButton::indicator {{
            width: 18px;
            height: 18px;
            border: {s['border_width']}px solid {p['border_light']};
            border-radius: 9px;
            background-color: {p['bg_input']};
        }}
        QRadioButton::indicator:checked {{
            background-color: {p['primary']};
            border-color: {p['primary']};
        }}
        QRadioButton::indicator:hover {{
            border-color: {p['primary']};
        }}
    """


def _spinbox_qss(p: dict, s: dict) -> str:
    r = s['border_radius_sm']
    bw = s['border_width']
    return f"""
        /* ═══ SpinBox ═══ */
        QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit {{
            background-color: {p['bg_input']};
            color: {p['text_primary']};
            border: {bw}px solid {p['border']};
            border-radius: {r}px;
            padding: {s['padding_input']};
            font-size: {_fs(FONT_SIZE_BODY, s)}px;
            font-family: {_font_stack()};
        }}
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border: {s['border_width_focus']}px solid {p['border_focus']};
        }}
        QSpinBox::up-button, QDoubleSpinBox::up-button,
        QSpinBox::down-button, QDoubleSpinBox::down-button {{
            border: none;
            background: transparent;
            width: 18px;
        }}
        QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
        QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
            background-color: {p['bg_hover']};
        }}
    """


def _table_qss(p: dict, s: dict) -> str:
    r = s['border_radius_md']
    bw = s['border_width']
    return f"""
        /* ═══ Tables ═══ */
        QTableWidget, QTableView {{
            background-color: {p['bg_card']};
            color: {p['text_primary']};
            border: {bw}px solid {p['border']};
            border-radius: {r}px;
            gridline-color: {p['border']};
            font-size: {_fs(FONT_SIZE_BODY, s)}px;
            font-family: {_font_stack()};
            selection-background-color: {p['selection_bg']};
            selection-color: {p['selection_text']};
            alternate-background-color: {p['bg_main']};
        }}
        QTableWidget::item, QTableView::item {{
            padding: {s['table_cell_padding']};
            border-bottom: 1px solid {p['border']};
        }}
        QTableWidget::item:selected, QTableView::item:selected {{
            background-color: {p['selection_bg']};
            color: {p['selection_text']};
        }}
        QTableWidget::item:hover, QTableView::item:hover {{
            background-color: {p['bg_hover']};
        }}
        QHeaderView::section {{
            background-color: {p['header_bg']};
            color: {p['header_text']};
            font-weight: 600;
            font-size: {_fs(FONT_SIZE_BODY, s)}px;
            padding: {s['table_header_padding']};
            border: none;
            border-bottom: 2px solid {p['header_border']};
            font-family: {_font_stack()};
        }}
        QHeaderView::section:hover {{
            background-color: {p['bg_hover']};
        }}
        QTableCornerButton::section {{
            background-color: {p['header_bg']};
            border: none;
        }}
    """


def _tree_list_qss(p: dict, s: dict) -> str:
    r = s['border_radius_sm']
    bw = s['border_width']
    return f"""
        /* ═══ Tree & List Widgets ═══ */
        QTreeWidget, QTreeView, QListWidget, QListView {{
            background-color: {p['bg_card']};
            color: {p['text_primary']};
            border: {bw}px solid {p['border']};
            border-radius: {r}px;
            font-size: {_fs(FONT_SIZE_BODY, s)}px;
            font-family: {_font_stack()};
            outline: none;
        }}
        QTreeWidget::item, QTreeView::item,
        QListWidget::item, QListView::item {{
            padding: {s['item_padding']};
            border-radius: {s['menu_item_radius']}px;
            margin: 1px {s['spacing_xs']}px;
        }}
        QTreeWidget::item:selected, QTreeView::item:selected,
        QListWidget::item:selected, QListView::item:selected {{
            background-color: {p['selection_bg']};
            color: {p['selection_text']};
        }}
        QTreeWidget::item:hover, QTreeView::item:hover,
        QListWidget::item:hover, QListView::item:hover {{
            background-color: {p['bg_hover']};
        }}
        QTreeWidget::branch {{
            background: transparent;
        }}
    """


def _tab_qss(p: dict, s: dict) -> str:
    r = s['border_radius_sm']
    return f"""
        /* ═══ Tabs ═══ */
        QTabWidget::pane {{
            background-color: {p['bg_card']};
            border: {s['border_width']}px solid {p['border']};
            border-radius: {r}px;
            top: -1px;
        }}
        QTabBar::tab {{
            background-color: {p['bg_main']};
            color: {p['text_secondary']};
            border: {s['border_width']}px solid {p['border']};
            border-bottom: none;
            border-top-left-radius: {r}px;
            border-top-right-radius: {r}px;
            padding: {s['padding_sm']};
            font-size: {_fs(FONT_SIZE_BODY, s)}px;
            font-family: {_font_stack()};
            margin-right: 2px;
        }}
        QTabBar::tab:selected {{
            background-color: {p['bg_card']};
            color: {p['primary']};
            border-bottom: 2px solid {p['primary']};
        }}
        QTabBar::tab:hover:!selected {{
            background-color: {p['bg_hover']};
            color: {p['text_primary']};
        }}
    """


def _menu_qss(p: dict, s: dict) -> str:
    r = s['border_radius_md']
    return f"""
        /* ═══ Menus ═══ */
        QMenuBar {{
            background-color: {p['bg_header']};
            color: {p['text_primary']};
            font-size: {_fs(FONT_SIZE_BODY, s)}px;
            font-weight: 500;
            padding: {s['toolbar_padding']}px;
            border-bottom: {s['separator_height']}px solid {p['border']};
            font-family: {_font_stack()};
        }}
        QMenuBar::item {{
            padding: {s['padding_sm']};
            border-radius: {s['menu_item_radius']}px;
            margin: 2px;
        }}
        QMenuBar::item:selected {{
            background-color: {p['primary']};
            color: {p['text_on_primary']};
        }}
        QMenuBar::item:pressed {{
            background-color: {p['primary_pressed']};
        }}
        QMenu {{
            background-color: {p['bg_card']};
            color: {p['text_primary']};
            border: {s['border_width']}px solid {p['border']};
            border-radius: {r}px;
            padding: {s['spacing_xs']}px;
            font-family: {_font_stack()};
        }}
        QMenu::item {{
            padding: {s['menu_item_padding']};
            border-radius: {s['menu_item_radius']}px;
            margin: 2px;
        }}
        QMenu::item:selected {{
            background-color: {p['primary']};
            color: {p['text_on_primary']};
        }}
        QMenu::separator {{
            height: {s['separator_height']}px;
            background-color: {p['border']};
            margin: {s['spacing_xs']}px {s['spacing_md']}px;
        }}
    """


def _toolbar_qss(p: dict, s: dict) -> str:
    return f"""
        /* ═══ Toolbar ═══ */
        QToolBar {{
            background-color: {p['bg_header']};
            border: none;
            padding: {s['toolbar_padding']}px;
            spacing: {s['spacing_sm']}px;
        }}
        QToolBar::separator {{
            width: {s['separator_height']}px;
            background-color: {p['border']};
            margin: {s['spacing_xs']}px;
        }}
        QToolBar QToolButton {{
            background-color: transparent;
            color: {p['text_primary']};
            border: none;
            border-radius: {s['menu_item_radius']}px;
            padding: {s['toolbar_btn_padding']};
            font-size: {_fs(FONT_SIZE_BODY, s)}px;
            font-weight: 500;
            font-family: {_font_stack()};
        }}
        QToolBar QToolButton:hover {{
            background-color: {p['bg_hover']};
        }}
        QToolBar QToolButton:pressed {{
            background-color: {p['primary']};
            color: {p['text_on_primary']};
        }}
        QToolBar QToolButton:checked {{
            background-color: {p['primary_light']};
            color: {p['primary']};
        }}
    """


def _statusbar_qss(p: dict, s: dict) -> str:
    return f"""
        /* ═══ StatusBar ═══ */
        QStatusBar {{
            background-color: {p['bg_header']};
            color: {p['text_secondary']};
            border-top: {s['separator_height']}px solid {p['border']};
            font-size: {_fs(FONT_SIZE_SMALL, s)}px;
            padding: {s['spacing_xs']}px;
            font-family: {_font_stack()};
        }}
        QStatusBar::item {{
            border: none;
        }}
        QStatusBar QLabel {{
            color: {p['text_secondary']};
            padding: 0 {s['spacing_sm']}px;
        }}
    """


def _scrollbar_qss(p: dict, s: dict) -> str:
    w = s['scrollbar_width']
    r = s['scrollbar_radius']
    m = s['scrollbar_min']
    return f"""
        /* ═══ ScrollBars ═══ */
        QScrollBar:vertical {{
            background-color: {p['scrollbar_bg']};
            width: {w}px;
            border-radius: {r}px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background-color: {p['scrollbar_handle']};
            border-radius: {r}px;
            min-height: {m}px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {p['scrollbar_hover']};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
        QScrollBar:horizontal {{
            background-color: {p['scrollbar_bg']};
            height: {w}px;
            border-radius: {r}px;
            margin: 0;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {p['scrollbar_handle']};
            border-radius: {r}px;
            min-width: {m}px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background-color: {p['scrollbar_hover']};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background: none;
        }}
    """


def _dialog_qss(p: dict, s: dict) -> str:
    r = s['border_radius_lg']
    return f"""
        /* ═══ Dialogs ═══ */
        QDialog {{
            background-color: {p['bg_dialog']};
            color: {p['text_primary']};
            border: {s['border_width']}px solid {p['border']};
            border-radius: {r}px;
            font-family: {_font_stack()};
        }}
    """


def _groupbox_qss(p: dict, s: dict) -> str:
    r = s['border_radius_md']
    return f"""
        /* ═══ GroupBox ═══ */
        QGroupBox {{
            color: {p['accent']};
            font-weight: 600;
            font-size: {_fs(FONT_SIZE_BODY, s)}px;
            border: {s['border_width']}px solid {p['border']};
            border-radius: {r}px;
            margin-top: {s['spacing_lg']}px;
            padding-top: {s['spacing_lg']}px;
            padding-left: {s['spacing_sm']}px;
            padding-right: {s['spacing_sm']}px;
            font-family: {_font_stack()};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: {s['spacing_lg']}px;
            padding: 0 {s['spacing_sm']}px;
            color: {p['text_primary']};
        }}
    """


def _frame_qss(p: dict, s: dict) -> str:
    return f"""
        /* ═══ Frames ═══ */
        QFrame[frameShape="4"], QFrame[frameShape="5"] {{
            color: {p['border']};
        }}
    """


def _scrollarea_qss(p: dict, s: dict) -> str:
    return f"""
        /* ═══ ScrollArea ═══ */
        QScrollArea {{
            border: none;
            background: transparent;
        }}
        QScrollArea > QWidget > QWidget {{
            background: transparent;
        }}
    """


def _progressbar_qss(p: dict, s: dict) -> str:
    r = s['border_radius_sm']
    return f"""
        /* ═══ ProgressBar ═══ */
        QProgressBar {{
            background-color: {p['bg_card']};
            border: {s['border_width']}px solid {p['border']};
            border-radius: {r}px;
            text-align: center;
            color: {p['text_primary']};
            font-size: {_fs(FONT_SIZE_SMALL, s)}px;
            min-height: 20px;
        }}
        QProgressBar::chunk {{
            background-color: {p['primary']};
            border-radius: {max(0, r - 1)}px;
        }}
    """


def _slider_qss(p: dict, s: dict) -> str:
    return f"""
        /* ═══ Slider ═══ */
        QSlider::groove:horizontal {{
            background-color: {p['border']};
            height: 4px;
            border-radius: 2px;
        }}
        QSlider::handle:horizontal {{
            background-color: {p['primary']};
            width: 16px;
            height: 16px;
            margin: -6px 0;
            border-radius: 8px;
        }}
        QSlider::handle:horizontal:hover {{
            background-color: {p['primary_hover']};
        }}
        QSlider::sub-page:horizontal {{
            background-color: {p['primary']};
            border-radius: 2px;
        }}
        QSlider::groove:vertical {{
            background-color: {p['border']};
            width: 4px;
            border-radius: 2px;
        }}
        QSlider::handle:vertical {{
            background-color: {p['primary']};
            width: 16px;
            height: 16px;
            margin: 0 -6px;
            border-radius: 8px;
        }}
    """


def _splitter_qss(p: dict, s: dict) -> str:
    return f"""
        /* ═══ Splitter ═══ */
        QSplitter::handle {{
            background-color: {p['border']};
        }}
        QSplitter::handle:horizontal {{
            width: 2px;
        }}
        QSplitter::handle:vertical {{
            height: 2px;
        }}
        QSplitter::handle:hover {{
            background-color: {p['primary']};
        }}
    """


def _tooltip_qss(p: dict, s: dict) -> str:
    r = s['border_radius_sm']
    return f"""
        /* ═══ Tooltips ═══ */
        QToolTip {{
            background-color: {p['bg_tooltip']};
            color: {p.get('text_on_primary', '#ffffff') if p['is_dark'] else p.get('text_on_primary', '#ffffff')};
            border: {s['border_width']}px solid {p['border_light']};
            border-radius: {r}px;
            padding: {s['padding_xs']};
            font-size: {_fs(FONT_SIZE_SMALL, s)}px;
            font-family: {_font_stack()};
        }}
    """


def _calendar_qss(p: dict, s: dict) -> str:
    return f"""
        /* ═══ Calendar Widget ═══ */
        QCalendarWidget {{
            background-color: {p['bg_card']};
            color: {p['text_primary']};
        }}
        QCalendarWidget QToolButton {{
            color: {p['text_primary']};
            background-color: transparent;
            border: none;
            border-radius: {s['menu_item_radius']}px;
            padding: {s['padding_xs']};
            font-family: {_font_stack()};
        }}
        QCalendarWidget QToolButton:hover {{
            background-color: {p['bg_hover']};
        }}
        QCalendarWidget QAbstractItemView {{
            background-color: {p['bg_card']};
            color: {p['text_primary']};
            selection-background-color: {p['primary']};
            selection-color: {p['text_on_primary']};
        }}
    """


def _dateedit_qss(p: dict, s: dict) -> str:
    r = s['border_radius_sm']
    bw = s['border_width']
    return f"""
        /* ═══ Date/Time Edit ═══ */
        QDateEdit, QTimeEdit, QDateTimeEdit {{
            background-color: {p['bg_input']};
            color: {p['text_primary']};
            border: {bw}px solid {p['border']};
            border-radius: {r}px;
            padding: {s['padding_input']};
            font-size: {_fs(FONT_SIZE_BODY, s)}px;
            font-family: {_font_stack()};
        }}
        QDateEdit:focus, QTimeEdit:focus, QDateTimeEdit:focus {{
            border: {s['border_width_focus']}px solid {p['border_focus']};
        }}
        QDateEdit::drop-down, QTimeEdit::drop-down, QDateTimeEdit::drop-down {{
            border: none;
            padding-right: 8px;
            width: 20px;
        }}
    """


# ─── Color Utilities ────────────────────────────────

def _darken(hex_color: str, amount: int = 20) -> str:
    """Darken a hex color by the given amount (0-255)."""
    hex_color = hex_color.lstrip('#')
    r = max(0, int(hex_color[0:2], 16) - amount)
    g = max(0, int(hex_color[2:4], 16) - amount)
    b = max(0, int(hex_color[4:6], 16) - amount)
    return f"#{r:02x}{g:02x}{b:02x}"
