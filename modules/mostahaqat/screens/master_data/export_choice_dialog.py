# -*- coding: utf-8 -*-
"""
Export Choice Dialog
====================
ديالوج اختيار نوع التصدير (كل البيانات أو المحدد فقط)

Features:
- Choose between all data or selected rows
- Delegates to ExportManager for actual export
- Dark/Light theme support
"""

from typing import List

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QRadioButton, QButtonGroup, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.components.tables.enterprise import ExportManager
from ui.dialogs.message import show_warning
from core.themes import get_current_palette, get_font, FONT_SIZE_TITLE, FONT_SIZE_BODY, FONT_WEIGHT_BOLD


class ExportChoiceDialog(QDialog):
    """
    Dialog to choose export scope (all data or selected only).
    Then opens the ExportManager for format selection and file saving.
    """

    def __init__(
        self,
        all_data: List[dict],
        selected_data: List[dict],
        columns: List[str],
        title: str = "البيانات",
        parent=None
    ):
        super().__init__(parent)

        self._all_data = all_data or []
        self._selected_data = selected_data or []
        self._columns = columns
        self._title = title

        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        """Setup dialog UI."""
        self.setWindowTitle(f"📤 تصدير {self._title}")
        self.setMinimumWidth(420)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        # Header
        header = QLabel(f"📤 تصدير {self._title}")
        header.setFont(get_font(FONT_SIZE_TITLE, FONT_WEIGHT_BOLD))
        header.setAlignment(Qt.AlignCenter)
        header.setObjectName("exportHeader")
        layout.addWidget(header)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("exportSep")
        layout.addWidget(sep)

        # Choice group
        choice_frame = QFrame()
        choice_frame.setObjectName("choiceFrame")
        choice_layout = QVBoxLayout(choice_frame)
        choice_layout.setContentsMargins(20, 20, 20, 20)
        choice_layout.setSpacing(15)

        info = QLabel("اختر نطاق التصدير:")
        info.setFont(get_font(FONT_SIZE_BODY))
        info.setObjectName("choiceLabel")
        choice_layout.addWidget(info)

        self._group = QButtonGroup(self)

        # All data option
        self._all_radio = QRadioButton(
            f"📊 كل البيانات ({len(self._all_data)} سجل)"
        )
        self._all_radio.setFont(get_font(FONT_SIZE_BODY))
        self._all_radio.setChecked(True)
        self._group.addButton(self._all_radio)
        choice_layout.addWidget(self._all_radio)

        # Selected data option
        selected_count = len(self._selected_data)
        self._selected_radio = QRadioButton(
            f"✅ المحدد فقط ({selected_count} سجل)"
        )
        self._selected_radio.setFont(get_font(FONT_SIZE_BODY))
        self._selected_radio.setEnabled(selected_count > 0)
        self._group.addButton(self._selected_radio)
        choice_layout.addWidget(self._selected_radio)

        layout.addWidget(choice_frame)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.setFont(get_font(FONT_SIZE_BODY))
        cancel_btn.setMinimumHeight(44)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        export_btn = QPushButton("📤 متابعة التصدير")
        export_btn.setFont(get_font(FONT_SIZE_BODY, FONT_WEIGHT_BOLD))
        export_btn.setMinimumHeight(44)
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.setProperty("buttonColor", "success")
        export_btn.clicked.connect(self._on_export)
        buttons_layout.addWidget(export_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

    def _on_export(self):
        """Handle export button - open ExportManager."""
        if self._selected_radio.isChecked():
            data = self._selected_data
        else:
            data = self._all_data

        if not data:
            show_warning(self, "تنبيه", "لا توجد بيانات للتصدير!")
            return

        # Open the existing ExportManager dialog
        export_dialog = ExportManager(data, self._columns, self)
        export_dialog.exec_()
        self.accept()

    def _apply_theme(self):
        """Apply current theme using palette."""
        p = get_current_palette()
        self.setStyleSheet(f"""
            QDialog {{ background-color: {p['bg_dialog']}; }}

            QLabel {{ color: {p['text_primary']}; background: transparent; }}
            QLabel#exportHeader {{ color: {p['accent']}; }}
            QLabel#choiceLabel {{ color: {p['text_secondary']}; }}

            QFrame#exportSep {{ background-color: {p['border']}; }}
            QFrame#choiceFrame {{
                background-color: {p['bg_main']};
                border: 1px solid {p['border']};
                border-radius: 12px;
            }}

            QRadioButton {{
                color: {p['text_primary']};
                spacing: 10px;
                padding: 10px;
            }}
            QRadioButton:disabled {{ color: {p['disabled_text']}; }}
            QRadioButton::indicator {{
                width: 18px; height: 18px;
                border-radius: 9px;
                border: 2px solid {p['border_light']};
                background-color: {p['bg_main']};
            }}
            QRadioButton::indicator:checked {{
                background-color: {p['primary']};
                border-color: {p['primary']};
            }}

            QPushButton {{
                background-color: {p['bg_card']}; color: {p['text_primary']};
                border: none; border-radius: 8px;
                padding: 10px 20px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {p['bg_hover']}; }}
            QPushButton[buttonColor="success"] {{ background-color: {p['success']}; color: {p['text_on_primary']}; }}
            QPushButton[buttonColor="success"]:hover {{ background-color: {p['success']}; }}
        """)
