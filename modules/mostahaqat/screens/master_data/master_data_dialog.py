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
- Duplicate detection (using parameterized queries)
- Dark/Light theme support
- RTL Arabic layout
"""

from typing import Optional, Dict, Any, List, Tuple

from psycopg2 import sql as psycopg2_sql

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame,
)
from PyQt5.QtCore import Qt

from core.database.queries import insert_returning_id, update, get_scalar
from core.threading import run_in_background
from core.themes import (
    get_current_palette, get_font,
    FONT_SIZE_TITLE, FONT_SIZE_BODY, FONT_SIZE_SMALL, FONT_WEIGHT_BOLD,
)
from core.logging import app_logger
from ui.components.notifications import toast_error, toast_warning, toast_success

from modules.designer.form_renderer import FormRenderer


# Allowed table names for master data (whitelist for SQL safety)
_ALLOWED_TABLES = frozenset({
    'nationalities', 'departments', 'job_titles', 'banks', 'companies',
    'employee_statuses',
})

# Allowed column names for master data fields (whitelist for SQL safety)
_ALLOWED_COLUMNS = frozenset({
    'name_ar', 'name_en', 'code', 'id',
})


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
        self._save_btn: Optional[QPushButton] = None
        self._saving = False

        self._setup_ui()
        self._apply_theme()

        if mode == 'edit' and record_data:
            self._populate_fields(record_data)

    def _setup_ui(self) -> None:
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
        self._save_btn = QPushButton(save_text)
        self._save_btn.setFont(get_font(FONT_SIZE_BODY, FONT_WEIGHT_BOLD))
        self._save_btn.setMinimumHeight(44)
        self._save_btn.setMinimumWidth(180)
        self._save_btn.setCursor(Qt.PointingHandCursor)
        self._save_btn.setProperty("buttonColor", "success")
        self._save_btn.clicked.connect(self._on_save)
        buttons_layout.addWidget(self._save_btn)

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
                    "id": "data",
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

    def _populate_fields(self, data: Dict) -> None:
        """Populate fields with existing data."""
        self._renderer.set_data(data)

    def _validate_local(self) -> bool:
        """Validate fields locally (no DB access - safe for main thread)."""
        is_valid, errors = self._renderer.validate()
        return is_valid

    def _set_saving(self, saving: bool) -> None:
        """Enable/disable save button during async operation."""
        self._saving = saving
        if self._save_btn:
            self._save_btn.setEnabled(not saving)
            if saving:
                self._save_btn.setText("⏳ جارٍ الحفظ...")
            else:
                self._save_btn.setText(
                    "➕ إضافة" if self._mode == 'add' else "✅ حفظ التعديلات"
                )

    def _on_save(self) -> None:
        """Handle save button click - validates locally, then runs DB ops in background."""
        if self._saving:
            return

        if not self._validate_local():
            return

        # Collect form data on main thread (widget access must be on main thread)
        form_data = self._collect_form_data()
        if form_data is None:
            return

        self._set_saving(True)

        # Run all DB operations (duplicate check + insert/update) in background (Rule #13)
        run_in_background(
            self._do_save_in_background,
            args=(form_data,),
            on_finished=self._on_save_finished,
            on_error=self._on_save_error,
        )

    def _collect_form_data(self) -> Optional[Dict[str, Any]]:
        """Collect all form data needed for save (called on main thread)."""
        table = self._config['table']
        if table not in _ALLOWED_TABLES:
            app_logger.error(f"Table '{table}' not in allowed tables whitelist")
            return None

        field_keys: List[str] = []
        values: List[Any] = []
        duplicate_checks: List[Tuple[str, str, str]] = []

        for field_def in self._config['fields']:
            key = field_def['key']
            if key not in _ALLOWED_COLUMNS:
                continue
            value = self._renderer.get_field_value(key)
            str_value = str(value).strip() if value is not None else ""

            if self._mode == 'add':
                if str_value:
                    field_keys.append(key)
                    values.append(str_value)
            else:
                field_keys.append(key)
                values.append(str_value if str_value else None)

            # Prepare duplicate checks for non-empty values
            if str_value and key in ('name_ar', 'name_en', 'code'):
                label_map = {
                    'name_ar': "هذا الاسم موجود بالفعل!",
                    'name_en': "هذا الاسم الإنجليزي موجود بالفعل!",
                    'code': "هذا الكود موجود بالفعل!",
                }
                duplicate_checks.append((key, str_value, label_map[key]))

        if self._mode == 'add' and not field_keys:
            toast_warning(self, "تنبيه", "يرجى إدخال بيانات!")
            return None

        return {
            'table': table,
            'field_keys': field_keys,
            'values': values,
            'duplicate_checks': duplicate_checks,
            'record_id': self._record.get('id') if self._mode == 'edit' else None,
        }

    def _do_save_in_background(self, form_data: Dict[str, Any]) -> bool:
        """
        Run duplicate check + insert/update in a background thread (Rule #13).

        Returns True on success. Raises Exception with user-facing message on failure.
        """
        table = form_data['table']
        field_keys = form_data['field_keys']
        values = form_data['values']
        record_id = form_data['record_id']

        # Step 1: Duplicate checks
        for column, value, dup_msg in form_data['duplicate_checks']:
            if self._is_duplicate_sync(table, column, value, record_id):
                raise Exception(dup_msg)

        # Step 2: Insert or Update
        if self._mode == 'add':
            return self._insert_record_sync(table, field_keys, values)
        else:
            if record_id is None:
                raise Exception("لم يتم تحديد السجل!")
            return self._update_record_sync(table, field_keys, values, record_id)

    @staticmethod
    def _is_duplicate_sync(
        table: str, column: str, value: str, record_id: Optional[int]
    ) -> bool:
        """Check duplicate in DB (called from background thread)."""
        try:
            if table not in _ALLOWED_TABLES:
                app_logger.error(f"Table '{table}' not in allowed tables whitelist")
                return True
            if column not in _ALLOWED_COLUMNS:
                app_logger.error(f"Column '{column}' not in allowed columns whitelist")
                return True

            if record_id is not None:
                query = psycopg2_sql.SQL(
                    "SELECT COUNT(*) FROM {} WHERE {} = %s AND id != %s"
                ).format(
                    psycopg2_sql.Identifier(table),
                    psycopg2_sql.Identifier(column),
                )
                count = get_scalar(query, (value, record_id))
            else:
                query = psycopg2_sql.SQL(
                    "SELECT COUNT(*) FROM {} WHERE {} = %s"
                ).format(
                    psycopg2_sql.Identifier(table),
                    psycopg2_sql.Identifier(column),
                )
                count = get_scalar(query, (value,))

            return count is not None and count > 0
        except Exception as e:
            app_logger.error(f"Duplicate check error: {e}", exc_info=True)
            return True

    def _insert_record_sync(
        self, table: str, field_keys: List[str], values: List[Any]
    ) -> bool:
        """Insert record (called from background thread)."""
        query = psycopg2_sql.SQL(
            "INSERT INTO {} ({}) VALUES ({}) RETURNING id"
        ).format(
            psycopg2_sql.Identifier(table),
            psycopg2_sql.SQL(', ').join(
                psycopg2_sql.Identifier(k) for k in field_keys
            ),
            psycopg2_sql.SQL(', ').join(
                psycopg2_sql.Placeholder() for _ in field_keys
            ),
        )
        new_id = insert_returning_id(query, tuple(values))

        if not new_id:
            raise Exception("فشل إنشاء السجل")

        app_logger.info(f"Master data: Added {self._entity_key} id={new_id}")
        return True

    def _update_record_sync(
        self, table: str, field_keys: List[str], values: List[Any],
        record_id: int,
    ) -> bool:
        """Update record (called from background thread)."""
        update_values = list(values) + [record_id]

        set_clause = psycopg2_sql.SQL(', ').join(
            psycopg2_sql.SQL("{} = %s").format(psycopg2_sql.Identifier(k))
            for k in field_keys
        )
        query = psycopg2_sql.SQL("UPDATE {} SET {} WHERE id = %s").format(
            psycopg2_sql.Identifier(table),
            set_clause,
        )
        success = update(query, tuple(update_values))

        if not success:
            raise Exception("فشل تحديث السجل")

        app_logger.info(f"Master data: Updated {self._entity_key} id={record_id}")
        return True

    def _on_save_finished(self, result: Any) -> None:
        """Handle successful save (callback on main thread)."""
        self._set_saving(False)
        if result:
            toast_success(self, "تم", "تم الحفظ بنجاح")
            self.accept()

    def _on_save_error(self, exc_type: type, message: str, traceback: str) -> None:
        """Handle save error (callback on main thread)."""
        self._set_saving(False)
        app_logger.error(f"Save error: {message}")
        # Duplicate detection messages are user-friendly
        if any(
            keyword in message
            for keyword in ("موجود بالفعل", "فشل إنشاء", "فشل تحديث", "لم يتم تحديد")
        ):
            toast_warning(self, "تنبيه", message)
        else:
            toast_error(self, "خطأ", "فشل الحفظ. يرجى المحاولة مرة أخرى.")

    def _apply_theme(self) -> None:
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
