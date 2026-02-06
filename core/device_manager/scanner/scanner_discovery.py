"""
Scanner Discovery (Q3)
======================
Discover scanners using TWAIN (Windows) and SANE (Linux).

Supports:
- TWAIN scanners (Windows)
- WIA scanners (Windows)
- SANE scanners (Linux)
- Network scanners
"""

import sys
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

from core.logging import app_logger


class ScannerType(Enum):
    """Scanner connection type."""
    USB = "usb"
    NETWORK = "network"
    TWAIN = "twain"
    WIA = "wia"
    SANE = "sane"
    UNKNOWN = "unknown"


class ScannerStatus(Enum):
    """Scanner status."""
    READY = "ready"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"
    WARMING_UP = "warming_up"
    COVER_OPEN = "cover_open"
    PAPER_JAM = "paper_jam"
    UNKNOWN = "unknown"


class ScannerFeature(Enum):
    """Scanner features/capabilities."""
    FLATBED = "flatbed"
    ADF = "adf"
    DUPLEX_ADF = "duplex_adf"
    COLOR = "color"
    GRAYSCALE = "grayscale"
    AUTO_CROP = "auto_crop"
    AUTO_DESKEW = "auto_deskew"
    MULTI_PAGE = "multi_page"


@dataclass
class ScannerInfo:
    """Information about a discovered scanner."""
    name: str
    scanner_id: str = ""
    scanner_type: ScannerType = ScannerType.UNKNOWN
    status: ScannerStatus = ScannerStatus.UNKNOWN
    manufacturer: str = ""
    model: str = ""
    driver: str = ""
    ip_address: str = ""
    serial_number: str = ""
    features: List[ScannerFeature] = field(default_factory=list)
    max_resolution_dpi: int = 600
    supported_resolutions: List[int] = field(default_factory=lambda: [75, 150, 300, 600])
    supported_formats: List[str] = field(default_factory=lambda: ['bmp', 'jpg', 'png', 'tiff', 'pdf'])
    has_adf: bool = False
    has_duplex: bool = False
    capabilities: Dict[str, Any] = field(default_factory=dict)
    last_seen: datetime = field(default_factory=datetime.now)

    @property
    def display_name(self) -> str:
        """Display-friendly name."""
        if self.manufacturer and self.model:
            return f"{self.manufacturer} {self.model}"
        return self.name

    @property
    def status_text_ar(self) -> str:
        """Arabic status text."""
        status_map = {
            ScannerStatus.READY: "جاهز",
            ScannerStatus.BUSY: "مشغول",
            ScannerStatus.OFFLINE: "غير متصل",
            ScannerStatus.ERROR: "خطأ",
            ScannerStatus.WARMING_UP: "تسخين",
            ScannerStatus.COVER_OPEN: "الغطاء مفتوح",
            ScannerStatus.PAPER_JAM: "انحشار ورق",
            ScannerStatus.UNKNOWN: "غير معروف",
        }
        return status_map.get(self.status, "غير معروف")

    @property
    def type_text_ar(self) -> str:
        """Arabic type text."""
        type_map = {
            ScannerType.USB: "USB",
            ScannerType.NETWORK: "شبكة",
            ScannerType.TWAIN: "TWAIN",
            ScannerType.WIA: "WIA",
            ScannerType.SANE: "SANE",
            ScannerType.UNKNOWN: "غير معروف",
        }
        return type_map.get(self.scanner_type, "غير معروف")

    @property
    def features_text_ar(self) -> str:
        """Arabic features summary."""
        parts = []
        if self.has_adf:
            parts.append("تلقيم تلقائي")
        if self.has_duplex:
            parts.append("وجهين")
        if ScannerFeature.COLOR in self.features:
            parts.append("ألوان")
        if not parts:
            parts.append("ماسح أساسي")
        return " | ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'scanner_id': self.scanner_id,
            'type': self.scanner_type.value,
            'status': self.status.value,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'driver': self.driver,
            'ip_address': self.ip_address,
            'max_resolution': self.max_resolution_dpi,
            'has_adf': self.has_adf,
            'has_duplex': self.has_duplex,
            'features': [f.value for f in self.features],
        }


class ScannerDiscovery:
    """
    Discover available scanners on the system.

    Usage:
        discovery = ScannerDiscovery()
        scanners = discovery.discover_all()

        for scanner in scanners:
            print(f"{scanner.display_name} - {scanner.status_text_ar}")
    """

    def __init__(self):
        self._cached_scanners: List[ScannerInfo] = []
        self._last_scan: Optional[datetime] = None
        self._platform = sys.platform

    def discover_all(self, force_refresh: bool = False) -> List[ScannerInfo]:
        """
        Discover all available scanners.

        Args:
            force_refresh: Force re-scan even if cache is fresh

        Returns:
            List of ScannerInfo objects
        """
        if not force_refresh and self._cached_scanners and self._last_scan:
            elapsed = (datetime.now() - self._last_scan).total_seconds()
            if elapsed < 30:
                return self._cached_scanners

        scanners = []

        if self._platform == 'win32':
            # Try WIA first (more modern), then TWAIN
            try:
                wia_scanners = self._discover_wia()
                scanners.extend(wia_scanners)
                app_logger.info(f"WIA scanners found: {len(wia_scanners)}")
            except Exception as e:
                app_logger.error(f"WIA discovery error: {e}")

            try:
                twain_scanners = self._discover_twain()
                existing_names = {s.name for s in scanners}
                for ts in twain_scanners:
                    if ts.name not in existing_names:
                        scanners.append(ts)
                app_logger.info(f"TWAIN scanners found: {len(twain_scanners)}")
            except Exception as e:
                app_logger.error(f"TWAIN discovery error: {e}")
        else:
            try:
                sane_scanners = self._discover_sane()
                scanners.extend(sane_scanners)
                app_logger.info(f"SANE scanners found: {len(sane_scanners)}")
            except Exception as e:
                app_logger.error(f"SANE discovery error: {e}")

        self._cached_scanners = scanners
        self._last_scan = datetime.now()

        app_logger.info(f"إجمالي الماسحات المكتشفة: {len(scanners)}")
        return scanners

    def get_scanner_by_name(self, name: str) -> Optional[ScannerInfo]:
        """Get scanner by name."""
        scanners = self.discover_all()
        for scanner in scanners:
            if scanner.name == name or scanner.display_name == name:
                return scanner
        return None

    def get_scanner_by_id(self, scanner_id: str) -> Optional[ScannerInfo]:
        """Get scanner by ID."""
        scanners = self.discover_all()
        for scanner in scanners:
            if scanner.scanner_id == scanner_id:
                return scanner
        return None

    def get_default_scanner(self) -> Optional[ScannerInfo]:
        """Get the first available scanner."""
        scanners = self.discover_all()
        return scanners[0] if scanners else None

    def refresh(self) -> List[ScannerInfo]:
        """Force refresh scanner list."""
        return self.discover_all(force_refresh=True)

    # ═══════════════════════════════════════════════════════
    # WIA Discovery (Windows)
    # ═══════════════════════════════════════════════════════

    def _discover_wia(self) -> List[ScannerInfo]:
        """Discover scanners via Windows Image Acquisition (WIA)."""
        scanners = []

        try:
            import comtypes
            from comtypes.client import CreateObject

            wia_manager = CreateObject("WIA.DeviceManager")
            device_infos = wia_manager.DeviceInfos

            for i in range(1, device_infos.Count + 1):
                try:
                    dev_info = device_infos.Item(i)
                    # Type 1 = Scanner
                    dev_type = dev_info.Type
                    if dev_type != 1:
                        continue

                    name = str(dev_info.Properties("Name").Value) if dev_info.Properties("Name") else f"WIA Scanner {i}"
                    manufacturer = ""
                    model = ""

                    try:
                        manufacturer = str(dev_info.Properties("Manufacturer").Value)
                    except Exception:
                        pass
                    try:
                        model = str(dev_info.Properties("Description").Value)
                    except Exception:
                        pass

                    scanner = ScannerInfo(
                        name=name,
                        scanner_id=str(dev_info.DeviceID),
                        scanner_type=ScannerType.WIA,
                        status=ScannerStatus.READY,
                        manufacturer=manufacturer,
                        model=model,
                        features=[ScannerFeature.FLATBED, ScannerFeature.COLOR, ScannerFeature.GRAYSCALE],
                    )
                    scanners.append(scanner)

                except Exception as e:
                    app_logger.warning(f"WIA device {i} error: {e}")

        except ImportError:
            app_logger.warning("comtypes not available - trying PowerShell WIA discovery")
            scanners = self._discover_wia_powershell()

        return scanners

    def _discover_wia_powershell(self) -> List[ScannerInfo]:
        """Fallback WIA discovery via PowerShell."""
        scanners = []
        try:
            ps_script = """
                $dm = New-Object -ComObject WIA.DeviceManager
                $result = @()
                foreach ($di in $dm.DeviceInfos) {
                    if ($di.Type -eq 1) {
                        $result += @{
                            Name = $di.Properties('Name').Value
                            ID = $di.DeviceID
                            Manufacturer = try { $di.Properties('Manufacturer').Value } catch { '' }
                        }
                    }
                }
                $result | ConvertTo-Json
            """
            result = subprocess.run(['powershell', '-Command', ps_script], capture_output=True, text=True, timeout=15)
            if result.returncode == 0 and result.stdout.strip():
                import json
                data = json.loads(result.stdout)
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    scanners.append(ScannerInfo(
                        name=item.get('Name', 'Unknown Scanner'),
                        scanner_id=item.get('ID', ''),
                        scanner_type=ScannerType.WIA,
                        status=ScannerStatus.READY,
                        manufacturer=item.get('Manufacturer', ''),
                        features=[ScannerFeature.FLATBED, ScannerFeature.COLOR],
                    ))
        except Exception as e:
            app_logger.error(f"PowerShell WIA discovery failed: {e}")

        return scanners

    # ═══════════════════════════════════════════════════════
    # TWAIN Discovery (Windows)
    # ═══════════════════════════════════════════════════════

    def _discover_twain(self) -> List[ScannerInfo]:
        """Discover scanners via TWAIN protocol."""
        scanners = []

        try:
            import twain

            sm = twain.SourceManager(0)
            try:
                source_list = sm.GetSourceList()
                if source_list:
                    for source_name in source_list:
                        scanner = ScannerInfo(
                            name=source_name,
                            scanner_id=f"twain:{source_name}",
                            scanner_type=ScannerType.TWAIN,
                            status=ScannerStatus.READY,
                            features=[ScannerFeature.FLATBED, ScannerFeature.COLOR],
                        )

                        # Try to get capabilities
                        try:
                            src = sm.OpenSource(source_name)
                            if src:
                                try:
                                    # Check for ADF
                                    cap_val = src.GetCapability(twain.CAP_FEEDERENABLED)
                                    if cap_val:
                                        scanner.has_adf = True
                                        scanner.features.append(ScannerFeature.ADF)

                                    # Check for duplex
                                    cap_val = src.GetCapability(twain.CAP_DUPLEX)
                                    if cap_val:
                                        scanner.has_duplex = True
                                        scanner.features.append(ScannerFeature.DUPLEX_ADF)
                                except Exception:
                                    pass
                                finally:
                                    src.destroy()
                        except Exception:
                            pass

                        scanners.append(scanner)
            finally:
                sm.destroy()

        except ImportError:
            app_logger.warning("pytwain not available - TWAIN discovery skipped")
        except Exception as e:
            app_logger.error(f"TWAIN discovery error: {e}")

        return scanners

    # ═══════════════════════════════════════════════════════
    # SANE Discovery (Linux)
    # ═══════════════════════════════════════════════════════

    def _discover_sane(self) -> List[ScannerInfo]:
        """Discover scanners via SANE (Scanner Access Now Easy)."""
        scanners = []

        # Try python-sane first
        try:
            import sane
            sane.init()
            devices = sane.get_devices()
            for device in devices:
                name = device[0]  # device name
                vendor = device[1] if len(device) > 1 else ""
                model = device[2] if len(device) > 2 else ""
                dev_type = device[3] if len(device) > 3 else ""

                scanner_type = ScannerType.USB
                if 'net' in name.lower():
                    scanner_type = ScannerType.NETWORK

                scanner = ScannerInfo(
                    name=name,
                    scanner_id=name,
                    scanner_type=scanner_type,
                    status=ScannerStatus.READY,
                    manufacturer=vendor,
                    model=model,
                    driver=dev_type,
                    features=[ScannerFeature.FLATBED, ScannerFeature.COLOR, ScannerFeature.GRAYSCALE],
                )

                # Try to get more capabilities
                try:
                    dev = sane.open(name)
                    try:
                        params = dev.get_parameters()
                        if params:
                            scanner.capabilities['params'] = str(params)
                        # Check for ADF source
                        try:
                            sources = dev['source']
                            if isinstance(sources, (list, tuple)):
                                for src in sources:
                                    if 'adf' in str(src).lower() or 'feeder' in str(src).lower():
                                        scanner.has_adf = True
                                        scanner.features.append(ScannerFeature.ADF)
                                        break
                        except Exception:
                            pass
                    finally:
                        dev.close()
                except Exception:
                    pass

                scanners.append(scanner)

            sane.exit()

        except ImportError:
            app_logger.warning("python-sane not available - trying scanimage CLI")
            scanners = self._discover_sane_cli()

        return scanners

    def _discover_sane_cli(self) -> List[ScannerInfo]:
        """Fallback SANE discovery via scanimage CLI."""
        scanners = []
        try:
            result = subprocess.run(
                ['scanimage', '-L'], capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    # Format: device `name' is a Vendor Model type scanner
                    if line.startswith("device"):
                        parts = line.split("'")
                        if len(parts) >= 2:
                            device_name = parts[1]
                            description = parts[2] if len(parts) > 2 else ""

                            # Parse description
                            desc_parts = description.strip().split()
                            vendor = desc_parts[2] if len(desc_parts) > 2 else ""
                            model = desc_parts[3] if len(desc_parts) > 3 else ""

                            scanner_type = ScannerType.USB
                            if 'net' in device_name.lower():
                                scanner_type = ScannerType.NETWORK

                            scanners.append(ScannerInfo(
                                name=device_name,
                                scanner_id=device_name,
                                scanner_type=scanner_type,
                                status=ScannerStatus.READY,
                                manufacturer=vendor,
                                model=model,
                                features=[ScannerFeature.FLATBED, ScannerFeature.COLOR],
                            ))

        except FileNotFoundError:
            app_logger.warning("scanimage not found - SANE not installed")
        except Exception as e:
            app_logger.error(f"SANE CLI discovery failed: {e}")

        return scanners
