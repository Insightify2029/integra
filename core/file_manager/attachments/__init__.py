"""
Attachments
===========
Hybrid document attachment system (DB BLOB + Local + Cloud).
"""

from .attachment_manager import AttachmentManager, Attachment, StorageType

__all__ = ['AttachmentManager', 'Attachment', 'StorageType']
