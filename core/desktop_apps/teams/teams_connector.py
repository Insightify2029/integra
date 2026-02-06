"""
Microsoft Teams Integration Connector
=======================================
Integration with Microsoft Teams for channel notifications,
webhook-based messaging, and adaptive cards.

Features:
- Incoming Webhooks for channel notifications
- Adaptive Cards for rich content
- Message formatting (titles, facts, actions)
- Alert routing to specific channels
- File sharing via webhook
- Approval workflow cards
- Status update cards
"""

import os
import json
import time
from enum import Enum
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field, asdict

from core.logging import app_logger


# ═══════════════════════════════════════════════════════
# Data Models
# ═══════════════════════════════════════════════════════

class CardType(Enum):
    """Adaptive Card types."""
    MESSAGE = "message"
    ALERT = "alert"
    APPROVAL = "approval"
    REPORT = "report"
    STATUS = "status"
    TASK = "task"


class ThemeColor(Enum):
    """Teams message theme colors."""
    DEFAULT = "0078D4"   # Microsoft Blue
    SUCCESS = "00C853"   # Green
    WARNING = "FF9800"   # Orange
    ERROR = "FF1744"     # Red
    INFO = "2196F3"      # Light Blue
    PURPLE = "9C27B0"    # Purple


@dataclass
class TeamsChannel:
    """A Teams channel with webhook URL."""
    name: str
    webhook_url: str
    description: str = ""
    is_active: bool = True
    channel_type: str = "general"  # general, alerts, reports, approvals


@dataclass
class TeamsMessage:
    """A Teams message record."""
    id: str = ""
    channel_name: str = ""
    title: str = ""
    content: str = ""
    card_type: CardType = CardType.MESSAGE
    sent: bool = False
    sent_at: str = ""
    error: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"teams_{int(time.time() * 1000)}"


# ═══════════════════════════════════════════════════════
# Adaptive Card Builder
# ═══════════════════════════════════════════════════════

class AdaptiveCardBuilder:
    """
    Build Microsoft Teams Adaptive Cards.

    Supports:
    - Text blocks, facts, images
    - Action buttons (URL, submit)
    - Columns and containers
    - Styling (colors, sizes, weights)
    """

    def __init__(self):
        self._body = []
        self._actions = []

    def add_heading(self, text: str, size: str = "Large",
                    color: str = "Default") -> 'AdaptiveCardBuilder':
        """Add a heading text block."""
        self._body.append({
            "type": "TextBlock",
            "text": text,
            "size": size,
            "weight": "Bolder",
            "color": color,
            "wrap": True,
        })
        return self

    def add_text(self, text: str, size: str = "Default",
                 color: str = "Default",
                 is_subtle: bool = False) -> 'AdaptiveCardBuilder':
        """Add a text block."""
        self._body.append({
            "type": "TextBlock",
            "text": text,
            "size": size,
            "color": color,
            "isSubtle": is_subtle,
            "wrap": True,
        })
        return self

    def add_fact_set(self, facts: dict) -> 'AdaptiveCardBuilder':
        """Add a fact set (key-value pairs)."""
        self._body.append({
            "type": "FactSet",
            "facts": [
                {"title": k, "value": v} for k, v in facts.items()
            ],
        })
        return self

    def add_separator(self) -> 'AdaptiveCardBuilder':
        """Add a separator."""
        self._body.append({
            "type": "TextBlock",
            "text": " ",
            "separator": True,
        })
        return self

    def add_image(self, url: str, alt_text: str = "",
                  size: str = "Auto") -> 'AdaptiveCardBuilder':
        """Add an image."""
        self._body.append({
            "type": "Image",
            "url": url,
            "altText": alt_text,
            "size": size,
        })
        return self

    def add_columns(self, columns: list[dict]) -> 'AdaptiveCardBuilder':
        """
        Add a column set.

        Each column dict: {"width": "auto|stretch", "items": [...]}
        """
        col_set = {
            "type": "ColumnSet",
            "columns": [
                {
                    "type": "Column",
                    "width": col.get("width", "stretch"),
                    "items": col.get("items", []),
                }
                for col in columns
            ],
        }
        self._body.append(col_set)
        return self

    def add_action_url(self, title: str, url: str) -> 'AdaptiveCardBuilder':
        """Add a URL action button."""
        self._actions.append({
            "type": "Action.OpenUrl",
            "title": title,
            "url": url,
        })
        return self

    def add_action_submit(self, title: str,
                          data: dict = None) -> 'AdaptiveCardBuilder':
        """Add a submit action button."""
        action = {
            "type": "Action.Submit",
            "title": title,
        }
        if data:
            action["data"] = data
        self._actions.append(action)
        return self

    def build(self) -> dict:
        """Build the Adaptive Card JSON."""
        card = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.4",
            "body": self._body,
        }
        if self._actions:
            card["actions"] = self._actions
        return card

    def build_payload(self) -> dict:
        """Build the full webhook payload with Adaptive Card."""
        return {
            "type": "message",
            "attachments": [
                {
                    "contentType":
                        "application/vnd.microsoft.card.adaptive",
                    "content": self.build(),
                }
            ],
        }


# ═══════════════════════════════════════════════════════
# Teams Connector
# ═══════════════════════════════════════════════════════

class TeamsConnector:
    """
    Microsoft Teams integration connector.

    Uses Incoming Webhooks to send notifications, alerts,
    and interactive cards to Teams channels.

    Provides:
    - Channel management with webhook URLs
    - Send text and Adaptive Card messages
    - Pre-built card templates (alerts, approvals, reports)
    - Alert routing by type
    - Message history
    """

    def __init__(self, config_path: str = ""):
        self._config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            ))),
            "config", "teams_config.json"
        )
        self._channels: list[TeamsChannel] = []
        self._message_history: list[TeamsMessage] = []
        self._default_channel = ""
        self._send_delay = 1.0

        # Channel routing by type
        self._routing = {
            "alerts": "",
            "reports": "",
            "approvals": "",
            "general": "",
        }

        self._load_config()

        app_logger.info("Teams Connector initialized")

    # ─── Configuration ───────────────────────────────

    def _load_config(self):
        """Load configuration from file."""
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                self._default_channel = config.get("default_channel", "")
                self._send_delay = config.get("send_delay", 1.0)
                self._routing = config.get("routing", self._routing)

                for ch in config.get("channels", []):
                    self._channels.append(TeamsChannel(**ch))

                app_logger.debug("Teams config loaded")
            except Exception as e:
                app_logger.error(f"Error loading Teams config: {e}")

    def save_config(self):
        """Save configuration to file."""
        config = {
            "default_channel": self._default_channel,
            "send_delay": self._send_delay,
            "routing": self._routing,
            "channels": [asdict(c) for c in self._channels],
        }
        try:
            os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            app_logger.debug("Teams config saved")
        except Exception as e:
            app_logger.error(f"Error saving Teams config: {e}")

    # ─── Channel Management ──────────────────────────

    def add_channel(self, name: str, webhook_url: str,
                    description: str = "",
                    channel_type: str = "general") -> TeamsChannel:
        """Add a Teams channel."""
        channel = TeamsChannel(
            name=name,
            webhook_url=webhook_url,
            description=description,
            channel_type=channel_type,
        )
        self._channels.append(channel)
        app_logger.info(f"Teams channel added: {name}")
        return channel

    def remove_channel(self, name: str):
        """Remove a channel by name."""
        self._channels = [c for c in self._channels if c.name != name]

    def get_channels(self) -> list[TeamsChannel]:
        """Get all channels."""
        return list(self._channels)

    def get_channel(self, name: str) -> Optional[TeamsChannel]:
        """Get a channel by name."""
        for ch in self._channels:
            if ch.name == name:
                return ch
        return None

    def _get_webhook_url(self, channel_name: str = "",
                         channel_type: str = "") -> str:
        """Get webhook URL for a channel."""
        # Try specific channel name
        if channel_name:
            ch = self.get_channel(channel_name)
            if ch and ch.is_active:
                return ch.webhook_url

        # Try routing by type
        if channel_type and self._routing.get(channel_type):
            routed_name = self._routing[channel_type]
            ch = self.get_channel(routed_name)
            if ch and ch.is_active:
                return ch.webhook_url

        # Fallback to default
        if self._default_channel:
            ch = self.get_channel(self._default_channel)
            if ch and ch.is_active:
                return ch.webhook_url

        # Last resort: first active channel
        for ch in self._channels:
            if ch.is_active:
                return ch.webhook_url

        return ""

    # ─── Sending ─────────────────────────────────────

    def _send_webhook(self, webhook_url: str,
                      payload: dict) -> bool:
        """Send payload to a webhook URL."""
        if not webhook_url:
            app_logger.error("No webhook URL provided")
            return False

        try:
            import requests
        except ImportError:
            app_logger.error("requests library not available")
            return False

        try:
            response = requests.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            if response.status_code == 200:
                return True
            else:
                app_logger.error(
                    f"Teams webhook error: {response.status_code} - "
                    f"{response.text}"
                )
                return False
        except Exception as e:
            app_logger.error(f"Teams webhook request failed: {e}")
            return False

    def send_text(self, text: str, channel_name: str = "",
                  title: str = "",
                  color: ThemeColor = ThemeColor.DEFAULT) -> bool:
        """
        Send a simple text message to a channel.

        Uses MessageCard format for backward compatibility.
        """
        webhook_url = self._get_webhook_url(
            channel_name=channel_name, channel_type="general"
        )

        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": color.value,
            "text": text,
        }
        if title:
            payload["title"] = title

        msg = TeamsMessage(
            channel_name=channel_name or self._default_channel,
            title=title,
            content=text,
            card_type=CardType.MESSAGE,
        )

        success = self._send_webhook(webhook_url, payload)

        msg.sent = success
        if success:
            msg.sent_at = datetime.now().isoformat()
        self._message_history.append(msg)

        return success

    def send_card(self, card_builder: AdaptiveCardBuilder,
                  channel_name: str = "",
                  channel_type: str = "general") -> bool:
        """Send an Adaptive Card to a channel."""
        webhook_url = self._get_webhook_url(
            channel_name=channel_name, channel_type=channel_type
        )
        payload = card_builder.build_payload()
        return self._send_webhook(webhook_url, payload)

    # ─── Pre-built Card Templates ────────────────────

    def send_alert(self, title: str, message: str,
                   severity: str = "info",
                   channel_name: str = "") -> bool:
        """
        Send an alert card.

        severity: info, warning, error, critical
        """
        color_map = {
            "info": "Accent",
            "warning": "Warning",
            "error": "Attention",
            "critical": "Attention",
        }
        theme_map = {
            "info": ThemeColor.INFO,
            "warning": ThemeColor.WARNING,
            "error": ThemeColor.ERROR,
            "critical": ThemeColor.ERROR,
        }
        emoji_map = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🚨",
        }

        card = AdaptiveCardBuilder()
        card.add_heading(
            f"{emoji_map.get(severity, '')} {title}",
            color=color_map.get(severity, "Default")
        )
        card.add_text(message)
        card.add_separator()
        card.add_text(
            f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            size="Small",
            is_subtle=True,
        )

        webhook_url = self._get_webhook_url(
            channel_name=channel_name, channel_type="alerts"
        )
        payload = card.build_payload()

        msg = TeamsMessage(
            channel_name=channel_name,
            title=title,
            content=message,
            card_type=CardType.ALERT,
        )

        success = self._send_webhook(webhook_url, payload)
        msg.sent = success
        if success:
            msg.sent_at = datetime.now().isoformat()
        self._message_history.append(msg)
        return success

    def send_approval_card(self, title: str, details: dict,
                           request_id: str,
                           approve_url: str = "",
                           reject_url: str = "",
                           channel_name: str = "") -> bool:
        """
        Send an approval request card with action buttons.
        """
        card = AdaptiveCardBuilder()
        card.add_heading(f"📋 طلب موافقة: {title}")
        card.add_separator()
        card.add_fact_set(details)
        card.add_separator()
        card.add_text(
            f"الرقم المرجعي: {request_id}",
            size="Small",
            is_subtle=True,
        )

        if approve_url:
            card.add_action_url("✅ موافقة", approve_url)
        if reject_url:
            card.add_action_url("❌ رفض", reject_url)

        webhook_url = self._get_webhook_url(
            channel_name=channel_name, channel_type="approvals"
        )

        msg = TeamsMessage(
            channel_name=channel_name,
            title=title,
            card_type=CardType.APPROVAL,
        )

        success = self._send_webhook(webhook_url, card.build_payload())
        msg.sent = success
        if success:
            msg.sent_at = datetime.now().isoformat()
        self._message_history.append(msg)
        return success

    def send_report_card(self, report_name: str,
                         summary: dict,
                         download_url: str = "",
                         channel_name: str = "") -> bool:
        """Send a report summary card."""
        card = AdaptiveCardBuilder()
        card.add_heading(f"📊 تقرير: {report_name}")
        card.add_separator()
        card.add_fact_set(summary)
        card.add_separator()
        card.add_text(
            f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d')}",
            size="Small",
            is_subtle=True,
        )

        if download_url:
            card.add_action_url("📥 تحميل التقرير", download_url)

        webhook_url = self._get_webhook_url(
            channel_name=channel_name, channel_type="reports"
        )

        msg = TeamsMessage(
            channel_name=channel_name,
            title=report_name,
            card_type=CardType.REPORT,
        )

        success = self._send_webhook(webhook_url, card.build_payload())
        msg.sent = success
        if success:
            msg.sent_at = datetime.now().isoformat()
        self._message_history.append(msg)
        return success

    def send_status_card(self, system_name: str,
                         status_items: dict,
                         overall_status: str = "healthy",
                         channel_name: str = "") -> bool:
        """Send a system status card."""
        status_emoji = {
            "healthy": "🟢",
            "degraded": "🟡",
            "down": "🔴",
        }
        emoji = status_emoji.get(overall_status, "⚪")

        card = AdaptiveCardBuilder()
        card.add_heading(f"{emoji} حالة النظام: {system_name}")
        card.add_separator()
        card.add_fact_set(status_items)
        card.add_separator()
        card.add_text(
            f"آخر تحديث: {datetime.now().strftime('%H:%M:%S')}",
            size="Small",
            is_subtle=True,
        )

        webhook_url = self._get_webhook_url(
            channel_name=channel_name, channel_type="general"
        )

        msg = TeamsMessage(
            channel_name=channel_name,
            title=f"Status: {system_name}",
            card_type=CardType.STATUS,
        )

        success = self._send_webhook(webhook_url, card.build_payload())
        msg.sent = success
        if success:
            msg.sent_at = datetime.now().isoformat()
        self._message_history.append(msg)
        return success

    def send_task_card(self, task_title: str, assignee: str,
                       due_date: str, priority: str = "normal",
                       details: str = "",
                       channel_name: str = "") -> bool:
        """Send a task assignment card."""
        priority_emoji = {
            "low": "🔵",
            "normal": "🟢",
            "high": "🟡",
            "urgent": "🔴",
        }
        emoji = priority_emoji.get(priority, "⚪")

        card = AdaptiveCardBuilder()
        card.add_heading(f"📋 مهمة جديدة: {task_title}")
        card.add_separator()

        facts = {
            "المكلف": assignee,
            "الأولوية": f"{emoji} {priority}",
            "الموعد النهائي": due_date,
        }
        if details:
            facts["التفاصيل"] = details

        card.add_fact_set(facts)

        webhook_url = self._get_webhook_url(
            channel_name=channel_name, channel_type="general"
        )

        msg = TeamsMessage(
            channel_name=channel_name,
            title=task_title,
            card_type=CardType.TASK,
        )

        success = self._send_webhook(webhook_url, card.build_payload())
        msg.sent = success
        if success:
            msg.sent_at = datetime.now().isoformat()
        self._message_history.append(msg)
        return success

    # ─── Broadcast ───────────────────────────────────

    def broadcast(self, text: str, title: str = "",
                  channel_type: str = "") -> dict:
        """Broadcast a message to all active channels."""
        results = {"sent": 0, "failed": 0, "total": 0}

        targets = [
            ch for ch in self._channels
            if ch.is_active and (
                not channel_type or ch.channel_type == channel_type
            )
        ]
        results["total"] = len(targets)

        for ch in targets:
            success = self.send_text(text, channel_name=ch.name, title=title)
            if success:
                results["sent"] += 1
            else:
                results["failed"] += 1
            time.sleep(self._send_delay)

        return results

    # ─── Status ──────────────────────────────────────

    @property
    def is_configured(self) -> bool:
        """Check if any channel is configured."""
        return len(self._channels) > 0

    def test_connection(self, channel_name: str = "") -> bool:
        """Test webhook connection by sending a test card."""
        return self.send_text(
            "✅ INTEGRA Teams integration test successful!",
            channel_name=channel_name,
            title="Test Connection",
            color=ThemeColor.SUCCESS,
        )

    def get_stats(self) -> dict:
        """Get connector statistics."""
        return {
            "configured": self.is_configured,
            "channels": len(self._channels),
            "active_channels": len(
                [c for c in self._channels if c.is_active]
            ),
            "messages_sent": len(
                [m for m in self._message_history if m.sent]
            ),
            "messages_failed": len(
                [m for m in self._message_history if not m.sent]
            ),
        }

    def get_message_history(self) -> list[TeamsMessage]:
        """Get message history."""
        return list(self._message_history)
