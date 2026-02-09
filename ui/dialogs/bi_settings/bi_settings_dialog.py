# -*- coding: utf-8 -*-
"""
BI Settings Dialog
==================
Power BI Desktop integration settings and management UI.

This dialog provides:
- Connection configuration display
- Data export controls
- Template management
- View status monitoring

Author: Mohamed
Version: 1.0.0
Date: February 2026
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QGroupBox, QFormLayout, QLineEdit,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QCheckBox, QTimeEdit, QComboBox, QProgressBar,
    QHeaderView, QFileDialog, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt, QTime, QThread, pyqtSignal
from core.themes import (
    get_stylesheet, get_current_palette,
    get_font, FONT_SIZE_BODY, FONT_SIZE_TITLE, FONT_WEIGHT_BOLD,
)
from core.logging import app_logger


class ExportWorker(QThread):
    """Background worker for data export."""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, export_format: str = "csv", views: list = None):
        super().__init__()
        self.export_format = export_format
        self.views = views

    def run(self):
        try:
            from core.bi import get_bi_exporter

            self.progress.emit(10, "جاري التحضير...")
            exporter = get_bi_exporter()

            if self.export_format == "excel":
                self.progress.emit(30, "جاري التصدير إلى Excel...")
                if self.views:
                    result = exporter.export_to_excel(self.views)
                else:
                    result = exporter.export_all_views_excel()

                if result.success:
                    self.progress.emit(100, "اكتمل التصدير!")
                    self.finished.emit(True, result.file_path)
                else:
                    self.finished.emit(False, result.error)
            else:
                self.progress.emit(30, "جاري التصدير إلى CSV...")
                if self.views:
                    results = [exporter.export_to_csv(v) for v in self.views]
                else:
                    results = exporter.export_all_views_csv()

                success_count = sum(1 for r in results if r.success)
                self.progress.emit(100, "اكتمل التصدير!")
                self.finished.emit(True, f"تم تصدير {success_count} ملفات")

        except Exception as e:
            self.finished.emit(False, str(e))


class ViewsWorker(QThread):
    """Background worker for creating/refreshing views."""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, int, int)

    def __init__(self, action: str = "create"):
        super().__init__()
        self.action = action

    def run(self):
        try:
            from core.bi import get_bi_views_manager

            self.progress.emit(10, "جاري الاتصال...")
            manager = get_bi_views_manager()

            if self.action == "create":
                self.progress.emit(30, "جاري إنشاء Views...")
                success, failed = manager.create_all_views()
            else:
                self.progress.emit(30, "جاري التحديث...")
                success, failed = manager.refresh_all_views()

            self.progress.emit(100, "اكتمل!")
            self.finished.emit(True, success, failed)

        except Exception as e:
            app_logger.error(f"Views operation failed: {e}")
            self.finished.emit(False, 0, 0)


class BISettingsDialog(QDialog):
    """
    Power BI Settings and Management Dialog.

    Provides comprehensive UI for managing Power BI integration,
    including connection info, data export, and template management.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 إعدادات Power BI")
        self.setMinimumSize(700, 600)
        self.setStyleSheet(get_stylesheet())

        self._worker = None
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header = QLabel("تكامل Power BI Desktop")
        header.setFont(get_font(FONT_SIZE_TITLE - 2, FONT_WEIGHT_BOLD))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_connection_tab(), "🔌 الاتصال")
        self.tabs.addTab(self._create_export_tab(), "📤 التصدير")
        self.tabs.addTab(self._create_views_tab(), "👁️ Views")
        self.tabs.addTab(self._create_templates_tab(), "📋 القوالب")
        self.tabs.addTab(self._create_guide_tab(), "📖 الدليل")
        layout.addWidget(self.tabs)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Buttons
        btn_layout = QHBoxLayout()

        save_btn = QPushButton("💾 حفظ الإعدادات")
        save_btn.clicked.connect(self._save_settings)

        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.close)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _create_connection_tab(self) -> QWidget:
        """Create connection settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # Connection info group
        conn_group = QGroupBox("معلومات الاتصال لـ Power BI")
        conn_layout = QFormLayout(conn_group)

        self.server_input = QLineEdit("localhost")
        self.server_input.setReadOnly(True)

        self.port_input = QLineEdit("5432")
        self.port_input.setReadOnly(True)

        self.database_input = QLineEdit("integra")
        self.database_input.setReadOnly(True)

        self.schema_input = QLineEdit("bi_views")
        self.schema_input.setReadOnly(True)

        conn_layout.addRow("السيرفر:", self.server_input)
        conn_layout.addRow("المنفذ:", self.port_input)
        conn_layout.addRow("قاعدة البيانات:", self.database_input)
        conn_layout.addRow("Schema:", self.schema_input)

        layout.addWidget(conn_group)

        # Connection string
        string_group = QGroupBox("نص الاتصال (Connection String)")
        string_layout = QVBoxLayout(string_group)

        self.conn_string = QLineEdit()
        self.conn_string.setReadOnly(True)
        self.conn_string.setText("Server=localhost;Port=5432;Database=integra")

        copy_btn = QPushButton("📋 نسخ")
        copy_btn.clicked.connect(self._copy_connection_string)

        string_layout.addWidget(self.conn_string)
        string_layout.addWidget(copy_btn)

        layout.addWidget(string_group)

        # Info box
        palette = get_current_palette()
        info_frame = QFrame()
        info_frame.setStyleSheet(f"background-color: {palette['primary_light']}; border-radius: 8px; padding: 10px;")
        info_layout = QVBoxLayout(info_frame)

        info_label = QLabel("""
        <b>خطوات الاتصال في Power BI Desktop:</b><br><br>
        1. افتح Power BI Desktop<br>
        2. اختر Get Data → PostgreSQL database<br>
        3. أدخل بيانات الاتصال أعلاه<br>
        4. اختر Views من schema: bi_views
        """)
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)

        layout.addWidget(info_frame)
        layout.addStretch()

        return widget

    def _create_export_tab(self) -> QWidget:
        """Create data export tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # Export settings group
        export_group = QGroupBox("إعدادات التصدير")
        export_layout = QFormLayout(export_group)

        self.auto_export_check = QCheckBox("تفعيل التصدير التلقائي اليومي")

        self.export_time = QTimeEdit()
        self.export_time.setTime(QTime(6, 0))
        self.export_time.setDisplayFormat("HH:mm")

        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["CSV", "Excel"])

        self.export_path_input = QLineEdit()
        browse_btn = QPushButton("...")
        browse_btn.setMaximumWidth(40)
        browse_btn.clicked.connect(self._browse_export_path)

        path_layout = QHBoxLayout()
        path_layout.addWidget(self.export_path_input)
        path_layout.addWidget(browse_btn)

        export_layout.addRow("التصدير التلقائي:", self.auto_export_check)
        export_layout.addRow("وقت التصدير:", self.export_time)
        export_layout.addRow("الصيغة:", self.export_format_combo)
        export_layout.addRow("مجلد التصدير:", path_layout)

        layout.addWidget(export_group)

        # Manual export group
        manual_group = QGroupBox("تصدير يدوي")
        manual_layout = QVBoxLayout(manual_group)

        export_csv_btn = QPushButton("📄 تصدير إلى CSV")
        export_csv_btn.clicked.connect(lambda: self._export_now("csv"))

        export_excel_btn = QPushButton("📊 تصدير إلى Excel")
        export_excel_btn.clicked.connect(lambda: self._export_now("excel"))

        manual_layout.addWidget(export_csv_btn)
        manual_layout.addWidget(export_excel_btn)

        layout.addWidget(manual_group)

        # Export history
        history_group = QGroupBox("سجل التصدير")
        history_layout = QVBoxLayout(history_group)

        self.export_history_table = QTableWidget()
        self.export_history_table.setColumnCount(4)
        self.export_history_table.setHorizontalHeaderLabels(["التاريخ", "النوع", "الحجم", "الحالة"])
        self.export_history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.export_history_table.setMaximumHeight(150)

        history_layout.addWidget(self.export_history_table)

        layout.addWidget(history_group)
        layout.addStretch()

        return widget

    def _create_views_tab(self) -> QWidget:
        """Create Views management tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # Views table
        views_group = QGroupBox("BI Views المتاحة")
        views_layout = QVBoxLayout(views_group)

        self.views_table = QTableWidget()
        self.views_table.setColumnCount(4)
        self.views_table.setHorizontalHeaderLabels(["View", "الاسم بالعربية", "الحالة", "السجلات"])
        self.views_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        views_layout.addWidget(self.views_table)

        # Buttons
        btn_layout = QHBoxLayout()

        refresh_btn = QPushButton("🔄 تحديث القائمة")
        refresh_btn.clicked.connect(self._refresh_views_list)

        create_btn = QPushButton("✨ إنشاء Views")
        create_btn.clicked.connect(self._create_views)

        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(create_btn)

        views_layout.addLayout(btn_layout)
        layout.addWidget(views_group)

        # Views info
        info_group = QGroupBox("معلومات")
        info_layout = QVBoxLayout(info_group)

        info_label = QLabel("""
        <b>BI Views</b> هي عروض محسّنة للتحليلات في Power BI:<br><br>
        • <b>employees_summary</b> - بيانات الموظفين الشاملة<br>
        • <b>department_stats</b> - إحصائيات الأقسام<br>
        • <b>payroll_analysis</b> - تحليل الرواتب<br>
        • <b>monthly_trends</b> - الاتجاهات الشهرية<br>
        • <b>company_summary</b> - ملخص الشركة
        """)
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)

        layout.addWidget(info_group)
        layout.addStretch()

        return widget

    def _create_templates_tab(self) -> QWidget:
        """Create templates management tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # Templates table
        templates_group = QGroupBox("قوالب Power BI الجاهزة")
        templates_layout = QVBoxLayout(templates_group)

        self.templates_table = QTableWidget()
        self.templates_table.setColumnCount(4)
        self.templates_table.setHorizontalHeaderLabels(["القالب", "الفئة", "الملف", "الحالة"])
        self.templates_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        templates_layout.addWidget(self.templates_table)

        # Buttons
        btn_layout = QHBoxLayout()

        open_btn = QPushButton("📂 فتح القالب المحدد")
        open_btn.clicked.connect(self._open_selected_template)

        create_placeholders_btn = QPushButton("📝 إنشاء ملفات README")
        create_placeholders_btn.clicked.connect(self._create_template_placeholders)

        btn_layout.addWidget(open_btn)
        btn_layout.addWidget(create_placeholders_btn)

        templates_layout.addLayout(btn_layout)
        layout.addWidget(templates_group)

        # Templates path
        path_group = QGroupBox("مجلد القوالب")
        path_layout = QHBoxLayout(path_group)

        self.templates_path_label = QLineEdit()
        self.templates_path_label.setReadOnly(True)

        open_folder_btn = QPushButton("📁 فتح المجلد")
        open_folder_btn.clicked.connect(self._open_templates_folder)

        path_layout.addWidget(self.templates_path_label)
        path_layout.addWidget(open_folder_btn)

        layout.addWidget(path_group)
        layout.addStretch()

        return widget

    def _create_guide_tab(self) -> QWidget:
        """Create user guide tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        guide_text = """
        <h2>دليل استخدام Power BI مع INTEGRA</h2>

        <h3>1. تثبيت Power BI Desktop (مجاني)</h3>
        <p>قم بتحميل Power BI Desktop من موقع Microsoft:<br>
        <a href="https://powerbi.microsoft.com/desktop">https://powerbi.microsoft.com/desktop</a></p>

        <h3>2. إعداد الاتصال</h3>
        <ol>
        <li>افتح Power BI Desktop</li>
        <li>اختر <b>Get Data</b> من الشريط العلوي</li>
        <li>ابحث عن <b>PostgreSQL database</b></li>
        <li>أدخل بيانات الاتصال:
            <ul>
            <li>Server: <code>localhost</code></li>
            <li>Database: <code>integra</code></li>
            </ul>
        </li>
        <li>اختر <b>DirectQuery</b> للبيانات الحية</li>
        </ol>

        <h3>3. اختيار البيانات</h3>
        <p>في Navigator، ابحث عن <b>bi_views</b> schema واختر Views المطلوبة:</p>
        <ul>
        <li><b>employees_summary</b> - بيانات الموظفين</li>
        <li><b>department_stats</b> - إحصائيات الأقسام</li>
        <li><b>payroll_analysis</b> - تحليل الرواتب</li>
        </ul>

        <h3>4. إنشاء التصورات</h3>
        <p>استخدم أدوات Power BI لإنشاء:</p>
        <ul>
        <li>مخططات بيانية (Charts)</li>
        <li>جداول (Tables)</li>
        <li>بطاقات (Cards)</li>
        <li>خرائط (Maps)</li>
        </ul>

        <h3>5. حفظ ومشاركة</h3>
        <p>احفظ التقرير كملف <code>.pbix</code> لمشاركته مع الآخرين.</p>
        """

        guide_label = QLabel(guide_text)
        guide_label.setWordWrap(True)
        guide_label.setOpenExternalLinks(True)
        guide_label.setTextFormat(Qt.RichText)

        from PyQt5.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidget(guide_label)
        scroll.setWidgetResizable(True)

        layout.addWidget(scroll)

        return widget

    def _load_settings(self):
        """Load current settings."""
        try:
            from core.bi import get_bi_config, get_export_path, get_template_manager

            config = get_bi_config()

            # Connection settings
            conn = config.get("connection", {})
            self.server_input.setText(conn.get("server", "localhost"))
            self.port_input.setText(str(conn.get("port", 5432)))
            self.database_input.setText(conn.get("database", "integra"))
            self.schema_input.setText(conn.get("bi_schema", "bi_views"))

            # Export settings
            export = config.get("export", {})
            self.auto_export_check.setChecked(export.get("auto_export_enabled", False))
            time_str = export.get("auto_export_time", "06:00")
            self.export_time.setTime(QTime.fromString(time_str, "HH:mm"))
            self.export_path_input.setText(str(get_export_path()))

            # Templates path
            tm = get_template_manager()
            self.templates_path_label.setText(str(tm.templates_path))

            # Load tables
            self._refresh_views_list()
            self._refresh_templates_list()

        except Exception as e:
            app_logger.error(f"Failed to load BI settings: {e}")

    def _save_settings(self):
        """Save current settings."""
        try:
            from core.bi.connection_config import save_settings, get_bi_config

            config = get_bi_config()

            # Update export settings
            config["export"]["auto_export_enabled"] = self.auto_export_check.isChecked()
            config["export"]["auto_export_time"] = self.export_time.time().toString("HH:mm")
            config["export"]["auto_export_format"] = self.export_format_combo.currentText().lower()
            config["export"]["export_path"] = self.export_path_input.text()

            if save_settings(config):
                self.status_label.setText("تم حفظ الإعدادات")
                p = get_current_palette()
                self.status_label.setStyleSheet(f"color: {p['success']};")
            else:
                self.status_label.setText("فشل حفظ الإعدادات")
                p = get_current_palette()
                self.status_label.setStyleSheet(f"color: {p['danger']};")

        except Exception as e:
            app_logger.error(f"Failed to save BI settings: {e}")
            self.status_label.setText(f"خطأ: {str(e)}")
            p = get_current_palette()
            self.status_label.setStyleSheet(f"color: {p['danger']};")

    def _copy_connection_string(self):
        """Copy connection string to clipboard."""
        from PyQt5.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.conn_string.text())
        self.status_label.setText("تم نسخ نص الاتصال")
        p = get_current_palette()
        self.status_label.setStyleSheet(f"color: {p['success']};")

    def _browse_export_path(self):
        """Browse for export directory."""
        path = QFileDialog.getExistingDirectory(self, "اختر مجلد التصدير")
        if path:
            self.export_path_input.setText(path)

    def _export_now(self, format_type: str):
        """Start export operation."""
        # Prevent starting a new export while one is running
        if self._worker is not None and self._worker.isRunning():
            self.status_label.setText("عملية تصدير قيد التنفيذ بالفعل...")
            p = get_current_palette()
            self.status_label.setStyleSheet(f"color: {p['warning']};")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self._worker = ExportWorker(export_format=format_type)
        self._worker.progress.connect(self._on_export_progress)
        self._worker.finished.connect(self._on_export_finished)
        self._worker.start()

    def _on_export_progress(self, value: int, message: str):
        """Handle export progress updates."""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)

    def _on_export_finished(self, success: bool, result: str):
        """Handle export completion."""
        self.progress_bar.setVisible(False)
        p = get_current_palette()

        if success:
            self.status_label.setText(f"{result}")
            self.status_label.setStyleSheet(f"color: {p['success']};")
        else:
            self.status_label.setText(f"{result}")
            self.status_label.setStyleSheet(f"color: {p['danger']};")

    def _refresh_views_list(self):
        """Refresh the views table."""
        try:
            from core.bi import get_bi_views_manager
            from core.bi.views_manager import ViewStatus

            manager = get_bi_views_manager()
            views_info = manager.get_all_views_info()

            self.views_table.setRowCount(len(views_info))

            for row, info in enumerate(views_info):
                self.views_table.setItem(row, 0, QTableWidgetItem(info.name))
                self.views_table.setItem(row, 1, QTableWidgetItem(info.name_ar))

                status_text = "✅ موجود" if info.status == ViewStatus.EXISTS else "❌ غير موجود"
                self.views_table.setItem(row, 2, QTableWidgetItem(status_text))

                self.views_table.setItem(row, 3, QTableWidgetItem(str(info.row_count)))

        except Exception as e:
            app_logger.error(f"Failed to refresh views list: {e}")

    def _create_views(self):
        """Create all BI Views."""
        # Prevent starting while another operation is running
        if self._worker is not None and self._worker.isRunning():
            self.status_label.setText("عملية قيد التنفيذ بالفعل...")
            p = get_current_palette()
            self.status_label.setStyleSheet(f"color: {p['warning']};")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self._worker = ViewsWorker(action="create")
        self._worker.progress.connect(self._on_export_progress)
        self._worker.finished.connect(self._on_views_finished)
        self._worker.start()

    def _on_views_finished(self, success: bool, created: int, failed: int):
        """Handle views creation completion."""
        self.progress_bar.setVisible(False)
        p = get_current_palette()

        if success:
            self.status_label.setText(f"تم إنشاء {created} views ({failed} فشل)")
            self.status_label.setStyleSheet(f"color: {p['success']};")
            self._refresh_views_list()
        else:
            self.status_label.setText("فشل إنشاء Views")
            self.status_label.setStyleSheet(f"color: {p['danger']};")

    def _refresh_templates_list(self):
        """Refresh the templates table."""
        try:
            from core.bi import get_template_manager

            manager = get_template_manager()
            templates = manager.get_all_templates()

            self.templates_table.setRowCount(len(templates))

            for row, template in enumerate(templates):
                self.templates_table.setItem(row, 0, QTableWidgetItem(template.name_ar))
                self.templates_table.setItem(row, 1, QTableWidgetItem(template.category.value))
                self.templates_table.setItem(row, 2, QTableWidgetItem(template.file_name))

                status = "✅ موجود" if template.exists else "❌ غير موجود"
                self.templates_table.setItem(row, 3, QTableWidgetItem(status))

        except Exception as e:
            app_logger.error(f"Failed to refresh templates list: {e}")

    def _open_selected_template(self):
        """Open the selected template in Power BI."""
        try:
            from core.bi import get_template_manager

            row = self.templates_table.currentRow()
            if row < 0:
                QMessageBox.warning(self, "تنبيه", "الرجاء اختيار قالب أولاً")
                return

            manager = get_template_manager()
            templates = manager.get_all_templates()

            if row < len(templates):
                template = templates[row]
                if template.exists:
                    manager.open_template(template.id)
                else:
                    QMessageBox.warning(self, "تنبيه", "ملف القالب غير موجود")

        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))

    def _create_template_placeholders(self):
        """Create placeholder files for templates."""
        try:
            from core.bi import get_template_manager

            manager = get_template_manager()
            count = manager.create_all_placeholders()

            QMessageBox.information(
                self,
                "تم",
                f"تم إنشاء {count} ملفات README للقوالب"
            )
            self._refresh_templates_list()

        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))

    def closeEvent(self, event):
        """Clean up worker threads on dialog close."""
        if self._worker is not None and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait(3000)
        self._worker = None
        super().closeEvent(event)

    def _open_templates_folder(self):
        """Open templates folder in file explorer."""
        import subprocess
        import platform

        path = self.templates_path_label.text()

        try:
            if platform.system() == "Windows":
                subprocess.run(["explorer", path])
            elif platform.system() == "Darwin":
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"تعذر فتح المجلد: {e}")
