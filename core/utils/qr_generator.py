"""
QR Code Generator
=================
Generate QR codes for employee badges, reports, and links.

Features:
- Generate QR codes from text/URLs
- Customizable size and colors
- Save as image file
- Convert to QPixmap for PyQt5

Usage:
    from core.utils import generate_qr_code, qr_to_pixmap

    # Generate and save
    generate_qr_code("EMP:12345", "employee_qr.png")

    # For PyQt5 widget
    pixmap = qr_to_pixmap("https://example.com/employee/123")
    label.setPixmap(pixmap)

    # With custom options
    from core.utils import QRGenerator
    qr = QRGenerator()
    qr.set_data("Employee: Mohamed")
    qr.set_colors(fill='#2563eb', back='white')
    qr.save("badge_qr.png")
"""

from typing import Optional, Tuple
from io import BytesIO
from pathlib import Path

try:
    import qrcode
    from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False

from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QByteArray, QBuffer

from core.logging import app_logger


# Error correction levels
ERROR_LEVELS = {
    'L': ERROR_CORRECT_L if QRCODE_AVAILABLE else 0,  # 7% recovery
    'M': ERROR_CORRECT_M if QRCODE_AVAILABLE else 1,  # 15% recovery
    'Q': ERROR_CORRECT_Q if QRCODE_AVAILABLE else 2,  # 25% recovery
    'H': ERROR_CORRECT_H if QRCODE_AVAILABLE else 3,  # 30% recovery
}


class QRGenerator:
    """Generate QR codes with customization options."""

    def __init__(self):
        """Initialize QR generator."""
        if not QRCODE_AVAILABLE:
            raise ImportError("qrcode not installed. Run: pip install qrcode[pil]")

        self._data: str = ""
        self._version: int = 1  # 1-40, auto-determined if None
        self._error_correction = ERROR_CORRECT_M
        self._box_size: int = 10  # Pixels per box
        self._border: int = 4  # Border boxes
        self._fill_color: str = "black"
        self._back_color: str = "white"

        app_logger.debug("QRGenerator initialized")

    def set_data(self, data: str) -> 'QRGenerator':
        """
        Set QR code data.

        Args:
            data: Text or URL to encode

        Returns:
            Self for chaining
        """
        self._data = data
        return self

    def set_size(self, box_size: int = 10, border: int = 4) -> 'QRGenerator':
        """
        Set QR code size.

        Args:
            box_size: Pixels per box (default 10)
            border: Border width in boxes (default 4)

        Returns:
            Self for chaining
        """
        self._box_size = box_size
        self._border = border
        return self

    def set_colors(
        self,
        fill: str = "black",
        back: str = "white"
    ) -> 'QRGenerator':
        """
        Set QR code colors.

        Args:
            fill: Fill color (foreground)
            back: Background color

        Returns:
            Self for chaining
        """
        self._fill_color = fill
        self._back_color = back
        return self

    def set_error_correction(self, level: str = 'M') -> 'QRGenerator':
        """
        Set error correction level.

        Args:
            level: 'L', 'M', 'Q', or 'H'

        Returns:
            Self for chaining
        """
        self._error_correction = ERROR_LEVELS.get(level.upper(), ERROR_CORRECT_M)
        return self

    def generate(self) -> 'qrcode.image.pil.PilImage':
        """
        Generate QR code image.

        Returns:
            PIL Image object
        """
        if not self._data:
            raise ValueError("No data set for QR code")

        qr = qrcode.QRCode(
            version=self._version,
            error_correction=self._error_correction,
            box_size=self._box_size,
            border=self._border
        )

        qr.add_data(self._data)
        qr.make(fit=True)

        img = qr.make_image(
            fill_color=self._fill_color,
            back_color=self._back_color
        )

        return img

    def save(self, path: str) -> bool:
        """
        Save QR code to file.

        Args:
            path: Output file path

        Returns:
            True if successful
        """
        try:
            img = self.generate()

            # Ensure directory exists
            Path(path).parent.mkdir(parents=True, exist_ok=True)

            img.save(path)
            app_logger.info(f"QR code saved: {path}")
            return True

        except Exception as e:
            app_logger.error(f"Failed to save QR code: {e}")
            return False

    def to_bytes(self, format: str = "PNG") -> bytes:
        """
        Get QR code as bytes.

        Args:
            format: Image format (PNG, JPEG, etc.)

        Returns:
            Image bytes
        """
        img = self.generate()
        buffer = BytesIO()
        img.save(buffer, format=format)
        return buffer.getvalue()

    def to_pixmap(self) -> QPixmap:
        """
        Get QR code as QPixmap for PyQt5.

        Returns:
            QPixmap object
        """
        img_bytes = self.to_bytes("PNG")

        pixmap = QPixmap()
        pixmap.loadFromData(img_bytes)

        return pixmap

    def to_base64(self, format: str = "PNG") -> str:
        """
        Get QR code as base64 string.

        Args:
            format: Image format

        Returns:
            Base64 encoded string
        """
        import base64
        img_bytes = self.to_bytes(format)
        return base64.b64encode(img_bytes).decode('utf-8')


# Convenience functions

def generate_qr_code(
    data: str,
    output_path: str,
    size: int = 10,
    fill_color: str = "black",
    back_color: str = "white"
) -> bool:
    """
    Generate and save QR code.

    Args:
        data: Text/URL to encode
        output_path: Output file path
        size: Box size in pixels
        fill_color: Foreground color
        back_color: Background color

    Returns:
        True if successful
    """
    try:
        qr = QRGenerator()
        qr.set_data(data)
        qr.set_size(box_size=size)
        qr.set_colors(fill=fill_color, back=back_color)
        return qr.save(output_path)
    except Exception as e:
        app_logger.error(f"QR generation failed: {e}")
        return False


def qr_to_pixmap(
    data: str,
    size: int = 10,
    fill_color: str = "black",
    back_color: str = "white"
) -> Optional[QPixmap]:
    """
    Generate QR code as QPixmap.

    Args:
        data: Text/URL to encode
        size: Box size in pixels
        fill_color: Foreground color
        back_color: Background color

    Returns:
        QPixmap or None if failed
    """
    try:
        qr = QRGenerator()
        qr.set_data(data)
        qr.set_size(box_size=size)
        qr.set_colors(fill=fill_color, back=back_color)
        return qr.to_pixmap()
    except Exception as e:
        app_logger.error(f"QR to pixmap failed: {e}")
        return None


def generate_employee_qr(
    employee_id: int,
    employee_name: str = "",
    output_path: Optional[str] = None
) -> Optional[QPixmap]:
    """
    Generate QR code for employee badge.

    Args:
        employee_id: Employee ID
        employee_name: Employee name (optional)
        output_path: Save path (optional)

    Returns:
        QPixmap or None
    """
    # Create employee data string
    data = f"EMP:{employee_id}"
    if employee_name:
        data += f"|{employee_name}"

    qr = QRGenerator()
    qr.set_data(data)
    qr.set_size(box_size=8)
    qr.set_colors(fill='#1e3a5f', back='white')

    if output_path:
        qr.save(output_path)

    return qr.to_pixmap()


def generate_url_qr(
    url: str,
    output_path: Optional[str] = None
) -> Optional[QPixmap]:
    """
    Generate QR code for URL.

    Args:
        url: URL to encode
        output_path: Save path (optional)

    Returns:
        QPixmap or None
    """
    qr = QRGenerator()
    qr.set_data(url)
    qr.set_size(box_size=8)
    qr.set_error_correction('M')

    if output_path:
        qr.save(output_path)

    return qr.to_pixmap()
