"""
Email UI Components
===================
UI components for email viewing and management.
"""

from .email_list import (
    EmailListWidget,
    EmailListItem,
    create_email_list
)

from .email_viewer import (
    EmailViewerWidget,
    create_email_viewer
)

from .email_panel import (
    EmailPanel,
    create_email_panel
)

__all__ = [
    'EmailListWidget',
    'EmailListItem',
    'create_email_list',
    'EmailViewerWidget',
    'create_email_viewer',
    'EmailPanel',
    'create_email_panel'
]
