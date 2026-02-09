"""
Print Manager (Q2)
==================
Print preview, settings, and print job management.

Supports:
- Print preview with page layout
- Configurable print settings (paper size, orientation, margins, copies)
- Print job queue management
- Direct printing and PDF export
"""

import os
import sys
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable
from enum import Enum
from datetime import datetime
from pathlib import Path

from core.logging import app_logger
from core.device_manager.subprocess_utils import HIDDEN_STARTUPINFO


class PaperSize(Enum):
    """Standard paper sizes."""
    A4 = ("A4", 210, 297)
    A3 = ("A3", 297, 420)
    A5 = ("A5", 148, 210)
    LETTER = ("Letter", 216, 279)
    LEGAL = ("Legal", 216, 356)
    B5 = ("B5", 176, 250)

    def __init__(self, label: str, width_mm: int, height_mm: int):
        self.label = label
        self.width_mm = width_mm
        self.height_mm = height_mm

    @property
    def name_ar(self) -> str:
        """Arabic name."""
        ar_map = {
            "A4": "A4 قياسي",
            "A3": "A3 كبير",
            "A5": "A5 صغير",
            "Letter": "Letter أمريكي",
            "Legal": "Legal قانوني",
            "B5": "B5 متوسط",
        }
        return ar_map.get(self.label, self.label)


class Orientation(Enum):
    """Page orientation."""
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"

    @property
    def name_ar(self) -> str:
        if self == Orientation.PORTRAIT:
            return "عمودي"
        return "أفقي"


class PrintQuality(Enum):
    """Print quality levels."""
    DRAFT = ("draft", 150)
    NORMAL = ("normal", 300)
    HIGH = ("high", 600)
    BEST = ("best", 1200)

    def __init__(self, label: str, dpi: int):
        self.label = label
        self.dpi = dpi

    @property
    def name_ar(self) -> str:
        ar_map = {
            "draft": "مسودة",
            "normal": "عادي",
            "high": "عالي",
            "best": "أفضل جودة",
        }
        return ar_map.get(self.label, self.label)


class ColorMode(Enum):
    """Print color mode."""
    COLOR = "color"
    GRAYSCALE = "grayscale"
    MONOCHROME = "monochrome"

    @property
    def name_ar(self) -> str:
        ar_map = {
            "color": "ألوان",
            "grayscale": "تدرج رمادي",
            "monochrome": "أبيض وأسود",
        }
        return ar_map.get(self.value, self.value)


class DuplexMode(Enum):
    """Duplex printing mode."""
    NONE = "none"
    LONG_EDGE = "long_edge"
    SHORT_EDGE = "short_edge"

    @property
    def name_ar(self) -> str:
        ar_map = {
            "none": "وجه واحد",
            "long_edge": "وجهين - الحافة الطويلة",
            "short_edge": "وجهين - الحافة القصيرة",
        }
        return ar_map.get(self.value, self.value)


@dataclass
class PrintSettings:
    """Print job settings."""
    printer_name: str = ""
    paper_size: PaperSize = PaperSize.A4
    orientation: Orientation = Orientation.PORTRAIT
    quality: PrintQuality = PrintQuality.NORMAL
    color_mode: ColorMode = ColorMode.COLOR
    duplex: DuplexMode = DuplexMode.NONE
    copies: int = 1
    collate: bool = True
    margin_top_mm: float = 10.0
    margin_bottom_mm: float = 10.0
    margin_left_mm: float = 10.0
    margin_right_mm: float = 10.0
    page_range: str = ""  # e.g. "1-5,8,10-12" or empty for all
    scale_percent: int = 100  # 10-400%
    fit_to_page: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'printer_name': self.printer_name,
            'paper_size': self.paper_size.label,
            'orientation': self.orientation.value,
            'quality': self.quality.label,
            'color_mode': self.color_mode.value,
            'duplex': self.duplex.value,
            'copies': self.copies,
            'collate': self.collate,
            'margins': {
                'top': self.margin_top_mm,
                'bottom': self.margin_bottom_mm,
                'left': self.margin_left_mm,
                'right': self.margin_right_mm,
            },
            'page_range': self.page_range,
            'scale_percent': self.scale_percent,
            'fit_to_page': self.fit_to_page,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PrintSettings':
        """Create from dictionary."""
        settings = cls()
        settings.printer_name = data.get('printer_name', '')
        settings.copies = data.get('copies', 1)
        settings.collate = data.get('collate', True)
        settings.page_range = data.get('page_range', '')
        settings.scale_percent = data.get('scale_percent', 100)
        settings.fit_to_page = data.get('fit_to_page', False)

        # Enums
        paper = data.get('paper_size', 'A4')
        for ps in PaperSize:
            if ps.label == paper:
                settings.paper_size = ps
                break

        orient = data.get('orientation', 'portrait')
        for o in Orientation:
            if o.value == orient:
                settings.orientation = o
                break

        quality = data.get('quality', 'normal')
        for q in PrintQuality:
            if q.label == quality:
                settings.quality = q
                break

        color = data.get('color_mode', 'color')
        for c in ColorMode:
            if c.value == color:
                settings.color_mode = c
                break

        duplex = data.get('duplex', 'none')
        for d in DuplexMode:
            if d.value == duplex:
                settings.duplex = d
                break

        margins = data.get('margins', {})
        settings.margin_top_mm = margins.get('top', 10.0)
        settings.margin_bottom_mm = margins.get('bottom', 10.0)
        settings.margin_left_mm = margins.get('left', 10.0)
        settings.margin_right_mm = margins.get('right', 10.0)

        return settings


class PrintJobStatus(Enum):
    """Print job status."""
    PENDING = "pending"
    PRINTING = "printing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PrintJob:
    """Represents a print job."""
    job_id: str = ""
    file_path: str = ""
    printer_name: str = ""
    settings: PrintSettings = field(default_factory=PrintSettings)
    status: PrintJobStatus = PrintJobStatus.PENDING
    pages_total: int = 0
    pages_printed: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error_message: str = ""

    @property
    def progress_percent(self) -> int:
        """Get print progress percentage."""
        if self.pages_total == 0:
            return 0
        return int((self.pages_printed / self.pages_total) * 100)

    @property
    def status_text_ar(self) -> str:
        """Arabic status text."""
        ar_map = {
            PrintJobStatus.PENDING: "في الانتظار",
            PrintJobStatus.PRINTING: "جاري الطباعة",
            PrintJobStatus.COMPLETED: "مكتمل",
            PrintJobStatus.FAILED: "فشل",
            PrintJobStatus.CANCELLED: "ملغي",
        }
        return ar_map.get(self.status, "غير معروف")


class PrintManager:
    """
    Manage print jobs and settings.

    Usage:
        manager = PrintManager()

        # Print a file
        settings = PrintSettings(printer_name="HP LaserJet", copies=2)
        job = manager.print_file("document.pdf", settings)

        # Check status
        print(job.status_text_ar)
    """

    def __init__(self):
        self._jobs: List[PrintJob] = []
        self._job_counter = 0
        self._platform = sys.platform

    def print_file(
        self,
        file_path: str,
        settings: Optional[PrintSettings] = None,
        on_progress: Optional[Callable] = None,
    ) -> PrintJob:
        """
        Print a file with given settings.

        Args:
            file_path: Path to the file to print
            settings: Print settings (uses defaults if None)
            on_progress: Optional progress callback(job)

        Returns:
            PrintJob with status information
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"الملف غير موجود: {file_path}")

        if settings is None:
            settings = PrintSettings()

        self._job_counter += 1
        job = PrintJob(
            job_id=f"JOB-{self._job_counter:04d}",
            file_path=file_path,
            printer_name=settings.printer_name,
            settings=settings,
        )
        self._jobs.append(job)

        try:
            job.status = PrintJobStatus.PRINTING
            if on_progress:
                on_progress(job)

            app_logger.info(f"بدء طباعة: {file_path} على {settings.printer_name}")

            if self._platform == 'win32':
                self._print_windows(job)
            else:
                self._print_linux(job)

            job.status = PrintJobStatus.COMPLETED
            job.completed_at = datetime.now()
            app_logger.info(f"اكتمال الطباعة: {job.job_id}")

        except Exception as e:
            job.status = PrintJobStatus.FAILED
            job.error_message = str(e)
            app_logger.error(f"فشل الطباعة {job.job_id}: {e}")

        if on_progress:
            on_progress(job)

        return job

    def print_text(self, text: str, settings: Optional[PrintSettings] = None) -> PrintJob:
        """Print plain text content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(text)
            temp_path = f.name

        try:
            return self.print_file(temp_path, settings)
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass

    def print_html(self, html: str, settings: Optional[PrintSettings] = None) -> PrintJob:
        """Print HTML content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html)
            temp_path = f.name

        try:
            return self.print_file(temp_path, settings)
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a print job."""
        for job in self._jobs:
            if job.job_id == job_id and job.status in (PrintJobStatus.PENDING, PrintJobStatus.PRINTING):
                job.status = PrintJobStatus.CANCELLED
                app_logger.info(f"إلغاء مهمة الطباعة: {job_id}")
                return True
        return False

    def get_jobs(self) -> List[PrintJob]:
        """Get all print jobs."""
        return self._jobs.copy()

    def get_active_jobs(self) -> List[PrintJob]:
        """Get active (pending/printing) jobs."""
        return [j for j in self._jobs if j.status in (PrintJobStatus.PENDING, PrintJobStatus.PRINTING)]

    def clear_completed(self):
        """Remove completed/failed/cancelled jobs from the list."""
        self._jobs = [j for j in self._jobs if j.status in (PrintJobStatus.PENDING, PrintJobStatus.PRINTING)]

    def parse_page_range(self, page_range: str, total_pages: int) -> List[int]:
        """
        Parse page range string to list of page numbers.

        Args:
            page_range: e.g. "1-5,8,10-12" or "" for all
            total_pages: total number of pages

        Returns:
            Sorted list of page numbers (1-based)
        """
        if not page_range.strip():
            return list(range(1, total_pages + 1))

        pages = set()
        parts = page_range.split(',')
        for part in parts:
            part = part.strip()
            if '-' in part:
                start_str, end_str = part.split('-', 1)
                start = max(1, int(start_str.strip()))
                end = min(total_pages, int(end_str.strip()))
                pages.update(range(start, end + 1))
            else:
                page = int(part)
                if 1 <= page <= total_pages:
                    pages.add(page)

        return sorted(pages)

    # ═══════════════════════════════════════════════════════
    # Platform-specific printing
    # ═══════════════════════════════════════════════════════

    def _print_windows(self, job: PrintJob):
        """Print on Windows."""
        settings = job.settings
        file_path = job.file_path
        ext = Path(file_path).suffix.lower()

        try:
            import win32print
            import win32api

            printer_name = settings.printer_name or win32print.GetDefaultPrinter()

            if ext == '.pdf':
                # Use system association for PDF
                win32api.ShellExecute(
                    0, "print", file_path, f'/d:"{printer_name}"', ".", 0
                )
            elif ext in ('.txt', '.log', '.csv'):
                # Direct raw text printing
                handle = win32print.OpenPrinter(printer_name)
                try:
                    win32print.StartDocPrinter(handle, 1, (f"INTEGRA-{job.job_id}", None, "RAW"))
                    win32print.StartPagePrinter(handle)
                    with open(file_path, 'rb') as f:
                        win32print.WritePrinter(handle, f.read())
                    win32print.EndPagePrinter(handle)
                    win32print.EndDocPrinter(handle)
                finally:
                    win32print.ClosePrinter(handle)
            else:
                # Use ShellExecute for other file types
                win32api.ShellExecute(
                    0, "print", file_path, f'/d:"{printer_name}"', ".", 0
                )

        except ImportError:
            # Fallback to subprocess
            self._print_windows_fallback(job)

    def _print_windows_fallback(self, job: PrintJob):
        """Fallback Windows printing via subprocess."""
        settings = job.settings
        printer_name = settings.printer_name

        cmd = [
            'powershell', '-Command',
            f'Start-Process -FilePath "{job.file_path}" -Verb Print'
        ]
        if printer_name:
            cmd = [
                'powershell', '-Command',
                f'(New-Object -ComObject WScript.Network).SetDefaultPrinter("{printer_name}"); '
                f'Start-Process -FilePath "{job.file_path}" -Verb Print'
            ]

        subprocess.run(cmd, capture_output=True, timeout=30, startupinfo=HIDDEN_STARTUPINFO)

    def _print_linux(self, job: PrintJob):
        """Print on Linux using CUPS/lp."""
        settings = job.settings
        cmd = ['lp']

        if settings.printer_name:
            cmd.extend(['-d', settings.printer_name])

        cmd.extend(['-n', str(settings.copies)])

        if settings.orientation == Orientation.LANDSCAPE:
            cmd.extend(['-o', 'landscape'])

        if settings.duplex != DuplexMode.NONE:
            if settings.duplex == DuplexMode.LONG_EDGE:
                cmd.extend(['-o', 'sides=two-sided-long-edge'])
            else:
                cmd.extend(['-o', 'sides=two-sided-short-edge'])

        if settings.page_range:
            cmd.extend(['-P', settings.page_range])

        if settings.fit_to_page:
            cmd.extend(['-o', 'fit-to-page'])

        cmd.append(job.file_path)

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise RuntimeError(f"lp failed: {result.stderr}")
