"""
PDF AI Studio
=============
Comprehensive PDF manipulation with AI-powered features.

Features:
- Split, merge, extract pages
- Rotate, compress
- OCR (Arabic + English)
- AI text enhancement and summarization
- Watermark and encryption
- Search within PDF
"""

from typing import List, Dict, Any, Optional
from pathlib import Path

from core.logging import app_logger


class PDFAIStudio:
    """AI-powered PDF studio."""

    def __init__(self):
        self.documents: Dict[str, Any] = {}

    def open(self, file_path: str) -> str:
        """
        Open a PDF file.

        Args:
            file_path: Path to PDF file

        Returns:
            Document ID for subsequent operations
        """
        import fitz

        doc_id = f"doc_{len(self.documents)}"
        self.documents[doc_id] = {
            "doc": fitz.open(file_path),
            "path": file_path,
        }
        app_logger.info(f"Opened PDF: {file_path} as {doc_id}")
        return doc_id

    def close(self, doc_id: str):
        """Close a document."""
        entry = self.documents.pop(doc_id, None)
        if entry:
            entry["doc"].close()

    def close_all(self):
        """Close all open documents."""
        for entry in self.documents.values():
            entry["doc"].close()
        self.documents.clear()

    def get_page_count(self, doc_id: str) -> int:
        """Get page count for a document."""
        entry = self.documents.get(doc_id)
        return len(entry["doc"]) if entry else 0

    # ═══════════════════════════════════════════════════════
    # Split & Merge
    # ═══════════════════════════════════════════════════════

    def split(self, doc_id: str, pages: List[int], output_path: str) -> bool:
        """
        Split specific pages into a new PDF.

        Args:
            doc_id: Source document ID
            pages: List of page numbers (0-indexed)
            output_path: Output file path

        Returns:
            True if successful
        """
        import fitz

        entry = self.documents.get(doc_id)
        if not entry:
            return False

        doc = entry["doc"]
        try:
            new_doc = fitz.open()
            for page_num in pages:
                if 0 <= page_num < len(doc):
                    new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

            new_doc.save(output_path)
            new_doc.close()
            app_logger.info(f"Split {len(pages)} pages to {output_path}")
            return True
        except Exception as e:
            app_logger.error(f"Split failed: {e}")
            return False

    def split_all(self, doc_id: str, output_folder: str) -> List[str]:
        """
        Split all pages into individual PDF files.

        Args:
            doc_id: Source document ID
            output_folder: Output directory

        Returns:
            List of output file paths
        """
        entry = self.documents.get(doc_id)
        if not entry:
            return []

        Path(output_folder).mkdir(parents=True, exist_ok=True)
        doc = entry["doc"]
        output_files = []

        for i in range(len(doc)):
            output_path = str(Path(output_folder) / f"page_{i+1}.pdf")
            if self.split(doc_id, [i], output_path):
                output_files.append(output_path)

        return output_files

    def merge(self, file_paths: List[str], output_path: str) -> bool:
        """
        Merge multiple PDF files into one.

        Args:
            file_paths: List of PDF file paths
            output_path: Output file path

        Returns:
            True if successful
        """
        import fitz

        try:
            merged = fitz.open()
            for path in file_paths:
                doc = fitz.open(path)
                merged.insert_pdf(doc)
                doc.close()

            merged.save(output_path)
            merged.close()
            app_logger.info(f"Merged {len(file_paths)} files to {output_path}")
            return True
        except Exception as e:
            app_logger.error(f"Merge failed: {e}")
            return False

    def extract_pages(self, doc_id: str, start: int, end: int,
                      output_path: str) -> bool:
        """
        Extract a range of pages.

        Args:
            doc_id: Source document ID
            start: Start page (0-indexed, inclusive)
            end: End page (0-indexed, inclusive)
            output_path: Output file path

        Returns:
            True if successful
        """
        return self.split(doc_id, list(range(start, end + 1)), output_path)

    # ═══════════════════════════════════════════════════════
    # Transform
    # ═══════════════════════════════════════════════════════

    def rotate_pages(self, doc_id: str, pages: List[int],
                     angle: int, output_path: str) -> bool:
        """
        Rotate specific pages.

        Args:
            doc_id: Document ID
            pages: Page numbers to rotate
            angle: Rotation angle (90, 180, 270)
            output_path: Output path

        Returns:
            True if successful
        """
        entry = self.documents.get(doc_id)
        if not entry:
            return False

        doc = entry["doc"]
        try:
            for page_num in pages:
                if 0 <= page_num < len(doc):
                    page = doc[page_num]
                    page.set_rotation(angle)

            doc.save(output_path)
            return True
        except Exception as e:
            app_logger.error(f"Rotate failed: {e}")
            return False

    def compress(self, doc_id: str, output_path: str,
                 quality: str = "medium") -> Dict[str, Any]:
        """
        Compress a PDF file.

        Args:
            doc_id: Document ID
            output_path: Output path
            quality: 'low' (max compression), 'medium', 'high' (min compression)

        Returns:
            Dict with compression stats
        """
        import fitz

        entry = self.documents.get(doc_id)
        if not entry:
            return {"success": False}

        doc = entry["doc"]
        try:
            original_bytes = doc.tobytes()
            original_size = len(original_bytes)

            if quality == "low":
                doc.save(output_path, garbage=4, deflate=True,
                         clean=True, linear=True)
            elif quality == "medium":
                doc.save(output_path, garbage=3, deflate=True, clean=True)
            else:
                doc.save(output_path, garbage=2, deflate=True)

            compressed_size = Path(output_path).stat().st_size

            return {
                "success": True,
                "original_size": original_size,
                "compressed_size": compressed_size,
                "reduction_percent": round((1 - compressed_size / original_size) * 100, 1)
                if original_size > 0 else 0,
            }
        except Exception as e:
            app_logger.error(f"Compress failed: {e}")
            return {"success": False, "error": str(e)}

    # ═══════════════════════════════════════════════════════
    # OCR
    # ═══════════════════════════════════════════════════════

    def ocr_page(self, doc_id: str, page_num: int,
                 lang: str = "ara+eng") -> str:
        """
        Extract text from a page using OCR.

        Args:
            doc_id: Document ID
            page_num: Page number (0-indexed)
            lang: Tesseract language code

        Returns:
            Extracted text
        """
        entry = self.documents.get(doc_id)
        if not entry or page_num >= len(entry["doc"]):
            return ""

        try:
            import fitz
            from PIL import Image
            import pytesseract
            import io

            doc = entry["doc"]
            page = doc[page_num]

            # Convert page to high-res image
            mat = fitz.Matrix(3.0, 3.0)
            pix = page.get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # OCR
            text = pytesseract.image_to_string(img, lang=lang, config='--psm 6')
            return text

        except ImportError as e:
            app_logger.warning(f"OCR dependencies not available: {e}")
            # Fallback to built-in text extraction
            return entry["doc"][page_num].get_text()
        except Exception as e:
            app_logger.error(f"OCR failed on page {page_num}: {e}")
            return ""

    def ocr_document(self, doc_id: str, lang: str = "ara+eng") -> List[Dict]:
        """
        OCR all pages.

        Args:
            doc_id: Document ID
            lang: Language code

        Returns:
            List of dicts with page text and stats
        """
        entry = self.documents.get(doc_id)
        if not entry:
            return []

        results = []
        for i in range(len(entry["doc"])):
            text = self.ocr_page(doc_id, i, lang)
            results.append({
                "page": i + 1,
                "text": text,
                "word_count": len(text.split()),
            })

        return results

    # ═══════════════════════════════════════════════════════
    # Text & Search
    # ═══════════════════════════════════════════════════════

    def get_all_text(self, doc_id: str) -> str:
        """Get all text from the document."""
        entry = self.documents.get(doc_id)
        if not entry:
            return ""

        text = ""
        for page in entry["doc"]:
            text += page.get_text() + "\n"
        return text

    def search(self, doc_id: str, query: str) -> List[Dict]:
        """
        Search for text in the document.

        Args:
            doc_id: Document ID
            query: Search query

        Returns:
            List of results with page numbers and positions
        """
        entry = self.documents.get(doc_id)
        if not entry:
            return []

        results = []
        doc = entry["doc"]
        for page_num, page in enumerate(doc):
            text = page.get_text()
            if query.lower() in text.lower():
                instances = page.search_for(query)
                results.append({
                    "page": page_num + 1,
                    "count": len(instances),
                    "positions": [
                        {"x": round(r.x0, 1), "y": round(r.y0, 1)}
                        for r in instances
                    ],
                })

        return results

    # ═══════════════════════════════════════════════════════
    # Watermark & Security
    # ═══════════════════════════════════════════════════════

    def add_watermark(self, doc_id: str, text: str,
                      output_path: str, opacity: float = 0.3) -> bool:
        """
        Add a text watermark to all pages.

        Args:
            doc_id: Document ID
            text: Watermark text
            output_path: Output path
            opacity: Watermark opacity (0.0 to 1.0)

        Returns:
            True if successful
        """
        import fitz

        entry = self.documents.get(doc_id)
        if not entry:
            return False

        doc = entry["doc"]
        try:
            gray = opacity
            for page in doc:
                rect = page.rect
                point = fitz.Point(rect.width / 4, rect.height / 2)
                page.insert_text(
                    point, text,
                    fontsize=40,
                    rotate=45,
                    color=(gray, gray, gray),
                    overlay=True,
                )

            doc.save(output_path)
            return True
        except Exception as e:
            app_logger.error(f"Watermark failed: {e}")
            return False

    def encrypt(self, doc_id: str, password: str,
                output_path: str) -> bool:
        """
        Encrypt PDF with a password.

        Args:
            doc_id: Document ID
            password: Encryption password
            output_path: Output path

        Returns:
            True if successful
        """
        import fitz

        entry = self.documents.get(doc_id)
        if not entry:
            return False

        try:
            entry["doc"].save(
                output_path,
                encryption=fitz.PDF_ENCRYPT_AES_256,
                user_pw=password,
                owner_pw=password,
            )
            return True
        except Exception as e:
            app_logger.error(f"Encrypt failed: {e}")
            return False

    # ═══════════════════════════════════════════════════════
    # AI Features
    # ═══════════════════════════════════════════════════════

    def summarize_document(self, doc_id: str) -> str:
        """
        Summarize document content using AI.

        Args:
            doc_id: Document ID

        Returns:
            AI-generated summary
        """
        full_text = self.get_all_text(doc_id)

        # If no text, try OCR
        if len(full_text.strip()) < 100:
            ocr_results = self.ocr_document(doc_id)
            full_text = "\n".join([r["text"] for r in ocr_results])

        if not full_text.strip():
            return "No text could be extracted from this document."

        try:
            from core.ai import get_ai_service
            ai = get_ai_service()
            summary = ai.summarize(full_text[:5000], max_length=500)
            return summary
        except Exception as e:
            app_logger.warning(f"AI summarization not available: {e}")
            # Return first 500 chars as fallback
            return full_text[:500] + "..."

    def extract_key_info(self, doc_id: str) -> Dict[str, Any]:
        """
        Extract key information from the document using AI.

        Returns:
            Dict with extracted entities (people, dates, amounts, etc.)
        """
        text = self.get_all_text(doc_id)
        if not text.strip():
            return {"extracted_info": "No text found in document."}

        try:
            from core.ai import get_ai_service
            ai = get_ai_service()

            prompt = (
                "استخرج المعلومات الرئيسية من المستند التالي:\n"
                "- الموضوع الرئيسي\n"
                "- الأشخاص المذكورين\n"
                "- التواريخ\n"
                "- المبالغ المالية\n"
                "- الأرقام المهمة\n\n"
                f"المستند:\n{text[:5000]}"
            )

            response = ai.chat(prompt)
            return {"extracted_info": response}

        except Exception as e:
            app_logger.warning(f"AI extraction not available: {e}")
            return {"extracted_info": "AI service not available."}

    # ═══════════════════════════════════════════════════════
    # Conversion
    # ═══════════════════════════════════════════════════════

    def to_images(self, doc_id: str, output_folder: str,
                  dpi: int = 150, fmt: str = "png") -> List[str]:
        """
        Convert PDF pages to images.

        Args:
            doc_id: Document ID
            output_folder: Output directory
            dpi: Resolution in DPI
            fmt: Image format ('png', 'jpg')

        Returns:
            List of output image paths
        """
        import fitz

        entry = self.documents.get(doc_id)
        if not entry:
            return []

        Path(output_folder).mkdir(parents=True, exist_ok=True)
        doc = entry["doc"]
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)

        output_files = []
        for i, page in enumerate(doc):
            pix = page.get_pixmap(matrix=mat)
            output_path = str(Path(output_folder) / f"page_{i+1}.{fmt}")
            pix.save(output_path)
            output_files.append(output_path)

        return output_files

    def __del__(self):
        """Cleanup on destruction."""
        self.close_all()
