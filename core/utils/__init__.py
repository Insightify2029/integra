"""
Core Utilities
==============
Utility functions and helpers.
"""

from .icons import (
    Icons,
    get_icon,
    icon
)

from .formatters import (
    # Numbers
    format_number,
    format_decimal,
    format_currency,
    format_percentage,
    format_large_number,
    # Dates
    format_date,
    format_time,
    format_datetime,
    format_time_ago,
    format_natural_day,
    # File size
    format_file_size,
    # Duration
    format_duration,
    # Count
    format_count,
    format_ordinal
)

from .qr_generator import (
    QRGenerator,
    generate_qr_code,
    qr_to_pixmap,
    generate_employee_qr,
    generate_url_qr
)

__all__ = [
    # Icons
    'Icons',
    'get_icon',
    'icon',
    # Number formatters
    'format_number',
    'format_decimal',
    'format_currency',
    'format_percentage',
    'format_large_number',
    # Date formatters
    'format_date',
    'format_time',
    'format_datetime',
    'format_time_ago',
    'format_natural_day',
    # File size
    'format_file_size',
    # Duration
    'format_duration',
    # Count
    'format_count',
    'format_ordinal',
    # QR Code
    'QRGenerator',
    'generate_qr_code',
    'qr_to_pixmap',
    'generate_employee_qr',
    'generate_url_qr'
]
