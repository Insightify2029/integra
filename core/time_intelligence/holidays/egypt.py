"""
Egypt Holidays
==============
Official holidays for the Arab Republic of Egypt.
"""


def get_holidays(year: int) -> list:
    """Get Egypt official holidays for a given year."""
    holidays = [
        {
            "date": f"{year}-01-07",
            "name_ar": "عيد الميلاد المجيد (القبطي)",
            "name_en": "Coptic Christmas",
            "type": "national",
            "days_count": 1,
        },
        {
            "date": f"{year}-01-25",
            "name_ar": "عيد ثورة 25 يناير",
            "name_en": "Revolution Day (Jan 25)",
            "type": "national",
            "days_count": 1,
        },
        {
            "date": f"{year}-04-25",
            "name_ar": "عيد تحرير سيناء",
            "name_en": "Sinai Liberation Day",
            "type": "national",
            "days_count": 1,
        },
        {
            "date": f"{year}-05-01",
            "name_ar": "عيد العمال",
            "name_en": "Labor Day",
            "type": "national",
            "days_count": 1,
        },
        {
            "date": f"{year}-06-30",
            "name_ar": "عيد ثورة 30 يونيو",
            "name_en": "Revolution Day (Jun 30)",
            "type": "national",
            "days_count": 1,
        },
        {
            "date": f"{year}-07-23",
            "name_ar": "عيد ثورة 23 يوليو",
            "name_en": "Revolution Day (Jul 23)",
            "type": "national",
            "days_count": 1,
        },
        {
            "date": f"{year}-10-06",
            "name_ar": "عيد القوات المسلحة",
            "name_en": "Armed Forces Day",
            "type": "national",
            "days_count": 1,
        },
    ]

    # Religious holidays (approximate)
    religious_holidays_by_year = {
        2025: [
            {"date": "2025-03-30", "name_ar": "عيد الفطر", "name_en": "Eid Al-Fitr", "type": "religious", "days_count": 3},
            {"date": "2025-06-06", "name_ar": "عيد الأضحى", "name_en": "Eid Al-Adha", "type": "religious", "days_count": 3},
        ],
        2026: [
            {"date": "2026-03-20", "name_ar": "عيد الفطر", "name_en": "Eid Al-Fitr", "type": "religious", "days_count": 3},
            {"date": "2026-05-27", "name_ar": "عيد الأضحى", "name_en": "Eid Al-Adha", "type": "religious", "days_count": 3},
        ],
        2027: [
            {"date": "2027-03-10", "name_ar": "عيد الفطر", "name_en": "Eid Al-Fitr", "type": "religious", "days_count": 3},
            {"date": "2027-05-16", "name_ar": "عيد الأضحى", "name_en": "Eid Al-Adha", "type": "religious", "days_count": 3},
        ],
    }

    if year in religious_holidays_by_year:
        holidays.extend(religious_holidays_by_year[year])

    return holidays
