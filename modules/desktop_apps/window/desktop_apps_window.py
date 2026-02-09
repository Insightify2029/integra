"""
Desktop Apps Window
===================
Main window for the Desktop Apps Integration module.

Tabbed interface with:
- WhatsApp tab (send messages, templates, contacts)
- Telegram tab (bot config, alerts, commands)
- Teams tab (channels, webhooks, cards)
- Automation tab (workflows, window management, apps)
"""

import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QGroupBox, QGridLayout,
    QPushButton, QTabWidget, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QProgressBar, QSpinBox, QCheckBox,
    QTextEdit, QSplitter, QMessageBox, QLineEdit,
    QFormLayout, QListWidget, QListWidgetItem,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal

from ui.windows.base import BaseWindow
from core.logging import app_logger
from core.themes import get_current_palette

class DesktopAppsWindow(BaseWindow):
    """
    Desktop Apps Integration main window.

    Tabbed interface with:
    - WhatsApp: Messages, templates, contacts
    - Telegram: Bot, alerts, commands
    - Teams: Channels, webhooks, cards
    - Automation: Workflows, windows, apps
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(
            "تكامل تطبيقات سطح المكتب - INTEGRA"
        )
        self.setMinimumSize(1100, 750)

        self._whatsapp_manager = None
        self._telegram_manager = None
        self._teams_connector = None
        self._automation_engine = None

        self._setup_ui()
        self._setup_connections()

        app_logger.info("Desktop Apps window opened")

    # ─── Styles ────────────────────────────────────

    def _build_styles(self):
        """Build palette-based styles."""
        p = get_current_palette()
        self._p = p

        self._section_style = f"""
            QGroupBox {{
                font-size: 16px;
                font-weight: bold;
                color: {p['accent']};
                border: 2px solid {p['accent']}40;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 20px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
            }}
        """

        self._btn_style = f"""
            QPushButton {{
                padding: 8px 16px;
                background-color: {p['primary']};
                color: {p['text_on_primary']};
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {p['primary_hover']};
            }}
            QPushButton:disabled {{
                background-color: {p['disabled_bg']};
                color: {p['disabled_text']};
            }}
        """

        self._btn_secondary_style = f"""
            QPushButton {{
                padding: 8px 16px;
                background-color: {p['bg_input']};
                color: {p['text_primary']};
                border: 1px solid {p['border']};
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {p['bg_hover']};
            }}
            QPushButton:disabled {{
                background-color: {p['bg_main']};
                color: {p['disabled_text']};
            }}
        """

        self._btn_success_style = f"""
            QPushButton {{
                padding: 8px 16px;
                background-color: {p['success']};
                color: {p['text_on_primary']};
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {p['success']};
                opacity: 0.9;
            }}
        """

        self._btn_danger_style = f"""
            QPushButton {{
                padding: 8px 16px;
                background-color: {p['danger']};
                color: {p['text_on_primary']};
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {p['danger']};
                opacity: 0.9;
            }}
        """

        self._input_style = f"""
            QLineEdit, QTextEdit, QComboBox, QSpinBox {{
                padding: 8px;
                border: 1px solid {p['border']};
                border-radius: 6px;
                background-color: {p['bg_input']};
                color: {p['text_primary']};
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border: 2px solid {p['border_focus']};
            }}
        """

        self._table_style = f"""
            QTableWidget {{
                gridline-color: {p['border']};
                background-color: {p['bg_input']};
                color: {p['text_primary']};
                border: 1px solid {p['border']};
                border-radius: 6px;
            }}
            QTableWidget::item {{
                padding: 6px;
            }}
            QTableWidget::item:selected {{
                background-color: {p['selection_bg']};
            }}
            QHeaderView::section {{
                background-color: {p['bg_header']};
                color: {p['text_primary']};
                font-weight: bold;
                padding: 8px;
                border: none;
            }}
        """

        self._tab_style = f"""
            QTabWidget::pane {{
                border: 1px solid {p['border']};
                border-radius: 8px;
                background-color: {p['bg_main']};
            }}
            QTabBar::tab {{
                font-weight: bold;
                padding: 10px 20px;
                margin: 2px;
                border-radius: 6px;
                background-color: {p['bg_input']};
                color: {p['text_muted']};
            }}
            QTabBar::tab:selected {{
                background-color: {p['primary']};
                color: {p['text_on_primary']};
            }}
            QTabBar::tab:hover {{
                background-color: {p['bg_hover']};
                color: {p['text_primary']};
            }}
        """

        self._status_label_style = f"""
            QLabel {{
                font-size: 12px;
                color: {p['text_muted']};
                padding: 4px 8px;
            }}
        """

        self._card_style = f"""
            QFrame {{
                background-color: {p['bg_card']};
                border: 1px solid {p['border']};
                border-radius: 10px;
                padding: 15px;
            }}
        """

    # ─── UI Setup ────────────────────────────────────

    def _setup_ui(self):
        """Build the main UI."""
        self._build_styles()
        p = self._p

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # Header
        header = self._create_header()
        main_layout.addWidget(header)

        # Tab widget
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(self._tab_style)
        main_layout.addWidget(self._tabs)

        # Create tabs
        self._tabs.addTab(self._create_whatsapp_tab(), "💬 واتساب")
        self._tabs.addTab(self._create_telegram_tab(), "🤖 تليجرام")
        self._tabs.addTab(self._create_teams_tab(), "👥 Teams")
        self._tabs.addTab(self._create_automation_tab(), "⚙️ الأتمتة")

        # Status bar
        self._status_label = QLabel("جاهز")
        self._status_label.setStyleSheet(self._status_label_style)
        main_layout.addWidget(self._status_label)

    def _create_header(self) -> QFrame:
        """Create header section."""
        p = self._p
        frame = QFrame()
        frame.setStyleSheet(self._card_style)
        layout = QHBoxLayout(frame)

        title = QLabel("💬 تكامل تطبيقات سطح المكتب")
        title.setStyleSheet(f"""
            font-size: 22px;
            font-weight: bold;
            color: {p['accent']};
        """)
        layout.addWidget(title)

        layout.addStretch()

        subtitle = QLabel("WhatsApp  |  Telegram  |  Teams  |  Automation")
        subtitle.setStyleSheet(f"""
            font-size: 13px;
            color: {p['text_muted']};
        """)
        layout.addWidget(subtitle)

        return frame

    # ─── WhatsApp Tab ────────────────────────────────

    def _create_whatsapp_tab(self) -> QWidget:
        """Create WhatsApp tab."""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tab)
        scroll.setFrameShape(QFrame.NoFrame)

        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # ── Send Message Section ──
        send_group = QGroupBox("إرسال رسالة")
        send_group.setStyleSheet(self._section_style)
        send_layout = QFormLayout(send_group)

        self._wa_phone = QLineEdit()
        self._wa_phone.setPlaceholderText("+966 5XX XXX XXXX")
        self._wa_phone.setStyleSheet(self._input_style)
        send_layout.addRow("رقم الهاتف:", self._wa_phone)

        self._wa_name = QLineEdit()
        self._wa_name.setPlaceholderText("اسم المستلم (اختياري)")
        self._wa_name.setStyleSheet(self._input_style)
        send_layout.addRow("الاسم:", self._wa_name)

        self._wa_template = QComboBox()
        self._wa_template.setStyleSheet(self._input_style)
        self._wa_template.addItem("رسالة مخصصة", "custom")
        self._wa_template.addItem("إشعار الراتب", "salary_notification")
        self._wa_template.addItem("الموافقة على الإجازة", "leave_approval")
        self._wa_template.addItem("رفض الإجازة", "leave_rejection")
        self._wa_template.addItem("التقرير جاهز", "report_ready")
        self._wa_template.addItem("مهمة جديدة", "task_assigned")
        send_layout.addRow("القالب:", self._wa_template)

        self._wa_message = QTextEdit()
        self._wa_message.setMaximumHeight(120)
        self._wa_message.setPlaceholderText("اكتب رسالتك هنا...")
        self._wa_message.setStyleSheet(self._input_style)
        send_layout.addRow("الرسالة:", self._wa_message)

        btn_row = QHBoxLayout()
        self._wa_send_btn = QPushButton("📤 إرسال")
        self._wa_send_btn.setStyleSheet(self._btn_style)
        btn_row.addWidget(self._wa_send_btn)

        self._wa_send_file_btn = QPushButton("📎 إرسال ملف")
        self._wa_send_file_btn.setStyleSheet(self._btn_secondary_style)
        btn_row.addWidget(self._wa_send_file_btn)

        self._wa_queue_btn = QPushButton("📋 إضافة للقائمة")
        self._wa_queue_btn.setStyleSheet(self._btn_secondary_style)
        btn_row.addWidget(self._wa_queue_btn)

        btn_row.addStretch()
        send_layout.addRow("", btn_row)

        layout.addWidget(send_group)

        # ── Contacts Section ──
        contacts_group = QGroupBox("جهات الاتصال")
        contacts_group.setStyleSheet(self._section_style)
        contacts_layout = QVBoxLayout(contacts_group)

        contacts_toolbar = QHBoxLayout()
        self._wa_contact_search = QLineEdit()
        self._wa_contact_search.setPlaceholderText("بحث في جهات الاتصال...")
        self._wa_contact_search.setStyleSheet(self._input_style)
        contacts_toolbar.addWidget(self._wa_contact_search)

        self._wa_add_contact_btn = QPushButton("➕ إضافة")
        self._wa_add_contact_btn.setStyleSheet(self._btn_success_style)
        contacts_toolbar.addWidget(self._wa_add_contact_btn)

        contacts_layout.addLayout(contacts_toolbar)

        self._wa_contacts_table = QTableWidget()
        self._wa_contacts_table.setColumnCount(4)
        self._wa_contacts_table.setHorizontalHeaderLabels(
            ["الاسم", "الرقم", "كود الدولة", "إجراء"]
        )
        self._wa_contacts_table.horizontalHeader().setStretchLastSection(True)
        self._wa_contacts_table.setStyleSheet(self._table_style)
        contacts_layout.addWidget(self._wa_contacts_table)

        layout.addWidget(contacts_group)

        # ── Message Queue Section ──
        queue_group = QGroupBox("قائمة الإرسال")
        queue_group.setStyleSheet(self._section_style)
        queue_layout = QVBoxLayout(queue_group)

        queue_toolbar = QHBoxLayout()
        self._wa_process_queue_btn = QPushButton("▶️ إرسال الكل")
        self._wa_process_queue_btn.setStyleSheet(self._btn_style)
        queue_toolbar.addWidget(self._wa_process_queue_btn)

        self._wa_clear_queue_btn = QPushButton("🗑️ مسح القائمة")
        self._wa_clear_queue_btn.setStyleSheet(self._btn_danger_style)
        queue_toolbar.addWidget(self._wa_clear_queue_btn)

        queue_toolbar.addStretch()
        self._wa_queue_count = QLabel("0 رسالة في القائمة")
        self._wa_queue_count.setStyleSheet(self._status_label_style)
        queue_toolbar.addWidget(self._wa_queue_count)
        queue_layout.addLayout(queue_toolbar)

        self._wa_queue_table = QTableWidget()
        self._wa_queue_table.setColumnCount(4)
        self._wa_queue_table.setHorizontalHeaderLabels(
            ["المستلم", "الرسالة", "الحالة", "إجراء"]
        )
        self._wa_queue_table.horizontalHeader().setStretchLastSection(True)
        self._wa_queue_table.setStyleSheet(self._table_style)
        queue_layout.addWidget(self._wa_queue_table)

        layout.addWidget(queue_group)

        layout.addStretch()

        # Wrap in scroll
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(scroll)
        return container

    # ─── Telegram Tab ────────────────────────────────

    def _create_telegram_tab(self) -> QWidget:
        """Create Telegram tab."""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tab)
        scroll.setFrameShape(QFrame.NoFrame)

        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # ── Bot Configuration ──
        config_group = QGroupBox("إعدادات البوت")
        config_group.setStyleSheet(self._section_style)
        config_layout = QFormLayout(config_group)

        self._tg_token = QLineEdit()
        self._tg_token.setPlaceholderText("أدخل Bot Token من @BotFather")
        self._tg_token.setEchoMode(QLineEdit.Password)
        self._tg_token.setStyleSheet(self._input_style)
        config_layout.addRow("Bot Token:", self._tg_token)

        self._tg_default_chat = QLineEdit()
        self._tg_default_chat.setPlaceholderText("Chat ID الافتراضي")
        self._tg_default_chat.setStyleSheet(self._input_style)
        config_layout.addRow("Chat ID:", self._tg_default_chat)

        config_btns = QHBoxLayout()
        self._tg_test_btn = QPushButton("🔗 اختبار الاتصال")
        self._tg_test_btn.setStyleSheet(self._btn_style)
        config_btns.addWidget(self._tg_test_btn)

        self._tg_save_btn = QPushButton("💾 حفظ الإعدادات")
        self._tg_save_btn.setStyleSheet(self._btn_success_style)
        config_btns.addWidget(self._tg_save_btn)

        config_btns.addStretch()
        self._tg_status = QLabel("غير متصل")
        self._tg_status.setStyleSheet(f"color: {self._p['danger']}; font-weight: bold;")
        config_btns.addWidget(self._tg_status)

        config_layout.addRow("", config_btns)
        layout.addWidget(config_group)

        # ── Send Alert ──
        alert_group = QGroupBox("إرسال تنبيه")
        alert_group.setStyleSheet(self._section_style)
        alert_layout = QFormLayout(alert_group)

        self._tg_alert_chat = QLineEdit()
        self._tg_alert_chat.setPlaceholderText("Chat ID (اتركه فارغاً للافتراضي)")
        self._tg_alert_chat.setStyleSheet(self._input_style)
        alert_layout.addRow("Chat ID:", self._tg_alert_chat)

        self._tg_priority = QComboBox()
        self._tg_priority.setStyleSheet(self._input_style)
        self._tg_priority.addItem("عادي", "normal")
        self._tg_priority.addItem("منخفض", "low")
        self._tg_priority.addItem("مرتفع", "high")
        self._tg_priority.addItem("عاجل", "urgent")
        self._tg_priority.addItem("حرج", "critical")
        alert_layout.addRow("الأولوية:", self._tg_priority)

        self._tg_message = QTextEdit()
        self._tg_message.setMaximumHeight(100)
        self._tg_message.setPlaceholderText("نص التنبيه...")
        self._tg_message.setStyleSheet(self._input_style)
        alert_layout.addRow("الرسالة:", self._tg_message)

        alert_btns = QHBoxLayout()
        self._tg_send_alert_btn = QPushButton("🔔 إرسال تنبيه")
        self._tg_send_alert_btn.setStyleSheet(self._btn_style)
        alert_btns.addWidget(self._tg_send_alert_btn)

        self._tg_send_file_btn = QPushButton("📎 إرسال ملف")
        self._tg_send_file_btn.setStyleSheet(self._btn_secondary_style)
        alert_btns.addWidget(self._tg_send_file_btn)

        self._tg_approval_btn = QPushButton("📋 طلب موافقة")
        self._tg_approval_btn.setStyleSheet(self._btn_secondary_style)
        alert_btns.addWidget(self._tg_approval_btn)

        alert_btns.addStretch()
        alert_layout.addRow("", alert_btns)
        layout.addWidget(alert_group)

        # ── Chats List ──
        chats_group = QGroupBox("المحادثات")
        chats_group.setStyleSheet(self._section_style)
        chats_layout = QVBoxLayout(chats_group)

        chats_toolbar = QHBoxLayout()
        self._tg_add_chat_btn = QPushButton("➕ إضافة محادثة")
        self._tg_add_chat_btn.setStyleSheet(self._btn_success_style)
        chats_toolbar.addWidget(self._tg_add_chat_btn)

        self._tg_broadcast_btn = QPushButton("📢 بث رسالة")
        self._tg_broadcast_btn.setStyleSheet(self._btn_secondary_style)
        chats_toolbar.addWidget(self._tg_broadcast_btn)

        chats_toolbar.addStretch()
        chats_layout.addLayout(chats_toolbar)

        self._tg_chats_table = QTableWidget()
        self._tg_chats_table.setColumnCount(4)
        self._tg_chats_table.setHorizontalHeaderLabels(
            ["الاسم", "Chat ID", "النوع", "الحالة"]
        )
        self._tg_chats_table.horizontalHeader().setStretchLastSection(True)
        self._tg_chats_table.setStyleSheet(self._table_style)
        chats_layout.addWidget(self._tg_chats_table)

        layout.addWidget(chats_group)

        # ── Alert History ──
        history_group = QGroupBox("سجل التنبيهات")
        history_group.setStyleSheet(self._section_style)
        history_layout = QVBoxLayout(history_group)

        self._tg_history_table = QTableWidget()
        self._tg_history_table.setColumnCount(5)
        self._tg_history_table.setHorizontalHeaderLabels(
            ["التاريخ", "المستلم", "الأولوية", "الرسالة", "الحالة"]
        )
        self._tg_history_table.horizontalHeader().setStretchLastSection(True)
        self._tg_history_table.setStyleSheet(self._table_style)
        history_layout.addWidget(self._tg_history_table)

        layout.addWidget(history_group)

        layout.addStretch()

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(scroll)
        return container

    # ─── Teams Tab ───────────────────────────────────

    def _create_teams_tab(self) -> QWidget:
        """Create Teams tab."""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tab)
        scroll.setFrameShape(QFrame.NoFrame)

        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # ── Channels Configuration ──
        channels_group = QGroupBox("القنوات")
        channels_group.setStyleSheet(self._section_style)
        channels_layout = QVBoxLayout(channels_group)

        channels_toolbar = QHBoxLayout()
        self._teams_add_channel_btn = QPushButton("➕ إضافة قناة")
        self._teams_add_channel_btn.setStyleSheet(self._btn_success_style)
        channels_toolbar.addWidget(self._teams_add_channel_btn)

        self._teams_test_btn = QPushButton("🔗 اختبار")
        self._teams_test_btn.setStyleSheet(self._btn_style)
        channels_toolbar.addWidget(self._teams_test_btn)

        self._teams_save_btn = QPushButton("💾 حفظ")
        self._teams_save_btn.setStyleSheet(self._btn_secondary_style)
        channels_toolbar.addWidget(self._teams_save_btn)

        channels_toolbar.addStretch()
        channels_layout.addLayout(channels_toolbar)

        self._teams_channels_table = QTableWidget()
        self._teams_channels_table.setColumnCount(5)
        self._teams_channels_table.setHorizontalHeaderLabels(
            ["الاسم", "النوع", "Webhook URL", "الحالة", "إجراء"]
        )
        self._teams_channels_table.horizontalHeader().setStretchLastSection(True)
        self._teams_channels_table.setStyleSheet(self._table_style)
        channels_layout.addWidget(self._teams_channels_table)

        layout.addWidget(channels_group)

        # ── Send Message ──
        send_group = QGroupBox("إرسال رسالة")
        send_group.setStyleSheet(self._section_style)
        send_layout = QFormLayout(send_group)

        self._teams_channel_select = QComboBox()
        self._teams_channel_select.setStyleSheet(self._input_style)
        self._teams_channel_select.addItem("القناة الافتراضية", "default")
        send_layout.addRow("القناة:", self._teams_channel_select)

        self._teams_card_type = QComboBox()
        self._teams_card_type.setStyleSheet(self._input_style)
        self._teams_card_type.addItem("رسالة نصية", "text")
        self._teams_card_type.addItem("تنبيه", "alert")
        self._teams_card_type.addItem("طلب موافقة", "approval")
        self._teams_card_type.addItem("تقرير", "report")
        self._teams_card_type.addItem("حالة النظام", "status")
        self._teams_card_type.addItem("مهمة", "task")
        send_layout.addRow("نوع البطاقة:", self._teams_card_type)

        self._teams_title = QLineEdit()
        self._teams_title.setPlaceholderText("عنوان الرسالة")
        self._teams_title.setStyleSheet(self._input_style)
        send_layout.addRow("العنوان:", self._teams_title)

        self._teams_message = QTextEdit()
        self._teams_message.setMaximumHeight(100)
        self._teams_message.setPlaceholderText("نص الرسالة...")
        self._teams_message.setStyleSheet(self._input_style)
        send_layout.addRow("الرسالة:", self._teams_message)

        send_btns = QHBoxLayout()
        self._teams_send_btn = QPushButton("📤 إرسال")
        self._teams_send_btn.setStyleSheet(self._btn_style)
        send_btns.addWidget(self._teams_send_btn)

        self._teams_broadcast_btn = QPushButton("📢 بث للكل")
        self._teams_broadcast_btn.setStyleSheet(self._btn_secondary_style)
        send_btns.addWidget(self._teams_broadcast_btn)

        send_btns.addStretch()
        send_layout.addRow("", send_btns)

        layout.addWidget(send_group)

        # ── Message History ──
        history_group = QGroupBox("سجل الرسائل")
        history_group.setStyleSheet(self._section_style)
        history_layout = QVBoxLayout(history_group)

        self._teams_history_table = QTableWidget()
        self._teams_history_table.setColumnCount(5)
        self._teams_history_table.setHorizontalHeaderLabels(
            ["التاريخ", "القناة", "النوع", "العنوان", "الحالة"]
        )
        self._teams_history_table.horizontalHeader().setStretchLastSection(True)
        self._teams_history_table.setStyleSheet(self._table_style)
        history_layout.addWidget(self._teams_history_table)

        layout.addWidget(history_group)

        layout.addStretch()

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(scroll)
        return container

    # ─── Automation Tab ──────────────────────────────

    def _create_automation_tab(self) -> QWidget:
        """Create Automation tab."""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tab)
        scroll.setFrameShape(QFrame.NoFrame)

        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # ── Window Management ──
        windows_group = QGroupBox("إدارة النوافذ")
        windows_group.setStyleSheet(self._section_style)
        windows_layout = QVBoxLayout(windows_group)

        win_toolbar = QHBoxLayout()
        self._auto_refresh_btn = QPushButton("🔄 تحديث النوافذ")
        self._auto_refresh_btn.setStyleSheet(self._btn_style)
        win_toolbar.addWidget(self._auto_refresh_btn)

        self._auto_filter = QLineEdit()
        self._auto_filter.setPlaceholderText("فلتر بالعنوان...")
        self._auto_filter.setStyleSheet(self._input_style)
        win_toolbar.addWidget(self._auto_filter)

        win_toolbar.addStretch()
        windows_layout.addLayout(win_toolbar)

        self._auto_windows_table = QTableWidget()
        self._auto_windows_table.setColumnCount(5)
        self._auto_windows_table.setHorizontalHeaderLabels(
            ["العنوان", "البرنامج", "PID", "الحجم", "إجراء"]
        )
        self._auto_windows_table.horizontalHeader().setStretchLastSection(True)
        self._auto_windows_table.setStyleSheet(self._table_style)
        windows_layout.addWidget(self._auto_windows_table)

        win_actions = QHBoxLayout()
        self._auto_focus_btn = QPushButton("🔍 تركيز")
        self._auto_focus_btn.setStyleSheet(self._btn_secondary_style)
        win_actions.addWidget(self._auto_focus_btn)

        self._auto_minimize_btn = QPushButton("➖ تصغير")
        self._auto_minimize_btn.setStyleSheet(self._btn_secondary_style)
        win_actions.addWidget(self._auto_minimize_btn)

        self._auto_maximize_btn = QPushButton("➕ تكبير")
        self._auto_maximize_btn.setStyleSheet(self._btn_secondary_style)
        win_actions.addWidget(self._auto_maximize_btn)

        self._auto_close_btn = QPushButton("✖ إغلاق")
        self._auto_close_btn.setStyleSheet(self._btn_danger_style)
        win_actions.addWidget(self._auto_close_btn)

        self._auto_screenshot_btn = QPushButton("📸 لقطة")
        self._auto_screenshot_btn.setStyleSheet(self._btn_secondary_style)
        win_actions.addWidget(self._auto_screenshot_btn)

        win_actions.addStretch()
        windows_layout.addLayout(win_actions)

        layout.addWidget(windows_group)

        # ── Registered Applications ──
        apps_group = QGroupBox("التطبيقات المسجلة")
        apps_group.setStyleSheet(self._section_style)
        apps_layout = QVBoxLayout(apps_group)

        apps_toolbar = QHBoxLayout()
        self._auto_add_app_btn = QPushButton("➕ تسجيل تطبيق")
        self._auto_add_app_btn.setStyleSheet(self._btn_success_style)
        apps_toolbar.addWidget(self._auto_add_app_btn)

        self._auto_launch_btn = QPushButton("🚀 تشغيل")
        self._auto_launch_btn.setStyleSheet(self._btn_style)
        apps_toolbar.addWidget(self._auto_launch_btn)

        apps_toolbar.addStretch()
        apps_layout.addLayout(apps_toolbar)

        self._auto_apps_table = QTableWidget()
        self._auto_apps_table.setColumnCount(3)
        self._auto_apps_table.setHorizontalHeaderLabels(
            ["الاسم", "المسار", "إجراء"]
        )
        self._auto_apps_table.horizontalHeader().setStretchLastSection(True)
        self._auto_apps_table.setStyleSheet(self._table_style)
        apps_layout.addWidget(self._auto_apps_table)

        layout.addWidget(apps_group)

        # ── Workflows ──
        workflow_group = QGroupBox("سيناريوهات الأتمتة")
        workflow_group.setStyleSheet(self._section_style)
        workflow_layout = QVBoxLayout(workflow_group)

        wf_toolbar = QHBoxLayout()
        self._auto_new_workflow_btn = QPushButton("➕ سيناريو جديد")
        self._auto_new_workflow_btn.setStyleSheet(self._btn_success_style)
        wf_toolbar.addWidget(self._auto_new_workflow_btn)

        self._auto_run_workflow_btn = QPushButton("▶️ تشغيل")
        self._auto_run_workflow_btn.setStyleSheet(self._btn_style)
        wf_toolbar.addWidget(self._auto_run_workflow_btn)

        self._auto_save_workflows_btn = QPushButton("💾 حفظ")
        self._auto_save_workflows_btn.setStyleSheet(self._btn_secondary_style)
        wf_toolbar.addWidget(self._auto_save_workflows_btn)

        wf_toolbar.addStretch()
        workflow_layout.addLayout(wf_toolbar)

        self._auto_workflows_table = QTableWidget()
        self._auto_workflows_table.setColumnCount(5)
        self._auto_workflows_table.setHorizontalHeaderLabels(
            ["الاسم", "الوصف", "الخطوات", "آخر تشغيل", "مرات التشغيل"]
        )
        self._auto_workflows_table.horizontalHeader().setStretchLastSection(
            True
        )
        self._auto_workflows_table.setStyleSheet(self._table_style)
        workflow_layout.addWidget(self._auto_workflows_table)

        layout.addWidget(workflow_group)

        # ── System Info ──
        info_group = QGroupBox("معلومات النظام")
        info_group.setStyleSheet(self._section_style)
        info_layout = QGridLayout(info_group)

        self._auto_platform_label = QLabel("المنصة: -")
        self._auto_platform_label.setStyleSheet(self._status_label_style)
        info_layout.addWidget(self._auto_platform_label, 0, 0)

        self._auto_window_mgmt_label = QLabel("إدارة النوافذ: -")
        self._auto_window_mgmt_label.setStyleSheet(self._status_label_style)
        info_layout.addWidget(self._auto_window_mgmt_label, 0, 1)

        self._auto_clipboard_label = QLabel("الحافظة: -")
        self._auto_clipboard_label.setStyleSheet(self._status_label_style)
        info_layout.addWidget(self._auto_clipboard_label, 0, 2)

        self._auto_screenshot_label = QLabel("لقطات الشاشة: -")
        self._auto_screenshot_label.setStyleSheet(self._status_label_style)
        info_layout.addWidget(self._auto_screenshot_label, 1, 0)

        self._auto_apps_count_label = QLabel("التطبيقات: 0")
        self._auto_apps_count_label.setStyleSheet(self._status_label_style)
        info_layout.addWidget(self._auto_apps_count_label, 1, 1)

        self._auto_workflows_count_label = QLabel("السيناريوهات: 0")
        self._auto_workflows_count_label.setStyleSheet(self._status_label_style)
        info_layout.addWidget(self._auto_workflows_count_label, 1, 2)

        layout.addWidget(info_group)

        layout.addStretch()

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(scroll)
        return container

    # ─── Connections ─────────────────────────────────

    def _setup_connections(self):
        """Connect signals to slots."""
        # WhatsApp
        self._wa_send_btn.clicked.connect(self._on_wa_send)
        self._wa_send_file_btn.clicked.connect(self._on_wa_send_file)
        self._wa_queue_btn.clicked.connect(self._on_wa_queue)
        self._wa_process_queue_btn.clicked.connect(self._on_wa_process_queue)
        self._wa_clear_queue_btn.clicked.connect(self._on_wa_clear_queue)
        self._wa_add_contact_btn.clicked.connect(self._on_wa_add_contact)
        self._wa_template.currentIndexChanged.connect(
            self._on_wa_template_changed
        )

        # Telegram
        self._tg_test_btn.clicked.connect(self._on_tg_test)
        self._tg_save_btn.clicked.connect(self._on_tg_save)
        self._tg_send_alert_btn.clicked.connect(self._on_tg_send_alert)
        self._tg_send_file_btn.clicked.connect(self._on_tg_send_file)
        self._tg_approval_btn.clicked.connect(self._on_tg_approval)
        self._tg_add_chat_btn.clicked.connect(self._on_tg_add_chat)
        self._tg_broadcast_btn.clicked.connect(self._on_tg_broadcast)

        # Teams
        self._teams_add_channel_btn.clicked.connect(
            self._on_teams_add_channel
        )
        self._teams_test_btn.clicked.connect(self._on_teams_test)
        self._teams_save_btn.clicked.connect(self._on_teams_save)
        self._teams_send_btn.clicked.connect(self._on_teams_send)
        self._teams_broadcast_btn.clicked.connect(self._on_teams_broadcast)

        # Automation
        self._auto_refresh_btn.clicked.connect(self._on_auto_refresh)
        self._auto_focus_btn.clicked.connect(self._on_auto_focus)
        self._auto_minimize_btn.clicked.connect(self._on_auto_minimize)
        self._auto_maximize_btn.clicked.connect(self._on_auto_maximize)
        self._auto_close_btn.clicked.connect(self._on_auto_close)
        self._auto_screenshot_btn.clicked.connect(self._on_auto_screenshot)
        self._auto_add_app_btn.clicked.connect(self._on_auto_add_app)
        self._auto_launch_btn.clicked.connect(self._on_auto_launch)
        self._auto_new_workflow_btn.clicked.connect(
            self._on_auto_new_workflow
        )
        self._auto_run_workflow_btn.clicked.connect(
            self._on_auto_run_workflow
        )
        self._auto_save_workflows_btn.clicked.connect(
            self._on_auto_save_workflows
        )

    # ─── Lazy Initialization ─────────────────────────

    def _get_whatsapp(self):
        """Get or create WhatsApp manager."""
        if self._whatsapp_manager is None:
            from core.desktop_apps.whatsapp import WhatsAppManager
            self._whatsapp_manager = WhatsAppManager()
        return self._whatsapp_manager

    def _get_telegram(self):
        """Get or create Telegram manager."""
        if self._telegram_manager is None:
            from core.desktop_apps.telegram import TelegramBotManager
            self._telegram_manager = TelegramBotManager()
        return self._telegram_manager

    def _get_teams(self):
        """Get or create Teams connector."""
        if self._teams_connector is None:
            from core.desktop_apps.teams import TeamsConnector
            self._teams_connector = TeamsConnector()
        return self._teams_connector

    def _get_automation(self):
        """Get or create automation engine."""
        if self._automation_engine is None:
            from core.desktop_apps.automation import DesktopAutomation
            self._automation_engine = DesktopAutomation()
        return self._automation_engine

    # ─── WhatsApp Handlers ───────────────────────────

    def _on_wa_send(self):
        """Send WhatsApp message."""
        phone = self._wa_phone.text().strip()
        message = self._wa_message.toPlainText().strip()
        if not phone or not message:
            QMessageBox.warning(
                self, "تنبيه", "الرجاء إدخال رقم الهاتف والرسالة"
            )
            return

        wa = self._get_whatsapp()
        name = self._wa_name.text().strip()
        success = wa.quick_send(phone, message)

        if success:
            self._status_label.setText("✅ تم إرسال الرسالة عبر واتساب")
            self._wa_message.clear()
        else:
            self._status_label.setText("❌ فشل إرسال الرسالة")

    def _on_wa_send_file(self):
        """Send file via WhatsApp."""
        phone = self._wa_phone.text().strip()
        if not phone:
            QMessageBox.warning(self, "تنبيه", "الرجاء إدخال رقم الهاتف")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "اختر ملف", "", "كل الملفات (*.*)"
        )
        if file_path:
            wa = self._get_whatsapp()
            caption = self._wa_message.toPlainText().strip()
            try:
                msg = wa.create_file_message(phone, file_path, caption)
                wa.send(msg)
                self._status_label.setText("✅ تم إرسال الملف")
            except Exception as e:
                self._status_label.setText(f"❌ خطأ: {e}")

    def _on_wa_queue(self):
        """Add message to WhatsApp queue."""
        phone = self._wa_phone.text().strip()
        message = self._wa_message.toPlainText().strip()
        if not phone or not message:
            return

        wa = self._get_whatsapp()
        msg = wa.create_message(phone, message)
        wa.queue_message(msg)
        self._wa_queue_count.setText(
            f"{len(wa.get_queue())} رسالة في القائمة"
        )
        self._status_label.setText("📋 تمت الإضافة للقائمة")

    def _on_wa_process_queue(self):
        """Process WhatsApp message queue."""
        wa = self._get_whatsapp()
        if not wa.get_queue():
            self._status_label.setText("القائمة فارغة")
            return
        results = wa.process_queue()
        self._status_label.setText(
            f"✅ تم إرسال {results['sent']}/{results['total']} رسالة"
        )
        self._wa_queue_count.setText(
            f"{len(wa.get_queue())} رسالة في القائمة"
        )

    def _on_wa_clear_queue(self):
        """Clear WhatsApp message queue."""
        wa = self._get_whatsapp()
        wa.clear_queue()
        self._wa_queue_count.setText("0 رسالة في القائمة")
        self._status_label.setText("🗑️ تم مسح القائمة")

    def _on_wa_add_contact(self):
        """Add WhatsApp contact."""
        from ui.dialogs import show_info
        show_info(self, "إضافة جهة اتصال", "سيتم فتح نافذة إضافة جهة اتصال")

    def _on_wa_template_changed(self, index):
        """Handle template selection change."""
        template_id = self._wa_template.currentData()
        if template_id == "custom":
            self._wa_message.clear()
            self._wa_message.setEnabled(True)
        else:
            wa = self._get_whatsapp()
            template = wa.get_template(template_id)
            if template:
                self._wa_message.setText(template.get("template_ar", ""))

    # ─── Telegram Handlers ───────────────────────────

    def _on_tg_test(self):
        """Test Telegram bot connection."""
        tg = self._get_telegram()
        token = self._tg_token.text().strip()
        if not token:
            QMessageBox.warning(self, "تنبيه", "الرجاء إدخال Bot Token")
            return

        tg.set_token(token)
        if tg.test_connection():
            self._tg_status.setText("✅ متصل")
            self._tg_status.setStyleSheet(f"color: {self._p['success']}; font-weight: bold;")
            info = tg.get_bot_info()
            if info:
                self._status_label.setText(
                    f"✅ متصل بـ @{info.get('username', '')}"
                )
        else:
            self._tg_status.setText("❌ فشل الاتصال")
            self._tg_status.setStyleSheet(f"color: {self._p['danger']}; font-weight: bold;")
            self._status_label.setText("❌ فشل الاتصال بالبوت")

    def _on_tg_save(self):
        """Save Telegram configuration."""
        tg = self._get_telegram()
        tg.set_token(self._tg_token.text().strip())
        tg.set_default_chat(self._tg_default_chat.text().strip())
        tg.save_config()
        self._status_label.setText("💾 تم حفظ إعدادات تليجرام")

    def _on_tg_send_alert(self):
        """Send Telegram alert."""
        tg = self._get_telegram()
        message = self._tg_message.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "تنبيه", "الرجاء إدخال نص التنبيه")
            return

        from core.desktop_apps.telegram.telegram_bot import AlertPriority
        priority_map = {
            "low": AlertPriority.LOW,
            "normal": AlertPriority.NORMAL,
            "high": AlertPriority.HIGH,
            "urgent": AlertPriority.URGENT,
            "critical": AlertPriority.CRITICAL,
        }
        priority = priority_map.get(
            self._tg_priority.currentData(), AlertPriority.NORMAL
        )
        chat_id = self._tg_alert_chat.text().strip()

        success = tg.send_alert(message, priority, chat_id)
        if success:
            self._status_label.setText("✅ تم إرسال التنبيه عبر تليجرام")
            self._tg_message.clear()
        else:
            self._status_label.setText("❌ فشل إرسال التنبيه")

    def _on_tg_send_file(self):
        """Send file via Telegram."""
        tg = self._get_telegram()
        chat_id = (
            self._tg_alert_chat.text().strip()
            or self._tg_default_chat.text().strip()
        )
        if not chat_id:
            QMessageBox.warning(self, "تنبيه", "الرجاء تحديد Chat ID")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "اختر ملف", "", "كل الملفات (*.*)"
        )
        if file_path:
            caption = self._tg_message.toPlainText().strip()
            success = tg.send_file(chat_id, file_path, caption)
            if success:
                self._status_label.setText("✅ تم إرسال الملف عبر تليجرام")
            else:
                self._status_label.setText("❌ فشل إرسال الملف")

    def _on_tg_approval(self):
        """Send approval request via Telegram."""
        from ui.dialogs import show_info
        show_info(
            self, "طلب موافقة",
            "سيتم فتح نافذة إنشاء طلب موافقة عبر تليجرام"
        )

    def _on_tg_add_chat(self):
        """Add Telegram chat."""
        from ui.dialogs import show_info
        show_info(self, "إضافة محادثة", "سيتم فتح نافذة إضافة محادثة")

    def _on_tg_broadcast(self):
        """Broadcast message to all Telegram chats."""
        tg = self._get_telegram()
        message = self._tg_message.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "تنبيه", "الرجاء إدخال نص الرسالة")
            return

        reply = QMessageBox.question(
            self, "تأكيد البث",
            "هل تريد بث هذه الرسالة لجميع المحادثات؟",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            results = tg.broadcast(message)
            self._status_label.setText(
                f"📢 تم البث: {results['sent']}/{results['total']}"
            )

    # ─── Teams Handlers ──────────────────────────────

    def _on_teams_add_channel(self):
        """Add Teams channel."""
        from ui.dialogs import show_info
        show_info(
            self, "إضافة قناة",
            "سيتم فتح نافذة إضافة قناة Teams مع Webhook URL"
        )

    def _on_teams_test(self):
        """Test Teams webhook connection."""
        teams = self._get_teams()
        if not teams.is_configured:
            QMessageBox.warning(
                self, "تنبيه", "الرجاء إضافة قناة أولاً"
            )
            return

        success = teams.test_connection()
        if success:
            self._status_label.setText("✅ تم الاتصال بـ Teams بنجاح")
        else:
            self._status_label.setText("❌ فشل الاتصال بـ Teams")

    def _on_teams_save(self):
        """Save Teams configuration."""
        teams = self._get_teams()
        teams.save_config()
        self._status_label.setText("💾 تم حفظ إعدادات Teams")

    def _on_teams_send(self):
        """Send Teams message."""
        teams = self._get_teams()
        title = self._teams_title.text().strip()
        message = self._teams_message.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "تنبيه", "الرجاء إدخال نص الرسالة")
            return

        card_type = self._teams_card_type.currentData()

        if card_type == "text":
            success = teams.send_text(message, title=title)
        elif card_type == "alert":
            success = teams.send_alert(title or "تنبيه", message)
        elif card_type == "status":
            success = teams.send_status_card(
                title or "INTEGRA", {"الحالة": message}
            )
        else:
            success = teams.send_text(message, title=title)

        if success:
            self._status_label.setText("✅ تم الإرسال عبر Teams")
            self._teams_message.clear()
        else:
            self._status_label.setText("❌ فشل الإرسال عبر Teams")

    def _on_teams_broadcast(self):
        """Broadcast to all Teams channels."""
        teams = self._get_teams()
        message = self._teams_message.toPlainText().strip()
        if not message:
            return

        reply = QMessageBox.question(
            self, "تأكيد البث",
            "هل تريد بث هذه الرسالة لجميع القنوات؟",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            title = self._teams_title.text().strip()
            results = teams.broadcast(message, title=title)
            self._status_label.setText(
                f"📢 تم البث: {results['sent']}/{results['total']}"
            )

    # ─── Automation Handlers ─────────────────────────

    def _on_auto_refresh(self):
        """Refresh windows list."""
        auto = self._get_automation()
        title_filter = self._auto_filter.text().strip()
        windows = auto.find_windows(title_filter)

        self._auto_windows_table.setRowCount(len(windows))
        for i, win in enumerate(windows):
            self._auto_windows_table.setItem(
                i, 0, QTableWidgetItem(win.title)
            )
            self._auto_windows_table.setItem(
                i, 1, QTableWidgetItem(win.process_name or win.class_name)
            )
            self._auto_windows_table.setItem(
                i, 2, QTableWidgetItem(str(win.process_id))
            )
            self._auto_windows_table.setItem(
                i, 3,
                QTableWidgetItem(f"{win.width}x{win.height}")
            )

        self._status_label.setText(f"🔄 تم العثور على {len(windows)} نافذة")

        # Update system info
        caps = auto.get_capabilities()
        self._auto_platform_label.setText(
            f"المنصة: {caps['platform']}"
        )
        self._auto_window_mgmt_label.setText(
            f"إدارة النوافذ: {'✅' if caps['window_management'] else '❌'}"
        )
        self._auto_clipboard_label.setText(
            f"الحافظة: {'✅' if caps['clipboard'] else '❌'}"
        )
        self._auto_screenshot_label.setText(
            f"لقطات الشاشة: {'✅' if caps['screenshot'] else '❌'}"
        )

        stats = auto.get_stats()
        self._auto_apps_count_label.setText(
            f"التطبيقات: {stats['registered_apps']}"
        )
        self._auto_workflows_count_label.setText(
            f"السيناريوهات: {stats['workflows']}"
        )

    def _get_selected_window_title(self) -> str:
        """Get title of selected window in table."""
        row = self._auto_windows_table.currentRow()
        if row >= 0:
            item = self._auto_windows_table.item(row, 0)
            if item:
                return item.text()
        return ""

    def _on_auto_focus(self):
        """Focus selected window."""
        title = self._get_selected_window_title()
        if not title:
            return
        auto = self._get_automation()
        if auto.focus_window(title):
            self._status_label.setText(f"🔍 تم التركيز على: {title}")
        else:
            self._status_label.setText(f"❌ فشل التركيز على: {title}")

    def _on_auto_minimize(self):
        """Minimize selected window."""
        title = self._get_selected_window_title()
        if not title:
            return
        auto = self._get_automation()
        auto.minimize_window(title)
        self._status_label.setText(f"➖ تم تصغير: {title}")

    def _on_auto_maximize(self):
        """Maximize selected window."""
        title = self._get_selected_window_title()
        if not title:
            return
        auto = self._get_automation()
        auto.maximize_window(title)
        self._status_label.setText(f"➕ تم تكبير: {title}")

    def _on_auto_close(self):
        """Close selected window."""
        title = self._get_selected_window_title()
        if not title:
            return

        reply = QMessageBox.question(
            self, "تأكيد الإغلاق",
            f"هل تريد إغلاق النافذة:\n{title}؟",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            auto = self._get_automation()
            auto.close_window(title)
            self._status_label.setText(f"✖ تم إغلاق: {title}")
            self._on_auto_refresh()

    def _on_auto_screenshot(self):
        """Take screenshot."""
        auto = self._get_automation()
        path = auto.take_screenshot()
        if path:
            self._status_label.setText(f"📸 تم حفظ لقطة الشاشة: {path}")
        else:
            self._status_label.setText("❌ فشل التقاط الشاشة")

    def _on_auto_add_app(self):
        """Register a new application."""
        from ui.dialogs import show_info
        show_info(
            self, "تسجيل تطبيق",
            "سيتم فتح نافذة تسجيل تطبيق جديد"
        )

    def _on_auto_launch(self):
        """Launch selected application."""
        row = self._auto_apps_table.currentRow()
        if row < 0:
            return
        item = self._auto_apps_table.item(row, 1)
        if item:
            auto = self._get_automation()
            pid = auto.launch_app(item.text())
            if pid:
                self._status_label.setText(
                    f"🚀 تم التشغيل (PID: {pid})"
                )
            else:
                self._status_label.setText("❌ فشل التشغيل")

    def _on_auto_new_workflow(self):
        """Create new workflow."""
        from ui.dialogs import show_info
        show_info(
            self, "سيناريو جديد",
            "سيتم فتح محرر سيناريوهات الأتمتة"
        )

    def _on_auto_run_workflow(self):
        """Run selected workflow."""
        row = self._auto_workflows_table.currentRow()
        if row < 0:
            return
        item = self._auto_workflows_table.item(row, 0)
        if item:
            auto = self._get_automation()
            wf = auto.get_workflow(item.text())
            if wf:
                results = auto.run_workflow(wf)
                self._status_label.setText(
                    f"▶️ اكتمل السيناريو: "
                    f"{results['success']}/{results['total']} نجح"
                )

    def _on_auto_save_workflows(self):
        """Save automation workflows."""
        auto = self._get_automation()
        auto.save_config()
        self._status_label.setText("💾 تم حفظ السيناريوهات")
