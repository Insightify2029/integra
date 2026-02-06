"""
Desktop Apps Integration
========================
Integration with desktop messaging apps and automation platforms.

Modules:
- WhatsApp Desktop: Send messages and files via WhatsApp Web API
- Telegram Bot: Bot for alerts, queries, and approvals
- Microsoft Teams: Channel notifications and webhooks
- Desktop Automation: Win32 API for desktop app control
"""

from .whatsapp.whatsapp_manager import WhatsAppManager
from .telegram.telegram_bot import TelegramBotManager
from .teams.teams_connector import TeamsConnector
from .automation.desktop_automation import DesktopAutomation

__all__ = [
    'WhatsAppManager',
    'TelegramBotManager',
    'TeamsConnector',
    'DesktopAutomation',
]
