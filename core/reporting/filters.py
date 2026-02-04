"""
Custom Jinja2 Filters
=====================
Custom filters for report templates with Arabic/RTL support.

Includes:
- Currency formatting
- Date/Time formatting
- Number formatting
- Text transformations
- Arabic utilities
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Any, Optional, Union
import locale


def format_currency(
    value: Union[int, float, Decimal, None],
    currency: str = "ر.س",
    decimals: int = 2,
    show_currency: bool = True
) -> str:
    """
    Format number as currency.

    Args:
        value: Number to format
        currency: Currency symbol (default: Saudi Riyal)
        decimals: Decimal places
        show_currency: Whether to show currency symbol

    Returns:
        Formatted currency string
    """
    if value is None:
        return "-"

    try:
        num = float(value)
        formatted = f"{num:,.{decimals}f}"

        if show_currency:
            return f"{formatted} {currency}"
        return formatted

    except (ValueError, TypeError):
        return str(value)


def format_number(
    value: Union[int, float, Decimal, None],
    decimals: int = 0,
    thousands_sep: str = ",",
    decimal_sep: str = "."
) -> str:
    """
    Format number with separators.

    Args:
        value: Number to format
        decimals: Decimal places
        thousands_sep: Thousands separator
        decimal_sep: Decimal separator

    Returns:
        Formatted number string
    """
    if value is None:
        return "-"

    try:
        num = float(value)

        if decimals == 0:
            formatted = f"{int(num):,}"
        else:
            formatted = f"{num:,.{decimals}f}"

        # Replace separators if custom
        if thousands_sep != "," or decimal_sep != ".":
            formatted = formatted.replace(",", "TEMP")
            formatted = formatted.replace(".", decimal_sep)
            formatted = formatted.replace("TEMP", thousands_sep)

        return formatted

    except (ValueError, TypeError):
        return str(value)


def format_percentage(
    value: Union[int, float, Decimal, None],
    decimals: int = 1,
    multiply: bool = False
) -> str:
    """
    Format number as percentage.

    Args:
        value: Number to format (0-100 or 0-1 if multiply=True)
        decimals: Decimal places
        multiply: Multiply by 100 first

    Returns:
        Formatted percentage string
    """
    if value is None:
        return "-"

    try:
        num = float(value)
        if multiply:
            num *= 100
        return f"{num:.{decimals}f}%"

    except (ValueError, TypeError):
        return str(value)


def format_date(
    value: Union[datetime, date, str, None],
    format_str: str = "%Y/%m/%d",
    arabic: bool = False
) -> str:
    """
    Format date value.

    Args:
        value: Date to format
        format_str: Date format string
        arabic: Use Arabic month names

    Returns:
        Formatted date string
    """
    if value is None:
        return "-"

    arabic_months = {
        1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل",
        5: "مايو", 6: "يونيو", 7: "يوليو", 8: "أغسطس",
        9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"
    }

    arabic_days = {
        0: "الاثنين", 1: "الثلاثاء", 2: "الأربعاء",
        3: "الخميس", 4: "الجمعة", 5: "السبت", 6: "الأحد"
    }

    try:
        if isinstance(value, str):
            # Try common formats
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y"]:
                try:
                    value = datetime.strptime(value, fmt)
                    break
                except ValueError:
                    continue
            else:
                return value

        if isinstance(value, date) and not isinstance(value, datetime):
            value = datetime.combine(value, datetime.min.time())

        formatted = value.strftime(format_str)

        if arabic:
            # Replace month number with Arabic name
            for num, name in arabic_months.items():
                formatted = formatted.replace(f"/{num:02d}/", f"/{name}/")

            # Replace day name if present
            for num, name in arabic_days.items():
                day_en = value.strftime("%A")
                if day_en in formatted:
                    formatted = formatted.replace(day_en, name)

        return formatted

    except (ValueError, TypeError, AttributeError):
        return str(value)


def format_datetime(
    value: Union[datetime, str, None],
    format_str: str = "%Y/%m/%d %H:%M",
    arabic: bool = False
) -> str:
    """
    Format datetime value.

    Args:
        value: Datetime to format
        format_str: Datetime format string
        arabic: Use Arabic formatting

    Returns:
        Formatted datetime string
    """
    return format_date(value, format_str, arabic)


def format_time(
    value: Union[datetime, str, None],
    format_str: str = "%H:%M",
    arabic: bool = False
) -> str:
    """
    Format time value.

    Args:
        value: Time to format
        format_str: Time format string
        arabic: Use Arabic AM/PM

    Returns:
        Formatted time string
    """
    if value is None:
        return "-"

    try:
        if isinstance(value, str):
            for fmt in ["%H:%M:%S", "%H:%M", "%I:%M %p"]:
                try:
                    value = datetime.strptime(value, fmt)
                    break
                except ValueError:
                    continue
            else:
                return value

        formatted = value.strftime(format_str)

        if arabic:
            formatted = formatted.replace("AM", "ص")
            formatted = formatted.replace("PM", "م")

        return formatted

    except (ValueError, TypeError, AttributeError):
        return str(value)


def truncate(
    value: Optional[str],
    length: int = 50,
    suffix: str = "..."
) -> str:
    """
    Truncate text to specified length.

    Args:
        value: Text to truncate
        length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if value is None:
        return ""

    text = str(value)
    if len(text) <= length:
        return text

    return text[:length - len(suffix)] + suffix


def nl2br(value: Optional[str]) -> str:
    """
    Convert newlines to <br> tags.

    Args:
        value: Text with newlines

    Returns:
        Text with <br> tags
    """
    if value is None:
        return ""

    return str(value).replace("\n", "<br>")


def strip_tags(value: Optional[str]) -> str:
    """
    Remove HTML tags from text.

    Args:
        value: HTML text

    Returns:
        Plain text
    """
    if value is None:
        return ""

    import re
    return re.sub(r'<[^>]+>', '', str(value))


def default_if_none(value: Any, default: Any = "-") -> Any:
    """
    Return default if value is None.

    Args:
        value: Value to check
        default: Default value

    Returns:
        Value or default
    """
    return default if value is None else value


def yesno(
    value: Any,
    yes: str = "نعم",
    no: str = "لا",
    null: str = "-"
) -> str:
    """
    Convert boolean to yes/no text.

    Args:
        value: Boolean value
        yes: Text for True
        no: Text for False
        null: Text for None

    Returns:
        Yes/No text
    """
    if value is None:
        return null
    return yes if value else no


def arabic_number(value: Union[int, float, None]) -> str:
    """
    Convert number to Arabic numerals.

    Args:
        value: Number to convert

    Returns:
        Arabic numeral string
    """
    if value is None:
        return ""

    arabic_digits = {
        '0': '٠', '1': '١', '2': '٢', '3': '٣', '4': '٤',
        '5': '٥', '6': '٦', '7': '٧', '8': '٨', '9': '٩'
    }

    text = str(value)
    for eng, ara in arabic_digits.items():
        text = text.replace(eng, ara)

    return text


def phone_format(value: Optional[str], country: str = "SA") -> str:
    """
    Format phone number.

    Args:
        value: Phone number
        country: Country code

    Returns:
        Formatted phone number
    """
    if value is None:
        return "-"

    # Remove non-digits
    digits = ''.join(c for c in str(value) if c.isdigit())

    if country == "SA":
        # Saudi format: +966 5X XXX XXXX
        if len(digits) == 9 and digits.startswith("5"):
            return f"+966 {digits[0:2]} {digits[2:5]} {digits[5:]}"
        elif len(digits) == 10 and digits.startswith("05"):
            return f"+966 {digits[1:3]} {digits[3:6]} {digits[6:]}"
        elif len(digits) == 12 and digits.startswith("966"):
            return f"+{digits[0:3]} {digits[3:5]} {digits[5:8]} {digits[8:]}"

    return value


def status_badge(
    value: Optional[str],
    mapping: Optional[dict] = None
) -> str:
    """
    Generate HTML status badge.

    Args:
        value: Status text
        mapping: Status to color mapping

    Returns:
        HTML badge
    """
    if value is None:
        return ""

    default_mapping = {
        "نشط": "#10b981",
        "active": "#10b981",
        "معلق": "#f59e0b",
        "pending": "#f59e0b",
        "غير نشط": "#ef4444",
        "inactive": "#ef4444",
        "مكتمل": "#3b82f6",
        "completed": "#3b82f6"
    }

    colors = mapping or default_mapping
    color = colors.get(str(value).lower(), "#6b7280")

    return f'<span style="background:{color};color:white;padding:2px 8px;border-radius:4px;font-size:12px;">{value}</span>'


def sum_column(items: list, column: str) -> float:
    """
    Sum a column in a list of dicts.

    Args:
        items: List of dictionaries
        column: Column name to sum

    Returns:
        Sum value
    """
    try:
        return sum(
            float(item.get(column, 0) or 0)
            for item in items
        )
    except (ValueError, TypeError):
        return 0


def avg_column(items: list, column: str) -> float:
    """
    Average a column in a list of dicts.

    Args:
        items: List of dictionaries
        column: Column name to average

    Returns:
        Average value
    """
    try:
        values = [
            float(item.get(column, 0) or 0)
            for item in items
        ]
        return sum(values) / len(values) if values else 0
    except (ValueError, TypeError):
        return 0


def count_column(items: list, column: str, value: Any = None) -> int:
    """
    Count items or items matching a value.

    Args:
        items: List of dictionaries
        column: Column name
        value: Value to match (None = count all)

    Returns:
        Count
    """
    if value is None:
        return len(items)

    return sum(1 for item in items if item.get(column) == value)


def group_by(items: list, column: str) -> dict:
    """
    Group items by column value.

    Args:
        items: List of dictionaries
        column: Column to group by

    Returns:
        Grouped dictionary
    """
    result = {}
    for item in items:
        key = item.get(column, "")
        if key not in result:
            result[key] = []
        result[key].append(item)
    return result


def sort_by(items: list, column: str, reverse: bool = False) -> list:
    """
    Sort items by column.

    Args:
        items: List of dictionaries
        column: Column to sort by
        reverse: Reverse order

    Returns:
        Sorted list
    """
    try:
        return sorted(
            items,
            key=lambda x: x.get(column, ""),
            reverse=reverse
        )
    except TypeError:
        return items


# All available filters
TEMPLATE_FILTERS = {
    # Currency/Numbers
    "currency": format_currency,
    "number": format_number,
    "percentage": format_percentage,
    "arabic_number": arabic_number,

    # Date/Time
    "date": format_date,
    "datetime": format_datetime,
    "time": format_time,

    # Text
    "truncate": truncate,
    "nl2br": nl2br,
    "strip_tags": strip_tags,
    "default": default_if_none,
    "yesno": yesno,
    "phone": phone_format,

    # HTML
    "status_badge": status_badge,

    # Aggregation
    "sum_column": sum_column,
    "avg_column": avg_column,
    "count_column": count_column,
    "group_by": group_by,
    "sort_by": sort_by
}
