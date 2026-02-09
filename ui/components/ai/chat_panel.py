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
from PyQt5.QtGui import QColor, QPalette, QIcon

from core.ai import get_ai_service, is_ollama_available
from core.logging import app_logger
from core.themes import get_current_palette

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
        palette = get_current_palette()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # Time label
        time_str = self.message.timestamp.strftime("%H:%M")
        time_label = QLabel(time_str)
        time_label.setStyleSheet(f"color: {palette['text_muted']}; font-size: 10px;")

        # Content label
        self.content_label = QLabel(self.message.content)
        self.content_label.setWordWrap(True)
        self.content_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )

        # Style based on role
        if self.message.role == MessageRole.USER:
            self.setStyleSheet(f"""
                MessageBubble {{
                    background-color: {palette['primary']};
                    border-radius: 12px;
                    border-bottom-right-radius: 4px;
                }}
            """)
            self.content_label.setStyleSheet(f"color: {palette['text_on_primary']}; font-size: 13px;")
            time_label.setStyleSheet(f"color: rgba(255,255,255,0.7); font-size: 10px;")
            layout.setAlignment(Qt.AlignRight)
        else:
            self.setStyleSheet(f"""
                MessageBubble {{
                    background-color: {palette['bg_card']};
                    border-radius: 12px;
                    border-bottom-left-radius: 4px;
                }}
            """)
            self.content_label.setStyleSheet(f"color: {palette['text_primary']}; font-size: 13px;")

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
        self._palette = get_current_palette()

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
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {self._palette['bg_main']};
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
        self.status_label.setStyleSheet(
            f"color: {self._palette['text_secondary']}; font-size: 11px;"
            f" padding: 4px; background-color: {self._palette['bg_card']};"
        )
        main_layout.addWidget(self.status_label)

    def _create_header(self) -> QWidget:
        """Create the header widget."""
        p = self._palette
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {p['bg_card']};
                border-bottom: 1px solid {p['border']};
            }}
        """)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(10, 8, 10, 8)

        # AI Icon
        icon_label = QLabel("🤖")
        icon_label.setStyleSheet("font-size: 20px;")

        # Title
        title = QLabel("المساعد الذكي")
        title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {p['text_primary']};")

        # Model info
        self.model_label = QLabel("")
        self.model_label.setStyleSheet(f"font-size: 11px; color: {p['text_secondary']};")

        # Clear button
        clear_btn = QPushButton("مسح")
        clear_btn.setFixedWidth(60)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: {p['bg_hover']};
                border: 1px solid {p['border_light']};
                border-radius: 4px;
                padding: 4px 8px;
                color: {p['text_primary']};
            }}
            QPushButton:hover {{
                background-color: {p['bg_tooltip']};
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
        p = self._palette
        input_frame = QFrame()
        input_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {p['bg_card']};
                border-top: 1px solid {p['border']};
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

        for text, prompt in quick_actions:
            btn = QPushButton(text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {p['bg_hover']};
                    border: none;
                    border-radius: 12px;
                    padding: 6px 12px;
                    font-size: 11px;
                    color: {p['text_primary']};
                }}
                QPushButton:hover {{
                    background-color: {p['bg_tooltip']};
                }}
            """)
            btn.clicked.connect(lambda checked, pr=prompt: self.send_message(pr))
            actions_layout.addWidget(btn)

        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        # Input row
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("اكتب رسالتك هنا...")
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {p['border_light']};
                border-radius: 20px;
                padding: 10px 16px;
                font-size: 13px;
                background-color: {p['bg_main']};
                color: {p['text_primary']};
            }}
            QLineEdit:focus {{
                border-color: {p['primary']};
            }}
        """)
        self.input_field.returnPressed.connect(self._on_send_clicked)

        self.send_btn = QPushButton("إرسال")
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {p['primary']};
                color: {p['text_on_primary']};
                border: none;
                border-radius: 20px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {p['primary_hover']};
            }}
            QPushButton:disabled {{
                background-color: {p['disabled_bg']};
                color: {p['disabled_text']};
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
        p = self._palette
        if error:
            color = p['danger']
        else:
            color = p['text_secondary']
        self.status_label.setStyleSheet(
            f"color: {color}; font-size: 11px; padding: 4px;"
            f" background-color: {p['bg_card']};"
        )
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
