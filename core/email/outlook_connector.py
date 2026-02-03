"""
Outlook Connector
=================
Connect to Outlook Classic using win32com.
Provides email reading, sending, and folder management.
"""

from typing import Optional, List, Generator, Callable
from datetime import datetime, timedelta
import threading

from .email_models import (
    Email, EmailFolder, EmailAttachment,
    EmailImportance, EmailPriority, FolderType
)
from core.logging import app_logger

# Try to import win32com
try:
    import win32com.client
    import pythoncom
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    win32com = None
    pythoncom = None


class OutlookConnector:
    """
    Connector for Outlook Classic.

    Features:
    - Read emails from any folder
    - Send emails with attachments
    - Manage folders
    - Mark as read/flagged
    - Thread-safe operations

    Usage:
        outlook = OutlookConnector()
        if outlook.connect():
            emails = outlook.get_emails(limit=50)
            for email in emails:
                print(email.subject)
    """

    _instance: Optional['OutlookConnector'] = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._outlook = None
        self._namespace = None
        self._connected = False
        self._account_name: Optional[str] = None
        self._account_email: Optional[str] = None
        self._initialized = True

    @property
    def is_connected(self) -> bool:
        """Check if connected to Outlook."""
        return self._connected and self._outlook is not None

    @property
    def account_name(self) -> Optional[str]:
        """Get current account name."""
        return self._account_name

    @property
    def account_email(self) -> Optional[str]:
        """Get current account email."""
        return self._account_email

    def connect(self) -> bool:
        """
        Connect to Outlook.

        Returns:
            True if connected successfully
        """
        if not WIN32_AVAILABLE:
            app_logger.error("win32com not available. Install pywin32.")
            return False

        try:
            # Initialize COM for this thread
            pythoncom.CoInitialize()

            # Connect to Outlook
            self._outlook = win32com.client.Dispatch("Outlook.Application")
            self._namespace = self._outlook.GetNamespace("MAPI")

            # Get account info
            try:
                accounts = self._namespace.Accounts
                if accounts.Count > 0:
                    account = accounts.Item(1)
                    self._account_name = account.DisplayName
                    self._account_email = account.SmtpAddress
            except Exception:
                # Try alternative method
                try:
                    self._account_email = self._namespace.CurrentUser.Address
                    self._account_name = self._namespace.CurrentUser.Name
                except Exception:
                    pass

            self._connected = True
            app_logger.info(f"Connected to Outlook: {self._account_email or 'Unknown'}")
            return True

        except Exception as e:
            app_logger.error(f"Failed to connect to Outlook: {e}")
            self._connected = False
            return False

    def disconnect(self):
        """Disconnect from Outlook."""
        try:
            if WIN32_AVAILABLE:
                pythoncom.CoUninitialize()
        except Exception:
            pass

        self._outlook = None
        self._namespace = None
        self._connected = False

    def _get_folder(self, folder_type: FolderType = FolderType.INBOX):
        """Get a default folder."""
        if not self.is_connected:
            return None

        try:
            return self._namespace.GetDefaultFolder(folder_type.value)
        except Exception as e:
            app_logger.error(f"Failed to get folder {folder_type}: {e}")
            return None

    def _get_folder_by_path(self, path: str):
        """
        Get folder by path (e.g., "Inbox/Projects/2024").

        Args:
            path: Folder path separated by /
        """
        if not self.is_connected:
            return None

        try:
            parts = path.split('/')
            folder = self._namespace.GetDefaultFolder(FolderType.INBOX.value)

            # Navigate to parent first
            folder = folder.Parent

            # Navigate down the path
            for part in parts:
                folder = folder.Folders[part]

            return folder
        except Exception as e:
            app_logger.error(f"Failed to get folder by path '{path}': {e}")
            return None

    def get_folders(self, include_subfolders: bool = True) -> List[EmailFolder]:
        """
        Get all email folders.

        Args:
            include_subfolders: Include nested folders

        Returns:
            List of EmailFolder objects
        """
        if not self.is_connected:
            return []

        folders = []

        try:
            # Get root folders
            root = self._namespace.Folders

            for store in root:
                try:
                    self._collect_folders(store, folders, include_subfolders)
                except Exception:
                    continue

        except Exception as e:
            app_logger.error(f"Failed to get folders: {e}")

        return folders

    def _collect_folders(
        self,
        parent_folder,
        result: List[EmailFolder],
        include_subfolders: bool,
        depth: int = 0
    ):
        """Recursively collect folders."""
        if depth > 5:  # Limit depth
            return

        try:
            for folder in parent_folder.Folders:
                try:
                    # Determine folder type
                    folder_type = None
                    try:
                        default_item_type = folder.DefaultItemType
                        if default_item_type == 0:  # Mail items
                            folder_type = FolderType.INBOX
                    except Exception:
                        pass

                    email_folder = EmailFolder(
                        name=folder.Name,
                        folder_type=folder_type,
                        entry_id=folder.EntryID,
                        unread_count=getattr(folder, 'UnReadItemCount', 0),
                        total_count=getattr(folder, 'Items', []).Count if hasattr(folder, 'Items') else 0
                    )

                    result.append(email_folder)

                    if include_subfolders:
                        self._collect_folders(
                            folder, email_folder.subfolders,
                            include_subfolders, depth + 1
                        )

                except Exception:
                    continue

        except Exception:
            pass

    def get_default_folders(self) -> List[EmailFolder]:
        """Get main default folders (Inbox, Sent, Drafts, etc.)."""
        if not self.is_connected:
            return []

        folders = []
        default_types = [
            FolderType.INBOX,
            FolderType.SENT,
            FolderType.DRAFTS,
            FolderType.DELETED,
            FolderType.JUNK,
            FolderType.OUTBOX
        ]

        for folder_type in default_types:
            try:
                folder = self._namespace.GetDefaultFolder(folder_type.value)
                folders.append(EmailFolder(
                    name=folder.Name,
                    folder_type=folder_type,
                    entry_id=folder.EntryID,
                    unread_count=folder.UnReadItemCount,
                    total_count=folder.Items.Count
                ))
            except Exception:
                continue

        return folders

    def get_emails(
        self,
        folder_type: FolderType = FolderType.INBOX,
        limit: int = 50,
        unread_only: bool = False,
        since: Optional[datetime] = None,
        search_query: Optional[str] = None
    ) -> List[Email]:
        """
        Get emails from a folder.

        Args:
            folder_type: Folder to read from
            limit: Maximum emails to return
            unread_only: Only return unread emails
            since: Only return emails after this date
            search_query: Search in subject and body

        Returns:
            List of Email objects
        """
        if not self.is_connected:
            return []

        folder = self._get_folder(folder_type)
        if not folder:
            return []

        return self._get_emails_from_folder(
            folder, limit, unread_only, since, search_query
        )

    def get_emails_from_path(
        self,
        folder_path: str,
        limit: int = 50,
        **kwargs
    ) -> List[Email]:
        """Get emails from a folder by path."""
        if not self.is_connected:
            return []

        folder = self._get_folder_by_path(folder_path)
        if not folder:
            return []

        return self._get_emails_from_folder(folder, limit, **kwargs)

    def _get_emails_from_folder(
        self,
        folder,
        limit: int = 50,
        unread_only: bool = False,
        since: Optional[datetime] = None,
        search_query: Optional[str] = None
    ) -> List[Email]:
        """Get emails from a folder object."""
        emails = []

        try:
            items = folder.Items
            items.Sort("[ReceivedTime]", True)  # Sort by received time, descending

            # Apply filters
            if unread_only:
                items = items.Restrict("[UnRead] = True")

            if since:
                date_str = since.strftime("%m/%d/%Y %H:%M %p")
                items = items.Restrict(f"[ReceivedTime] >= '{date_str}'")

            if search_query:
                # Search in subject and body
                items = items.Restrict(
                    f"@SQL=\"urn:schemas:httpmail:subject\" LIKE '%{search_query}%' "
                    f"OR \"urn:schemas:httpmail:textdescription\" LIKE '%{search_query}%'"
                )

            count = 0
            for item in items:
                if count >= limit:
                    break

                try:
                    email = self._parse_mail_item(item, folder.Name)
                    if email:
                        emails.append(email)
                        count += 1
                except Exception as e:
                    app_logger.debug(f"Failed to parse email: {e}")
                    continue

        except Exception as e:
            app_logger.error(f"Failed to get emails: {e}")

        return emails

    def _parse_mail_item(self, item, folder_name: str) -> Optional[Email]:
        """Parse Outlook mail item to Email object."""
        try:
            # Check if it's a mail item
            if item.Class != 43:  # 43 = olMail
                return None

            # Get attachments
            attachments = []
            has_attachments = item.Attachments.Count > 0

            if has_attachments:
                for att in item.Attachments:
                    try:
                        attachments.append(EmailAttachment(
                            filename=att.FileName,
                            size=att.Size,
                        ))
                    except Exception:
                        continue

            # Get recipients
            to_list = []
            cc_list = []
            try:
                for recipient in item.Recipients:
                    if recipient.Type == 1:  # To
                        to_list.append(recipient.Address or recipient.Name)
                    elif recipient.Type == 2:  # CC
                        cc_list.append(recipient.Address or recipient.Name)
            except Exception:
                pass

            # Get categories
            categories = []
            try:
                if item.Categories:
                    categories = [c.strip() for c in item.Categories.split(',')]
            except Exception:
                pass

            return Email(
                entry_id=item.EntryID,
                conversation_id=getattr(item, 'ConversationID', None),
                subject=item.Subject or "(بدون موضوع)",
                body=item.Body or "",
                body_html=getattr(item, 'HTMLBody', None),
                sender_name=getattr(item, 'SenderName', ''),
                sender_email=getattr(item, 'SenderEmailAddress', ''),
                to=to_list,
                cc=cc_list,
                received_time=self._parse_datetime(item.ReceivedTime),
                sent_time=self._parse_datetime(getattr(item, 'SentOn', None)),
                created_time=self._parse_datetime(getattr(item, 'CreationTime', None)),
                is_read=not item.UnRead,
                is_flagged=item.FlagStatus == 2,  # 2 = olFlagMarked
                importance=EmailImportance(item.Importance),
                attachments=attachments,
                has_attachments=has_attachments,
                folder_name=folder_name,
                categories=categories
            )

        except Exception as e:
            app_logger.debug(f"Error parsing mail item: {e}")
            return None

    def _parse_datetime(self, pytime) -> Optional[datetime]:
        """Parse PyTime to datetime."""
        if pytime is None:
            return None
        try:
            return datetime(
                pytime.year, pytime.month, pytime.day,
                pytime.hour, pytime.minute, pytime.second
            )
        except Exception:
            return None

    def get_email_by_id(self, entry_id: str) -> Optional[Email]:
        """Get a single email by its EntryID."""
        if not self.is_connected:
            return None

        try:
            item = self._namespace.GetItemFromID(entry_id)
            return self._parse_mail_item(item, "")
        except Exception as e:
            app_logger.error(f"Failed to get email by ID: {e}")
            return None

    def mark_as_read(self, entry_id: str, read: bool = True) -> bool:
        """Mark an email as read/unread."""
        if not self.is_connected:
            return False

        try:
            item = self._namespace.GetItemFromID(entry_id)
            item.UnRead = not read
            item.Save()
            return True
        except Exception as e:
            app_logger.error(f"Failed to mark email: {e}")
            return False

    def mark_as_flagged(self, entry_id: str, flagged: bool = True) -> bool:
        """Mark an email as flagged/unflagged."""
        if not self.is_connected:
            return False

        try:
            item = self._namespace.GetItemFromID(entry_id)
            item.FlagStatus = 2 if flagged else 0  # 2 = flagged, 0 = not flagged
            item.Save()
            return True
        except Exception as e:
            app_logger.error(f"Failed to flag email: {e}")
            return False

    def delete_email(self, entry_id: str, permanent: bool = False) -> bool:
        """Delete an email (move to trash or permanent)."""
        if not self.is_connected:
            return False

        try:
            item = self._namespace.GetItemFromID(entry_id)
            if permanent:
                item.Delete()
            else:
                item.Move(self._namespace.GetDefaultFolder(FolderType.DELETED.value))
            return True
        except Exception as e:
            app_logger.error(f"Failed to delete email: {e}")
            return False

    def send_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        html_body: Optional[str] = None,
        importance: EmailImportance = EmailImportance.NORMAL
    ) -> bool:
        """
        Send an email.

        Args:
            to: List of recipient emails
            subject: Email subject
            body: Plain text body
            cc: CC recipients
            bcc: BCC recipients
            attachments: List of file paths to attach
            html_body: HTML body (optional)
            importance: Email importance level

        Returns:
            True if sent successfully
        """
        if not self.is_connected:
            return False

        try:
            mail = self._outlook.CreateItem(0)  # 0 = olMailItem

            # Set recipients
            mail.To = "; ".join(to)
            if cc:
                mail.CC = "; ".join(cc)
            if bcc:
                mail.BCC = "; ".join(bcc)

            # Set content
            mail.Subject = subject

            if html_body:
                mail.HTMLBody = html_body
            else:
                mail.Body = body

            # Set importance
            mail.Importance = importance.value

            # Add attachments
            if attachments:
                for file_path in attachments:
                    mail.Attachments.Add(file_path)

            # Send
            mail.Send()

            app_logger.info(f"Email sent to {to}")
            return True

        except Exception as e:
            app_logger.error(f"Failed to send email: {e}")
            return False

    def create_draft(
        self,
        to: List[str],
        subject: str,
        body: str,
        **kwargs
    ) -> Optional[str]:
        """Create a draft email. Returns EntryID of the draft."""
        if not self.is_connected:
            return None

        try:
            mail = self._outlook.CreateItem(0)
            mail.To = "; ".join(to)
            mail.Subject = subject
            mail.Body = body
            mail.Save()  # Save as draft

            return mail.EntryID

        except Exception as e:
            app_logger.error(f"Failed to create draft: {e}")
            return None

    def reply(self, entry_id: str, body: str, reply_all: bool = False) -> bool:
        """Reply to an email."""
        if not self.is_connected:
            return False

        try:
            item = self._namespace.GetItemFromID(entry_id)

            if reply_all:
                reply = item.ReplyAll()
            else:
                reply = item.Reply()

            reply.Body = body + reply.Body
            reply.Send()

            return True

        except Exception as e:
            app_logger.error(f"Failed to reply: {e}")
            return False

    def forward(self, entry_id: str, to: List[str], body: Optional[str] = None) -> bool:
        """Forward an email."""
        if not self.is_connected:
            return False

        try:
            item = self._namespace.GetItemFromID(entry_id)
            forward = item.Forward()
            forward.To = "; ".join(to)

            if body:
                forward.Body = body + forward.Body

            forward.Send()
            return True

        except Exception as e:
            app_logger.error(f"Failed to forward: {e}")
            return False


# Singleton instance
_connector: Optional[OutlookConnector] = None


def get_outlook() -> OutlookConnector:
    """Get the singleton Outlook connector."""
    global _connector
    if _connector is None:
        _connector = OutlookConnector()
    return _connector


def is_outlook_available() -> bool:
    """Check if Outlook is available and connected."""
    connector = get_outlook()
    if not connector.is_connected:
        connector.connect()
    return connector.is_connected


def get_inbox(limit: int = 50, **kwargs) -> List[Email]:
    """Quick function to get inbox emails."""
    connector = get_outlook()
    if not connector.is_connected:
        connector.connect()
    return connector.get_emails(FolderType.INBOX, limit, **kwargs)


def get_folders() -> List[EmailFolder]:
    """Quick function to get email folders."""
    connector = get_outlook()
    if not connector.is_connected:
        connector.connect()
    return connector.get_default_folders()


def get_emails(folder_type: FolderType = FolderType.INBOX, limit: int = 50, **kwargs) -> List[Email]:
    """Quick function to get emails from any folder."""
    connector = get_outlook()
    if not connector.is_connected:
        connector.connect()
    return connector.get_emails(folder_type, limit, **kwargs)


def send_email(to: List[str], subject: str, body: str, **kwargs) -> bool:
    """Quick function to send an email."""
    connector = get_outlook()
    if not connector.is_connected:
        connector.connect()
    return connector.send_email(to, subject, body, **kwargs)
