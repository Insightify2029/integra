# -*- coding: utf-8 -*-
"""
Master Data Window
==================
نافذة إدارة البيانات الأساسية - قابلة لإعادة الاستخدام لكل الكيانات

Features:
- Enterprise-grade table for viewing all records
- Add / Edit / Delete with FK protection
- Excel Import with AI validation
- Excel Export (all or selected)
- Dark/Light theme support
- RTL Arabic layout
"""

from typing import Optional, List, Dict, Any

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QToolBar, QAction
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from ui.windows.base import BaseWindow
from ui.components.tables.enterprise import EnterpriseTableWidget
from ui.components.notifications import toast_success, toast_error, toast_warning, toast_info
from ui.dialogs.message import confirm, show_warning, show_error
from core.database.queries import select_all, delete_returning_count, get_count
from core.themes import get_current_theme
from core.logging import app_logger

from .master_data_dialog import MasterDataDialog
from .import_dialog import ImportDialog
from .export_choice_dialog import ExportChoiceDialog


# ═══════════════════════════════════════════════════════════════
# Entity Configurations
# ═══════════════════════════════════════════════════════════════

ENTITY_CONFIGS = {
    'nationalities': {
        'table': 'nationalities',
        'title_ar': 'الجنسيات',
        'title_en': 'Nationalities',
        'icon': '🌍',
        'columns_ar': ['#', 'الاسم بالعربي', 'الاسم بالإنجليزي'],
        'columns_keys': ['id', 'name_ar', 'name_en'],
        'fields': [
            {'key': 'name_ar', 'label': 'الاسم بالعربي', 'required': True, 'max_length': 100},
            {'key': 'name_en', 'label': 'الاسم بالإنجليزي', 'required': False, 'max_length': 100},
        ],
        'fk_checks': [
            {'table': 'employees', 'column': 'nationality_id', 'label': 'موظفين'},
        ],
        'order_by': 'name_ar',
    },
    'departments': {
        'table': 'departments',
        'title_ar': 'الأقسام',
        'title_en': 'Departments',
        'icon': '🏢',
        'columns_ar': ['#', 'الاسم بالعربي', 'الاسم بالإنجليزي'],
        'columns_keys': ['id', 'name_ar', 'name_en'],
        'fields': [
            {'key': 'name_ar', 'label': 'الاسم بالعربي', 'required': True, 'max_length': 200},
            {'key': 'name_en', 'label': 'الاسم بالإنجليزي', 'required': False, 'max_length': 200},
        ],
        'fk_checks': [
            {'table': 'employees', 'column': 'department_id', 'label': 'موظفين'},
        ],
        'order_by': 'name_ar',
    },
    'job_titles': {
        'table': 'job_titles',
        'title_ar': 'الوظائف',
        'title_en': 'Job Titles',
        'icon': '💼',
        'columns_ar': ['#', 'الاسم بالعربي', 'الاسم بالإنجليزي'],
        'columns_keys': ['id', 'name_ar', 'name_en'],
        'fields': [
            {'key': 'name_ar', 'label': 'الاسم بالعربي', 'required': True, 'max_length': 200},
            {'key': 'name_en', 'label': 'الاسم بالإنجليزي', 'required': False, 'max_length': 200},
        ],
        'fk_checks': [
            {'table': 'employees', 'column': 'job_title_id', 'label': 'موظفين'},
        ],
        'order_by': 'name_ar',
    },
    'banks': {
        'table': 'banks',
        'title_ar': 'البنوك',
        'title_en': 'Banks',
        'icon': '🏦',
        'columns_ar': ['#', 'الاسم بالعربي', 'الاسم بالإنجليزي'],
        'columns_keys': ['id', 'name_ar', 'name_en'],
        'fields': [
            {'key': 'name_ar', 'label': 'الاسم بالعربي', 'required': True, 'max_length': 100},
            {'key': 'name_en', 'label': 'الاسم بالإنجليزي', 'required': False, 'max_length': 100},
        ],
        'fk_checks': [
            {'table': 'employees', 'column': 'bank_id', 'label': 'موظفين'},
        ],
        'order_by': 'name_ar',
    },
    'companies': {
        'table': 'companies',
        'title_ar': 'الشركات',
        'title_en': 'Companies',
        'icon': '🏭',
        'columns_ar': ['#', 'الكود', 'الاسم بالعربي', 'الاسم بالإنجليزي'],
        'columns_keys': ['id', 'code', 'name_ar', 'name_en'],
        'fields': [
            {'key': 'code', 'label': 'كود الشركة', 'required': False, 'max_length': 20},
            {'key': 'name_ar', 'label': 'الاسم بالعربي', 'required': True, 'max_length': 200},
            {'key': 'name_en', 'label': 'الاسم بالإنجليزي', 'required': False, 'max_length': 200},
        ],
        'fk_checks': [
            {'table': 'employees', 'column': 'company_id', 'label': 'موظفين'},
        ],
        'order_by': 'name_ar',
    },
}


class MasterDataWindow(BaseWindow):
    """
    Professional master data management window.
    Reusable for all 5 entities (nationalities, departments, job_titles, banks, companies).

    Features:
    - Enterprise table with search, filter, column chooser
    - Add / Edit / Delete with foreign key protection
    - Excel Import with AI-powered validation
    - Excel Export (all data or selected only)
    - Full theme support (dark/light)
    """

    data_changed = pyqtSignal()

    def __init__(self, entity_key: str, parent=None):
        """
        Initialize master data window.

        Args:
            entity_key: One of 'nationalities', 'departments', 'job_titles', 'banks', 'companies'
            parent: Parent widget
        """
        if entity_key not in ENTITY_CONFIGS:
            raise ValueError(f"Unknown entity: {entity_key}")

        self._entity_key = entity_key
        self._config = ENTITY_CONFIGS[entity_key]
        self._parent_ref = parent

        title = f"{self._config['icon']} إدارة {self._config['title_ar']}"
        super().__init__(title_suffix=title)

        self._setup_action_bar()
        self._setup_central_area()
        self._setup_statusbar()
        self._apply_theme()
        self._load_data()

    # ═══════════════════════════════════════════════════════════════
    # UI Setup
    # ═══════════════════════════════════════════════════════════════

    def _setup_action_bar(self):
        """Setup action toolbar with CRUD and import/export buttons."""
        toolbar = QToolBar("شريط الأدوات")
        toolbar.setMovable(False)
        toolbar.setObjectName("masterDataToolbar")

        # Add New
        add_action = QAction("➕ إضافة جديد", self)
        add_action.triggered.connect(self._on_add)
        toolbar.addAction(add_action)

        # Edit Selected
        edit_action = QAction("✏️ تعديل المحدد", self)
        edit_action.triggered.connect(self._on_edit)
        toolbar.addAction(edit_action)

        # Delete Selected
        delete_action = QAction("🗑️ حذف المحدد", self)
        delete_action.triggered.connect(self._on_delete)
        toolbar.addAction(delete_action)

        toolbar.addSeparator()

        # Import Excel
        import_action = QAction("📥 استيراد Excel", self)
        import_action.triggered.connect(self._on_import)
        toolbar.addAction(import_action)

        # Export Excel
        export_action = QAction("📤 تصدير Excel", self)
        export_action.triggered.connect(self._on_export)
        toolbar.addAction(export_action)

        toolbar.addSeparator()

        # Refresh
        refresh_action = QAction("🔄 تحديث", self)
        refresh_action.triggered.connect(self._load_data)
        toolbar.addAction(refresh_action)

        self.addToolBar(toolbar)

    def _setup_central_area(self):
        """Setup central area with enterprise table."""
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(0)

        # Enterprise Table
        self._table = EnterpriseTableWidget()
        self._table.set_title(
            f"{self._config['icon']} {self._config['title_ar']} - {self._config['title_en']}"
        )
        self._table.set_search_placeholder(
            f"🔍 بحث في {self._config['title_ar']}..."
        )

        # Hide the built-in add button (we use toolbar instead)
        self._table.show_add_button(False)

        # Set columns
        self._table.set_columns(
            self._config['columns_ar'],
            self._config['columns_keys']
        )

        # Connect double-click to edit
        self._table.row_double_clicked.connect(self._on_row_double_clicked)

        layout.addWidget(self._table)

    def _setup_statusbar(self):
        """Setup status bar."""
        status = self.statusBar()
        status.setObjectName("masterDataStatusBar")
        status.showMessage("جاهز")

    def _apply_theme(self):
        """Apply current theme to the window."""
        theme = get_current_theme()

        if theme == 'dark':
            self.setStyleSheet("""
                QMainWindow { background-color: #0f172a; }

                QToolBar#masterDataToolbar {
                    background-color: #1e293b;
                    border: none;
                    border-bottom: 1px solid #334155;
                    padding: 8px;
                    spacing: 6px;
                }
                QToolBar#masterDataToolbar QToolButton {
                    background-color: #334155;
                    color: #f1f5f9;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 13px;
                    font-family: Cairo;
                    font-weight: 500;
                }
                QToolBar#masterDataToolbar QToolButton:hover {
                    background-color: #475569;
                }
                QToolBar#masterDataToolbar QToolButton:pressed {
                    background-color: #2563eb;
                }
                QToolBar#masterDataToolbar::separator {
                    width: 1px;
                    background-color: #475569;
                    margin: 0 10px;
                }

                QStatusBar#masterDataStatusBar {
                    background-color: #1e293b;
                    color: #94a3b8;
                    border-top: 1px solid #334155;
                    padding: 5px;
                    font-family: Cairo;
                }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow { background-color: #f8fafc; }

                QToolBar#masterDataToolbar {
                    background-color: #ffffff;
                    border: none;
                    border-bottom: 1px solid #e2e8f0;
                    padding: 8px;
                    spacing: 6px;
                }
                QToolBar#masterDataToolbar QToolButton {
                    background-color: #e2e8f0;
                    color: #1e293b;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 13px;
                    font-family: Cairo;
                    font-weight: 500;
                }
                QToolBar#masterDataToolbar QToolButton:hover {
                    background-color: #cbd5e1;
                }
                QToolBar#masterDataToolbar QToolButton:pressed {
                    background-color: #2563eb;
                    color: #ffffff;
                }
                QToolBar#masterDataToolbar::separator {
                    width: 1px;
                    background-color: #e2e8f0;
                    margin: 0 10px;
                }

                QStatusBar#masterDataStatusBar {
                    background-color: #ffffff;
                    color: #64748b;
                    border-top: 1px solid #e2e8f0;
                    padding: 5px;
                    font-family: Cairo;
                }
            """)

    # ═══════════════════════════════════════════════════════════════
    # Data Operations
    # ═══════════════════════════════════════════════════════════════

    def _load_data(self):
        """Load data from database into table."""
        try:
            table = self._config['table']
            keys = self._config['columns_keys']
            order = self._config['order_by']

            columns_sql = ', '.join(keys)
            query = f"SELECT {columns_sql} FROM {table} ORDER BY {order}"

            columns, rows = select_all(query)

            data = []
            if rows:
                for row in rows:
                    record = {}
                    for i, key in enumerate(keys):
                        record[key] = row[i] if row[i] is not None else ''
                    data.append(record)

            self._table.set_data(data)
            self.statusBar().showMessage(
                f"تم تحميل {len(data)} سجل من {self._config['title_ar']}"
            )

        except Exception as e:
            app_logger.error(f"Error loading {self._entity_key}: {e}", exc_info=True)
            toast_error(self, "خطأ", f"فشل تحميل البيانات: {e}")

    def _check_fk_references(self, record_id: int) -> Optional[str]:
        """
        Check if record has foreign key references (cannot delete).

        Args:
            record_id: The record ID to check

        Returns:
            Error message if references exist, None if safe to delete
        """
        for fk in self._config['fk_checks']:
            try:
                count = get_count(
                    f"SELECT COUNT(*) FROM {fk['table']} WHERE {fk['column']} = %s",
                    (record_id,)
                )
                if count and count > 0:
                    return (
                        f"لا يمكن حذف هذا السجل لأنه مرتبط بـ {count} "
                        f"{fk['label']} في جدول {fk['table']}"
                    )
            except Exception as e:
                app_logger.error(f"FK check error: {e}", exc_info=True)
                return f"خطأ أثناء التحقق من الارتباطات: {e}"

        return None

    # ═══════════════════════════════════════════════════════════════
    # Action Handlers
    # ═══════════════════════════════════════════════════════════════

    def _on_add(self):
        """Open add dialog."""
        dialog = MasterDataDialog(
            entity_key=self._entity_key,
            mode='add',
            parent=self
        )
        if dialog.exec_():
            self._load_data()
            toast_success(self, "تم", "تمت الإضافة بنجاح!")
            self.data_changed.emit()

    def _on_edit(self):
        """Open edit dialog for selected record."""
        selected = self._table.get_selected_row()
        if not selected:
            toast_warning(self, "تنبيه", "يرجى تحديد سجل للتعديل")
            return

        dialog = MasterDataDialog(
            entity_key=self._entity_key,
            mode='edit',
            record_data=selected,
            parent=self
        )
        if dialog.exec_():
            self._load_data()
            toast_success(self, "تم", "تم التعديل بنجاح!")
            self.data_changed.emit()

    def _on_row_double_clicked(self, row_data: dict):
        """Handle row double-click - opens edit dialog."""
        dialog = MasterDataDialog(
            entity_key=self._entity_key,
            mode='edit',
            record_data=row_data,
            parent=self
        )
        if dialog.exec_():
            self._load_data()
            toast_success(self, "تم", "تم التعديل بنجاح!")
            self.data_changed.emit()

    def _on_delete(self):
        """Delete selected record with FK protection."""
        selected = self._table.get_selected_row()
        if not selected:
            toast_warning(self, "تنبيه", "يرجى تحديد سجل للحذف")
            return

        record_id = selected.get('id')
        if not record_id:
            toast_error(self, "خطأ", "لم يتم تحديد السجل!")
            return

        # Display name for confirmation
        display_name = selected.get('name_ar', selected.get('name_en', str(record_id)))

        # Check foreign key references
        fk_error = self._check_fk_references(record_id)
        if fk_error:
            show_warning(self, "لا يمكن الحذف", fk_error)
            return

        # Confirm deletion
        if not confirm(
            self,
            "تأكيد الحذف",
            f"هل أنت متأكد من حذف: {display_name}؟\n\nهذا الإجراء لا يمكن التراجع عنه."
        ):
            return

        # Perform delete
        try:
            count = delete_returning_count(
                f"DELETE FROM {self._config['table']} WHERE id = %s",
                (record_id,)
            )
            if count and count > 0:
                self._load_data()
                toast_success(self, "تم", f"تم حذف: {display_name}")
                self.data_changed.emit()
            else:
                toast_error(self, "خطأ", "فشل حذف السجل!")
        except Exception as e:
            app_logger.error(f"Delete error: {e}", exc_info=True)
            toast_error(self, "خطأ", f"فشل الحذف: {e}")

    def _on_import(self):
        """Open Excel import dialog."""
        dialog = ImportDialog(
            entity_key=self._entity_key,
            parent=self
        )
        if dialog.exec_():
            self._load_data()
            toast_success(self, "تم", "تم الاستيراد بنجاح!")
            self.data_changed.emit()

    def _on_export(self):
        """Open export choice dialog."""
        all_data = self._table.get_all_data()
        selected_data = self._table.get_selected_rows()

        if not all_data:
            toast_warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return

        dialog = ExportChoiceDialog(
            all_data=all_data,
            selected_data=selected_data,
            columns=self._config['columns_ar'],
            title=self._config['title_ar'],
            parent=self
        )
        dialog.exec_()
