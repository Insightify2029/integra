"""
Excel Importer
==============
Import data from Excel files using pandas and openpyxl.

Features:
- Read Excel files (.xlsx, .xls)
- Read CSV files
- Preview data before import
- Validate required columns
- Map columns to database fields
- Batch import with progress

Usage:
    from core.import_export import ExcelImporter

    # Simple import
    importer = ExcelImporter("employees.xlsx")
    data = importer.read_all()

    # With validation
    importer = ExcelImporter("employees.xlsx")
    importer.set_required_columns(["الاسم", "الراتب", "القسم"])
    if importer.validate():
        data = importer.read_all()
    else:
        print(importer.get_errors())

    # Preview first rows
    preview = importer.preview(rows=5)
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Tuple
from datetime import datetime

from core.logging import app_logger


class ExcelImporter:
    """Import data from Excel/CSV files."""

    def __init__(self, file_path: str, sheet_name: Optional[str] = None):
        """
        Initialize Excel importer.

        Args:
            file_path: Path to Excel or CSV file
            sheet_name: Sheet name for Excel files (default: first sheet)
        """
        self.file_path = Path(file_path)
        self.sheet_name = sheet_name or 0  # 0 = first sheet

        self._df: Optional[pd.DataFrame] = None
        self._required_columns: List[str] = []
        self._column_mapping: Dict[str, str] = {}
        self._errors: List[str] = []
        self._warnings: List[str] = []

        app_logger.info(f"ExcelImporter initialized: {file_path}")

    def read(self) -> bool:
        """
        Read the file into memory.

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.file_path.exists():
                self._errors.append(f"الملف غير موجود: {self.file_path}")
                return False

            suffix = self.file_path.suffix.lower()

            if suffix == '.csv':
                # Try different encodings for Arabic support
                for encoding in ['utf-8', 'utf-8-sig', 'cp1256', 'iso-8859-6']:
                    try:
                        self._df = pd.read_csv(self.file_path, encoding=encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    self._errors.append("فشل في قراءة الملف - مشكلة في الترميز")
                    return False

            elif suffix in ['.xlsx', '.xls']:
                self._df = pd.read_excel(
                    self.file_path,
                    sheet_name=self.sheet_name,
                    engine='openpyxl' if suffix == '.xlsx' else None
                )

            else:
                self._errors.append(f"نوع ملف غير مدعوم: {suffix}")
                return False

            # Clean column names
            self._df.columns = self._df.columns.str.strip()

            app_logger.info(
                f"File read successfully: {len(self._df)} rows, "
                f"{len(self._df.columns)} columns"
            )
            return True

        except Exception as e:
            self._errors.append(f"خطأ في قراءة الملف: {str(e)}")
            app_logger.error(f"Excel read error: {e}")
            return False

    def preview(self, rows: int = 10) -> Optional[pd.DataFrame]:
        """
        Get preview of first N rows.

        Args:
            rows: Number of rows to preview

        Returns:
            DataFrame with preview data or None
        """
        if self._df is None:
            if not self.read():
                return None

        return self._df.head(rows)

    def get_columns(self) -> List[str]:
        """Get list of column names."""
        if self._df is None:
            if not self.read():
                return []

        return list(self._df.columns)

    def get_sheet_names(self) -> List[str]:
        """Get list of sheet names (Excel only)."""
        try:
            if self.file_path.suffix.lower() in ['.xlsx', '.xls']:
                xl = pd.ExcelFile(self.file_path)
                return xl.sheet_names
            return []
        except Exception:
            return []

    def set_required_columns(self, columns: List[str]) -> None:
        """Set columns that must exist in the file."""
        self._required_columns = columns

    def set_column_mapping(self, mapping: Dict[str, str]) -> None:
        """
        Set column name mapping.

        Args:
            mapping: Dict of {file_column: target_column}
        """
        self._column_mapping = mapping

    def validate(self) -> bool:
        """
        Validate the file against requirements.

        Returns:
            True if valid, False otherwise
        """
        self._errors = []
        self._warnings = []

        if self._df is None:
            if not self.read():
                return False

        # Check required columns
        if self._required_columns:
            missing = [
                col for col in self._required_columns
                if col not in self._df.columns
            ]
            if missing:
                self._errors.append(
                    f"أعمدة مطلوبة غير موجودة: {', '.join(missing)}"
                )
                return False

        # Check for empty file
        if len(self._df) == 0:
            self._errors.append("الملف فارغ")
            return False

        # Check for duplicate headers
        if len(self._df.columns) != len(set(self._df.columns)):
            self._warnings.append("يوجد أعمدة بأسماء مكررة")

        return len(self._errors) == 0

    def read_all(self) -> List[Dict[str, Any]]:
        """
        Read all data as list of dictionaries.

        Returns:
            List of row dictionaries
        """
        if self._df is None:
            if not self.read():
                return []

        # Apply column mapping if set
        df = self._df.copy()
        if self._column_mapping:
            df = df.rename(columns=self._column_mapping)

        # Convert to list of dicts, handling NaN values
        records = df.where(pd.notnull(df), None).to_dict('records')

        return records

    def read_column(self, column: str) -> List[Any]:
        """
        Read single column as list.

        Args:
            column: Column name

        Returns:
            List of values
        """
        if self._df is None:
            if not self.read():
                return []

        if column not in self._df.columns:
            return []

        return self._df[column].tolist()

    def get_row_count(self) -> int:
        """Get total number of rows."""
        if self._df is None:
            if not self.read():
                return 0

        return len(self._df)

    def get_errors(self) -> List[str]:
        """Get list of errors."""
        return self._errors

    def get_warnings(self) -> List[str]:
        """Get list of warnings."""
        return self._warnings

    def iter_rows(
        self,
        chunk_size: int = 100,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ):
        """
        Iterate over rows in chunks.

        Args:
            chunk_size: Number of rows per chunk
            progress_callback: Callback function (current, total)

        Yields:
            List of row dictionaries
        """
        if self._df is None:
            if not self.read():
                return

        total = len(self._df)

        # Apply column mapping
        df = self._df.copy()
        if self._column_mapping:
            df = df.rename(columns=self._column_mapping)

        for i in range(0, total, chunk_size):
            chunk = df.iloc[i:i + chunk_size]
            records = chunk.where(pd.notnull(chunk), None).to_dict('records')

            if progress_callback:
                progress_callback(min(i + chunk_size, total), total)

            yield records

    def to_dataframe(self) -> Optional[pd.DataFrame]:
        """Get the underlying DataFrame."""
        if self._df is None:
            self.read()
        return self._df


def read_excel(
    file_path: str,
    sheet_name: Optional[str] = None,
    required_columns: Optional[List[str]] = None
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Convenience function to read Excel file.

    Args:
        file_path: Path to file
        sheet_name: Sheet name (optional)
        required_columns: Required columns (optional)

    Returns:
        Tuple of (data, errors)
    """
    importer = ExcelImporter(file_path, sheet_name)

    if required_columns:
        importer.set_required_columns(required_columns)

    if not importer.validate():
        return [], importer.get_errors()

    return importer.read_all(), []


def get_excel_preview(
    file_path: str,
    rows: int = 10,
    sheet_name: Optional[str] = None
) -> Tuple[Optional[pd.DataFrame], List[str]]:
    """
    Convenience function to preview Excel file.

    Args:
        file_path: Path to file
        rows: Number of rows
        sheet_name: Sheet name (optional)

    Returns:
        Tuple of (DataFrame, errors)
    """
    importer = ExcelImporter(file_path, sheet_name)
    preview = importer.preview(rows)

    return preview, importer.get_errors()
