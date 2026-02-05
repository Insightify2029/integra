"""
System Time Core
================
Core time utilities for INTEGRA - Gregorian + Hijri calendar support.
"""

from datetime import datetime, date, time, timedelta
from typing import Optional


# Arabic day names
DAYS_AR = [
    "الاثنين", "الثلاثاء", "الأربعاء", "الخميس",
    "الجمعة", "السبت", "الأحد"
]

DAYS_EN = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday"
]

# Arabic month names (Gregorian)
MONTHS_AR = [
    "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
    "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
]

# Hijri month names
HIJRI_MONTHS_AR = [
    "محرم", "صفر", "ربيع الأول", "ربيع الثاني",
    "جمادى الأولى", "جمادى الآخرة", "رجب", "شعبان",
    "رمضان", "شوال", "ذو القعدة", "ذو الحجة"
]


class SystemTime:
    """Core system time - reads time from machine with Gregorian + Hijri support."""

    @property
    def now(self) -> datetime:
        """Current datetime."""
        return datetime.now()

    @property
    def today(self) -> date:
        """Today's date."""
        return date.today()

    @property
    def current_time(self) -> time:
        """Current time."""
        return datetime.now().time()

    @property
    def day_of_week(self) -> str:
        """Day of week in Arabic."""
        return DAYS_AR[self.today.weekday()]

    @property
    def day_of_week_en(self) -> str:
        """Day of week in English."""
        return DAYS_EN[self.today.weekday()]

    @property
    def week_number(self) -> int:
        """Week number in year."""
        return self.today.isocalendar()[1]

    @property
    def quarter(self) -> str:
        """Current quarter (Q1-Q4)."""
        month = self.today.month
        if month <= 3:
            return "Q1"
        elif month <= 6:
            return "Q2"
        elif month <= 9:
            return "Q3"
        else:
            return "Q4"

    @property
    def quarter_number(self) -> int:
        """Current quarter as number (1-4)."""
        return (self.today.month - 1) // 3 + 1

    @property
    def fiscal_year(self) -> int:
        """Fiscal year (starts January)."""
        return self.today.year

    @property
    def month_name_ar(self) -> str:
        """Current month name in Arabic."""
        return MONTHS_AR[self.today.month - 1]

    def get_quarter_for_date(self, d: date) -> str:
        """Get quarter string for a given date."""
        q = (d.month - 1) // 3 + 1
        return f"Q{q}"

    def get_quarter_range(self, year: int, quarter: int) -> tuple:
        """Get start and end dates for a quarter."""
        start_month = (quarter - 1) * 3 + 1
        end_month = start_month + 2

        start = date(year, start_month, 1)
        if end_month == 12:
            end = date(year, 12, 31)
        else:
            end = date(year, end_month + 1, 1) - timedelta(days=1)

        return start, end

    def get_month_range(self, year: int, month: int) -> tuple:
        """Get start and end dates for a month."""
        start = date(year, month, 1)
        if month == 12:
            end = date(year, 12, 31)
        else:
            end = date(year, month + 1, 1) - timedelta(days=1)
        return start, end

    def to_hijri(self, gregorian_date: Optional[date] = None) -> dict:
        """Convert Gregorian date to Hijri."""
        if gregorian_date is None:
            gregorian_date = self.today

        try:
            from hijri_converter import Gregorian
            hijri = Gregorian(
                gregorian_date.year,
                gregorian_date.month,
                gregorian_date.day
            ).to_hijri()
            return {
                "year": hijri.year,
                "month": hijri.month,
                "day": hijri.day,
                "month_name": HIJRI_MONTHS_AR[hijri.month - 1],
                "formatted": f"{hijri.day} {HIJRI_MONTHS_AR[hijri.month - 1]} {hijri.year}"
            }
        except ImportError:
            return self._approximate_hijri(gregorian_date)

    def from_hijri(self, hijri_year: int, hijri_month: int, hijri_day: int) -> date:
        """Convert Hijri date to Gregorian."""
        try:
            from hijri_converter import Hijri
            greg = Hijri(hijri_year, hijri_month, hijri_day).to_gregorian()
            return date(greg.year, greg.month, greg.day)
        except ImportError:
            return self._approximate_from_hijri(hijri_year, hijri_month, hijri_day)

    def _approximate_hijri(self, gregorian_date: date) -> dict:
        """Approximate Hijri date when hijri_converter is not available."""
        # Approximate: Hijri year ~ (Gregorian - 622) * (33/32)
        jd = self._gregorian_to_jd(gregorian_date)
        hijri_year, hijri_month, hijri_day = self._jd_to_hijri(jd)
        month_name = HIJRI_MONTHS_AR[hijri_month - 1] if 1 <= hijri_month <= 12 else ""
        return {
            "year": hijri_year,
            "month": hijri_month,
            "day": hijri_day,
            "month_name": month_name,
            "formatted": f"{hijri_day} {month_name} {hijri_year}"
        }

    def _approximate_from_hijri(self, h_year: int, h_month: int, h_day: int) -> date:
        """Approximate Gregorian date from Hijri when library is not available."""
        jd = self._hijri_to_jd(h_year, h_month, h_day)
        return self._jd_to_gregorian(jd)

    @staticmethod
    def _gregorian_to_jd(d: date) -> int:
        """Convert Gregorian date to Julian Day Number."""
        y, m, day = d.year, d.month, d.day
        if m <= 2:
            y -= 1
            m += 12
        A = y // 100
        B = 2 - A + A // 4
        return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + day + B - 1524

    @staticmethod
    def _jd_to_hijri(jd: int) -> tuple:
        """Convert Julian Day to approximate Hijri date."""
        jd = int(jd) + 0.5
        y = 10631.0 / 30.0
        epoch = 1948439.5
        shift = 8.01 / 60.0

        z = jd - epoch
        cyc = int(z / 10631.0)
        z = z - 10631 * cyc
        j = int((z - shift) / 29.5305882353)
        if j == 12:
            j = 11
        z = z - int(29.5305882353 * j + shift)
        day = int(z)
        month = j + 1
        year = 30 * cyc + int((11 * j + 3) / 325.0) + 1

        if day <= 0:
            day = 30
            month -= 1
        if month <= 0:
            month = 12
            year -= 1

        return int(year), int(month), int(day)

    @staticmethod
    def _hijri_to_jd(year: int, month: int, day: int) -> int:
        """Convert Hijri date to Julian Day Number."""
        return int(
            day + 29.5001 * (month - 1) + 0.99
            + (year - 1) * 354.36667
            + 1948439.5
        )

    @staticmethod
    def _jd_to_gregorian(jd: int) -> date:
        """Convert Julian Day Number to Gregorian date."""
        jd = jd + 0.5
        z = int(jd)
        a = int((z - 1867216.25) / 36524.25)
        a = z + 1 + a - int(a / 4)
        b = a + 1524
        c = int((b - 122.1) / 365.25)
        d = int(365.25 * c)
        e = int((b - d) / 30.6001)

        day = b - d - int(30.6001 * e)
        month = e - 1 if e < 14 else e - 13
        year = c - 4716 if month > 2 else c - 4715

        return date(int(year), int(month), int(day))

    def get_full_context(self) -> dict:
        """Get comprehensive time context for AI Copilot."""
        hijri = self.to_hijri()
        return {
            "gregorian": {
                "date": self.today.isoformat(),
                "time": self.current_time.strftime("%H:%M:%S"),
                "day_ar": self.day_of_week,
                "day_en": self.day_of_week_en,
                "month_ar": self.month_name_ar,
                "week": self.week_number,
                "quarter": self.quarter,
                "year": self.today.year,
            },
            "hijri": hijri,
            "fiscal": {
                "year": self.fiscal_year,
                "quarter": self.quarter,
                "quarter_number": self.quarter_number,
            }
        }


# Singleton
_system_time: Optional[SystemTime] = None


def get_system_time() -> SystemTime:
    """Get singleton SystemTime instance."""
    global _system_time
    if _system_time is None:
        _system_time = SystemTime()
    return _system_time
