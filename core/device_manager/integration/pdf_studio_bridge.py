"""
PDF Studio Bridge (Q7)
======================
Integration between Device Manager and PDF AI Studio (Track P).

Bridges:
- Scan directly to PDF with OCR
- Print PDFs with advanced settings
- Batch scan → merge into PDF → OCR → save
- Scan → PDF → email (future integration)
"""

import os
import tempfile
from typing import Optional, List, Callable, Dict, Any
from datetime import datetime
from pathlib import Path

from core.logging import app_logger


class PDFStudioBridge:
    """
    Bridge between Device Manager (Track Q) and PDF AI Studio (Track P).

    Combines scanning/printing with PDF processing:
    - Scan to searchable PDF (with OCR)
    - Print PDF with preview
    - Batch scan to PDF with post-processing
    - PDF merge from multiple scans

    Usage:
        bridge = PDFStudioBridge()

        # Scan to searchable PDF
        result = bridge.scan_to_searchable_pdf(
            scanner_name="HP ScanJet",
            output_path="document.pdf",
            ocr_lang="ara+eng",
        )

        # Print PDF with settings
        bridge.print_pdf(
            "document.pdf",
            printer_name="HP LaserJet",
            copies=2,
        )
    """

    def __init__(self):
        self._pdf_studio = None
        self._scan_engine = None
        self._batch_scanner = None
        self._print_manager = None

    @property
    def pdf_studio(self):
        """Lazy-load PDF AI Studio."""
        if self._pdf_studio is None:
            try:
                from core.file_manager.pdf import PDFAIStudio
                self._pdf_studio = PDFAIStudio()
            except ImportError:
                app_logger.warning("PDF AI Studio not available")
        return self._pdf_studio

    @property
    def scan_engine(self):
        """Lazy-load Scan Engine."""
        if self._scan_engine is None:
            from core.device_manager.scanner.scan_engine import ScanEngine
            self._scan_engine = ScanEngine()
        return self._scan_engine

    @property
    def batch_scanner(self):
        """Lazy-load Batch Scanner."""
        if self._batch_scanner is None:
            from core.device_manager.scanner.batch_scanner import BatchScanner
            self._batch_scanner = BatchScanner()
        return self._batch_scanner

    @property
    def print_manager(self):
        """Lazy-load Print Manager."""
        if self._print_manager is None:
            from core.device_manager.printer.print_manager import PrintManager
            self._print_manager = PrintManager()
        return self._print_manager

    def scan_to_searchable_pdf(
        self,
        scanner_name: str = "",
        output_path: str = "",
        resolution_dpi: int = 300,
        ocr_lang: str = "ara+eng",
        auto_deskew: bool = True,
        auto_crop: bool = True,
        on_progress: Optional[Callable[[int, str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Scan document and create a searchable PDF with OCR.

        Args:
            scanner_name: Scanner to use
            output_path: Where to save the final PDF
            resolution_dpi: Scan resolution
            ocr_lang: OCR language (ara, eng, ara+eng)
            auto_deskew: Auto-straighten scanned image
            auto_crop: Auto-crop white borders
            on_progress: Progress callback(percent, message)

        Returns:
            Dict with 'success', 'file_path', 'text', 'pages'
        """
        from core.device_manager.scanner.scan_engine import (
            ScanSettings, ScanFormat, ScanColorMode,
        )

        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join(os.path.expanduser("~"), "INTEGRA_Scans")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"scan_ocr_{timestamp}.pdf")

        try:
            # Step 1: Scan to temporary image
            if on_progress:
                on_progress(10, "جاري المسح الضوئي...")

            scan_settings = ScanSettings(
                scanner_name=scanner_name,
                resolution_dpi=resolution_dpi,
                color_mode=ScanColorMode.COLOR,
                output_format=ScanFormat.PNG,
                auto_deskew=auto_deskew,
                auto_crop=auto_crop,
                output_directory=tempfile.gettempdir(),
                filename_prefix="ocr_scan",
            )

            scan_result = self.scan_engine.scan(scan_settings)

            if not scan_result.success:
                return {
                    'success': False,
                    'error': scan_result.error_message,
                }

            if on_progress:
                on_progress(50, "تحويل إلى PDF...")

            # Step 2: Convert to PDF
            temp_pdf = tempfile.mktemp(suffix='.pdf')

            try:
                from PIL import Image
                img = Image.open(scan_result.file_path)
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                img.save(temp_pdf, 'PDF', resolution=resolution_dpi)
                img.close()
            except ImportError:
                # No PIL - just copy
                import shutil
                shutil.copy2(scan_result.file_path, temp_pdf)

            # Step 3: OCR
            ocr_text = ""
            if self.pdf_studio:
                if on_progress:
                    on_progress(70, "التعرف على النصوص (OCR)...")

                try:
                    doc_id = self.pdf_studio.load(temp_pdf)
                    if doc_id:
                        ocr_results = self.pdf_studio.ocr_document(doc_id, lang=ocr_lang)
                        ocr_text = "\n".join(r.get('text', '') for r in ocr_results)
                except Exception as e:
                    app_logger.warning(f"OCR failed (non-critical): {e}")

            # Step 4: Save final PDF
            if on_progress:
                on_progress(90, "حفظ الملف النهائي...")

            import shutil
            shutil.move(temp_pdf, output_path)

            # Cleanup temp scan
            try:
                os.unlink(scan_result.file_path)
            except OSError:
                pass

            if on_progress:
                on_progress(100, "تم بنجاح!")

            app_logger.info(f"Scan to searchable PDF: {output_path}")

            return {
                'success': True,
                'file_path': output_path,
                'text': ocr_text,
                'pages': 1,
                'file_size': os.path.getsize(output_path),
            }

        except Exception as e:
            app_logger.error(f"Scan to searchable PDF failed: {e}")
            return {
                'success': False,
                'error': str(e),
            }

    def batch_scan_to_pdf(
        self,
        scanner_name: str = "",
        output_path: str = "",
        resolution_dpi: int = 300,
        ocr_lang: str = "ara+eng",
        enable_ocr: bool = True,
        auto_deskew: bool = True,
        blank_page_detection: bool = True,
        on_progress: Optional[Callable[[int, str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Batch scan multiple pages via ADF into a single PDF with OCR.

        Args:
            scanner_name: Scanner name
            output_path: Output PDF path
            resolution_dpi: Scan resolution
            ocr_lang: OCR language
            enable_ocr: Whether to run OCR on the result
            auto_deskew: Auto-straighten pages
            blank_page_detection: Skip blank pages
            on_progress: Progress callback

        Returns:
            Dict with results
        """
        from core.device_manager.scanner.batch_scanner import (
            BatchScanSettings, OutputMode,
        )
        from core.device_manager.scanner.scan_engine import ScanColorMode, ScanSource

        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join(os.path.expanduser("~"), "INTEGRA_Scans")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"batch_scan_{timestamp}.pdf")

        try:
            if on_progress:
                on_progress(5, "إعداد المسح الدفعي...")

            batch_settings = BatchScanSettings(
                scanner_name=scanner_name,
                resolution_dpi=resolution_dpi,
                color_mode=ScanColorMode.COLOR,
                source=ScanSource.ADF_FRONT,
                output_mode=OutputMode.SINGLE_PDF,
                output_directory=os.path.dirname(output_path),
                filename_prefix=Path(output_path).stem,
                auto_deskew=auto_deskew,
                blank_page_detection=blank_page_detection,
            )

            def batch_progress(pct, msg, job):
                if on_progress:
                    # Scale batch progress to 0-70%
                    scaled = int(pct * 0.7)
                    on_progress(scaled, msg)

            batch_job = self.batch_scanner.start_batch(batch_settings, on_progress=batch_progress)

            if batch_job.status.value == "failed":
                return {
                    'success': False,
                    'error': batch_job.error_message,
                }

            # OCR the result if requested
            ocr_text = ""
            if enable_ocr and self.pdf_studio and batch_job.output_path:
                if on_progress:
                    on_progress(75, "التعرف على النصوص (OCR)...")

                try:
                    doc_id = self.pdf_studio.load(batch_job.output_path)
                    if doc_id:
                        ocr_results = self.pdf_studio.ocr_document(doc_id, lang=ocr_lang)
                        ocr_text = "\n".join(r.get('text', '') for r in ocr_results)
                except Exception as e:
                    app_logger.warning(f"OCR on batch scan failed: {e}")

            # Move to desired output path if different
            if batch_job.output_path and batch_job.output_path != output_path:
                import shutil
                shutil.move(batch_job.output_path, output_path)

            if on_progress:
                on_progress(100, f"تم مسح {batch_job.total_pages_included} صفحة")

            return {
                'success': True,
                'file_path': output_path,
                'text': ocr_text,
                'pages': batch_job.total_pages_included,
                'blank_skipped': batch_job.blank_pages_skipped,
                'file_size': os.path.getsize(output_path) if os.path.exists(output_path) else 0,
            }

        except Exception as e:
            app_logger.error(f"Batch scan to PDF failed: {e}")
            return {
                'success': False,
                'error': str(e),
            }

    def print_pdf(
        self,
        file_path: str,
        printer_name: str = "",
        copies: int = 1,
        page_range: str = "",
        duplex: bool = False,
        color: bool = True,
        fit_to_page: bool = False,
        on_progress: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Print a PDF file with advanced settings.

        Args:
            file_path: PDF file path
            printer_name: Target printer
            copies: Number of copies
            page_range: e.g. "1-5,8"
            duplex: Double-sided printing
            color: Color or monochrome
            fit_to_page: Scale to fit page
            on_progress: Progress callback

        Returns:
            Dict with results
        """
        from core.device_manager.printer.print_manager import (
            PrintSettings, ColorMode, DuplexMode,
        )

        if not os.path.exists(file_path):
            return {'success': False, 'error': f'الملف غير موجود: {file_path}'}

        try:
            settings = PrintSettings(
                printer_name=printer_name,
                copies=copies,
                page_range=page_range,
                duplex=DuplexMode.LONG_EDGE if duplex else DuplexMode.NONE,
                color_mode=ColorMode.COLOR if color else ColorMode.MONOCHROME,
                fit_to_page=fit_to_page,
            )

            job = self.print_manager.print_file(file_path, settings)

            return {
                'success': job.status.value == 'completed',
                'job_id': job.job_id,
                'status': job.status_text_ar,
                'error': job.error_message,
            }

        except Exception as e:
            app_logger.error(f"Print PDF failed: {e}")
            return {'success': False, 'error': str(e)}

    def scan_and_merge(
        self,
        scanner_name: str = "",
        existing_pdf: str = "",
        output_path: str = "",
        resolution_dpi: int = 300,
        append: bool = True,
        on_progress: Optional[Callable[[int, str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Scan pages and merge with an existing PDF.

        Args:
            scanner_name: Scanner to use
            existing_pdf: Existing PDF to merge with
            output_path: Output path for merged PDF
            resolution_dpi: Scan resolution
            append: If True, append scan after existing PDF. If False, prepend.
            on_progress: Progress callback

        Returns:
            Dict with results
        """
        from core.device_manager.scanner.scan_engine import (
            ScanSettings, ScanFormat, ScanColorMode,
        )

        if not output_path:
            output_path = existing_pdf  # Overwrite original

        try:
            # Step 1: Scan to temp PDF
            if on_progress:
                on_progress(10, "جاري المسح الضوئي...")

            scan_settings = ScanSettings(
                scanner_name=scanner_name,
                resolution_dpi=resolution_dpi,
                color_mode=ScanColorMode.COLOR,
                output_format=ScanFormat.PDF,
                output_directory=tempfile.gettempdir(),
                filename_prefix="merge_scan",
            )

            scan_result = self.scan_engine.scan(scan_settings)

            if not scan_result.success:
                return {'success': False, 'error': scan_result.error_message}

            # Step 2: Merge PDFs
            if on_progress:
                on_progress(60, "دمج الملفات...")

            if self.pdf_studio:
                if append:
                    merge_files = [existing_pdf, scan_result.file_path]
                else:
                    merge_files = [scan_result.file_path, existing_pdf]

                temp_merged = tempfile.mktemp(suffix='.pdf')
                success = self.pdf_studio.merge(merge_files, temp_merged)

                if success:
                    import shutil
                    shutil.move(temp_merged, output_path)
                else:
                    return {'success': False, 'error': 'فشل دمج الملفات'}
            else:
                # Without PDF Studio, try basic merge with PyPDF2/pikepdf
                try:
                    from PyPDF2 import PdfMerger
                    merger = PdfMerger()
                    if append:
                        merger.append(existing_pdf)
                        merger.append(scan_result.file_path)
                    else:
                        merger.append(scan_result.file_path)
                        merger.append(existing_pdf)
                    merger.write(output_path)
                    merger.close()
                except ImportError:
                    return {'success': False, 'error': 'PDF Studio أو PyPDF2 مطلوب للدمج'}

            # Cleanup
            try:
                os.unlink(scan_result.file_path)
            except OSError:
                pass

            if on_progress:
                on_progress(100, "تم الدمج بنجاح!")

            return {
                'success': True,
                'file_path': output_path,
                'file_size': os.path.getsize(output_path) if os.path.exists(output_path) else 0,
            }

        except Exception as e:
            app_logger.error(f"Scan and merge failed: {e}")
            return {'success': False, 'error': str(e)}

    def scan_to_compressed_pdf(
        self,
        scanner_name: str = "",
        output_path: str = "",
        resolution_dpi: int = 300,
        compression_level: str = "medium",
        on_progress: Optional[Callable[[int, str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Scan and create a compressed PDF.

        Args:
            scanner_name: Scanner name
            output_path: Output path
            resolution_dpi: Scan resolution
            compression_level: 'low', 'medium', 'high'
            on_progress: Progress callback

        Returns:
            Dict with results
        """
        # First scan to PDF
        result = self.scan_to_searchable_pdf(
            scanner_name=scanner_name,
            output_path="",  # temp
            resolution_dpi=resolution_dpi,
            ocr_lang="",  # No OCR for speed
            on_progress=lambda p, m: on_progress(int(p * 0.7), m) if on_progress else None,
        )

        if not result.get('success'):
            return result

        scanned_pdf = result['file_path']

        # Compress using PDF Studio
        if self.pdf_studio and os.path.exists(scanned_pdf):
            if on_progress:
                on_progress(75, "ضغط PDF...")

            try:
                doc_id = self.pdf_studio.load(scanned_pdf)
                if doc_id:
                    if not output_path:
                        output_path = scanned_pdf
                    self.pdf_studio.compress(doc_id, output_path, level=compression_level)

                    original_size = result.get('file_size', 0)
                    compressed_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
                    savings = ((original_size - compressed_size) / original_size * 100) if original_size > 0 else 0

                    if on_progress:
                        on_progress(100, f"تم الضغط - توفير {savings:.0f}%")

                    return {
                        'success': True,
                        'file_path': output_path,
                        'original_size': original_size,
                        'compressed_size': compressed_size,
                        'savings_percent': savings,
                    }
            except Exception as e:
                app_logger.warning(f"Compression failed: {e}")

        # If no compression, just return original
        if not output_path:
            output_path = scanned_pdf
        elif scanned_pdf != output_path:
            import shutil
            shutil.move(scanned_pdf, output_path)

        if on_progress:
            on_progress(100, "تم (بدون ضغط)")

        return {
            'success': True,
            'file_path': output_path,
            'file_size': os.path.getsize(output_path) if os.path.exists(output_path) else 0,
        }
