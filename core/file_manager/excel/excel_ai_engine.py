"""
Excel AI Engine
===============
AI-powered Excel/CSV import, analysis, cleaning, and database mapping.

Features:
- Smart file loading (Excel/CSV with encoding detection)
- AI column type detection
- Automatic data cleaning
- Column-to-DB mapping suggestions
- Database import with multiple modes
"""

from typing import List, Dict, Any, Optional, Tuple

from core.logging import app_logger
from .column_detector import ColumnDetector, ColumnAnalysis, ColumnType
from .data_cleaner import DataCleaner
from .db_importer import DBImporter


class ExcelAIEngine:
    """AI-powered Excel/CSV engine."""

    def __init__(self, file_path: str = None):
        self.file_path = file_path
        self.df = None
        self.column_analyses: List[ColumnAnalysis] = []

        self._detector = ColumnDetector()
        self._cleaner = DataCleaner()
        self._importer = DBImporter()

    def load(self, file_path: str = None) -> Tuple[bool, str]:
        """
        Load an Excel or CSV file.

        Args:
            file_path: Path to the file (overrides constructor path)

        Returns:
            Tuple of (success, message)
        """
        path = file_path or self.file_path
        if not path:
            return False, "No file path specified"

        self.file_path = path

        try:
            import pandas as pd

            if path.lower().endswith('.csv'):
                self.df = self._load_csv(path)
            elif path.lower().endswith(('.xls', '.xlsx', '.xlsm', '.xlsb')):
                self.df = pd.read_excel(path)
            else:
                return False, f"Unsupported file format: {path}"

            self._cleaner.set_data(self.df)
            row_count = len(self.df)
            col_count = len(self.df.columns)

            app_logger.info(f"Loaded file: {path} ({row_count} rows, {col_count} columns)")
            return True, f"Loaded {row_count} rows, {col_count} columns"

        except Exception as e:
            app_logger.error(f"Failed to load file {path}: {e}")
            return False, str(e)

    def _load_csv(self, path: str):
        """Load CSV with automatic encoding detection."""
        import pandas as pd

        encodings = ['utf-8', 'utf-8-sig', 'cp1256', 'iso-8859-6', 'latin1']
        for enc in encodings:
            try:
                return pd.read_csv(path, encoding=enc)
            except (UnicodeDecodeError, UnicodeError):
                continue

        # Fallback with error handling
        return pd.read_csv(path, encoding='utf-8', errors='replace')

    def analyze_columns(self) -> List[ColumnAnalysis]:
        """
        Analyze all columns to detect types and suggest mappings.

        Returns:
            List of ColumnAnalysis for each column
        """
        if self.df is None:
            return []

        analyses = []
        for col in self.df.columns:
            analysis = self._detector.analyze_column(self.df[col], col)
            analyses.append(analysis)

        self.column_analyses = analyses
        return analyses

    def clean_data(self) -> Dict[str, Any]:
        """
        Run automatic data cleaning.

        Returns:
            Dict with cleaning results
        """
        if self.df is None:
            return {"success": False, "message": "No file loaded"}

        result = self._cleaner.clean_all()
        self.df = self._cleaner.df
        return result

    def detect_duplicates(self, columns: List[str] = None):
        """
        Detect duplicate rows.

        Args:
            columns: Subset of columns to check

        Returns:
            DataFrame with duplicates
        """
        if self.df is None:
            return None
        return self._cleaner.detect_duplicates(columns)

    def remove_duplicates(self, columns: List[str] = None) -> int:
        """
        Remove duplicate rows.

        Args:
            columns: Subset of columns to check

        Returns:
            Number removed
        """
        if self.df is None:
            return 0
        removed = self._cleaner.remove_duplicates(columns)
        self.df = self._cleaner.df
        return removed

    def preview(self, rows: int = 10):
        """
        Preview the data.

        Args:
            rows: Number of rows to preview

        Returns:
            DataFrame with preview
        """
        if self.df is None:
            return None
        return self.df.head(rows)

    def get_column_mapping_suggestions(self, target_table: str) -> Dict[str, str]:
        """
        Get AI suggestions for mapping columns to database table.

        Args:
            target_table: Target database table name

        Returns:
            Dict mapping source columns to suggested DB columns
        """
        if not self.column_analyses:
            self.analyze_columns()

        suggestions = {}
        for analysis in self.column_analyses:
            if analysis.suggested_db_column:
                suggestions[analysis.name] = analysis.suggested_db_column

        return suggestions

    def import_to_database(self, table_name: str,
                           column_mapping: Dict[str, str],
                           mode: str = "append",
                           key_columns: List[str] = None) -> Dict[str, Any]:
        """
        Import data to database.

        Args:
            table_name: Target table
            column_mapping: Column mapping
            mode: 'append', 'replace', or 'update'
            key_columns: Key columns for upsert mode

        Returns:
            Dict with import results
        """
        if self.df is None:
            return {"success": False, "message": "No file loaded"}

        return self._importer.import_data(
            self.df, table_name, column_mapping, mode, key_columns
        )

    def get_data_quality_report(self) -> Dict[str, Any]:
        """Get a quality report for the loaded data."""
        return self._cleaner.get_data_quality_report()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get basic stats about the loaded data.

        Returns:
            Dict with file stats
        """
        if self.df is None:
            return {"loaded": False}

        return {
            "loaded": True,
            "file_path": self.file_path,
            "rows": len(self.df),
            "columns": len(self.df.columns),
            "column_names": list(self.df.columns),
            "dtypes": {col: str(dtype) for col, dtype in self.df.dtypes.items()},
        }
