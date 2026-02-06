"""
Column Detector
===============
AI-powered column type detection for Excel/CSV data.
Detects: text, number, currency, date, phone, email, IBAN, percentage, boolean.
"""

import re
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Any, Optional, Tuple

from core.logging import app_logger


class ColumnType(Enum):
    """Detected column types."""
    TEXT = "text"
    NUMBER = "number"
    CURRENCY = "currency"
    DATE = "date"
    PHONE = "phone"
    EMAIL = "email"
    IBAN = "iban"
    PERCENTAGE = "percentage"
    BOOLEAN = "boolean"
    UNKNOWN = "unknown"


@dataclass
class ColumnAnalysis:
    """Analysis result for a single column."""
    name: str
    detected_type: ColumnType
    confidence: float  # 0.0 to 1.0
    sample_values: List[Any] = field(default_factory=list)
    null_count: int = 0
    unique_count: int = 0
    suggested_db_column: Optional[str] = None


# Regex patterns for type detection
_PATTERNS = {
    ColumnType.PHONE: re.compile(
        r'^[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[0-9]{3,4}[-\s\.]?[0-9]{4,6}$'
    ),
    ColumnType.EMAIL: re.compile(
        r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    ),
    ColumnType.IBAN: re.compile(
        r'^[A-Z]{2}[0-9]{2}[A-Z0-9]{4,30}$'
    ),
    ColumnType.DATE: re.compile(
        r'^\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}$'
    ),
    ColumnType.PERCENTAGE: re.compile(
        r'^-?\d+(\.\d+)?\s*%$'
    ),
}

# Arabic column name mappings for DB suggestions
_ARABIC_COLUMN_MAP = {
    "الاسم": "name_ar",
    "الاسم بالعربي": "name_ar",
    "الاسم بالعربية": "name_ar",
    "الاسم بالانجليزي": "name_en",
    "الاسم بالإنجليزي": "name_en",
    "رقم الموظف": "employee_number",
    "كود الموظف": "employee_number",
    "الراتب": "salary",
    "الراتب الأساسي": "basic_salary",
    "تاريخ التعيين": "hire_date",
    "تاريخ الالتحاق": "hire_date",
    "الهاتف": "phone",
    "الجوال": "mobile",
    "رقم الجوال": "mobile",
    "البريد": "email",
    "البريد الإلكتروني": "email",
    "IBAN": "iban",
    "رقم الحساب": "account_number",
    "الشركة": "company_id",
    "القسم": "department_id",
    "الإدارة": "department_id",
    "المسمى الوظيفي": "job_title_id",
    "الوظيفة": "job_title_id",
    "الجنسية": "nationality_id",
    "البنك": "bank_id",
    "الحالة": "status_id",
    "العنوان": "address",
    "المدينة": "city",
    "رقم الهوية": "id_number",
}


class ColumnDetector:
    """AI-powered column type detector."""

    def __init__(self):
        self._custom_mappings = {}

    def detect_type(self, values, col_name: str = "") -> Tuple[ColumnType, float]:
        """
        Detect column type from a series of values.

        Args:
            values: List or pandas Series of values
            col_name: Column name for context

        Returns:
            Tuple of (ColumnType, confidence)
        """
        try:
            import pandas as pd
            if isinstance(values, pd.Series):
                non_null = values.dropna()
            else:
                non_null = [v for v in values if v is not None and str(v).strip()]
        except ImportError:
            non_null = [v for v in values if v is not None and str(v).strip()]

        if len(non_null) == 0:
            return ColumnType.UNKNOWN, 0.0

        samples = [str(v).strip() for v in non_null][:100]

        # Check boolean first (small set of values)
        bool_values = {'true', 'false', 'yes', 'no', 'نعم', 'لا', '1', '0',
                       'صح', 'خطأ', 'y', 'n', 't', 'f'}
        bool_matches = sum(1 for s in samples if s.lower() in bool_values)
        if bool_matches / len(samples) > 0.9:
            return ColumnType.BOOLEAN, bool_matches / len(samples)

        # Check regex patterns
        for col_type, pattern in _PATTERNS.items():
            matches = sum(1 for s in samples if pattern.match(s))
            ratio = matches / len(samples)
            if ratio > 0.8:
                return col_type, ratio

        # Check numeric
        numeric_count = 0
        numeric_sum = 0
        for s in samples:
            cleaned = s.replace(',', '').replace('٫', '.').replace(' ', '')
            try:
                val = float(cleaned)
                numeric_count += 1
                numeric_sum += val
            except (ValueError, TypeError):
                pass

        if numeric_count / len(samples) > 0.9:
            avg = numeric_sum / numeric_count if numeric_count > 0 else 0
            # Heuristic: large numbers with 2 decimals are likely currency
            if avg > 100 and avg < 10_000_000:
                return ColumnType.CURRENCY, 0.7
            return ColumnType.NUMBER, 0.95

        return ColumnType.TEXT, 0.5

    def analyze_column(self, values, col_name: str) -> ColumnAnalysis:
        """
        Full analysis of a single column.

        Args:
            values: List or pandas Series of values
            col_name: Column name

        Returns:
            ColumnAnalysis with detected type, stats, and suggestions
        """
        try:
            import pandas as pd
            if isinstance(values, pd.Series):
                null_count = int(values.isnull().sum())
                unique_count = int(values.nunique())
                sample_values = values.dropna().head(5).tolist()
            else:
                null_count = sum(1 for v in values if v is None)
                unique_values = set(v for v in values if v is not None)
                unique_count = len(unique_values)
                sample_values = [v for v in values if v is not None][:5]
        except ImportError:
            null_count = sum(1 for v in values if v is None)
            unique_values = set(v for v in values if v is not None)
            unique_count = len(unique_values)
            sample_values = [v for v in values if v is not None][:5]

        detected_type, confidence = self.detect_type(values, col_name)
        suggested_db = self.suggest_db_column(col_name, detected_type)

        return ColumnAnalysis(
            name=col_name,
            detected_type=detected_type,
            confidence=confidence,
            sample_values=sample_values,
            null_count=null_count,
            unique_count=unique_count,
            suggested_db_column=suggested_db,
        )

    def suggest_db_column(self, col_name: str, col_type: ColumnType = None) -> Optional[str]:
        """
        Suggest a database column name based on the source column name.

        Args:
            col_name: Original column name
            col_type: Detected column type

        Returns:
            Suggested DB column name or None
        """
        # Check custom mappings first
        if col_name in self._custom_mappings:
            return self._custom_mappings[col_name]

        # Check Arabic mappings
        stripped = col_name.strip()
        if stripped in _ARABIC_COLUMN_MAP:
            return _ARABIC_COLUMN_MAP[stripped]

        # English column name normalization
        normalized = stripped.lower().replace(' ', '_').replace('-', '_')
        return normalized if normalized != stripped else None

    def add_custom_mapping(self, source_col: str, db_col: str):
        """Add a custom column name mapping."""
        self._custom_mappings[source_col] = db_col
