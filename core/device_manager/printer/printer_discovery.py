"""
Printer Discovery (Q1)
======================
Discover local and network printers.

Supports:
- Local USB/LPT printers
- Network printers (IPP, LPD, SMB)
- Cross-platform detection (Windows via win32print, Linux via CUPS)
"""

import os
import sys
import socket
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

from core.logging import app_logger


class PrinterType(Enum):
    """Printer connection type."""
    LOCAL = "local"
    NETWORK = "network"
    SHARED = "shared"
    VIRTUAL = "virtual"
    UNKNOWN = "unknown"


class PrinterStatus(Enum):
    """Printer status."""
    READY = "ready"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"
    PAPER_JAM = "paper_jam"
    OUT_OF_PAPER = "out_of_paper"
    LOW_TONER = "low_toner"
    UNKNOWN = "unknown"


@dataclass
class PrinterInfo:
    """Information about a discovered printer."""
    name: str
    printer_type: PrinterType = PrinterType.UNKNOWN
    status: PrinterStatus = PrinterStatus.UNKNOWN
    is_default: bool = False
    driver: str = ""
    port: str = ""
    location: str = ""
    ip_address: str = ""
    mac_address: str = ""
    model: str = ""
    manufacturer: str = ""
    is_color: bool = False
    is_duplex: bool = False
    supported_formats: List[str] = field(default_factory=list)
    capabilities: Dict[str, Any] = field(default_factory=dict)
    last_seen: datetime = field(default_factory=datetime.now)

    @property
    def display_name(self) -> str:
        """Get display-friendly name."""
        return self.name

    @property
    def status_text_ar(self) -> str:
        """Get Arabic status text."""
        status_map = {
            PrinterStatus.READY: "جاهزة",
            PrinterStatus.BUSY: "مشغولة",
            PrinterStatus.OFFLINE: "غير متصلة",
            PrinterStatus.ERROR: "خطأ",
            PrinterStatus.PAPER_JAM: "انحشار ورق",
            PrinterStatus.OUT_OF_PAPER: "نفاد الورق",
            PrinterStatus.LOW_TONER: "حبر منخفض",
            PrinterStatus.UNKNOWN: "غير معروف",
        }
        return status_map.get(self.status, "غير معروف")

    @property
    def type_text_ar(self) -> str:
        """Get Arabic type text."""
        type_map = {
            PrinterType.LOCAL: "محلية",
            PrinterType.NETWORK: "شبكة",
            PrinterType.SHARED: "مشتركة",
            PrinterType.VIRTUAL: "افتراضية",
            PrinterType.UNKNOWN: "غير معروف",
        }
        return type_map.get(self.printer_type, "غير معروف")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'type': self.printer_type.value,
            'status': self.status.value,
            'is_default': self.is_default,
            'driver': self.driver,
            'port': self.port,
            'location': self.location,
            'ip_address': self.ip_address,
            'model': self.model,
            'manufacturer': self.manufacturer,
            'is_color': self.is_color,
            'is_duplex': self.is_duplex,
        }


class PrinterDiscovery:
    """
    Discover local and network printers.

    Usage:
        discovery = PrinterDiscovery()
        printers = discovery.discover_all()

        for printer in printers:
            print(f"{printer.name} - {printer.status_text_ar}")
    """

    def __init__(self):
        self._cached_printers: List[PrinterInfo] = []
        self._last_scan: Optional[datetime] = None
        self._platform = sys.platform

    def discover_all(self, force_refresh: bool = False) -> List[PrinterInfo]:
        """
        Discover all available printers (local + network).

        Args:
            force_refresh: Force re-scan even if cache is fresh

        Returns:
            List of PrinterInfo objects
        """
        if not force_refresh and self._cached_printers and self._last_scan:
            elapsed = (datetime.now() - self._last_scan).total_seconds()
            if elapsed < 30:
                return self._cached_printers

        printers = []

        try:
            local_printers = self._discover_local()
            printers.extend(local_printers)
            app_logger.info(f"اكتشاف الطابعات المحلية: {len(local_printers)}")
        except Exception as e:
            app_logger.error(f"خطأ في اكتشاف الطابعات المحلية: {e}")

        try:
            network_printers = self._discover_network()
            # Avoid duplicates
            existing_names = {p.name for p in printers}
            for np in network_printers:
                if np.name not in existing_names:
                    printers.append(np)
            app_logger.info(f"اكتشاف طابعات الشبكة: {len(network_printers)}")
        except Exception as e:
            app_logger.error(f"خطأ في اكتشاف طابعات الشبكة: {e}")

        self._cached_printers = printers
        self._last_scan = datetime.now()

        app_logger.info(f"إجمالي الطابعات المكتشفة: {len(printers)}")
        return printers

    def discover_local(self) -> List[PrinterInfo]:
        """Discover local printers only."""
        return self._discover_local()

    def discover_network(self) -> List[PrinterInfo]:
        """Discover network printers only."""
        return self._discover_network()

    def get_default_printer(self) -> Optional[PrinterInfo]:
        """Get the system default printer."""
        printers = self.discover_all()
        for printer in printers:
            if printer.is_default:
                return printer
        return printers[0] if printers else None

    def get_printer_by_name(self, name: str) -> Optional[PrinterInfo]:
        """Get printer info by name."""
        printers = self.discover_all()
        for printer in printers:
            if printer.name == name:
                return printer
        return None

    def refresh(self) -> List[PrinterInfo]:
        """Force refresh printer list."""
        return self.discover_all(force_refresh=True)

    # ═══════════════════════════════════════════════════════
    # Platform-specific discovery
    # ═══════════════════════════════════════════════════════

    def _discover_local(self) -> List[PrinterInfo]:
        """Discover local printers based on platform."""
        if self._platform == 'win32':
            return self._discover_local_windows()
        else:
            return self._discover_local_linux()

    def _discover_local_windows(self) -> List[PrinterInfo]:
        """Discover local printers on Windows using win32print."""
        printers = []

        try:
            import win32print

            default_name = win32print.GetDefaultPrinter()

            flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            printer_list = win32print.EnumPrinters(flags, None, 2)

            for printer_data in printer_list:
                name = printer_data['pPrinterName']
                driver = printer_data.get('pDriverName', '')
                port = printer_data.get('pPortName', '')
                location = printer_data.get('pLocation', '')
                status_code = printer_data.get('Status', 0)

                printer_type = self._classify_printer_type_win(port)
                status = self._map_win_status(status_code)

                info = PrinterInfo(
                    name=name,
                    printer_type=printer_type,
                    status=status,
                    is_default=(name == default_name),
                    driver=driver,
                    port=port,
                    location=location,
                    model=driver,
                )

                # Extract capabilities
                try:
                    handle = win32print.OpenPrinter(name)
                    try:
                        dev_mode = win32print.GetPrinter(handle, 2)
                        if dev_mode.get('pDevMode'):
                            dm = dev_mode['pDevMode']
                            info.is_color = getattr(dm, 'Color', 1) == 2
                            info.is_duplex = getattr(dm, 'Duplex', 1) > 1
                    finally:
                        win32print.ClosePrinter(handle)
                except Exception:
                    pass

                printers.append(info)

        except ImportError:
            app_logger.warning("win32print غير متوفر - استخدام PowerShell للاكتشاف")
            printers = self._discover_local_windows_powershell()

        return printers

    def _discover_local_windows_powershell(self) -> List[PrinterInfo]:
        """Fallback: discover printers via PowerShell."""
        printers = []
        try:
            cmd = 'powershell -Command "Get-Printer | Select-Object Name, DriverName, PortName, PrinterStatus, Type, Shared | ConvertTo-Json"'
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0 and result.stdout.strip():
                import json
                data = json.loads(result.stdout)
                if isinstance(data, dict):
                    data = [data]

                # Get default printer
                default_cmd = 'powershell -Command "(Get-WmiObject -Query \\"SELECT * FROM Win32_Printer WHERE Default=True\\").Name"'
                default_result = subprocess.run(
                    default_cmd, shell=True, capture_output=True, text=True, timeout=10
                )
                default_name = default_result.stdout.strip() if default_result.returncode == 0 else ""

                for item in data:
                    name = item.get('Name', '')
                    if not name:
                        continue

                    port = item.get('PortName', '')
                    printer_type = self._classify_printer_type_win(port)

                    status_code = item.get('PrinterStatus', 0)
                    status = PrinterStatus.READY if status_code == 0 else PrinterStatus.ERROR

                    printers.append(PrinterInfo(
                        name=name,
                        printer_type=printer_type,
                        status=status,
                        is_default=(name == default_name),
                        driver=item.get('DriverName', ''),
                        port=port,
                        model=item.get('DriverName', ''),
                    ))
        except Exception as e:
            app_logger.error(f"PowerShell printer discovery failed: {e}")

        return printers

    def _discover_local_linux(self) -> List[PrinterInfo]:
        """Discover local printers on Linux using CUPS."""
        printers = []

        try:
            result = subprocess.run(
                ['lpstat', '-p', '-d'], capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                return printers

            default_name = ""
            for line in result.stdout.splitlines():
                if line.startswith("system default destination:"):
                    default_name = line.split(":")[-1].strip()
                elif line.startswith("printer"):
                    parts = line.split()
                    if len(parts) >= 2:
                        name = parts[1]
                        is_enabled = "enabled" in line.lower()
                        status = PrinterStatus.READY if is_enabled else PrinterStatus.OFFLINE

                        printers.append(PrinterInfo(
                            name=name,
                            printer_type=PrinterType.LOCAL,
                            status=status,
                            is_default=(name == default_name),
                        ))

        except FileNotFoundError:
            app_logger.warning("lpstat not found - CUPS may not be installed")
        except Exception as e:
            app_logger.error(f"Linux printer discovery failed: {e}")

        return printers

    def _discover_network(self) -> List[PrinterInfo]:
        """Discover network printers using common protocols."""
        printers = []

        # Scan common printer ports on local network
        try:
            local_ip = self._get_local_ip()
            if local_ip:
                subnet = '.'.join(local_ip.split('.')[:3])
                network_printers = self._scan_network_printers(subnet)
                printers.extend(network_printers)
        except Exception as e:
            app_logger.error(f"Network printer scan failed: {e}")

        return printers

    def _scan_network_printers(self, subnet: str, timeout: float = 0.5) -> List[PrinterInfo]:
        """
        Scan network for printers on common ports.

        Checks:
        - Port 9100 (RAW/JetDirect)
        - Port 631 (IPP/CUPS)
        - Port 515 (LPD)
        """
        printers = []
        printer_ports = [9100, 631, 515]

        for host_id in range(1, 255):
            ip = f"{subnet}.{host_id}"
            for port in printer_ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(timeout)
                    result = sock.connect_ex((ip, port))
                    sock.close()

                    if result == 0:
                        protocol = {9100: "RAW", 631: "IPP", 515: "LPD"}.get(port, "")
                        hostname = self._resolve_hostname(ip)
                        name = hostname if hostname else f"Network-{ip}"

                        printers.append(PrinterInfo(
                            name=name,
                            printer_type=PrinterType.NETWORK,
                            status=PrinterStatus.READY,
                            ip_address=ip,
                            port=f"{protocol}:{port}",
                            location=f"Network ({ip})",
                            capabilities={'protocol': protocol, 'port': port},
                        ))
                        break  # Found printer on this IP, skip other ports

                except socket.error:
                    continue

        return printers

    # ═══════════════════════════════════════════════════════
    # Helper methods
    # ═══════════════════════════════════════════════════════

    def _get_local_ip(self) -> Optional[str]:
        """Get local IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return None

    def _resolve_hostname(self, ip: str) -> Optional[str]:
        """Try to resolve hostname from IP."""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except socket.herror:
            return None

    def _classify_printer_type_win(self, port: str) -> PrinterType:
        """Classify printer type based on Windows port name."""
        port_upper = port.upper()
        if any(prefix in port_upper for prefix in ['USB', 'LPT', 'COM']):
            return PrinterType.LOCAL
        elif any(prefix in port_upper for prefix in ['TCP', 'IP_', 'WSD']):
            return PrinterType.NETWORK
        elif '\\\\' in port:
            return PrinterType.SHARED
        elif any(vp in port_upper for vp in ['XPS', 'PDF', 'FAX', 'ONENOTE', 'NUL']):
            return PrinterType.VIRTUAL
        return PrinterType.UNKNOWN

    def _map_win_status(self, status_code: int) -> PrinterStatus:
        """Map Windows printer status code to PrinterStatus."""
        if status_code == 0:
            return PrinterStatus.READY
        # Common Windows status flags
        if status_code & 0x00000008:  # Paper jam
            return PrinterStatus.PAPER_JAM
        if status_code & 0x00000010:  # Paper out
            return PrinterStatus.OUT_OF_PAPER
        if status_code & 0x00040000:  # Toner low
            return PrinterStatus.LOW_TONER
        if status_code & 0x00000400:  # Offline
            return PrinterStatus.OFFLINE
        if status_code & 0x00000004:  # Error
            return PrinterStatus.ERROR
        if status_code & 0x00000001:  # Busy/Paused
            return PrinterStatus.BUSY
        return PrinterStatus.UNKNOWN
