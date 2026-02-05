"""
Saudi Arabia Holidays
=====================
Official holidays for the Kingdom of Saudi Arabia.
"""


def get_holidays(year: int) -> list:
    """Get Saudi Arabia official holidays for a given year."""
    holidays = [
        {
            "date": f"{year}-02-22",
            "name_ar": "يوم التأسيس",
            "name_en": "Founding Day",
            "type": "national",
            "days_count": 1,
        },
        {
            "date": f"{year}-09-23",
            "name_ar": "اليوم الوطني",
            "name_en": "National Day",
            "type": "national",
            "days_count": 1,
        },
    ]

    # Religious holidays (approximate Gregorian dates vary by year)
    # These are approximate and should be updated with actual dates
    religious_holidays_by_year = {
        2025: [
            {"date": "2025-03-30", "name_ar": "عيد الفطر", "name_en": "Eid Al-Fitr", "type": "religious", "days_count": 4},
            {"date": "2025-06-06", "name_ar": "عيد الأضحى", "name_en": "Eid Al-Adha", "type": "religious", "days_count": 4},
        ],
        2026: [
            {"date": "2026-03-20", "name_ar": "عيد الفطر", "name_en": "Eid Al-Fitr", "type": "religious", "days_count": 4},
            {"date": "2026-05-27", "name_ar": "عيد الأضحى", "name_en": "Eid Al-Adha", "type": "religious", "days_count": 4},
        ],
        2027: [
            {"date": "2027-03-10", "name_ar": "عيد الفطر", "name_en": "Eid Al-Fitr", "type": "religious", "days_count": 4},
            {"date": "2027-05-16", "name_ar": "عيد الأضحى", "name_en": "Eid Al-Adha", "type": "religious", "days_count": 4},
        ],
    }

    if year in religious_holidays_by_year:
        holidays.extend(religious_holidays_by_year[year])

    return holidays
