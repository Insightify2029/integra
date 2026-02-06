"""
Batch Scanner (Q5)
==================
Batch scanning with ADF (Automatic Document Feeder) support.

Features:
- Multi-page scanning via ADF
- Combine pages into single PDF
- Page ordering and re-ordering
- Individual page settings
- Progress tracking per page
"""

import os
import sys
import tempfile
from dataclasses import dataclass, field
from typing import Optional, List, Callable, Dict, Any
from enum import Enum
from datetime import datetime
from pathlib import Path

from core.logging import app_logger
from .scan_engine import ScanEngine, ScanSettings, ScanResult, ScanColorMode, ScanSource, ScanFormat


class BatchStatus(Enum):
    """Batch scan job status."""
    IDLE = "idle"
    SCANNING = "scanning"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def name_ar(self) -> str:
        ar_map = {
            "idle": "جاهز",
            "scanning": "جاري المسح",
            "processing": "جاري المعالجة",
            "completed": "مكتمل",
            "failed": "فشل",
            "cancelled": "ملغي",
        }
        return ar_map.get(self.value, self.value)


class OutputMode(Enum):
    """How to handle multi-page output."""
    SINGLE_PDF = "single_pdf"        # All pages in one PDF
    SEPARATE_FILES = "separate_files"  # Each page as a separate file
    TIFF_MULTIPAGE = "tiff_multipage"  # All pages in one TIFF

    @property
    def name_ar(self) -> str:
        ar_map = {
            "single_pdf": "ملف PDF واحد",
            "separate_files": "ملفات منفصلة",
            "tiff_multipage": "ملف TIFF متعدد الصفحات",
        }
        return ar_map.get(self.value, self.value)


@dataclass
class BatchScanSettings:
    """Settings for a batch scan job."""
    scanner_name: str = ""
    resolution_dpi: int = 300
    color_mode: ScanColorMode = ScanColorMode.COLOR
    source: ScanSource = ScanSource.ADF_FRONT
    output_mode: OutputMode = OutputMode.SINGLE_PDF
    output_format: ScanFormat = ScanFormat.PDF
    output_directory: str = ""
    filename_prefix: str = "batch_scan"
    max_pages: int = 0  # 0 = unlimited (scan until ADF is empty)
    auto_crop: bool = False
    auto_deskew: bool = False
    blank_page_detection: bool = True  # Skip blank pages
    blank_threshold: float = 0.99  # Whiteness threshold for blank detection
    jpeg_quality: int = 85

    @property
    def output_dir(self) -> str:
        if self.output_directory:
            return self.output_directory
        default_dir = os.path.join(os.path.expanduser("~"), "INTEGRA_Scans", "batch")
        os.makedirs(default_dir, exist_ok=True)
        return default_dir


@dataclass
class PageInfo:
    """Information about a scanned page."""
    page_number: int
    file_path: str
    width_px: int = 0
    height_px: int = 0
    file_size_bytes: int = 0
    is_blank: bool = False
    is_included: bool = True  # User can exclude pages


@dataclass
class BatchScanJob:
    """Represents a batch scan job."""
    job_id: str = ""
    status: BatchStatus = BatchStatus.IDLE
    settings: BatchScanSettings = field(default_factory=BatchScanSettings)
    pages: List[PageInfo] = field(default_factory=list)
    output_path: str = ""
    output_paths: List[str] = field(default_factory=list)
    total_pages_scanned: int = 0
    total_pages_included: int = 0
    blank_pages_skipped: int = 0
    total_size_bytes: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: str = ""

    @property
    def progress_percent(self) -> int:
        if self.settings.max_pages > 0:
            return int((self.total_pages_scanned / self.settings.max_pages) * 100)
        return 0

    @property
    def duration_seconds(self) -> float:
        if self.started_at:
            end = self.completed_at or datetime.now()
            return (end - self.started_at).total_seconds()
        return 0.0

    @property
    def status_text_ar(self) -> str:
        return self.status.name_ar


class BatchScanner:
    """
    Batch scanning with ADF support.

    Usage:
        scanner = BatchScanner()

        settings = BatchScanSettings(
            scanner_name="HP ScanJet Pro",
            source=ScanSource.ADF_FRONT,
            output_mode=OutputMode.SINGLE_PDF,
            resolution_dpi=300,
        )

        job = scanner.start_batch(settings, on_progress=my_callback)

        # Check result
        if job.status == BatchStatus.COMPLETED:
            print(f"Scanned {job.total_pages_included} pages to {job.output_path}")
    """

    def __init__(self):
        self._engine = ScanEngine()
        self._job_counter = 0
        self._current_job: Optional[BatchScanJob] = None
        self._cancel_requested = False

    @property
    def is_scanning(self) -> bool:
        """Check if a batch scan is in progress."""
        return self._current_job is not None and self._current_job.status == BatchStatus.SCANNING

    def start_batch(
        self,
        settings: BatchScanSettings,
        on_progress: Optional[Callable[[int, str, BatchScanJob], None]] = None,
        on_page_scanned: Optional[Callable[[PageInfo], None]] = None,
    ) -> BatchScanJob:
        """
        Start a batch scan job.

        Args:
            settings: Batch scan configuration
            on_progress: Progress callback(percent, message, job)
            on_page_scanned: Called after each page is scanned

        Returns:
            BatchScanJob with results
        """
        self._cancel_requested = False
        self._job_counter += 1

        job = BatchScanJob(
            job_id=f"BATCH-{self._job_counter:04d}",
            settings=settings,
            status=BatchStatus.SCANNING,
            started_at=datetime.now(),
        )
        self._current_job = job

        try:
            if on_progress:
                on_progress(0, "بدء المسح الدفعي...", job)

            # Scan pages
            temp_dir = tempfile.mkdtemp(prefix="integra_batch_")
            page_files = []
            page_num = 0

            while True:
                if self._cancel_requested:
                    job.status = BatchStatus.CANCELLED
                    app_logger.info(f"Batch scan cancelled: {job.job_id}")
                    break

                if settings.max_pages > 0 and page_num >= settings.max_pages:
                    break

                page_num += 1
                page_settings = ScanSettings(
                    scanner_name=settings.scanner_name,
                    resolution_dpi=settings.resolution_dpi,
                    color_mode=settings.color_mode,
                    source=settings.source,
                    output_format=ScanFormat.PNG,  # Intermediate format
                    auto_crop=settings.auto_crop,
                    auto_deskew=settings.auto_deskew,
                    output_directory=temp_dir,
                    filename_prefix=f"page_{page_num:04d}",
                )

                if on_progress:
                    progress = int((page_num / max(settings.max_pages, page_num + 5)) * 80)
                    on_progress(progress, f"مسح الصفحة {page_num}...", job)

                result = self._engine.scan(page_settings)

                if not result.success:
                    # ADF might be empty - this is normal end of batch
                    if 'empty' in result.error_message.lower() or \
                       'no document' in result.error_message.lower() or \
                       'paper' in result.error_message.lower():
                        app_logger.info(f"ADF empty after {page_num - 1} pages")
                        break
                    else:
                        app_logger.warning(f"Page {page_num} scan failed: {result.error_message}")
                        if page_num == 1:
                            # First page failed - abort
                            job.status = BatchStatus.FAILED
                            job.error_message = result.error_message
                            return job
                        break

                # Check for blank page
                is_blank = False
                if settings.blank_page_detection:
                    is_blank = self._is_blank_page(result.file_path, settings.blank_threshold)

                page_info = PageInfo(
                    page_number=page_num,
                    file_path=result.file_path,
                    width_px=result.width_px,
                    height_px=result.height_px,
                    file_size_bytes=result.file_size_bytes,
                    is_blank=is_blank,
                    is_included=not is_blank,
                )

                job.pages.append(page_info)
                job.total_pages_scanned = page_num

                if is_blank:
                    job.blank_pages_skipped += 1
                else:
                    page_files.append(result.file_path)
                    job.total_pages_included += 1

                if on_page_scanned:
                    on_page_scanned(page_info)

            # Process pages into final output
            if job.status != BatchStatus.CANCELLED and page_files:
                job.status = BatchStatus.PROCESSING

                if on_progress:
                    on_progress(85, "معالجة الصفحات...", job)

                included_pages = [p.file_path for p in job.pages if p.is_included]

                if settings.output_mode == OutputMode.SINGLE_PDF:
                    output_path = self._combine_to_pdf(included_pages, settings)
                    job.output_path = output_path
                    job.output_paths = [output_path]

                elif settings.output_mode == OutputMode.TIFF_MULTIPAGE:
                    output_path = self._combine_to_tiff(included_pages, settings)
                    job.output_path = output_path
                    job.output_paths = [output_path]

                elif settings.output_mode == OutputMode.SEPARATE_FILES:
                    output_paths = self._save_separate_files(included_pages, settings)
                    job.output_paths = output_paths
                    job.output_path = output_paths[0] if output_paths else ""

                # Calculate total size
                for path in job.output_paths:
                    if os.path.exists(path):
                        job.total_size_bytes += os.path.getsize(path)

                if job.status != BatchStatus.CANCELLED:
                    job.status = BatchStatus.COMPLETED

            elif not page_files and job.status != BatchStatus.CANCELLED:
                job.status = BatchStatus.FAILED
                job.error_message = "لم يتم مسح أي صفحات"

            job.completed_at = datetime.now()

            if on_progress:
                final_msg = f"تم مسح {job.total_pages_included} صفحة" if job.status == BatchStatus.COMPLETED else "فشل المسح الدفعي"
                on_progress(100, final_msg, job)

            app_logger.info(
                f"Batch scan {job.job_id}: {job.total_pages_scanned} scanned, "
                f"{job.total_pages_included} included, "
                f"{job.blank_pages_skipped} blank skipped"
            )

        except Exception as e:
            job.status = BatchStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()
            app_logger.error(f"Batch scan error: {e}")

        finally:
            self._current_job = None

        return job

    def cancel(self):
        """Cancel the current batch scan."""
        self._cancel_requested = True
        if self._current_job:
            app_logger.info(f"Cancel requested for {self._current_job.job_id}")

    def reorder_pages(self, job: BatchScanJob, new_order: List[int]) -> BatchScanJob:
        """
        Reorder pages in a batch scan job.

        Args:
            job: The batch scan job
            new_order: List of page numbers in desired order

        Returns:
            Updated job with reordered pages
        """
        page_map = {p.page_number: p for p in job.pages}
        reordered = []
        for num in new_order:
            if num in page_map:
                reordered.append(page_map[num])
        job.pages = reordered
        return job

    def exclude_page(self, job: BatchScanJob, page_number: int) -> BatchScanJob:
        """Exclude a page from the final output."""
        for page in job.pages:
            if page.page_number == page_number:
                page.is_included = False
                job.total_pages_included = sum(1 for p in job.pages if p.is_included)
                break
        return job

    def include_page(self, job: BatchScanJob, page_number: int) -> BatchScanJob:
        """Re-include a previously excluded page."""
        for page in job.pages:
            if page.page_number == page_number:
                page.is_included = True
                job.total_pages_included = sum(1 for p in job.pages if p.is_included)
                break
        return job

    def rebuild_output(
        self,
        job: BatchScanJob,
        on_progress: Optional[Callable] = None,
    ) -> BatchScanJob:
        """Rebuild the output file(s) with current page selection/order."""
        settings = job.settings
        included_pages = [p.file_path for p in job.pages if p.is_included]

        if not included_pages:
            job.error_message = "لا توجد صفحات محددة"
            return job

        if settings.output_mode == OutputMode.SINGLE_PDF:
            output_path = self._combine_to_pdf(included_pages, settings)
            job.output_path = output_path
            job.output_paths = [output_path]
        elif settings.output_mode == OutputMode.TIFF_MULTIPAGE:
            output_path = self._combine_to_tiff(included_pages, settings)
            job.output_path = output_path
            job.output_paths = [output_path]
        elif settings.output_mode == OutputMode.SEPARATE_FILES:
            output_paths = self._save_separate_files(included_pages, settings)
            job.output_paths = output_paths
            job.output_path = output_paths[0] if output_paths else ""

        job.total_size_bytes = sum(
            os.path.getsize(p) for p in job.output_paths if os.path.exists(p)
        )

        return job

    # ═══════════════════════════════════════════════════════
    # Helper methods
    # ═══════════════════════════════════════════════════════

    def _is_blank_page(self, image_path: str, threshold: float = 0.99) -> bool:
        """Detect if a scanned page is blank."""
        try:
            from PIL import Image
            import numpy as np

            img = Image.open(image_path).convert('L')
            arr = np.array(img)
            white_ratio = (arr > 240).sum() / arr.size
            return white_ratio > threshold

        except ImportError:
            # Without numpy/PIL, assume page is not blank
            return False

    def _combine_to_pdf(self, page_files: List[str], settings: BatchScanSettings) -> str:
        """Combine multiple page images into a single PDF."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(
            settings.output_dir,
            f"{settings.filename_prefix}_{timestamp}.pdf"
        )

        try:
            from PIL import Image

            images = []
            for f in page_files:
                img = Image.open(f)
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                images.append(img)

            if images:
                first = images[0]
                rest = images[1:] if len(images) > 1 else []
                first.save(
                    output_path, 'PDF',
                    save_all=True,
                    append_images=rest,
                    resolution=settings.resolution_dpi,
                )

                # Close images
                for img in images:
                    img.close()

            app_logger.info(f"Combined {len(page_files)} pages to PDF: {output_path}")

        except ImportError:
            app_logger.error("Pillow required for PDF creation")
            raise RuntimeError("مكتبة Pillow مطلوبة لإنشاء PDF")

        return output_path

    def _combine_to_tiff(self, page_files: List[str], settings: BatchScanSettings) -> str:
        """Combine multiple page images into a multi-page TIFF."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(
            settings.output_dir,
            f"{settings.filename_prefix}_{timestamp}.tiff"
        )

        try:
            from PIL import Image

            images = []
            for f in page_files:
                images.append(Image.open(f))

            if images:
                first = images[0]
                rest = images[1:] if len(images) > 1 else []
                first.save(
                    output_path, 'TIFF',
                    save_all=True,
                    append_images=rest,
                    compression='tiff_lzw',
                )
                for img in images:
                    img.close()

            app_logger.info(f"Combined {len(page_files)} pages to TIFF: {output_path}")

        except ImportError:
            raise RuntimeError("مكتبة Pillow مطلوبة لإنشاء TIFF")

        return output_path

    def _save_separate_files(self, page_files: List[str], settings: BatchScanSettings) -> List[str]:
        """Save pages as separate files in target format."""
        output_paths = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            from PIL import Image

            for i, f in enumerate(page_files, 1):
                img = Image.open(f)
                filename = f"{settings.filename_prefix}_{timestamp}_p{i:03d}{settings.output_format.extension}"
                out_path = os.path.join(settings.output_dir, filename)

                if settings.output_format == ScanFormat.JPEG:
                    if img.mode == 'RGBA':
                        img = img.convert('RGB')
                    img.save(out_path, 'JPEG', quality=settings.jpeg_quality)
                elif settings.output_format == ScanFormat.PDF:
                    if img.mode == 'RGBA':
                        img = img.convert('RGB')
                    img.save(out_path, 'PDF', resolution=settings.resolution_dpi)
                elif settings.output_format == ScanFormat.TIFF:
                    img.save(out_path, 'TIFF', compression='tiff_lzw')
                else:
                    img.save(out_path)

                img.close()
                output_paths.append(out_path)

        except ImportError:
            # Without Pillow, just copy files
            import shutil
            for i, f in enumerate(page_files, 1):
                filename = f"{settings.filename_prefix}_{timestamp}_p{i:03d}.png"
                out_path = os.path.join(settings.output_dir, filename)
                shutil.copy2(f, out_path)
                output_paths.append(out_path)

        return output_paths
