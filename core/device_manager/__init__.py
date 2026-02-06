"""
Device Manager Core
====================
Core infrastructure for printer, scanner, and bluetooth device management.

Components:
- printer: Printer discovery, print preview, print jobs
- scanner: Scanner discovery, scan to PDF/Image, batch scanning
- bluetooth: Bluetooth device management
- integration: PDF Studio bridge (Track P)
"""

from .printer import PrinterDiscovery, PrintManager, PrinterInfo
from .scanner import ScannerDiscovery, ScanEngine, BatchScanner, ScannerInfo
from .bluetooth import BluetoothManager, BluetoothDevice
from .integration import PDFStudioBridge

__all__ = [
    'PrinterDiscovery', 'PrintManager', 'PrinterInfo',
    'ScannerDiscovery', 'ScanEngine', 'BatchScanner', 'ScannerInfo',
    'BluetoothManager', 'BluetoothDevice',
    'PDFStudioBridge',
]
