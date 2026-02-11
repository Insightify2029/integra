# -*- coding: utf-8 -*-
"""
Employee Profile Screen (FormRenderer-based)
=============================================
شاشة ملف الموظف - مبنية على FormRenderer

Migrated from hardcoded Python layout to JSON-configurable FormRenderer.
Uses employee_profile.iform for read-only data display.
Maintains same signals and public API as the original.

Features:
- All employee data displayed via FormRenderer (read-only)
- Action buttons: Edit, Deactivate, Leave Settlement, End of Service, Overtime
- Professional layout
"""

import os
from typing import Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea,
)
from PyQt5.QtCore import Qt, pyqtSignal

from core.themes import (
    get_current_palette, get_font,
    FONT_SIZE_TITLE, FONT_SIZE_BODY, FONT_WEIGHT_BOLD,
)
from core.logging import app_logger

from modules.designer.form_renderer import FormRenderer


# Path to the .iform template
_IFORM_DIR = os.path.normpath(os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..", "designer", "templates", "builtin",
))
_IFORM_PATH = os.path.join(_IFORM_DIR, "employee_profile.iform")


class ActionButton(QPushButton):
    """Styled action button for the profile screen."""

    def __init__(
        self,
        text: str,
        icon: str = "",
        color: str = "primary",
        parent: Optional[QWidget] = None,
    ):
        display = f"{icon} {text}" if icon else text
        super().__init__(display, parent)
        self._color = color
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(get_font(FONT_SIZE_BODY))
        self.setMinimumHeight(45)
        self.setProperty("buttonColor", color)


class EmployeeProfileScreen(QWidget):
    """
    Employee Profile Screen using FormRenderer.

    Shows complete employee information with action buttons.
    Provides the same public API and signals as the original.

    Signals:
        edit_clicked(dict): Edit button clicked
        deactivate_clicked(dict): Deactivate button clicked
        leave_settlement_clicked(dict): Leave settlement clicked
        end_of_service_clicked(dict): End of service clicked
        overtime_clicked(dict): Overtime clicked
        back_clicked(): Back button clicked
    """

    # Signals
    edit_clicked = pyqtSignal(dict)
    deactivate_clicked = pyqtSignal(dict)
    leave_settlement_clicked = pyqtSignal(dict)
    end_of_service_clicked = pyqtSignal(dict)
    overtime_clicked = pyqtSignal(dict)
    back_clicked = pyqtSignal()

    def __init__(
        self,
        employee_data: Optional[dict] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)

        self._employee: dict = employee_data or {}

        self._setup_ui()
        self._apply_theme()

        if employee_data:
            self.set_employee(employee_data)

    # ------------------------------------------------------------------
    # UI Setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        """Setup screen UI: header + FormRenderer + action buttons."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header with back button and title
        header = QHBoxLayout()

        self._back_btn = QPushButton("→ رجوع")
        self._back_btn.setCursor(Qt.PointingHandCursor)
        self._back_btn.setFont(get_font(FONT_SIZE_BODY))
        self._back_btn.setObjectName("backButton")
        self._back_btn.clicked.connect(self.back_clicked.emit)
        header.addWidget(self._back_btn)

        self._title_label = QLabel("ملف الموظف")
        self._title_label.setFont(get_font(FONT_SIZE_TITLE, FONT_WEIGHT_BOLD))
        self._title_label.setAlignment(Qt.AlignCenter)
        self._title_label.setObjectName("screenTitle")
        header.addWidget(self._title_label, 1)

        # Spacer for symmetry
        spacer = QWidget()
        spacer.setFixedWidth(80)
        header.addWidget(spacer)

        layout.addLayout(header)

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(20)

        # FormRenderer for employee data (read-only)
        self._renderer = FormRenderer(scroll_content)
        loaded = self._renderer.load_form(_IFORM_PATH)
        if not loaded:
            app_logger.error(
                f"Failed to load employee profile form: {_IFORM_PATH}"
            )
        scroll_layout.addWidget(self._renderer)

        # Action Buttons
        actions_frame = QFrame()
        actions_frame.setObjectName("actionsFrame")
        actions_layout = QHBoxLayout(actions_frame)
        actions_layout.setContentsMargins(20, 20, 20, 20)
        actions_layout.setSpacing(15)

        self._edit_btn = ActionButton("تعديل البيانات", "📝", "primary")
        self._edit_btn.clicked.connect(self._on_edit)
        actions_layout.addWidget(self._edit_btn)

        self._leave_btn = ActionButton("تسوية إجازة", "🏖️", "success")
        self._leave_btn.clicked.connect(self._on_leave_settlement)
        actions_layout.addWidget(self._leave_btn)

        self._overtime_btn = ActionButton("حساب الإضافي", "⏰", "info")
        self._overtime_btn.clicked.connect(self._on_overtime)
        actions_layout.addWidget(self._overtime_btn)

        self._eos_btn = ActionButton("نهاية الخدمة", "🚪", "warning")
        self._eos_btn.clicked.connect(self._on_end_of_service)
        actions_layout.addWidget(self._eos_btn)

        self._deactivate_btn = ActionButton("إيقاف الموظف", "⛔", "danger")
        self._deactivate_btn.clicked.connect(self._on_deactivate)
        actions_layout.addWidget(self._deactivate_btn)

        scroll_layout.addWidget(actions_frame)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_employee(self, data: dict) -> None:
        """Set employee data to display."""
        self._employee = data

        # Update title
        name = data.get('name_ar', data.get('name_en', 'موظف'))
        self._title_label.setText(f"ملف الموظف: {name}")

        # Pass data to FormRenderer – maps via data_binding.column
        self._renderer.set_data(data)

    def get_employee(self) -> dict:
        """Get current employee data."""
        return self._employee

    # ------------------------------------------------------------------
    # Signal Handlers
    # ------------------------------------------------------------------

    def _on_edit(self) -> None:
        """Handle edit button click."""
        self.edit_clicked.emit(self._employee)

    def _on_deactivate(self) -> None:
        """Handle deactivate button click."""
        self.deactivate_clicked.emit(self._employee)

    def _on_leave_settlement(self) -> None:
        """Handle leave settlement button click."""
        self.leave_settlement_clicked.emit(self._employee)

    def _on_end_of_service(self) -> None:
        """Handle end of service button click."""
        self.end_of_service_clicked.emit(self._employee)

    def _on_overtime(self) -> None:
        """Handle overtime button click."""
        self.overtime_clicked.emit(self._employee)

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def _apply_theme(self) -> None:
        """Apply current theme using palette."""
        p = get_current_palette()
        text_on_primary = p.get('text_on_primary', '#ffffff')
        self.setStyleSheet(f"""
            QWidget {{ background-color: {p.get('bg_main', '#0f172a')}; }}
            QLabel {{ color: {p.get('text_primary', '#e2e8f0')}; background: transparent; }}
            QLabel#screenTitle {{ color: {p.get('accent', '#3b82f6')}; }}
            QFrame#actionsFrame {{
                background-color: {p.get('bg_card', '#1e293b')};
                border: 1px solid {p.get('border', '#334155')};
                border-radius: 12px;
            }}
            QPushButton {{
                background-color: {p.get('bg_card', '#1e293b')};
                color: {p.get('text_primary', '#e2e8f0')};
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {p.get('bg_hover', '#334155')};
            }}
            QPushButton#backButton {{
                background-color: transparent;
                color: {p.get('text_secondary', '#94a3b8')};
                border: 1px solid {p.get('border', '#334155')};
            }}
            QPushButton#backButton:hover {{
                background-color: {p.get('bg_card', '#1e293b')};
                color: {p.get('text_primary', '#e2e8f0')};
            }}
            QPushButton[buttonColor="primary"] {{
                background-color: {p.get('primary', '#2563eb')};
                color: {text_on_primary};
            }}
            QPushButton[buttonColor="primary"]:hover {{
                background-color: {p.get('primary_hover', '#1d4ed8')};
            }}
            QPushButton[buttonColor="success"] {{
                background-color: {p.get('success', '#22c55e')};
                color: {text_on_primary};
            }}
            QPushButton[buttonColor="info"] {{
                background-color: {p.get('info', '#06b6d4')};
                color: {text_on_primary};
            }}
            QPushButton[buttonColor="warning"] {{
                background-color: {p.get('warning', '#f59e0b')};
                color: {text_on_primary};
            }}
            QPushButton[buttonColor="danger"] {{
                background-color: {p.get('danger', '#ef4444')};
                color: {text_on_primary};
            }}
            QScrollArea {{ background: transparent; border: none; }}
        """)
