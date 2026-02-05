"""
Working Calendar
================
Work days, hours, and holiday-aware calendar for business operations.
"""

from datetime import date, datetime, time, timedelta
from typing import Optional

from .holidays import HolidayLoader


# Default working days: Sunday-Thursday (0=Mon, 6=Sun => 6,0,1,2,3)
# Saudi/Gulf standard
DEFAULT_WORKING_DAYS_GULF = [6, 0, 1, 2, 3]  # Sun-Thu
DEFAULT_WEEKEND_GULF = [4, 5]  # Fri-Sat

# Egypt standard
DEFAULT_WORKING_DAYS_EGYPT = [6, 0, 1, 2, 3]  # Sun-Thu
DEFAULT_WEEKEND_EGYPT = [4, 5]  # Fri-Sat

# Western standard
DEFAULT_WORKING_DAYS_WESTERN = [0, 1, 2, 3, 4]  # Mon-Fri
DEFAULT_WEEKEND_WESTERN = [5, 6]  # Sat-Sun

COUNTRY_DEFAULTS = {
    "SA": {"working_days": DEFAULT_WORKING_DAYS_GULF, "weekend": DEFAULT_WEEKEND_GULF},
    "EG": {"working_days": DEFAULT_WORKING_DAYS_EGYPT, "weekend": DEFAULT_WEEKEND_EGYPT},
    "AE": {"working_days": DEFAULT_WORKING_DAYS_GULF, "weekend": DEFAULT_WEEKEND_GULF},
}


class WorkingCalendar:
    """Working calendar - working days, hours, and holidays."""

    def __init__(
        self,
        country_code: str = "SA",
        working_days: Optional[list] = None,
        weekend_days: Optional[list] = None,
        working_hours_start: str = "08:00",
        working_hours_end: str = "16:00",
    ):
        self.country_code = country_code.upper()
        self.holiday_loader = HolidayLoader(self.country_code)

        defaults = COUNTRY_DEFAULTS.get(self.country_code, COUNTRY_DEFAULTS["SA"])
        self.working_days = working_days or defaults["working_days"]
        self.weekend_days = weekend_days or defaults["weekend"]
        self.working_hours = {
            "start": working_hours_start,
            "end": working_hours_end,
        }

    def is_working_day(self, check_date: Optional[date] = None) -> bool:
        """Check if a date is a working day."""
        if check_date is None:
            check_date = date.today()

        # Check weekend
        if check_date.weekday() in self.weekend_days:
            return False

        # Check official holidays
        if self.holiday_loader.is_holiday(check_date):
            return False

        return True

    def is_working_hours(self, check_time: Optional[time] = None) -> bool:
        """Check if current time is within working hours."""
        if check_time is None:
            check_time = datetime.now().time()

        start = datetime.strptime(self.working_hours["start"], "%H:%M").time()
        end = datetime.strptime(self.working_hours["end"], "%H:%M").time()

        return start <= check_time <= end

    def is_work_time_now(self) -> bool:
        """Check if right now is during work hours on a work day."""
        return self.is_working_day() and self.is_working_hours()

    def working_days_between(self, start: date, end: date) -> int:
        """Count working days between two dates (inclusive)."""
        count = 0
        current = start
        while current <= end:
            if self.is_working_day(current):
                count += 1
            current += timedelta(days=1)
        return count

    def next_working_day(self, from_date: Optional[date] = None) -> date:
        """Get the next working day after the given date."""
        if from_date is None:
            from_date = date.today()

        next_day = from_date + timedelta(days=1)
        while not self.is_working_day(next_day):
            next_day += timedelta(days=1)
        return next_day

    def previous_working_day(self, from_date: Optional[date] = None) -> date:
        """Get the previous working day before the given date."""
        if from_date is None:
            from_date = date.today()

        prev_day = from_date - timedelta(days=1)
        while not self.is_working_day(prev_day):
            prev_day -= timedelta(days=1)
        return prev_day

    def add_working_days(self, from_date: date, days: int) -> date:
        """Add N working days to a date (skipping weekends and holidays)."""
        current = from_date
        added = 0
        while added < days:
            current += timedelta(days=1)
            if self.is_working_day(current):
                added += 1
        return current

    def subtract_working_days(self, from_date: date, days: int) -> date:
        """Subtract N working days from a date."""
        current = from_date
        subtracted = 0
        while subtracted < days:
            current -= timedelta(days=1)
            if self.is_working_day(current):
                subtracted += 1
        return current

    def first_working_day_of_month(self, year: int, month: int) -> date:
        """Get the first working day of a month."""
        d = date(year, month, 1)
        while not self.is_working_day(d):
            d += timedelta(days=1)
        return d

    def last_working_day_of_month(self, year: int, month: int) -> date:
        """Get the last working day of a month."""
        if month == 12:
            d = date(year, 12, 31)
        else:
            d = date(year, month + 1, 1) - timedelta(days=1)
        while not self.is_working_day(d):
            d -= timedelta(days=1)
        return d

    def get_working_days_in_month(self, year: int, month: int) -> int:
        """Count working days in a month."""
        first = date(year, month, 1)
        if month == 12:
            last = date(year, 12, 31)
        else:
            last = date(year, month + 1, 1) - timedelta(days=1)
        return self.working_days_between(first, last)

    def get_day_status(self, check_date: Optional[date] = None) -> dict:
        """Get comprehensive status for a date."""
        if check_date is None:
            check_date = date.today()

        is_weekend = check_date.weekday() in self.weekend_days
        holiday_name = self.holiday_loader.get_holiday_name(check_date)
        is_holiday = holiday_name is not None
        is_working = self.is_working_day(check_date)

        if is_holiday:
            status = "holiday"
            reason = holiday_name
        elif is_weekend:
            status = "weekend"
            reason = "إجازة أسبوعية"
        else:
            status = "working"
            reason = "يوم عمل"

        return {
            "date": check_date.isoformat(),
            "status": status,
            "is_working": is_working,
            "is_weekend": is_weekend,
            "is_holiday": is_holiday,
            "holiday_name": holiday_name,
            "reason": reason,
        }

    def get_context(self) -> dict:
        """Get working calendar context for AI Copilot."""
        today = date.today()
        now = datetime.now().time()

        return {
            "country": self.country_code,
            "is_working_day": self.is_working_day(today),
            "is_working_hours": self.is_working_hours(now),
            "is_work_time": self.is_work_time_now(),
            "working_hours": self.working_hours,
            "today_status": self.get_day_status(today),
            "next_working_day": self.next_working_day(today).isoformat(),
            "upcoming_holidays": self.holiday_loader.get_upcoming_holidays(today, 3),
        }


# Singleton
_working_calendar: Optional[WorkingCalendar] = None


def get_working_calendar(country_code: str = "SA") -> WorkingCalendar:
    """Get singleton WorkingCalendar instance."""
    global _working_calendar
    if _working_calendar is None or _working_calendar.country_code != country_code:
        _working_calendar = WorkingCalendar(country_code=country_code)
    return _working_calendar
