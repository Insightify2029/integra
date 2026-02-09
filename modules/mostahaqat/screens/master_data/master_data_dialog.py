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
from core.themes import get_current_palette, get_font, FONT_SIZE_TITLE, FONT_SIZE_BODY, FONT_SIZE_SMALL, FONT_WEIGHT_BOLD
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
        header_label.setFont(get_font(FONT_SIZE_TITLE, FONT_WEIGHT_BOLD))
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
            lbl.setFont(get_font(FONT_SIZE_BODY))
            lbl.setObjectName("fieldLabel")
            card_layout.addWidget(lbl)

            # Input
            inp = QLineEdit()
            inp.setFont(get_font(FONT_SIZE_BODY))
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
            err.setFont(get_font(FONT_SIZE_SMALL))
            err.setObjectName("fieldError")
            err.setVisible(False)
            card_layout.addWidget(err)
            self._error_labels[field_key] = err

        layout.addWidget(card)

        # Show record ID in edit mode
        if self._mode == 'edit':
            record_id = self._record.get('id', '')
            id_label = QLabel(f"رقم السجل: {record_id}")
            id_label.setFont(get_font(FONT_SIZE_SMALL))
            id_label.setObjectName("recordIdLabel")
            id_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(id_label)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        buttons_layout.addStretch()

        # Cancel
        cancel_btn = QPushButton("❌ إلغاء")
        cancel_btn.setFont(get_font(FONT_SIZE_BODY))
        cancel_btn.setMinimumHeight(44)
        cancel_btn.setMinimumWidth(140)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setProperty("buttonColor", "danger")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        # Save
        save_text = "➕ إضافة" if self._mode == 'add' else "✅ حفظ التعديلات"
        save_btn = QPushButton(save_text)
        save_btn.setFont(get_font(FONT_SIZE_BODY, FONT_WEIGHT_BOLD))
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
        """Apply current theme using palette."""
        p = get_current_palette()
        self.setStyleSheet(f"""
            QDialog {{ background-color: {p['bg_dialog']}; }}

            QLabel {{ color: {p['text_primary']}; background: transparent; }}
            QLabel#dialogHeader {{ color: {p['accent']}; }}
            QLabel#fieldLabel {{ color: {p['text_secondary']}; }}
            QLabel#fieldError {{ color: {p['danger']}; font-weight: bold; }}
            QLabel#recordIdLabel {{ color: {p['text_muted']}; }}

            QFrame#dialogSeparator {{ background-color: {p['border']}; }}
            QFrame#fieldsCard {{
                background-color: {p['bg_main']};
                border: 1px solid {p['border']};
                border-radius: 12px;
            }}

            QLineEdit#fieldInput {{
                background-color: {p['bg_input']};
                color: {p['text_primary']};
                border: 2px solid {p['border']};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }}
            QLineEdit#fieldInput:focus {{ border-color: {p['border_focus']}; }}

            QPushButton {{
                background-color: {p['bg_card']};
                color: {p['text_primary']};
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {p['bg_hover']}; }}
            QPushButton[buttonColor="success"] {{ background-color: {p['success']}; color: {p['text_on_primary']}; }}
            QPushButton[buttonColor="success"]:hover {{ background-color: {p['success']}; }}
            QPushButton[buttonColor="danger"] {{ background-color: {p['danger']}; color: {p['text_on_primary']}; }}
            QPushButton[buttonColor="danger"]:hover {{ background-color: {p['danger']}; }}
        """)
