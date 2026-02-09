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
from core.themes import get_current_theme


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
        header.setFont(QFont("Cairo", 16, QFont.Bold))
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
        info.setFont(QFont("Cairo", 12))
        info.setObjectName("choiceLabel")
        choice_layout.addWidget(info)

        self._group = QButtonGroup(self)

        # All data option
        self._all_radio = QRadioButton(
            f"📊 كل البيانات ({len(self._all_data)} سجل)"
        )
        self._all_radio.setFont(QFont("Cairo", 12))
        self._all_radio.setChecked(True)
        self._group.addButton(self._all_radio)
        choice_layout.addWidget(self._all_radio)

        # Selected data option
        selected_count = len(self._selected_data)
        self._selected_radio = QRadioButton(
            f"✅ المحدد فقط ({selected_count} سجل)"
        )
        self._selected_radio.setFont(QFont("Cairo", 12))
        self._selected_radio.setEnabled(selected_count > 0)
        self._group.addButton(self._selected_radio)
        choice_layout.addWidget(self._selected_radio)

        layout.addWidget(choice_frame)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.setFont(QFont("Cairo", 12))
        cancel_btn.setMinimumHeight(44)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        export_btn = QPushButton("📤 متابعة التصدير")
        export_btn.setFont(QFont("Cairo", 12, QFont.Bold))
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
        """Apply current theme."""
        theme = get_current_theme()

        if theme == 'dark':
            self.setStyleSheet("""
                QDialog { background-color: #1e293b; }

                QLabel { color: #f1f5f9; background: transparent; }
                QLabel#exportHeader { color: #38bdf8; }
                QLabel#choiceLabel { color: #94a3b8; }

                QFrame#exportSep { background-color: #334155; }
                QFrame#choiceFrame {
                    background-color: #0f172a;
                    border: 1px solid #334155;
                    border-radius: 12px;
                }

                QRadioButton {
                    color: #f1f5f9;
                    spacing: 10px;
                    padding: 10px;
                }
                QRadioButton:disabled { color: #475569; }
                QRadioButton::indicator {
                    width: 18px; height: 18px;
                    border-radius: 9px;
                    border: 2px solid #475569;
                    background-color: #0f172a;
                }
                QRadioButton::indicator:checked {
                    background-color: #2563eb;
                    border-color: #2563eb;
                }

                QPushButton {
                    background-color: #334155; color: #f1f5f9;
                    border: none; border-radius: 8px;
                    padding: 10px 20px; font-weight: bold;
                }
                QPushButton:hover { background-color: #475569; }
                QPushButton[buttonColor="success"] { background-color: #10b981; }
                QPushButton[buttonColor="success"]:hover { background-color: #059669; }
            """)
        else:
            self.setStyleSheet("""
                QDialog { background-color: #ffffff; }

                QLabel { color: #1e293b; background: transparent; }
                QLabel#exportHeader { color: #0891b2; }
                QLabel#choiceLabel { color: #64748b; }

                QFrame#exportSep { background-color: #e2e8f0; }
                QFrame#choiceFrame {
                    background-color: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 12px;
                }

                QRadioButton {
                    color: #1e293b;
                    spacing: 10px;
                    padding: 10px;
                }
                QRadioButton:disabled { color: #94a3b8; }
                QRadioButton::indicator {
                    width: 18px; height: 18px;
                    border-radius: 9px;
                    border: 2px solid #cbd5e1;
                    background-color: #ffffff;
                }
                QRadioButton::indicator:checked {
                    background-color: #2563eb;
                    border-color: #2563eb;
                }

                QPushButton {
                    background-color: #e2e8f0; color: #1e293b;
                    border: none; border-radius: 8px;
                    padding: 10px 20px; font-weight: bold;
                }
                QPushButton:hover { background-color: #cbd5e1; }
                QPushButton[buttonColor="success"] { background-color: #10b981; color: #ffffff; }
                QPushButton[buttonColor="success"]:hover { background-color: #059669; }
            """)
