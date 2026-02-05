"""
UAE Holidays
============
Official holidays for the United Arab Emirates.
"""


def get_holidays(year: int) -> list:
    """Get UAE official holidays for a given year."""
    holidays = [
        {
            "date": f"{year}-01-01",
            "name_ar": "رأس السنة الميلادية",
            "name_en": "New Year's Day",
            "type": "national",
            "days_count": 1,
        },
        {
            "date": f"{year}-12-01",
            "name_ar": "يوم الشهيد",
            "name_en": "Commemoration Day",
            "type": "national",
            "days_count": 1,
        },
        {
            "date": f"{year}-12-02",
            "name_ar": "اليوم الوطني",
            "name_en": "National Day",
            "type": "national",
            "days_count": 2,
        },
    ]

    # Religious holidays (approximate)
    religious_holidays_by_year = {
        2025: [
            {"date": "2025-03-30", "name_ar": "عيد الفطر", "name_en": "Eid Al-Fitr", "type": "religious", "days_count": 3},
            {"date": "2025-06-05", "name_ar": "وقفة عرفات", "name_en": "Arafat Day", "type": "religious", "days_count": 1},
            {"date": "2025-06-06", "name_ar": "عيد الأضحى", "name_en": "Eid Al-Adha", "type": "religious", "days_count": 3},
            {"date": "2025-06-26", "name_ar": "رأس السنة الهجرية", "name_en": "Islamic New Year", "type": "religious", "days_count": 1},
            {"date": "2025-09-04", "name_ar": "المولد النبوي", "name_en": "Prophet's Birthday", "type": "religious", "days_count": 1},
        ],
        2026: [
            {"date": "2026-03-20", "name_ar": "عيد الفطر", "name_en": "Eid Al-Fitr", "type": "religious", "days_count": 3},
            {"date": "2026-05-26", "name_ar": "وقفة عرفات", "name_en": "Arafat Day", "type": "religious", "days_count": 1},
            {"date": "2026-05-27", "name_ar": "عيد الأضحى", "name_en": "Eid Al-Adha", "type": "religious", "days_count": 3},
            {"date": "2026-06-16", "name_ar": "رأس السنة الهجرية", "name_en": "Islamic New Year", "type": "religious", "days_count": 1},
            {"date": "2026-08-25", "name_ar": "المولد النبوي", "name_en": "Prophet's Birthday", "type": "religious", "days_count": 1},
        ],
        2027: [
            {"date": "2027-03-10", "name_ar": "عيد الفطر", "name_en": "Eid Al-Fitr", "type": "religious", "days_count": 3},
            {"date": "2027-05-16", "name_ar": "عيد الأضحى", "name_en": "Eid Al-Adha", "type": "religious", "days_count": 3},
        ],
    }

    if year in religious_holidays_by_year:
        holidays.extend(religious_holidays_by_year[year])

    return holidays
