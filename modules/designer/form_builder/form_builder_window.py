"""
Form Builder Window (Enhanced - Phase 2)
=========================================
Main window for visual form builder.

Phase 2 enhancements:
- Preview Mode connected to FormRenderer
- Undo/Redo wired to QUndoStack
- Template browser for loading templates
- Canvas zoom controls
- Alignment tools toolbar
- Copy/Paste/Cut shortcuts
"""

import html
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QToolBar,
    QAction, QMenu, QMenuBar, QStatusBar, QLabel, QFileDialog,
    QMessageBox, QSplitter, QComboBox, QPushButton, QDialog,
    QDialogButtonBox, QFormLayout, QLineEdit, QScrollArea,
    QGridLayout, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
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


class PreviewDialog(QDialog):
    """Form preview dialog using FormRenderer."""

    def __init__(self, form_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setWindowTitle("معاينة النموذج")
        self.setModal(True)
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(10, 8, 10, 8)

        p = get_current_palette()
        info_label = QLabel("وضع المعاينة - هذا عرض تقريبي للنموذج")
        info_label.setStyleSheet(f"color: {p.get('text_muted', '#94a3b8')}; font-style: italic;")
        toolbar.addWidget(info_label)

        toolbar.addStretch()

        close_btn = QPushButton("إغلاق المعاينة")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {p.get('primary', '#3b82f6')};
                color: {p.get('text_on_primary', '#ffffff')};
                padding: 6px 16px;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background: {p.get('primary_dark', p.get('primary', '#3b82f6'))};
            }}
        """)
        toolbar.addWidget(close_btn)

        toolbar_widget = QWidget()
        toolbar_widget.setLayout(toolbar)
        toolbar_widget.setStyleSheet(f"background: {p.get('bg_card', '#1e293b')}; border-bottom: 1px solid {p.get('border', '#334155')};")
        layout.addWidget(toolbar_widget)

        # FormRenderer
        try:
            from modules.designer.form_renderer import FormRenderer
            self._renderer = FormRenderer(self)
            success = self._renderer.load_form_dict(form_data)
            if success:
                layout.addWidget(self._renderer, 1)
            else:
                error_label = QLabel("فشل في تحميل المعاينة")
                error_label.setAlignment(Qt.AlignCenter)
                error_label.setStyleSheet(f"color: {p.get('danger', '#ef4444')}; font-size: 14px; padding: 40px;")
                layout.addWidget(error_label, 1)
        except Exception as e:
            app_logger.error(f"Preview failed: {e}", exc_info=True)
            error_label = QLabel(f"خطأ في المعاينة:\n{html.escape(str(e))}")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setWordWrap(True)
            error_label.setStyleSheet(f"color: {p.get('danger', '#ef4444')}; font-size: 13px; padding: 40px;")
            layout.addWidget(error_label, 1)


class TemplateBrowserDialog(QDialog):
    """Template selection dialog."""

    template_selected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("مكتبة القوالب")
        self.setModal(True)
        self.setMinimumSize(700, 500)

        self._selected_template = None
        self._setup_ui()
        self._load_templates()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        p = get_current_palette()

        # Header
        header = QLabel("اختر قالباً لبدء التصميم")
        header.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {p.get('text_primary', '#e2e8f0')}; padding: 10px;")
        layout.addWidget(header)

        # Categories filter
        filter_layout = QHBoxLayout()
        filter_label = QLabel("التصنيف:")
        filter_layout.addWidget(filter_label)

        self._category_combo = QComboBox()
        self._category_combo.addItem("الكل", "all")
        self._category_combo.addItem("الموظفين", "employee")
        self._category_combo.addItem("البيانات الرئيسية", "master_data")
        self._category_combo.addItem("البحث", "search")
        self._category_combo.addItem("الإعدادات", "settings")
        self._category_combo.addItem("التقارير", "report")
        self._category_combo.addItem("فارغ", "blank")
        self._category_combo.currentIndexChanged.connect(self._filter_templates)
        filter_layout.addWidget(self._category_combo)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Templates grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        self._grid_widget = QWidget()
        self._grid_layout = QGridLayout(self._grid_widget)
        self._grid_layout.setSpacing(12)
        self._grid_layout.setContentsMargins(10, 10, 10, 10)

        scroll.setWidget(self._grid_widget)
        layout.addWidget(scroll, 1)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self._use_btn = QPushButton("استخدام القالب")
        self._use_btn.setEnabled(False)
        self._use_btn.clicked.connect(self._use_template)
        self._use_btn.setStyleSheet(f"""
            QPushButton {{
                background: {p.get('primary', '#3b82f6')};
                color: {p.get('text_on_primary', '#ffffff')};
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{ background: {p.get('primary_dark', p.get('primary', '#3b82f6'))}; }}
            QPushButton:disabled {{ background: {p.get('border', '#334155')}; color: {p.get('text_muted', '#94a3b8')}; }}
        """)
        btn_layout.addWidget(self._use_btn)

        layout.addLayout(btn_layout)

    def _load_templates(self) -> None:
        """Load templates from the template manager."""
        self._templates = []
        self._template_cards: List[QFrame] = []

        try:
            from modules.designer.templates import get_template_manager
            tm = get_template_manager()
            self._templates = tm.get_all_templates()
        except Exception as e:
            app_logger.error(f"Failed to load templates: {e}")

        self._display_templates(self._templates)

    def _display_templates(self, templates) -> None:
        """Display template cards in grid."""
        # Clear existing
        while self._grid_layout.count():
            child = self._grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self._template_cards.clear()
        p = get_current_palette()

        row, col = 0, 0
        for tmpl in templates:
            card = QFrame()
            card.setFixedSize(200, 150)
            card.setCursor(Qt.PointingHandCursor)
            card.setProperty("template_id", tmpl.template_id)
            card.setStyleSheet(f"""
                QFrame {{
                    background: {p.get('bg_card', '#1e293b')};
                    border: 2px solid {p.get('border', '#334155')};
                    border-radius: 8px;
                }}
                QFrame:hover {{
                    border-color: {p.get('primary', '#3b82f6')};
                }}
            """)

            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 12, 12, 12)

            icon = QLabel(tmpl.icon)
            icon.setStyleSheet("font-size: 28px;")
            icon.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(icon)

            name = QLabel(tmpl.name_ar)
            name.setStyleSheet(f"font-weight: bold; color: {p.get('text_primary', '#e2e8f0')}; font-size: 12px;")
            name.setAlignment(Qt.AlignCenter)
            name.setWordWrap(True)
            card_layout.addWidget(name)

            desc = QLabel(tmpl.description_ar)
            desc.setStyleSheet(f"color: {p.get('text_muted', '#94a3b8')}; font-size: 10px;")
            desc.setAlignment(Qt.AlignCenter)
            desc.setWordWrap(True)
            card_layout.addWidget(desc)

            cols = QLabel(f"{tmpl.columns} أعمدة")
            cols.setStyleSheet(f"color: {p.get('text_muted', '#94a3b8')}; font-size: 9px;")
            cols.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(cols)

            # Click handler
            card.mousePressEvent = lambda e, t=tmpl: self._select_card(t)
            card.mouseDoubleClickEvent = lambda e, t=tmpl: self._use_template_direct(t)

            self._grid_layout.addWidget(card, row, col)
            self._template_cards.append(card)

            col += 1
            if col >= 3:
                col = 0
                row += 1

    def _select_card(self, template) -> None:
        """Select a template card."""
        p = get_current_palette()
        self._selected_template = template

        # Reset all card styles
        for card in self._template_cards:
            card.setStyleSheet(f"""
                QFrame {{
                    background: {p.get('bg_card', '#1e293b')};
                    border: 2px solid {p.get('border', '#334155')};
                    border-radius: 8px;
                }}
                QFrame:hover {{
                    border-color: {p.get('primary', '#3b82f6')};
                }}
            """)

        # Highlight selected
        for card in self._template_cards:
            if card.property("template_id") == template.template_id:
                card.setStyleSheet(f"""
                    QFrame {{
                        background: {p.get('primary_light', p.get('bg_card', '#1e293b'))};
                        border: 2px solid {p.get('primary', '#3b82f6')};
                        border-radius: 8px;
                    }}
                """)

        self._use_btn.setEnabled(True)

    def _use_template(self) -> None:
        """Use the selected template."""
        if self._selected_template:
            self._use_template_direct(self._selected_template)

    def _use_template_direct(self, template) -> None:
        """Load and emit template data."""
        try:
            from modules.designer.templates import get_template_manager
            tm = get_template_manager()
            data = tm.get_template(template.template_id)
            if data:
                self.template_selected.emit(data)
                self.accept()
            else:
                QMessageBox.warning(self, "خطأ", "فشل في تحميل القالب")
        except Exception as e:
            app_logger.error(f"Failed to load template: {e}")
            QMessageBox.warning(self, "خطأ", f"خطأ:\n{html.escape(str(e))}")

    def _filter_templates(self) -> None:
        """Filter templates by category."""
        category = self._category_combo.currentData()

        if category == "all":
            self._display_templates(self._templates)
        else:
            filtered = [t for t in self._templates if t.category == category]
            self._display_templates(filtered)

    def get_selected_data(self) -> Optional[Dict]:
        """Get selected template data."""
        return self._selected_template


class FormBuilderWindow(QMainWindow):
    """
    Main form builder window (Enhanced - Phase 2).

    Features:
    - WYSIWYG form design
    - Preview mode via FormRenderer
    - Undo/Redo with QUndoStack
    - Template browser
    - Zoom controls
    - Multi-select and alignment tools
    - Copy/Paste/Cut
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

        app_logger.info("FormBuilderWindow initialized (Phase 2)")

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
                background: {p.get('bg_main', '#0f172a')};
            }}
            QToolBar {{
                background: {p.get('bg_card', '#1e293b')};
                border-bottom: 1px solid {p.get('border', '#334155')};
                padding: 4px;
            }}
            QMenuBar {{
                background: {p.get('bg_card', '#1e293b')};
                border-bottom: 1px solid {p.get('border', '#334155')};
            }}
        """)

    def _setup_menus(self) -> None:
        """Setup menu bar."""
        menubar = self.menuBar()

        # ===== File menu =====
        file_menu = menubar.addMenu("ملف")

        new_action = QAction("جديد", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self._new_form)
        file_menu.addAction(new_action)

        new_from_template = QAction("جديد من قالب...", self)
        new_from_template.triggered.connect(self._new_from_template)
        file_menu.addAction(new_from_template)

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

        # ===== Edit menu =====
        edit_menu = menubar.addMenu("تحرير")

        # Wire undo/redo to canvas undo stack
        undo_stack = self._canvas.get_undo_stack()

        self._undo_action = undo_stack.createUndoAction(self, "تراجع")
        self._undo_action.setShortcut(QKeySequence.Undo)
        edit_menu.addAction(self._undo_action)

        self._redo_action = undo_stack.createRedoAction(self, "إعادة")
        self._redo_action.setShortcut(QKeySequence.Redo)
        edit_menu.addAction(self._redo_action)

        edit_menu.addSeparator()

        cut_action = QAction("قص", self)
        cut_action.setShortcut(QKeySequence.Cut)
        cut_action.triggered.connect(self._canvas.cut_selected)
        edit_menu.addAction(cut_action)

        copy_action = QAction("نسخ", self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self._canvas.copy_selected)
        edit_menu.addAction(copy_action)

        paste_action = QAction("لصق", self)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(self._canvas.paste)
        edit_menu.addAction(paste_action)

        edit_menu.addSeparator()

        delete_action = QAction("حذف", self)
        delete_action.setShortcut(QKeySequence.Delete)
        delete_action.triggered.connect(self._delete_selected)
        edit_menu.addAction(delete_action)

        select_all_action = QAction("تحديد الكل", self)
        select_all_action.setShortcut(QKeySequence.SelectAll)
        select_all_action.triggered.connect(self._canvas.select_all)
        edit_menu.addAction(select_all_action)

        # ===== View menu =====
        view_menu = menubar.addMenu("عرض")

        grid_action = QAction("إظهار الشبكة", self)
        grid_action.setCheckable(True)
        grid_action.setChecked(True)
        grid_action.triggered.connect(self._canvas.set_grid_visible)
        view_menu.addAction(grid_action)

        view_menu.addSeparator()

        zoom_in_action = QAction("تكبير", self)
        zoom_in_action.setShortcut(QKeySequence.ZoomIn)
        zoom_in_action.triggered.connect(self._canvas.zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("تصغير", self)
        zoom_out_action.setShortcut(QKeySequence.ZoomOut)
        zoom_out_action.triggered.connect(self._canvas.zoom_out)
        view_menu.addAction(zoom_out_action)

        zoom_reset_action = QAction("حجم طبيعي", self)
        zoom_reset_action.setShortcut(QKeySequence("Ctrl+0"))
        zoom_reset_action.triggered.connect(self._canvas.zoom_reset)
        view_menu.addAction(zoom_reset_action)

        view_menu.addSeparator()

        preview_action = QAction("معاينة النموذج", self)
        preview_action.setShortcut(QKeySequence("Ctrl+P"))
        preview_action.triggered.connect(self._preview)
        view_menu.addAction(preview_action)

        # ===== Align menu =====
        align_menu = menubar.addMenu("محاذاة")

        align_left = QAction("محاذاة لليسار", self)
        align_left.triggered.connect(self._canvas.align_left)
        align_menu.addAction(align_left)

        align_right = QAction("محاذاة لليمين", self)
        align_right.triggered.connect(self._canvas.align_right)
        align_menu.addAction(align_right)

        align_top = QAction("محاذاة للأعلى", self)
        align_top.triggered.connect(self._canvas.align_top)
        align_menu.addAction(align_top)

        align_bottom = QAction("محاذاة للأسفل", self)
        align_bottom.triggered.connect(self._canvas.align_bottom)
        align_menu.addAction(align_bottom)

        align_menu.addSeparator()

        dist_h = QAction("توزيع أفقي", self)
        dist_h.triggered.connect(self._canvas.distribute_horizontal)
        align_menu.addAction(dist_h)

        dist_v = QAction("توزيع رأسي", self)
        dist_v.triggered.connect(self._canvas.distribute_vertical)
        align_menu.addAction(dist_v)

        # ===== Insert menu =====
        insert_menu = menubar.addMenu("إدراج")

        for widget_type in WidgetType:
            action = QAction(widget_type.value, self)
            action.triggered.connect(
                lambda checked, t=widget_type: self._insert_widget(t)
            )
            insert_menu.addAction(action)

        # ===== Help menu =====
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

        p = get_current_palette()
        btn_style = f"""
            QPushButton {{
                padding: 4px 10px;
                border: 1px solid {p.get('border', '#334155')};
                border-radius: 4px;
                background: {p.get('bg_card', '#1e293b')};
            }}
            QPushButton:hover {{
                background: {p.get('bg_hover', '#334155')};
                border-color: {p.get('primary', '#3b82f6')};
            }}
        """

        # File operations
        new_btn = QPushButton("جديد")
        new_btn.setStyleSheet(btn_style)
        new_btn.clicked.connect(self._new_form)
        toolbar.addWidget(new_btn)

        template_btn = QPushButton("قوالب")
        template_btn.setStyleSheet(btn_style)
        template_btn.clicked.connect(self._new_from_template)
        toolbar.addWidget(template_btn)

        open_btn = QPushButton("فتح")
        open_btn.setStyleSheet(btn_style)
        open_btn.clicked.connect(self._open_file)
        toolbar.addWidget(open_btn)

        save_btn = QPushButton("حفظ")
        save_btn.setStyleSheet(btn_style)
        save_btn.clicked.connect(self._save_file)
        toolbar.addWidget(save_btn)

        toolbar.addSeparator()

        # Quick add widgets
        label_btn = QPushButton("Aa نص")
        label_btn.setStyleSheet(btn_style)
        label_btn.clicked.connect(lambda: self._insert_widget(WidgetType.LABEL))
        toolbar.addWidget(label_btn)

        input_btn = QPushButton("[__] حقل")
        input_btn.setStyleSheet(btn_style)
        input_btn.clicked.connect(lambda: self._insert_widget(WidgetType.TEXT_INPUT))
        toolbar.addWidget(input_btn)

        combo_btn = QPushButton("[v] قائمة")
        combo_btn.setStyleSheet(btn_style)
        combo_btn.clicked.connect(lambda: self._insert_widget(WidgetType.COMBO_BOX))
        toolbar.addWidget(combo_btn)

        check_btn = QPushButton("* اختيار")
        check_btn.setStyleSheet(btn_style)
        check_btn.clicked.connect(lambda: self._insert_widget(WidgetType.CHECK_BOX))
        toolbar.addWidget(check_btn)

        btn_btn = QPushButton("[OK] زر")
        btn_btn.setStyleSheet(btn_style)
        btn_btn.clicked.connect(lambda: self._insert_widget(WidgetType.BUTTON))
        toolbar.addWidget(btn_btn)

        toolbar.addSeparator()

        # Zoom controls
        zoom_out_btn = QPushButton("-")
        zoom_out_btn.setFixedWidth(30)
        zoom_out_btn.setStyleSheet(btn_style)
        zoom_out_btn.clicked.connect(self._canvas.zoom_out)
        toolbar.addWidget(zoom_out_btn)

        self._zoom_label = QLabel("100%")
        self._zoom_label.setStyleSheet(f"padding: 0 6px; color: {p.get('text_primary', '#e2e8f0')};")
        toolbar.addWidget(self._zoom_label)

        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setFixedWidth(30)
        zoom_in_btn.setStyleSheet(btn_style)
        zoom_in_btn.clicked.connect(self._canvas.zoom_in)
        toolbar.addWidget(zoom_in_btn)

        toolbar.addSeparator()

        # Preview
        preview_btn = QPushButton("معاينة")
        preview_btn.setStyleSheet(f"""
            QPushButton {{
                padding: 4px 14px;
                border: none;
                border-radius: 4px;
                background: {p.get('primary', '#3b82f6')};
                color: {p.get('text_on_primary', '#ffffff')};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {p.get('primary_dark', p.get('primary', '#3b82f6'))};
            }}
        """)
        preview_btn.clicked.connect(self._preview)
        toolbar.addWidget(preview_btn)

    def _setup_statusbar(self) -> None:
        """Setup status bar."""
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)

        self._sel_label = QLabel("لا يوجد تحديد")
        self._statusbar.addWidget(self._sel_label)

        self._zoom_status = QLabel("100%")
        self._statusbar.addPermanentWidget(self._zoom_status)

    def _connect_signals(self) -> None:
        """Connect signals."""
        self._canvas.widget_selected.connect(self._on_widget_selected)
        self._canvas.widget_changed.connect(self._on_widget_changed)
        self._canvas.canvas_changed.connect(self._on_canvas_changed)

        self._properties.property_changed.connect(self._on_property_changed)

        # Undo stack clean state
        self._canvas.get_undo_stack().cleanChanged.connect(self._on_undo_clean_changed)

    # -----------------------------------------------------------------------
    # File operations
    # -----------------------------------------------------------------------

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

    def _new_from_template(self) -> None:
        """Create new form from template."""
        if self._modified:
            reply = QMessageBox.question(
                self,
                "حفظ التغييرات",
                "هل تريد حفظ التغييرات أولاً؟",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            if reply == QMessageBox.Save:
                if not self._save_file():
                    return
            elif reply == QMessageBox.Cancel:
                return

        dialog = TemplateBrowserDialog(self)
        dialog.template_selected.connect(self._on_template_selected)
        dialog.exec_()

    def _on_template_selected(self, form_data: Dict) -> None:
        """Handle template selection."""
        self._canvas.clear()
        self._file_path = None

        # Convert template sections/fields to canvas widgets
        try:
            self._load_template_to_canvas(form_data)
            self._modified = True
            self._update_title()
            self._statusbar.showMessage("تم تحميل القالب", 3000)
        except Exception as e:
            app_logger.error(f"Failed to load template to canvas: {e}")
            QMessageBox.warning(self, "خطأ", f"فشل في تحميل القالب:\n{html.escape(str(e))}")

    def _load_template_to_canvas(self, form_data: Dict) -> None:
        """Convert template .iform data to canvas widgets."""
        y_offset = 30
        x_offset = 30

        for section in form_data.get("sections", []):
            title = section.get("title_ar", section.get("title_en", ""))
            if title:
                # Add section header as label
                self._canvas.add_widget(
                    WidgetType.LABEL,
                    x=x_offset, y=y_offset,
                    width=300, height=30,
                    label=title
                )
                y_offset += 40

            section_cols = section.get("columns", form_data.get("settings", {}).get("columns", 2))

            for field_def in section.get("fields", []):
                widget_type_str = field_def.get("widget_type", "text_input")
                try:
                    wtype = WidgetType(widget_type_str)
                except ValueError:
                    wtype = WidgetType.TEXT_INPUT

                layout_info = field_def.get("layout", {})
                row = layout_info.get("row", 0)
                col = layout_info.get("col", 0)

                label = field_def.get("label_ar", field_def.get("label_en", ""))

                # Calculate position based on grid
                calc_x = x_offset + col * 220
                calc_y = y_offset + row * 50

                w = self._canvas.add_widget(
                    wtype,
                    x=calc_x, y=calc_y,
                    label=label
                )

                # Set data binding if present
                binding = field_def.get("data_binding")
                if binding:
                    table = binding.get("table", "")
                    column = binding.get("column", "")
                    if table and column:
                        w.data_binding = f"{table}.{column}"

            y_offset += 60  # Space between sections

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
                f"فشل فتح الملف:\n{html.escape(str(e))}"
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
            self._canvas.get_undo_stack().setClean()
            self._update_title()

            self._statusbar.showMessage("تم الحفظ", 3000)
            app_logger.info(f"Saved form: {file_path}")
            return True

        except Exception as e:
            QMessageBox.critical(
                self,
                "خطأ",
                f"فشل حفظ الملف:\n{html.escape(str(e))}"
            )
            app_logger.error(f"Failed to save form: {e}")
            return False

    # -----------------------------------------------------------------------
    # Widget operations
    # -----------------------------------------------------------------------

    def _insert_widget(self, widget_type: WidgetType) -> None:
        """Insert new widget."""
        self._canvas.add_widget(widget_type)

    def _delete_selected(self) -> None:
        """Delete selected widget(s)."""
        self._canvas.delete_selected()

    # -----------------------------------------------------------------------
    # Preview
    # -----------------------------------------------------------------------

    def _preview(self) -> None:
        """Preview form using FormRenderer."""
        form_data = self._build_preview_form_data()

        if not form_data.get("sections"):
            QMessageBox.information(
                self,
                "معاينة",
                "لا يوجد عناصر في النموذج للمعاينة.\nأضف عناصر أولاً."
            )
            return

        dialog = PreviewDialog(form_data, self)
        dialog.exec_()

    def _build_preview_form_data(self) -> Dict[str, Any]:
        """Convert canvas data to FormRenderer-compatible .iform format."""
        canvas_data = self._canvas.to_dict()
        widgets = canvas_data.get("widgets", [])

        if not widgets:
            return {
                "version": "2.0",
                "form_id": "preview",
                "form_name_ar": "معاينة",
                "settings": {},
                "sections": [],
                "actions": [],
                "rules": [],
            }

        # Group widgets into rows for smart_grid layout
        # Sort by y position, then x position
        sorted_widgets = sorted(widgets, key=lambda w: (w.get("y", 0), w.get("x", 0)))

        fields = []
        row = 0
        col = 0
        last_y = -1
        row_threshold = 30  # Widgets within this y-range are on same row

        for w_data in sorted_widgets:
            widget_type = w_data.get("type", "text_input")

            # Skip separators and group_box in preview fields
            if widget_type in ("separator", "group_box", "image"):
                continue

            current_y = w_data.get("y", 0)

            if last_y >= 0 and abs(current_y - last_y) > row_threshold:
                row += 1
                col = 0
            elif last_y >= 0:
                col += 1

            last_y = current_y

            label_text = w_data.get("label", "")
            field_id = w_data.get("id", f"field_{row}_{col}")

            field_def = {
                "id": field_id,
                "widget_type": widget_type,
                "label_ar": label_text,
                "label_en": label_text,
                "layout": {
                    "row": row,
                    "col": col,
                    "colspan": 1,
                    "rowspan": 1,
                },
                "properties": {
                    "readonly": False,
                    "enabled": True,
                    "visible": True,
                },
                "validation": [],
            }

            # Add placeholder
            placeholder = w_data.get("placeholder", "")
            if placeholder:
                field_def["placeholder_ar"] = placeholder
                field_def["placeholder_en"] = placeholder

            # Add data binding
            binding = w_data.get("data_binding")
            if binding:
                parts = binding.split(".", 1) if isinstance(binding, str) else []
                if len(parts) == 2:
                    field_def["data_binding"] = {
                        "table": parts[0],
                        "column": parts[1],
                        "data_type": "string",
                    }

            # Add validation
            for v in w_data.get("validation", []):
                field_def["validation"].append({
                    "rule": v.get("type", "required"),
                    "value": v.get("value"),
                    "message_ar": v.get("message", ""),
                })

            fields.append(field_def)

        form_data = {
            "version": "2.0",
            "form_id": "preview",
            "form_name_ar": "معاينة النموذج",
            "form_name_en": "Form Preview",
            "settings": {
                "direction": "rtl",
                "layout_mode": "smart_grid",
                "columns": 2,
                "column_gap": 20,
                "row_gap": 15,
                "margins": {"top": 20, "right": 20, "bottom": 20, "left": 20},
                "min_width": 600,
                "max_width": 1200,
                "scrollable": True,
                "show_required_indicator": True,
                "save_button_position": "bottom_left",
            },
            "sections": [
                {
                    "id": "main",
                    "title_ar": "النموذج",
                    "title_en": "Form",
                    "collapsed": False,
                    "collapsible": False,
                    "visible": True,
                    "fields": fields,
                }
            ],
            "actions": [
                {
                    "id": "save",
                    "type": "primary",
                    "label_ar": "حفظ",
                    "label_en": "Save",
                    "action": "save",
                    "position": "footer_left",
                    "width": 120,
                },
                {
                    "id": "cancel",
                    "type": "danger",
                    "label_ar": "إلغاء",
                    "label_en": "Cancel",
                    "action": "cancel",
                    "position": "footer_left",
                    "width": 100,
                },
            ],
            "rules": [],
            "events": {},
        }

        return form_data

    # -----------------------------------------------------------------------
    # Signal handlers
    # -----------------------------------------------------------------------

    def _on_widget_selected(self, widget) -> None:
        """Handle widget selection."""
        self._properties.set_widget(widget)

        if widget:
            selected = self._canvas.get_selected_widgets()
            if len(selected) > 1:
                self._sel_label.setText(f"محدد: {len(selected)} عناصر")
            else:
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

        # Update zoom label
        zoom = self._canvas.zoom_level
        zoom_text = f"{zoom:.0%}"
        self._zoom_label.setText(zoom_text)
        self._zoom_status.setText(zoom_text)

    def _on_property_changed(self, widget) -> None:
        """Handle property change."""
        self._canvas.update_widget(widget)
        self._modified = True
        self._update_title()

    def _on_undo_clean_changed(self, clean: bool) -> None:
        """Handle undo stack clean state."""
        if clean:
            self._modified = False
        else:
            self._modified = True
        self._update_title()

    # -----------------------------------------------------------------------
    # UI helpers
    # -----------------------------------------------------------------------

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
            """<h3>منشئ النماذج - INTEGRA v2.0</h3>
            <p>الإصدار 2.0.0 (Phase 2)</p>
            <p>أداة تصميم نماذج بواجهة سحب وإفلات</p>
            <p>المميزات:</p>
            <ul>
                <li>سحب وإفلات الأدوات</li>
                <li>معاينة النموذج عبر FormRenderer</li>
                <li>تراجع / إعادة (Undo/Redo)</li>
                <li>مكتبة قوالب جاهزة</li>
                <li>تحديد متعدد ومحاذاة</li>
                <li>تكبير / تصغير</li>
                <li>نسخ / قص / لصق</li>
                <li>ربط البيانات بقاعدة البيانات</li>
                <li>التحقق من صحة البيانات</li>
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
