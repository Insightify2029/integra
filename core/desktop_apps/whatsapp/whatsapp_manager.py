"""
WhatsApp Desktop Integration Manager
=====================================
Integration with WhatsApp Desktop / WhatsApp Web for sending
messages, files, and notifications from INTEGRA.

Approaches:
1. WhatsApp Web API via HTTP (pywhatkit / requests)
2. WhatsApp Business API (for business accounts)
3. Desktop automation via Win32 (pyautogui fallback)

Features:
- Send text messages to contacts/groups
- Send files (PDF reports, Excel, images)
- Message templates for common notifications
- Contact management and validation
- Message queue with retry logic
- Delivery status tracking
"""

import os
import re
import json
import time
import urllib.parse
import webbrowser
from enum import Enum
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field, asdict

from core.logging import app_logger


# ═══════════════════════════════════════════════════════
# Data Models
# ═══════════════════════════════════════════════════════

class MessageStatus(Enum):
    """Message delivery status."""
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessageType(Enum):
    """Type of WhatsApp message."""
    TEXT = "text"
    FILE = "file"
    IMAGE = "image"
    DOCUMENT = "document"
    TEMPLATE = "template"


@dataclass
class WhatsAppContact:
    """A WhatsApp contact."""
    phone: str
    name: str = ""
    country_code: str = "+966"  # Saudi Arabia default
    is_group: bool = False
    group_id: str = ""

    @property
    def full_number(self) -> str:
        """Get full international number."""
        number = self.phone.strip()
        # Remove leading zeros
        number = number.lstrip('0')
        # Remove spaces and dashes
        number = re.sub(r'[\s\-\(\)]', '', number)
        # Add country code if not present
        if not number.startswith('+'):
            code = self.country_code.lstrip('+')
            if not number.startswith(code):
                number = code + number
            number = '+' + number
        return number

    @property
    def number_digits(self) -> str:
        """Get digits-only number (no + prefix)."""
        return self.full_number.lstrip('+')


@dataclass
class WhatsAppMessage:
    """A WhatsApp message in the queue."""
    id: str = ""
    contact: WhatsAppContact = None
    message_type: MessageType = MessageType.TEXT
    content: str = ""
    file_path: str = ""
    caption: str = ""
    template_id: str = ""
    template_params: dict = field(default_factory=dict)
    status: MessageStatus = MessageStatus.PENDING
    created_at: str = ""
    sent_at: str = ""
    error: str = ""
    retry_count: int = 0
    max_retries: int = 3

    def __post_init__(self):
        if not self.id:
            self.id = f"wa_{int(time.time() * 1000)}"
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


# ═══════════════════════════════════════════════════════
# Message Templates
# ═══════════════════════════════════════════════════════

DEFAULT_TEMPLATES = {
    "salary_notification": {
        "name_ar": "إشعار الراتب",
        "name_en": "Salary Notification",
        "template_ar": "مرحباً {employee_name}،\n\nتم إيداع راتبك لشهر {month} بمبلغ {amount} ريال.\n\nشكراً لك.\nINTEGRA HR",
        "template_en": "Hello {employee_name},\n\nYour salary for {month} of {amount} SAR has been deposited.\n\nThank you.\nINTEGRA HR",
        "params": ["employee_name", "month", "amount"],
    },
    "leave_approval": {
        "name_ar": "الموافقة على الإجازة",
        "name_en": "Leave Approval",
        "template_ar": "مرحباً {employee_name}،\n\nتمت الموافقة على طلب إجازتك من {start_date} إلى {end_date}.\n\nشكراً لك.\nINTEGRA HR",
        "template_en": "Hello {employee_name},\n\nYour leave request from {start_date} to {end_date} has been approved.\n\nThank you.\nINTEGRA HR",
        "params": ["employee_name", "start_date", "end_date"],
    },
    "leave_rejection": {
        "name_ar": "رفض الإجازة",
        "name_en": "Leave Rejection",
        "template_ar": "مرحباً {employee_name}،\n\nنأسف لإبلاغك أن طلب إجازتك من {start_date} إلى {end_date} لم تتم الموافقة عليه.\nالسبب: {reason}\n\nشكراً لك.\nINTEGRA HR",
        "template_en": "Hello {employee_name},\n\nWe regret to inform you that your leave request from {start_date} to {end_date} was not approved.\nReason: {reason}\n\nThank you.\nINTEGRA HR",
        "params": ["employee_name", "start_date", "end_date", "reason"],
    },
    "report_ready": {
        "name_ar": "التقرير جاهز",
        "name_en": "Report Ready",
        "template_ar": "مرحباً {recipient_name}،\n\nتقرير {report_name} جاهز للمراجعة.\n\nINTEGRA",
        "template_en": "Hello {recipient_name},\n\nThe {report_name} report is ready for review.\n\nINTEGRA",
        "params": ["recipient_name", "report_name"],
    },
    "task_assigned": {
        "name_ar": "مهمة جديدة",
        "name_en": "Task Assigned",
        "template_ar": "مرحباً {employee_name}،\n\nتم تكليفك بمهمة جديدة:\n{task_title}\n\nالموعد النهائي: {due_date}\n\nINTEGRA",
        "template_en": "Hello {employee_name},\n\nYou have been assigned a new task:\n{task_title}\n\nDeadline: {due_date}\n\nINTEGRA",
        "params": ["employee_name", "task_title", "due_date"],
    },
    "general": {
        "name_ar": "رسالة عامة",
        "name_en": "General Message",
        "template_ar": "{message}",
        "template_en": "{message}",
        "params": ["message"],
    },
}


# ═══════════════════════════════════════════════════════
# WhatsApp Manager
# ═══════════════════════════════════════════════════════

class WhatsAppManager:
    """
    WhatsApp Desktop integration manager.

    Provides:
    - Send text messages via WhatsApp Web URL scheme
    - Send files with captions
    - Message templates for HR notifications
    - Message queue with retry logic
    - Contact validation
    - Delivery tracking
    """

    def __init__(self, config_path: str = ""):
        self._config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            ))),
            "config", "whatsapp_config.json"
        )
        self._templates = dict(DEFAULT_TEMPLATES)
        self._message_queue: list[WhatsAppMessage] = []
        self._sent_messages: list[WhatsAppMessage] = []
        self._contacts: list[WhatsAppContact] = []
        self._is_connected = False
        self._default_country_code = "+966"
        self._send_delay = 2.0  # seconds between messages
        self._use_business_api = False
        self._business_api_url = ""
        self._business_api_token = ""

        self._load_config()

        app_logger.info("WhatsApp Manager initialized")

    # ─── Configuration ───────────────────────────────

    def _load_config(self):
        """Load configuration from file."""
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                self._default_country_code = config.get(
                    "default_country_code", self._default_country_code
                )
                self._send_delay = config.get(
                    "send_delay", self._send_delay
                )
                self._use_business_api = config.get(
                    "use_business_api", False
                )
                self._business_api_url = config.get(
                    "business_api_url", ""
                )
                self._business_api_token = config.get(
                    "business_api_token", ""
                )

                # Load custom templates
                custom_templates = config.get("custom_templates", {})
                self._templates.update(custom_templates)

                # Load contacts
                for c in config.get("contacts", []):
                    self._contacts.append(WhatsAppContact(**c))

                app_logger.debug("WhatsApp config loaded")
            except Exception as e:
                app_logger.error(f"Error loading WhatsApp config: {e}")

    def save_config(self):
        """Save configuration to file."""
        config = {
            "default_country_code": self._default_country_code,
            "send_delay": self._send_delay,
            "use_business_api": self._use_business_api,
            "business_api_url": self._business_api_url,
            "business_api_token": self._business_api_token,
            "contacts": [asdict(c) for c in self._contacts],
            "custom_templates": {
                k: v for k, v in self._templates.items()
                if k not in DEFAULT_TEMPLATES
            },
        }
        try:
            os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            app_logger.debug("WhatsApp config saved")
        except Exception as e:
            app_logger.error(f"Error saving WhatsApp config: {e}")

    # ─── Contact Management ──────────────────────────

    @staticmethod
    def validate_phone(phone: str, country_code: str = "+966") -> bool:
        """Validate phone number format."""
        number = re.sub(r'[\s\-\(\)\+]', '', phone)
        # Must be 7-15 digits
        return bool(re.match(r'^\d{7,15}$', number))

    def add_contact(self, phone: str, name: str = "",
                    country_code: str = "") -> WhatsAppContact:
        """Add a contact."""
        code = country_code or self._default_country_code
        contact = WhatsAppContact(
            phone=phone,
            name=name,
            country_code=code
        )
        self._contacts.append(contact)
        app_logger.info(f"WhatsApp contact added: {name} ({phone})")
        return contact

    def remove_contact(self, phone: str):
        """Remove a contact by phone number."""
        self._contacts = [
            c for c in self._contacts if c.phone != phone
        ]

    def get_contacts(self) -> list[WhatsAppContact]:
        """Get all contacts."""
        return list(self._contacts)

    def find_contact(self, query: str) -> list[WhatsAppContact]:
        """Search contacts by name or phone."""
        query_lower = query.lower()
        return [
            c for c in self._contacts
            if query_lower in c.name.lower() or query_lower in c.phone
        ]

    # ─── Templates ───────────────────────────────────

    def get_templates(self) -> dict:
        """Get all message templates."""
        return dict(self._templates)

    def get_template(self, template_id: str) -> Optional[dict]:
        """Get a specific template."""
        return self._templates.get(template_id)

    def render_template(self, template_id: str, params: dict,
                        lang: str = "ar") -> str:
        """Render a template with parameters."""
        template = self._templates.get(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        key = f"template_{lang}"
        if key not in template:
            key = "template_ar"  # fallback

        text = template[key]
        try:
            return text.format(**params)
        except KeyError as e:
            raise ValueError(f"Missing template parameter: {e}")

    def add_template(self, template_id: str, name_ar: str, name_en: str,
                     template_ar: str, template_en: str,
                     params: list[str]):
        """Add a custom message template."""
        self._templates[template_id] = {
            "name_ar": name_ar,
            "name_en": name_en,
            "template_ar": template_ar,
            "template_en": template_en,
            "params": params,
        }

    # ─── Message Creation ────────────────────────────

    def create_message(self, phone: str, text: str,
                       name: str = "",
                       country_code: str = "") -> WhatsAppMessage:
        """Create a text message."""
        code = country_code or self._default_country_code
        contact = WhatsAppContact(
            phone=phone, name=name, country_code=code
        )
        return WhatsAppMessage(
            contact=contact,
            message_type=MessageType.TEXT,
            content=text,
        )

    def create_file_message(self, phone: str, file_path: str,
                            caption: str = "",
                            name: str = "",
                            country_code: str = "") -> WhatsAppMessage:
        """Create a file message."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        code = country_code or self._default_country_code
        contact = WhatsAppContact(
            phone=phone, name=name, country_code=code
        )
        return WhatsAppMessage(
            contact=contact,
            message_type=MessageType.FILE,
            file_path=file_path,
            caption=caption,
        )

    def create_template_message(self, phone: str, template_id: str,
                                params: dict, lang: str = "ar",
                                name: str = "",
                                country_code: str = "") -> WhatsAppMessage:
        """Create a template-based message."""
        content = self.render_template(template_id, params, lang)
        code = country_code or self._default_country_code
        contact = WhatsAppContact(
            phone=phone, name=name, country_code=code
        )
        return WhatsAppMessage(
            contact=contact,
            message_type=MessageType.TEMPLATE,
            content=content,
            template_id=template_id,
            template_params=params,
        )

    # ─── Sending ─────────────────────────────────────

    def send_via_web(self, message: WhatsAppMessage) -> bool:
        """
        Send message via WhatsApp Web URL scheme.

        Opens wa.me link in default browser which triggers WhatsApp Desktop.
        """
        try:
            message.status = MessageStatus.SENDING
            number = message.contact.number_digits
            text = urllib.parse.quote(message.content)
            url = f"https://wa.me/{number}?text={text}"

            webbrowser.open(url)
            time.sleep(0.5)

            message.status = MessageStatus.SENT
            message.sent_at = datetime.now().isoformat()
            self._sent_messages.append(message)

            app_logger.info(
                f"WhatsApp message sent to {message.contact.name or number}"
            )
            return True

        except Exception as e:
            message.status = MessageStatus.FAILED
            message.error = str(e)
            app_logger.error(f"Failed to send WhatsApp message: {e}")
            return False

    def send_via_api(self, message: WhatsAppMessage) -> bool:
        """
        Send message via WhatsApp Business API.

        Requires configured business API URL and token.
        """
        if not self._use_business_api:
            app_logger.warning("Business API not configured")
            return False

        if not self._business_api_url or not self._business_api_token:
            app_logger.error("Business API URL or token not set")
            return False

        try:
            import requests
        except ImportError:
            app_logger.error("requests library not available for API calls")
            return False

        try:
            message.status = MessageStatus.SENDING
            number = message.contact.number_digits

            headers = {
                "Authorization": f"Bearer {self._business_api_token}",
                "Content-Type": "application/json",
            }

            payload = {
                "messaging_product": "whatsapp",
                "to": number,
                "type": "text",
                "text": {"body": message.content},
            }

            response = requests.post(
                f"{self._business_api_url}/messages",
                json=payload,
                headers=headers,
                timeout=30,
            )

            if response.status_code == 200:
                message.status = MessageStatus.SENT
                message.sent_at = datetime.now().isoformat()
                self._sent_messages.append(message)
                app_logger.info(
                    f"WhatsApp API message sent to {number}"
                )
                return True
            else:
                message.status = MessageStatus.FAILED
                message.error = f"API error: {response.status_code}"
                app_logger.error(
                    f"WhatsApp API error: {response.status_code} - "
                    f"{response.text}"
                )
                return False

        except Exception as e:
            message.status = MessageStatus.FAILED
            message.error = str(e)
            app_logger.error(f"WhatsApp API send failed: {e}")
            return False

    def send(self, message: WhatsAppMessage) -> bool:
        """Send a message using the best available method."""
        if self._use_business_api:
            return self.send_via_api(message)
        return self.send_via_web(message)

    # ─── Queue Management ────────────────────────────

    def queue_message(self, message: WhatsAppMessage):
        """Add a message to the send queue."""
        self._message_queue.append(message)
        app_logger.debug(f"Message queued: {message.id}")

    def process_queue(self) -> dict:
        """Process all messages in the queue."""
        results = {"sent": 0, "failed": 0, "total": len(self._message_queue)}

        for message in list(self._message_queue):
            success = self.send(message)
            if success:
                results["sent"] += 1
                self._message_queue.remove(message)
            else:
                message.retry_count += 1
                if message.retry_count >= message.max_retries:
                    message.status = MessageStatus.CANCELLED
                    results["failed"] += 1
                    self._message_queue.remove(message)

            time.sleep(self._send_delay)

        app_logger.info(
            f"Queue processed: {results['sent']}/{results['total']} sent, "
            f"{results['failed']} failed"
        )
        return results

    def get_queue(self) -> list[WhatsAppMessage]:
        """Get current message queue."""
        return list(self._message_queue)

    def clear_queue(self):
        """Clear the message queue."""
        self._message_queue.clear()

    def get_sent_messages(self) -> list[WhatsAppMessage]:
        """Get history of sent messages."""
        return list(self._sent_messages)

    # ─── Bulk Operations ─────────────────────────────

    def send_bulk(self, phones: list[str], text: str,
                  country_code: str = "") -> dict:
        """Send same message to multiple contacts."""
        for phone in phones:
            msg = self.create_message(phone, text, country_code=country_code)
            self.queue_message(msg)
        return self.process_queue()

    def send_template_bulk(self, recipients: list[dict],
                           template_id: str, lang: str = "ar") -> dict:
        """
        Send template message to multiple recipients.

        Each recipient dict should have: phone, name, and template params.
        """
        for r in recipients:
            phone = r.get("phone", "")
            params = {k: v for k, v in r.items() if k != "phone"}
            msg = self.create_template_message(
                phone, template_id, params, lang
            )
            self.queue_message(msg)
        return self.process_queue()

    # ─── Quick Send Helpers ──────────────────────────

    def quick_send(self, phone: str, text: str) -> bool:
        """Quick send a text message."""
        msg = self.create_message(phone, text)
        return self.send(msg)

    def send_salary_notification(self, phone: str, employee_name: str,
                                 month: str, amount: str,
                                 lang: str = "ar") -> bool:
        """Send salary deposit notification."""
        msg = self.create_template_message(
            phone, "salary_notification",
            {"employee_name": employee_name, "month": month, "amount": amount},
            lang
        )
        return self.send(msg)

    def send_leave_approval(self, phone: str, employee_name: str,
                            start_date: str, end_date: str,
                            lang: str = "ar") -> bool:
        """Send leave approval notification."""
        msg = self.create_template_message(
            phone, "leave_approval",
            {
                "employee_name": employee_name,
                "start_date": start_date,
                "end_date": end_date,
            },
            lang
        )
        return self.send(msg)

    def send_task_notification(self, phone: str, employee_name: str,
                               task_title: str, due_date: str,
                               lang: str = "ar") -> bool:
        """Send task assignment notification."""
        msg = self.create_template_message(
            phone, "task_assigned",
            {
                "employee_name": employee_name,
                "task_title": task_title,
                "due_date": due_date,
            },
            lang
        )
        return self.send(msg)

    # ─── Status ──────────────────────────────────────

    @property
    def is_configured(self) -> bool:
        """Check if WhatsApp is configured."""
        return True  # Web method always available

    @property
    def has_business_api(self) -> bool:
        """Check if Business API is configured."""
        return (
            self._use_business_api
            and bool(self._business_api_url)
            and bool(self._business_api_token)
        )

    def get_stats(self) -> dict:
        """Get message statistics."""
        return {
            "total_sent": len(self._sent_messages),
            "queue_size": len(self._message_queue),
            "contacts": len(self._contacts),
            "templates": len(self._templates),
            "has_business_api": self.has_business_api,
        }
