"""
File Manager Core
=================
Smart File Manager with AI-powered tools for Excel, PDF, Images, Word,
File Browsing, Cloud Storage, and Document Attachments.
"""

from .excel.excel_ai_engine import ExcelAIEngine
from .excel.column_detector import ColumnDetector
from .excel.data_cleaner import DataCleaner
from .excel.db_importer import DBImporter

from .pdf.pdf_ai_studio import PDFAIStudio
from .pdf.pdf_tools import PDFTools

from .image.image_tools import ImageTools

from .word.word_engine import WordEngine

from .browser.file_browser import FileBrowser, FileInfo
from .browser.file_search import FileSearch

from .cloud.cloud_storage import CloudStorageManager, CloudProvider

from .attachments.attachment_manager import AttachmentManager

__all__ = [
    # Excel
    'ExcelAIEngine', 'ColumnDetector', 'DataCleaner', 'DBImporter',
    # PDF
    'PDFAIStudio', 'PDFTools',
    # Image
    'ImageTools',
    # Word
    'WordEngine',
    # Browser
    'FileBrowser', 'FileInfo', 'FileSearch',
    # Cloud
    'CloudStorageManager', 'CloudProvider',
    # Attachments
    'AttachmentManager',
]
