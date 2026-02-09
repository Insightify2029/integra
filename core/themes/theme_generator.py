"""
Theme Generator
===============
Generates complete QSS stylesheets from a color palette dictionary.
"""

from .theme_palettes import get_palette


def generate_stylesheet(theme_name: str) -> str:
    """Generate complete QSS stylesheet for a theme."""
    p = get_palette(theme_name)
    return _build_qss(p)


def _build_qss(p: dict) -> str:
    """Build full QSS from palette dict."""
    return (
        _base_qss(p)
        + _button_qss(p)
        + _table_qss(p)
        + _input_qss(p)
        + _menu_qss(p)
        + _toolbar_qss(p)
        + _statusbar_qss(p)
        + _scrollbar_qss(p)
        + _dialog_qss(p)
    )


def _base_qss(p: dict) -> str:
    return f"""
        QMainWindow, QWidget {{
            background-color: {p['bg_main']};
        }}
        QLabel {{
            color: {p['text_primary']};
            background: transparent;
        }}
    """


def _button_qss(p: dict) -> str:
    return f"""
        QPushButton {{
            background-color: {p['primary']};
            color: #ffffff;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: {p['primary_hover']};
        }}
        QPushButton:pressed {{
            background-color: {p['primary_pressed']};
        }}
        QPushButton:disabled {{
            background-color: {p['disabled_bg']};
            color: {p['disabled_text']};
        }}
    """


def _table_qss(p: dict) -> str:
    return f"""
        QTableWidget, QTableView {{
            background-color: {p['bg_card']};
            color: {p['text_primary']};
            border: 1px solid {p['border']};
            border-radius: 8px;
            gridline-color: {p['border']};
            font-size: 13px;
        }}
        QTableWidget::item, QTableView::item {{
            padding: 10px;
            border-bottom: 1px solid {p['border']};
        }}
        QTableWidget::item:selected, QTableView::item:selected {{
            background-color: {p['selection_bg']};
            color: {p['selection_text']};
        }}
        QTableWidget::item:hover, QTableView::item:hover {{
            background-color: {p['border']};
        }}
        QHeaderView::section {{
            background-color: {p['header_bg']};
            color: {p['header_text']};
            font-weight: 600;
            font-size: 13px;
            padding: 12px;
            border: none;
            border-bottom: 2px solid {p['header_border']};
        }}
    """


def _input_qss(p: dict) -> str:
    return f"""
        QLineEdit, QTextEdit {{
            background-color: {p['bg_input']};
            color: {p['text_primary']};
            border: 1px solid {p['border']};
            border-radius: 6px;
            padding: 10px;
            font-size: 13px;
        }}
        QLineEdit:focus, QTextEdit:focus {{
            border: 2px solid {p['primary']};
        }}
        QLineEdit:hover, QTextEdit:hover {{
            border-color: {p['border_light']};
        }}
        QLineEdit:disabled, QTextEdit:disabled {{
            background-color: {p['disabled_bg']};
            color: {p['disabled_text']};
        }}
    """


def _menu_qss(p: dict) -> str:
    return f"""
        QMenuBar {{
            background-color: {p['bg_header']};
            color: {p['text_primary']};
            font-size: 14px;
            font-weight: 500;
            padding: 5px;
            border-bottom: 1px solid {p['border']};
        }}
        QMenuBar::item {{
            padding: 8px 15px;
            border-radius: 5px;
            margin: 2px;
        }}
        QMenuBar::item:selected {{
            background-color: {p['primary']};
        }}
        QMenuBar::item:pressed {{
            background-color: {p['primary_pressed']};
        }}
        QMenu {{
            background-color: {p['bg_header']};
            color: {p['text_primary']};
            border: 1px solid {p['border']};
            border-radius: 8px;
            padding: 5px;
        }}
        QMenu::item {{
            padding: 10px 30px;
            border-radius: 5px;
            margin: 2px;
        }}
        QMenu::item:selected {{
            background-color: {p['primary']};
        }}
        QMenu::separator {{
            height: 1px;
            background-color: {p['border']};
            margin: 5px 10px;
        }}
    """


def _toolbar_qss(p: dict) -> str:
    return f"""
        QToolBar {{
            background-color: {p['bg_header']};
            border: none;
            padding: 5px;
            spacing: 5px;
        }}
        QToolBar QToolButton {{
            background-color: transparent;
            color: {p['text_primary']};
            border: none;
            border-radius: 5px;
            padding: 8px 15px;
            font-size: 13px;
            font-weight: 500;
        }}
        QToolBar QToolButton:hover {{
            background-color: {p['border']};
        }}
        QToolBar QToolButton:pressed {{
            background-color: {p['primary']};
        }}
    """


def _statusbar_qss(p: dict) -> str:
    return f"""
        QStatusBar {{
            background-color: {p['bg_header']};
            color: {p['text_secondary']};
            border-top: 1px solid {p['border']};
            font-size: 12px;
            padding: 5px;
        }}
    """


def _scrollbar_qss(p: dict) -> str:
    return f"""
        QScrollBar:vertical {{
            background-color: {p['scrollbar_bg']};
            width: 12px;
            border-radius: 6px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {p['scrollbar_handle']};
            border-radius: 6px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {p['scrollbar_hover']};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar:horizontal {{
            background-color: {p['scrollbar_bg']};
            height: 12px;
            border-radius: 6px;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {p['scrollbar_handle']};
            border-radius: 6px;
            min-width: 30px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background-color: {p['scrollbar_hover']};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
    """


def _dialog_qss(p: dict) -> str:
    return f"""
        QDialog {{
            background-color: {p['bg_dialog']};
            border: 1px solid {p['border']};
            border-radius: 12px;
        }}
        QGroupBox {{
            color: {p['accent']};
            font-weight: 600;
            border: 1px solid {p['border']};
            border-radius: 8px;
            margin-top: 15px;
            padding-top: 15px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 15px;
            padding: 0 5px;
        }}
        QComboBox {{
            background-color: {p['bg_input']};
            color: {p['text_primary']};
            border: 1px solid {p['border']};
            border-radius: 6px;
            padding: 10px;
            font-size: 13px;
        }}
        QComboBox:hover {{
            border-color: {p['border_light']};
        }}
        QComboBox::drop-down {{
            border: none;
            padding-right: 10px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {p['bg_input']};
            color: {p['text_primary']};
            border: 1px solid {p['border']};
            selection-background-color: {p['selection_bg']};
        }}
    """
