"""
Data Formatters
===============
Human-readable formatting for numbers, dates, and file sizes.

Uses the `humanize` library for intelligent formatting with Arabic support.

Usage:
    from core.utils import (
        format_number,
        format_currency,
        format_date,
        format_time_ago,
        format_file_size,
        format_duration
    )

    # Numbers
    format_number(5000)                    # "5,000"
    format_currency(5000)                  # "5,000 ر.س"

    # Dates
    format_date(datetime.now())            # "3 فبراير 2026"
    format_time_ago(datetime.now() - timedelta(minutes=5))  # "منذ 5 دقائق"

    # File sizes
    format_file_size(1024000)              # "1.0 MB"
"""

import humanize
from datetime import datetime, timedelta
from typing import Union, Optional


# Arabic locale (deferred activation to avoid side effects at import)
_arabic_available = False
_arabic_activated = False


def _ensure_arabic():
    """Activate Arabic locale on first use (lazy initialization)."""
    global _arabic_available, _arabic_activated
    if _arabic_activated:
        return
    _arabic_activated = True
    try:
        humanize.activate("ar")
        _arabic_available = True
    except Exception:
        _arabic_available = False


# ========== Number Formatting ==========

def format_number(value: Union[int, float], use_comma: bool = True) -> str:
    """
    Format number with thousand separators.

    Args:
        value: Number to format
        use_comma: Use comma separators (default True)

    Returns:
        Formatted string (e.g., "5,000")
    """
    if value is None:
        return "0"

    try:
        _ensure_arabic()
        if use_comma:
            return humanize.intcomma(int(value))
        return str(int(value))
    except (ValueError, TypeError):
        return str(value)


def format_decimal(value: Union[int, float], decimals: int = 2) -> str:
    """
    Format number with decimal places and thousand separators.

    Args:
        value: Number to format
        decimals: Number of decimal places

    Returns:
        Formatted string (e.g., "5,000.00")
    """
    if value is None:
        return "0.00"

    try:
        formatted = f"{float(value):,.{decimals}f}"
        return formatted
    except (ValueError, TypeError):
        return str(value)


def format_currency(
    value: Union[int, float],
    currency: str = "ر.س",
    decimals: int = 0
) -> str:
    """
    Format number as currency.

    Args:
        value: Amount to format
        currency: Currency symbol (default "ر.س" for Saudi Riyal)
        decimals: Decimal places (default 0)

    Returns:
        Formatted string (e.g., "5,000 ر.س")
    """
    if value is None:
        return f"0 {currency}"

    try:
        _ensure_arabic()
        if decimals > 0:
            formatted = f"{float(value):,.{decimals}f}"
        else:
            formatted = humanize.intcomma(int(value))
        return f"{formatted} {currency}"
    except (ValueError, TypeError):
        return f"{value} {currency}"


def format_percentage(value: Union[int, float], decimals: int = 1) -> str:
    """
    Format number as percentage.

    Args:
        value: Percentage value (0-100)
        decimals: Decimal places

    Returns:
        Formatted string (e.g., "75.5%")
    """
    if value is None:
        return "0%"

    try:
        return f"{float(value):.{decimals}f}%"
    except (ValueError, TypeError):
        return f"{value}%"


def format_large_number(value: Union[int, float]) -> str:
    """
    Format large numbers in word form.

    Args:
        value: Number to format

    Returns:
        Formatted string (e.g., "1 million", "2.5 billion")
    """
    if value is None:
        return "0"

    try:
        _ensure_arabic()
        return humanize.intword(int(value))
    except (ValueError, TypeError):
        return str(value)


# ========== Date/Time Formatting ==========

def format_date(
    date: Union[datetime, str],
    include_year: bool = True,
    format_style: str = "full"
) -> str:
    """
    Format date in Arabic style.

    Args:
        date: Date to format
        include_year: Include year in output
        format_style: "full", "short", or "numeric"

    Returns:
        Formatted string (e.g., "3 فبراير 2026")
    """
    if date is None:
        return ""

    try:
        if isinstance(date, str):
            date = datetime.fromisoformat(date)

        arabic_months = [
            "يناير", "فبراير", "مارس", "أبريل",
            "مايو", "يونيو", "يوليو", "أغسطس",
            "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
        ]

        if format_style == "numeric":
            if include_year:
                return date.strftime("%Y/%m/%d")
            return date.strftime("%m/%d")

        if format_style == "short":
            month = arabic_months[date.month - 1][:3]
        else:
            month = arabic_months[date.month - 1]

        if include_year:
            return f"{date.day} {month} {date.year}"
        return f"{date.day} {month}"

    except Exception:
        return str(date)


def format_time(dt: Union[datetime, str], include_seconds: bool = False) -> str:
    """
    Format time.

    Args:
        dt: Time to format
        include_seconds: Include seconds

    Returns:
        Formatted string (e.g., "14:30")
    """
    if dt is None:
        return ""

    try:
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt)

        if include_seconds:
            return dt.strftime("%H:%M:%S")
        return dt.strftime("%H:%M")
    except Exception:
        return str(dt)


def format_datetime(dt: Union[datetime, str]) -> str:
    """
    Format full datetime.

    Args:
        dt: Datetime to format

    Returns:
        Formatted string (e.g., "3 فبراير 2026 - 14:30")
    """
    if dt is None:
        return ""

    try:
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt)

        date_str = format_date(dt)
        time_str = format_time(dt)
        return f"{date_str} - {time_str}"
    except Exception:
        return str(dt)


def format_time_ago(
    dt: Union[datetime, str],
    add_prefix: bool = True
) -> str:
    """
    Format datetime as relative time.

    Args:
        dt: Datetime to format
        add_prefix: Add "منذ" prefix

    Returns:
        Formatted string (e.g., "منذ 5 دقائق")
    """
    if dt is None:
        return ""

    try:
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt)

        now = datetime.now()
        diff = now - dt

        # Use humanize for Arabic
        _ensure_arabic()
        result = humanize.naturaltime(dt)

        # Manual fallback if humanize fails
        if not _arabic_available or result == str(dt):
            seconds = diff.total_seconds()
            if seconds < 60:
                result = "الآن"
            elif seconds < 3600:
                minutes = int(seconds / 60)
                result = f"{minutes} دقيقة" if minutes == 1 else f"{minutes} دقائق"
            elif seconds < 86400:
                hours = int(seconds / 3600)
                result = f"{hours} ساعة" if hours == 1 else f"{hours} ساعات"
            else:
                days = int(seconds / 86400)
                result = f"{days} يوم" if days == 1 else f"{days} أيام"

            if add_prefix and result != "الآن":
                result = f"منذ {result}"

        return result

    except Exception:
        return str(dt)


def format_natural_day(date: Union[datetime, str]) -> str:
    """
    Format date as natural day reference.

    Args:
        date: Date to format

    Returns:
        "اليوم", "أمس", "غداً", or formatted date
    """
    if date is None:
        return ""

    try:
        if isinstance(date, str):
            date = datetime.fromisoformat(date)

        today = datetime.now().date()
        target = date.date() if isinstance(date, datetime) else date

        diff = (target - today).days

        if diff == 0:
            return "اليوم"
        elif diff == -1:
            return "أمس"
        elif diff == 1:
            return "غداً"
        elif -7 <= diff < -1:
            return f"منذ {abs(diff)} أيام"
        elif 1 < diff <= 7:
            return f"بعد {diff} أيام"
        else:
            return format_date(date)

    except Exception:
        return str(date)


# ========== File Size Formatting ==========

def format_file_size(size_bytes: int, binary: bool = True) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes
        binary: Use binary units (1024) vs decimal (1000)

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    if size_bytes is None or size_bytes < 0:
        return "0 B"

    try:
        _ensure_arabic()
        return humanize.naturalsize(size_bytes, binary=binary)
    except Exception:
        return f"{size_bytes} B"


# ========== Duration Formatting ==========

def format_duration(
    seconds: Union[int, float, timedelta],
    granularity: int = 2
) -> str:
    """
    Format duration in human-readable format.

    Args:
        seconds: Duration in seconds or timedelta
        granularity: Number of units to show

    Returns:
        Formatted string (e.g., "2 ساعات و 30 دقيقة")
    """
    if seconds is None:
        return "0 ثانية"

    try:
        if isinstance(seconds, timedelta):
            seconds = seconds.total_seconds()

        seconds = int(seconds)

        if seconds < 60:
            return f"{seconds} ثانية"

        units = [
            (86400, "يوم", "أيام"),
            (3600, "ساعة", "ساعات"),
            (60, "دقيقة", "دقائق"),
            (1, "ثانية", "ثواني")
        ]

        parts = []
        remaining = seconds

        for unit_seconds, singular, plural in units:
            if remaining >= unit_seconds:
                count = remaining // unit_seconds
                remaining = remaining % unit_seconds
                unit_name = singular if count == 1 else plural
                parts.append(f"{count} {unit_name}")

            if len(parts) >= granularity:
                break

        return " و ".join(parts) if parts else "0 ثانية"

    except Exception:
        return str(seconds)


# ========== List/Count Formatting ==========

def format_count(count: int, singular: str, plural: str = None) -> str:
    """
    Format count with appropriate singular/plural form.

    Args:
        count: The count
        singular: Singular form (e.g., "موظف")
        plural: Plural form (e.g., "موظفين"), defaults to singular

    Returns:
        Formatted string (e.g., "5 موظفين")
    """
    if plural is None:
        plural = singular

    if count is None:
        count = 0

    word = singular if count == 1 else plural
    return f"{format_number(count)} {word}"


def format_ordinal(number: int) -> str:
    """
    Format number as ordinal.

    Args:
        number: Number to format

    Returns:
        Ordinal string (e.g., "الأول", "الثاني")
    """
    if number is None or number < 1:
        return ""

    try:
        _ensure_arabic()
        return humanize.ordinal(number)
    except Exception:
        return f"#{number}"
