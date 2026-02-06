"""
PDF Tools
=========
Basic PDF operations: info, page count, text extraction.
"""

from typing import Dict, Any, Optional
from pathlib import Path

from core.logging import app_logger


class PDFTools:
    """Basic PDF utility functions."""

    @staticmethod
    def get_info(file_path: str) -> Dict[str, Any]:
        """
        Get PDF file information.

        Args:
            file_path: Path to PDF file

        Returns:
            Dict with page count, size, metadata, etc.
        """
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(file_path)
            metadata = doc.metadata or {}
            file_size = Path(file_path).stat().st_size

            info = {
                "file_path": file_path,
                "page_count": len(doc),
                "file_size": file_size,
                "file_size_formatted": _format_size(file_size),
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
                "creation_date": metadata.get("creationDate", ""),
                "is_encrypted": doc.is_encrypted,
            }

            doc.close()
            return info

        except Exception as e:
            app_logger.error(f"Failed to get PDF info: {e}")
            return {"error": str(e)}

    @staticmethod
    def get_page_count(file_path: str) -> int:
        """Get the number of pages in a PDF."""
        try:
            import fitz
            doc = fitz.open(file_path)
            count = len(doc)
            doc.close()
            return count
        except Exception:
            return 0

    @staticmethod
    def extract_text(file_path: str, page_num: int = None) -> str:
        """
        Extract text from PDF.

        Args:
            file_path: Path to PDF
            page_num: Specific page (0-indexed), None for all pages

        Returns:
            Extracted text
        """
        try:
            import fitz
            doc = fitz.open(file_path)

            if page_num is not None:
                if 0 <= page_num < len(doc):
                    text = doc[page_num].get_text()
                else:
                    text = ""
            else:
                text = ""
                for page in doc:
                    text += page.get_text() + "\n"

            doc.close()
            return text

        except Exception as e:
            app_logger.error(f"Failed to extract text: {e}")
            return ""

    @staticmethod
    def has_text(file_path: str) -> bool:
        """Check if PDF contains extractable text (not just scanned images)."""
        text = PDFTools.extract_text(file_path)
        return len(text.strip()) > 50

    @staticmethod
    def get_page_images(file_path: str, page_num: int) -> list:
        """
        Get images from a specific page.

        Args:
            file_path: Path to PDF
            page_num: Page number (0-indexed)

        Returns:
            List of image info dicts
        """
        try:
            import fitz
            doc = fitz.open(file_path)

            if page_num >= len(doc):
                doc.close()
                return []

            page = doc[page_num]
            images = page.get_images(full=True)

            result = []
            for img in images:
                xref = img[0]
                result.append({
                    "xref": xref,
                    "width": img[2],
                    "height": img[3],
                })

            doc.close()
            return result

        except Exception as e:
            app_logger.error(f"Failed to get page images: {e}")
            return []


def _format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
