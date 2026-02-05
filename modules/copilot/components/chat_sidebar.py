"""
Copilot Sidebar
===============
Main chat sidebar for AI Copilot.
"""

from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QLineEdit, QPushButton, QScrollArea,
    QFrame, QSizePolicy, QApplication, QMenu, QAction,
    QToolButton, QStackedWidget, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSize, QPropertyAnimation,
    QEasingCurve, pyqtProperty
)
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QTextCursor

from core.logging import app_logger


class MessageType(Enum):
    """Types of chat messages."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ACTION = "action"
    ERROR = "error"


@dataclass
class CopilotMessage:
    """A copilot chat message."""
    type: MessageType
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    actions: List[Dict[str, Any]] = field(default_factory=list)


class CopilotWorker(QThread):
    """Worker thread for AI responses."""
    chunk_received = pyqtSignal(str)
    action_suggested = pyqtSignal(dict)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, message: str, context: str = "", parent=None):
        super().__init__(parent)
        self.message = message
        self.context = context
        self._stopped = False

    def run(self):
        """Process the message with AI."""
        try:
            from core.ai import get_ai_service, is_ollama_available

            if not is_ollama_available():
                self.error.emit("خدمة AI غير متاحة")
                return

            service = get_ai_service()

            # Build prompt with context
            full_prompt = self._build_prompt()

            # Get streaming response
            full_response = []
            for chunk in service.chat_stream(full_prompt):
                if self._stopped:
                    break
                full_response.append(chunk)
                self.chunk_received.emit(chunk)

            response_text = "".join(full_response)

            # Check for suggested actions
            actions = self._extract_actions(response_text)
            for action in actions:
                self.action_suggested.emit(action)

            self.finished.emit(response_text)

        except Exception as e:
            self.error.emit(str(e))

    def _build_prompt(self) -> str:
        """Build the full prompt with context."""
        prompt_parts = []

        # Add system context
        prompt_parts.append("أنت مساعد ذكي لنظام INTEGRA. ساعد المستخدم بالعربية.")

        # Add application context
        if self.context:
            prompt_parts.append(f"\n{self.context}")

        # Add user message
        prompt_parts.append(f"\nسؤال المستخدم: {self.message}")

        return "\n".join(prompt_parts)

    def _extract_actions(self, response: str) -> List[Dict[str, Any]]:
        """Extract suggested actions from response."""
        actions = []

        # Simple action detection patterns
        action_patterns = [
            ("إضافة", "create"),
            ("تعديل", "edit"),
            ("حذف", "delete"),
            ("عرض", "view"),
            ("تصدير", "export"),
            ("طباعة", "print"),
        ]

        response_lower = response.lower()
        for ar_word, action_type in action_patterns:
            if ar_word in response_lower:
                actions.append({
                    "type": action_type,
                    "detected_from": ar_word,
                    "requires_approval": action_type in ["create", "edit", "delete"]
                })

        return actions

    def stop(self):
        """Stop the worker."""
        self._stopped = True


class MessageBubble(QFrame):
    """A chat message bubble."""

    action_clicked = pyqtSignal(dict)

    def __init__(self, message: CopilotMessage, parent=None):
        super().__init__(parent)
        self.message = message
        self._setup_ui()

    def _setup_ui(self):
        """Setup the bubble UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Style based on message type
        if self.message.type == MessageType.USER:
            self.setStyleSheet("""
                MessageBubble {
                    background-color: #8b5cf6;
                    border-radius: 16px;
                    border-bottom-right-radius: 4px;
                }
            """)
            text_color = "white"
            time_color = "rgba(255,255,255,0.7)"
        elif self.message.type == MessageType.ERROR:
            self.setStyleSheet("""
                MessageBubble {
                    background-color: #fee2e2;
                    border-radius: 16px;
                    border: 1px solid #fca5a5;
                }
            """)
            text_color = "#dc2626"
            time_color = "#f87171"
        elif self.message.type == MessageType.ACTION:
            self.setStyleSheet("""
                MessageBubble {
                    background-color: #fef3c7;
                    border-radius: 16px;
                    border: 1px solid #fcd34d;
                }
            """)
            text_color = "#92400e"
            time_color = "#b45309"
        else:
            self.setStyleSheet("""
                MessageBubble {
                    background-color: #f3f4f6;
                    border-radius: 16px;
                    border-bottom-left-radius: 4px;
                }
            """)
            text_color = "#1f2937"
            time_color = "#6b7280"

        # Content label
        self.content_label = QLabel(self.message.content)
        self.content_label.setWordWrap(True)
        self.content_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )
        self.content_label.setStyleSheet(f"color: {text_color}; font-size: 13px;")
        layout.addWidget(self.content_label)

        # Actions (if any)
        if self.message.actions:
            actions_layout = QHBoxLayout()
            actions_layout.setSpacing(8)

            for action in self.message.actions:
                btn = QPushButton(self._get_action_label(action))
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #8b5cf6;
                        color: white;
                        border: none;
                        border-radius: 12px;
                        padding: 6px 12px;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background-color: #7c3aed;
                    }
                """)
                btn.clicked.connect(lambda checked, a=action: self.action_clicked.emit(a))
                actions_layout.addWidget(btn)

            actions_layout.addStretch()
            layout.addLayout(actions_layout)

        # Time label
        time_str = self.message.timestamp.strftime("%H:%M")
        time_label = QLabel(time_str)
        time_label.setStyleSheet(f"color: {time_color}; font-size: 10px;")
        time_label.setAlignment(Qt.AlignRight if self.message.type == MessageType.USER else Qt.AlignLeft)
        layout.addWidget(time_label)

    def _get_action_label(self, action: Dict[str, Any]) -> str:
        """Get display label for an action."""
        labels = {
            "create": "إنشاء",
            "edit": "تعديل",
            "delete": "حذف",
            "view": "عرض",
            "export": "تصدير",
            "print": "طباعة"
        }
        return labels.get(action.get("type", ""), "تنفيذ")

    def append_text(self, text: str):
        """Append text to the message."""
        current = self.content_label.text()
        self.content_label.setText(current + text)

    def set_text(self, text: str):
        """Set the message text."""
        self.content_label.setText(text)


class CopilotSidebar(QWidget):
    """
    AI Copilot Sidebar.

    Features:
    - Streaming AI responses
    - Context-aware assistance
    - Quick actions
    - Action suggestions with approval
    - Search history

    Usage:
        sidebar = CopilotSidebar(parent)
        sidebar.show()
    """

    # Signals
    message_sent = pyqtSignal(str)
    response_received = pyqtSignal(str)
    action_requested = pyqtSignal(dict)
    toggle_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._messages: List[CopilotMessage] = []
        self._current_worker: Optional[CopilotWorker] = None
        self._current_bubble: Optional[MessageBubble] = None
        self._collapsed = False

        self.setObjectName("CopilotSidebar")
        self.setMinimumWidth(320)
        self.setMaximumWidth(450)

        self._setup_ui()
        self._connect_signals()
        self._add_welcome_message()

    def _setup_ui(self):
        """Setup the sidebar UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = self._create_header()
        main_layout.addWidget(header)

        # Chat area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: white;
            }
        """)

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(12, 12, 12, 12)
        self.chat_layout.setSpacing(12)
        self.chat_layout.addStretch()

        self.scroll_area.setWidget(self.chat_container)
        main_layout.addWidget(self.scroll_area, 1)

        # Quick actions
        quick_actions = self._create_quick_actions()
        main_layout.addWidget(quick_actions)

        # Input area
        input_area = self._create_input_area()
        main_layout.addWidget(input_area)

        # Status bar
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #6b7280;
                font-size: 11px;
                padding: 6px 12px;
                background-color: #f9fafb;
                border-top: 1px solid #e5e7eb;
            }
        """)
        main_layout.addWidget(self.status_label)

        # Apply main style
        self.setStyleSheet("""
            CopilotSidebar {
                background-color: white;
                border-left: 1px solid #e5e7eb;
            }
        """)

    def _create_header(self) -> QWidget:
        """Create the header widget."""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8b5cf6, stop:1 #6366f1);
                border-bottom: none;
            }
        """)
        header.setFixedHeight(56)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 0, 12, 0)

        # Icon and title
        icon_label = QLabel("🤖")
        icon_label.setStyleSheet("font-size: 24px;")

        title_layout = QVBoxLayout()
        title_layout.setSpacing(0)

        title = QLabel("المساعد الذكي")
        title.setStyleSheet("color: white; font-size: 15px; font-weight: bold;")

        self.status_text = QLabel("جاهز للمساعدة")
        self.status_text.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 11px;")

        title_layout.addWidget(title)
        title_layout.addWidget(self.status_text)

        # Actions
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(4)

        # Clear button
        clear_btn = QToolButton()
        clear_btn.setText("🗑️")
        clear_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: none;
                font-size: 16px;
                padding: 4px;
            }
            QToolButton:hover {
                background-color: rgba(255,255,255,0.2);
                border-radius: 4px;
            }
        """)
        clear_btn.clicked.connect(self.clear_chat)

        # Menu button
        menu_btn = QToolButton()
        menu_btn.setText("⋮")
        menu_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: none;
                font-size: 18px;
                padding: 4px;
                color: white;
            }
            QToolButton:hover {
                background-color: rgba(255,255,255,0.2);
                border-radius: 4px;
            }
        """)
        menu_btn.clicked.connect(self._show_menu)

        # Collapse button
        self.collapse_btn = QToolButton()
        self.collapse_btn.setText("◀")
        self.collapse_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: none;
                font-size: 14px;
                padding: 4px;
                color: white;
            }
            QToolButton:hover {
                background-color: rgba(255,255,255,0.2);
                border-radius: 4px;
            }
        """)
        self.collapse_btn.clicked.connect(self._toggle_collapse)

        actions_layout.addWidget(clear_btn)
        actions_layout.addWidget(menu_btn)
        actions_layout.addWidget(self.collapse_btn)

        layout.addWidget(icon_label)
        layout.addSpacing(8)
        layout.addLayout(title_layout)
        layout.addStretch()
        layout.addLayout(actions_layout)

        return header

    def _create_quick_actions(self) -> QWidget:
        """Create quick actions widget."""
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #f9fafb;
                border-top: 1px solid #e5e7eb;
            }
        """)

        layout = QHBoxLayout(container)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        actions = [
            ("📊 تحليل", "حلل البيانات الحالية"),
            ("📝 تقرير", "أنشئ تقرير"),
            ("❓ مساعدة", "كيف أستخدم هذه الشاشة؟"),
        ]

        for text, prompt in actions:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border: 1px solid #e5e7eb;
                    border-radius: 16px;
                    padding: 6px 12px;
                    font-size: 12px;
                    color: #374151;
                }
                QPushButton:hover {
                    background-color: #f3f4f6;
                    border-color: #8b5cf6;
                }
            """)
            btn.clicked.connect(lambda checked, p=prompt: self.send_message(p))
            layout.addWidget(btn)

        layout.addStretch()
        return container

    def _create_input_area(self) -> QWidget:
        """Create the input area widget."""
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-top: 1px solid #e5e7eb;
            }
        """)

        layout = QHBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Input field
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("اكتب سؤالك هنا...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                border: 1px solid #e5e7eb;
                border-radius: 20px;
                padding: 10px 16px;
                font-size: 13px;
                background-color: #f9fafb;
            }
            QLineEdit:focus {
                border-color: #8b5cf6;
                background-color: white;
            }
        """)
        self.input_field.returnPressed.connect(self._on_send_clicked)

        # Send button
        self.send_btn = QPushButton("➤")
        self.send_btn.setFixedSize(40, 40)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #8b5cf6;
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #7c3aed;
            }
            QPushButton:disabled {
                background-color: #d1d5db;
            }
        """)
        self.send_btn.clicked.connect(self._on_send_clicked)

        layout.addWidget(self.input_field, 1)
        layout.addWidget(self.send_btn)

        return container

    def _connect_signals(self):
        """Connect internal signals."""
        pass

    def _add_welcome_message(self):
        """Add the welcome message."""
        welcome = CopilotMessage(
            type=MessageType.ASSISTANT,
            content="مرحباً! أنا مساعدك الذكي في INTEGRA. كيف يمكنني مساعدتك اليوم؟\n\nيمكنني:\n• الإجابة على أسئلتك\n• تحليل البيانات\n• تنفيذ المهام\n• تقديم اقتراحات"
        )
        self._add_message_bubble(welcome)

    def _add_message_bubble(self, message: CopilotMessage) -> MessageBubble:
        """Add a message bubble to the chat."""
        self._messages.append(message)

        bubble = MessageBubble(message)
        bubble.action_clicked.connect(self._on_action_clicked)

        # Insert before stretch
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)

        # Align based on type
        if message.type == MessageType.USER:
            self.chat_layout.setAlignment(bubble, Qt.AlignRight)
        else:
            self.chat_layout.setAlignment(bubble, Qt.AlignLeft)

        self._scroll_to_bottom()
        return bubble

    def _scroll_to_bottom(self):
        """Scroll to bottom of chat."""
        QTimer.singleShot(50, lambda: (
            self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().maximum()
            )
        ))

    def _set_status(self, text: str, is_error: bool = False):
        """Set status text."""
        color = "#dc2626" if is_error else "#6b7280"
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 11px;
                padding: 6px 12px;
                background-color: #f9fafb;
                border-top: 1px solid #e5e7eb;
            }}
        """)
        self.status_label.setText(text)
        self.status_text.setText(text if not is_error else "خطأ")

    def _on_send_clicked(self):
        """Handle send button click."""
        text = self.input_field.text().strip()
        if not text:
            return

        self.input_field.clear()
        self.send_message(text)

    def send_message(self, text: str):
        """Send a message to the AI."""
        # Add user message
        user_msg = CopilotMessage(type=MessageType.USER, content=text)
        self._add_message_bubble(user_msg)
        self.message_sent.emit(text)

        # Disable input
        self.input_field.setEnabled(False)
        self.send_btn.setEnabled(False)
        self._set_status("جاري التفكير...")

        # Get context
        context = self._get_context()

        # Create assistant bubble
        assistant_msg = CopilotMessage(type=MessageType.ASSISTANT, content="")
        self._current_bubble = self._add_message_bubble(assistant_msg)

        # Start worker
        self._current_worker = CopilotWorker(text, context)
        self._current_worker.chunk_received.connect(self._on_chunk)
        self._current_worker.action_suggested.connect(self._on_action_suggested)
        self._current_worker.finished.connect(self._on_response_finished)
        self._current_worker.error.connect(self._on_error)
        self._current_worker.start()

    def _get_context(self) -> str:
        """Get current application context."""
        context_parts = []

        try:
            # Get context from context manager
            from ..context import get_context_manager
            cm = get_context_manager()
            if cm.is_ready():
                context_parts.append(cm.get_prompt_context())
        except Exception:
            pass

        try:
            # Get knowledge context
            from ..knowledge import get_knowledge_engine
            ke = get_knowledge_engine()
            if ke.is_ready():
                # Get recent user message
                if self._messages:
                    last_user_msg = next(
                        (m for m in reversed(self._messages) if m.type == MessageType.USER),
                        None
                    )
                    if last_user_msg:
                        knowledge_context = ke.get_context_for_prompt(
                            last_user_msg.content,
                            max_items=2,
                            max_length=1000
                        )
                        if knowledge_context:
                            context_parts.append(knowledge_context)
        except Exception:
            pass

        return "\n\n".join(context_parts)

    def _on_chunk(self, chunk: str):
        """Handle received chunk."""
        if self._current_bubble:
            self._current_bubble.append_text(chunk)
            self._scroll_to_bottom()

    def _on_action_suggested(self, action: Dict[str, Any]):
        """Handle suggested action."""
        if action.get("requires_approval"):
            self.action_requested.emit(action)

    def _on_response_finished(self, response: str):
        """Handle response completion."""
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.input_field.setFocus()
        self._set_status("جاهز")

        self.response_received.emit(response)
        self._current_worker = None
        self._current_bubble = None

    def _on_error(self, error: str):
        """Handle error."""
        self._set_status(f"خطأ: {error}", is_error=True)

        if self._current_bubble:
            self._current_bubble.set_text("عذراً، حدث خطأ. الرجاء المحاولة مرة أخرى.")

        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)

    def _on_action_clicked(self, action: Dict[str, Any]):
        """Handle action button click."""
        self.action_requested.emit(action)

    def _show_menu(self):
        """Show options menu."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #f3f4f6;
            }
        """)

        history_action = menu.addAction("📜 سجل المحادثات")
        history_action.triggered.connect(self._show_history)

        settings_action = menu.addAction("⚙️ الإعدادات")
        settings_action.triggered.connect(self._show_settings)

        menu.addSeparator()

        help_action = menu.addAction("❓ المساعدة")
        help_action.triggered.connect(lambda: self.send_message("كيف أستخدم المساعد الذكي؟"))

        menu.exec_(self.mapToGlobal(self.sender().pos()))

    def _toggle_collapse(self):
        """Toggle sidebar collapse."""
        self._collapsed = not self._collapsed
        self.toggle_requested.emit()

        if self._collapsed:
            self.collapse_btn.setText("▶")
        else:
            self.collapse_btn.setText("◀")

    def _show_history(self):
        """Show conversation history."""
        # TODO: Implement history view
        pass

    def _show_settings(self):
        """Show settings dialog."""
        # TODO: Implement settings
        pass

    def clear_chat(self):
        """Clear the chat."""
        # Remove all bubbles except stretch
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._messages.clear()

        # Clear AI context
        try:
            from core.ai import get_ai_service
            service = get_ai_service()
            service.clear_context()
        except Exception:
            pass

        self._set_status("تم مسح المحادثة")

        # Re-add welcome
        QTimer.singleShot(100, self._add_welcome_message)

    def stop_generation(self):
        """Stop current generation."""
        if self._current_worker:
            self._current_worker.stop()
