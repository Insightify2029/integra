"""
Data Cleaner
=============
Automatic data cleaning for imported Excel/CSV data.
Handles: whitespace, duplicates, formatting, missing values.
"""

from typing import List, Dict, Any, Optional
from core.logging import app_logger


class DataCleaner:
    """Automatic data cleaner for tabular data."""

    def __init__(self, df=None):
        """
        Initialize with an optional pandas DataFrame.

        Args:
            df: pandas DataFrame to clean
        """
        self.df = df
        self._changes_log: List[str] = []

    def set_data(self, df):
        """Set the DataFrame to clean."""
        self.df = df
        self._changes_log = []

    def clean_all(self) -> Dict[str, Any]:
        """
        Run all cleaning operations.

        Returns:
            Dict with cleaning results and statistics
        """
        if self.df is None:
            return {"success": False, "message": "No data loaded"}

        original_rows = len(self.df)
        original_cols = len(self.df.columns)
        self._changes_log = []

        self.strip_whitespace()
        self.remove_empty_rows()
        self.normalize_arabic_text()
        self.standardize_phone_numbers()

        return {
            "success": True,
            "original_rows": original_rows,
            "cleaned_rows": len(self.df),
            "removed_rows": original_rows - len(self.df),
            "columns": original_cols,
            "changes": self._changes_log,
        }

    def strip_whitespace(self):
        """Remove leading/trailing whitespace from all text columns."""
        import pandas as pd

        text_cols = self.df.select_dtypes(include=['object']).columns
        for col in text_cols:
            before = self.df[col].copy()
            self.df[col] = self.df[col].astype(str).str.strip()
            # Restore NaN values
            self.df.loc[before.isna(), col] = None
            changed = (before.fillna('') != self.df[col].fillna('')).sum()
            if changed > 0:
                self._changes_log.append(f"Stripped whitespace in '{col}' ({changed} cells)")

    def remove_empty_rows(self):
        """Remove rows that are completely empty."""
        before = len(self.df)
        self.df = self.df.dropna(how='all')
        removed = before - len(self.df)
        if removed > 0:
            self._changes_log.append(f"Removed {removed} empty rows")

    def remove_duplicates(self, columns: List[str] = None, keep: str = 'first') -> int:
        """
        Remove duplicate rows.

        Args:
            columns: Subset of columns to check for duplicates (None = all)
            keep: Which duplicate to keep ('first', 'last', False)

        Returns:
            Number of duplicates removed
        """
        before = len(self.df)
        self.df = self.df.drop_duplicates(subset=columns, keep=keep)
        removed = before - len(self.df)
        if removed > 0:
            self._changes_log.append(f"Removed {removed} duplicate rows")
        return removed

    def detect_duplicates(self, columns: List[str] = None):
        """
        Detect duplicate rows without removing them.

        Args:
            columns: Subset of columns to check

        Returns:
            DataFrame with duplicate rows
        """
        if columns:
            return self.df[self.df.duplicated(subset=columns, keep=False)]
        return self.df[self.df.duplicated(keep=False)]

    def normalize_arabic_text(self):
        """Normalize Arabic text (hamza, taa marbuta, etc.)."""
        import pandas as pd

        text_cols = self.df.select_dtypes(include=['object']).columns
        replacements = {
            '\u0623': '\u0627',  # أ -> ا
            '\u0625': '\u0627',  # إ -> ا
            '\u0622': '\u0627',  # آ -> ا
            '\u0629': '\u0647',  # ة -> ه
        }

        for col in text_cols:
            original = self.df[col].copy()
            for old, new in replacements.items():
                self.df[col] = self.df[col].astype(str).str.replace(old, new, regex=False)
            changed = (original.fillna('') != self.df[col].fillna('')).sum()
            if changed > 0:
                self._changes_log.append(f"Normalized Arabic in '{col}' ({changed} cells)")

    def standardize_phone_numbers(self, country_code: str = "+966"):
        """
        Standardize phone number formats.

        Args:
            country_code: Default country code to prepend
        """
        import re
        import pandas as pd

        text_cols = self.df.select_dtypes(include=['object']).columns
        phone_pattern = re.compile(r'^0?5\d{8}$')

        for col in text_cols:
            sample = self.df[col].dropna().astype(str).head(20)
            phone_matches = sum(1 for v in sample if phone_pattern.match(v.strip()))
            if phone_matches / max(len(sample), 1) > 0.5:
                count = 0
                for idx, val in self.df[col].items():
                    if val and phone_pattern.match(str(val).strip()):
                        clean = str(val).strip()
                        if clean.startswith('0'):
                            clean = clean[1:]
                        self.df.at[idx, col] = f"{country_code}{clean}"
                        count += 1
                if count > 0:
                    self._changes_log.append(
                        f"Standardized {count} phone numbers in '{col}'"
                    )

    def fill_missing(self, column: str, strategy: str = "mode",
                     value: Any = None) -> int:
        """
        Fill missing values in a column.

        Args:
            column: Column name
            strategy: 'mode' (most common), 'mean', 'median', 'value' (custom)
            value: Custom value when strategy='value'

        Returns:
            Number of values filled
        """
        if column not in self.df.columns:
            return 0

        missing_before = int(self.df[column].isnull().sum())

        if strategy == "mode":
            mode_val = self.df[column].mode()
            if len(mode_val) > 0:
                self.df[column] = self.df[column].fillna(mode_val[0])
        elif strategy == "mean":
            self.df[column] = self.df[column].fillna(self.df[column].mean())
        elif strategy == "median":
            self.df[column] = self.df[column].fillna(self.df[column].median())
        elif strategy == "value" and value is not None:
            self.df[column] = self.df[column].fillna(value)

        filled = missing_before - int(self.df[column].isnull().sum())
        if filled > 0:
            self._changes_log.append(f"Filled {filled} missing values in '{column}'")
        return filled

    def get_data_quality_report(self) -> Dict[str, Any]:
        """
        Generate a data quality report.

        Returns:
            Dict with quality metrics per column
        """
        if self.df is None:
            return {}

        report = {
            "total_rows": len(self.df),
            "total_columns": len(self.df.columns),
            "columns": {},
        }

        for col in self.df.columns:
            series = self.df[col]
            report["columns"][col] = {
                "null_count": int(series.isnull().sum()),
                "null_percent": round(series.isnull().sum() / len(self.df) * 100, 1),
                "unique_count": int(series.nunique()),
                "dtype": str(series.dtype),
            }

        return report

    @property
    def changes(self) -> List[str]:
        """Get the log of changes made."""
        return self._changes_log.copy()
