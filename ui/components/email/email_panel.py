"""
Email Panel
===========
Main email panel combining list and viewer.
"""

from typing import Optional, List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QFrame, QLabel, QPushButton, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread

from .email_list import EmailListWidget
from .email_viewer import EmailViewerWidget
from core.email import (
    Email, EmailFolder, FolderType,
    get_outlook, is_outlook_available, get_emails,
    get_email_cache, cache_emails
)
from core.logging import app_logger

# Try to import AI
try:
    from core.ai import is_ollama_available, get_ai_service
    from core.ai.prompts import EMAIL_ASSISTANT_PROMPT
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False


class EmailLoadWorker(QThread):
    """Worker thread for loading emails."""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, folder_type: FolderType, limit: int = 50, parent=None):
        super().__init__(parent)
        self.folder_type = folder_type
        self.limit = limit

    def run(self):
        """Load emails in background."""
        try:
            # Import COM libraries
            import pythoncom
            import win32com.client

            # Initialize COM for this thread
            pythoncom.CoInitialize()

            try:
                # Create new Outlook connection in this thread
                outlook = win32com.client.Dispatch("Outlook.Application")
                namespace = outlook.GetNamespace("MAPI")

                # Get folder
                folder = namespace.GetDefaultFolder(self.folder_type.value)
                folder_name = folder.Name
                app_logger.info(f"Loading emails from folder: {folder_name}")

                # Get items
                items = folder.Items
                total_items = items.Count
                app_logger.info(f"Folder has {total_items} total items")

                if total_items == 0:
                    self.finished.emit([])
                    return

                # Sort by received time (newest first)
                items.Sort("[ReceivedTime]", True)

                emails = []
                count = 0
                skipped = 0

                # Use index-based iteration (1-based index in COM)
                max_check = min(total_items, self.limit * 2)
                for i in range(1, max_check + 1):
                    if count >= self.limit:
                        break

                    try:
                        item = items.Item(i)

                        # Only process mail items (Class 43 = olMail)
                        if item.Class != 43:
                            skipped += 1
                            continue

                        # Parse email
                        email = self._parse_item(item, folder_name)
                        if email:
                            emails.append(email)
                            count += 1
                    except Exception as e:
                        app_logger.debug(f"Error processing item {i}: {e}")
                        continue

                app_logger.info(f"Loaded {len(emails)} emails, skipped {skipped} non-mail items")

                # Cache emails
                cache_emails(emails)
                self.finished.emit(emails)

            finally:
                pythoncom.CoUninitialize()

        except Exception as e:
            app_logger.error(f"Email load error: {e}")
            self.error.emit(str(e))

    def _parse_item(self, item, folder_name: str) -> Email:
        """Parse Outlook item to Email object."""
        from core.email import Email, EmailImportance, EmailAttachment

        # Get attachments info
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
                if recipient.Type == 1:
                    to_list.append(recipient.Address or recipient.Name)
                elif recipient.Type == 2:
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

        # Parse datetime
        def parse_dt(pytime):
            if pytime is None:
                return None
            try:
                from datetime import datetime
                return datetime(
                    pytime.year, pytime.month, pytime.day,
                    pytime.hour, pytime.minute, pytime.second
                )
            except Exception:
                return None

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
            received_time=parse_dt(item.ReceivedTime),
            sent_time=parse_dt(getattr(item, 'SentOn', None)),
            created_time=parse_dt(getattr(item, 'CreationTime', None)),
            is_read=not item.UnRead,
            is_flagged=item.FlagStatus == 2,
            importance=EmailImportance(item.Importance),
            attachments=attachments,
            has_attachments=has_attachments,
            folder_name=folder_name,
            categories=categories
        )


class AIAnalyzeWorker(QThread):
    """Worker thread for AI analysis."""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, email: Email, parent=None):
        super().__init__(parent)
        self.email = email

    def run(self):
        """Analyze email with AI."""
        try:
            if not AI_AVAILABLE or not is_ollama_available():
                self.error.emit("AI غير متاح")
                return

            service = get_ai_service()
            service.use_prompt("email")

            prompt = f"""حلل الإيميل التالي وقدم:
1. ملخص مختصر (جملة أو جملتين)
2. التصنيف (عمل/شخصي/إعلان/اجتماعات/مهام/أخرى)
3. الأولوية (عاجل/مهم/عادي)
4. أي مهام أو إجراءات مطلوبة

الموضوع: {self.email.subject}
المرسل: {self.email.sender_name} <{self.email.sender_email}>
المحتوى:
{self.email.body[:2000]}

قدم الإجابة بالتنسيق التالي:
الملخص: ...
التصنيف: ...
الأولوية: ...
المهام: (إن وجدت)
- ...
- ...
"""

            response = service.chat(prompt, keep_context=False, temperature=0.3)

            if response:
                result = self._parse_response(response)
                self.finished.emit(result)
            else:
                self.error.emit("لم يتم الحصول على رد")

        except Exception as e:
            self.error.emit(str(e))

    def _parse_response(self, response: str) -> dict:
        """Parse AI response."""
        result = {
            'summary': '',
            'category': '',
            'priority': '',
            'tasks': []
        }

        lines = response.split('\n')
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith('الملخص:'):
                result['summary'] = line.replace('الملخص:', '').strip()
                current_section = 'summary'
            elif line.startswith('التصنيف:'):
                result['category'] = line.replace('التصنيف:', '').strip()
                current_section = 'category'
            elif line.startswith('الأولوية:'):
                result['priority'] = line.replace('الأولوية:', '').strip()
                current_section = 'priority'
            elif line.startswith('المهام:'):
                current_section = 'tasks'
            elif current_section == 'tasks' and line.startswith('-'):
                result['tasks'].append(line[1:].strip())

        return result


class EmailPanel(QWidget):
    """
    Main email panel.

    Features:
    - Folder selection
    - Email list with search
    - Email viewer
    - AI integration

    Usage:
        panel = EmailPanel(parent)
        panel.load_emails()
    """

    email_opened = pyqtSignal(Email)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._current_folder = FolderType.INBOX
        self._current_email: Optional[Email] = None
        self._load_worker: Optional[EmailLoadWorker] = None
        self._ai_worker: Optional[AIAnalyzeWorker] = None
        self._setup_ui()

    def _setup_ui(self):
        """Setup the panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top bar
        topbar = self._create_topbar()
        layout.addWidget(topbar)

        # Splitter for list and viewer
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #e8e8e8;
                width: 1px;
            }
        """)

        # Email list
        self.email_list = EmailListWidget()
        self.email_list.setMinimumWidth(300)
        self.email_list.setMaximumWidth(450)
        self.email_list.email_selected.connect(self._on_email_selected)
        self.email_list.email_double_clicked.connect(self._on_email_double_clicked)
        self.email_list.refresh_requested.connect(self.load_emails)

        # Email viewer
        self.email_viewer = EmailViewerWidget()
        self.email_viewer.ai_analyze_clicked.connect(self._on_ai_analyze)
        self.email_viewer.reply_clicked.connect(self._on_reply)
        self.email_viewer.forward_clicked.connect(self._on_forward)
        self.email_viewer.delete_clicked.connect(self._on_delete)

        splitter.addWidget(self.email_list)
        splitter.addWidget(self.email_viewer)
        splitter.setSizes([350, 650])

        layout.addWidget(splitter, 1)

        # Status bar
        self.status_bar = self._create_status_bar()
        layout.addWidget(self.status_bar)

    def _create_topbar(self) -> QWidget:
        """Create top bar with folder selection."""
        topbar = QFrame()
        topbar.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border-bottom: 1px solid #ddd;
            }
        """)

        layout = QHBoxLayout(topbar)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Outlook status
        self.outlook_status = QLabel()
        self._update_outlook_status()

        # Folder selector
        folder_label = QLabel("المجلد:")
        folder_label.setStyleSheet("font-size: 12px;")

        self.folder_combo = QComboBox()
        self.folder_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 150px;
            }
        """)
        self.folder_combo.addItem("📥 الوارد", FolderType.INBOX)
        self.folder_combo.addItem("📤 المرسل", FolderType.SENT)
        self.folder_combo.addItem("📝 المسودات", FolderType.DRAFTS)
        self.folder_combo.addItem("🗑️ المحذوف", FolderType.DELETED)
        self.folder_combo.currentIndexChanged.connect(self._on_folder_changed)

        # Compose button
        compose_btn = QPushButton("✉️ رسالة جديدة")
        compose_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        compose_btn.clicked.connect(self._on_compose)

        layout.addWidget(self.outlook_status)
        layout.addWidget(folder_label)
        layout.addWidget(self.folder_combo)
        layout.addStretch()
        layout.addWidget(compose_btn)

        return topbar

    def _create_status_bar(self) -> QWidget:
        """Create status bar."""
        status = QFrame()
        status.setStyleSheet("background-color: #f8f8f8; border-top: 1px solid #ddd;")

        layout = QHBoxLayout(status)
        layout.setContentsMargins(12, 6, 12, 6)

        self.status_label = QLabel("جاهز")
        self.status_label.setStyleSheet("font-size: 11px; color: #666;")

        # AI status
        self.ai_status = QLabel()
        self._update_ai_status()

        layout.addWidget(self.status_label)
        layout.addStretch()
        layout.addWidget(self.ai_status)

        return status

    def _update_outlook_status(self):
        """Update Outlook connection status."""
        if is_outlook_available():
            outlook = get_outlook()
            email = outlook.account_email or "متصل"
            self.outlook_status.setText(f"✅ Outlook: {email}")
            self.outlook_status.setStyleSheet("color: #22c55e; font-size: 11px;")
        else:
            self.outlook_status.setText("❌ Outlook غير متصل")
            self.outlook_status.setStyleSheet("color: #ef4444; font-size: 11px;")

    def _update_ai_status(self):
        """Update AI status."""
        if AI_AVAILABLE and is_ollama_available():
            self.ai_status.setText("🤖 AI متاح")
            self.ai_status.setStyleSheet("color: #22c55e; font-size: 11px;")
        else:
            self.ai_status.setText("🤖 AI غير متاح")
            self.ai_status.setStyleSheet("color: #888; font-size: 11px;")

    def _on_folder_changed(self, index: int):
        """Handle folder change."""
        folder_type = self.folder_combo.currentData()
        if folder_type:
            self._current_folder = folder_type
            self.load_emails()

    def load_emails(self, limit: int = 50):
        """Load emails from current folder."""
        if not is_outlook_available():
            self.status_label.setText("❌ Outlook غير متصل")
            return

        self.status_label.setText("⏳ جاري تحميل الرسائل...")

        # Stop any existing worker
        if self._load_worker and self._load_worker.isRunning():
            self._load_worker.terminate()

        self._load_worker = EmailLoadWorker(self._current_folder, limit)
        self._load_worker.finished.connect(self._on_emails_loaded)
        self._load_worker.error.connect(self._on_load_error)
        self._load_worker.start()

    def _on_emails_loaded(self, emails: List[Email]):
        """Handle loaded emails."""
        self.email_list.set_emails(emails)
        self.email_viewer.clear()
        self.status_label.setText(f"✅ تم تحميل {len(emails)} رسالة")

    def _on_load_error(self, error: str):
        """Handle load error."""
        self.status_label.setText(f"❌ خطأ: {error}")
        app_logger.error(f"Email load error: {error}")

    def _on_email_selected(self, email: Email):
        """Handle email selection."""
        self._current_email = email
        self.email_viewer.set_email(email)

        # Mark as read
        if not email.is_read:
            try:
                outlook = get_outlook()
                outlook.mark_as_read(email.entry_id)
                self.email_list.mark_email_as_read(email.entry_id)
            except Exception as e:
                app_logger.error(f"Failed to mark as read: {e}")

    def _on_email_double_clicked(self, email: Email):
        """Handle email double-click."""
        self.email_opened.emit(email)

    def _on_ai_analyze(self, email: Email):
        """Handle AI analyze request."""
        if not AI_AVAILABLE or not is_ollama_available():
            self.status_label.setText("❌ AI غير متاح")
            return

        self.status_label.setText("🤖 جاري التحليل...")

        if self._ai_worker and self._ai_worker.isRunning():
            self._ai_worker.terminate()

        self._ai_worker = AIAnalyzeWorker(email)
        self._ai_worker.finished.connect(self._on_ai_finished)
        self._ai_worker.error.connect(self._on_ai_error)
        self._ai_worker.start()

    def _on_ai_finished(self, result: dict):
        """Handle AI analysis result."""
        self.email_viewer.show_ai_result(
            summary=result.get('summary', ''),
            category=result.get('category', ''),
            priority=result.get('priority', ''),
            tasks=result.get('tasks', [])
        )

        # Update cache
        if self._current_email:
            cache = get_email_cache()
            cache.update_ai_analysis(
                self._current_email.entry_id,
                summary=result.get('summary'),
                category=result.get('category'),
                priority=result.get('priority'),
                tasks=result.get('tasks')
            )

        self.status_label.setText("✅ تم التحليل بنجاح")

    def _on_ai_error(self, error: str):
        """Handle AI error."""
        self.status_label.setText(f"❌ خطأ AI: {error}")

    def _on_compose(self):
        """Handle compose new email."""
        # TODO: Implement compose dialog
        self.status_label.setText("📝 ميزة الإنشاء قيد التطوير")

    def _on_reply(self, email: Email):
        """Handle reply."""
        # TODO: Implement reply dialog
        self.status_label.setText("↩️ ميزة الرد قيد التطوير")

    def _on_forward(self, email: Email):
        """Handle forward."""
        # TODO: Implement forward dialog
        self.status_label.setText("➡️ ميزة التوجيه قيد التطوير")

    def _on_delete(self, email: Email):
        """Handle delete."""
        try:
            outlook = get_outlook()
            if outlook.delete_email(email.entry_id):
                self.status_label.setText("🗑️ تم حذف الرسالة")
                self.load_emails()
        except Exception as e:
            self.status_label.setText(f"❌ فشل الحذف: {e}")

    def refresh(self):
        """Refresh the panel."""
        self._update_outlook_status()
        self._update_ai_status()
        self.load_emails()


def create_email_panel(parent: Optional[QWidget] = None) -> EmailPanel:
    """Create and return an email panel."""
    return EmailPanel(parent)
