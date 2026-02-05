"""
File Manager Window
===================
Main window for the Smart File Manager module.

Provides a tabbed interface for:
- File Browser with dual-pane navigation
- Excel AI Engine
- PDF AI Studio
- Image Tools
- Word Engine
- Cloud Storage
- Document Attachments
"""

import os
from pathlib import Path
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QGroupBox, QGridLayout,
    QPushButton, QTabWidget, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QSplitter, QTreeWidget, QTreeWidgetItem,
    QLineEdit, QComboBox, QProgressBar, QTextEdit,
    QSpinBox, QCheckBox, QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSignal

from ui.windows.base import BaseWindow
from core.logging import app_logger


# ═══════════════════════════════════════════════════════
# Styles
# ═══════════════════════════════════════════════════════

ACCENT_COLOR = "#06b6d4"  # Cyan

SECTION_STYLE = f"""
    QGroupBox {{
        font-size: 16px;
        font-weight: bold;
        color: {ACCENT_COLOR};
        border: 2px solid {ACCENT_COLOR}40;
        border-radius: 10px;
        margin-top: 10px;
        padding-top: 20px;
        font-family: 'Cairo', sans-serif;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 15px;
        padding: 0 8px;
    }}
"""

BTN_STYLE = f"""
    QPushButton {{
        font-size: 13px;
        font-family: 'Cairo', sans-serif;
        padding: 8px 16px;
        background-color: {ACCENT_COLOR};
        color: #1f2937;
        border: none;
        border-radius: 6px;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: #0891b2;
    }}
    QPushButton:disabled {{
        background-color: #374151;
        color: #6b7280;
    }}
"""

BTN_SECONDARY_STYLE = """
    QPushButton {
        font-size: 13px;
        font-family: 'Cairo', sans-serif;
        padding: 8px 16px;
        background-color: #374151;
        color: #e5e7eb;
        border: 1px solid #4b5563;
        border-radius: 6px;
    }
    QPushButton:hover {
        background-color: #4b5563;
    }
"""

TABLE_STYLE = """
    QTableWidget {
        background-color: #1f2937;
        color: #e5e7eb;
        border: 1px solid #374151;
        border-radius: 6px;
        font-size: 13px;
        font-family: 'Cairo', sans-serif;
        gridline-color: #374151;
    }
    QTableWidget::item {
        padding: 5px;
    }
    QTableWidget::item:selected {
        background-color: #06b6d440;
    }
    QHeaderView::section {
        background-color: #111827;
        color: #9ca3af;
        padding: 8px;
        border: 1px solid #374151;
        font-weight: bold;
    }
"""

INPUT_STYLE = """
    QLineEdit, QComboBox, QSpinBox {
        font-size: 13px;
        font-family: 'Cairo', sans-serif;
        padding: 6px 10px;
        background-color: #1f2937;
        color: #e5e7eb;
        border: 1px solid #374151;
        border-radius: 6px;
    }
    QLineEdit:focus, QComboBox:focus {
        border-color: #06b6d4;
    }
"""


class FileManagerWindow(BaseWindow):
    """
    Smart File Manager main window.

    Tabbed interface with:
    - File Browser
    - Excel AI Engine
    - PDF AI Studio
    - Image Tools
    - Word Engine
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("مدير الملفات الذكي - INTEGRA")
        self.setMinimumSize(1100, 750)

        self._current_excel_engine = None
        self._current_pdf_studio = None

        self._setup_ui()

    def _setup_ui(self):
        """Setup the window UI."""
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Title
        title = QLabel("مدير الملفات الذكي")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {ACCENT_COLOR};
            padding: 8px;
            font-family: 'Cairo', sans-serif;
        """)
        main_layout.addWidget(title)

        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid #374151;
                border-radius: 6px;
                background-color: #111827;
            }}
            QTabBar::tab {{
                background-color: #1f2937;
                color: #9ca3af;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-family: 'Cairo', sans-serif;
                font-size: 13px;
                font-weight: bold;
            }}
            QTabBar::tab:selected {{
                background-color: {ACCENT_COLOR};
                color: #1f2937;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: #374151;
                color: #e5e7eb;
            }}
        """)
        self.tabs.setLayoutDirection(Qt.RightToLeft)

        # Create tabs
        self.tabs.addTab(self._create_browser_tab(), "مستكشف الملفات")
        self.tabs.addTab(self._create_excel_tab(), "Excel الذكي")
        self.tabs.addTab(self._create_pdf_tab(), "استوديو PDF")
        self.tabs.addTab(self._create_image_tab(), "أدوات الصور")
        self.tabs.addTab(self._create_word_tab(), "محرك Word")

        main_layout.addWidget(self.tabs)

        # Status bar
        self.status_label = QLabel("جاهز")
        self.status_label.setStyleSheet(
            "font-size: 12px; color: #6b7280; font-family: 'Cairo'; padding: 5px;"
        )
        main_layout.addWidget(self.status_label)

    # ═══════════════════════════════════════════════════════
    # File Browser Tab
    # ═══════════════════════════════════════════════════════

    def _create_browser_tab(self) -> QWidget:
        """Create the file browser tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        # Navigation bar
        nav_layout = QHBoxLayout()

        btn_up = QPushButton("Up")
        btn_up.setStyleSheet(BTN_SECONDARY_STYLE)
        btn_up.setFixedWidth(60)
        btn_up.clicked.connect(self._browser_go_up)
        nav_layout.addWidget(btn_up)

        btn_home = QPushButton("Home")
        btn_home.setStyleSheet(BTN_SECONDARY_STYLE)
        btn_home.setFixedWidth(70)
        btn_home.clicked.connect(self._browser_go_home)
        nav_layout.addWidget(btn_home)

        self.path_input = QLineEdit()
        self.path_input.setStyleSheet(INPUT_STYLE)
        self.path_input.setText(str(Path.home()))
        self.path_input.returnPressed.connect(self._browser_navigate)
        nav_layout.addWidget(self.path_input)

        btn_go = QPushButton("Go")
        btn_go.setStyleSheet(BTN_STYLE)
        btn_go.setFixedWidth(60)
        btn_go.clicked.connect(self._browser_navigate)
        nav_layout.addWidget(btn_go)

        layout.addLayout(nav_layout)

        # File table
        self.file_table = QTableWidget()
        self.file_table.setStyleSheet(TABLE_STYLE)
        self.file_table.setColumnCount(4)
        self.file_table.setHorizontalHeaderLabels(["الاسم", "النوع", "الحجم", "تاريخ التعديل"])
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.file_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.file_table.doubleClicked.connect(self._browser_item_activated)
        self.file_table.setLayoutDirection(Qt.RightToLeft)
        layout.addWidget(self.file_table)

        # Actions bar
        actions = QHBoxLayout()

        btn_refresh = QPushButton("تحديث")
        btn_refresh.setStyleSheet(BTN_SECONDARY_STYLE)
        btn_refresh.clicked.connect(self._browser_refresh)
        actions.addWidget(btn_refresh)

        btn_new_folder = QPushButton("مجلد جديد")
        btn_new_folder.setStyleSheet(BTN_SECONDARY_STYLE)
        btn_new_folder.clicked.connect(self._browser_new_folder)
        actions.addWidget(btn_new_folder)

        actions.addStretch()

        self.lbl_dir_stats = QLabel("")
        self.lbl_dir_stats.setStyleSheet("font-size: 12px; color: #6b7280; font-family: 'Cairo';")
        actions.addWidget(self.lbl_dir_stats)

        layout.addLayout(actions)

        # Load initial directory
        self._browser_load_directory(str(Path.home()))

        return widget

    # ═══════════════════════════════════════════════════════
    # Excel Tab
    # ═══════════════════════════════════════════════════════

    def _create_excel_tab(self) -> QWidget:
        """Create the Excel AI Engine tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        # File selection
        file_layout = QHBoxLayout()

        self.excel_path = QLineEdit()
        self.excel_path.setStyleSheet(INPUT_STYLE)
        self.excel_path.setPlaceholderText("اختر ملف Excel أو CSV...")
        self.excel_path.setReadOnly(True)
        file_layout.addWidget(self.excel_path)

        btn_browse_excel = QPushButton("استعراض")
        btn_browse_excel.setStyleSheet(BTN_STYLE)
        btn_browse_excel.clicked.connect(self._excel_browse)
        file_layout.addWidget(btn_browse_excel)

        btn_load_excel = QPushButton("تحميل")
        btn_load_excel.setStyleSheet(BTN_STYLE)
        btn_load_excel.clicked.connect(self._excel_load)
        file_layout.addWidget(btn_load_excel)

        layout.addLayout(file_layout)

        # Info label
        self.excel_info = QLabel("لم يتم تحميل ملف")
        self.excel_info.setStyleSheet("font-size: 13px; color: #9ca3af; font-family: 'Cairo';")
        self.excel_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.excel_info)

        # Data preview table
        self.excel_table = QTableWidget()
        self.excel_table.setStyleSheet(TABLE_STYLE)
        self.excel_table.setLayoutDirection(Qt.RightToLeft)
        layout.addWidget(self.excel_table)

        # Action buttons
        excel_actions = QHBoxLayout()

        btn_analyze = QPushButton("تحليل الأعمدة")
        btn_analyze.setStyleSheet(BTN_STYLE)
        btn_analyze.clicked.connect(self._excel_analyze)
        excel_actions.addWidget(btn_analyze)

        btn_clean = QPushButton("تنظيف البيانات")
        btn_clean.setStyleSheet(BTN_SECONDARY_STYLE)
        btn_clean.clicked.connect(self._excel_clean)
        excel_actions.addWidget(btn_clean)

        btn_duplicates = QPushButton("اكتشاف المكرر")
        btn_duplicates.setStyleSheet(BTN_SECONDARY_STYLE)
        btn_duplicates.clicked.connect(self._excel_duplicates)
        excel_actions.addWidget(btn_duplicates)

        btn_quality = QPushButton("تقرير الجودة")
        btn_quality.setStyleSheet(BTN_SECONDARY_STYLE)
        btn_quality.clicked.connect(self._excel_quality)
        excel_actions.addWidget(btn_quality)

        excel_actions.addStretch()
        layout.addLayout(excel_actions)

        # Analysis results
        self.excel_results = QTextEdit()
        self.excel_results.setStyleSheet("""
            QTextEdit {
                background-color: #1f2937;
                color: #e5e7eb;
                border: 1px solid #374151;
                border-radius: 6px;
                font-size: 13px;
                font-family: 'Cairo', monospace;
                padding: 10px;
            }
        """)
        self.excel_results.setReadOnly(True)
        self.excel_results.setMaximumHeight(200)
        layout.addWidget(self.excel_results)

        return widget

    # ═══════════════════════════════════════════════════════
    # PDF Tab
    # ═══════════════════════════════════════════════════════

    def _create_pdf_tab(self) -> QWidget:
        """Create the PDF AI Studio tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        # File selection
        file_layout = QHBoxLayout()

        self.pdf_path = QLineEdit()
        self.pdf_path.setStyleSheet(INPUT_STYLE)
        self.pdf_path.setPlaceholderText("اختر ملف PDF...")
        self.pdf_path.setReadOnly(True)
        file_layout.addWidget(self.pdf_path)

        btn_browse_pdf = QPushButton("استعراض")
        btn_browse_pdf.setStyleSheet(BTN_STYLE)
        btn_browse_pdf.clicked.connect(self._pdf_browse)
        file_layout.addWidget(btn_browse_pdf)

        layout.addLayout(file_layout)

        # PDF Info
        self.pdf_info = QLabel("لم يتم تحميل ملف")
        self.pdf_info.setStyleSheet("font-size: 13px; color: #9ca3af; font-family: 'Cairo';")
        self.pdf_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.pdf_info)

        # PDF Operations
        ops_group = QGroupBox("العمليات")
        ops_group.setStyleSheet(SECTION_STYLE)
        ops_layout = QGridLayout()
        ops_group.setLayout(ops_layout)

        # Row 1: Split & Merge
        btn_split = QPushButton("فصل الصفحات")
        btn_split.setStyleSheet(BTN_STYLE)
        btn_split.clicked.connect(self._pdf_split_all)
        ops_layout.addWidget(btn_split, 0, 0)

        btn_merge = QPushButton("دمج ملفات PDF")
        btn_merge.setStyleSheet(BTN_STYLE)
        btn_merge.clicked.connect(self._pdf_merge)
        ops_layout.addWidget(btn_merge, 0, 1)

        btn_compress = QPushButton("ضغط PDF")
        btn_compress.setStyleSheet(BTN_STYLE)
        btn_compress.clicked.connect(self._pdf_compress)
        ops_layout.addWidget(btn_compress, 0, 2)

        # Row 2: OCR & Text
        btn_text = QPushButton("استخراج النص")
        btn_text.setStyleSheet(BTN_SECONDARY_STYLE)
        btn_text.clicked.connect(self._pdf_extract_text)
        ops_layout.addWidget(btn_text, 1, 0)

        btn_ocr = QPushButton("OCR (عربي + إنجليزي)")
        btn_ocr.setStyleSheet(BTN_SECONDARY_STYLE)
        btn_ocr.clicked.connect(self._pdf_ocr)
        ops_layout.addWidget(btn_ocr, 1, 1)

        btn_search = QPushButton("بحث في المحتوى")
        btn_search.setStyleSheet(BTN_SECONDARY_STYLE)
        btn_search.clicked.connect(self._pdf_search)
        ops_layout.addWidget(btn_search, 1, 2)

        # Row 3: Security & Conversion
        btn_watermark = QPushButton("علامة مائية")
        btn_watermark.setStyleSheet(BTN_SECONDARY_STYLE)
        btn_watermark.clicked.connect(self._pdf_watermark)
        ops_layout.addWidget(btn_watermark, 2, 0)

        btn_encrypt = QPushButton("تشفير بكلمة مرور")
        btn_encrypt.setStyleSheet(BTN_SECONDARY_STYLE)
        btn_encrypt.clicked.connect(self._pdf_encrypt)
        ops_layout.addWidget(btn_encrypt, 2, 1)

        btn_to_images = QPushButton("تحويل إلى صور")
        btn_to_images.setStyleSheet(BTN_SECONDARY_STYLE)
        btn_to_images.clicked.connect(self._pdf_to_images)
        ops_layout.addWidget(btn_to_images, 2, 2)

        layout.addWidget(ops_group)

        # Results area
        self.pdf_results = QTextEdit()
        self.pdf_results.setStyleSheet("""
            QTextEdit {
                background-color: #1f2937;
                color: #e5e7eb;
                border: 1px solid #374151;
                border-radius: 6px;
                font-size: 13px;
                font-family: 'Cairo', monospace;
                padding: 10px;
            }
        """)
        self.pdf_results.setReadOnly(True)
        layout.addWidget(self.pdf_results)

        return widget

    # ═══════════════════════════════════════════════════════
    # Image Tab
    # ═══════════════════════════════════════════════════════

    def _create_image_tab(self) -> QWidget:
        """Create the Image Tools tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        # File selection
        file_layout = QHBoxLayout()

        self.image_path = QLineEdit()
        self.image_path.setStyleSheet(INPUT_STYLE)
        self.image_path.setPlaceholderText("اختر صورة...")
        self.image_path.setReadOnly(True)
        file_layout.addWidget(self.image_path)

        btn_browse_img = QPushButton("استعراض")
        btn_browse_img.setStyleSheet(BTN_STYLE)
        btn_browse_img.clicked.connect(self._image_browse)
        file_layout.addWidget(btn_browse_img)

        layout.addLayout(file_layout)

        # Image info
        self.image_info = QLabel("لم يتم تحميل صورة")
        self.image_info.setStyleSheet("font-size: 13px; color: #9ca3af; font-family: 'Cairo';")
        self.image_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_info)

        # Operations
        ops = QGroupBox("العمليات")
        ops.setStyleSheet(SECTION_STYLE)
        ops_layout = QGridLayout()
        ops.setLayout(ops_layout)

        # Resize
        ops_layout.addWidget(QLabel("تغيير الحجم:"), 0, 0)
        self.img_width = QSpinBox()
        self.img_width.setStyleSheet(INPUT_STYLE)
        self.img_width.setRange(1, 10000)
        self.img_width.setValue(800)
        ops_layout.addWidget(self.img_width, 0, 1)

        ops_layout.addWidget(QLabel("x"), 0, 2)
        self.img_height = QSpinBox()
        self.img_height.setStyleSheet(INPUT_STYLE)
        self.img_height.setRange(1, 10000)
        self.img_height.setValue(600)
        ops_layout.addWidget(self.img_height, 0, 3)

        btn_resize = QPushButton("تطبيق")
        btn_resize.setStyleSheet(BTN_STYLE)
        btn_resize.clicked.connect(self._image_resize)
        ops_layout.addWidget(btn_resize, 0, 4)

        # Convert
        ops_layout.addWidget(QLabel("تحويل إلى:"), 1, 0)
        self.img_format = QComboBox()
        self.img_format.setStyleSheet(INPUT_STYLE)
        self.img_format.addItems(["PNG", "JPEG", "BMP", "WEBP", "TIFF"])
        ops_layout.addWidget(self.img_format, 1, 1, 1, 2)

        btn_convert = QPushButton("تحويل")
        btn_convert.setStyleSheet(BTN_STYLE)
        btn_convert.clicked.connect(self._image_convert)
        ops_layout.addWidget(btn_convert, 1, 4)

        # Compress
        ops_layout.addWidget(QLabel("ضغط (جودة):"), 2, 0)
        self.img_quality = QSpinBox()
        self.img_quality.setStyleSheet(INPUT_STYLE)
        self.img_quality.setRange(1, 100)
        self.img_quality.setValue(85)
        ops_layout.addWidget(self.img_quality, 2, 1, 1, 2)

        btn_compress = QPushButton("ضغط")
        btn_compress.setStyleSheet(BTN_STYLE)
        btn_compress.clicked.connect(self._image_compress)
        ops_layout.addWidget(btn_compress, 2, 4)

        # Batch processing
        btn_batch = QPushButton("معالجة دفعية")
        btn_batch.setStyleSheet(BTN_SECONDARY_STYLE)
        btn_batch.clicked.connect(self._image_batch)
        ops_layout.addWidget(btn_batch, 3, 0, 1, 5)

        layout.addWidget(ops)

        # Results
        self.image_results = QTextEdit()
        self.image_results.setStyleSheet("""
            QTextEdit {
                background-color: #1f2937;
                color: #e5e7eb;
                border: 1px solid #374151;
                border-radius: 6px;
                font-size: 13px;
                font-family: 'Cairo', monospace;
                padding: 10px;
            }
        """)
        self.image_results.setReadOnly(True)
        layout.addWidget(self.image_results)

        return widget

    # ═══════════════════════════════════════════════════════
    # Word Tab
    # ═══════════════════════════════════════════════════════

    def _create_word_tab(self) -> QWidget:
        """Create the Word Engine tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        # File selection
        file_layout = QHBoxLayout()

        self.word_path = QLineEdit()
        self.word_path.setStyleSheet(INPUT_STYLE)
        self.word_path.setPlaceholderText("اختر ملف Word...")
        self.word_path.setReadOnly(True)
        file_layout.addWidget(self.word_path)

        btn_browse_word = QPushButton("استعراض")
        btn_browse_word.setStyleSheet(BTN_STYLE)
        btn_browse_word.clicked.connect(self._word_browse)
        file_layout.addWidget(btn_browse_word)

        btn_new_word = QPushButton("مستند جديد")
        btn_new_word.setStyleSheet(BTN_SECONDARY_STYLE)
        btn_new_word.clicked.connect(self._word_new)
        file_layout.addWidget(btn_new_word)

        layout.addLayout(file_layout)

        # Word info
        self.word_info = QLabel("لم يتم تحميل مستند")
        self.word_info.setStyleSheet("font-size: 13px; color: #9ca3af; font-family: 'Cairo';")
        self.word_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.word_info)

        # Content display
        self.word_content = QTextEdit()
        self.word_content.setStyleSheet("""
            QTextEdit {
                background-color: #1f2937;
                color: #e5e7eb;
                border: 1px solid #374151;
                border-radius: 6px;
                font-size: 14px;
                font-family: 'Cairo', sans-serif;
                padding: 15px;
            }
        """)
        self.word_content.setReadOnly(True)
        layout.addWidget(self.word_content)

        # Actions
        word_actions = QHBoxLayout()

        btn_read = QPushButton("قراءة النص")
        btn_read.setStyleSheet(BTN_STYLE)
        btn_read.clicked.connect(self._word_read)
        word_actions.addWidget(btn_read)

        btn_tables = QPushButton("قراءة الجداول")
        btn_tables.setStyleSheet(BTN_SECONDARY_STYLE)
        btn_tables.clicked.connect(self._word_read_tables)
        word_actions.addWidget(btn_tables)

        btn_stats = QPushButton("إحصائيات")
        btn_stats.setStyleSheet(BTN_SECONDARY_STYLE)
        btn_stats.clicked.connect(self._word_stats)
        word_actions.addWidget(btn_stats)

        btn_to_pdf = QPushButton("تحويل إلى PDF")
        btn_to_pdf.setStyleSheet(BTN_SECONDARY_STYLE)
        btn_to_pdf.clicked.connect(self._word_to_pdf)
        word_actions.addWidget(btn_to_pdf)

        word_actions.addStretch()
        layout.addLayout(word_actions)

        return widget

    # ═══════════════════════════════════════════════════════
    # File Browser Handlers
    # ═══════════════════════════════════════════════════════

    def _browser_load_directory(self, path: str):
        """Load directory contents into the table."""
        try:
            from core.file_manager.browser import FileBrowser

            browser = FileBrowser()
            items = browser.list_directory(path)

            self.file_table.setRowCount(len(items))
            for i, item in enumerate(items):
                self.file_table.setItem(i, 0, QTableWidgetItem(
                    f"{'[DIR] ' if item.is_dir else ''}{item.name}"
                ))
                self.file_table.setItem(i, 1, QTableWidgetItem(
                    "مجلد" if item.is_dir else item.extension or "ملف"
                ))
                self.file_table.setItem(i, 2, QTableWidgetItem(
                    item.size_formatted if not item.is_dir else ""
                ))
                self.file_table.setItem(i, 3, QTableWidgetItem(
                    item.modified.strftime("%Y-%m-%d %H:%M") if item.modified else ""
                ))

            self.path_input.setText(path)

            # Stats
            stats = browser.get_directory_stats(path)
            self.lbl_dir_stats.setText(
                f"{stats['folders']} مجلد | {stats['files']} ملف | {stats['total_size_formatted']}"
            )
            self._set_status(f"تم تحميل: {path}")

        except Exception as e:
            self._set_status(f"خطأ: {e}")

    def _browser_navigate(self):
        path = self.path_input.text().strip()
        if path and Path(path).is_dir():
            self._browser_load_directory(path)

    def _browser_go_up(self):
        current = Path(self.path_input.text())
        parent = current.parent
        if parent != current:
            self._browser_load_directory(str(parent))

    def _browser_go_home(self):
        self._browser_load_directory(str(Path.home()))

    def _browser_refresh(self):
        self._browser_load_directory(self.path_input.text())

    def _browser_item_activated(self, index):
        row = index.row()
        name_item = self.file_table.item(row, 0)
        if not name_item:
            return

        name = name_item.text()
        if name.startswith("[DIR] "):
            name = name.replace("[DIR] ", "")
            new_path = str(Path(self.path_input.text()) / name)
            self._browser_load_directory(new_path)

    def _browser_new_folder(self):
        from PyQt5.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(self, "مجلد جديد", "اسم المجلد:")
        if ok and name:
            try:
                new_path = Path(self.path_input.text()) / name
                new_path.mkdir(parents=True, exist_ok=True)
                self._browser_refresh()
                self._set_status(f"تم إنشاء المجلد: {name}")
            except Exception as e:
                self._set_status(f"خطأ في إنشاء المجلد: {e}")

    # ═══════════════════════════════════════════════════════
    # Excel Handlers
    # ═══════════════════════════════════════════════════════

    def _excel_browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "اختر ملف Excel/CSV", "",
            "Excel/CSV Files (*.xlsx *.xls *.csv *.xlsm);;All Files (*)"
        )
        if path:
            self.excel_path.setText(path)

    def _excel_load(self):
        path = self.excel_path.text()
        if not path:
            return

        try:
            from core.file_manager.excel import ExcelAIEngine

            self._current_excel_engine = ExcelAIEngine(path)
            success, msg = self._current_excel_engine.load()

            if success:
                self.excel_info.setText(msg)
                self.excel_info.setStyleSheet(
                    "font-size: 13px; color: #10b981; font-family: 'Cairo';"
                )

                # Show preview
                preview = self._current_excel_engine.preview(20)
                if preview is not None:
                    self.excel_table.setRowCount(len(preview))
                    self.excel_table.setColumnCount(len(preview.columns))
                    self.excel_table.setHorizontalHeaderLabels(list(preview.columns))

                    for i in range(len(preview)):
                        for j in range(len(preview.columns)):
                            val = preview.iloc[i, j]
                            self.excel_table.setItem(
                                i, j, QTableWidgetItem(str(val) if val is not None else "")
                            )

                self._set_status(f"تم تحميل: {Path(path).name}")
            else:
                self.excel_info.setText(f"خطأ: {msg}")
                self.excel_info.setStyleSheet(
                    "font-size: 13px; color: #ef4444; font-family: 'Cairo';"
                )
        except Exception as e:
            self._set_status(f"خطأ: {e}")

    def _excel_analyze(self):
        if not self._current_excel_engine:
            return

        analyses = self._current_excel_engine.analyze_columns()
        results = "=== تحليل الأعمدة ===\n\n"

        for a in analyses:
            results += (
                f"العمود: {a.name}\n"
                f"  النوع: {a.detected_type.value} (ثقة: {a.confidence:.0%})\n"
                f"  القيم الفارغة: {a.null_count} | القيم الفريدة: {a.unique_count}\n"
            )
            if a.suggested_db_column:
                results += f"  عمود DB المقترح: {a.suggested_db_column}\n"
            results += "\n"

        self.excel_results.setText(results)
        self._set_status("تم تحليل الأعمدة")

    def _excel_clean(self):
        if not self._current_excel_engine:
            return

        result = self._current_excel_engine.clean_data()
        text = "=== تنظيف البيانات ===\n\n"
        text += f"الصفوف الأصلية: {result.get('original_rows', 0)}\n"
        text += f"الصفوف بعد التنظيف: {result.get('cleaned_rows', 0)}\n"
        text += f"الصفوف المحذوفة: {result.get('removed_rows', 0)}\n\n"
        text += "التغييرات:\n"
        for change in result.get('changes', []):
            text += f"  - {change}\n"

        self.excel_results.setText(text)
        self._set_status("تم تنظيف البيانات")

    def _excel_duplicates(self):
        if not self._current_excel_engine:
            return

        dups = self._current_excel_engine.detect_duplicates()
        if dups is not None and len(dups) > 0:
            self.excel_results.setText(
                f"=== الصفوف المكررة ===\n\nعدد المكررات: {len(dups)}\n\n"
                f"{dups.head(20).to_string()}"
            )
        else:
            self.excel_results.setText("لا توجد صفوف مكررة")
        self._set_status("تم فحص المكررات")

    def _excel_quality(self):
        if not self._current_excel_engine:
            return

        report = self._current_excel_engine.get_data_quality_report()
        text = "=== تقرير جودة البيانات ===\n\n"
        text += f"الصفوف: {report.get('total_rows', 0)}\n"
        text += f"الأعمدة: {report.get('total_columns', 0)}\n\n"

        for col, info in report.get('columns', {}).items():
            text += (
                f"  {col}: "
                f"فارغ {info['null_percent']}% | "
                f"فريد {info['unique_count']} | "
                f"نوع {info['dtype']}\n"
            )

        self.excel_results.setText(text)
        self._set_status("تم إنشاء تقرير الجودة")

    # ═══════════════════════════════════════════════════════
    # PDF Handlers
    # ═══════════════════════════════════════════════════════

    def _pdf_browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "اختر ملف PDF", "", "PDF Files (*.pdf);;All Files (*)"
        )
        if path:
            self.pdf_path.setText(path)
            self._pdf_load(path)

    def _pdf_load(self, path: str):
        try:
            from core.file_manager.pdf import PDFTools, PDFAIStudio

            info = PDFTools.get_info(path)
            self.pdf_info.setText(
                f"الصفحات: {info.get('page_count', 0)} | "
                f"الحجم: {info.get('file_size_formatted', '')} | "
                f"مشفر: {'نعم' if info.get('is_encrypted') else 'لا'}"
            )
            self.pdf_info.setStyleSheet(
                "font-size: 13px; color: #10b981; font-family: 'Cairo';"
            )

            self._current_pdf_studio = PDFAIStudio()
            self._current_pdf_studio.open(path)

            self._set_status(f"تم تحميل PDF: {Path(path).name}")
        except Exception as e:
            self.pdf_info.setText(f"خطأ: {e}")
            self._set_status(f"خطأ: {e}")

    def _pdf_split_all(self):
        if not self._current_pdf_studio or not self._current_pdf_studio.documents:
            return

        folder = QFileDialog.getExistingDirectory(self, "اختر مجلد الحفظ")
        if folder:
            doc_id = list(self._current_pdf_studio.documents.keys())[0]
            files = self._current_pdf_studio.split_all(doc_id, folder)
            self.pdf_results.setText(f"تم فصل {len(files)} صفحة إلى:\n{folder}")
            self._set_status(f"تم فصل {len(files)} صفحة")

    def _pdf_merge(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "اختر ملفات PDF للدمج", "", "PDF Files (*.pdf)"
        )
        if len(files) < 2:
            return

        output, _ = QFileDialog.getSaveFileName(
            self, "حفظ الملف المدمج", "", "PDF Files (*.pdf)"
        )
        if output:
            studio = PDFAIStudio() if not self._current_pdf_studio else self._current_pdf_studio
            if studio.merge(files, output):
                self.pdf_results.setText(f"تم دمج {len(files)} ملفات في:\n{output}")
                self._set_status("تم الدمج بنجاح")
            else:
                self.pdf_results.setText("فشل الدمج")

    def _pdf_compress(self):
        if not self._current_pdf_studio or not self._current_pdf_studio.documents:
            return

        output, _ = QFileDialog.getSaveFileName(
            self, "حفظ الملف المضغوط", "", "PDF Files (*.pdf)"
        )
        if output:
            doc_id = list(self._current_pdf_studio.documents.keys())[0]
            result = self._current_pdf_studio.compress(doc_id, output, "medium")
            if result.get("success"):
                self.pdf_results.setText(
                    f"تم الضغط بنجاح!\n"
                    f"الحجم الأصلي: {result['original_size']:,} bytes\n"
                    f"الحجم المضغوط: {result['compressed_size']:,} bytes\n"
                    f"نسبة التخفيض: {result['reduction_percent']}%"
                )
            else:
                self.pdf_results.setText("فشل الضغط")

    def _pdf_extract_text(self):
        if not self._current_pdf_studio or not self._current_pdf_studio.documents:
            return

        doc_id = list(self._current_pdf_studio.documents.keys())[0]
        text = self._current_pdf_studio.get_all_text(doc_id)
        self.pdf_results.setText(text if text.strip() else "لا يوجد نص قابل للاستخراج في هذا الملف")
        self._set_status("تم استخراج النص")

    def _pdf_ocr(self):
        if not self._current_pdf_studio or not self._current_pdf_studio.documents:
            return

        doc_id = list(self._current_pdf_studio.documents.keys())[0]
        results = self._current_pdf_studio.ocr_document(doc_id)
        text = "=== نتائج OCR ===\n\n"
        for r in results:
            text += f"--- صفحة {r['page']} ({r['word_count']} كلمة) ---\n{r['text']}\n\n"
        self.pdf_results.setText(text)
        self._set_status("تم OCR")

    def _pdf_search(self):
        from PyQt5.QtWidgets import QInputDialog

        query, ok = QInputDialog.getText(self, "بحث", "نص البحث:")
        if ok and query:
            if not self._current_pdf_studio or not self._current_pdf_studio.documents:
                return
            doc_id = list(self._current_pdf_studio.documents.keys())[0]
            results = self._current_pdf_studio.search(doc_id, query)
            text = f"=== نتائج البحث عن '{query}' ===\n\n"
            for r in results:
                text += f"صفحة {r['page']}: {r['count']} نتيجة\n"
            if not results:
                text += "لم يتم العثور على نتائج"
            self.pdf_results.setText(text)

    def _pdf_watermark(self):
        if not self._current_pdf_studio or not self._current_pdf_studio.documents:
            return

        from PyQt5.QtWidgets import QInputDialog

        text, ok = QInputDialog.getText(self, "علامة مائية", "نص العلامة المائية:")
        if ok and text:
            output, _ = QFileDialog.getSaveFileName(
                self, "حفظ", "", "PDF Files (*.pdf)"
            )
            if output:
                doc_id = list(self._current_pdf_studio.documents.keys())[0]
                if self._current_pdf_studio.add_watermark(doc_id, text, output):
                    self.pdf_results.setText(f"تم إضافة العلامة المائية: {output}")

    def _pdf_encrypt(self):
        if not self._current_pdf_studio or not self._current_pdf_studio.documents:
            return

        from PyQt5.QtWidgets import QInputDialog

        password, ok = QInputDialog.getText(self, "تشفير", "كلمة المرور:")
        if ok and password:
            output, _ = QFileDialog.getSaveFileName(
                self, "حفظ", "", "PDF Files (*.pdf)"
            )
            if output:
                doc_id = list(self._current_pdf_studio.documents.keys())[0]
                if self._current_pdf_studio.encrypt(doc_id, password, output):
                    self.pdf_results.setText(f"تم التشفير: {output}")

    def _pdf_to_images(self):
        if not self._current_pdf_studio or not self._current_pdf_studio.documents:
            return

        folder = QFileDialog.getExistingDirectory(self, "اختر مجلد الحفظ")
        if folder:
            doc_id = list(self._current_pdf_studio.documents.keys())[0]
            files = self._current_pdf_studio.to_images(doc_id, folder)
            self.pdf_results.setText(f"تم تحويل {len(files)} صفحة إلى صور في:\n{folder}")

    # ═══════════════════════════════════════════════════════
    # Image Handlers
    # ═══════════════════════════════════════════════════════

    def _image_browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "اختر صورة", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp *.tiff *.gif);;All Files (*)"
        )
        if path:
            self.image_path.setText(path)
            self._image_load_info(path)

    def _image_load_info(self, path: str):
        try:
            from core.file_manager.image import ImageTools

            info = ImageTools.get_info(path)
            if "error" not in info:
                self.image_info.setText(
                    f"الأبعاد: {info['width']}x{info['height']} | "
                    f"الصيغة: {info['format']} | "
                    f"الحجم: {info['file_size_formatted']}"
                )
                self.image_info.setStyleSheet(
                    "font-size: 13px; color: #10b981; font-family: 'Cairo';"
                )
                self.img_width.setValue(info['width'])
                self.img_height.setValue(info['height'])
        except Exception as e:
            self.image_info.setText(f"خطأ: {e}")

    def _image_resize(self):
        path = self.image_path.text()
        if not path:
            return

        output, _ = QFileDialog.getSaveFileName(self, "حفظ", "", "Images (*.png *.jpg)")
        if output:
            from core.file_manager.image import ImageTools
            result = ImageTools.resize(
                path, output,
                size=(self.img_width.value(), self.img_height.value())
            )
            if result.get("success"):
                self.image_results.setText(
                    f"تم تغيير الحجم!\n"
                    f"الأصلي: {result['original_size']}\n"
                    f"الجديد: {result['new_size']}"
                )

    def _image_convert(self):
        path = self.image_path.text()
        if not path:
            return

        fmt = self.img_format.currentText()
        ext = fmt.lower()
        if ext == "jpeg":
            ext = "jpg"

        output, _ = QFileDialog.getSaveFileName(
            self, "حفظ", "", f"{fmt} Files (*.{ext})"
        )
        if output:
            from core.file_manager.image import ImageTools
            result = ImageTools.convert(path, output, fmt)
            if result.get("success"):
                self.image_results.setText(
                    f"تم التحويل من {result['original_format']} إلى {result['new_format']}"
                )

    def _image_compress(self):
        path = self.image_path.text()
        if not path:
            return

        output, _ = QFileDialog.getSaveFileName(self, "حفظ", "", "Images (*.jpg *.png)")
        if output:
            from core.file_manager.image import ImageTools
            result = ImageTools.compress(path, output, self.img_quality.value())
            if result.get("success"):
                self.image_results.setText(
                    f"تم الضغط!\n"
                    f"الحجم الأصلي: {result['original_size']:,} bytes\n"
                    f"الحجم المضغوط: {result['compressed_size']:,} bytes\n"
                    f"نسبة التخفيض: {result['reduction_percent']}%"
                )

    def _image_batch(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "اختر صور", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp);;All Files (*)"
        )
        if not files:
            return

        folder = QFileDialog.getExistingDirectory(self, "اختر مجلد الحفظ")
        if not folder:
            return

        from core.file_manager.image import ImageTools

        operations = [
            {"type": "resize", "scale": 0.5},
            {"type": "compress", "quality": self.img_quality.value()},
        ]

        results = ImageTools.batch_process(files, folder, operations)
        text = f"=== معالجة دفعية ({len(results)} صورة) ===\n\n"
        success = sum(1 for r in results if r.get("success"))
        text += f"نجح: {success} | فشل: {len(results) - success}\n"
        self.image_results.setText(text)

    # ═══════════════════════════════════════════════════════
    # Word Handlers
    # ═══════════════════════════════════════════════════════

    def _word_browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "اختر ملف Word", "",
            "Word Files (*.docx *.doc);;All Files (*)"
        )
        if path:
            self.word_path.setText(path)
            self._word_load_info(path)

    def _word_load_info(self, path: str):
        try:
            from core.file_manager.word import WordEngine

            engine = WordEngine(path)
            stats = engine.get_stats()
            self.word_info.setText(
                f"الفقرات: {stats['paragraphs']} | "
                f"الجداول: {stats['tables']} | "
                f"الكلمات: {stats['words']}"
            )
            self.word_info.setStyleSheet(
                "font-size: 13px; color: #10b981; font-family: 'Cairo';"
            )
        except Exception as e:
            self.word_info.setText(f"خطأ: {e}")

    def _word_new(self):
        self.word_path.setText("")
        self.word_info.setText("مستند جديد")
        self.word_content.clear()
        self._set_status("مستند Word جديد")

    def _word_read(self):
        path = self.word_path.text()
        if not path:
            return

        try:
            from core.file_manager.word import WordEngine
            engine = WordEngine(path)
            text = engine.read_text()
            self.word_content.setText(text)
            self._set_status("تم قراءة النص")
        except Exception as e:
            self._set_status(f"خطأ: {e}")

    def _word_read_tables(self):
        path = self.word_path.text()
        if not path:
            return

        try:
            from core.file_manager.word import WordEngine
            engine = WordEngine(path)
            tables = engine.read_tables()

            text = f"=== {len(tables)} جدول ===\n\n"
            for i, table in enumerate(tables, 1):
                text += f"--- جدول {i} ---\n"
                for row in table:
                    text += " | ".join(row) + "\n"
                text += "\n"

            self.word_content.setText(text)
            self._set_status(f"تم قراءة {len(tables)} جدول")
        except Exception as e:
            self._set_status(f"خطأ: {e}")

    def _word_stats(self):
        path = self.word_path.text()
        if not path:
            return

        try:
            from core.file_manager.word import WordEngine
            engine = WordEngine(path)
            stats = engine.get_stats()

            text = "=== إحصائيات المستند ===\n\n"
            text += f"الفقرات: {stats['paragraphs']}\n"
            text += f"الجداول: {stats['tables']}\n"
            text += f"الكلمات: {stats['words']}\n"
            text += f"الأحرف: {stats['characters']}\n"
            text += f"الأقسام: {stats['sections']}\n"

            headings = engine.get_headings()
            if headings:
                text += f"\nالعناوين ({len(headings)}):\n"
                for h in headings:
                    text += f"  {'  ' * h['level']}{h['text']}\n"

            self.word_content.setText(text)
        except Exception as e:
            self._set_status(f"خطأ: {e}")

    def _word_to_pdf(self):
        path = self.word_path.text()
        if not path:
            return

        output, _ = QFileDialog.getSaveFileName(
            self, "حفظ PDF", "", "PDF Files (*.pdf)"
        )
        if output:
            try:
                from core.file_manager.word import WordEngine
                engine = WordEngine(path)
                if engine.to_pdf(output):
                    self.word_content.setText(f"تم التحويل إلى PDF:\n{output}")
                else:
                    self.word_content.setText("فشل التحويل (قد يتطلب LibreOffice أو docx2pdf)")
            except Exception as e:
                self._set_status(f"خطأ: {e}")

    # ═══════════════════════════════════════════════════════
    # Utility
    # ═══════════════════════════════════════════════════════

    def _set_status(self, msg: str):
        """Update status bar message."""
        self.status_label.setText(msg)

    def closeEvent(self, event):
        """Cleanup on close."""
        if self._current_pdf_studio:
            self._current_pdf_studio.close_all()
        event.accept()
