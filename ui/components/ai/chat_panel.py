"""
AI Chat Panel
=============
Chat interface for AI interaction in INTEGRA.
"""

from typing import Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QLineEdit, QPushButton, QScrollArea,
    QFrame, QSizePolicy, QApplication, QMenu
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSize
)
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon

from core.ai import get_ai_service, is_ollama_available
from core.logging import app_logger
from core.themes import get_current_theme

try:
    from core.utils import Icons, icon
    HAS_ICONS = True
except ImportError:
    HAS_ICONS = False
    Icons = None


class MessageRole(Enum):
    """Chat message roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ChatMessage:
    """Represents a chat message."""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


class StreamWorker(QThread):
    """Worker thread for streaming AI responses."""
    chunk_received = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        self.message = message
        self._stopped = False

    def run(self):
        """Run the streaming chat."""
        try:
            service = get_ai_service()
            for chunk in service.chat_stream(self.message):
                if self._stopped:
                    break
                self.chunk_received.emit(chunk)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        """Stop the streaming."""
        self._stopped = True


class MessageBubble(QFrame):
    """A single message bubble in the chat."""

    def __init__(
        self,
        message: ChatMessage,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.message = message
        self._setup_ui()

    def _setup_ui(self):
        """Setup the message bubble UI."""
        theme = get_current_theme()
        is_dark = theme == 'dark'

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # Time label
        time_str = self.message.timestamp.strftime("%H:%M")
        time_label = QLabel(time_str)
        time_color = "#64748b" if is_dark else "#888"
        time_label.setStyleSheet(f"color: {time_color}; font-size: 10px;")

        # Content label
        self.content_label = QLabel(self.message.content)
        self.content_label.setWordWrap(True)
        self.content_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )

        # Style based on role
        if self.message.role == MessageRole.USER:
            self.setStyleSheet("""
                MessageBubble {
                    background-color: #2563eb;
                    border-radius: 12px;
                    border-bottom-right-radius: 4px;
                }
            """)
            self.content_label.setStyleSheet("color: white; font-size: 13px;")
            time_label.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 10px;")
            layout.setAlignment(Qt.AlignRight)
        else:
            bg = "#334155" if is_dark else "#f0f0f0"
            text_color = "#f1f5f9" if is_dark else "#333"
            self.setStyleSheet(f"""
                MessageBubble {{
                    background-color: {bg};
                    border-radius: 12px;
                    border-bottom-left-radius: 4px;
                }}
            """)
            self.content_label.setStyleSheet(f"color: {text_color}; font-size: 13px;")

        layout.addWidget(self.content_label)
        layout.addWidget(time_label)

    def append_text(self, text: str):
        """Append text to the message (for streaming)."""
        current = self.content_label.text()
        self.content_label.setText(current + text)

    def set_text(self, text: str):
        """Set the message text."""
        self.content_label.setText(text)


class AIChatPanel(QWidget):
    """
    AI Chat Panel for INTEGRA.

    Features:
    - Streaming responses (character by character)
    - Conversation history
    - Quick action buttons
    - RTL support for Arabic

    Usage:
        chat = AIChatPanel(parent)
        chat.show()
    """

    message_sent = pyqtSignal(str)  # Emitted when user sends a message
    response_received = pyqtSignal(str)  # Emitted when AI responds

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._messages: List[ChatMessage] = []
        self._current_worker: Optional[StreamWorker] = None
        self._current_bubble: Optional[MessageBubble] = None
        self._setup_ui()
        self._check_availability()

    def _setup_ui(self):
        """Setup the chat panel UI."""
        self._is_dark = get_current_theme() == 'dark'

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = self._create_header()
        main_layout.addWidget(header)

        # Chat area (scrollable)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        chat_bg = "#0f172a" if self._is_dark else "white"
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {chat_bg};
            }}
        """)

        # Chat container
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(10, 10, 10, 10)
        self.chat_layout.setSpacing(10)
        self.chat_layout.addStretch()

        self.scroll_area.setWidget(self.chat_container)
        main_layout.addWidget(self.scroll_area, 1)

        # Input area
        input_area = self._create_input_area()
        main_layout.addWidget(input_area)

        # Status bar
        self.status_label = QLabel("")
        status_color = "#94a3b8" if self._is_dark else "#888"
        status_bg = "#1e293b" if self._is_dark else "transparent"
        self.status_label.setStyleSheet(f"color: {status_color}; font-size: 11px; padding: 4px; background-color: {status_bg};")
        main_layout.addWidget(self.status_label)

    def _create_header(self) -> QWidget:
        """Create the header widget."""
        header = QFrame()
        hdr_bg = "#1e293b" if self._is_dark else "#f8f8f8"
        hdr_border = "#334155" if self._is_dark else "#ddd"
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {hdr_bg};
                border-bottom: 1px solid {hdr_border};
            }}
        """)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(10, 8, 10, 8)

        # AI Icon
        icon_label = QLabel("🤖")
        icon_label.setStyleSheet("font-size: 20px;")

        # Title
        title_color = "#f1f5f9" if self._is_dark else "#333"
        title = QLabel("المساعد الذكي")
        title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {title_color};")

        # Model info
        model_color = "#94a3b8" if self._is_dark else "#888"
        self.model_label = QLabel("")
        self.model_label.setStyleSheet(f"font-size: 11px; color: {model_color};")

        # Clear button
        btn_bg = "#334155" if self._is_dark else "none"
        btn_border = "#475569" if self._is_dark else "#ddd"
        btn_color = "#f1f5f9" if self._is_dark else "#666"
        btn_hover = "#475569" if self._is_dark else "#f0f0f0"
        clear_btn = QPushButton("مسح")
        clear_btn.setFixedWidth(60)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: {btn_bg};
                border: 1px solid {btn_border};
                border-radius: 4px;
                padding: 4px 8px;
                color: {btn_color};
            }}
            QPushButton:hover {{
                background-color: {btn_hover};
            }}
        """)
        clear_btn.clicked.connect(self.clear_chat)

        layout.addWidget(icon_label)
        layout.addWidget(title)
        layout.addWidget(self.model_label)
        layout.addStretch()
        layout.addWidget(clear_btn)

        return header

    def _create_input_area(self) -> QWidget:
        """Create the input area widget."""
        input_frame = QFrame()
        frame_bg = "#1e293b" if self._is_dark else "#f8f8f8"
        frame_border = "#334155" if self._is_dark else "#ddd"
        input_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {frame_bg};
                border-top: 1px solid {frame_border};
            }}
        """)

        layout = QVBoxLayout(input_frame)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        # Quick actions
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(6)

        quick_actions = [
            ("لخّص البيانات", "لخّص بيانات الموظفين الحالية"),
            ("تحليل الرواتب", "حلل توزيع الرواتب واكتشف أي شذوذ"),
            ("اقتراحات", "اقترح تحسينات لإدارة الموظفين"),
        ]

        qa_bg = "#334155" if self._is_dark else "#e8e8e8"
        qa_color = "#f1f5f9" if self._is_dark else "#444"
        qa_hover = "#475569" if self._is_dark else "#d8d8d8"
        for text, prompt in quick_actions:
            btn = QPushButton(text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {qa_bg};
                    border: none;
                    border-radius: 12px;
                    padding: 6px 12px;
                    font-size: 11px;
                    color: {qa_color};
                }}
                QPushButton:hover {{
                    background-color: {qa_hover};
                }}
            """)
            btn.clicked.connect(lambda checked, p=prompt: self.send_message(p))
            actions_layout.addWidget(btn)

        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        # Input row
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        input_bg = "#0f172a" if self._is_dark else "white"
        input_border = "#475569" if self._is_dark else "#ddd"
        input_color = "#f1f5f9" if self._is_dark else "#333"
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("اكتب رسالتك هنا...")
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {input_border};
                border-radius: 20px;
                padding: 10px 16px;
                font-size: 13px;
                background-color: {input_bg};
                color: {input_color};
            }}
            QLineEdit:focus {{
                border-color: #2563eb;
            }}
        """)
        self.input_field.returnPressed.connect(self._on_send_clicked)

        disabled_bg = "#475569" if self._is_dark else "#ccc"
        self.send_btn = QPushButton("إرسال")
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #3b82f6;
            }}
            QPushButton:disabled {{
                background-color: {disabled_bg};
            }}
        """)
        self.send_btn.clicked.connect(self._on_send_clicked)

        input_layout.addWidget(self.input_field, 1)
        input_layout.addWidget(self.send_btn)

        layout.addLayout(input_layout)

        return input_frame

    def _check_availability(self):
        """Check if AI service is available."""
        if is_ollama_available():
            service = get_ai_service()
            model = service.model or "غير محدد"
            self.model_label.setText(f"({model})")
            self._set_status("جاهز للمحادثة")
        else:
            self.model_label.setText("(غير متصل)")
            self._set_status("خدمة Ollama غير متاحة", error=True)
            self.input_field.setEnabled(False)
            self.send_btn.setEnabled(False)

    def _set_status(self, text: str, error: bool = False):
        """Set status text."""
        if error:
            color = "#ef4444"
        else:
            color = "#94a3b8" if self._is_dark else "#888"
        bg = "#1e293b" if self._is_dark else "transparent"
        self.status_label.setStyleSheet(f"color: {color}; font-size: 11px; padding: 4px; background-color: {bg};")
        self.status_label.setText(text)

    def _scroll_to_bottom(self):
        """Scroll chat to bottom."""
        QTimer.singleShot(50, lambda: (
            self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().maximum()
            )
        ))

    def _add_message(self, role: MessageRole, content: str) -> MessageBubble:
        """Add a message to the chat."""
        message = ChatMessage(role=role, content=content)
        self._messages.append(message)

        bubble = MessageBubble(message)

        # Insert before stretch
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)

        # Align based on role
        if role == MessageRole.USER:
            self.chat_layout.setAlignment(bubble, Qt.AlignRight)
        else:
            self.chat_layout.setAlignment(bubble, Qt.AlignLeft)

        self._scroll_to_bottom()
        return bubble

    def _on_send_clicked(self):
        """Handle send button click."""
        text = self.input_field.text().strip()
        if not text:
            return

        self.input_field.clear()
        self.send_message(text)

    def send_message(self, text: str):
        """Send a message to the AI."""
        if not is_ollama_available():
            self._set_status("خدمة Ollama غير متاحة", error=True)
            return

        # Add user message
        self._add_message(MessageRole.USER, text)
        self.message_sent.emit(text)

        # Disable input while processing
        self.input_field.setEnabled(False)
        self.send_btn.setEnabled(False)
        self._set_status("جاري الرد...")

        # Create assistant bubble for streaming
        self._current_bubble = self._add_message(MessageRole.ASSISTANT, "")

        # Start streaming worker
        self._current_worker = StreamWorker(text)
        self._current_worker.chunk_received.connect(self._on_chunk)
        self._current_worker.finished.connect(self._on_stream_finished)
        self._current_worker.error.connect(self._on_stream_error)
        self._current_worker.start()

    def _on_chunk(self, chunk: str):
        """Handle received chunk."""
        if self._current_bubble:
            self._current_bubble.append_text(chunk)
            self._scroll_to_bottom()

    def _on_stream_finished(self):
        """Handle stream completion."""
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.input_field.setFocus()
        self._set_status("جاهز")

        if self._current_bubble:
            self.response_received.emit(self._current_bubble.content_label.text())

        self._current_worker = None
        self._current_bubble = None

    def _on_stream_error(self, error: str):
        """Handle stream error."""
        self._set_status(f"خطأ: {error}", error=True)
        app_logger.error(f"AI Chat error: {error}")

        if self._current_bubble:
            self._current_bubble.set_text("حدث خطأ أثناء الرد. الرجاء المحاولة مرة أخرى.")

        # إعادة تمكين حقل الإدخال (لأن finished لا يُرسل عند الخطأ)
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.input_field.setFocus()
        self._current_worker = None
        self._current_bubble = None

    def clear_chat(self):
        """Clear all messages."""
        # Remove all bubbles
        while self.chat_layout.count() > 1:  # Keep the stretch
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._messages.clear()

        # Clear AI service context
        try:
            service = get_ai_service()
            service.clear_context()
        except Exception:
            pass

        self._set_status("تم مسح المحادثة")

    def stop_streaming(self):
        """Stop current streaming response."""
        if self._current_worker:
            self._current_worker.stop()


def create_chat_panel(parent: Optional[QWidget] = None) -> AIChatPanel:
    """Create and return a chat panel."""
    return AIChatPanel(parent)
