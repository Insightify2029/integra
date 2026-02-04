"""
Report Preview & Print
======================
Preview and print functionality for reports.

Features:
- HTML/PDF preview in PyQt5 window
- Print with system dialog
- Page navigation
- Zoom controls
- Export options
- Print settings
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QToolBar,
    QAction, QLabel, QSpinBox, QComboBox, QPushButton,
    QFileDialog, QMessageBox, QStatusBar, QProgressBar,
    QDialog, QDialogButtonBox, QFormLayout, QCheckBox,
    QGroupBox, QRadioButton
)
from PyQt5.QtCore import Qt, QUrl, QSize, pyqtSignal
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog

from core.logging import app_logger


class PreviewMode(Enum):
    """Preview display mode."""
    FIT_WIDTH = "fit_width"
    FIT_PAGE = "fit_page"
    ACTUAL_SIZE = "actual_size"
    CUSTOM = "custom"


@dataclass
class PrintConfig:
    """Print configuration."""

    # Paper
    paper_size: str = "A4"
    orientation: str = "portrait"

    # Margins (mm)
    margin_top: float = 10
    margin_bottom: float = 10
    margin_left: float = 10
    margin_right: float = 10

    # Print options
    color_mode: str = "color"  # color, grayscale
    copies: int = 1
    collate: bool = True
    duplex: bool = False

    # Page range
    print_all: bool = True
    from_page: int = 1
    to_page: int = 0

    # Header/Footer
    print_header: bool = True
    print_footer: bool = True


class PrintSettingsDialog(QDialog):
    """Dialog for print settings."""

    def __init__(self, config: PrintConfig = None, parent=None):
        super().__init__(parent)
        self._config = config or PrintConfig()

        self.setWindowTitle("إعدادات الطباعة")
        self.setModal(True)
        self.setMinimumWidth(400)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup dialog UI."""
        layout = QVBoxLayout(self)

        # Paper settings
        paper_group = QGroupBox("إعدادات الورق")
        paper_layout = QFormLayout(paper_group)

        self._paper_combo = QComboBox()
        self._paper_combo.addItems(["A4", "A3", "A5", "Letter", "Legal"])
        self._paper_combo.setCurrentText(self._config.paper_size)
        paper_layout.addRow("حجم الورق:", self._paper_combo)

        orient_layout = QHBoxLayout()
        self._portrait_radio = QRadioButton("عمودي")
        self._landscape_radio = QRadioButton("أفقي")
        if self._config.orientation == "portrait":
            self._portrait_radio.setChecked(True)
        else:
            self._landscape_radio.setChecked(True)
        orient_layout.addWidget(self._portrait_radio)
        orient_layout.addWidget(self._landscape_radio)
        paper_layout.addRow("الاتجاه:", orient_layout)

        layout.addWidget(paper_group)

        # Margins
        margins_group = QGroupBox("الهوامش (مم)")
        margins_layout = QFormLayout(margins_group)

        self._margin_top = QSpinBox()
        self._margin_top.setRange(0, 100)
        self._margin_top.setValue(int(self._config.margin_top))
        margins_layout.addRow("أعلى:", self._margin_top)

        self._margin_bottom = QSpinBox()
        self._margin_bottom.setRange(0, 100)
        self._margin_bottom.setValue(int(self._config.margin_bottom))
        margins_layout.addRow("أسفل:", self._margin_bottom)

        self._margin_left = QSpinBox()
        self._margin_left.setRange(0, 100)
        self._margin_left.setValue(int(self._config.margin_left))
        margins_layout.addRow("يسار:", self._margin_left)

        self._margin_right = QSpinBox()
        self._margin_right.setRange(0, 100)
        self._margin_right.setValue(int(self._config.margin_right))
        margins_layout.addRow("يمين:", self._margin_right)

        layout.addWidget(margins_group)

        # Print options
        options_group = QGroupBox("خيارات الطباعة")
        options_layout = QFormLayout(options_group)

        self._copies_spin = QSpinBox()
        self._copies_spin.setRange(1, 100)
        self._copies_spin.setValue(self._config.copies)
        options_layout.addRow("عدد النسخ:", self._copies_spin)

        self._color_combo = QComboBox()
        self._color_combo.addItems(["ألوان", "أبيض وأسود"])
        self._color_combo.setCurrentIndex(0 if self._config.color_mode == "color" else 1)
        options_layout.addRow("وضع اللون:", self._color_combo)

        self._collate_check = QCheckBox("ترتيب النسخ")
        self._collate_check.setChecked(self._config.collate)
        options_layout.addRow("", self._collate_check)

        self._duplex_check = QCheckBox("طباعة على الوجهين")
        self._duplex_check.setChecked(self._config.duplex)
        options_layout.addRow("", self._duplex_check)

        layout.addWidget(options_group)

        # Header/Footer
        hf_group = QGroupBox("الرأس والتذييل")
        hf_layout = QVBoxLayout(hf_group)

        self._header_check = QCheckBox("طباعة الرأس")
        self._header_check.setChecked(self._config.print_header)
        hf_layout.addWidget(self._header_check)

        self._footer_check = QCheckBox("طباعة التذييل")
        self._footer_check.setChecked(self._config.print_footer)
        hf_layout.addWidget(self._footer_check)

        layout.addWidget(hf_group)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_config(self) -> PrintConfig:
        """Get configured settings."""
        return PrintConfig(
            paper_size=self._paper_combo.currentText(),
            orientation="portrait" if self._portrait_radio.isChecked() else "landscape",
            margin_top=self._margin_top.value(),
            margin_bottom=self._margin_bottom.value(),
            margin_left=self._margin_left.value(),
            margin_right=self._margin_right.value(),
            color_mode="color" if self._color_combo.currentIndex() == 0 else "grayscale",
            copies=self._copies_spin.value(),
            collate=self._collate_check.isChecked(),
            duplex=self._duplex_check.isChecked(),
            print_header=self._header_check.isChecked(),
            print_footer=self._footer_check.isChecked()
        )


class ReportPreviewWindow(QMainWindow):
    """
    Report preview window.

    Displays HTML reports with print and export capabilities.
    """

    # Signals
    print_requested = pyqtSignal()
    export_requested = pyqtSignal(str)  # format

    def __init__(
        self,
        html_content: str = "",
        title: str = "معاينة التقرير",
        parent=None
    ):
        super().__init__(parent)

        self._html_content = html_content
        self._title = title
        self._temp_file: Optional[str] = None
        self._print_config = PrintConfig()
        self._zoom_level = 100

        self._setup_ui()
        self._setup_toolbar()
        self._setup_statusbar()

        if html_content:
            self.set_content(html_content)

        app_logger.info("ReportPreviewWindow initialized")

    def _setup_ui(self) -> None:
        """Setup window UI."""
        self.setWindowTitle(self._title)
        self.setMinimumSize(900, 700)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        # Web view for preview
        self._web_view = QWebEngineView()
        self._web_view.setContextMenuPolicy(Qt.NoContextMenu)
        layout.addWidget(self._web_view)

        self.setCentralWidget(central)

        # Style
        self.setStyleSheet("""
            QMainWindow {
                background: #f3f4f6;
            }
            QToolBar {
                background: #ffffff;
                border-bottom: 1px solid #e5e7eb;
                padding: 6px;
                spacing: 8px;
            }
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                background: white;
            }
            QPushButton:hover {
                background: #f3f4f6;
            }
            QPushButton:pressed {
                background: #e5e7eb;
            }
        """)

    def _setup_toolbar(self) -> None:
        """Setup toolbar."""
        toolbar = QToolBar("الأدوات")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)

        # Print
        print_btn = QPushButton("🖨️ طباعة")
        print_btn.clicked.connect(self._print)
        toolbar.addWidget(print_btn)

        print_settings_btn = QPushButton("⚙️ إعدادات")
        print_settings_btn.clicked.connect(self._show_print_settings)
        toolbar.addWidget(print_settings_btn)

        toolbar.addSeparator()

        # Export
        export_pdf_btn = QPushButton("📄 PDF")
        export_pdf_btn.clicked.connect(lambda: self._export("pdf"))
        toolbar.addWidget(export_pdf_btn)

        export_html_btn = QPushButton("🌐 HTML")
        export_html_btn.clicked.connect(lambda: self._export("html"))
        toolbar.addWidget(export_html_btn)

        toolbar.addSeparator()

        # Zoom
        zoom_out_btn = QPushButton("-")
        zoom_out_btn.setFixedWidth(30)
        zoom_out_btn.clicked.connect(self._zoom_out)
        toolbar.addWidget(zoom_out_btn)

        self._zoom_label = QLabel("100%")
        self._zoom_label.setAlignment(Qt.AlignCenter)
        self._zoom_label.setMinimumWidth(50)
        toolbar.addWidget(self._zoom_label)

        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setFixedWidth(30)
        zoom_in_btn.clicked.connect(self._zoom_in)
        toolbar.addWidget(zoom_in_btn)

        zoom_reset_btn = QPushButton("↺")
        zoom_reset_btn.setFixedWidth(30)
        zoom_reset_btn.setToolTip("إعادة تعيين التكبير")
        zoom_reset_btn.clicked.connect(self._zoom_reset)
        toolbar.addWidget(zoom_reset_btn)

        toolbar.addSeparator()

        # View modes
        fit_width_btn = QPushButton("⬌ ملائمة العرض")
        fit_width_btn.clicked.connect(self._fit_width)
        toolbar.addWidget(fit_width_btn)

        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(spacer.sizePolicy().Expanding, spacer.sizePolicy().Preferred)
        toolbar.addWidget(spacer)

        # Close
        close_btn = QPushButton("✕ إغلاق")
        close_btn.clicked.connect(self.close)
        toolbar.addWidget(close_btn)

    def _setup_statusbar(self) -> None:
        """Setup status bar."""
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)

        self._status_label = QLabel("جاهز")
        self._statusbar.addWidget(self._status_label)

    def set_content(self, html_content: str) -> None:
        """
        Set HTML content to preview.

        Args:
            html_content: HTML string
        """
        self._html_content = html_content

        # Create temp file for web view
        self._temp_file = tempfile.mktemp(suffix=".html")
        with open(self._temp_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        self._web_view.setUrl(QUrl.fromLocalFile(self._temp_file))

    def set_url(self, url: str) -> None:
        """
        Set URL to preview.

        Args:
            url: URL string
        """
        self._web_view.setUrl(QUrl(url))

    def set_file(self, file_path: str) -> None:
        """
        Set file to preview.

        Args:
            file_path: Path to HTML or PDF file
        """
        if Path(file_path).suffix.lower() == '.pdf':
            # For PDF, use pdf.js or system viewer
            self._open_pdf(file_path)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.set_content(f.read())

    def _print(self) -> None:
        """Open print dialog."""
        printer = QPrinter(QPrinter.HighResolution)

        # Apply config
        if self._print_config.paper_size == "A4":
            printer.setPageSize(QPrinter.A4)
        elif self._print_config.paper_size == "A3":
            printer.setPageSize(QPrinter.A3)
        elif self._print_config.paper_size == "Letter":
            printer.setPageSize(QPrinter.Letter)

        if self._print_config.orientation == "landscape":
            printer.setOrientation(QPrinter.Landscape)
        else:
            printer.setOrientation(QPrinter.Portrait)

        printer.setCopyCount(self._print_config.copies)
        printer.setCollateCopies(self._print_config.collate)

        if self._print_config.duplex:
            printer.setDuplex(QPrinter.DuplexLongSide)

        if self._print_config.color_mode == "grayscale":
            printer.setColorMode(QPrinter.GrayScale)

        # Show dialog
        dialog = QPrintDialog(printer, self)
        if dialog.exec_() == QDialog.Accepted:
            self._web_view.page().print(printer, lambda ok: self._on_print_finished(ok))

    def _on_print_finished(self, success: bool) -> None:
        """Handle print completion."""
        if success:
            self._status_label.setText("تم إرسال المهمة للطباعة")
            self.print_requested.emit()
        else:
            self._status_label.setText("فشلت الطباعة")

    def _show_print_settings(self) -> None:
        """Show print settings dialog."""
        dialog = PrintSettingsDialog(self._print_config, self)
        if dialog.exec_() == QDialog.Accepted:
            self._print_config = dialog.get_config()

    def _export(self, format_type: str) -> None:
        """Export to file."""
        if format_type == "pdf":
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "تصدير PDF",
                "",
                "ملفات PDF (*.pdf)"
            )

            if file_path:
                if not file_path.endswith('.pdf'):
                    file_path += '.pdf'

                # Use web engine to print to PDF
                page_layout = self._web_view.page()
                page_layout.printToPdf(file_path)

                self._status_label.setText(f"تم التصدير: {file_path}")
                self.export_requested.emit("pdf")

        elif format_type == "html":
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "تصدير HTML",
                "",
                "ملفات HTML (*.html)"
            )

            if file_path:
                if not file_path.endswith('.html'):
                    file_path += '.html'

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self._html_content)

                self._status_label.setText(f"تم التصدير: {file_path}")
                self.export_requested.emit("html")

    def _zoom_in(self) -> None:
        """Zoom in."""
        self._zoom_level = min(300, self._zoom_level + 10)
        self._apply_zoom()

    def _zoom_out(self) -> None:
        """Zoom out."""
        self._zoom_level = max(25, self._zoom_level - 10)
        self._apply_zoom()

    def _zoom_reset(self) -> None:
        """Reset zoom."""
        self._zoom_level = 100
        self._apply_zoom()

    def _apply_zoom(self) -> None:
        """Apply current zoom level."""
        self._web_view.setZoomFactor(self._zoom_level / 100)
        self._zoom_label.setText(f"{self._zoom_level}%")

    def _fit_width(self) -> None:
        """Fit content to window width."""
        # Calculate zoom to fit width
        view_width = self._web_view.width()
        # Assume standard A4 width (595 points)
        ideal_zoom = (view_width / 595) * 100
        self._zoom_level = int(min(150, max(50, ideal_zoom)))
        self._apply_zoom()

    def _open_pdf(self, file_path: str) -> None:
        """Open PDF file."""
        # Use system default PDF viewer
        import subprocess
        import platform

        if platform.system() == 'Windows':
            os.startfile(file_path)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.run(['open', file_path])
        else:  # Linux
            subprocess.run(['xdg-open', file_path])

    def closeEvent(self, event) -> None:
        """Clean up on close."""
        # Remove temp file
        if self._temp_file and os.path.exists(self._temp_file):
            try:
                os.remove(self._temp_file)
            except Exception:
                pass

        event.accept()


def preview_html(
    html_content: str,
    title: str = "معاينة التقرير",
    parent=None
) -> ReportPreviewWindow:
    """
    Open preview window for HTML content.

    Args:
        html_content: HTML string
        title: Window title
        parent: Parent widget

    Returns:
        Preview window instance
    """
    window = ReportPreviewWindow(html_content, title, parent)
    window.show()
    return window


def preview_file(
    file_path: str,
    title: str = "معاينة التقرير",
    parent=None
) -> ReportPreviewWindow:
    """
    Open preview window for file.

    Args:
        file_path: Path to HTML/PDF file
        title: Window title
        parent: Parent widget

    Returns:
        Preview window instance
    """
    window = ReportPreviewWindow(title=title, parent=parent)
    window.set_file(file_path)
    window.show()
    return window


def print_html(
    html_content: str,
    config: PrintConfig = None,
    show_dialog: bool = True,
    parent=None
) -> bool:
    """
    Print HTML content.

    Args:
        html_content: HTML string
        config: Print configuration
        show_dialog: Show print dialog
        parent: Parent widget

    Returns:
        True if print was initiated
    """
    window = ReportPreviewWindow(html_content, parent=parent)
    window.hide()

    if config:
        window._print_config = config

    window._print()
    return True
