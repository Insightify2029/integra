"""
Arabic Time Patterns
====================
Regular expressions and patterns for Arabic time expressions.
"""

import re

# Simple date expressions
SIMPLE_DATE_PATTERNS = {
    "اليوم": "today",
    "النهارده": "today",
    "النهاردة": "today",
    "أمس": "yesterday",
    "إمبارح": "yesterday",
    "امبارح": "yesterday",
    "بكرة": "tomorrow",
    "بكره": "tomorrow",
    "بكرا": "tomorrow",
    "غدا": "tomorrow",
    "غداً": "tomorrow",
}

# Relative time keywords
AFTER_KEYWORDS = ["بعد", "خلال"]
BEFORE_KEYWORDS = ["قبل"]

# Time unit patterns (Arabic)
TIME_UNITS = {
    "يوم": 1,
    "أيام": 1,
    "ايام": 1,
    "يومين": 2,
    "أسبوع": 7,
    "اسبوع": 7,
    "أسبوعين": 14,
    "اسبوعين": 14,
    "شهر": 30,
    "شهرين": 60,
    "سنة": 365,
    "سنتين": 730,
}

# Period references
PERIOD_PATTERNS = {
    "الأسبوع الجاي": "next_week",
    "الاسبوع الجاي": "next_week",
    "الأسبوع القادم": "next_week",
    "الأسبوع اللي فات": "last_week",
    "الأسبوع الماضي": "last_week",
    "الشهر الجاي": "next_month",
    "الشهر القادم": "next_month",
    "الشهر اللي فات": "last_month",
    "الشهر الماضي": "last_month",
    "السنة الجاية": "next_year",
    "السنة القادمة": "next_year",
    "السنة اللي فاتت": "last_year",
    "السنة الماضية": "last_year",
}

# Special period references
SPECIAL_PERIODS = {
    "أول الشهر": "month_start",
    "اول الشهر": "month_start",
    "نهاية الشهر": "month_end",
    "آخر الشهر": "month_end",
    "اخر الشهر": "month_end",
    "أول السنة": "year_start",
    "اول السنة": "year_start",
    "نهاية السنة": "year_end",
    "آخر السنة": "year_end",
    "اخر السنة": "year_end",
    "أول الأسبوع": "week_start",
    "اول الاسبوع": "week_start",
    "نهاية الأسبوع": "week_end",
    "آخر الأسبوع": "week_end",
}

# Islamic event keywords
ISLAMIC_EVENTS = {
    "رمضان": "ramadan",
    "العيد": "eid",
    "عيد الفطر": "eid_fitr",
    "عيد الأضحى": "eid_adha",
    "عيد الاضحى": "eid_adha",
    "الوطني": "national_day",
    "التأسيس": "founding_day",
}

# Day name keywords (Arabic)
DAY_NAMES = {
    "السبت": 5,
    "الأحد": 6,
    "الاحد": 6,
    "الاثنين": 0,
    "الإثنين": 0,
    "الثلاثاء": 1,
    "الأربعاء": 2,
    "الاربعاء": 2,
    "الخميس": 3,
    "الجمعة": 4,
}

# Arabic numerals
ARABIC_NUMBERS = {
    "واحد": 1, "١": 1,
    "اثنين": 2, "اتنين": 2, "٢": 2,
    "ثلاثة": 3, "تلاتة": 3, "٣": 3,
    "أربعة": 4, "اربعة": 4, "٤": 4,
    "خمسة": 5, "خمس": 5, "٥": 5,
    "ستة": 6, "ست": 6, "٦": 6,
    "سبعة": 7, "سبع": 7, "٧": 7,
    "ثمانية": 8, "تمانية": 8, "٨": 8,
    "تسعة": 9, "تسع": 9, "٩": 9,
    "عشرة": 10, "عشر": 10, "١٠": 10,
}

# Regex for "بعد N أيام/شهور/..."
RELATIVE_PATTERN = re.compile(
    r"(بعد|قبل|خلال)\s+(\d+|" +
    "|".join(ARABIC_NUMBERS.keys()) +
    r")\s+(يوم|أيام|ايام|أسبوع|اسبوع|شهر|شهور|أشهر|سنة|سنين|سنوات)"
)
