"""
Email Models
============
Data models for email handling.
"""

from typing import Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum


class EmailPriority(IntEnum):
    """Email priority levels (matches Outlook constants)."""
    LOW = 0
    NORMAL = 1
    HIGH = 2


class EmailImportance(IntEnum):
    """Email importance (Outlook OlImportance)."""
    LOW = 0
    NORMAL = 1
    HIGH = 2


class FolderType(IntEnum):
    """Outlook folder types (OlDefaultFolders)."""
    DELETED = 3
    OUTBOX = 4
    SENT = 5
    INBOX = 6
    CALENDAR = 9
    CONTACTS = 10
    JOURNAL = 11
    NOTES = 12
    TASKS = 13
    DRAFTS = 16
    JUNK = 23


@dataclass
class EmailAttachment:
    """Represents an email attachment."""
    filename: str
    size: int
    content_type: Optional[str] = None
    path: Optional[str] = None  # Local path if saved

    @property
    def size_kb(self) -> float:
        """Size in KB."""
        return self.size / 1024

    @property
    def size_display(self) -> str:
        """Human-readable size."""
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f} KB"
        else:
            return f"{self.size / (1024 * 1024):.1f} MB"


@dataclass
class EmailFolder:
    """Represents an email folder."""
    name: str
    folder_type: Optional[FolderType] = None
    entry_id: Optional[str] = None
    unread_count: int = 0
    total_count: int = 0
    subfolders: List['EmailFolder'] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        """Get display name with unread count."""
        if self.unread_count > 0:
            return f"{self.name} ({self.unread_count})"
        return self.name

    @property
    def icon(self) -> str:
        """Get folder icon based on type."""
        icons = {
            FolderType.INBOX: "📥",
            FolderType.SENT: "📤",
            FolderType.DRAFTS: "📝",
            FolderType.DELETED: "🗑️",
            FolderType.JUNK: "⚠️",
            FolderType.OUTBOX: "📮",
        }
        return icons.get(self.folder_type, "📁")


@dataclass
class Email:
    """Represents an email message."""
    # Identifiers
    entry_id: str
    conversation_id: Optional[str] = None

    # Basic info
    subject: str = ""
    body: str = ""
    body_html: Optional[str] = None

    # Sender
    sender_name: str = ""
    sender_email: str = ""

    # Recipients
    to: List[str] = field(default_factory=list)
    cc: List[str] = field(default_factory=list)
    bcc: List[str] = field(default_factory=list)

    # Dates
    received_time: Optional[datetime] = None
    sent_time: Optional[datetime] = None
    created_time: Optional[datetime] = None

    # Status
    is_read: bool = False
    is_flagged: bool = False
    importance: EmailImportance = EmailImportance.NORMAL
    priority: EmailPriority = EmailPriority.NORMAL

    # Attachments
    attachments: List[EmailAttachment] = field(default_factory=list)
    has_attachments: bool = False

    # Folder
    folder_name: Optional[str] = None
    folder_id: Optional[str] = None

    # Categories/Labels
    categories: List[str] = field(default_factory=list)

    # AI Analysis (filled later)
    ai_summary: Optional[str] = None
    ai_category: Optional[str] = None
    ai_priority: Optional[str] = None
    ai_tasks: List[str] = field(default_factory=list)

    @property
    def preview(self) -> str:
        """Get preview of email body (first 100 chars)."""
        text = self.body.strip()
        if len(text) > 100:
            return text[:100] + "..."
        return text

    @property
    def display_date(self) -> str:
        """Get display date."""
        dt = self.received_time or self.sent_time or self.created_time
        if not dt:
            return ""

        now = datetime.now()
        if dt.date() == now.date():
            return dt.strftime("%H:%M")
        elif dt.year == now.year:
            return dt.strftime("%d/%m")
        else:
            return dt.strftime("%d/%m/%Y")

    @property
    def importance_icon(self) -> str:
        """Get importance icon."""
        if self.importance == EmailImportance.HIGH:
            return "❗"
        elif self.importance == EmailImportance.LOW:
            return "⬇️"
        return ""

    @property
    def status_icons(self) -> str:
        """Get status icons."""
        icons = []
        if not self.is_read:
            icons.append("●")  # Unread dot
        if self.is_flagged:
            icons.append("🚩")
        if self.has_attachments:
            icons.append("📎")
        if self.importance == EmailImportance.HIGH:
            icons.append("❗")
        return " ".join(icons)

    def to_dict(self) -> dict:
        """Convert to dictionary for caching."""
        return {
            'entry_id': self.entry_id,
            'conversation_id': self.conversation_id,
            'subject': self.subject,
            'body': self.body,
            'body_html': self.body_html,
            'sender_name': self.sender_name,
            'sender_email': self.sender_email,
            'to': ','.join(self.to),
            'cc': ','.join(self.cc),
            'received_time': self.received_time.isoformat() if self.received_time else None,
            'sent_time': self.sent_time.isoformat() if self.sent_time else None,
            'is_read': self.is_read,
            'is_flagged': self.is_flagged,
            'importance': self.importance.value,
            'has_attachments': self.has_attachments,
            'folder_name': self.folder_name,
            'folder_id': self.folder_id,
            'categories': ','.join(self.categories),
            'ai_summary': self.ai_summary,
            'ai_category': self.ai_category,
            'ai_priority': self.ai_priority,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Email':
        """Create Email from dictionary."""
        return cls(
            entry_id=data['entry_id'],
            conversation_id=data.get('conversation_id'),
            subject=data.get('subject', ''),
            body=data.get('body', ''),
            body_html=data.get('body_html'),
            sender_name=data.get('sender_name', ''),
            sender_email=data.get('sender_email', ''),
            to=data.get('to', '').split(',') if data.get('to') else [],
            cc=data.get('cc', '').split(',') if data.get('cc') else [],
            received_time=datetime.fromisoformat(data['received_time']) if data.get('received_time') else None,
            sent_time=datetime.fromisoformat(data['sent_time']) if data.get('sent_time') else None,
            is_read=data.get('is_read', False),
            is_flagged=data.get('is_flagged', False),
            importance=EmailImportance(data.get('importance', 1)),
            has_attachments=data.get('has_attachments', False),
            folder_name=data.get('folder_name'),
            folder_id=data.get('folder_id'),
            categories=data.get('categories', '').split(',') if data.get('categories') else [],
            ai_summary=data.get('ai_summary'),
            ai_category=data.get('ai_category'),
            ai_priority=data.get('ai_priority'),
        )
