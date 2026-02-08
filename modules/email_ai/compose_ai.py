"""
G3: Email Compose AI
====================
كتابة الإيميل بالذكاء الاصطناعي.

Features:
- إنشاء رد تلقائي على إيميل
- تحسين صياغة الإيميل
- ترجمة ذكية (عربي ↔ إنجليزي)
- قوالب ذكية حسب السياق
- تعديل النبرة (رسمي/ودي/احترافي)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
import threading

from core.logging import app_logger

try:
    from core.ai import get_ollama_client, is_ollama_available
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

try:
    from core.email import Email
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    Email = None


class ReplyTone(Enum):
    """نبرة الرد"""
    FORMAL = "formal"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    BRIEF = "brief"
    DETAILED = "detailed"
    APOLOGETIC = "apologetic"
    GRATEFUL = "grateful"

    @property
    def label_ar(self) -> str:
        labels = {
            "formal": "رسمي",
            "professional": "احترافي",
            "friendly": "ودي",
            "brief": "مختصر",
            "detailed": "تفصيلي",
            "apologetic": "اعتذاري",
            "grateful": "شكر وتقدير",
        }
        return labels.get(self.value, "احترافي")

    @property
    def instruction_ar(self) -> str:
        instructions = {
            "formal": "اكتب بأسلوب رسمي جداً مع ألقاب وتحيات رسمية",
            "professional": "اكتب بأسلوب احترافي مهذب ومباشر",
            "friendly": "اكتب بأسلوب ودي وغير رسمي",
            "brief": "اكتب رداً مختصراً جداً في 2-3 جمل",
            "detailed": "اكتب رداً تفصيلياً يغطي كل النقاط",
            "apologetic": "اكتب رداً اعتذارياً مع تعهد بالتحسين",
            "grateful": "اكتب رداً يعبر عن الشكر والتقدير",
        }
        return instructions.get(self.value, "اكتب بأسلوب احترافي")


class TemplateType(Enum):
    """أنواع القوالب"""
    ACKNOWLEDGMENT = "acknowledgment"
    MEETING_ACCEPT = "meeting_accept"
    MEETING_DECLINE = "meeting_decline"
    TASK_COMPLETION = "task_completion"
    LEAVE_REQUEST = "leave_request"
    FOLLOW_UP = "follow_up"
    INTRODUCTION = "introduction"
    APOLOGY = "apology"
    ESCALATION = "escalation"
    THANK_YOU = "thank_you"

    @property
    def label_ar(self) -> str:
        labels = {
            "acknowledgment": "تأكيد استلام",
            "meeting_accept": "قبول اجتماع",
            "meeting_decline": "اعتذار عن اجتماع",
            "task_completion": "إتمام مهمة",
            "leave_request": "طلب إجازة",
            "follow_up": "متابعة",
            "introduction": "تعريف",
            "apology": "اعتذار",
            "escalation": "تصعيد",
            "thank_you": "شكر",
        }
        return labels.get(self.value, "قالب")


@dataclass
class ComposedEmail:
    """إيميل مُنشأ أو محسّن"""
    subject: str = ""
    body: str = ""
    tone: ReplyTone = ReplyTone.PROFESSIONAL
    language: str = "ar"
    is_reply: bool = False
    original_email_id: Optional[str] = None
    template_used: Optional[TemplateType] = None
    generated_at: Optional[datetime] = None


# Built-in templates
EMAIL_TEMPLATES: Dict[TemplateType, Dict[str, str]] = {
    TemplateType.ACKNOWLEDGMENT: {
        "ar": """السلام عليكم ورحمة الله وبركاته،

تم استلام رسالتكم بخصوص "{subject}" وسيتم مراجعتها والرد عليكم في أقرب وقت.

مع التحية،
{sender_name}""",
        "en": """Dear {recipient},

Thank you for your email regarding "{subject}". I acknowledge receipt and will review it promptly.

Best regards,
{sender_name}""",
    },
    TemplateType.MEETING_ACCEPT: {
        "ar": """السلام عليكم،

شكراً لدعوتكم. أؤكد حضوري للاجتماع بخصوص "{subject}".

{meeting_details}

مع التحية،
{sender_name}""",
        "en": """Dear {recipient},

Thank you for the invitation. I confirm my attendance for the meeting regarding "{subject}".

{meeting_details}

Best regards,
{sender_name}""",
    },
    TemplateType.MEETING_DECLINE: {
        "ar": """السلام عليكم،

شكراً لدعوتكم. أعتذر عن عدم تمكني من حضور الاجتماع بخصوص "{subject}" نظراً لارتباط سابق.

هل يمكن اقتراح موعد بديل؟

مع التحية،
{sender_name}""",
        "en": """Dear {recipient},

Thank you for the invitation. Unfortunately, I am unable to attend the meeting regarding "{subject}" due to a prior commitment.

Could we reschedule to an alternative time?

Best regards,
{sender_name}""",
    },
    TemplateType.TASK_COMPLETION: {
        "ar": """السلام عليكم،

أفيدكم بأنه تم الانتهاء من المهمة المطلوبة بخصوص "{subject}".

{task_details}

في حال وجود أي ملاحظات أو تعديلات، أرجو إفادتي.

مع التحية،
{sender_name}""",
        "en": """Dear {recipient},

I am pleased to inform you that the requested task regarding "{subject}" has been completed.

{task_details}

Please let me know if there are any comments or modifications needed.

Best regards,
{sender_name}""",
    },
    TemplateType.LEAVE_REQUEST: {
        "ar": """السلام عليكم،

أتقدم بطلب إجازة {leave_type} لمدة {leave_days} أيام، من تاريخ {start_date} إلى {end_date}.

السبب: {reason}

أرجو الموافقة والاعتماد.

مع التحية،
{sender_name}""",
        "en": """Dear {recipient},

I would like to request {leave_type} leave for {leave_days} days, from {start_date} to {end_date}.

Reason: {reason}

I kindly request your approval.

Best regards,
{sender_name}""",
    },
    TemplateType.FOLLOW_UP: {
        "ar": """السلام عليكم،

أود المتابعة بخصوص الرسالة السابقة حول "{subject}".

هل هناك أي تحديث؟

مع التحية،
{sender_name}""",
        "en": """Dear {recipient},

I would like to follow up on my previous email regarding "{subject}".

Is there any update?

Best regards,
{sender_name}""",
    },
    TemplateType.APOLOGY: {
        "ar": """السلام عليكم،

أعتذر عن {apology_reason}. نعمل على معالجة الموضوع في أقرب وقت.

{corrective_action}

نشكركم على تفهمكم.

مع التحية،
{sender_name}""",
        "en": """Dear {recipient},

I sincerely apologize for {apology_reason}. We are working to resolve the matter promptly.

{corrective_action}

Thank you for your understanding.

Best regards,
{sender_name}""",
    },
    TemplateType.THANK_YOU: {
        "ar": """السلام عليكم،

شكراً جزيلاً على {thank_reason}.

نقدر تعاونكم ونتطلع لاستمرار العمل معاً.

مع التحية،
{sender_name}""",
        "en": """Dear {recipient},

Thank you very much for {thank_reason}.

We appreciate your cooperation and look forward to continuing our work together.

Best regards,
{sender_name}""",
    },
    TemplateType.ESCALATION: {
        "ar": """السلام عليكم،

أود تصعيد الموضوع التالي للاهتمام والمتابعة:

الموضوع: {subject}
التفاصيل: {details}
الإجراء المطلوب: {required_action}

أرجو التكرم بالتوجيه.

مع التحية،
{sender_name}""",
        "en": """Dear {recipient},

I would like to escalate the following matter for your attention:

Subject: {subject}
Details: {details}
Required Action: {required_action}

I kindly request your guidance.

Best regards,
{sender_name}""",
    },
    TemplateType.INTRODUCTION: {
        "ar": """السلام عليكم ورحمة الله وبركاته،

أتشرف بتعريفكم على نفسي. أنا {sender_name}، {position} في {company}.

{intro_details}

أتطلع للتعاون معكم.

مع أطيب التحيات،
{sender_name}""",
        "en": """Dear {recipient},

I would like to introduce myself. I am {sender_name}, {position} at {company}.

{intro_details}

I look forward to working with you.

Best regards,
{sender_name}""",
    },
}


class ComposeAI:
    """
    مُنشئ الإيميل الذكي (G3)

    يولد ردود ذكية ويحسن الصياغة ويترجم.

    Usage:
        composer = get_compose_ai()
        reply = composer.generate_reply(email, tone=ReplyTone.PROFESSIONAL)
        improved = composer.improve_text(draft_text)
        translated = composer.translate(text, target="en")
    """

    _instance: Optional['ComposeAI'] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._client = None
        if AI_AVAILABLE:
            try:
                self._client = get_ollama_client()
            except Exception as e:
                app_logger.warning(f"Ollama client not available: {e}")

        self._initialized = True
        app_logger.info("ComposeAI (G3) initialized")

    @property
    def is_ai_available(self) -> bool:
        return self._client is not None and AI_AVAILABLE and self._client.is_available()

    def generate_reply(
        self,
        email: 'Email',
        tone: ReplyTone = ReplyTone.PROFESSIONAL,
        language: str = "ar",
        additional_context: str = "",
    ) -> ComposedEmail:
        """
        توليد رد ذكي على إيميل.

        Args:
            email: الإيميل المراد الرد عليه
            tone: نبرة الرد
            language: لغة الرد (ar/en)
            additional_context: سياق إضافي

        Returns:
            ComposedEmail مع الرد المقترح
        """
        if self.is_ai_available:
            return self._generate_reply_ai(email, tone, language, additional_context)
        return self._generate_reply_template(email, tone, language)

    def improve_text(
        self,
        text: str,
        tone: ReplyTone = ReplyTone.PROFESSIONAL,
        language: str = "ar",
    ) -> str:
        """
        تحسين صياغة نص.

        Args:
            text: النص المراد تحسينه
            tone: النبرة المطلوبة
            language: اللغة

        Returns:
            النص المحسّن
        """
        if not self.is_ai_available:
            return text

        lang_name = "العربية" if language == "ar" else "English"
        prompt = f"""حسّن صياغة النص التالي {tone.instruction_ar}.
اللغة: {lang_name}

النص الأصلي:
{text}

النص المحسّن:"""

        try:
            response = self._client.chat(
                message=prompt,
                system="أنت كاتب محترف. حسّن النص مع الحفاظ على المعنى الأصلي.",
                temperature=0.4
            )
            if response:
                return response.strip()
        except Exception as e:
            app_logger.error(f"Text improvement failed: {e}")

        return text

    def translate(
        self,
        text: str,
        target: str = "en",
    ) -> str:
        """
        ترجمة ذكية.

        Args:
            text: النص المراد ترجمته
            target: اللغة الهدف (ar/en)

        Returns:
            النص المترجم
        """
        if not self.is_ai_available:
            return text

        if target == "en":
            prompt = f"ترجم النص التالي إلى الإنجليزية بأسلوب احترافي:\n\n{text}\n\nالترجمة:"
        else:
            prompt = f"Translate the following text to Arabic in a professional style:\n\n{text}\n\nالترجمة:"

        try:
            response = self._client.chat(
                message=prompt,
                system="أنت مترجم محترف. ترجم بدقة مع الحفاظ على النبرة والأسلوب.",
                temperature=0.3
            )
            if response:
                return response.strip()
        except Exception as e:
            app_logger.error(f"Translation failed: {e}")

        return text

    def get_template(
        self,
        template_type: TemplateType,
        language: str = "ar",
        variables: Optional[Dict[str, str]] = None,
    ) -> ComposedEmail:
        """
        الحصول على قالب إيميل.

        Args:
            template_type: نوع القالب
            language: اللغة
            variables: متغيرات القالب

        Returns:
            ComposedEmail بالقالب المعبأ
        """
        template = EMAIL_TEMPLATES.get(template_type, {})
        body = template.get(language, template.get("ar", ""))

        if variables:
            for key, value in variables.items():
                body = body.replace(f"{{{key}}}", value)

        return ComposedEmail(
            subject=variables.get("subject", "") if variables else "",
            body=body,
            language=language,
            template_used=template_type,
            generated_at=datetime.now(),
        )

    def get_available_templates(self) -> List[Dict[str, str]]:
        """قائمة القوالب المتاحة."""
        return [
            {"type": t.value, "label_ar": t.label_ar}
            for t in TemplateType
        ]

    def generate_subject(
        self,
        body: str,
        language: str = "ar",
    ) -> str:
        """توليد موضوع مناسب للإيميل."""
        if not self.is_ai_available:
            return ""

        prompt = f"""اكتب عنوان/موضوع مختصر ومناسب للإيميل التالي (سطر واحد فقط):

{body[:1000]}

الموضوع:"""

        try:
            response = self._client.chat(
                message=prompt,
                system="اكتب عنوان إيميل مختصر ودقيق في سطر واحد فقط.",
                temperature=0.3
            )
            if response:
                return response.strip().split('\n')[0]
        except Exception as e:
            app_logger.error(f"Subject generation failed: {e}")

        return ""

    # --- Private methods ---

    def _generate_reply_ai(
        self,
        email: 'Email',
        tone: ReplyTone,
        language: str,
        additional_context: str,
    ) -> ComposedEmail:
        """توليد رد باستخدام AI."""
        lang_name = "العربية" if language == "ar" else "English"
        context_note = f"\nسياق إضافي: {additional_context}" if additional_context else ""

        prompt = f"""اكتب رد على الإيميل التالي.
النبرة: {tone.instruction_ar}
اللغة: {lang_name}
{context_note}

الإيميل الأصلي:
الموضوع: {email.subject}
المرسل: {email.sender_name}
المحتوى:
{email.body[:2000]}

اكتب الرد فقط بدون أي شرح:"""

        try:
            response = self._client.chat(
                message=prompt,
                system=f"أنت كاتب إيميلات محترف. اكتب ردوداً بـ{lang_name} {tone.instruction_ar}.",
                temperature=0.5
            )

            if response:
                return ComposedEmail(
                    subject=f"Re: {email.subject}",
                    body=response.strip(),
                    tone=tone,
                    language=language,
                    is_reply=True,
                    original_email_id=email.entry_id,
                    generated_at=datetime.now(),
                )
        except Exception as e:
            app_logger.error(f"AI reply generation failed: {e}")

        return self._generate_reply_template(email, tone, language)

    def _generate_reply_template(
        self,
        email: 'Email',
        tone: ReplyTone,
        language: str,
    ) -> ComposedEmail:
        """توليد رد باستخدام القوالب (fallback)."""
        template = self.get_template(
            TemplateType.ACKNOWLEDGMENT,
            language=language,
            variables={
                "subject": email.subject or "",
                "recipient": email.sender_name or "",
                "sender_name": "",
            }
        )

        return ComposedEmail(
            subject=f"Re: {email.subject}",
            body=template.body,
            tone=tone,
            language=language,
            is_reply=True,
            original_email_id=email.entry_id,
            template_used=TemplateType.ACKNOWLEDGMENT,
            generated_at=datetime.now(),
        )


# Singleton
_composer: Optional[ComposeAI] = None
_composer_lock = threading.Lock()


def get_compose_ai() -> ComposeAI:
    """Get singleton ComposeAI."""
    global _composer
    with _composer_lock:
        if _composer is None:
            _composer = ComposeAI()
        return _composer
