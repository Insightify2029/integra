"""
Email Viewer Widget
===================
Displays email content with full details.
"""

import html
from typing import Optional, List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QScrollArea, QTextBrowser,
    QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from core.email import Email, EmailImportance
from core.logging import app_logger
from core.themes import get_current_theme


class EmailViewerWidget(QWidget):
    """
    Widget for displaying email content.

    Signals:
        reply_clicked: Emitted when reply is clicked
        reply_all_clicked: Emitted when reply all is clicked
        forward_clicked: Emitted when forward is clicked
        delete_clicked: Emitted when delete is clicked
        ai_analyze_clicked: Emitted when AI analyze is clicked
    """

    reply_clicked = pyqtSignal(Email)
    reply_all_clicked = pyqtSignal(Email)
    forward_clicked = pyqtSignal(Email)
    delete_clicked = pyqtSignal(Email)
    ai_analyze_clicked = pyqtSignal(Email)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._email: Optional[Email] = None
        self._is_dark = get_current_theme() == 'dark'
        self._setup_ui()

    def _setup_ui(self):
        """Setup the viewer UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Empty state
        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_color = "#64748b" if self._is_dark else "#999"
        empty_label = QLabel("📧\n\nاختر رسالة لعرضها")
        empty_label.setAlignment(Qt.AlignCenter)
        empty_label.setStyleSheet(f"color: {empty_color}; font-size: 16px;")
        empty_layout.addStretch()
        empty_layout.addWidget(empty_label)
        empty_layout.addStretch()

        # Email content widget
        self.content_widget = QWidget()
        self._setup_content_widget()
        self.content_widget.hide()

        layout.addWidget(self.empty_widget)
        layout.addWidget(self.content_widget)

    def _setup_content_widget(self):
        """Setup the content widget."""
        layout = QVBoxLayout(self.content_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # AI Summary panel (hidden by default)
        self.ai_panel = self._create_ai_panel()
        self.ai_panel.hide()
        layout.addWidget(self.ai_panel)

        # Body scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_bg = "#0f172a" if self._is_dark else "white"
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {scroll_bg}; }}")

        body_widget = QWidget()
        body_layout = QVBoxLayout(body_widget)
        body_layout.setContentsMargins(16, 16, 16, 16)

        self.body_browser = QTextBrowser()
        self.body_browser.setOpenExternalLinks(True)
        self.body_browser.setStyleSheet("""
            QTextBrowser {
                border: none;
                font-size: 13px;
                line-height: 1.5;
            }
        """)

        body_layout.addWidget(self.body_browser)
        scroll.setWidget(body_widget)
        layout.addWidget(scroll, 1)

        # Attachments panel
        self.attachments_panel = self._create_attachments_panel()
        self.attachments_panel.hide()
        layout.addWidget(self.attachments_panel)

    def _create_header(self) -> QWidget:
        """Create email header."""
        header = QFrame()
        hdr_bg = "#1e293b" if self._is_dark else "white"
        hdr_border = "#334155" if self._is_dark else "#e8e8e8"
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {hdr_bg};
                border-bottom: 1px solid {hdr_border};
            }}
        """)

        layout = QVBoxLayout(header)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Subject row
        subject_row = QHBoxLayout()

        self.importance_label = QLabel()
        self.importance_label.setStyleSheet("font-size: 16px;")

        subj_color = "#f1f5f9" if self._is_dark else "#333"
        self.subject_label = QLabel()
        self.subject_label.setWordWrap(True)
        self.subject_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {subj_color};")

        subject_row.addWidget(self.importance_label)
        subject_row.addWidget(self.subject_label, 1)

        # Sender row
        sender_row = QHBoxLayout()
        sender_row.setSpacing(8)

        # Avatar placeholder
        av_bg = "#334155" if self._is_dark else "#e8e8e8"
        avatar = QLabel("👤")
        avatar.setFixedSize(40, 40)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(f"""
            background-color: {av_bg};
            border-radius: 20px;
            font-size: 20px;
        """)

        # Sender info
        sender_info = QVBoxLayout()
        sender_info.setSpacing(2)

        sn_color = "#f1f5f9" if self._is_dark else "#333"
        se_color = "#94a3b8" if self._is_dark else "#666"
        self.sender_name_label = QLabel()
        self.sender_name_label.setStyleSheet(f"font-weight: bold; font-size: 13px; color: {sn_color};")

        self.sender_email_label = QLabel()
        self.sender_email_label.setStyleSheet(f"font-size: 11px; color: {se_color};")

        sender_info.addWidget(self.sender_name_label)
        sender_info.addWidget(self.sender_email_label)

        # Date
        date_color = "#64748b" if self._is_dark else "#888"
        self.date_label = QLabel()
        self.date_label.setStyleSheet(f"font-size: 11px; color: {date_color};")

        sender_row.addWidget(avatar)
        sender_row.addLayout(sender_info, 1)
        sender_row.addWidget(self.date_label)

        # Recipients row
        rec_color = "#94a3b8" if self._is_dark else "#666"
        self.recipients_label = QLabel()
        self.recipients_label.setStyleSheet(f"font-size: 11px; color: {rec_color};")
        self.recipients_label.setWordWrap(True)

        layout.addLayout(subject_row)
        layout.addLayout(sender_row)
        layout.addWidget(self.recipients_label)

        return header

    def _create_toolbar(self) -> QWidget:
        """Create action toolbar."""
        toolbar = QFrame()
        tb_bg = "#0f172a" if self._is_dark else "#f8f8f8"
        tb_border = "#334155" if self._is_dark else "#e8e8e8"
        toolbar.setStyleSheet(f"background-color: {tb_bg}; border-bottom: 1px solid {tb_border};")

        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        # Action buttons
        btn_border = "#475569" if self._is_dark else "#ddd"
        btn_color = "#f1f5f9" if self._is_dark else "#333"
        btn_hover = "#334155" if self._is_dark else "#e8e8e8"
        btn_style = f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {btn_border};
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
                color: {btn_color};
            }}
            QPushButton:hover {{
                background-color: {btn_hover};
            }}
        """

        reply_btn = QPushButton("↩️ رد")
        reply_btn.setStyleSheet(btn_style)
        reply_btn.clicked.connect(lambda: self.reply_clicked.emit(self._email) if self._email else None)

        reply_all_btn = QPushButton("↩️↩️ رد للكل")
        reply_all_btn.setStyleSheet(btn_style)
        reply_all_btn.clicked.connect(lambda: self.reply_all_clicked.emit(self._email) if self._email else None)

        forward_btn = QPushButton("➡️ إعادة توجيه")
        forward_btn.setStyleSheet(btn_style)
        forward_btn.clicked.connect(lambda: self.forward_clicked.emit(self._email) if self._email else None)

        # AI button
        ai_bg = "#1e3a5f" if self._is_dark else "#e8f4ff"
        ai_border = "#3b82f6" if self._is_dark else "#0078d4"
        ai_color = "#93c5fd" if self._is_dark else "#0078d4"
        ai_hover = "#1e4070" if self._is_dark else "#d0e8ff"
        ai_btn = QPushButton("🤖 تحليل AI")
        ai_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ai_bg};
                border: 1px solid {ai_border};
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
                color: {ai_color};
            }}
            QPushButton:hover {{
                background-color: {ai_hover};
            }}
        """)
        ai_btn.clicked.connect(lambda: self.ai_analyze_clicked.emit(self._email) if self._email else None)

        # Delete button
        delete_btn = QPushButton("🗑️")
        delete_btn.setToolTip("حذف")
        delete_btn.setFixedWidth(40)
        delete_btn.setStyleSheet(btn_style)
        delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self._email) if self._email else None)

        layout.addWidget(reply_btn)
        layout.addWidget(reply_all_btn)
        layout.addWidget(forward_btn)
        layout.addStretch()
        layout.addWidget(ai_btn)
        layout.addWidget(delete_btn)

        return toolbar

    def _create_ai_panel(self) -> QWidget:
        """Create AI analysis panel."""
        panel = QFrame()
        ai_panel_bg = "#0f2744" if self._is_dark else "#f0f7ff"
        ai_panel_border = "#1e3a5f" if self._is_dark else "#c5d5ff"
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {ai_panel_bg};
                border-bottom: 1px solid {ai_panel_border};
            }}
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Header
        header_row = QHBoxLayout()
        ai_hdr_color = "#93c5fd" if self._is_dark else "#0052a3"
        header_label = QLabel("🤖 تحليل الذكاء الاصطناعي")
        header_label.setStyleSheet(f"font-weight: bold; color: {ai_hdr_color}; font-size: 12px;")

        close_color = "#94a3b8" if self._is_dark else "#666"
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet(f"border: none; color: {close_color};")
        close_btn.clicked.connect(lambda: self.ai_panel.hide())

        header_row.addWidget(header_label)
        header_row.addStretch()
        header_row.addWidget(close_btn)

        # Summary
        ai_text = "#f1f5f9" if self._is_dark else "#333"
        ai_meta_color = "#94a3b8" if self._is_dark else "#666"
        self.ai_summary_label = QLabel()
        self.ai_summary_label.setWordWrap(True)
        self.ai_summary_label.setStyleSheet(f"font-size: 12px; color: {ai_text};")

        # Category & Priority
        self.ai_meta_label = QLabel()
        self.ai_meta_label.setStyleSheet(f"font-size: 11px; color: {ai_meta_color};")

        # Tasks
        self.ai_tasks_label = QLabel()
        self.ai_tasks_label.setWordWrap(True)
        self.ai_tasks_label.setStyleSheet(f"font-size: 11px; color: {ai_text};")

        layout.addLayout(header_row)
        layout.addWidget(self.ai_summary_label)
        layout.addWidget(self.ai_meta_label)
        layout.addWidget(self.ai_tasks_label)

        return panel

    def _create_attachments_panel(self) -> QWidget:
        """Create attachments panel."""
        panel = QFrame()
        att_bg = "#1e293b" if self._is_dark else "#f8f8f8"
        att_border = "#334155" if self._is_dark else "#e8e8e8"
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {att_bg};
                border-top: 1px solid {att_border};
            }}
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        att_hdr_color = "#f1f5f9" if self._is_dark else "#333"
        header_label = QLabel("📎 المرفقات")
        header_label.setStyleSheet(f"font-weight: bold; font-size: 12px; color: {att_hdr_color};")

        self.attachments_layout = QHBoxLayout()
        self.attachments_layout.setSpacing(8)

        layout.addWidget(header_label)
        layout.addLayout(self.attachments_layout)

        return panel

    def set_email(self, email: Optional[Email]):
        """Set the email to display."""
        self._email = email

        if email is None:
            self.empty_widget.show()
            self.content_widget.hide()
            return

        self.empty_widget.hide()
        self.content_widget.show()

        # Update header
        self.subject_label.setText(email.subject)

        if email.importance == EmailImportance.HIGH:
            self.importance_label.setText("❗")
            self.importance_label.show()
        else:
            self.importance_label.hide()

        self.sender_name_label.setText(email.sender_name or email.sender_email)
        self.sender_email_label.setText(f"<{email.sender_email}>" if email.sender_name else "")

        # Date
        if email.received_time:
            self.date_label.setText(email.received_time.strftime("%Y/%m/%d %H:%M"))
        else:
            self.date_label.setText("")

        # Recipients
        recipients = []
        if email.to:
            recipients.append(f"إلى: {', '.join(email.to[:3])}")
            if len(email.to) > 3:
                recipients[-1] += f" و{len(email.to) - 3} آخرين"
        if email.cc:
            recipients.append(f"نسخة: {', '.join(email.cc[:2])}")
        self.recipients_label.setText(" | ".join(recipients))

        # Body
        if email.body_html:
            self.body_browser.setHtml(email.body_html)
        else:
            # Convert plain text to HTML with proper formatting
            # Escape HTML entities to prevent injection from plain text emails
            text = html.escape(email.body).replace('\n', '<br>')
            self.body_browser.setHtml(f"<div style='white-space: pre-wrap;'>{text}</div>")

        # AI Panel
        if email.ai_summary or email.ai_category:
            self._show_ai_analysis(email)
        else:
            self.ai_panel.hide()

        # Attachments
        self._show_attachments(email)

    def _show_ai_analysis(self, email: Email):
        """Show AI analysis panel."""
        if email.ai_summary:
            self.ai_summary_label.setText(f"📝 {email.ai_summary}")
            self.ai_summary_label.show()
        else:
            self.ai_summary_label.hide()

        meta = []
        if email.ai_category:
            meta.append(f"📁 التصنيف: {email.ai_category}")
        if email.ai_priority:
            meta.append(f"⚡ الأولوية: {email.ai_priority}")
        self.ai_meta_label.setText(" | ".join(meta))
        self.ai_meta_label.setVisible(bool(meta))

        if email.ai_tasks:
            tasks_text = "📋 المهام:\n" + "\n".join(f"  • {t}" for t in email.ai_tasks)
            self.ai_tasks_label.setText(tasks_text)
            self.ai_tasks_label.show()
        else:
            self.ai_tasks_label.hide()

        self.ai_panel.show()

    def _show_attachments(self, email: Email):
        """Show attachments panel."""
        # Clear existing
        while self.attachments_layout.count():
            item = self.attachments_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not email.attachments:
            self.attachments_panel.hide()
            return

        for att in email.attachments:
            att_btn = QPushButton(f"📄 {att.filename}\n({att.size_display})")
            att_btn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 8px 12px;
                    text-align: left;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #f0f0f0;
                }
            """)
            self.attachments_layout.addWidget(att_btn)

        self.attachments_layout.addStretch()
        self.attachments_panel.show()

    def show_ai_result(self, summary: str, category: str = None, priority: str = None, tasks: List[str] = None):
        """Show AI analysis result."""
        if self._email:
            self._email.ai_summary = summary
            self._email.ai_category = category
            self._email.ai_priority = priority
            self._email.ai_tasks = tasks or []
            self._show_ai_analysis(self._email)

    def clear(self):
        """Clear the viewer."""
        self.set_email(None)


def create_email_viewer(parent: Optional[QWidget] = None) -> EmailViewerWidget:
    """Create and return an email viewer widget."""
    return EmailViewerWidget(parent)
