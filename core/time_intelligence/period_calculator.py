"""
Period Calculator
=================
Calculates date ranges for various business periods.
"""

from datetime import date, timedelta
from typing import Optional


class PeriodCalculator:
    """Calculates date ranges for common business periods."""

    def current_month(self, ref: Optional[date] = None) -> tuple:
        """Get current month range."""
        if ref is None:
            ref = date.today()
        start = date(ref.year, ref.month, 1)
        if ref.month == 12:
            end = date(ref.year, 12, 31)
        else:
            end = date(ref.year, ref.month + 1, 1) - timedelta(days=1)
        return start, end

    def previous_month(self, ref: Optional[date] = None) -> tuple:
        """Get previous month range."""
        if ref is None:
            ref = date.today()
        if ref.month == 1:
            start = date(ref.year - 1, 12, 1)
            end = date(ref.year - 1, 12, 31)
        else:
            start = date(ref.year, ref.month - 1, 1)
            end = date(ref.year, ref.month, 1) - timedelta(days=1)
        return start, end

    def current_quarter(self, ref: Optional[date] = None) -> tuple:
        """Get current quarter range."""
        if ref is None:
            ref = date.today()
        q = (ref.month - 1) // 3 + 1
        start_month = (q - 1) * 3 + 1
        start = date(ref.year, start_month, 1)
        end_month = start_month + 2
        if end_month == 12:
            end = date(ref.year, 12, 31)
        else:
            end = date(ref.year, end_month + 1, 1) - timedelta(days=1)
        return start, end

    def previous_quarter(self, ref: Optional[date] = None) -> tuple:
        """Get previous quarter range."""
        if ref is None:
            ref = date.today()
        q = (ref.month - 1) // 3 + 1
        if q == 1:
            return date(ref.year - 1, 10, 1), date(ref.year - 1, 12, 31)
        start_month = (q - 2) * 3 + 1
        end_month = start_month + 2
        start = date(ref.year, start_month, 1)
        if end_month == 12:
            end = date(ref.year, 12, 31)
        else:
            end = date(ref.year, end_month + 1, 1) - timedelta(days=1)
        return start, end

    def current_year(self, ref: Optional[date] = None) -> tuple:
        """Get current year range."""
        if ref is None:
            ref = date.today()
        return date(ref.year, 1, 1), date(ref.year, 12, 31)

    def previous_year(self, ref: Optional[date] = None) -> tuple:
        """Get previous year range."""
        if ref is None:
            ref = date.today()
        return date(ref.year - 1, 1, 1), date(ref.year - 1, 12, 31)

    def current_week(self, ref: Optional[date] = None, week_start: int = 6) -> tuple:
        """Get current week range. Default week starts Sunday (weekday=6)."""
        if ref is None:
            ref = date.today()
        days_since_start = (ref.weekday() - week_start) % 7
        start = ref - timedelta(days=days_since_start)
        end = start + timedelta(days=6)
        return start, end

    def previous_week(self, ref: Optional[date] = None, week_start: int = 6) -> tuple:
        """Get previous week range."""
        if ref is None:
            ref = date.today()
        current_start, _ = self.current_week(ref, week_start)
        prev_end = current_start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=6)
        return prev_start, prev_end

    def year_to_date(self, ref: Optional[date] = None) -> tuple:
        """Year-to-date range."""
        if ref is None:
            ref = date.today()
        return date(ref.year, 1, 1), ref

    def last_n_days(self, n: int, ref: Optional[date] = None) -> tuple:
        """Last N days range."""
        if ref is None:
            ref = date.today()
        return ref - timedelta(days=n), ref

    def last_n_months(self, n: int, ref: Optional[date] = None) -> tuple:
        """Last N months range (approximate)."""
        if ref is None:
            ref = date.today()
        start_month = ref.month - n
        start_year = ref.year
        while start_month <= 0:
            start_month += 12
            start_year -= 1
        return date(start_year, start_month, 1), ref

    def same_period_last_year(self, start: date, end: date) -> tuple:
        """Get the same period from last year."""
        ly_start = date(start.year - 1, start.month, min(start.day, 28))
        ly_end = date(end.year - 1, end.month, min(end.day, 28))
        return ly_start, ly_end

    def fiscal_quarter(self, ref: Optional[date] = None, fiscal_year_start_month: int = 1) -> tuple:
        """Get fiscal quarter range with custom fiscal year start."""
        if ref is None:
            ref = date.today()

        # Adjust month to fiscal calendar
        adjusted_month = (ref.month - fiscal_year_start_month) % 12 + 1
        q = (adjusted_month - 1) // 3 + 1

        start_month = ((q - 1) * 3 + fiscal_year_start_month - 1) % 12 + 1
        start_year = ref.year if start_month <= ref.month else ref.year - 1
        start = date(start_year, start_month, 1)

        end_month = (start_month + 2 - 1) % 12 + 1
        end_year = start_year if end_month >= start_month else start_year + 1
        if end_month == 12:
            end = date(end_year, 12, 31)
        else:
            end = date(end_year, end_month + 1, 1) - timedelta(days=1)

        return start, end

    def get_period_label(self, start: date, end: date) -> str:
        """Generate a human-readable Arabic label for a period."""
        from .system_time import MONTHS_AR

        if start.year == end.year and start.month == end.month:
            return f"{MONTHS_AR[start.month - 1]} {start.year}"

        if start == date(start.year, 1, 1) and end == date(start.year, 12, 31):
            return f"سنة {start.year}"

        q_start = (start.month - 1) // 3 + 1
        q_end = (end.month - 1) // 3 + 1
        if q_start == q_end and start.year == end.year:
            return f"Q{q_start} {start.year}"

        return f"{start.day}/{start.month}/{start.year} - {end.day}/{end.month}/{end.year}"


# Singleton
_calculator: Optional[PeriodCalculator] = None


def get_period_calculator() -> PeriodCalculator:
    """Get singleton PeriodCalculator instance."""
    global _calculator
    if _calculator is None:
        _calculator = PeriodCalculator()
    return _calculator
