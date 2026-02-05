"""
Hijri Utilities
===============
Hijri calendar utilities and helpers.
"""

from datetime import date, timedelta
from typing import Optional

from .system_time import get_system_time, HIJRI_MONTHS_AR


def hijri_today() -> dict:
    """Get today's Hijri date."""
    return get_system_time().to_hijri()


def hijri_for_date(d: date) -> dict:
    """Get Hijri date for a Gregorian date."""
    return get_system_time().to_hijri(d)


def gregorian_from_hijri(year: int, month: int, day: int) -> date:
    """Convert Hijri to Gregorian."""
    return get_system_time().from_hijri(year, month, day)


def days_until_ramadan(from_date: Optional[date] = None) -> int:
    """Calculate days until next Ramadan."""
    if from_date is None:
        from_date = date.today()

    st = get_system_time()
    hijri = st.to_hijri(from_date)

    if hijri["month"] < 9:
        # Ramadan is in the current Hijri year
        ramadan_start = st.from_hijri(hijri["year"], 9, 1)
    else:
        # Ramadan next year
        ramadan_start = st.from_hijri(hijri["year"] + 1, 9, 1)

    delta = (ramadan_start - from_date).days
    return max(0, delta)


def days_until_eid_fitr(from_date: Optional[date] = None) -> int:
    """Calculate days until next Eid Al-Fitr (1 Shawwal)."""
    if from_date is None:
        from_date = date.today()

    st = get_system_time()
    hijri = st.to_hijri(from_date)

    if hijri["month"] < 10:
        eid_date = st.from_hijri(hijri["year"], 10, 1)
    else:
        eid_date = st.from_hijri(hijri["year"] + 1, 10, 1)

    delta = (eid_date - from_date).days
    return max(0, delta)


def days_until_eid_adha(from_date: Optional[date] = None) -> int:
    """Calculate days until next Eid Al-Adha (10 Dhul Hijjah)."""
    if from_date is None:
        from_date = date.today()

    st = get_system_time()
    hijri = st.to_hijri(from_date)

    if hijri["month"] < 12 or (hijri["month"] == 12 and hijri["day"] < 10):
        eid_date = st.from_hijri(hijri["year"], 12, 10)
    else:
        eid_date = st.from_hijri(hijri["year"] + 1, 12, 10)

    delta = (eid_date - from_date).days
    return max(0, delta)


def get_hijri_month_name(month: int) -> str:
    """Get Arabic name for a Hijri month (1-12)."""
    if 1 <= month <= 12:
        return HIJRI_MONTHS_AR[month - 1]
    return ""


def get_upcoming_islamic_events(from_date: Optional[date] = None, count: int = 5) -> list:
    """Get upcoming Islamic events/occasions."""
    if from_date is None:
        from_date = date.today()

    events = []
    st = get_system_time()
    hijri = st.to_hijri(from_date)
    current_year = hijri["year"]

    # Key Islamic dates (Hijri month, day, name)
    islamic_dates = [
        (1, 1, "رأس السنة الهجرية"),
        (1, 10, "عاشوراء"),
        (3, 12, "المولد النبوي"),
        (7, 27, "الإسراء والمعراج"),
        (8, 15, "ليلة النصف من شعبان"),
        (9, 1, "بداية رمضان"),
        (9, 27, "ليلة القدر (تقريباً)"),
        (10, 1, "عيد الفطر"),
        (12, 8, "يوم التروية"),
        (12, 9, "يوم عرفة"),
        (12, 10, "عيد الأضحى"),
    ]

    for year_offset in range(2):
        check_year = current_year + year_offset
        for h_month, h_day, name in islamic_dates:
            try:
                greg_date = st.from_hijri(check_year, h_month, h_day)
                if greg_date >= from_date:
                    days_away = (greg_date - from_date).days
                    events.append({
                        "name": name,
                        "hijri_date": f"{h_day} {HIJRI_MONTHS_AR[h_month - 1]} {check_year}",
                        "gregorian_date": greg_date.isoformat(),
                        "days_away": days_away,
                    })
            except (ValueError, OverflowError):
                continue

    events.sort(key=lambda x: x["days_away"])
    return events[:count]
