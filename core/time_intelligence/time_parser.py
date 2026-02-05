"""
Natural Language Time Parser
============================
Parses Arabic natural language time expressions into dates.
"""

import re
from datetime import date, timedelta
from typing import Optional, Union

from .arabic_time_patterns import (
    SIMPLE_DATE_PATTERNS,
    PERIOD_PATTERNS,
    SPECIAL_PERIODS,
    ISLAMIC_EVENTS,
    DAY_NAMES,
    ARABIC_NUMBERS,
    RELATIVE_PATTERN,
    TIME_UNITS,
)


class NaturalTimeParser:
    """Parser for Arabic natural language time expressions."""

    def parse(self, text: str, reference_date: Optional[date] = None) -> Optional[date]:
        """Parse Arabic text into a date."""
        if reference_date is None:
            reference_date = date.today()

        text = text.strip()

        # 1. Simple date mappings
        result = self._parse_simple(text, reference_date)
        if result:
            return result

        # 2. Special period references
        result = self._parse_special_period(text, reference_date)
        if result:
            return result

        # 3. Period patterns (next/last week/month)
        result = self._parse_period(text, reference_date)
        if result:
            return result

        # 4. Relative expressions (بعد 3 أيام, قبل أسبوع)
        result = self._parse_relative(text, reference_date)
        if result:
            return result

        # 5. Day name references (الخميس الجاي, آخر خميس)
        result = self._parse_day_name(text, reference_date)
        if result:
            return result

        # 6. Islamic event references (بعد العيد, قبل رمضان)
        result = self._parse_event_relative(text, reference_date)
        if result:
            return result

        return None

    def parse_to_range(self, text: str, reference_date: Optional[date] = None) -> Optional[tuple]:
        """Parse text into a date range (start, end)."""
        if reference_date is None:
            reference_date = date.today()

        text = text.strip()

        # Period patterns that return ranges
        for pattern, period_type in PERIOD_PATTERNS.items():
            if pattern in text:
                return self._get_period_range(period_type, reference_date)

        # "هذا الشهر" / "الشهر ده"
        if "هذا الشهر" in text or "الشهر ده" in text or "الشهر الحالي" in text:
            first = date(reference_date.year, reference_date.month, 1)
            if reference_date.month == 12:
                last = date(reference_date.year, 12, 31)
            else:
                last = date(reference_date.year, reference_date.month + 1, 1) - timedelta(days=1)
            return first, last

        # "هذا الأسبوع"
        if "هذا الأسبوع" in text or "الأسبوع ده" in text or "الأسبوع الحالي" in text:
            # Week starts Sunday (weekday 6)
            start = reference_date - timedelta(days=(reference_date.weekday() + 1) % 7)
            end = start + timedelta(days=6)
            return start, end

        # Single date fallback
        single = self.parse(text, reference_date)
        if single:
            return single, single

        return None

    def _parse_simple(self, text: str, ref: date) -> Optional[date]:
        """Parse simple date expressions."""
        lower_text = text.strip()
        for pattern, meaning in SIMPLE_DATE_PATTERNS.items():
            if pattern == lower_text or pattern in lower_text:
                if meaning == "today":
                    return ref
                elif meaning == "yesterday":
                    return ref - timedelta(days=1)
                elif meaning == "tomorrow":
                    return ref + timedelta(days=1)
        return None

    def _parse_special_period(self, text: str, ref: date) -> Optional[date]:
        """Parse special period references."""
        for pattern, period_type in SPECIAL_PERIODS.items():
            if pattern in text:
                if period_type == "month_start":
                    return date(ref.year, ref.month, 1)
                elif period_type == "month_end":
                    if ref.month == 12:
                        return date(ref.year, 12, 31)
                    return date(ref.year, ref.month + 1, 1) - timedelta(days=1)
                elif period_type == "year_start":
                    return date(ref.year, 1, 1)
                elif period_type == "year_end":
                    return date(ref.year, 12, 31)
                elif period_type == "week_start":
                    # Week starts Sunday
                    return ref - timedelta(days=(ref.weekday() + 1) % 7)
                elif period_type == "week_end":
                    start = ref - timedelta(days=(ref.weekday() + 1) % 7)
                    return start + timedelta(days=6)
        return None

    def _parse_period(self, text: str, ref: date) -> Optional[date]:
        """Parse period references (next/last week/month)."""
        for pattern, period_type in PERIOD_PATTERNS.items():
            if pattern in text:
                if period_type == "next_week":
                    return ref + timedelta(days=7 - ref.weekday() + 6)  # Next Sunday
                elif period_type == "last_week":
                    return ref - timedelta(days=ref.weekday() + 8)  # Last Sunday
                elif period_type == "next_month":
                    month = ref.month + 1
                    year = ref.year
                    if month > 12:
                        month = 1
                        year += 1
                    return date(year, month, 1)
                elif period_type == "last_month":
                    month = ref.month - 1
                    year = ref.year
                    if month < 1:
                        month = 12
                        year -= 1
                    return date(year, month, 1)
                elif period_type == "next_year":
                    return date(ref.year + 1, 1, 1)
                elif period_type == "last_year":
                    return date(ref.year - 1, 1, 1)
        return None

    def _parse_relative(self, text: str, ref: date) -> Optional[date]:
        """Parse relative expressions (بعد 3 أيام, قبل أسبوع)."""
        match = RELATIVE_PATTERN.search(text)
        if match:
            direction = match.group(1)
            number_str = match.group(2)
            unit = match.group(3)

            # Parse number
            try:
                number = int(number_str)
            except ValueError:
                number = ARABIC_NUMBERS.get(number_str, 1)

            # Parse unit to days
            unit_days = self._unit_to_days(unit)
            total_days = number * unit_days

            if direction in ("بعد", "خلال"):
                return ref + timedelta(days=total_days)
            elif direction == "قبل":
                return ref - timedelta(days=total_days)

        # Handle simple "بعد أسبوع" (without number)
        for keyword in ["بعد", "خلال"]:
            if keyword in text:
                for unit_name, unit_days in TIME_UNITS.items():
                    if unit_name in text:
                        return ref + timedelta(days=unit_days)

        for keyword in ["قبل"]:
            if keyword in text:
                for unit_name, unit_days in TIME_UNITS.items():
                    if unit_name in text:
                        return ref - timedelta(days=unit_days)

        return None

    def _parse_day_name(self, text: str, ref: date) -> Optional[date]:
        """Parse day name references (الخميس الجاي, آخر خميس)."""
        target_weekday = None

        for day_name, weekday in DAY_NAMES.items():
            if day_name in text:
                target_weekday = weekday
                break

        if target_weekday is None:
            return None

        # "الجاي" / "القادم" = next occurrence
        if "الجاي" in text or "القادم" in text or "الجاية" in text:
            days_ahead = (target_weekday - ref.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            return ref + timedelta(days=days_ahead)

        # "اللي فات" / "الماضي" = last occurrence
        if "اللي فات" in text or "الماضي" in text or "الماضية" in text:
            days_back = (ref.weekday() - target_weekday) % 7
            if days_back == 0:
                days_back = 7
            return ref - timedelta(days=days_back)

        # "آخر" / "أول" in month
        if "آخر" in text or "اخر" in text:
            return self._last_weekday_in_month(target_weekday, ref.year, ref.month)
        if "أول" in text or "اول" in text:
            return self._first_weekday_in_month(target_weekday, ref.year, ref.month)

        # Default: next occurrence
        days_ahead = (target_weekday - ref.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        return ref + timedelta(days=days_ahead)

    def _parse_event_relative(self, text: str, ref: date) -> Optional[date]:
        """Parse event-relative expressions (بعد العيد, قبل رمضان)."""
        from .hijri_utils import days_until_ramadan, days_until_eid_fitr, days_until_eid_adha
        from .system_time import get_system_time

        st = get_system_time()

        for event_name, event_type in ISLAMIC_EVENTS.items():
            if event_name not in text:
                continue

            # Get the event date
            if event_type == "ramadan":
                hijri = st.to_hijri(ref)
                if hijri["month"] < 9:
                    event_date = st.from_hijri(hijri["year"], 9, 1)
                else:
                    event_date = st.from_hijri(hijri["year"] + 1, 9, 1)
            elif event_type in ("eid", "eid_fitr"):
                hijri = st.to_hijri(ref)
                if hijri["month"] < 10:
                    event_date = st.from_hijri(hijri["year"], 10, 1)
                else:
                    event_date = st.from_hijri(hijri["year"] + 1, 10, 1)
            elif event_type == "eid_adha":
                hijri = st.to_hijri(ref)
                if hijri["month"] < 12 or (hijri["month"] == 12 and hijri["day"] < 10):
                    event_date = st.from_hijri(hijri["year"], 12, 10)
                else:
                    event_date = st.from_hijri(hijri["year"] + 1, 12, 10)
            elif event_type == "national_day":
                event_date = date(ref.year, 9, 23)
                if event_date < ref:
                    event_date = date(ref.year + 1, 9, 23)
            elif event_type == "founding_day":
                event_date = date(ref.year, 2, 22)
                if event_date < ref:
                    event_date = date(ref.year + 1, 2, 22)
            else:
                continue

            # "بعد العيد" = day after event
            if "بعد" in text:
                return event_date + timedelta(days=1)
            # "قبل رمضان" = day before event
            elif "قبل" in text:
                return event_date - timedelta(days=1)
            else:
                return event_date

        return None

    @staticmethod
    def _unit_to_days(unit: str) -> int:
        """Convert Arabic time unit to days."""
        unit_map = {
            "يوم": 1, "أيام": 1, "ايام": 1,
            "أسبوع": 7, "اسبوع": 7, "أسابيع": 7, "اسابيع": 7,
            "شهر": 30, "شهور": 30, "أشهر": 30,
            "سنة": 365, "سنين": 365, "سنوات": 365,
        }
        return unit_map.get(unit, 1)

    @staticmethod
    def _first_weekday_in_month(weekday: int, year: int, month: int) -> date:
        """Get the first occurrence of a weekday in a month."""
        d = date(year, month, 1)
        while d.weekday() != weekday:
            d += timedelta(days=1)
        return d

    @staticmethod
    def _last_weekday_in_month(weekday: int, year: int, month: int) -> date:
        """Get the last occurrence of a weekday in a month."""
        if month == 12:
            d = date(year, 12, 31)
        else:
            d = date(year, month + 1, 1) - timedelta(days=1)
        while d.weekday() != weekday:
            d -= timedelta(days=1)
        return d


# Singleton
_parser: Optional[NaturalTimeParser] = None


def get_time_parser() -> NaturalTimeParser:
    """Get singleton NaturalTimeParser instance."""
    global _parser
    if _parser is None:
        _parser = NaturalTimeParser()
    return _parser
