"""
Holiday Loader
==============
Loads holidays for different countries.
"""

from datetime import date, timedelta
from typing import Optional

from . import saudi_arabia, egypt, uae


# Country code to module mapping
COUNTRY_MODULES = {
    "SA": saudi_arabia,
    "EG": egypt,
    "AE": uae,
}

COUNTRY_NAMES = {
    "SA": {"ar": "المملكة العربية السعودية", "en": "Saudi Arabia"},
    "EG": {"ar": "جمهورية مصر العربية", "en": "Egypt"},
    "AE": {"ar": "الإمارات العربية المتحدة", "en": "United Arab Emirates"},
}


class HolidayLoader:
    """Loads and manages country-specific holidays."""

    def __init__(self, country_code: str = "SA"):
        self.country_code = country_code.upper()
        self._cache = {}

    @property
    def supported_countries(self) -> list:
        """List of supported country codes."""
        return list(COUNTRY_MODULES.keys())

    def get_holidays(self, year: Optional[int] = None) -> list:
        """Get holidays for the configured country and year."""
        if year is None:
            year = date.today().year

        cache_key = f"{self.country_code}_{year}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        module = COUNTRY_MODULES.get(self.country_code)
        if module is None:
            return []

        holidays = module.get_holidays(year)
        self._cache[cache_key] = holidays
        return holidays

    def is_holiday(self, check_date: Optional[date] = None) -> bool:
        """Check if a date is an official holiday."""
        if check_date is None:
            check_date = date.today()

        holidays = self.get_holidays(check_date.year)
        for holiday in holidays:
            h_date = date.fromisoformat(holiday["date"])
            days_count = holiday.get("days_count", 1)

            for i in range(days_count):
                if check_date == h_date + timedelta(days=i):
                    return True

        return False

    def get_holiday_name(self, check_date: Optional[date] = None) -> Optional[str]:
        """Get the Arabic name of a holiday on a given date."""
        if check_date is None:
            check_date = date.today()

        holidays = self.get_holidays(check_date.year)
        for holiday in holidays:
            h_date = date.fromisoformat(holiday["date"])
            days_count = holiday.get("days_count", 1)

            for i in range(days_count):
                if check_date == h_date + timedelta(days=i):
                    return holiday["name_ar"]

        return None

    def get_upcoming_holidays(self, from_date: Optional[date] = None, count: int = 5) -> list:
        """Get the next N upcoming holidays."""
        if from_date is None:
            from_date = date.today()

        upcoming = []
        for year in [from_date.year, from_date.year + 1]:
            holidays = self.get_holidays(year)
            for holiday in holidays:
                h_date = date.fromisoformat(holiday["date"])
                if h_date >= from_date:
                    days_away = (h_date - from_date).days
                    upcoming.append({
                        **holiday,
                        "days_away": days_away,
                    })

        upcoming.sort(key=lambda x: x["days_away"])
        return upcoming[:count]

    def get_country_name(self, lang: str = "ar") -> str:
        """Get country name in specified language."""
        names = COUNTRY_NAMES.get(self.country_code, {})
        return names.get(lang, self.country_code)


def get_holidays_for_country(country_code: str, year: Optional[int] = None) -> list:
    """Convenience function to get holidays for a country."""
    loader = HolidayLoader(country_code)
    return loader.get_holidays(year)
