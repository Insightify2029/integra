"""
INTEGRA Email Module
====================
Email integration using Outlook Classic (win32com).
"""

from .outlook_connector import (
    OutlookConnector,
    get_outlook,
    is_outlook_available,
    get_inbox,
    get_folders,
    get_emails,
    send_email
)

from .email_cache import (
    EmailCache,
    get_email_cache,
    cache_emails,
    get_cached_emails,
    search_cached_emails
)

from .email_models import (
    Email,
    EmailFolder,
    EmailAttachment,
    EmailPriority,
    EmailImportance,
    FolderType
)

__all__ = [
    # Outlook Connector
    'OutlookConnector',
    'get_outlook',
    'is_outlook_available',
    'get_inbox',
    'get_folders',
    'get_emails',
    'send_email',
    # Email Cache
    'EmailCache',
    'get_email_cache',
    'cache_emails',
    'get_cached_emails',
    'search_cached_emails',
    # Models
    'Email',
    'EmailFolder',
    'EmailAttachment',
    'EmailPriority',
    'EmailImportance',
    'FolderType'
]
