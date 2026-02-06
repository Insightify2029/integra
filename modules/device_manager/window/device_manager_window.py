"""
Device Manager Window
=====================
Main window for the Device Manager module.

Tabbed interface with:
- Printers tab (discovery, status, print settings)
- Scanners tab (discovery, scan, batch scan)
- Bluetooth tab (discovery, pairing, connection)
"""

import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QGroupBox, QGridLayout,
    QPushButton, QTabWidget, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QProgressBar, QSpinBox, QCheckBox,
    QTextEdit, QSplitter, QMessageBox,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal

from ui.windows.base import BaseWindow
from core.logging import app_logger
from core.threading import run_in_background


# ═══════════════════════════════════════════════════════
# Styles
# ═══════════════════════════════════════════════════════

ACCENT_COLOR = "#e11d48"  # Rose

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
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: #be123c;
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

TABLE_STYLE = f"""
    QTableWidget {{
        background-color: #1f2937;
        color: #e5e7eb;
        border: 1px solid #374151;
        border-radius: 6px;
        font-size: 13px;
        font-family: 'Cairo', sans-serif;
        gridline-color: #374151;
    }}
    QTableWidget::item {{
        padding: 5px;
    }}
    QTableWidget::item:selected {{
        background-color: {ACCENT_COLOR}40;
    }}
    QHeaderView::section {{
        background-color: #111827;
        color: #9ca3af;
        padding: 8px;
        border: 1px solid #374151;
        font-weight: bold;
    }}
"""

TAB_STYLE = f"""
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
        font-size: 14px;
        font-weight: bold;
    }}
    QTabBar::tab:selected {{
        background-color: {ACCENT_COLOR};
        color: white;
    }}
    QTabBar::tab:hover:!selected {{
        background-color: #374151;
        color: #e5e7eb;
    }}
"""

INPUT_STYLE = """
    QComboBox, QSpinBox {
        font-size: 13px;
        font-family: 'Cairo', sans-serif;
        padding: 6px 10px;
        background-color: #1f2937;
        color: #e5e7eb;
        border: 1px solid #374151;
        border-radius: 6px;
    }
    QComboBox:focus, QSpinBox:focus {
        border-color: #e11d48;
    }
"""

STATUS_COLORS = {
    'ready': '#10b981',
    'جاهزة': '#10b981',
    'جاهز': '#10b981',
    'connected': '#10b981',
    'متصل': '#10b981',
    'busy': '#f59e0b',
    'مشغولة': '#f59e0b',
    'مشغول': '#f59e0b',
    'paired': '#3b82f6',
    'مقترن': '#3b82f6',
    'offline': '#6b7280',
    'غير متصلة': '#6b7280',
    'غير متصل': '#6b7280',
    'error': '#ef4444',
    'خطأ': '#ef4444',
}


class DeviceManagerWindow(BaseWindow):
    """
    Device Manager main window.

    Tabbed interface with:
    - Printers: Discovery, status, print settings
    - Scanners: Discovery, scan settings, batch scan
    - Bluetooth: Discovery, pairing, connection management
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إدارة الأجهزة والطابعات - INTEGRA")
        self.setMinimumSize(1100, 750)

        self._printer_discovery = None
        self._scanner_discovery = None
        self._bluetooth_manager = None
        self._print_manager = None
        self._scan_engine = None
        self._batch_scanner = None
        self._pdf_bridge = None

        self._setup_ui()
        self._setup_connections()

        # Auto-discover on open
        QTimer.singleShot(500, self._initial_discovery)

    # ═══════════════════════════════════════════════════════
    # Lazy-load components
    # ═══════════════════════════════════════════════════════

    @property
    def printer_discovery(self):
        if self._printer_discovery is None:
            from core.device_manager.printer import PrinterDiscovery
            self._printer_discovery = PrinterDiscovery()
        return self._printer_discovery

    @property
    def scanner_discovery(self):
        if self._scanner_discovery is None:
            from core.device_manager.scanner import ScannerDiscovery
            self._scanner_discovery = ScannerDiscovery()
        return self._scanner_discovery

    @property
    def bluetooth_manager(self):
        if self._bluetooth_manager is None:
            from core.device_manager.bluetooth import BluetoothManager
            self._bluetooth_manager = BluetoothManager()
        return self._bluetooth_manager

    @property
    def print_manager(self):
        if self._print_manager is None:
            from core.device_manager.printer import PrintManager
            self._print_manager = PrintManager()
        return self._print_manager

    @property
    def scan_engine(self):
        if self._scan_engine is None:
            from core.device_manager.scanner import ScanEngine
            self._scan_engine = ScanEngine()
        return self._scan_engine

    @property
    def batch_scanner(self):
        if self._batch_scanner is None:
            from core.device_manager.scanner import BatchScanner
            self._batch_scanner = BatchScanner()
        return self._batch_scanner

    @property
    def pdf_bridge(self):
        if self._pdf_bridge is None:
            from core.device_manager.integration import PDFStudioBridge
            self._pdf_bridge = PDFStudioBridge()
        return self._pdf_bridge

    # ═══════════════════════════════════════════════════════
    # UI Setup
    # ═══════════════════════════════════════════════════════

    def _setup_ui(self):
        """Setup the window UI."""
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # Title
        title = QLabel("إدارة الأجهزة والطابعات")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {ACCENT_COLOR};
            padding: 10px;
            font-family: 'Cairo', sans-serif;
        """)
        main_layout.addWidget(title)

        subtitle = QLabel("الطابعات | الماسحات الضوئية | البلوتوث")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 14px;
            color: #9ca3af;
            padding-bottom: 5px;
            font-family: 'Cairo', sans-serif;
        """)
        main_layout.addWidget(subtitle)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(TAB_STYLE)
        main_layout.addWidget(self.tabs)

        # Create tabs
        self._create_printers_tab()
        self._create_scanners_tab()
        self._create_bluetooth_tab()

        # Status bar at bottom
        self.status_label = QLabel("جاهز")
        self.status_label.setStyleSheet("""
            font-size: 12px;
            color: #6b7280;
            padding: 5px;
            font-family: 'Cairo', sans-serif;
        """)
        main_layout.addWidget(self.status_label)

    # ═══════════════════════════════════════════════════════
    # Printers Tab
    # ═══════════════════════════════════════════════════════

    def _create_printers_tab(self):
        """Create the printers management tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Toolbar
        toolbar = QHBoxLayout()

        btn_refresh_printers = QPushButton("تحديث الطابعات")
        btn_refresh_printers.setStyleSheet(BTN_STYLE)
        btn_refresh_printers.setObjectName("btn_refresh_printers")
        toolbar.addWidget(btn_refresh_printers)

        btn_print_test = QPushButton("طباعة صفحة اختبار")
        btn_print_test.setStyleSheet(BTN_SECONDARY_STYLE)
        btn_print_test.setObjectName("btn_print_test")
        toolbar.addWidget(btn_print_test)

        btn_print_file = QPushButton("طباعة ملف")
        btn_print_file.setStyleSheet(BTN_SECONDARY_STYLE)
        btn_print_file.setObjectName("btn_print_file")
        toolbar.addWidget(btn_print_file)

        toolbar.addStretch()

        self.lbl_printer_count = QLabel("الطابعات: 0")
        self.lbl_printer_count.setStyleSheet("font-size: 13px; color: #9ca3af; font-family: 'Cairo';")
        toolbar.addWidget(self.lbl_printer_count)

        layout.addLayout(toolbar)

        # Printers table
        self.printer_table = QTableWidget()
        self.printer_table.setStyleSheet(TABLE_STYLE)
        self.printer_table.setColumnCount(7)
        self.printer_table.setHorizontalHeaderLabels([
            "الاسم", "النوع", "الحالة", "المنفذ", "التعريف", "الموقع", "افتراضي"
        ])
        self.printer_table.horizontalHeader().setStretchLastSection(True)
        self.printer_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.printer_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.printer_table.setAlternatingRowColors(True)
        self.printer_table.verticalHeader().setVisible(False)
        self.printer_table.setLayoutDirection(Qt.RightToLeft)
        layout.addWidget(self.printer_table)

        # Print Settings Section
        settings_group = QGroupBox("إعدادات الطباعة")
        settings_group.setStyleSheet(SECTION_STYLE)
        settings_layout = QGridLayout()
        settings_layout.setSpacing(10)

        # Paper size
        settings_layout.addWidget(self._make_label("حجم الورق:"), 0, 3)
        self.combo_paper = QComboBox()
        self.combo_paper.setStyleSheet(INPUT_STYLE)
        self.combo_paper.addItems(["A4 قياسي", "A3 كبير", "A5 صغير", "Letter أمريكي", "Legal قانوني"])
        settings_layout.addWidget(self.combo_paper, 0, 2)

        # Orientation
        settings_layout.addWidget(self._make_label("الاتجاه:"), 0, 1)
        self.combo_orientation = QComboBox()
        self.combo_orientation.setStyleSheet(INPUT_STYLE)
        self.combo_orientation.addItems(["عمودي", "أفقي"])
        settings_layout.addWidget(self.combo_orientation, 0, 0)

        # Copies
        settings_layout.addWidget(self._make_label("عدد النسخ:"), 1, 3)
        self.spin_copies = QSpinBox()
        self.spin_copies.setStyleSheet(INPUT_STYLE)
        self.spin_copies.setRange(1, 999)
        self.spin_copies.setValue(1)
        settings_layout.addWidget(self.spin_copies, 1, 2)

        # Quality
        settings_layout.addWidget(self._make_label("الجودة:"), 1, 1)
        self.combo_quality = QComboBox()
        self.combo_quality.setStyleSheet(INPUT_STYLE)
        self.combo_quality.addItems(["مسودة", "عادي", "عالي", "أفضل جودة"])
        self.combo_quality.setCurrentIndex(1)
        settings_layout.addWidget(self.combo_quality, 1, 0)

        # Color mode
        settings_layout.addWidget(self._make_label("الألوان:"), 2, 3)
        self.combo_color = QComboBox()
        self.combo_color.setStyleSheet(INPUT_STYLE)
        self.combo_color.addItems(["ألوان", "تدرج رمادي", "أبيض وأسود"])
        settings_layout.addWidget(self.combo_color, 2, 2)

        # Duplex
        settings_layout.addWidget(self._make_label("الوجهين:"), 2, 1)
        self.combo_duplex = QComboBox()
        self.combo_duplex.setStyleSheet(INPUT_STYLE)
        self.combo_duplex.addItems(["وجه واحد", "وجهين - الحافة الطويلة", "وجهين - الحافة القصيرة"])
        settings_layout.addWidget(self.combo_duplex, 2, 0)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        self.tabs.addTab(tab, "🖨️ الطابعات")

    # ═══════════════════════════════════════════════════════
    # Scanners Tab
    # ═══════════════════════════════════════════════════════

    def _create_scanners_tab(self):
        """Create the scanners management tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Toolbar
        toolbar = QHBoxLayout()

        btn_refresh_scanners = QPushButton("تحديث الماسحات")
        btn_refresh_scanners.setStyleSheet(BTN_STYLE)
        btn_refresh_scanners.setObjectName("btn_refresh_scanners")
        toolbar.addWidget(btn_refresh_scanners)

        btn_scan = QPushButton("مسح ضوئي")
        btn_scan.setStyleSheet(BTN_SECONDARY_STYLE)
        btn_scan.setObjectName("btn_scan")
        toolbar.addWidget(btn_scan)

        btn_batch_scan = QPushButton("مسح دفعي (ADF)")
        btn_batch_scan.setStyleSheet(BTN_SECONDARY_STYLE)
        btn_batch_scan.setObjectName("btn_batch_scan")
        toolbar.addWidget(btn_batch_scan)

        btn_scan_to_pdf = QPushButton("مسح إلى PDF")
        btn_scan_to_pdf.setStyleSheet(BTN_SECONDARY_STYLE)
        btn_scan_to_pdf.setObjectName("btn_scan_to_pdf")
        toolbar.addWidget(btn_scan_to_pdf)

        toolbar.addStretch()

        self.lbl_scanner_count = QLabel("الماسحات: 0")
        self.lbl_scanner_count.setStyleSheet("font-size: 13px; color: #9ca3af; font-family: 'Cairo';")
        toolbar.addWidget(self.lbl_scanner_count)

        layout.addLayout(toolbar)

        # Scanners table
        self.scanner_table = QTableWidget()
        self.scanner_table.setStyleSheet(TABLE_STYLE)
        self.scanner_table.setColumnCount(7)
        self.scanner_table.setHorizontalHeaderLabels([
            "الاسم", "النوع", "الحالة", "الشركة", "الموديل", "ADF", "الدقة القصوى"
        ])
        self.scanner_table.horizontalHeader().setStretchLastSection(True)
        self.scanner_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.scanner_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.scanner_table.setAlternatingRowColors(True)
        self.scanner_table.verticalHeader().setVisible(False)
        self.scanner_table.setLayoutDirection(Qt.RightToLeft)
        layout.addWidget(self.scanner_table)

        # Scan settings
        scan_group = QGroupBox("إعدادات المسح الضوئي")
        scan_group.setStyleSheet(SECTION_STYLE)
        scan_layout = QGridLayout()
        scan_layout.setSpacing(10)

        # Resolution
        scan_layout.addWidget(self._make_label("الدقة (DPI):"), 0, 3)
        self.combo_resolution = QComboBox()
        self.combo_resolution.setStyleSheet(INPUT_STYLE)
        self.combo_resolution.addItems(["75", "150", "200", "300", "600", "1200"])
        self.combo_resolution.setCurrentIndex(3)  # 300 DPI default
        scan_layout.addWidget(self.combo_resolution, 0, 2)

        # Color mode
        scan_layout.addWidget(self._make_label("وضع اللون:"), 0, 1)
        self.combo_scan_color = QComboBox()
        self.combo_scan_color.setStyleSheet(INPUT_STYLE)
        self.combo_scan_color.addItems(["ألوان", "تدرج رمادي", "أبيض وأسود"])
        scan_layout.addWidget(self.combo_scan_color, 0, 0)

        # Source
        scan_layout.addWidget(self._make_label("المصدر:"), 1, 3)
        self.combo_scan_source = QComboBox()
        self.combo_scan_source.setStyleSheet(INPUT_STYLE)
        self.combo_scan_source.addItems(["السطح المستوي", "التلقيم التلقائي - وجه واحد", "التلقيم التلقائي - وجهين"])
        scan_layout.addWidget(self.combo_scan_source, 1, 2)

        # Format
        scan_layout.addWidget(self._make_label("الصيغة:"), 1, 1)
        self.combo_scan_format = QComboBox()
        self.combo_scan_format.setStyleSheet(INPUT_STYLE)
        self.combo_scan_format.addItems(["PNG", "JPEG", "TIFF", "BMP", "PDF"])
        scan_layout.addWidget(self.combo_scan_format, 1, 0)

        # Paper size
        scan_layout.addWidget(self._make_label("حجم الورق:"), 2, 3)
        self.combo_scan_paper = QComboBox()
        self.combo_scan_paper.setStyleSheet(INPUT_STYLE)
        self.combo_scan_paper.addItems(["A4", "A3", "A5", "Letter", "Legal", "تلقائي"])
        scan_layout.addWidget(self.combo_scan_paper, 2, 2)

        # Checkboxes
        self.chk_auto_crop = QCheckBox("قص تلقائي")
        self.chk_auto_crop.setStyleSheet("font-family: 'Cairo'; font-size: 13px; color: #e5e7eb;")
        scan_layout.addWidget(self.chk_auto_crop, 2, 1)

        self.chk_auto_deskew = QCheckBox("تعديل الميل تلقائياً")
        self.chk_auto_deskew.setStyleSheet("font-family: 'Cairo'; font-size: 13px; color: #e5e7eb;")
        scan_layout.addWidget(self.chk_auto_deskew, 2, 0)

        scan_group.setLayout(scan_layout)
        layout.addWidget(scan_group)

        # Progress bar
        self.scan_progress = QProgressBar()
        self.scan_progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #374151;
                border-radius: 4px;
                text-align: center;
                font-family: 'Cairo';
                color: #e5e7eb;
                background-color: #1f2937;
            }}
            QProgressBar::chunk {{
                background-color: {ACCENT_COLOR};
                border-radius: 3px;
            }}
        """)
        self.scan_progress.setVisible(False)
        layout.addWidget(self.scan_progress)

        self.tabs.addTab(tab, "📷 الماسحات الضوئية")

    # ═══════════════════════════════════════════════════════
    # Bluetooth Tab
    # ═══════════════════════════════════════════════════════

    def _create_bluetooth_tab(self):
        """Create the Bluetooth management tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Adapter status bar
        adapter_bar = QHBoxLayout()

        self.lbl_bt_adapter = QLabel("محول البلوتوث: جاري الفحص...")
        self.lbl_bt_adapter.setStyleSheet("font-size: 14px; color: #9ca3af; font-family: 'Cairo'; font-weight: bold;")
        adapter_bar.addWidget(self.lbl_bt_adapter)

        adapter_bar.addStretch()

        self.btn_bt_toggle = QPushButton("تشغيل البلوتوث")
        self.btn_bt_toggle.setStyleSheet(BTN_SECONDARY_STYLE)
        self.btn_bt_toggle.setObjectName("btn_bt_toggle")
        adapter_bar.addWidget(self.btn_bt_toggle)

        layout.addLayout(adapter_bar)

        # Toolbar
        toolbar = QHBoxLayout()

        btn_bt_scan = QPushButton("بحث عن أجهزة")
        btn_bt_scan.setStyleSheet(BTN_STYLE)
        btn_bt_scan.setObjectName("btn_bt_scan")
        toolbar.addWidget(btn_bt_scan)

        btn_bt_pair = QPushButton("اقتران")
        btn_bt_pair.setStyleSheet(BTN_SECONDARY_STYLE)
        btn_bt_pair.setObjectName("btn_bt_pair")
        toolbar.addWidget(btn_bt_pair)

        btn_bt_connect = QPushButton("اتصال")
        btn_bt_connect.setStyleSheet(BTN_SECONDARY_STYLE)
        btn_bt_connect.setObjectName("btn_bt_connect")
        toolbar.addWidget(btn_bt_connect)

        btn_bt_disconnect = QPushButton("قطع الاتصال")
        btn_bt_disconnect.setStyleSheet(BTN_SECONDARY_STYLE)
        btn_bt_disconnect.setObjectName("btn_bt_disconnect")
        toolbar.addWidget(btn_bt_disconnect)

        toolbar.addStretch()

        self.lbl_bt_count = QLabel("الأجهزة: 0")
        self.lbl_bt_count.setStyleSheet("font-size: 13px; color: #9ca3af; font-family: 'Cairo';")
        toolbar.addWidget(self.lbl_bt_count)

        layout.addLayout(toolbar)

        # Bluetooth devices table
        self.bt_table = QTableWidget()
        self.bt_table.setStyleSheet(TABLE_STYLE)
        self.bt_table.setColumnCount(7)
        self.bt_table.setHorizontalHeaderLabels([
            "الجهاز", "النوع", "الحالة", "العنوان (MAC)", "الإشارة", "البطارية", "مقترن"
        ])
        self.bt_table.horizontalHeader().setStretchLastSection(True)
        self.bt_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.bt_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.bt_table.setAlternatingRowColors(True)
        self.bt_table.verticalHeader().setVisible(False)
        self.bt_table.setLayoutDirection(Qt.RightToLeft)
        layout.addWidget(self.bt_table)

        # Device info panel
        info_group = QGroupBox("معلومات الجهاز")
        info_group.setStyleSheet(SECTION_STYLE)
        info_layout = QGridLayout()
        info_layout.setSpacing(8)

        self.lbl_bt_name = self._make_value_label("---")
        info_layout.addWidget(self._make_label("الاسم:"), 0, 3)
        info_layout.addWidget(self.lbl_bt_name, 0, 2)

        self.lbl_bt_type = self._make_value_label("---")
        info_layout.addWidget(self._make_label("النوع:"), 0, 1)
        info_layout.addWidget(self.lbl_bt_type, 0, 0)

        self.lbl_bt_mac = self._make_value_label("---")
        info_layout.addWidget(self._make_label("العنوان:"), 1, 3)
        info_layout.addWidget(self.lbl_bt_mac, 1, 2)

        self.lbl_bt_signal = self._make_value_label("---")
        info_layout.addWidget(self._make_label("الإشارة:"), 1, 1)
        info_layout.addWidget(self.lbl_bt_signal, 1, 0)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        self.tabs.addTab(tab, "📶 البلوتوث")

    # ═══════════════════════════════════════════════════════
    # Connections
    # ═══════════════════════════════════════════════════════

    def _setup_connections(self):
        """Connect signals to slots."""
        # Printers
        self._find_button("btn_refresh_printers").clicked.connect(self._refresh_printers)
        self._find_button("btn_print_test").clicked.connect(self._print_test_page)
        self._find_button("btn_print_file").clicked.connect(self._print_file)

        # Scanners
        self._find_button("btn_refresh_scanners").clicked.connect(self._refresh_scanners)
        self._find_button("btn_scan").clicked.connect(self._scan_single)
        self._find_button("btn_batch_scan").clicked.connect(self._batch_scan)
        self._find_button("btn_scan_to_pdf").clicked.connect(self._scan_to_pdf)

        # Bluetooth
        self._find_button("btn_bt_scan").clicked.connect(self._bt_discover)
        self._find_button("btn_bt_toggle").clicked.connect(self._bt_toggle)
        self._find_button("btn_bt_pair").clicked.connect(self._bt_pair)
        self._find_button("btn_bt_connect").clicked.connect(self._bt_connect)
        self._find_button("btn_bt_disconnect").clicked.connect(self._bt_disconnect)

        # Table selection
        self.bt_table.currentCellChanged.connect(self._on_bt_selection_changed)

    def _find_button(self, name: str) -> QPushButton:
        """Find a button by object name."""
        btn = self.findChild(QPushButton, name)
        if btn is None:
            btn = QPushButton()  # Dummy to avoid errors
        return btn

    # ═══════════════════════════════════════════════════════
    # Initial Discovery
    # ═══════════════════════════════════════════════════════

    def _initial_discovery(self):
        """Run initial device discovery."""
        self._update_status("جاري اكتشاف الأجهزة...")
        self._refresh_printers()
        self._refresh_scanners()
        self._bt_check_adapter()

    # ═══════════════════════════════════════════════════════
    # Printer Actions
    # ═══════════════════════════════════════════════════════

    def _refresh_printers(self):
        """Refresh printer list (runs in background thread)."""
        self._update_status("جاري البحث عن الطابعات...")
        self._find_button("btn_refresh_printers").setEnabled(False)

        def _do_discover():
            return self.printer_discovery.refresh()

        def _on_done(printers):
            self._find_button("btn_refresh_printers").setEnabled(True)
            self.printer_table.setRowCount(0)

            for printer in printers:
                row = self.printer_table.rowCount()
                self.printer_table.insertRow(row)

                self.printer_table.setItem(row, 0, QTableWidgetItem(printer.name))

                type_item = QTableWidgetItem(printer.type_text_ar)
                self.printer_table.setItem(row, 1, type_item)

                status_item = QTableWidgetItem(printer.status_text_ar)
                status_item.setForeground(Qt.white)
                self.printer_table.setItem(row, 2, status_item)

                self.printer_table.setItem(row, 3, QTableWidgetItem(printer.port))
                self.printer_table.setItem(row, 4, QTableWidgetItem(printer.driver))
                self.printer_table.setItem(row, 5, QTableWidgetItem(printer.location))
                self.printer_table.setItem(row, 6, QTableWidgetItem("✓" if printer.is_default else ""))

            self.lbl_printer_count.setText(f"الطابعات: {len(printers)}")
            self._update_status(f"تم اكتشاف {len(printers)} طابعة")

        def _on_error(error_type, error_msg, tb):
            self._find_button("btn_refresh_printers").setEnabled(True)
            app_logger.error(f"Error refreshing printers: {error_msg}")
            self._update_status(f"خطأ في اكتشاف الطابعات: {error_msg}")

        run_in_background(_do_discover, on_finished=_on_done, on_error=_on_error, task_name="printer_discovery")

    def _print_test_page(self):
        """Print a test page on selected printer (runs in background)."""
        row = self.printer_table.currentRow()
        if row < 0:
            self._show_warning("تنبيه", "يرجى اختيار طابعة أولاً")
            return

        printer_name = self.printer_table.item(row, 0).text()
        self._find_button("btn_print_test").setEnabled(False)
        self._update_status(f"جاري طباعة صفحة اختبار على {printer_name}...")

        def _do_print():
            from core.device_manager.printer.print_manager import PrintSettings
            settings = PrintSettings(printer_name=printer_name)
            test_html = f"""
            <html dir="rtl">
            <body style="font-family: Cairo, Arial; text-align: center; padding: 50px;">
                <h1 style="color: #e11d48;">INTEGRA - صفحة اختبار</h1>
                <hr>
                <p>الطابعة: {printer_name}</p>
                <p>التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
                <p>هذه صفحة اختبار من نظام INTEGRA</p>
                <p>This is a test page from INTEGRA system</p>
                <hr>
                <p style="color: #10b981; font-weight: bold;">الطباعة تعمل بنجاح!</p>
            </body>
            </html>
            """
            return self.print_manager.print_html(test_html, settings)

        def _on_done(job):
            self._find_button("btn_print_test").setEnabled(True)
            self._update_status(f"طباعة اختبار: {job.status_text_ar}")

        def _on_error(error_type, error_msg, tb):
            self._find_button("btn_print_test").setEnabled(True)
            self._update_status(f"خطأ في الطباعة: {error_msg}")

        run_in_background(_do_print, on_finished=_on_done, on_error=_on_error, task_name="print_test_page")

    def _print_file(self):
        """Open file dialog and print selected file (runs in background)."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "اختر ملف للطباعة", "",
            "كل الملفات (*);;PDF (*.pdf);;نصوص (*.txt);;صور (*.png *.jpg *.bmp)"
        )
        if not file_path:
            return

        row = self.printer_table.currentRow()
        printer_name = ""
        if row >= 0:
            printer_name = self.printer_table.item(row, 0).text()

        copies = self.spin_copies.value()
        self._find_button("btn_print_file").setEnabled(False)
        self._update_status(f"جاري طباعة {os.path.basename(file_path)}...")

        def _do_print():
            from core.device_manager.printer.print_manager import PrintSettings
            settings = PrintSettings(
                printer_name=printer_name,
                copies=copies,
            )
            return self.print_manager.print_file(file_path, settings)

        def _on_done(job):
            self._find_button("btn_print_file").setEnabled(True)
            self._update_status(f"طباعة: {job.status_text_ar} - {os.path.basename(file_path)}")

        def _on_error(error_type, error_msg, tb):
            self._find_button("btn_print_file").setEnabled(True)
            self._update_status(f"خطأ في الطباعة: {error_msg}")

        run_in_background(_do_print, on_finished=_on_done, on_error=_on_error, task_name="print_file")

    # ═══════════════════════════════════════════════════════
    # Scanner Actions
    # ═══════════════════════════════════════════════════════

    def _refresh_scanners(self):
        """Refresh scanner list (runs in background thread)."""
        self._update_status("جاري البحث عن الماسحات الضوئية...")
        self._find_button("btn_refresh_scanners").setEnabled(False)

        def _do_discover():
            return self.scanner_discovery.refresh()

        def _on_done(scanners):
            self._find_button("btn_refresh_scanners").setEnabled(True)
            self.scanner_table.setRowCount(0)

            for scanner in scanners:
                row = self.scanner_table.rowCount()
                self.scanner_table.insertRow(row)

                self.scanner_table.setItem(row, 0, QTableWidgetItem(scanner.display_name))
                self.scanner_table.setItem(row, 1, QTableWidgetItem(scanner.type_text_ar))

                status_item = QTableWidgetItem(scanner.status_text_ar)
                self.scanner_table.setItem(row, 2, status_item)

                self.scanner_table.setItem(row, 3, QTableWidgetItem(scanner.manufacturer))
                self.scanner_table.setItem(row, 4, QTableWidgetItem(scanner.model))
                self.scanner_table.setItem(row, 5, QTableWidgetItem("✓" if scanner.has_adf else "✗"))
                self.scanner_table.setItem(row, 6, QTableWidgetItem(f"{scanner.max_resolution_dpi} DPI"))

            self.lbl_scanner_count.setText(f"الماسحات: {len(scanners)}")
            self._update_status(f"تم اكتشاف {len(scanners)} ماسح ضوئي")

        def _on_error(error_type, error_msg, tb):
            self._find_button("btn_refresh_scanners").setEnabled(True)
            app_logger.error(f"Error refreshing scanners: {error_msg}")
            self._update_status(f"خطأ في اكتشاف الماسحات: {error_msg}")

        run_in_background(_do_discover, on_finished=_on_done, on_error=_on_error, task_name="scanner_discovery")

    def _get_scan_settings(self):
        """Build ScanSettings from UI controls."""
        from core.device_manager.scanner.scan_engine import (
            ScanSettings, ScanColorMode, ScanSource, ScanFormat, ScanPaperSize,
        )

        row = self.scanner_table.currentRow()
        scanner_name = ""
        if row >= 0:
            scanner_name = self.scanner_table.item(row, 0).text()

        color_map = {0: ScanColorMode.COLOR, 1: ScanColorMode.GRAYSCALE, 2: ScanColorMode.BLACK_WHITE}
        source_map = {0: ScanSource.FLATBED, 1: ScanSource.ADF_FRONT, 2: ScanSource.ADF_DUPLEX}
        format_map = {0: ScanFormat.PNG, 1: ScanFormat.JPEG, 2: ScanFormat.TIFF, 3: ScanFormat.BMP, 4: ScanFormat.PDF}
        paper_map = {0: ScanPaperSize.A4, 1: ScanPaperSize.A3, 2: ScanPaperSize.A5, 3: ScanPaperSize.LETTER, 4: ScanPaperSize.LEGAL, 5: ScanPaperSize.AUTO}

        return ScanSettings(
            scanner_name=scanner_name,
            resolution_dpi=int(self.combo_resolution.currentText()),
            color_mode=color_map.get(self.combo_scan_color.currentIndex(), ScanColorMode.COLOR),
            source=source_map.get(self.combo_scan_source.currentIndex(), ScanSource.FLATBED),
            output_format=format_map.get(self.combo_scan_format.currentIndex(), ScanFormat.PNG),
            paper_size=paper_map.get(self.combo_scan_paper.currentIndex(), ScanPaperSize.A4),
            auto_crop=self.chk_auto_crop.isChecked(),
            auto_deskew=self.chk_auto_deskew.isChecked(),
        )

    def _scan_single(self):
        """Perform a single scan (runs in background thread)."""
        settings = self._get_scan_settings()

        self.scan_progress.setVisible(True)
        self.scan_progress.setValue(0)
        self._update_status("جاري المسح الضوئي...")
        self._find_button("btn_scan").setEnabled(False)

        def _do_scan(progress_callback):
            def on_prog(pct, msg):
                progress_callback(pct, msg)
            return self.scan_engine.scan(settings, on_progress=on_prog)

        def _on_done(result):
            self._find_button("btn_scan").setEnabled(True)
            self.scan_progress.setVisible(False)
            if result.success:
                self._update_status(f"تم المسح: {result.file_path} ({result.file_size_text})")
                self._show_info("نجاح", f"تم المسح الضوئي بنجاح\n{result.file_path}\nالحجم: {result.file_size_text}")
            else:
                self._update_status(f"فشل المسح: {result.error_message}")
                self._show_warning("خطأ", f"فشل المسح الضوئي:\n{result.error_message}")

        def _on_error(error_type, error_msg, tb):
            self._find_button("btn_scan").setEnabled(True)
            self.scan_progress.setVisible(False)
            self._update_status(f"خطأ: {error_msg}")

        def _on_progress(pct, msg):
            self.scan_progress.setValue(pct)
            self._update_status(msg)

        run_in_background(
            _do_scan, use_progress=True,
            on_finished=_on_done, on_error=_on_error, on_progress=_on_progress,
            task_name="scan_single",
        )

    def _batch_scan(self):
        """Perform batch scanning via ADF (runs in background thread)."""
        from core.device_manager.scanner.batch_scanner import BatchScanSettings, OutputMode
        from core.device_manager.scanner.scan_engine import ScanColorMode, ScanSource

        row = self.scanner_table.currentRow()
        scanner_name = self.scanner_table.item(row, 0).text() if row >= 0 else ""

        color_map = {0: ScanColorMode.COLOR, 1: ScanColorMode.GRAYSCALE, 2: ScanColorMode.BLACK_WHITE}

        batch_settings = BatchScanSettings(
            scanner_name=scanner_name,
            resolution_dpi=int(self.combo_resolution.currentText()),
            color_mode=color_map.get(self.combo_scan_color.currentIndex(), ScanColorMode.COLOR),
            source=ScanSource.ADF_FRONT,
            output_mode=OutputMode.SINGLE_PDF,
            auto_crop=self.chk_auto_crop.isChecked(),
            auto_deskew=self.chk_auto_deskew.isChecked(),
        )

        self.scan_progress.setVisible(True)
        self.scan_progress.setValue(0)
        self._update_status("جاري المسح الدفعي...")
        self._find_button("btn_batch_scan").setEnabled(False)

        def _do_batch(progress_callback):
            def on_prog(pct, msg, job):
                progress_callback(pct, msg)
            return self.batch_scanner.start_batch(batch_settings, on_progress=on_prog)

        def _on_done(job):
            self._find_button("btn_batch_scan").setEnabled(True)
            self.scan_progress.setVisible(False)
            if job.status.value == "completed":
                self._update_status(f"تم مسح {job.total_pages_included} صفحة")
                self._show_info(
                    "نجاح",
                    f"تم المسح الدفعي بنجاح\n"
                    f"الصفحات: {job.total_pages_included}\n"
                    f"الملف: {job.output_path}"
                )
            else:
                self._update_status(f"فشل المسح الدفعي: {job.error_message}")

        def _on_error(error_type, error_msg, tb):
            self._find_button("btn_batch_scan").setEnabled(True)
            self.scan_progress.setVisible(False)
            self._update_status(f"خطأ: {error_msg}")

        def _on_progress(pct, msg):
            self.scan_progress.setValue(pct)
            self._update_status(msg)

        run_in_background(
            _do_batch, use_progress=True,
            on_finished=_on_done, on_error=_on_error, on_progress=_on_progress,
            task_name="batch_scan",
        )

    def _scan_to_pdf(self):
        """Scan to searchable PDF with OCR (runs in background thread)."""
        row = self.scanner_table.currentRow()
        scanner_name = self.scanner_table.item(row, 0).text() if row >= 0 else ""

        save_path, _ = QFileDialog.getSaveFileName(
            self, "حفظ PDF", "", "PDF (*.pdf)"
        )
        if not save_path:
            return

        resolution_dpi = int(self.combo_resolution.currentText())
        self.scan_progress.setVisible(True)
        self.scan_progress.setValue(0)
        self._update_status("جاري المسح إلى PDF...")
        self._find_button("btn_scan_to_pdf").setEnabled(False)

        def _do_scan(progress_callback):
            def on_prog(pct, msg):
                progress_callback(pct, msg)
            return self.pdf_bridge.scan_to_searchable_pdf(
                scanner_name=scanner_name,
                output_path=save_path,
                resolution_dpi=resolution_dpi,
                on_progress=on_prog,
            )

        def _on_done(result):
            self._find_button("btn_scan_to_pdf").setEnabled(True)
            self.scan_progress.setVisible(False)
            if result.get('success'):
                self._update_status(f"تم الحفظ: {save_path}")
                self._show_info("نجاح", f"تم المسح وحفظ PDF\n{save_path}")
            else:
                self._update_status(f"فشل: {result.get('error', '')}")

        def _on_error(error_type, error_msg, tb):
            self._find_button("btn_scan_to_pdf").setEnabled(True)
            self.scan_progress.setVisible(False)
            self._update_status(f"خطأ: {error_msg}")

        def _on_progress(pct, msg):
            self.scan_progress.setValue(pct)
            self._update_status(msg)

        run_in_background(
            _do_scan, use_progress=True,
            on_finished=_on_done, on_error=_on_error, on_progress=_on_progress,
            task_name="scan_to_pdf",
        )

    # ═══════════════════════════════════════════════════════
    # Bluetooth Actions
    # ═══════════════════════════════════════════════════════

    def _bt_check_adapter(self):
        """Check Bluetooth adapter status (runs in background thread)."""

        def _do_check():
            return self.bluetooth_manager.get_adapter_status()

        def _on_done(status):
            status_text = {
                'on': "محول البلوتوث: يعمل",
                'off': "محول البلوتوث: متوقف",
                'not_found': "محول البلوتوث: غير موجود",
                'error': "محول البلوتوث: خطأ",
            }.get(status.value, "محول البلوتوث: غير معروف")

            color = {
                'on': '#10b981',
                'off': '#f59e0b',
                'not_found': '#ef4444',
                'error': '#ef4444',
            }.get(status.value, '#6b7280')

            self.lbl_bt_adapter.setText(status_text)
            self.lbl_bt_adapter.setStyleSheet(f"font-size: 14px; color: {color}; font-family: 'Cairo'; font-weight: bold;")

            self.btn_bt_toggle.setText("إيقاف البلوتوث" if status.value == 'on' else "تشغيل البلوتوث")

            if status.value == 'on':
                self._bt_load_paired()

        def _on_error(error_type, error_msg, tb):
            self.lbl_bt_adapter.setText(f"محول البلوتوث: خطأ - {error_msg}")

        run_in_background(_do_check, on_finished=_on_done, on_error=_on_error, task_name="bt_check_adapter")

    def _bt_toggle(self):
        """Toggle Bluetooth adapter on/off (runs in background thread)."""
        self._find_button("btn_bt_toggle").setEnabled(False)

        def _do_toggle():
            status = self.bluetooth_manager.get_adapter_status()
            if status.value == 'on':
                self.bluetooth_manager.disable_adapter()
            else:
                self.bluetooth_manager.enable_adapter()

        def _on_done(_result):
            self._find_button("btn_bt_toggle").setEnabled(True)
            QTimer.singleShot(1000, self._bt_check_adapter)

        def _on_error(error_type, error_msg, tb):
            self._find_button("btn_bt_toggle").setEnabled(True)
            self._update_status(f"خطأ في تبديل البلوتوث: {error_msg}")

        run_in_background(_do_toggle, on_finished=_on_done, on_error=_on_error, task_name="bt_toggle")

    def _bt_discover(self):
        """Discover Bluetooth devices (runs in background thread)."""
        self._update_status("جاري البحث عن أجهزة البلوتوث...")
        self._find_button("btn_bt_scan").setEnabled(False)

        def _do_discover():
            return self.bluetooth_manager.discover_devices(timeout=8)

        def _on_done(devices):
            self._find_button("btn_bt_scan").setEnabled(True)
            self._populate_bt_table(devices)
            self.lbl_bt_count.setText(f"الأجهزة: {len(devices)}")
            self._update_status(f"تم اكتشاف {len(devices)} جهاز بلوتوث")

        def _on_error(error_type, error_msg, tb):
            self._find_button("btn_bt_scan").setEnabled(True)
            self._update_status(f"خطأ في اكتشاف البلوتوث: {error_msg}")

        run_in_background(_do_discover, on_finished=_on_done, on_error=_on_error, task_name="bt_discover")

    def _bt_load_paired(self):
        """Load paired Bluetooth devices (runs in background thread)."""

        def _do_load():
            return self.bluetooth_manager.get_paired_devices()

        def _on_done(devices):
            self._populate_bt_table(devices)
            self.lbl_bt_count.setText(f"الأجهزة: {len(devices)}")

        def _on_error(error_type, error_msg, tb):
            app_logger.error(f"Error loading paired devices: {error_msg}")

        run_in_background(_do_load, on_finished=_on_done, on_error=_on_error, task_name="bt_load_paired")

    def _populate_bt_table(self, devices):
        """Populate Bluetooth devices table."""
        self.bt_table.setRowCount(0)
        for device in devices:
            row = self.bt_table.rowCount()
            self.bt_table.insertRow(row)

            name_item = QTableWidgetItem(f"{device.device_type.icon} {device.display_name}")
            self.bt_table.setItem(row, 0, name_item)

            self.bt_table.setItem(row, 1, QTableWidgetItem(device.device_type.name_ar))

            status_item = QTableWidgetItem(device.status.name_ar)
            self.bt_table.setItem(row, 2, status_item)

            self.bt_table.setItem(row, 3, QTableWidgetItem(device.address))
            self.bt_table.setItem(row, 4, QTableWidgetItem(device.signal_strength_text))
            self.bt_table.setItem(row, 5, QTableWidgetItem(device.battery_text))
            self.bt_table.setItem(row, 6, QTableWidgetItem("✓" if device.is_paired else ""))

    def _bt_pair(self):
        """Pair with selected Bluetooth device (runs in background thread)."""
        row = self.bt_table.currentRow()
        if row < 0:
            self._show_warning("تنبيه", "يرجى اختيار جهاز أولاً")
            return

        address = self.bt_table.item(row, 3).text()
        name = self.bt_table.item(row, 0).text()
        self._update_status(f"جاري الاقتران مع {name}...")
        self._find_button("btn_bt_pair").setEnabled(False)

        def _do_pair():
            return self.bluetooth_manager.pair_device(address)

        def _on_done(success):
            self._find_button("btn_bt_pair").setEnabled(True)
            if success:
                self._update_status(f"تم الاقتران مع {name}")
                self._bt_discover()
            else:
                self._update_status(f"فشل الاقتران مع {name}")

        def _on_error(error_type, error_msg, tb):
            self._find_button("btn_bt_pair").setEnabled(True)
            self._update_status(f"خطأ: {error_msg}")

        run_in_background(_do_pair, on_finished=_on_done, on_error=_on_error, task_name="bt_pair")

    def _bt_connect(self):
        """Connect to selected Bluetooth device (runs in background thread)."""
        row = self.bt_table.currentRow()
        if row < 0:
            self._show_warning("تنبيه", "يرجى اختيار جهاز أولاً")
            return

        address = self.bt_table.item(row, 3).text()
        name = self.bt_table.item(row, 0).text()
        self._update_status(f"جاري الاتصال بـ {name}...")
        self._find_button("btn_bt_connect").setEnabled(False)

        def _do_connect():
            return self.bluetooth_manager.connect_device(address)

        def _on_done(success):
            self._find_button("btn_bt_connect").setEnabled(True)
            if success:
                self._update_status(f"تم الاتصال بـ {name}")
                self._bt_discover()
            else:
                self._update_status(f"فشل الاتصال بـ {name}")

        def _on_error(error_type, error_msg, tb):
            self._find_button("btn_bt_connect").setEnabled(True)
            self._update_status(f"خطأ: {error_msg}")

        run_in_background(_do_connect, on_finished=_on_done, on_error=_on_error, task_name="bt_connect")

    def _bt_disconnect(self):
        """Disconnect from selected Bluetooth device (runs in background thread)."""
        row = self.bt_table.currentRow()
        if row < 0:
            self._show_warning("تنبيه", "يرجى اختيار جهاز أولاً")
            return

        address = self.bt_table.item(row, 3).text()
        name = self.bt_table.item(row, 0).text()
        self._find_button("btn_bt_disconnect").setEnabled(False)

        def _do_disconnect():
            return self.bluetooth_manager.disconnect_device(address)

        def _on_done(success):
            self._find_button("btn_bt_disconnect").setEnabled(True)
            if success:
                self._update_status(f"تم قطع الاتصال بـ {name}")
                self._bt_discover()
            else:
                self._update_status(f"فشل قطع الاتصال بـ {name}")

        def _on_error(error_type, error_msg, tb):
            self._find_button("btn_bt_disconnect").setEnabled(True)
            self._update_status(f"خطأ: {error_msg}")

        run_in_background(_do_disconnect, on_finished=_on_done, on_error=_on_error, task_name="bt_disconnect")

    def _on_bt_selection_changed(self, row, col, prev_row, prev_col):
        """Update device info panel on selection change."""
        if row < 0:
            return

        self.lbl_bt_name.setText(self.bt_table.item(row, 0).text())
        self.lbl_bt_type.setText(self.bt_table.item(row, 1).text())
        self.lbl_bt_mac.setText(self.bt_table.item(row, 3).text())
        self.lbl_bt_signal.setText(self.bt_table.item(row, 4).text())

    # ═══════════════════════════════════════════════════════
    # Helper methods
    # ═══════════════════════════════════════════════════════

    def _make_label(self, text: str) -> QLabel:
        """Create a styled label."""
        label = QLabel(text)
        label.setStyleSheet("font-size: 13px; color: #9ca3af; font-family: 'Cairo';")
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return label

    def _make_value_label(self, text: str) -> QLabel:
        """Create a styled value label."""
        label = QLabel(text)
        label.setStyleSheet("font-size: 14px; font-weight: bold; color: #e5e7eb; font-family: 'Cairo';")
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return label

    def _update_status(self, text: str):
        """Update status bar."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_label.setText(f"[{timestamp}] {text}")

    def _show_info(self, title: str, message: str):
        """Show info message."""
        try:
            from ui.dialogs import show_info
            show_info(self, title, message)
        except ImportError:
            QMessageBox.information(self, title, message)

    def _show_warning(self, title: str, message: str):
        """Show warning message."""
        try:
            from ui.dialogs import show_error
            show_error(self, title, message)
        except ImportError:
            QMessageBox.warning(self, title, message)
