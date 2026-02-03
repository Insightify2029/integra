"""
PDF Reader
==========
Read and extract data from PDF files using pdfplumber.

Features:
- Extract text from PDF
- Extract tables from PDF
- Page-by-page processing
- Arabic text support

Usage:
    from core.import_export import PDFReader

    # Read all text
    reader = PDFReader("document.pdf")
    text = reader.extract_text()

    # Extract tables
    tables = reader.extract_tables()

    # Page by page
    for page_num, text in reader.iter_pages():
        print(f"Page {page_num}: {text[:100]}...")
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Generator, Tuple
import re

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

from core.logging import app_logger


class PDFReader:
    """Read and extract data from PDF files."""

    def __init__(self, file_path: str):
        """
        Initialize PDF reader.

        Args:
            file_path: Path to PDF file
        """
        if not PDFPLUMBER_AVAILABLE:
            raise ImportError(
                "pdfplumber not installed. Run: pip install pdfplumber"
            )

        self.file_path = Path(file_path)
        self._pdf = None
        self._errors: List[str] = []

        if not self.file_path.exists():
            self._errors.append(f"الملف غير موجود: {file_path}")

        app_logger.info(f"PDFReader initialized: {file_path}")

    def open(self) -> bool:
        """
        Open PDF file.

        Returns:
            True if successful
        """
        try:
            if self._pdf is not None:
                return True

            if not self.file_path.exists():
                return False

            self._pdf = pdfplumber.open(str(self.file_path))
            app_logger.info(f"PDF opened: {self.page_count} pages")
            return True

        except Exception as e:
            self._errors.append(f"خطأ في فتح الملف: {str(e)}")
            app_logger.error(f"PDF open error: {e}")
            return False

    def close(self) -> None:
        """Close PDF file."""
        if self._pdf is not None:
            self._pdf.close()
            self._pdf = None

    @property
    def page_count(self) -> int:
        """Get number of pages."""
        if not self.open():
            return 0
        return len(self._pdf.pages)

    def extract_text(
        self,
        page_numbers: Optional[List[int]] = None,
        separator: str = "\n\n"
    ) -> str:
        """
        Extract all text from PDF.

        Args:
            page_numbers: Specific pages to extract (1-indexed), None for all
            separator: Text separator between pages

        Returns:
            Extracted text
        """
        if not self.open():
            return ""

        try:
            texts = []

            if page_numbers is None:
                pages = self._pdf.pages
            else:
                pages = [
                    self._pdf.pages[i - 1]
                    for i in page_numbers
                    if 0 < i <= len(self._pdf.pages)
                ]

            for page in pages:
                text = page.extract_text()
                if text:
                    texts.append(text.strip())

            return separator.join(texts)

        except Exception as e:
            self._errors.append(f"خطأ في استخراج النص: {str(e)}")
            app_logger.error(f"Text extraction error: {e}")
            return ""

    def extract_text_from_page(self, page_number: int) -> str:
        """
        Extract text from specific page.

        Args:
            page_number: Page number (1-indexed)

        Returns:
            Page text
        """
        if not self.open():
            return ""

        try:
            if not 0 < page_number <= len(self._pdf.pages):
                return ""

            page = self._pdf.pages[page_number - 1]
            text = page.extract_text()
            return text.strip() if text else ""

        except Exception as e:
            app_logger.error(f"Page text extraction error: {e}")
            return ""

    def extract_tables(
        self,
        page_numbers: Optional[List[int]] = None
    ) -> List[List[List[str]]]:
        """
        Extract all tables from PDF.

        Args:
            page_numbers: Specific pages (1-indexed), None for all

        Returns:
            List of tables (each table is list of rows)
        """
        if not self.open():
            return []

        try:
            all_tables = []

            if page_numbers is None:
                pages = self._pdf.pages
            else:
                pages = [
                    self._pdf.pages[i - 1]
                    for i in page_numbers
                    if 0 < i <= len(self._pdf.pages)
                ]

            for page in pages:
                tables = page.extract_tables()
                if tables:
                    all_tables.extend(tables)

            return all_tables

        except Exception as e:
            self._errors.append(f"خطأ في استخراج الجداول: {str(e)}")
            app_logger.error(f"Table extraction error: {e}")
            return []

    def extract_tables_as_dicts(
        self,
        page_numbers: Optional[List[int]] = None
    ) -> List[List[Dict[str, Any]]]:
        """
        Extract tables as list of dictionaries.
        First row is used as headers.

        Args:
            page_numbers: Specific pages (1-indexed)

        Returns:
            List of tables (each table is list of row dicts)
        """
        tables = self.extract_tables(page_numbers)
        result = []

        for table in tables:
            if len(table) < 2:  # Need at least header + 1 row
                continue

            headers = [str(h).strip() if h else f"col_{i}"
                      for i, h in enumerate(table[0])]

            rows = []
            for row in table[1:]:
                row_dict = {}
                for i, value in enumerate(row):
                    if i < len(headers):
                        row_dict[headers[i]] = value
                rows.append(row_dict)

            result.append(rows)

        return result

    def iter_pages(self) -> Generator[Tuple[int, str], None, None]:
        """
        Iterate over pages.

        Yields:
            Tuple of (page_number, text)
        """
        if not self.open():
            return

        for i, page in enumerate(self._pdf.pages, 1):
            text = page.extract_text()
            yield i, text.strip() if text else ""

    def search_text(
        self,
        pattern: str,
        case_sensitive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search for text pattern in PDF.

        Args:
            pattern: Search pattern (regex supported)
            case_sensitive: Case sensitive search

        Returns:
            List of matches with page numbers
        """
        if not self.open():
            return []

        results = []
        flags = 0 if case_sensitive else re.IGNORECASE

        try:
            regex = re.compile(pattern, flags)

            for i, page in enumerate(self._pdf.pages, 1):
                text = page.extract_text()
                if not text:
                    continue

                matches = regex.findall(text)
                if matches:
                    results.append({
                        "page": i,
                        "matches": matches,
                        "count": len(matches)
                    })

            return results

        except re.error as e:
            self._errors.append(f"خطأ في نمط البحث: {str(e)}")
            return []

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get PDF metadata.

        Returns:
            Metadata dictionary
        """
        if not self.open():
            return {}

        try:
            return self._pdf.metadata or {}
        except Exception:
            return {}

    def get_errors(self) -> List[str]:
        """Get list of errors."""
        return self._errors

    def __enter__(self):
        """Context manager entry."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def read_pdf_text(file_path: str) -> Tuple[str, List[str]]:
    """
    Convenience function to read PDF text.

    Args:
        file_path: Path to PDF file

    Returns:
        Tuple of (text, errors)
    """
    reader = PDFReader(file_path)
    text = reader.extract_text()
    errors = reader.get_errors()
    reader.close()
    return text, errors


def read_pdf_tables(
    file_path: str,
    as_dicts: bool = True
) -> Tuple[List, List[str]]:
    """
    Convenience function to read PDF tables.

    Args:
        file_path: Path to PDF file
        as_dicts: Return as list of dicts

    Returns:
        Tuple of (tables, errors)
    """
    reader = PDFReader(file_path)

    if as_dicts:
        tables = reader.extract_tables_as_dicts()
    else:
        tables = reader.extract_tables()

    errors = reader.get_errors()
    reader.close()
    return tables, errors
