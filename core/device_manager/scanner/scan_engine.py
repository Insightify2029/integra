"""
Scan Engine (Q4)
================
Scan to PDF/Image with configurable settings.

Supports:
- Scan to PNG, JPEG, TIFF, BMP
- Scan to PDF (single and multi-page)
- Configurable resolution, color mode, paper size
- Auto-crop and auto-deskew
- Preview scan
"""

import os
import sys
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Optional, List, Callable, Tuple
from enum import Enum
from pathlib import Path
from datetime import datetime

from core.logging import app_logger


class ScanColorMode(Enum):
    """Scan color mode."""
    COLOR = "color"
    GRAYSCALE = "grayscale"
    BLACK_WHITE = "black_white"

    @property
    def name_ar(self) -> str:
        ar_map = {
            "color": "ألوان",
            "grayscale": "تدرج رمادي",
            "black_white": "أبيض وأسود",
        }
        return ar_map.get(self.value, self.value)


class ScanSource(Enum):
    """Scan source."""
    FLATBED = "flatbed"
    ADF_FRONT = "adf_front"
    ADF_DUPLEX = "adf_duplex"

    @property
    def name_ar(self) -> str:
        ar_map = {
            "flatbed": "السطح المستوي",
            "adf_front": "التلقيم التلقائي - وجه واحد",
            "adf_duplex": "التلقيم التلقائي - وجهين",
        }
        return ar_map.get(self.value, self.value)


class ScanFormat(Enum):
    """Output format for scanned images."""
    PNG = "png"
    JPEG = "jpeg"
    TIFF = "tiff"
    BMP = "bmp"
    PDF = "pdf"

    @property
    def extension(self) -> str:
        ext_map = {
            "png": ".png",
            "jpeg": ".jpg",
            "tiff": ".tiff",
            "bmp": ".bmp",
            "pdf": ".pdf",
        }
        return ext_map.get(self.value, f".{self.value}")


class ScanPaperSize(Enum):
    """Scan area paper sizes."""
    A4 = ("A4", 210.0, 297.0)
    A3 = ("A3", 297.0, 420.0)
    A5 = ("A5", 148.0, 210.0)
    LETTER = ("Letter", 215.9, 279.4)
    LEGAL = ("Legal", 215.9, 355.6)
    AUTO = ("Auto", 0.0, 0.0)

    def __init__(self, label: str, width_mm: float, height_mm: float):
        self.label = label
        self.width_mm = width_mm
        self.height_mm = height_mm


@dataclass
class ScanSettings:
    """Scan job settings."""
    scanner_name: str = ""
    resolution_dpi: int = 300
    color_mode: ScanColorMode = ScanColorMode.COLOR
    source: ScanSource = ScanSource.FLATBED
    output_format: ScanFormat = ScanFormat.PNG
    paper_size: ScanPaperSize = ScanPaperSize.A4
    brightness: int = 0  # -100 to 100
    contrast: int = 0  # -100 to 100
    auto_crop: bool = False
    auto_deskew: bool = False
    output_directory: str = ""
    filename_prefix: str = "scan"
    jpeg_quality: int = 85  # 1-100 for JPEG

    @property
    def output_dir(self) -> str:
        """Get output directory, creating default if needed."""
        if self.output_directory:
            return self.output_directory
        default_dir = os.path.join(os.path.expanduser("~"), "INTEGRA_Scans")
        os.makedirs(default_dir, exist_ok=True)
        return default_dir


@dataclass
class ScanResult:
    """Result of a scan operation."""
    success: bool
    file_path: str = ""
    file_paths: List[str] = field(default_factory=list)
    format: ScanFormat = ScanFormat.PNG
    resolution_dpi: int = 300
    width_px: int = 0
    height_px: int = 0
    file_size_bytes: int = 0
    scan_time_seconds: float = 0.0
    error_message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def file_size_text(self) -> str:
        """Human-readable file size."""
        size = self.file_size_bytes
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"


class ScanEngine:
    """
    Scan engine for acquiring images from scanners.

    Usage:
        engine = ScanEngine()

        # Simple scan
        settings = ScanSettings(
            scanner_name="HP ScanJet",
            resolution_dpi=300,
            color_mode=ScanColorMode.COLOR,
            output_format=ScanFormat.PDF,
        )
        result = engine.scan(settings)

        if result.success:
            print(f"Scanned to: {result.file_path}")
    """

    def __init__(self):
        self._platform = sys.platform

    def scan(
        self,
        settings: ScanSettings,
        on_progress: Optional[Callable[[int, str], None]] = None,
    ) -> ScanResult:
        """
        Perform a scan with the given settings.

        Args:
            settings: Scan configuration
            on_progress: Optional progress callback(percent, message)

        Returns:
            ScanResult with file path and metadata
        """
        start_time = datetime.now()

        if on_progress:
            on_progress(0, "بدء المسح الضوئي...")

        try:
            if self._platform == 'win32':
                result = self._scan_windows(settings, on_progress)
            else:
                result = self._scan_linux(settings, on_progress)

            elapsed = (datetime.now() - start_time).total_seconds()
            result.scan_time_seconds = elapsed

            if result.success and result.file_path and os.path.exists(result.file_path):
                result.file_size_bytes = os.path.getsize(result.file_path)
                app_logger.info(
                    f"مسح ضوئي ناجح: {result.file_path} "
                    f"({result.file_size_text}, {elapsed:.1f}s)"
                )

            if on_progress:
                on_progress(100, "اكتمل المسح الضوئي" if result.success else "فشل المسح")

            return result

        except Exception as e:
            app_logger.error(f"خطأ في المسح الضوئي: {e}")
            return ScanResult(
                success=False,
                error_message=str(e),
            )

    def preview_scan(self, settings: ScanSettings) -> ScanResult:
        """
        Perform a low-resolution preview scan.

        Returns a temporary image for preview purposes.
        """
        preview_settings = ScanSettings(
            scanner_name=settings.scanner_name,
            resolution_dpi=75,  # Low res for preview
            color_mode=settings.color_mode,
            source=settings.source,
            output_format=ScanFormat.PNG,
            paper_size=settings.paper_size,
            output_directory=tempfile.gettempdir(),
            filename_prefix="preview",
        )
        return self.scan(preview_settings)

    def get_supported_resolutions(self, scanner_name: str) -> List[int]:
        """Get supported resolutions for a scanner."""
        # Common resolutions - in production, query the scanner
        return [75, 100, 150, 200, 300, 400, 600, 1200]

    # ═══════════════════════════════════════════════════════
    # Windows scanning
    # ═══════════════════════════════════════════════════════

    def _scan_windows(
        self,
        settings: ScanSettings,
        on_progress: Optional[Callable] = None,
    ) -> ScanResult:
        """Scan using WIA on Windows."""
        output_path = self._generate_output_path(settings)

        try:
            return self._scan_wia(settings, output_path, on_progress)
        except Exception as e:
            app_logger.warning(f"WIA scan failed, trying TWAIN: {e}")
            try:
                return self._scan_twain(settings, output_path, on_progress)
            except Exception as e2:
                app_logger.error(f"TWAIN scan also failed: {e2}")
                return ScanResult(success=False, error_message=str(e2))

    def _scan_wia(
        self,
        settings: ScanSettings,
        output_path: str,
        on_progress: Optional[Callable] = None,
    ) -> ScanResult:
        """Scan using WIA (Windows Image Acquisition)."""
        try:
            import comtypes
            from comtypes.client import CreateObject

            if on_progress:
                on_progress(10, "الاتصال بالماسح الضوئي...")

            wia_manager = CreateObject("WIA.DeviceManager")
            device = None

            # Find the scanner
            for i in range(1, wia_manager.DeviceInfos.Count + 1):
                dev_info = wia_manager.DeviceInfos.Item(i)
                if dev_info.Type == 1:  # Scanner
                    if not settings.scanner_name or settings.scanner_name in str(dev_info.Properties("Name").Value):
                        device = dev_info.Connect()
                        break

            if not device:
                return ScanResult(success=False, error_message="لم يتم العثور على الماسح الضوئي")

            if on_progress:
                on_progress(30, "إعداد المسح الضوئي...")

            # Configure scan item
            item = device.Items(1)

            # Set resolution
            item.Properties("Horizontal Resolution").Value = settings.resolution_dpi
            item.Properties("Vertical Resolution").Value = settings.resolution_dpi

            # Set color mode
            color_map = {
                ScanColorMode.COLOR: 1,
                ScanColorMode.GRAYSCALE: 2,
                ScanColorMode.BLACK_WHITE: 4,
            }
            item.Properties("Current Intent").Value = color_map.get(settings.color_mode, 1)

            # Set scan area if paper size is not auto
            if settings.paper_size != ScanPaperSize.AUTO:
                width_px = int(settings.paper_size.width_mm / 25.4 * settings.resolution_dpi)
                height_px = int(settings.paper_size.height_mm / 25.4 * settings.resolution_dpi)
                item.Properties("Horizontal Extent").Value = width_px
                item.Properties("Vertical Extent").Value = height_px

            if on_progress:
                on_progress(50, "جاري المسح الضوئي...")

            # Perform scan
            image = item.Transfer("{B96B3CAE-0728-11D3-9D7B-0000F81EF32E}")  # BMP format

            if on_progress:
                on_progress(80, "حفظ الصورة...")

            # Save to temp BMP first
            temp_bmp = tempfile.mktemp(suffix='.bmp')
            image.SaveFile(temp_bmp)

            # Convert if needed
            if settings.output_format == ScanFormat.BMP:
                import shutil
                shutil.move(temp_bmp, output_path)
            else:
                self._convert_image(temp_bmp, output_path, settings)
                try:
                    os.unlink(temp_bmp)
                except OSError:
                    pass

            return ScanResult(
                success=True,
                file_path=output_path,
                file_paths=[output_path],
                format=settings.output_format,
                resolution_dpi=settings.resolution_dpi,
            )

        except ImportError:
            # Fallback to PowerShell WIA
            return self._scan_wia_powershell(settings, output_path, on_progress)

    def _scan_wia_powershell(
        self,
        settings: ScanSettings,
        output_path: str,
        on_progress: Optional[Callable] = None,
    ) -> ScanResult:
        """Fallback WIA scanning via PowerShell."""
        if on_progress:
            on_progress(20, "استخدام PowerShell للمسح...")

        temp_bmp = tempfile.mktemp(suffix='.bmp')
        ps_script = (
            "$dm = New-Object -ComObject WIA.DeviceManager; "
            "$dev = $null; "
            "foreach ($di in $dm.DeviceInfos) { "
            "  if ($di.Type -eq 1) { $dev = $di.Connect(); break } "
            "}; "
            "if ($dev) { "
            "  $item = $dev.Items(1); "
            f"  $item.Properties('Horizontal Resolution').Value = {settings.resolution_dpi}; "
            f"  $item.Properties('Vertical Resolution').Value = {settings.resolution_dpi}; "
            "  $img = $item.Transfer('{B96B3CAE-0728-11D3-9D7B-0000F81EF32E}'); "
            f"  $img.SaveFile('{temp_bmp}'); "
            "  Write-Output 'SUCCESS' "
            "} else { Write-Output 'NO_SCANNER' }"
        )

        result = subprocess.run(['powershell', '-Command', ps_script], capture_output=True, text=True, timeout=60)

        if 'SUCCESS' in result.stdout:
            if on_progress:
                on_progress(80, "تحويل الصورة...")

            if settings.output_format == ScanFormat.BMP:
                import shutil
                shutil.move(temp_bmp, output_path)
            else:
                self._convert_image(temp_bmp, output_path, settings)
                try:
                    os.unlink(temp_bmp)
                except OSError:
                    pass

            return ScanResult(
                success=True,
                file_path=output_path,
                file_paths=[output_path],
                format=settings.output_format,
                resolution_dpi=settings.resolution_dpi,
            )
        else:
            return ScanResult(
                success=False,
                error_message="لم يتم العثور على ماسح ضوئي أو فشل المسح",
            )

    def _scan_twain(
        self,
        settings: ScanSettings,
        output_path: str,
        on_progress: Optional[Callable] = None,
    ) -> ScanResult:
        """Scan using TWAIN protocol."""
        try:
            import twain

            if on_progress:
                on_progress(10, "الاتصال عبر TWAIN...")

            sm = twain.SourceManager(0)
            try:
                if settings.scanner_name:
                    src = sm.OpenSource(settings.scanner_name)
                else:
                    src = sm.OpenSource()

                if not src:
                    return ScanResult(success=False, error_message="لم يتم فتح مصدر TWAIN")

                try:
                    # Set resolution
                    src.SetCapability(twain.ICAP_XRESOLUTION, twain.TWTY_FIX32, settings.resolution_dpi)
                    src.SetCapability(twain.ICAP_YRESOLUTION, twain.TWTY_FIX32, settings.resolution_dpi)

                    # Set color mode
                    pixel_type = {
                        ScanColorMode.COLOR: twain.TWPT_RGB,
                        ScanColorMode.GRAYSCALE: twain.TWPT_GRAY,
                        ScanColorMode.BLACK_WHITE: twain.TWPT_BW,
                    }.get(settings.color_mode, twain.TWPT_RGB)
                    src.SetCapability(twain.ICAP_PIXELTYPE, twain.TWTY_UINT16, pixel_type)

                    # Set source (ADF vs Flatbed)
                    if settings.source in (ScanSource.ADF_FRONT, ScanSource.ADF_DUPLEX):
                        src.SetCapability(twain.CAP_FEEDERENABLED, twain.TWTY_BOOL, True)
                        if settings.source == ScanSource.ADF_DUPLEX:
                            src.SetCapability(twain.CAP_DUPLEXENABLED, twain.TWTY_BOOL, True)

                    if on_progress:
                        on_progress(40, "جاري المسح الضوئي...")

                    # Acquire
                    src.RequestAcquire(0, 0)
                    info = src.GetImageInfo()
                    temp_bmp = tempfile.mktemp(suffix='.bmp')
                    src.GetNativeData()  # This gets the scan data

                    if on_progress:
                        on_progress(80, "حفظ الصورة...")

                    # Convert/save
                    if settings.output_format == ScanFormat.BMP:
                        import shutil
                        shutil.move(temp_bmp, output_path)
                    else:
                        self._convert_image(temp_bmp, output_path, settings)

                    return ScanResult(
                        success=True,
                        file_path=output_path,
                        file_paths=[output_path],
                        format=settings.output_format,
                        resolution_dpi=settings.resolution_dpi,
                    )

                finally:
                    src.destroy()
            finally:
                sm.destroy()

        except ImportError:
            return ScanResult(success=False, error_message="مكتبة TWAIN غير متوفرة")

    # ═══════════════════════════════════════════════════════
    # Linux scanning
    # ═══════════════════════════════════════════════════════

    def _scan_linux(
        self,
        settings: ScanSettings,
        on_progress: Optional[Callable] = None,
    ) -> ScanResult:
        """Scan using SANE on Linux."""
        output_path = self._generate_output_path(settings)

        try:
            return self._scan_sane(settings, output_path, on_progress)
        except Exception as e:
            app_logger.warning(f"python-sane failed, trying CLI: {e}")
            return self._scan_sane_cli(settings, output_path, on_progress)

    def _scan_sane(
        self,
        settings: ScanSettings,
        output_path: str,
        on_progress: Optional[Callable] = None,
    ) -> ScanResult:
        """Scan using python-sane."""
        try:
            import sane

            if on_progress:
                on_progress(10, "الاتصال بالماسح...")

            sane.init()
            try:
                dev = sane.open(settings.scanner_name)

                # Configure
                dev.resolution = settings.resolution_dpi

                mode_map = {
                    ScanColorMode.COLOR: 'Color',
                    ScanColorMode.GRAYSCALE: 'Gray',
                    ScanColorMode.BLACK_WHITE: 'Lineart',
                }
                try:
                    dev.mode = mode_map.get(settings.color_mode, 'Color')
                except Exception:
                    pass

                # Set source
                if settings.source != ScanSource.FLATBED:
                    try:
                        dev.source = 'ADF' if settings.source == ScanSource.ADF_FRONT else 'ADF Duplex'
                    except Exception:
                        pass

                # Set brightness/contrast
                if settings.brightness != 0:
                    try:
                        dev.brightness = settings.brightness
                    except Exception:
                        pass
                if settings.contrast != 0:
                    try:
                        dev.contrast = settings.contrast
                    except Exception:
                        pass

                if on_progress:
                    on_progress(30, "جاري المسح الضوئي...")

                # Scan
                dev.start()
                image = dev.snap()

                if on_progress:
                    on_progress(70, "معالجة الصورة...")

                # Auto-deskew using PIL
                if settings.auto_deskew:
                    image = self._auto_deskew(image)

                # Auto-crop
                if settings.auto_crop:
                    image = self._auto_crop(image)

                if on_progress:
                    on_progress(85, "حفظ الصورة...")

                # Save
                if settings.output_format == ScanFormat.PDF:
                    image.save(output_path, 'PDF', resolution=settings.resolution_dpi)
                elif settings.output_format == ScanFormat.JPEG:
                    image.save(output_path, 'JPEG', quality=settings.jpeg_quality)
                elif settings.output_format == ScanFormat.TIFF:
                    image.save(output_path, 'TIFF', compression='tiff_lzw')
                else:
                    image.save(output_path)

                width, height = image.size

                dev.close()

                return ScanResult(
                    success=True,
                    file_path=output_path,
                    file_paths=[output_path],
                    format=settings.output_format,
                    resolution_dpi=settings.resolution_dpi,
                    width_px=width,
                    height_px=height,
                )

            finally:
                sane.exit()

        except ImportError:
            raise RuntimeError("python-sane not available")

    def _scan_sane_cli(
        self,
        settings: ScanSettings,
        output_path: str,
        on_progress: Optional[Callable] = None,
    ) -> ScanResult:
        """Fallback: scan using scanimage CLI."""
        if on_progress:
            on_progress(10, "استخدام scanimage...")

        # Build scanimage command
        temp_pnm = tempfile.mktemp(suffix='.pnm')
        cmd = ['scanimage']

        if settings.scanner_name:
            cmd.extend(['-d', settings.scanner_name])

        cmd.extend(['--resolution', str(settings.resolution_dpi)])

        mode_map = {
            ScanColorMode.COLOR: 'Color',
            ScanColorMode.GRAYSCALE: 'Gray',
            ScanColorMode.BLACK_WHITE: 'Lineart',
        }
        cmd.extend(['--mode', mode_map.get(settings.color_mode, 'Color')])

        if settings.source == ScanSource.ADF_FRONT:
            cmd.extend(['--source', 'ADF'])
        elif settings.source == ScanSource.ADF_DUPLEX:
            cmd.extend(['--source', 'ADF Duplex'])

        cmd.extend(['-o', temp_pnm])

        if on_progress:
            on_progress(30, "جاري المسح الضوئي...")

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode != 0:
            return ScanResult(
                success=False,
                error_message=f"scanimage failed: {result.stderr}",
            )

        if on_progress:
            on_progress(70, "تحويل الصورة...")

        # Convert PNM to target format
        self._convert_image(temp_pnm, output_path, settings)

        try:
            os.unlink(temp_pnm)
        except OSError:
            pass

        return ScanResult(
            success=True,
            file_path=output_path,
            file_paths=[output_path],
            format=settings.output_format,
            resolution_dpi=settings.resolution_dpi,
        )

    # ═══════════════════════════════════════════════════════
    # Helper methods
    # ═══════════════════════════════════════════════════════

    def _generate_output_path(self, settings: ScanSettings) -> str:
        """Generate unique output file path."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{settings.filename_prefix}_{timestamp}{settings.output_format.extension}"
        return os.path.join(settings.output_dir, filename)

    def _convert_image(self, input_path: str, output_path: str, settings: ScanSettings):
        """Convert image to target format using Pillow."""
        try:
            from PIL import Image

            img = Image.open(input_path)

            if settings.auto_deskew:
                img = self._auto_deskew(img)
            if settings.auto_crop:
                img = self._auto_crop(img)

            if settings.output_format == ScanFormat.PDF:
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                img.save(output_path, 'PDF', resolution=settings.resolution_dpi)
            elif settings.output_format == ScanFormat.JPEG:
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                img.save(output_path, 'JPEG', quality=settings.jpeg_quality)
            elif settings.output_format == ScanFormat.TIFF:
                img.save(output_path, 'TIFF', compression='tiff_lzw')
            elif settings.output_format == ScanFormat.PNG:
                img.save(output_path, 'PNG')
            else:
                img.save(output_path)

        except ImportError:
            # No Pillow - try to just copy if same format
            import shutil
            shutil.copy2(input_path, output_path)
            app_logger.warning("Pillow not available - saved raw image without conversion")

    def _auto_deskew(self, image):
        """Auto-deskew a scanned image."""
        try:
            from PIL import Image
            import numpy as np

            # Convert to grayscale for analysis
            gray = image.convert('L')
            arr = np.array(gray)

            # Simple deskew using variance of row sums at different angles
            best_angle = 0
            best_variance = 0

            for angle_10x in range(-50, 51):
                angle = angle_10x / 10.0
                rotated = image.rotate(angle, fillcolor='white', expand=False)
                gray_rot = rotated.convert('L')
                arr_rot = np.array(gray_rot)
                row_sums = arr_rot.sum(axis=1)
                variance = np.var(row_sums)
                if variance > best_variance:
                    best_variance = variance
                    best_angle = angle

            if abs(best_angle) > 0.1:
                image = image.rotate(best_angle, fillcolor='white', expand=True)
                app_logger.info(f"Auto-deskew: rotated {best_angle:.1f}°")

        except ImportError:
            app_logger.warning("numpy not available - skipping auto-deskew")

        return image

    def _auto_crop(self, image):
        """Auto-crop whitespace from scanned image."""
        try:
            from PIL import ImageOps

            # Invert, get bounding box, crop
            inverted = ImageOps.invert(image.convert('RGB'))
            bbox = inverted.getbbox()
            if bbox:
                # Add small margin
                margin = 10
                x1 = max(0, bbox[0] - margin)
                y1 = max(0, bbox[1] - margin)
                x2 = min(image.width, bbox[2] + margin)
                y2 = min(image.height, bbox[3] + margin)
                image = image.crop((x1, y1, x2, y2))
                app_logger.info("Auto-crop: trimmed whitespace")

        except Exception as e:
            app_logger.warning(f"Auto-crop failed: {e}")

        return image
