"""
Bluetooth Manager (Q6)
======================
Bluetooth device discovery, pairing, and management.

Supports:
- Device discovery and scanning
- Pairing and unpairing
- Connection management
- Device information and status
- Cross-platform (Windows via PowerShell, Linux via bluetoothctl)
"""

import sys
import subprocess
import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from enum import Enum
from datetime import datetime

from core.logging import app_logger


class BluetoothDeviceType(Enum):
    """Bluetooth device type."""
    AUDIO = "audio"
    PRINTER = "printer"
    KEYBOARD = "keyboard"
    MOUSE = "mouse"
    PHONE = "phone"
    HEADSET = "headset"
    COMPUTER = "computer"
    IMAGING = "imaging"
    PERIPHERAL = "peripheral"
    NETWORK = "network"
    UNKNOWN = "unknown"

    @property
    def name_ar(self) -> str:
        ar_map = {
            "audio": "صوت",
            "printer": "طابعة",
            "keyboard": "لوحة مفاتيح",
            "mouse": "فأرة",
            "phone": "هاتف",
            "headset": "سماعة",
            "computer": "كمبيوتر",
            "imaging": "تصوير",
            "peripheral": "ملحقات",
            "network": "شبكة",
            "unknown": "غير معروف",
        }
        return ar_map.get(self.value, "غير معروف")

    @property
    def icon(self) -> str:
        icon_map = {
            "audio": "🔊",
            "printer": "🖨️",
            "keyboard": "⌨️",
            "mouse": "🖱️",
            "phone": "📱",
            "headset": "🎧",
            "computer": "💻",
            "imaging": "📷",
            "peripheral": "🔌",
            "network": "🌐",
            "unknown": "📶",
        }
        return icon_map.get(self.value, "📶")


class BluetoothStatus(Enum):
    """Bluetooth device connection status."""
    CONNECTED = "connected"
    PAIRED = "paired"
    AVAILABLE = "available"
    DISCONNECTED = "disconnected"
    UNAVAILABLE = "unavailable"

    @property
    def name_ar(self) -> str:
        ar_map = {
            "connected": "متصل",
            "paired": "مقترن",
            "available": "متاح",
            "disconnected": "غير متصل",
            "unavailable": "غير متاح",
        }
        return ar_map.get(self.value, "غير معروف")

    @property
    def color(self) -> str:
        color_map = {
            "connected": "#10b981",
            "paired": "#3b82f6",
            "available": "#f59e0b",
            "disconnected": "#6b7280",
            "unavailable": "#ef4444",
        }
        return color_map.get(self.value, "#6b7280")


@dataclass
class BluetoothDevice:
    """Information about a Bluetooth device."""
    name: str
    address: str  # MAC address
    device_type: BluetoothDeviceType = BluetoothDeviceType.UNKNOWN
    status: BluetoothStatus = BluetoothStatus.AVAILABLE
    is_paired: bool = False
    is_connected: bool = False
    rssi: int = 0  # Signal strength (dBm)
    manufacturer: str = ""
    battery_level: int = -1  # -1 = unknown
    services: List[str] = field(default_factory=list)
    last_seen: datetime = field(default_factory=datetime.now)
    capabilities: Dict[str, Any] = field(default_factory=dict)

    @property
    def display_name(self) -> str:
        return self.name or f"Device {self.address}"

    @property
    def signal_strength_text(self) -> str:
        """Human-readable signal strength."""
        if self.rssi == 0:
            return "غير معروف"
        if self.rssi > -50:
            return "ممتاز"
        if self.rssi > -70:
            return "جيد"
        if self.rssi > -85:
            return "متوسط"
        return "ضعيف"

    @property
    def signal_bars(self) -> int:
        """Signal strength as bar count (0-4)."""
        if self.rssi == 0:
            return 0
        if self.rssi > -50:
            return 4
        if self.rssi > -65:
            return 3
        if self.rssi > -80:
            return 2
        if self.rssi > -90:
            return 1
        return 0

    @property
    def battery_text(self) -> str:
        """Battery level text."""
        if self.battery_level < 0:
            return "غير معروف"
        return f"{self.battery_level}%"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'address': self.address,
            'type': self.device_type.value,
            'status': self.status.value,
            'is_paired': self.is_paired,
            'is_connected': self.is_connected,
            'rssi': self.rssi,
            'manufacturer': self.manufacturer,
            'battery_level': self.battery_level,
        }


class BluetoothAdapterStatus(Enum):
    """Bluetooth adapter status."""
    ON = "on"
    OFF = "off"
    NOT_FOUND = "not_found"
    ERROR = "error"


class BluetoothManager:
    """
    Manage Bluetooth devices.

    Usage:
        bt = BluetoothManager()

        # Check adapter
        if bt.is_adapter_available():
            # Discover devices
            devices = bt.discover_devices(timeout=10)

            for device in devices:
                print(f"{device.device_type.icon} {device.display_name} - {device.status.name_ar}")

            # Pair with a device
            bt.pair_device(devices[0].address)

            # Connect
            bt.connect_device(devices[0].address)
    """

    def __init__(self):
        self._platform = sys.platform
        self._cached_devices: List[BluetoothDevice] = []
        self._last_scan: Optional[datetime] = None

    def get_adapter_status(self) -> BluetoothAdapterStatus:
        """Get the Bluetooth adapter status."""
        if self._platform == 'win32':
            return self._get_adapter_status_windows()
        else:
            return self._get_adapter_status_linux()

    def is_adapter_available(self) -> bool:
        """Check if Bluetooth adapter is available and enabled."""
        return self.get_adapter_status() == BluetoothAdapterStatus.ON

    def enable_adapter(self) -> bool:
        """Enable the Bluetooth adapter."""
        if self._platform == 'win32':
            return self._enable_adapter_windows()
        else:
            return self._enable_adapter_linux()

    def disable_adapter(self) -> bool:
        """Disable the Bluetooth adapter."""
        if self._platform == 'win32':
            return self._disable_adapter_windows()
        else:
            return self._disable_adapter_linux()

    def discover_devices(
        self,
        timeout: int = 10,
        on_device_found: Optional[Callable[[BluetoothDevice], None]] = None,
    ) -> List[BluetoothDevice]:
        """
        Discover nearby Bluetooth devices.

        Args:
            timeout: Discovery timeout in seconds
            on_device_found: Callback for each discovered device

        Returns:
            List of discovered BluetoothDevice objects
        """
        if self._platform == 'win32':
            devices = self._discover_windows(timeout)
        else:
            devices = self._discover_linux(timeout)

        # Merge with paired devices
        paired = self.get_paired_devices()
        paired_addresses = {d.address for d in paired}
        discovered_addresses = {d.address for d in devices}

        # Update paired info
        for device in devices:
            if device.address in paired_addresses:
                device.is_paired = True
                device.status = BluetoothStatus.PAIRED

        # Add paired devices not in discovery range
        for device in paired:
            if device.address not in discovered_addresses:
                device.status = BluetoothStatus.DISCONNECTED
                devices.append(device)

        self._cached_devices = devices
        self._last_scan = datetime.now()

        if on_device_found:
            for device in devices:
                on_device_found(device)

        app_logger.info(f"اكتشاف البلوتوث: {len(devices)} جهاز")
        return devices

    def get_paired_devices(self) -> List[BluetoothDevice]:
        """Get list of paired Bluetooth devices."""
        if self._platform == 'win32':
            return self._get_paired_windows()
        else:
            return self._get_paired_linux()

    def get_connected_devices(self) -> List[BluetoothDevice]:
        """Get list of currently connected devices."""
        paired = self.get_paired_devices()
        return [d for d in paired if d.is_connected]

    def pair_device(self, address: str) -> bool:
        """
        Pair with a Bluetooth device.

        Args:
            address: MAC address of the device

        Returns:
            True if pairing was successful
        """
        try:
            if self._platform == 'win32':
                return self._pair_windows(address)
            else:
                return self._pair_linux(address)
        except Exception as e:
            app_logger.error(f"فشل الاقتران: {address} - {e}")
            return False

    def unpair_device(self, address: str) -> bool:
        """Remove pairing with a device."""
        try:
            if self._platform == 'win32':
                return self._unpair_windows(address)
            else:
                return self._unpair_linux(address)
        except Exception as e:
            app_logger.error(f"فشل إلغاء الاقتران: {address} - {e}")
            return False

    def connect_device(self, address: str) -> bool:
        """Connect to a paired device."""
        try:
            if self._platform == 'win32':
                return self._connect_windows(address)
            else:
                return self._connect_linux(address)
        except Exception as e:
            app_logger.error(f"فشل الاتصال: {address} - {e}")
            return False

    def disconnect_device(self, address: str) -> bool:
        """Disconnect from a device."""
        try:
            if self._platform == 'win32':
                return self._disconnect_windows(address)
            else:
                return self._disconnect_linux(address)
        except Exception as e:
            app_logger.error(f"فشل قطع الاتصال: {address} - {e}")
            return False

    def get_device_info(self, address: str) -> Optional[BluetoothDevice]:
        """Get detailed info about a specific device."""
        for device in self._cached_devices:
            if device.address == address:
                return device
        # Try to find in paired devices
        for device in self.get_paired_devices():
            if device.address == address:
                return device
        return None

    # ═══════════════════════════════════════════════════════
    # Windows implementation
    # ═══════════════════════════════════════════════════════

    def _get_adapter_status_windows(self) -> BluetoothAdapterStatus:
        try:
            result = subprocess.run(
                ['powershell', '-Command', 'Get-PnpDevice -Class Bluetooth -Status OK | Select-Object -First 1 | ConvertTo-Json'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                return BluetoothAdapterStatus.ON
            return BluetoothAdapterStatus.OFF
        except Exception:
            return BluetoothAdapterStatus.NOT_FOUND

    def _enable_adapter_windows(self) -> bool:
        try:
            result = subprocess.run(
                ['powershell', '-Command', 'Get-PnpDevice -Class Bluetooth | Enable-PnpDevice -Confirm:$false'],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False

    def _disable_adapter_windows(self) -> bool:
        try:
            result = subprocess.run(
                ['powershell', '-Command', 'Get-PnpDevice -Class Bluetooth -Status OK | Disable-PnpDevice -Confirm:$false'],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False

    def _discover_windows(self, timeout: int) -> List[BluetoothDevice]:
        devices = []
        try:
            ps_script = (
                "$devices = @(); "
                "$paired = Get-PnpDevice -Class Bluetooth | Where-Object { $_.FriendlyName -ne 'Bluetooth Device (RFCOMM Protocol TDI)' -and $_.FriendlyName -notlike '*Radio*' }; "
                "foreach ($d in $paired) { "
                "  $devices += @{ Name = $d.FriendlyName; InstanceId = $d.InstanceId; Status = $d.Status; Class = $d.Class } "
                "}; "
                "$devices | ConvertTo-Json"
            )
            result = subprocess.run(['powershell', '-Command', ps_script], capture_output=True, text=True, timeout=timeout + 5)
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    name = item.get('Name', '')
                    if not name:
                        continue
                    instance_id = item.get('InstanceId', '')
                    # Extract MAC from InstanceId if possible
                    address = self._extract_mac_from_instance_id(instance_id)
                    status_str = item.get('Status', '')

                    bt_status = BluetoothStatus.AVAILABLE
                    is_connected = False
                    if status_str == 'OK':
                        bt_status = BluetoothStatus.CONNECTED
                        is_connected = True

                    device_type = self._classify_device_type(name)

                    devices.append(BluetoothDevice(
                        name=name,
                        address=address or instance_id,
                        device_type=device_type,
                        status=bt_status,
                        is_paired=True,
                        is_connected=is_connected,
                    ))
        except Exception as e:
            app_logger.error(f"Windows BT discovery error: {e}")

        return devices

    def _get_paired_windows(self) -> List[BluetoothDevice]:
        return self._discover_windows(5)

    def _pair_windows(self, address: str) -> bool:
        app_logger.info(f"Windows BT pairing requested for {address} - using system dialog")
        try:
            subprocess.run(
                ['explorer.exe', 'ms-settings:bluetooth'],
                capture_output=True, timeout=5
            )
            return True
        except Exception:
            return False

    def _unpair_windows(self, address: str) -> bool:
        try:
            ps_script = f"Get-PnpDevice | Where-Object {{ $_.InstanceId -like '*{address}*' }} | Remove-PnpDevice -Confirm:$false"
            result = subprocess.run(['powershell', '-Command', ps_script], capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except Exception:
            return False

    def _connect_windows(self, address: str) -> bool:
        try:
            ps_script = f"Get-PnpDevice | Where-Object {{ $_.InstanceId -like '*{address}*' }} | Enable-PnpDevice -Confirm:$false"
            result = subprocess.run(['powershell', '-Command', ps_script], capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except Exception:
            return False

    def _disconnect_windows(self, address: str) -> bool:
        try:
            ps_script = f"Get-PnpDevice | Where-Object {{ $_.InstanceId -like '*{address}*' }} | Disable-PnpDevice -Confirm:$false"
            result = subprocess.run(['powershell', '-Command', ps_script], capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except Exception:
            return False

    # ═══════════════════════════════════════════════════════
    # Linux implementation
    # ═══════════════════════════════════════════════════════

    def _get_adapter_status_linux(self) -> BluetoothAdapterStatus:
        try:
            result = subprocess.run(
                ['bluetoothctl', 'show'], capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                return BluetoothAdapterStatus.NOT_FOUND
            if 'Powered: yes' in result.stdout:
                return BluetoothAdapterStatus.ON
            return BluetoothAdapterStatus.OFF
        except FileNotFoundError:
            return BluetoothAdapterStatus.NOT_FOUND
        except Exception:
            return BluetoothAdapterStatus.ERROR

    def _enable_adapter_linux(self) -> bool:
        try:
            result = subprocess.run(
                ['bluetoothctl', 'power', 'on'], capture_output=True, text=True, timeout=5
            )
            return 'succeeded' in result.stdout.lower()
        except Exception:
            return False

    def _disable_adapter_linux(self) -> bool:
        try:
            result = subprocess.run(
                ['bluetoothctl', 'power', 'off'], capture_output=True, text=True, timeout=5
            )
            return 'succeeded' in result.stdout.lower()
        except Exception:
            return False

    def _discover_linux(self, timeout: int) -> List[BluetoothDevice]:
        devices = []
        try:
            # Start scan
            subprocess.run(
                ['bluetoothctl', 'scan', 'on'],
                capture_output=True, text=True, timeout=2
            )

            import time
            time.sleep(min(timeout, 10))

            # Stop scan
            subprocess.run(
                ['bluetoothctl', 'scan', 'off'],
                capture_output=True, text=True, timeout=2
            )

            # Get devices
            result = subprocess.run(
                ['bluetoothctl', 'devices'], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    # Format: Device XX:XX:XX:XX:XX:XX DeviceName
                    parts = line.strip().split(' ', 2)
                    if len(parts) >= 3 and parts[0] == 'Device':
                        address = parts[1]
                        name = parts[2]
                        device_type = self._classify_device_type(name)

                        device = BluetoothDevice(
                            name=name,
                            address=address,
                            device_type=device_type,
                            status=BluetoothStatus.AVAILABLE,
                        )

                        # Check if paired/connected
                        info = self._get_device_info_linux(address)
                        if info:
                            device.is_paired = info.get('paired', False)
                            device.is_connected = info.get('connected', False)
                            if device.is_connected:
                                device.status = BluetoothStatus.CONNECTED
                            elif device.is_paired:
                                device.status = BluetoothStatus.PAIRED

                        devices.append(device)

        except FileNotFoundError:
            app_logger.warning("bluetoothctl not found")
        except Exception as e:
            app_logger.error(f"Linux BT discovery error: {e}")

        return devices

    def _get_paired_linux(self) -> List[BluetoothDevice]:
        devices = []
        try:
            result = subprocess.run(
                ['bluetoothctl', 'paired-devices'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    parts = line.strip().split(' ', 2)
                    if len(parts) >= 3 and parts[0] == 'Device':
                        address = parts[1]
                        name = parts[2]
                        device_type = self._classify_device_type(name)

                        info = self._get_device_info_linux(address)
                        is_connected = info.get('connected', False) if info else False

                        devices.append(BluetoothDevice(
                            name=name,
                            address=address,
                            device_type=device_type,
                            status=BluetoothStatus.CONNECTED if is_connected else BluetoothStatus.PAIRED,
                            is_paired=True,
                            is_connected=is_connected,
                        ))
        except Exception as e:
            app_logger.error(f"Error getting paired devices: {e}")

        return devices

    def _get_device_info_linux(self, address: str) -> Optional[Dict[str, Any]]:
        try:
            result = subprocess.run(
                ['bluetoothctl', 'info', address],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                info = {}
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if 'Paired: yes' in line:
                        info['paired'] = True
                    elif 'Connected: yes' in line:
                        info['connected'] = True
                    elif 'Battery Percentage' in line:
                        try:
                            info['battery'] = int(line.split('(')[1].split(')')[0])
                        except Exception:
                            pass
                return info
        except Exception:
            pass
        return None

    def _pair_linux(self, address: str) -> bool:
        try:
            result = subprocess.run(
                ['bluetoothctl', 'pair', address],
                capture_output=True, text=True, timeout=30
            )
            return 'successful' in result.stdout.lower()
        except Exception:
            return False

    def _unpair_linux(self, address: str) -> bool:
        try:
            result = subprocess.run(
                ['bluetoothctl', 'remove', address],
                capture_output=True, text=True, timeout=10
            )
            return 'removed' in result.stdout.lower()
        except Exception:
            return False

    def _connect_linux(self, address: str) -> bool:
        try:
            result = subprocess.run(
                ['bluetoothctl', 'connect', address],
                capture_output=True, text=True, timeout=15
            )
            return 'successful' in result.stdout.lower()
        except Exception:
            return False

    def _disconnect_linux(self, address: str) -> bool:
        try:
            result = subprocess.run(
                ['bluetoothctl', 'disconnect', address],
                capture_output=True, text=True, timeout=10
            )
            return 'successful' in result.stdout.lower()
        except Exception:
            return False

    # ═══════════════════════════════════════════════════════
    # Helper methods
    # ═══════════════════════════════════════════════════════

    def _extract_mac_from_instance_id(self, instance_id: str) -> Optional[str]:
        """Extract MAC address from Windows InstanceId."""
        # InstanceId often contains MAC like BTHENUM\{...}_LOCALMFG&xxxx\X&XXXXXXXX&X&XXXXXXXXXXXX
        parts = instance_id.replace('_', '&').split('&')
        for part in parts:
            clean = part.replace(':', '').replace('-', '')
            if len(clean) == 12 and all(c in '0123456789ABCDEFabcdef' for c in clean):
                return ':'.join(clean[i:i + 2] for i in range(0, 12, 2)).upper()
        return None

    def _classify_device_type(self, name: str) -> BluetoothDeviceType:
        """Classify device type from name."""
        name_lower = name.lower()

        if any(kw in name_lower for kw in ['headphone', 'headset', 'earphone', 'earbud', 'airpod', 'buds']):
            return BluetoothDeviceType.HEADSET
        if any(kw in name_lower for kw in ['speaker', 'soundbar', 'audio', 'sound']):
            return BluetoothDeviceType.AUDIO
        if any(kw in name_lower for kw in ['keyboard', 'keychron', 'logitech k']):
            return BluetoothDeviceType.KEYBOARD
        if any(kw in name_lower for kw in ['mouse', 'trackpad', 'trackball', 'logitech m']):
            return BluetoothDeviceType.MOUSE
        if any(kw in name_lower for kw in ['phone', 'iphone', 'samsung', 'galaxy', 'pixel', 'huawei']):
            return BluetoothDeviceType.PHONE
        if any(kw in name_lower for kw in ['printer', 'print', 'hp ', 'epson', 'canon', 'brother']):
            return BluetoothDeviceType.PRINTER
        if any(kw in name_lower for kw in ['laptop', 'desktop', 'macbook', 'thinkpad']):
            return BluetoothDeviceType.COMPUTER
        if any(kw in name_lower for kw in ['camera', 'scan', 'imag']):
            return BluetoothDeviceType.IMAGING

        return BluetoothDeviceType.UNKNOWN
