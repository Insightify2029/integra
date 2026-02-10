# -*- coding: utf-8 -*-
"""
Edit Employee Screen (FormRenderer-based)
==========================================
شاشة تعديل بيانات الموظف - مبنية على FormRenderer

Migrated from hardcoded Python layout to JSON-configurable FormRenderer.
Uses employee_edit.iform for form definition.
Maintains same signals and public API as the original.
"""

import os
from typing import Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton,
)
from PyQt5.QtCore import Qt, pyqtSignal

from core.themes import (
    get_current_palette, get_font,
    FONT_SIZE_TITLE, FONT_SIZE_BODY, FONT_WEIGHT_BOLD,
)
from core.logging import app_logger
from ui.components.notifications import toast_success, toast_error, toast_warning

from modules.designer.form_renderer import FormRenderer


# Path to the .iform template (resolved at module load)
_IFORM_DIR = os.path.normpath(os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..", "designer", "templates", "builtin",
))
_IFORM_PATH = os.path.join(_IFORM_DIR, "employee_edit.iform")


class EditEmployeeScreen(QWidget):
    """
    Edit Employee Screen using FormRenderer.

    Provides the same public API as the original hardcoded version:
    - Signals: saved(dict), cancelled()
    - Methods: set_employee(data)

    Internally renders the form from employee_edit.iform via FormRenderer.
    """

    saved = pyqtSignal(dict)
    cancelled = pyqtSignal()

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
        """Build the screen: header + FormRenderer."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header bar: [Back] --- Title --- [Spacer]
        header = QHBoxLayout()

        self._back_btn = QPushButton("→ رجوع")
        self._back_btn.setCursor(Qt.PointingHandCursor)
        self._back_btn.setFont(get_font(FONT_SIZE_BODY))
        self._back_btn.setObjectName("backButton")
        self._back_btn.clicked.connect(self._on_cancel)
        header.addWidget(self._back_btn)

        self._title_label = QLabel("تعديل بيانات الموظف")
        self._title_label.setFont(get_font(FONT_SIZE_TITLE, FONT_WEIGHT_BOLD))
        self._title_label.setAlignment(Qt.AlignCenter)
        self._title_label.setTextFormat(Qt.PlainText)
        self._title_label.setObjectName("screenTitle")
        header.addWidget(self._title_label, 1)

        spacer = QWidget()
        spacer.setFixedWidth(80)
        header.addWidget(spacer)

        layout.addLayout(header)

        # FormRenderer for the form body
        self._renderer = FormRenderer(self)
        self._renderer.saved.connect(self._on_form_saved)
        self._renderer.cancelled.connect(self._on_cancel)
        self._renderer.validation_failed.connect(self._on_validation_failed)

        loaded = self._renderer.load_form(_IFORM_PATH)
        if not loaded:
            app_logger.error(f"Failed to load employee edit form: {_IFORM_PATH}")
            err_label = QLabel("فشل تحميل نموذج التعديل")
            err_label.setAlignment(Qt.AlignCenter)
            err_label.setStyleSheet("color: red; font-size: 16px;")
            layout.addWidget(err_label)

        layout.addWidget(self._renderer, 1)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_employee(self, data: dict) -> None:
        """
        Populate the form with employee data.

        Args:
            data: Employee data dict (from employees list / profile screen).
                  Contains keys like: id, employee_code, name_ar, name_en,
                  national_id, nationality_id, department_id, job_title_id,
                  bank_id, company_id, status_id, hire_date, iban, etc.
        """
        if not isinstance(data, dict) or not data:
            return

        self._employee = data

        name = data.get('name_ar', data.get('name_en', ''))
        self._title_label.setText(f"تعديل بيانات: {name}")

        # Set record identity for save operations (public API, no DB load)
        employee_id = data.get('id')
        if employee_id is not None:
            self._renderer.set_record_identity("employees", int(employee_id))

        # Pass data directly to FormRenderer – it maps via data_binding.column
        self._renderer.set_data(data)

    # ------------------------------------------------------------------
    # Signal handlers
    # ------------------------------------------------------------------

    def _on_form_saved(self, saved_data: dict) -> None:
        """Handle FormRenderer save completion."""
        # Build updated_data dict that includes both IDs and display names
        # (matches the format the original screen emitted)
        updated_data = dict(self._employee)

        # Update all fields from saved data (saved_data keys match both
        # field_ids and data_binding.column names in employee_edit.iform)
        for key in ('name_ar', 'name_en', 'national_id', 'iban',
                     'employee_code'):
            if key in saved_data:
                updated_data[key] = saved_data[key]

        # Update ID fields
        for key in ('nationality_id', 'department_id', 'job_title_id',
                     'bank_id', 'company_id', 'status_id'):
            if key in saved_data:
                updated_data[key] = saved_data[key]

        # Extract display names from combo boxes for backward compat
        # Uses FormRenderer's public get_combo_display_text() API
        combo_display_map = {
            'nationality_id': 'nationality',
            'department_id': 'department',
            'job_title_id': 'job_title',
            'bank_id': 'bank',
            'company_id': 'company',
            'status_id': 'status',
        }
        for field_id, display_key in combo_display_map.items():
            text = self._renderer.get_combo_display_text(field_id)
            if text:
                updated_data[display_key] = text

        # Get hire_date as string (single source of truth)
        hire_date_val = self._renderer.get_field_value('hire_date')
        if hire_date_val is not None:
            updated_data['hire_date'] = str(hire_date_val)

        # Update internal state for subsequent saves
        self._employee = updated_data

        toast_success(self, "تم", "تم حفظ التعديلات بنجاح!")
        self.saved.emit(updated_data)

    def _on_cancel(self) -> None:
        """Handle cancel/back."""
        self.cancelled.emit()

    def _on_validation_failed(self, errors: list) -> None:
        """Handle validation errors from FormRenderer."""
        if errors:
            toast_warning(self, "تنبيه", errors[0])

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def _apply_theme(self) -> None:
        """Apply theme to the header area. FormRenderer handles its own theming."""
        p = get_current_palette()
        self.setStyleSheet(f"""
            QWidget {{ background-color: {p['bg_main']}; }}
            QLabel {{ color: {p['text_primary']}; background: transparent; }}
            QLabel#screenTitle {{ color: {p['accent']}; }}
            QPushButton#backButton {{
                background-color: transparent;
                color: {p['text_secondary']};
                border: 1px solid {p['border']};
                border-radius: 8px;
                padding: 8px 16px;
            }}
            QPushButton#backButton:hover {{
                background-color: {p['bg_card']};
                color: {p['text_primary']};
            }}
        """)
