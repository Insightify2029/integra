# -*- coding: utf-8 -*-
"""
Master Data Dialog
==================
ديالوج إضافة وتعديل البيانات الأساسية

Features:
- Add new / Edit existing records
- Field validation (required, max length, duplicates)
- Dark/Light theme support
- RTL Arabic layout
"""

from typing import Optional, Dict, Any

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QGridLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.database.queries import select_all, insert_returning_id, update, get_count
from core.themes import get_current_theme
from core.logging import app_logger
from ui.components.notifications import toast_error, toast_warning


class MasterDataDialog(QDialog):
    """
    Professional Add/Edit dialog for master data entities.

    Supports:
    - Add mode: creates a new record
    - Edit mode: updates an existing record
    - Field validation with error feedback
    - Duplicate detection
    """

    def __init__(
        self,
        entity_key: str,
        mode: str = 'add',
        record_data: Optional[Dict] = None,
        parent=None
    ):
        """
        Initialize dialog.

        Args:
            entity_key: Entity identifier (e.g., 'nationalities')
            mode: 'add' or 'edit'
            record_data: Existing record data for edit mode
            parent: Parent widget
        """
        super().__init__(parent)

        # Avoid circular import - get config from the window module
        from .master_data_window import ENTITY_CONFIGS
        if entity_key not in ENTITY_CONFIGS:
            raise ValueError(f"Unknown entity: {entity_key}")

        self._entity_key = entity_key
        self._config = ENTITY_CONFIGS[entity_key]
        self._mode = mode
        self._record = record_data or {}
        self._inputs: Dict[str, QLineEdit] = {}
        self._error_labels: Dict[str, QLabel] = {}

        self._setup_ui()
        self._apply_theme()

        if mode == 'edit' and record_data:
            self._populate_fields(record_data)

    def _setup_ui(self):
        """Setup dialog UI."""
        icon = self._config['icon']
        title_ar = self._config['title_ar']

        if self._mode == 'add':
            self.setWindowTitle(f"{icon} إضافة {title_ar} جديد")
        else:
            self.setWindowTitle(f"{icon} تعديل {title_ar}")

        self.setMinimumWidth(500)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        # Header
        header_label = QLabel(
            f"{'➕ إضافة' if self._mode == 'add' else '✏️ تعديل'} {title_ar}"
        )
        header_label.setFont(QFont("Cairo", 16, QFont.Bold))
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setObjectName("dialogHeader")
        layout.addWidget(header_label)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("dialogSeparator")
        layout.addWidget(sep)

        # Fields Card
        card = QFrame()
        card.setObjectName("fieldsCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        # Build fields from config
        for field_def in self._config['fields']:
            field_key = field_def['key']
            field_label = field_def['label']
            is_required = field_def.get('required', False)

            # Label
            label_text = f"{field_label}{'  *' if is_required else ''}:"
            lbl = QLabel(label_text)
            lbl.setFont(QFont("Cairo", 12))
            lbl.setObjectName("fieldLabel")
            card_layout.addWidget(lbl)

            # Input
            inp = QLineEdit()
            inp.setFont(QFont("Cairo", 13))
            inp.setMinimumHeight(42)
            inp.setObjectName("fieldInput")
            inp.setPlaceholderText(f"أدخل {field_label}")
            max_len = field_def.get('max_length')
            if max_len:
                inp.setMaxLength(max_len)
            card_layout.addWidget(inp)
            self._inputs[field_key] = inp

            # Error label (hidden by default)
            err = QLabel("")
            err.setFont(QFont("Cairo", 10))
            err.setObjectName("fieldError")
            err.setVisible(False)
            card_layout.addWidget(err)
            self._error_labels[field_key] = err

        layout.addWidget(card)

        # Show record ID in edit mode
        if self._mode == 'edit':
            record_id = self._record.get('id', '')
            id_label = QLabel(f"رقم السجل: {record_id}")
            id_label.setFont(QFont("Cairo", 10))
            id_label.setObjectName("recordIdLabel")
            id_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(id_label)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        buttons_layout.addStretch()

        # Cancel
        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.setFont(QFont("Cairo", 12))
        cancel_btn.setMinimumHeight(44)
        cancel_btn.setMinimumWidth(140)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setProperty("buttonColor", "danger")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        # Save
        save_text = "➕ إضافة" if self._mode == 'add' else "✅ حفظ التعديلات"
        save_btn = QPushButton(save_text)
        save_btn.setFont(QFont("Cairo", 12, QFont.Bold))
        save_btn.setMinimumHeight(44)
        save_btn.setMinimumWidth(180)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setProperty("buttonColor", "success")
        save_btn.clicked.connect(self._on_save)
        buttons_layout.addWidget(save_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

    def _populate_fields(self, data: Dict):
        """Populate fields with existing data."""
        for field_def in self._config['fields']:
            key = field_def['key']
            if key in self._inputs and key in data:
                value = data[key]
                self._inputs[key].setText(str(value) if value else '')

    def _validate(self) -> bool:
        """
        Validate all fields.

        Returns:
            True if valid, False otherwise
        """
        is_valid = True

        # Clear previous errors
        for err in self._error_labels.values():
            err.setVisible(False)

        for field_def in self._config['fields']:
            key = field_def['key']
            value = self._inputs[key].text().strip()
            is_required = field_def.get('required', False)

            # Required check
            if is_required and not value:
                self._show_field_error(key, f"{field_def['label']} مطلوب")
                is_valid = False
                continue

            # Max length check
            max_len = field_def.get('max_length')
            if value and max_len and len(value) > max_len:
                self._show_field_error(key, f"الحد الأقصى {max_len} حرف")
                is_valid = False
                continue

        # Duplicate check (name_ar must be unique)
        if is_valid and 'name_ar' in self._inputs:
            name_ar = self._inputs['name_ar'].text().strip()
            if name_ar and self._is_duplicate('name_ar', name_ar):
                self._show_field_error('name_ar', "هذا الاسم موجود بالفعل!")
                is_valid = False

        # Duplicate check for name_en
        if is_valid and 'name_en' in self._inputs:
            name_en = self._inputs['name_en'].text().strip()
            if name_en and self._is_duplicate('name_en', name_en):
                self._show_field_error('name_en', "هذا الاسم الإنجليزي موجود بالفعل!")
                is_valid = False

        # Duplicate check for code (companies)
        if is_valid and 'code' in self._inputs:
            code = self._inputs['code'].text().strip()
            if code and self._is_duplicate('code', code):
                self._show_field_error('code', "هذا الكود موجود بالفعل!")
                is_valid = False

        return is_valid

    def _is_duplicate(self, column: str, value: str) -> bool:
        """Check if value already exists in the table."""
        try:
            table = self._config['table']
            if self._mode == 'edit':
                record_id = self._record.get('id')
                count = get_count(
                    f"SELECT COUNT(*) FROM {table} WHERE {column} = %s AND id != %s",
                    (value, record_id)
                )
            else:
                count = get_count(
                    f"SELECT COUNT(*) FROM {table} WHERE {column} = %s",
                    (value,)
                )
            return count is not None and count > 0
        except Exception as e:
            app_logger.error(f"Duplicate check error: {e}", exc_info=True)
            return False

    def _show_field_error(self, key: str, message: str):
        """Show error message for a field."""
        if key in self._error_labels:
            self._error_labels[key].setText(f"⚠️ {message}")
            self._error_labels[key].setVisible(True)

    def _on_save(self):
        """Handle save button click."""
        if not self._validate():
            return

        try:
            if self._mode == 'add':
                self._insert_record()
            else:
                self._update_record()
            self.accept()
        except Exception as e:
            app_logger.error(f"Save error: {e}", exc_info=True)
            toast_error(self, "خطأ", f"فشل الحفظ: {e}")

    def _insert_record(self):
        """Insert new record."""
        fields = []
        values = []
        placeholders = []

        for field_def in self._config['fields']:
            key = field_def['key']
            value = self._inputs[key].text().strip()
            if value:
                fields.append(key)
                values.append(value)
                placeholders.append('%s')

        if not fields:
            toast_warning(self, "تنبيه", "يرجى إدخال بيانات!")
            return

        columns_str = ', '.join(fields)
        placeholders_str = ', '.join(placeholders)
        table = self._config['table']

        query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders_str}) RETURNING id"
        new_id = insert_returning_id(query, tuple(values))

        if not new_id:
            raise Exception("فشل إنشاء السجل")

        app_logger.info(
            f"Master data: Added {self._entity_key} id={new_id}"
        )

    def _update_record(self):
        """Update existing record."""
        record_id = self._record.get('id')
        if not record_id:
            raise Exception("لم يتم تحديد السجل!")

        set_parts = []
        values = []

        for field_def in self._config['fields']:
            key = field_def['key']
            value = self._inputs[key].text().strip()
            set_parts.append(f"{key} = %s")
            values.append(value if value else None)

        values.append(record_id)
        table = self._config['table']
        set_str = ', '.join(set_parts)

        query = f"UPDATE {table} SET {set_str} WHERE id = %s"
        success = update(query, tuple(values))

        if not success:
            raise Exception("فشل تحديث السجل")

        app_logger.info(
            f"Master data: Updated {self._entity_key} id={record_id}"
        )

    def _apply_theme(self):
        """Apply current theme."""
        theme = get_current_theme()

        if theme == 'dark':
            self.setStyleSheet("""
                QDialog { background-color: #1e293b; }

                QLabel { color: #f1f5f9; background: transparent; }
                QLabel#dialogHeader { color: #38bdf8; }
                QLabel#fieldLabel { color: #94a3b8; }
                QLabel#fieldError { color: #f87171; font-weight: bold; }
                QLabel#recordIdLabel { color: #64748b; }

                QFrame#dialogSeparator { background-color: #334155; }
                QFrame#fieldsCard {
                    background-color: #0f172a;
                    border: 1px solid #334155;
                    border-radius: 12px;
                }

                QLineEdit#fieldInput {
                    background-color: #1e293b;
                    color: #f1f5f9;
                    border: 2px solid #334155;
                    border-radius: 8px;
                    padding: 8px 12px;
                    font-size: 13px;
                }
                QLineEdit#fieldInput:focus { border-color: #06b6d4; }

                QPushButton {
                    background-color: #334155;
                    color: #f1f5f9;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #475569; }
                QPushButton[buttonColor="success"] { background-color: #10b981; }
                QPushButton[buttonColor="success"]:hover { background-color: #059669; }
                QPushButton[buttonColor="danger"] { background-color: #ef4444; }
                QPushButton[buttonColor="danger"]:hover { background-color: #dc2626; }
            """)
        else:
            self.setStyleSheet("""
                QDialog { background-color: #ffffff; }

                QLabel { color: #1e293b; background: transparent; }
                QLabel#dialogHeader { color: #0891b2; }
                QLabel#fieldLabel { color: #64748b; }
                QLabel#fieldError { color: #ef4444; font-weight: bold; }
                QLabel#recordIdLabel { color: #94a3b8; }

                QFrame#dialogSeparator { background-color: #e2e8f0; }
                QFrame#fieldsCard {
                    background-color: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 12px;
                }

                QLineEdit#fieldInput {
                    background-color: #ffffff;
                    color: #1e293b;
                    border: 2px solid #e2e8f0;
                    border-radius: 8px;
                    padding: 8px 12px;
                    font-size: 13px;
                }
                QLineEdit#fieldInput:focus { border-color: #06b6d4; }

                QPushButton {
                    background-color: #e2e8f0;
                    color: #1e293b;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #cbd5e1; }
                QPushButton[buttonColor="success"] { background-color: #10b981; color: #ffffff; }
                QPushButton[buttonColor="success"]:hover { background-color: #059669; }
                QPushButton[buttonColor="danger"] { background-color: #ef4444; color: #ffffff; }
                QPushButton[buttonColor="danger"]:hover { background-color: #dc2626; }
            """)
