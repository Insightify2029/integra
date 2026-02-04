"""
Report Designer Window
======================
Main window for visual report designer.

Features:
- Full WYSIWYG editing
- File operations (new, open, save)
- Undo/Redo
- Zoom controls
- Preview and export
- Template library
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QToolBar,
    QAction, QActionGroup, QMenu, QMenuBar, QStatusBar, QLabel,
    QFileDialog, QMessageBox, QSplitter, QComboBox, QSpinBox,
    QDockWidget, QDialog, QDialogButtonBox, QFormLayout, QLineEdit,
    QPushButton
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QKeySequence, QCloseEvent

from core.logging import app_logger

from .design_canvas import DesignCanvas, ElementType, BandType
from .element_palette import ElementPalette
from .property_panel import PropertyPanel


class NewReportDialog(QDialog):
    """Dialog for creating new report."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("تقرير جديد")
        self.setModal(True)
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Form
        form = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("اسم التقرير")
        form.addRow("اسم التقرير:", self.name_edit)

        self.page_size = QComboBox()
        self.page_size.addItems(["A4", "A3", "A5", "Letter", "Legal"])
        form.addRow("حجم الورق:", self.page_size)

        self.orientation = QComboBox()
        self.orientation.addItem("عمودي", "portrait")
        self.orientation.addItem("أفقي", "landscape")
        form.addRow("الاتجاه:", self.orientation)

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_settings(self) -> Dict[str, Any]:
        """Get dialog settings."""
        return {
            "name": self.name_edit.text(),
            "page_size": self.page_size.currentText(),
            "orientation": self.orientation.currentData()
        }


class ReportDesignerWindow(QMainWindow):
    """
    Main report designer window.

    Provides full WYSIWYG report editing capabilities.
    """

    def __init__(self, template_path: str = None, parent=None):
        super().__init__(parent)

        self._template_path = template_path
        self._file_path: Optional[str] = None
        self._modified = False

        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_statusbar()
        self._connect_signals()

        # Load template if provided
        if template_path:
            self._load_file(template_path)
        else:
            self._new_report()

        app_logger.info("ReportDesignerWindow initialized")

    def _setup_ui(self) -> None:
        """Setup window UI."""
        self.setWindowTitle("مصمم التقارير - INTEGRA")
        self.setMinimumSize(1200, 800)

        # Central widget with splitter
        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Main splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left panel - Element Palette
        self._palette = ElementPalette()
        splitter.addWidget(self._palette)

        # Center - Design Canvas
        self._canvas = DesignCanvas()
        splitter.addWidget(self._canvas)

        # Right panel - Properties
        self._properties = PropertyPanel()
        splitter.addWidget(self._properties)

        # Set splitter sizes
        splitter.setSizes([180, 700, 280])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)

        layout.addWidget(splitter)
        self.setCentralWidget(central)

        # Window style
        self.setStyleSheet("""
            QMainWindow {
                background: #f3f4f6;
            }
            QToolBar {
                background: #ffffff;
                border-bottom: 1px solid #e5e7eb;
                padding: 4px;
                spacing: 4px;
            }
            QToolBar QToolButton {
                padding: 6px 10px;
                border-radius: 4px;
            }
            QToolBar QToolButton:hover {
                background: #f3f4f6;
            }
            QToolBar QToolButton:pressed {
                background: #e5e7eb;
            }
            QMenuBar {
                background: #ffffff;
                border-bottom: 1px solid #e5e7eb;
                padding: 4px;
            }
            QMenuBar::item {
                padding: 6px 12px;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background: #f3f4f6;
            }
            QMenu {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 24px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: #f3f4f6;
            }
            QStatusBar {
                background: #ffffff;
                border-top: 1px solid #e5e7eb;
            }
        """)

    def _setup_menus(self) -> None:
        """Setup menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("ملف")

        new_action = QAction("جديد", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self._new_report)
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
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self._save_file_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        # Export submenu
        export_menu = file_menu.addMenu("تصدير")

        export_pdf = QAction("PDF", self)
        export_pdf.triggered.connect(lambda: self._export("pdf"))
        export_menu.addAction(export_pdf)

        export_excel = QAction("Excel", self)
        export_excel.triggered.connect(lambda: self._export("xlsx"))
        export_menu.addAction(export_excel)

        export_word = QAction("Word", self)
        export_word.triggered.connect(lambda: self._export("docx"))
        export_menu.addAction(export_word)

        export_html = QAction("HTML", self)
        export_html.triggered.connect(lambda: self._export("html"))
        export_menu.addAction(export_html)

        file_menu.addSeparator()

        close_action = QAction("إغلاق", self)
        close_action.setShortcut(QKeySequence.Close)
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)

        # Edit menu
        edit_menu = menubar.addMenu("تحرير")

        undo_action = QAction("تراجع", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self._canvas.get_undo_stack().undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("إعادة", self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.triggered.connect(self._canvas.get_undo_stack().redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        cut_action = QAction("قص", self)
        cut_action.setShortcut(QKeySequence.Cut)
        edit_menu.addAction(cut_action)

        copy_action = QAction("نسخ", self)
        copy_action.setShortcut(QKeySequence.Copy)
        edit_menu.addAction(copy_action)

        paste_action = QAction("لصق", self)
        paste_action.setShortcut(QKeySequence.Paste)
        edit_menu.addAction(paste_action)

        edit_menu.addSeparator()

        delete_action = QAction("حذف", self)
        delete_action.setShortcut(QKeySequence.Delete)
        delete_action.triggered.connect(self._delete_selected)
        edit_menu.addAction(delete_action)

        select_all_action = QAction("تحديد الكل", self)
        select_all_action.setShortcut(QKeySequence.SelectAll)
        edit_menu.addAction(select_all_action)

        # View menu
        view_menu = menubar.addMenu("عرض")

        grid_action = QAction("إظهار الشبكة", self)
        grid_action.setCheckable(True)
        grid_action.setChecked(True)
        grid_action.triggered.connect(self._canvas.set_grid_visible)
        view_menu.addAction(grid_action)

        view_menu.addSeparator()

        zoom_in = QAction("تكبير", self)
        zoom_in.setShortcut(QKeySequence.ZoomIn)
        zoom_in.triggered.connect(lambda: self._zoom(1.1))
        view_menu.addAction(zoom_in)

        zoom_out = QAction("تصغير", self)
        zoom_out.setShortcut(QKeySequence.ZoomOut)
        zoom_out.triggered.connect(lambda: self._zoom(0.9))
        view_menu.addAction(zoom_out)

        zoom_fit = QAction("ملائمة", self)
        zoom_fit.triggered.connect(self._zoom_fit)
        view_menu.addAction(zoom_fit)

        zoom_100 = QAction("100%", self)
        zoom_100.triggered.connect(lambda: self._zoom_to(1.0))
        view_menu.addAction(zoom_100)

        # Insert menu
        insert_menu = menubar.addMenu("إدراج")

        for elem_type in ElementType:
            action = QAction(elem_type.value, self)
            action.triggered.connect(
                lambda checked, t=elem_type: self._insert_element(t)
            )
            insert_menu.addAction(action)

        # Format menu
        format_menu = menubar.addMenu("تنسيق")

        align_menu = format_menu.addMenu("محاذاة")
        align_left = QAction("يسار", self)
        align_menu.addAction(align_left)
        align_center = QAction("وسط", self)
        align_menu.addAction(align_center)
        align_right = QAction("يمين", self)
        align_menu.addAction(align_right)

        # Help menu
        help_menu = menubar.addMenu("مساعدة")

        about_action = QAction("حول مصمم التقارير", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_toolbar(self) -> None:
        """Setup toolbar."""
        toolbar = QToolBar("الأدوات الرئيسية")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)

        # File operations
        new_btn = QPushButton("جديد")
        new_btn.clicked.connect(self._new_report)
        toolbar.addWidget(new_btn)

        open_btn = QPushButton("فتح")
        open_btn.clicked.connect(self._open_file)
        toolbar.addWidget(open_btn)

        save_btn = QPushButton("حفظ")
        save_btn.clicked.connect(self._save_file)
        toolbar.addWidget(save_btn)

        toolbar.addSeparator()

        # Undo/Redo
        undo_btn = QPushButton("↩ تراجع")
        undo_btn.clicked.connect(self._canvas.get_undo_stack().undo)
        toolbar.addWidget(undo_btn)

        redo_btn = QPushButton("↪ إعادة")
        redo_btn.clicked.connect(self._canvas.get_undo_stack().redo)
        toolbar.addWidget(redo_btn)

        toolbar.addSeparator()

        # Quick add elements
        text_btn = QPushButton("📝 نص")
        text_btn.clicked.connect(lambda: self._insert_element(ElementType.TEXT))
        toolbar.addWidget(text_btn)

        field_btn = QPushButton("[F] حقل")
        field_btn.clicked.connect(lambda: self._insert_element(ElementType.FIELD))
        toolbar.addWidget(field_btn)

        table_btn = QPushButton("⊞ جدول")
        table_btn.clicked.connect(lambda: self._insert_element(ElementType.TABLE))
        toolbar.addWidget(table_btn)

        image_btn = QPushButton("🖼 صورة")
        image_btn.clicked.connect(lambda: self._insert_element(ElementType.IMAGE))
        toolbar.addWidget(image_btn)

        toolbar.addSeparator()

        # Zoom
        toolbar.addWidget(QLabel(" تكبير: "))

        self._zoom_combo = QComboBox()
        self._zoom_combo.addItems(["50%", "75%", "100%", "125%", "150%", "200%"])
        self._zoom_combo.setCurrentText("100%")
        self._zoom_combo.currentTextChanged.connect(self._on_zoom_changed)
        self._zoom_combo.setMinimumWidth(80)
        toolbar.addWidget(self._zoom_combo)

        toolbar.addSeparator()

        # Preview & Export
        preview_btn = QPushButton("معاينة")
        preview_btn.clicked.connect(self._preview)
        toolbar.addWidget(preview_btn)

        export_btn = QPushButton("تصدير PDF")
        export_btn.clicked.connect(lambda: self._export("pdf"))
        toolbar.addWidget(export_btn)

    def _setup_statusbar(self) -> None:
        """Setup status bar."""
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)

        # Position label
        self._pos_label = QLabel("X: 0, Y: 0")
        self._statusbar.addWidget(self._pos_label)

        # Spacer
        spacer = QWidget()
        spacer.setFixedWidth(20)
        self._statusbar.addWidget(spacer)

        # Selection label
        self._sel_label = QLabel("لا يوجد تحديد")
        self._statusbar.addWidget(self._sel_label)

        # Right side - zoom
        self._statusbar.addPermanentWidget(QLabel(""))

    def _connect_signals(self) -> None:
        """Connect signals."""
        # Canvas signals
        self._canvas.element_selected.connect(self._on_element_selected)
        self._canvas.element_changed.connect(self._on_element_changed)
        self._canvas.canvas_changed.connect(self._on_canvas_changed)

        # Properties signals
        self._properties.property_changed.connect(self._on_property_changed)

    def _new_report(self) -> None:
        """Create new report."""
        if self._modified:
            reply = QMessageBox.question(
                self,
                "حفظ التغييرات",
                "هل تريد حفظ التغييرات قبل إنشاء تقرير جديد؟",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )

            if reply == QMessageBox.Save:
                if not self._save_file():
                    return
            elif reply == QMessageBox.Cancel:
                return

        # Show new report dialog
        dialog = NewReportDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            settings = dialog.get_settings()

            self._canvas.clear()
            self._file_path = None
            self._modified = False

            # Set page size
            page_sizes = {
                "A4": (595, 842),
                "A3": (842, 1191),
                "A5": (420, 595),
                "Letter": (612, 792),
                "Legal": (612, 1008)
            }

            width, height = page_sizes.get(settings["page_size"], (595, 842))

            if settings["orientation"] == "landscape":
                width, height = height, width

            self._canvas.set_page_size(width, height)

            self._update_title()

    def _open_file(self) -> None:
        """Open report file."""
        if self._modified:
            reply = QMessageBox.question(
                self,
                "حفظ التغييرات",
                "هل تريد حفظ التغييرات قبل فتح ملف آخر؟",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )

            if reply == QMessageBox.Save:
                if not self._save_file():
                    return
            elif reply == QMessageBox.Cancel:
                return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "فتح تقرير",
            "",
            "ملفات التقارير (*.irpt);;كل الملفات (*.*)"
        )

        if file_path:
            self._load_file(file_path)

    def _load_file(self, file_path: str) -> bool:
        """Load report from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self._canvas.from_dict(data)
            self._file_path = file_path
            self._modified = False
            self._update_title()

            app_logger.info(f"Loaded report: {file_path}")
            return True

        except Exception as e:
            QMessageBox.critical(
                self,
                "خطأ",
                f"فشل فتح الملف:\n{str(e)}"
            )
            app_logger.error(f"Failed to load report: {e}")
            return False

    def _save_file(self) -> bool:
        """Save report to file."""
        if not self._file_path:
            return self._save_file_as()

        return self._save_to_path(self._file_path)

    def _save_file_as(self) -> bool:
        """Save report to new file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "حفظ التقرير",
            "",
            "ملفات التقارير (*.irpt)"
        )

        if file_path:
            if not file_path.endswith('.irpt'):
                file_path += '.irpt'
            return self._save_to_path(file_path)

        return False

    def _save_to_path(self, file_path: str) -> bool:
        """Save report to specific path."""
        try:
            data = self._canvas.to_dict()

            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self._file_path = file_path
            self._modified = False
            self._update_title()

            self._statusbar.showMessage("تم الحفظ", 3000)
            app_logger.info(f"Saved report: {file_path}")
            return True

        except Exception as e:
            QMessageBox.critical(
                self,
                "خطأ",
                f"فشل حفظ الملف:\n{str(e)}"
            )
            app_logger.error(f"Failed to save report: {e}")
            return False

    def _export(self, format: str) -> None:
        """Export report to format."""
        ext_map = {
            "pdf": "PDF (*.pdf)",
            "xlsx": "Excel (*.xlsx)",
            "docx": "Word (*.docx)",
            "html": "HTML (*.html)"
        }

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "تصدير التقرير",
            "",
            ext_map.get(format, "All Files (*.*)")
        )

        if not file_path:
            return

        if not file_path.endswith(f'.{format}'):
            file_path += f'.{format}'

        try:
            from core.reporting import generate_report, ReportFormat, ReportConfig

            # Get canvas data
            data = self._canvas.to_dict()
            elements = data.get("elements", [])

            # For now, export a simple version
            # TODO: Full rendering from canvas elements

            config = ReportConfig(
                title="تقرير",
                rtl=True
            )

            format_map = {
                "pdf": ReportFormat.PDF,
                "xlsx": ReportFormat.EXCEL,
                "docx": ReportFormat.WORD,
                "html": ReportFormat.HTML
            }

            config.output_format = format_map.get(format, ReportFormat.PDF)

            # Generate with sample data for now
            sample_data = [{"العنصر": "اختبار", "القيمة": "123"}]

            if generate_report(sample_data, output_path=file_path, config=config):
                self._statusbar.showMessage(f"تم التصدير إلى {file_path}", 5000)
                QMessageBox.information(
                    self,
                    "تم التصدير",
                    f"تم تصدير التقرير بنجاح:\n{file_path}"
                )
            else:
                QMessageBox.warning(self, "تحذير", "فشل التصدير")

        except Exception as e:
            QMessageBox.critical(
                self,
                "خطأ",
                f"فشل التصدير:\n{str(e)}"
            )
            app_logger.error(f"Export failed: {e}")

    def _preview(self) -> None:
        """Preview report."""
        # TODO: Implement preview window
        QMessageBox.information(
            self,
            "معاينة",
            "ميزة المعاينة قيد التطوير"
        )

    def _insert_element(self, element_type: ElementType) -> None:
        """Insert new element."""
        self._canvas.add_element(element_type)

    def _delete_selected(self) -> None:
        """Delete selected elements."""
        for element in self._canvas.get_selected_elements():
            self._canvas.remove_element(element.id)

    def _zoom(self, factor: float) -> None:
        """Zoom by factor."""
        self._canvas.scale(factor, factor)
        self._update_zoom_combo()

    def _zoom_to(self, level: float) -> None:
        """Zoom to specific level."""
        self._canvas.resetTransform()
        self._canvas.scale(level, level)
        self._update_zoom_combo()

    def _zoom_fit(self) -> None:
        """Fit canvas in view."""
        self._canvas.fitInView(
            self._canvas.sceneRect(),
            Qt.KeepAspectRatio
        )
        self._update_zoom_combo()

    def _on_zoom_changed(self, text: str) -> None:
        """Handle zoom combo change."""
        try:
            level = int(text.replace("%", "")) / 100
            self._zoom_to(level)
        except ValueError:
            pass

    def _update_zoom_combo(self) -> None:
        """Update zoom combo to current level."""
        transform = self._canvas.transform()
        zoom = transform.m11() * 100
        self._zoom_combo.blockSignals(True)
        self._zoom_combo.setCurrentText(f"{int(zoom)}%")
        self._zoom_combo.blockSignals(False)

    def _on_element_selected(self, element) -> None:
        """Handle element selection."""
        self._properties.set_element(element)

        if element:
            self._sel_label.setText(f"محدد: {element.element_type.value}")
        else:
            self._sel_label.setText("لا يوجد تحديد")

    def _on_element_changed(self, element) -> None:
        """Handle element change."""
        self._properties.set_element(element)
        self._modified = True
        self._update_title()

    def _on_canvas_changed(self) -> None:
        """Handle canvas change."""
        self._modified = True
        self._update_title()

    def _on_property_changed(self, element) -> None:
        """Handle property change from panel."""
        self._canvas.update_element(element)
        self._modified = True
        self._update_title()

    def _update_title(self) -> None:
        """Update window title."""
        title = "مصمم التقارير - INTEGRA"

        if self._file_path:
            title = f"{Path(self._file_path).name} - {title}"

        if self._modified:
            title = f"* {title}"

        self.setWindowTitle(title)

    def _show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "حول مصمم التقارير",
            """<h3>مصمم التقارير - INTEGRA</h3>
            <p>الإصدار 1.0.0</p>
            <p>أداة تصميم تقارير احترافية بواجهة WYSIWYG</p>
            <p>المميزات:</p>
            <ul>
                <li>سحب وإفلات العناصر</li>
                <li>معاينة مباشرة</li>
                <li>تصدير PDF, Excel, Word</li>
                <li>دعم RTL والعربية</li>
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
