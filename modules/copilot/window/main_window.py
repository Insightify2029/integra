"""
Copilot Main Window
===================
Main window for the AI Copilot module.
"""

from typing import Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QLabel, QPushButton, QFrame,
    QStackedWidget, QListWidget, QListWidgetItem, QTextEdit
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

from core.logging import app_logger

from ..components.chat_sidebar import CopilotSidebar
from ..components.action_preview import ActionPreview
from ..components.suggestion_panel import SuggestionPanel


class CopilotMainWindow(QMainWindow):
    """
    Main window for AI Copilot module.

    Features:
    - Full chat interface
    - Action preview panel
    - History browser
    - Settings
    """

    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("المساعد الذكي - INTEGRA")
        self.setMinimumSize(900, 600)
        self.resize(1100, 700)

        self._setup_ui()
        self._connect_signals()
        self._initialize_systems()

    def _setup_ui(self):
        """Setup the window UI."""
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left sidebar - navigation
        nav_panel = self._create_nav_panel()
        main_layout.addWidget(nav_panel)

        # Main content area
        content_splitter = QSplitter(Qt.Horizontal)

        # Chat panel (main)
        self.chat_panel = CopilotSidebar()
        self.chat_panel.setMinimumWidth(400)
        self.chat_panel.setMaximumWidth(16777215)  # Remove max width limit
        content_splitter.addWidget(self.chat_panel)

        # Right panel - tabs for actions, history, etc.
        right_panel = self._create_right_panel()
        content_splitter.addWidget(right_panel)

        content_splitter.setSizes([600, 400])
        main_layout.addWidget(content_splitter, 1)

        # Apply style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f9fafb;
            }
        """)

    def _create_nav_panel(self) -> QWidget:
        """Create the navigation panel."""
        panel = QFrame()
        panel.setFixedWidth(60)
        panel.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8b5cf6, stop:1 #6366f1);
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(8)

        # Logo
        logo = QLabel("🤖")
        logo.setStyleSheet("font-size: 28px;")
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

        layout.addSpacing(20)

        # Navigation buttons
        nav_buttons = [
            ("💬", "محادثة", 0),
            ("⚡", "إجراءات", 1),
            ("📜", "السجل", 2),
            ("⚙️", "الإعدادات", 3),
        ]

        self.nav_btn_group = []
        for icon, tooltip, index in nav_buttons:
            btn = QPushButton(icon)
            btn.setFixedSize(44, 44)
            btn.setToolTip(tooltip)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    border-radius: 8px;
                    font-size: 20px;
                }
                QPushButton:hover {
                    background-color: rgba(255,255,255,0.2);
                }
                QPushButton:checked {
                    background-color: rgba(255,255,255,0.3);
                }
            """)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, i=index: self._on_nav_clicked(i))
            self.nav_btn_group.append(btn)
            layout.addWidget(btn, alignment=Qt.AlignCenter)

        layout.addStretch()

        # Help button
        help_btn = QPushButton("❓")
        help_btn.setFixedSize(44, 44)
        help_btn.setToolTip("مساعدة")
        help_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 8px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.2);
            }
        """)
        help_btn.clicked.connect(self._show_help)
        layout.addWidget(help_btn, alignment=Qt.AlignCenter)

        # Set first button as active
        if self.nav_btn_group:
            self.nav_btn_group[0].setChecked(True)

        return panel

    def _create_right_panel(self) -> QWidget:
        """Create the right panel with tabs."""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border-left: 1px solid #e5e7eb;
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tab widget
        self.right_tabs = QTabWidget()
        self.right_tabs.setTabPosition(QTabWidget.North)
        self.right_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: white;
            }
            QTabBar::tab {
                padding: 10px 16px;
                background-color: #f3f4f6;
                border: none;
                border-bottom: 2px solid transparent;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #8b5cf6;
            }
            QTabBar::tab:hover {
                background-color: #e5e7eb;
            }
        """)

        # Actions tab
        self.action_preview = ActionPreview()
        self.action_preview.action_approved.connect(self._on_action_approved)
        self.action_preview.action_rejected.connect(self._on_action_rejected)
        self.right_tabs.addTab(self.action_preview, "⚡ إجراءات")

        # Suggestions tab
        self.suggestions = SuggestionPanel()
        self.right_tabs.addTab(self.suggestions, "💡 اقتراحات")

        # History tab
        history_widget = self._create_history_widget()
        self.right_tabs.addTab(history_widget, "📜 السجل")

        layout.addWidget(self.right_tabs)

        return panel

    def _create_history_widget(self) -> QWidget:
        """Create the history browser widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("سجل المحادثات")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1f2937;")

        clear_btn = QPushButton("مسح الكل")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #fee2e2;
                color: #dc2626;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #fecaca;
            }
        """)
        clear_btn.clicked.connect(self._clear_history)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(clear_btn)
        layout.addLayout(header)

        # Session list
        self.history_list = QListWidget()
        self.history_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                background-color: #f9fafb;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #e5e7eb;
            }
            QListWidget::item:selected {
                background-color: #ede9fe;
            }
            QListWidget::item:hover {
                background-color: #f3f4f6;
            }
        """)
        self.history_list.itemClicked.connect(self._on_history_item_clicked)
        layout.addWidget(self.history_list, 1)

        # Session preview
        preview_label = QLabel("معاينة:")
        preview_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #374151;")
        layout.addWidget(preview_label)

        self.history_preview = QTextEdit()
        self.history_preview.setReadOnly(True)
        self.history_preview.setMaximumHeight(150)
        self.history_preview.setStyleSheet("""
            QTextEdit {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                background-color: white;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.history_preview)

        return widget

    def _connect_signals(self):
        """Connect signals."""
        self.chat_panel.action_requested.connect(self._on_action_requested)

    def _initialize_systems(self):
        """Initialize copilot systems."""
        try:
            # Initialize knowledge engine
            from ..knowledge import get_knowledge_engine
            ke = get_knowledge_engine()
            ke.initialize()

            # Initialize context manager
            from ..context import get_context_manager
            cm = get_context_manager()
            cm.initialize()

            # Initialize learning system
            from ..learning import get_learning_system
            ls = get_learning_system()
            ls.initialize()

            # Initialize history manager
            from ..history import get_history_manager
            hm = get_history_manager()
            hm.initialize()
            hm.start_session(title="جلسة جديدة")

            # Load history
            self._load_history()

            app_logger.info("Copilot systems initialized")

        except Exception as e:
            app_logger.error(f"Error initializing copilot systems: {e}")

    def _on_nav_clicked(self, index: int):
        """Handle navigation button click."""
        # Update button states
        for i, btn in enumerate(self.nav_btn_group):
            btn.setChecked(i == index)

        # Switch content (for future expansion)
        if index == 1:  # Actions
            self.right_tabs.setCurrentIndex(0)
        elif index == 2:  # History
            self.right_tabs.setCurrentIndex(2)

    def _on_action_requested(self, action: dict):
        """Handle action request from chat."""
        from ..components.action_preview import PreviewAction

        preview_action = PreviewAction(
            id=action.get("id", ""),
            type=action.get("type", "custom"),
            title=action.get("title", "إجراء"),
            description=action.get("description", ""),
            target=action.get("target", ""),
            changes=action.get("changes", {})
        )
        self.action_preview.add_action(preview_action)
        self.right_tabs.setCurrentIndex(0)

    def _on_action_approved(self, action):
        """Handle action approval."""
        from ..sandbox import get_action_sandbox
        sandbox = get_action_sandbox()
        sandbox.approve_action(action.id)
        sandbox.execute_action(action.id)

    def _on_action_rejected(self, action):
        """Handle action rejection."""
        from ..sandbox import get_action_sandbox
        sandbox = get_action_sandbox()
        sandbox.reject_action(action.id, "Rejected by user")

    def _load_history(self):
        """Load history sessions."""
        self.history_list.clear()

        try:
            from ..history import get_history_manager
            hm = get_history_manager()
            sessions = hm.get_recent_sessions(limit=20)

            for session in sessions:
                item = QListWidgetItem()
                item.setText(f"{session.title}\n{session.summary}")
                item.setData(Qt.UserRole, session.id)
                self.history_list.addItem(item)

        except Exception as e:
            app_logger.error(f"Error loading history: {e}")

    def _on_history_item_clicked(self, item: QListWidgetItem):
        """Handle history item click."""
        session_id = item.data(Qt.UserRole)

        try:
            from ..history import get_history_manager
            hm = get_history_manager()
            session = hm.get_session(session_id)

            if session:
                self.history_preview.setText(session.get_conversation_text())

        except Exception as e:
            app_logger.error(f"Error loading session: {e}")

    def _clear_history(self):
        """Clear history."""
        from ..history import get_history_manager
        hm = get_history_manager()
        hm.clear()
        self.history_list.clear()
        self.history_preview.clear()

    def _show_help(self):
        """Show help."""
        self.chat_panel.send_message("كيف أستخدم المساعد الذكي؟")

    def closeEvent(self, event):
        """Handle window close."""
        # End current session
        try:
            from ..history import get_history_manager
            hm = get_history_manager()
            hm.end_session()
        except Exception:
            pass

        self.closed.emit()
        super().closeEvent(event)
