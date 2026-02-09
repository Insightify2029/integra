"""
Form Builder Window
===================
Main window for visual form builder.

Features:
- WYSIWYG form design
- Widget toolbox
- Property editor
- Data binding
- Preview mode
- Save/Load forms
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QToolBar,
    QAction, QMenu, QMenuBar, QStatusBar, QLabel, QFileDialog,
    QMessageBox, QSplitter, QComboBox, QPushButton, QDialog,
    QDialogButtonBox, QFormLayout, QLineEdit
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QKeySequence, QCloseEvent

from core.logging import app_logger
from core.themes import get_current_palette

from .form_canvas import FormCanvas, WidgetType
from .widget_toolbox import WidgetToolbox
from .property_editor import FormPropertyEditor
from .data_binding import DataBindingManager


class NewFormDialog(QDialog):
    """Dialog for creating new form."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("نموذج جديد")
        self.setModal(True)
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("اسم النموذج")
        form.addRow("اسم النموذج:", self.name_edit)

        self.table_combo = QComboBox()
        self.table_combo.addItems(["employees", "departments", "companies"])
        form.addRow("الجدول الرئيسي:", self.table_combo)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_settings(self) -> Dict[str, Any]:
        return {
            "name": self.name_edit.text(),
            "table": self.table_combo.currentText()
        }


class FormBuilderWindow(QMainWindow):
    """
    Main form builder window.

    Provides visual form design capabilities.
    """

    def __init__(self, form_path: str = None, parent=None):
        super().__init__(parent)

        self._form_path = form_path
        self._file_path: Optional[str] = None
        self._modified = False
        self._binding_manager = DataBindingManager()

        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_statusbar()
        self._connect_signals()

        if form_path:
            self._load_file(form_path)
        else:
            self._new_form()

        app_logger.info("FormBuilderWindow initialized")

    def _setup_ui(self) -> None:
        """Setup window UI."""
        self.setWindowTitle("منشئ النماذج - INTEGRA")
        self.setMinimumSize(1200, 800)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)

        # Left - Widget Toolbox
        self._toolbox = WidgetToolbox()
        splitter.addWidget(self._toolbox)

        # Center - Form Canvas
        self._canvas = FormCanvas()
        splitter.addWidget(self._canvas)

        # Right - Properties
        self._properties = FormPropertyEditor()
        splitter.addWidget(self._properties)

        splitter.setSizes([180, 700, 280])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)

        layout.addWidget(splitter)
        self.setCentralWidget(central)

        # Style
        p = get_current_palette()
        self.setStyleSheet(f"""
            QMainWindow {{
                background: {p['bg_main']};
            }}
            QToolBar {{
                background: {p['bg_card']};
                border-bottom: 1px solid {p['border']};
                padding: 4px;
            }}
            QMenuBar {{
                background: {p['bg_card']};
                border-bottom: 1px solid {p['border']};
            }}
        """)

    def _setup_menus(self) -> None:
        """Setup menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("ملف")

        new_action = QAction("جديد", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self._new_form)
        file_menu.addAction(new_action)

        open_action = QAction("فتح...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        save_action = QAction("حفظ", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self._save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction("حفظ باسم...", self)
        save_as_action.triggered.connect(self._save_file_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        close_action = QAction("إغلاق", self)
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)

        # Edit menu
        edit_menu = menubar.addMenu("تحرير")

        undo_action = QAction("تراجع", self)
        undo_action.setShortcut(QKeySequence.Undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("إعادة", self)
        redo_action.setShortcut(QKeySequence.Redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        delete_action = QAction("حذف", self)
        delete_action.setShortcut(QKeySequence.Delete)
        delete_action.triggered.connect(self._delete_selected)
        edit_menu.addAction(delete_action)

        # View menu
        view_menu = menubar.addMenu("عرض")

        grid_action = QAction("إظهار الشبكة", self)
        grid_action.setCheckable(True)
        grid_action.setChecked(True)
        grid_action.triggered.connect(self._canvas.set_grid_visible)
        view_menu.addAction(grid_action)

        view_menu.addSeparator()

        preview_action = QAction("معاينة النموذج", self)
        preview_action.triggered.connect(self._preview)
        view_menu.addAction(preview_action)

        # Insert menu
        insert_menu = menubar.addMenu("إدراج")

        for widget_type in WidgetType:
            action = QAction(widget_type.value, self)
            action.triggered.connect(
                lambda checked, t=widget_type: self._insert_widget(t)
            )
            insert_menu.addAction(action)

        # Help menu
        help_menu = menubar.addMenu("مساعدة")

        about_action = QAction("حول منشئ النماذج", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_toolbar(self) -> None:
        """Setup toolbar."""
        toolbar = QToolBar("الأدوات")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)

        # File operations
        new_btn = QPushButton("جديد")
        new_btn.clicked.connect(self._new_form)
        toolbar.addWidget(new_btn)

        open_btn = QPushButton("فتح")
        open_btn.clicked.connect(self._open_file)
        toolbar.addWidget(open_btn)

        save_btn = QPushButton("حفظ")
        save_btn.clicked.connect(self._save_file)
        toolbar.addWidget(save_btn)

        toolbar.addSeparator()

        # Quick add widgets
        label_btn = QPushButton("Aa نص")
        label_btn.clicked.connect(lambda: self._insert_widget(WidgetType.LABEL))
        toolbar.addWidget(label_btn)

        input_btn = QPushButton("[__] حقل")
        input_btn.clicked.connect(lambda: self._insert_widget(WidgetType.TEXT_INPUT))
        toolbar.addWidget(input_btn)

        combo_btn = QPushButton("[▼] قائمة")
        combo_btn.clicked.connect(lambda: self._insert_widget(WidgetType.COMBO_BOX))
        toolbar.addWidget(combo_btn)

        check_btn = QPushButton("☑ اختيار")
        check_btn.clicked.connect(lambda: self._insert_widget(WidgetType.CHECK_BOX))
        toolbar.addWidget(check_btn)

        btn_btn = QPushButton("[OK] زر")
        btn_btn.clicked.connect(lambda: self._insert_widget(WidgetType.BUTTON))
        toolbar.addWidget(btn_btn)

        toolbar.addSeparator()

        # Preview
        preview_btn = QPushButton("معاينة")
        preview_btn.clicked.connect(self._preview)
        toolbar.addWidget(preview_btn)

    def _setup_statusbar(self) -> None:
        """Setup status bar."""
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)

        self._sel_label = QLabel("لا يوجد تحديد")
        self._statusbar.addWidget(self._sel_label)

    def _connect_signals(self) -> None:
        """Connect signals."""
        self._canvas.widget_selected.connect(self._on_widget_selected)
        self._canvas.widget_changed.connect(self._on_widget_changed)
        self._canvas.canvas_changed.connect(self._on_canvas_changed)

        self._properties.property_changed.connect(self._on_property_changed)

    def _new_form(self) -> None:
        """Create new form."""
        if self._modified:
            reply = QMessageBox.question(
                self,
                "حفظ التغييرات",
                "هل تريد حفظ التغييرات؟",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )

            if reply == QMessageBox.Save:
                if not self._save_file():
                    return
            elif reply == QMessageBox.Cancel:
                return

        dialog = NewFormDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            settings = dialog.get_settings()

            self._canvas.clear()
            self._file_path = None
            self._modified = False

            self._update_title()

    def _open_file(self) -> None:
        """Open form file."""
        if self._modified:
            reply = QMessageBox.question(
                self,
                "حفظ التغييرات",
                "هل تريد حفظ التغييرات؟",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )

            if reply == QMessageBox.Save:
                if not self._save_file():
                    return
            elif reply == QMessageBox.Cancel:
                return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "فتح نموذج",
            "",
            "ملفات النماذج (*.iform);;كل الملفات (*.*)"
        )

        if file_path:
            self._load_file(file_path)

    def _load_file(self, file_path: str) -> bool:
        """Load form from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self._canvas.from_dict(data.get("canvas", {}))
            self._binding_manager.from_dict(data.get("bindings", {}))

            self._file_path = file_path
            self._modified = False
            self._update_title()

            app_logger.info(f"Loaded form: {file_path}")
            return True

        except Exception as e:
            QMessageBox.critical(
                self,
                "خطأ",
                f"فشل فتح الملف:\n{str(e)}"
            )
            app_logger.error(f"Failed to load form: {e}")
            return False

    def _save_file(self) -> bool:
        """Save form to file."""
        if not self._file_path:
            return self._save_file_as()

        return self._save_to_path(self._file_path)

    def _save_file_as(self) -> bool:
        """Save form to new file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "حفظ النموذج",
            "",
            "ملفات النماذج (*.iform)"
        )

        if file_path:
            if not file_path.endswith('.iform'):
                file_path += '.iform'
            return self._save_to_path(file_path)

        return False

    def _save_to_path(self, file_path: str) -> bool:
        """Save form to specific path."""
        try:
            data = {
                "canvas": self._canvas.to_dict(),
                "bindings": self._binding_manager.to_dict()
            }

            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self._file_path = file_path
            self._modified = False
            self._update_title()

            self._statusbar.showMessage("تم الحفظ", 3000)
            app_logger.info(f"Saved form: {file_path}")
            return True

        except Exception as e:
            QMessageBox.critical(
                self,
                "خطأ",
                f"فشل حفظ الملف:\n{str(e)}"
            )
            app_logger.error(f"Failed to save form: {e}")
            return False

    def _insert_widget(self, widget_type: WidgetType) -> None:
        """Insert new widget."""
        self._canvas.add_widget(widget_type)

    def _delete_selected(self) -> None:
        """Delete selected widget."""
        widget = self._canvas.get_selected_widget()
        if widget:
            self._canvas.remove_widget(widget.id)

    def _preview(self) -> None:
        """Preview form."""
        QMessageBox.information(
            self,
            "معاينة",
            "ميزة المعاينة قيد التطوير"
        )

    def _on_widget_selected(self, widget) -> None:
        """Handle widget selection."""
        self._properties.set_widget(widget)

        if widget:
            self._sel_label.setText(f"محدد: {widget.widget_type.value}")
        else:
            self._sel_label.setText("لا يوجد تحديد")

    def _on_widget_changed(self, widget) -> None:
        """Handle widget change."""
        self._properties.set_widget(widget)
        self._modified = True
        self._update_title()

    def _on_canvas_changed(self) -> None:
        """Handle canvas change."""
        self._modified = True
        self._update_title()

    def _on_property_changed(self, widget) -> None:
        """Handle property change."""
        self._canvas.update_widget(widget)
        self._modified = True
        self._update_title()

    def _update_title(self) -> None:
        """Update window title."""
        title = "منشئ النماذج - INTEGRA"

        if self._file_path:
            title = f"{Path(self._file_path).name} - {title}"

        if self._modified:
            title = f"* {title}"

        self.setWindowTitle(title)

    def _show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "حول منشئ النماذج",
            """<h3>منشئ النماذج - INTEGRA</h3>
            <p>الإصدار 1.0.0</p>
            <p>أداة تصميم نماذج بواجهة سحب وإفلات</p>
            <p>المميزات:</p>
            <ul>
                <li>سحب وإفلات الأدوات</li>
                <li>ربط البيانات بقاعدة البيانات</li>
                <li>التحقق من صحة البيانات</li>
                <li>معاينة النموذج</li>
            </ul>
            """
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close."""
        if self._modified:
            reply = QMessageBox.question(
                self,
                "حفظ التغييرات",
                "هل تريد حفظ التغييرات قبل الإغلاق؟",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )

            if reply == QMessageBox.Save:
                if not self._save_file():
                    event.ignore()
                    return
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return

        event.accept()
