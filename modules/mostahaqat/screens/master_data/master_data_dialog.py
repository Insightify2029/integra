# -*- coding: utf-8 -*-
"""
Master Data Dialog (FormRenderer-based)
=======================================
ديالوج إضافة وتعديل البيانات الأساسية - مبني على FormRenderer

Migrated from hardcoded Python layout to JSON-configurable FormRenderer.
Dynamically builds form definition from ENTITY_CONFIGS.
Maintains same public API as the original.

Features:
- Add new / Edit existing records
- Field validation via FormRenderer's ValidationEngine
- Duplicate detection
- Dark/Light theme support
- RTL Arabic layout
"""

from typing import Optional, Dict, Any

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame,
)
from PyQt5.QtCore import Qt

from core.database.queries import insert_returning_id, update, get_count
from core.themes import (
    get_current_palette, get_font,
    FONT_SIZE_TITLE, FONT_SIZE_BODY, FONT_SIZE_SMALL, FONT_WEIGHT_BOLD,
)
from core.logging import app_logger
from ui.components.notifications import toast_error, toast_warning

from modules.designer.form_renderer import FormRenderer


class MasterDataDialog(QDialog):
    """
    Professional Add/Edit dialog for master data entities.

    Supports:
    - Add mode: creates a new record
    - Edit mode: updates an existing record
    - Field validation via FormRenderer
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

        self._setup_ui()
        self._apply_theme()

        if mode == 'edit' and record_data:
            self._populate_fields(record_data)

    def _setup_ui(self):
        """Setup dialog UI with FormRenderer."""
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

        # Build form definition from entity config and render with FormRenderer
        form_dict = self._build_form_dict()
        self._renderer = FormRenderer(self)
        self._renderer.load_form_dict(form_dict)
        layout.addWidget(self._renderer)

        # Show record ID in edit mode
        if self._mode == 'edit':
            record_id = self._record.get('id', '')
            id_label = QLabel(f"رقم السجل: {record_id}")
            id_label.setFont(get_font(FONT_SIZE_SMALL))
            id_label.setObjectName("recordIdLabel")
            id_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(id_label)

        # Buttons (custom buttons outside FormRenderer for dialog control)
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

    def _build_form_dict(self) -> dict:
        """Build a FormRenderer-compatible form definition from entity config."""
        fields = []
        for i, field_def in enumerate(self._config['fields']):
            key = field_def['key']
            label = field_def['label']
            is_required = field_def.get('required', False)
            max_length = field_def.get('max_length')

            validation_rules = []
            if is_required:
                validation_rules.append({
                    "rule": "required",
                    "message_ar": f"{label} مطلوب",
                })
            if max_length:
                validation_rules.append({
                    "rule": "max_length",
                    "value": max_length,
                    "message_ar": f"الحد الأقصى {max_length} حرف",
                })

            fields.append({
                "id": key,
                "widget_type": "text_input",
                "label_ar": label,
                "label_en": key,
                "placeholder_ar": f"أدخل {label}",
                "layout": {
                    "row": i,
                    "col": 0,
                    "colspan": 1,
                    "rowspan": 1,
                },
                "properties": {
                    "readonly": False,
                    "enabled": True,
                    "visible": True,
                },
                "validation": validation_rules,
                "data_binding": {
                    "column": key,
                    "type": "string",
                },
            })

        return {
            "version": "2.0",
            "form_id": f"master_data_{self._entity_key}",
            "form_name_ar": "",
            "form_name_en": "",
            "target_table": self._config['table'],
            "settings": {
                "direction": "rtl",
                "layout_mode": "smart_grid",
                "columns": 1,
                "column_gap": 20,
                "row_gap": 10,
                "margins": {"top": 10, "right": 15, "bottom": 10, "left": 15},
                "min_width": 400,
                "max_width": 500,
                "scrollable": False,
                "show_required_indicator": True,
                "save_button_position": "bottom_left",
            },
            "sections": [
                {
                    "section_id": "data",
                    "title_ar": "",
                    "title_en": "",
                    "collapsible": False,
                    "fields": fields,
                }
            ],
            "actions": [],
            "rules": [],
            "events": {},
        }

    def _populate_fields(self, data: Dict):
        """Populate fields with existing data."""
        self._renderer.set_data(data)

    def _validate(self) -> bool:
        """Validate all fields including duplicate checks."""
        # Use FormRenderer's built-in validation first
        is_valid, errors = self._renderer.validate()
        if not is_valid:
            return False

        # Additional duplicate checks
        if 'name_ar' in self._renderer._input_widgets:
            name_ar = self._renderer.get_field_value('name_ar')
            if name_ar and isinstance(name_ar, str) and name_ar.strip():
                if self._is_duplicate('name_ar', name_ar.strip()):
                    toast_warning(self, "تنبيه", "هذا الاسم موجود بالفعل!")
                    return False

        if 'name_en' in self._renderer._input_widgets:
            name_en = self._renderer.get_field_value('name_en')
            if name_en and isinstance(name_en, str) and name_en.strip():
                if self._is_duplicate('name_en', name_en.strip()):
                    toast_warning(self, "تنبيه", "هذا الاسم الإنجليزي موجود بالفعل!")
                    return False

        if 'code' in self._renderer._input_widgets:
            code = self._renderer.get_field_value('code')
            if code and isinstance(code, str) and code.strip():
                if self._is_duplicate('code', code.strip()):
                    toast_warning(self, "تنبيه", "هذا الكود موجود بالفعل!")
                    return False

        return True

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
        """Insert new record using FormRenderer data."""
        fields = []
        values = []
        placeholders = []

        for field_def in self._config['fields']:
            key = field_def['key']
            value = self._renderer.get_field_value(key)
            str_value = str(value).strip() if value else ""
            if str_value:
                fields.append(key)
                values.append(str_value)
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
        """Update existing record using FormRenderer data."""
        record_id = self._record.get('id')
        if not record_id:
            raise Exception("لم يتم تحديد السجل!")

        set_parts = []
        values = []

        for field_def in self._config['fields']:
            key = field_def['key']
            value = self._renderer.get_field_value(key)
            str_value = str(value).strip() if value else ""
            set_parts.append(f"{key} = %s")
            values.append(str_value if str_value else None)

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
