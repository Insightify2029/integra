"""
Telegram Bot Integration Manager
=================================
Integration with Telegram Bot API for sending alerts,
notifications, and handling queries from INTEGRA.

Features:
- Bot setup and configuration
- Send text messages and files
- Inline keyboard for approvals
- Command handling (/salary, /leave, /tasks, /status)
- Group and channel notifications
- Message formatting (Markdown/HTML)
- Webhook and polling modes
- Alert priority levels
"""

import os
import json
import time
from enum import Enum
from datetime import datetime
from typing import Optional, Callable
from dataclasses import dataclass, field, asdict

from core.logging import app_logger


# ═══════════════════════════════════════════════════════
# Data Models
# ═══════════════════════════════════════════════════════

class AlertPriority(Enum):
    """Alert priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class ParseMode(Enum):
    """Telegram message parse mode."""
    TEXT = ""
    MARKDOWN = "MarkdownV2"
    HTML = "HTML"


@dataclass
class TelegramChat:
    """A Telegram chat (user, group, or channel)."""
    chat_id: str
    title: str = ""
    chat_type: str = "private"  # private, group, supergroup, channel
    username: str = ""
    is_active: bool = True

    @property
    def display_name(self) -> str:
        """Get display name."""
        return self.title or self.username or self.chat_id


@dataclass
class BotCommand:
    """A bot command definition."""
    command: str
    description_ar: str
    description_en: str
    handler: Optional[Callable] = None


@dataclass
class InlineButton:
    """An inline keyboard button."""
    text: str
    callback_data: str = ""
    url: str = ""


@dataclass
class TelegramAlert:
    """An alert to send via Telegram."""
    id: str = ""
    chat_id: str = ""
    message: str = ""
    priority: AlertPriority = AlertPriority.NORMAL
    parse_mode: ParseMode = ParseMode.HTML
    buttons: list = field(default_factory=list)
    file_path: str = ""
    sent: bool = False
    sent_at: str = ""
    error: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"tg_{int(time.time() * 1000)}"


# ═══════════════════════════════════════════════════════
# Default Bot Commands
# ═══════════════════════════════════════════════════════

DEFAULT_COMMANDS = [
    BotCommand(
        command="start",
        description_ar="بدء المحادثة مع البوت",
        description_en="Start conversation with bot",
    ),
    BotCommand(
        command="help",
        description_ar="عرض الأوامر المتاحة",
        description_en="Show available commands",
    ),
    BotCommand(
        command="status",
        description_ar="حالة النظام",
        description_en="System status",
    ),
    BotCommand(
        command="salary",
        description_ar="استعلام عن الراتب",
        description_en="Salary inquiry",
    ),
    BotCommand(
        command="leave",
        description_ar="حالة الإجازات",
        description_en="Leave status",
    ),
    BotCommand(
        command="tasks",
        description_ar="المهام المعلقة",
        description_en="Pending tasks",
    ),
    BotCommand(
        command="approve",
        description_ar="الموافقة على طلب",
        description_en="Approve a request",
    ),
    BotCommand(
        command="reject",
        description_ar="رفض طلب",
        description_en="Reject a request",
    ),
    BotCommand(
        command="report",
        description_ar="طلب تقرير",
        description_en="Request a report",
    ),
    BotCommand(
        command="notify",
        description_ar="إعدادات الإشعارات",
        description_en="Notification settings",
    ),
]


# ═══════════════════════════════════════════════════════
# Priority Emoji Map
# ═══════════════════════════════════════════════════════

PRIORITY_EMOJI = {
    AlertPriority.LOW: "",
    AlertPriority.NORMAL: "",
    AlertPriority.HIGH: "⚠️",
    AlertPriority.URGENT: "🔴",
    AlertPriority.CRITICAL: "🚨",
}


# ═══════════════════════════════════════════════════════
# Telegram Bot Manager
# ═══════════════════════════════════════════════════════

class TelegramBotManager:
    """
    Telegram Bot integration manager.

    Provides:
    - Bot configuration and token management
    - Send alerts and notifications
    - Command handling for queries
    - Inline keyboards for approvals
    - Group/channel messaging
    - File sending (reports, PDFs)
    - Priority-based alerts
    """

    # Telegram Bot API base URL
    API_BASE = "https://api.telegram.org/bot{token}"

    def __init__(self, config_path: str = ""):
        self._config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            ))),
            "config", "telegram_config.json"
        )
        self._bot_token = ""
        self._bot_username = ""
        self._chats: list[TelegramChat] = []
        self._commands = list(DEFAULT_COMMANDS)
        self._command_handlers: dict[str, Callable] = {}
        self._alert_history: list[TelegramAlert] = []
        self._default_chat_id = ""
        self._is_running = False
        self._send_delay = 0.5

        # Alert routing: priority -> chat_ids
        self._alert_routing: dict[str, list[str]] = {
            "low": [],
            "normal": [],
            "high": [],
            "urgent": [],
            "critical": [],
        }

        self._load_config()

        app_logger.info("Telegram Bot Manager initialized")

    # ─── Configuration ───────────────────────────────

    def _load_config(self):
        """Load configuration from file."""
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                self._bot_token = config.get("bot_token", "")
                self._bot_username = config.get("bot_username", "")
                self._default_chat_id = config.get("default_chat_id", "")
                self._send_delay = config.get("send_delay", 0.5)
                self._alert_routing = config.get(
                    "alert_routing", self._alert_routing
                )

                for c in config.get("chats", []):
                    self._chats.append(TelegramChat(**c))

                app_logger.debug("Telegram config loaded")
            except Exception as e:
                app_logger.error(f"Error loading Telegram config: {e}")

    def save_config(self):
        """Save configuration to file."""
        config = {
            "bot_token": self._bot_token,
            "bot_username": self._bot_username,
            "default_chat_id": self._default_chat_id,
            "send_delay": self._send_delay,
            "alert_routing": self._alert_routing,
            "chats": [asdict(c) for c in self._chats],
        }
        try:
            os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            app_logger.debug("Telegram config saved")
        except Exception as e:
            app_logger.error(f"Error saving Telegram config: {e}")

    def set_token(self, token: str):
        """Set bot token."""
        self._bot_token = token.strip()

    def set_default_chat(self, chat_id: str):
        """Set default chat for alerts."""
        self._default_chat_id = chat_id.strip()

    # ─── API Helpers ─────────────────────────────────

    @property
    def api_url(self) -> str:
        """Get API base URL with token."""
        return self.API_BASE.format(token=self._bot_token)

    def _api_request(self, method: str, data: dict = None,
                     files: dict = None) -> Optional[dict]:
        """Make Telegram Bot API request."""
        if not self._bot_token:
            app_logger.error("Telegram bot token not configured")
            return None

        try:
            import requests
        except ImportError:
            app_logger.error("requests library not available")
            return None

        url = f"{self.api_url}/{method}"

        try:
            if files:
                response = requests.post(
                    url, data=data, files=files, timeout=30
                )
            else:
                response = requests.post(url, json=data, timeout=30)

            result = response.json()
            if result.get("ok"):
                return result.get("result")
            else:
                app_logger.error(
                    f"Telegram API error: {result.get('description', 'Unknown')}"
                )
                return None

        except Exception as e:
            app_logger.error(f"Telegram API request failed: {e}")
            return None

    # ─── Bot Info ─────────────────────────────────────

    def get_bot_info(self) -> Optional[dict]:
        """Get bot information from Telegram."""
        result = self._api_request("getMe")
        if result:
            self._bot_username = result.get("username", "")
        return result

    def test_connection(self) -> bool:
        """Test if bot token is valid."""
        return self.get_bot_info() is not None

    # ─── Chat Management ─────────────────────────────

    def add_chat(self, chat_id: str, title: str = "",
                 chat_type: str = "private") -> TelegramChat:
        """Add a chat."""
        chat = TelegramChat(
            chat_id=chat_id, title=title, chat_type=chat_type
        )
        self._chats.append(chat)
        app_logger.info(f"Telegram chat added: {title or chat_id}")
        return chat

    def remove_chat(self, chat_id: str):
        """Remove a chat."""
        self._chats = [c for c in self._chats if c.chat_id != chat_id]

    def get_chats(self) -> list[TelegramChat]:
        """Get all chats."""
        return list(self._chats)

    # ─── Sending Messages ────────────────────────────

    def send_message(self, chat_id: str, text: str,
                     parse_mode: str = "HTML",
                     buttons: list[list[InlineButton]] = None) -> bool:
        """
        Send a text message.

        Args:
            chat_id: Target chat ID
            text: Message text
            parse_mode: HTML or MarkdownV2
            buttons: Optional inline keyboard (list of button rows)
        """
        data = {
            "chat_id": chat_id,
            "text": text,
        }
        if parse_mode:
            data["parse_mode"] = parse_mode

        if buttons:
            keyboard = []
            for row in buttons:
                btn_row = []
                for btn in row:
                    btn_data = {"text": btn.text}
                    if btn.callback_data:
                        btn_data["callback_data"] = btn.callback_data
                    elif btn.url:
                        btn_data["url"] = btn.url
                    btn_row.append(btn_data)
                keyboard.append(btn_row)
            data["reply_markup"] = {"inline_keyboard": keyboard}

        result = self._api_request("sendMessage", data)
        return result is not None

    def send_file(self, chat_id: str, file_path: str,
                  caption: str = "") -> bool:
        """Send a file (document)."""
        if not os.path.exists(file_path):
            app_logger.error(f"File not found: {file_path}")
            return False

        data = {"chat_id": chat_id}
        if caption:
            data["caption"] = caption
            data["parse_mode"] = "HTML"

        try:
            with open(file_path, 'rb') as f:
                files = {"document": f}
                result = self._api_request("sendDocument", data, files)
            return result is not None
        except Exception as e:
            app_logger.error(f"Failed to send file: {e}")
            return False

    def send_photo(self, chat_id: str, photo_path: str,
                   caption: str = "") -> bool:
        """Send a photo."""
        if not os.path.exists(photo_path):
            app_logger.error(f"Photo not found: {photo_path}")
            return False

        data = {"chat_id": chat_id}
        if caption:
            data["caption"] = caption
            data["parse_mode"] = "HTML"

        try:
            with open(photo_path, 'rb') as f:
                files = {"photo": f}
                result = self._api_request("sendPhoto", data, files)
            return result is not None
        except Exception as e:
            app_logger.error(f"Failed to send photo: {e}")
            return False

    # ─── Alert System ────────────────────────────────

    def send_alert(self, message: str,
                   priority: AlertPriority = AlertPriority.NORMAL,
                   chat_id: str = "",
                   buttons: list[list[InlineButton]] = None) -> bool:
        """
        Send a priority-based alert.

        Routes to appropriate chats based on priority level.
        """
        target = chat_id or self._default_chat_id
        if not target:
            # Try routing
            routed = self._alert_routing.get(priority.value, [])
            if routed:
                target = routed[0]

        if not target:
            app_logger.error("No target chat for alert")
            return False

        emoji = PRIORITY_EMOJI.get(priority, "")
        prefix = f"{emoji} " if emoji else ""

        if priority in (AlertPriority.URGENT, AlertPriority.CRITICAL):
            formatted = (
                f"{prefix}<b>[{priority.value.upper()}]</b>\n\n{message}"
            )
        else:
            formatted = f"{prefix}{message}"

        alert = TelegramAlert(
            chat_id=target,
            message=message,
            priority=priority,
        )

        success = self.send_message(target, formatted, buttons=buttons)

        alert.sent = success
        if success:
            alert.sent_at = datetime.now().isoformat()
        else:
            alert.error = "Send failed"

        self._alert_history.append(alert)
        return success

    def send_approval_request(self, chat_id: str, title: str,
                              details: str, request_id: str) -> bool:
        """
        Send an approval request with Accept/Reject buttons.
        """
        message = (
            f"<b>طلب موافقة</b>\n\n"
            f"<b>{title}</b>\n"
            f"{details}\n\n"
            f"<i>الرقم المرجعي: {request_id}</i>"
        )

        buttons = [[
            InlineButton(
                text="✅ موافقة",
                callback_data=f"approve_{request_id}"
            ),
            InlineButton(
                text="❌ رفض",
                callback_data=f"reject_{request_id}"
            ),
        ]]

        return self.send_message(chat_id, message, buttons=buttons)

    # ─── Notification Helpers ────────────────────────

    def notify_salary(self, employee_name: str, month: str,
                      amount: str, chat_id: str = "") -> bool:
        """Send salary notification."""
        target = chat_id or self._default_chat_id
        message = (
            f"💰 <b>إشعار راتب</b>\n\n"
            f"الموظف: {employee_name}\n"
            f"الشهر: {month}\n"
            f"المبلغ: {amount} ريال\n\n"
            f"<i>INTEGRA HR System</i>"
        )
        return self.send_message(target, message)

    def notify_leave(self, employee_name: str, start_date: str,
                     end_date: str, status: str,
                     chat_id: str = "") -> bool:
        """Send leave status notification."""
        target = chat_id or self._default_chat_id
        status_emoji = "✅" if status == "approved" else "❌"
        status_text = "موافق عليها" if status == "approved" else "مرفوضة"
        message = (
            f"{status_emoji} <b>إجازة {status_text}</b>\n\n"
            f"الموظف: {employee_name}\n"
            f"من: {start_date}\n"
            f"إلى: {end_date}\n\n"
            f"<i>INTEGRA HR System</i>"
        )
        return self.send_message(target, message)

    def notify_task(self, employee_name: str, task_title: str,
                    due_date: str, chat_id: str = "") -> bool:
        """Send task assignment notification."""
        target = chat_id or self._default_chat_id
        message = (
            f"📋 <b>مهمة جديدة</b>\n\n"
            f"المكلف: {employee_name}\n"
            f"المهمة: {task_title}\n"
            f"الموعد النهائي: {due_date}\n\n"
            f"<i>INTEGRA Task System</i>"
        )
        return self.send_message(target, message)

    def notify_system_alert(self, title: str, details: str,
                            priority: AlertPriority = AlertPriority.HIGH) -> bool:
        """Send system alert to admin."""
        message = (
            f"<b>{title}</b>\n\n"
            f"{details}\n\n"
            f"<i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
        )
        return self.send_alert(message, priority)

    # ─── Command Registration ────────────────────────

    def register_command(self, command: str, handler: Callable,
                         description_ar: str = "",
                         description_en: str = ""):
        """Register a command handler."""
        self._command_handlers[command] = handler
        # Update command list
        for cmd in self._commands:
            if cmd.command == command:
                cmd.handler = handler
                return
        self._commands.append(BotCommand(
            command=command,
            description_ar=description_ar,
            description_en=description_en,
            handler=handler,
        ))

    def set_commands(self) -> bool:
        """Set bot commands in Telegram."""
        commands = [
            {"command": cmd.command, "description": cmd.description_en}
            for cmd in self._commands
        ]
        result = self._api_request("setMyCommands", {"commands": commands})
        return result is not None

    # ─── Broadcast ───────────────────────────────────

    def broadcast(self, message: str,
                  chat_type: str = "") -> dict:
        """
        Broadcast message to all active chats.

        Args:
            message: Message text
            chat_type: Filter by chat type (private/group/channel)
        """
        results = {"sent": 0, "failed": 0, "total": 0}

        targets = [
            c for c in self._chats
            if c.is_active and (not chat_type or c.chat_type == chat_type)
        ]
        results["total"] = len(targets)

        for chat in targets:
            success = self.send_message(chat.chat_id, message)
            if success:
                results["sent"] += 1
            else:
                results["failed"] += 1
            time.sleep(self._send_delay)

        app_logger.info(
            f"Broadcast: {results['sent']}/{results['total']} sent"
        )
        return results

    # ─── Status ──────────────────────────────────────

    @property
    def is_configured(self) -> bool:
        """Check if bot is configured."""
        return bool(self._bot_token)

    def get_stats(self) -> dict:
        """Get bot statistics."""
        return {
            "configured": self.is_configured,
            "bot_username": self._bot_username,
            "chats": len(self._chats),
            "commands": len(self._commands),
            "alerts_sent": len([a for a in self._alert_history if a.sent]),
            "alerts_failed": len(
                [a for a in self._alert_history if not a.sent]
            ),
        }

    def get_alert_history(self) -> list[TelegramAlert]:
        """Get alert history."""
        return list(self._alert_history)
