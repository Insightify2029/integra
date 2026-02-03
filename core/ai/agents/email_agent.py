"""
Email Agent
===========
AI agent specialized in email analysis and management.
"""

from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum
import threading

from ..ollama_client import get_ollama_client
from ..prompts import SYSTEM_PROMPTS
from core.logging import app_logger

# Try to import email models
try:
    from core.email import Email
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    Email = None


class EmailCategory(Enum):
    """Email categories."""
    WORK = "عمل"
    PERSONAL = "شخصي"
    MEETING = "اجتماعات"
    TASK = "مهام"
    NEWSLETTER = "إعلان"
    SOCIAL = "اجتماعي"
    OTHER = "أخرى"


class EmailPriorityAI(Enum):
    """AI-determined email priority."""
    URGENT = "عاجل"
    IMPORTANT = "مهم"
    NORMAL = "عادي"
    LOW = "منخفض"


@dataclass
class EmailAnalysis:
    """Result of email analysis."""
    summary: str
    category: EmailCategory
    priority: EmailPriorityAI
    tasks: List[str]
    key_points: List[str]
    suggested_reply: Optional[str] = None
    sentiment: Optional[str] = None  # إيجابي، سلبي، محايد


class EmailAgent:
    """
    AI Agent for email analysis and management.

    Features:
    - Email summarization
    - Category classification
    - Priority detection
    - Task extraction
    - Reply suggestions
    - Batch analysis

    Usage:
        agent = EmailAgent()
        analysis = agent.analyze_email(email)
        print(analysis.summary)
    """

    _instance: Optional['EmailAgent'] = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._client = get_ollama_client()
        self._system_prompt = SYSTEM_PROMPTS.get("email")
        self._initialized = True

    @property
    def is_available(self) -> bool:
        """Check if agent is available."""
        return self._client.is_available()

    def analyze_email(self, email: 'Email') -> Optional[EmailAnalysis]:
        """
        Analyze a single email.

        Args:
            email: Email object to analyze

        Returns:
            EmailAnalysis object or None if failed
        """
        if not self.is_available or not EMAIL_AVAILABLE:
            return None

        prompt = f"""حلل الإيميل التالي بدقة:

الموضوع: {email.subject}
المرسل: {email.sender_name} <{email.sender_email}>
التاريخ: {email.received_time.strftime('%Y-%m-%d %H:%M') if email.received_time else 'غير محدد'}
المحتوى:
---
{email.body[:3000]}
---

قدم التحليل بالتنسيق التالي:
الملخص: (ملخص مختصر في جملة أو جملتين)
التصنيف: (عمل/شخصي/اجتماعات/مهام/إعلان/اجتماعي/أخرى)
الأولوية: (عاجل/مهم/عادي/منخفض)
النقاط الرئيسية:
- نقطة 1
- نقطة 2
المهام المطلوبة:
- مهمة 1 (إن وجدت)
المشاعر: (إيجابي/سلبي/محايد)
اقتراح رد: (اقتراح مختصر للرد إن كان مطلوباً)
"""

        try:
            response = self._client.chat(
                message=prompt,
                system=self._system_prompt,
                temperature=0.3
            )

            if response:
                return self._parse_analysis(response)

        except Exception as e:
            app_logger.error(f"Email analysis error: {e}")

        return None

    def _parse_analysis(self, response: str) -> EmailAnalysis:
        """Parse AI response into EmailAnalysis."""
        lines = response.split('\n')

        summary = ""
        category = EmailCategory.OTHER
        priority = EmailPriorityAI.NORMAL
        tasks = []
        key_points = []
        suggested_reply = None
        sentiment = None

        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith('الملخص:'):
                summary = line.replace('الملخص:', '').strip()
            elif line.startswith('التصنيف:'):
                cat_text = line.replace('التصنيف:', '').strip()
                category = self._parse_category(cat_text)
            elif line.startswith('الأولوية:'):
                pri_text = line.replace('الأولوية:', '').strip()
                priority = self._parse_priority(pri_text)
            elif line.startswith('النقاط الرئيسية:'):
                current_section = 'points'
            elif line.startswith('المهام المطلوبة:'):
                current_section = 'tasks'
            elif line.startswith('المشاعر:'):
                sentiment = line.replace('المشاعر:', '').strip()
                current_section = None
            elif line.startswith('اقتراح رد:'):
                suggested_reply = line.replace('اقتراح رد:', '').strip()
                current_section = 'reply'
            elif line.startswith('-'):
                item = line[1:].strip()
                if current_section == 'points':
                    key_points.append(item)
                elif current_section == 'tasks':
                    tasks.append(item)
            elif current_section == 'reply' and not line.startswith('-'):
                if suggested_reply:
                    suggested_reply += " " + line
                else:
                    suggested_reply = line

        return EmailAnalysis(
            summary=summary or "لم يتم تلخيص الإيميل",
            category=category,
            priority=priority,
            tasks=tasks,
            key_points=key_points,
            suggested_reply=suggested_reply,
            sentiment=sentiment
        )

    def _parse_category(self, text: str) -> EmailCategory:
        """Parse category text to enum."""
        text = text.lower()
        mapping = {
            'عمل': EmailCategory.WORK,
            'شخصي': EmailCategory.PERSONAL,
            'اجتماع': EmailCategory.MEETING,
            'اجتماعات': EmailCategory.MEETING,
            'مهم': EmailCategory.TASK,
            'مهام': EmailCategory.TASK,
            'إعلان': EmailCategory.NEWSLETTER,
            'اعلان': EmailCategory.NEWSLETTER,
            'اجتماعي': EmailCategory.SOCIAL,
        }
        for key, value in mapping.items():
            if key in text:
                return value
        return EmailCategory.OTHER

    def _parse_priority(self, text: str) -> EmailPriorityAI:
        """Parse priority text to enum."""
        text = text.lower()
        if 'عاجل' in text:
            return EmailPriorityAI.URGENT
        elif 'مهم' in text:
            return EmailPriorityAI.IMPORTANT
        elif 'منخفض' in text:
            return EmailPriorityAI.LOW
        return EmailPriorityAI.NORMAL

    def summarize_email(self, email: 'Email', max_words: int = 50) -> Optional[str]:
        """
        Get a quick summary of an email.

        Args:
            email: Email to summarize
            max_words: Maximum words in summary

        Returns:
            Summary string or None
        """
        if not self.is_available:
            return None

        prompt = f"""لخص الإيميل التالي في {max_words} كلمة أو أقل:

الموضوع: {email.subject}
المرسل: {email.sender_name}
المحتوى:
{email.body[:2000]}

الملخص:"""

        try:
            return self._client.chat(
                message=prompt,
                system="أنت ملخص إيميلات محترف. قدم ملخصات مختصرة ودقيقة.",
                temperature=0.2
            )
        except Exception as e:
            app_logger.error(f"Summarization error: {e}")
            return None

    def extract_tasks(self, email: 'Email') -> List[str]:
        """
        Extract action items/tasks from an email.

        Args:
            email: Email to analyze

        Returns:
            List of tasks
        """
        if not self.is_available:
            return []

        prompt = f"""استخرج المهام والإجراءات المطلوبة من الإيميل التالي.
إذا لم توجد مهام، قل "لا توجد مهام".

الموضوع: {email.subject}
المحتوى:
{email.body[:2000]}

المهام:"""

        try:
            response = self._client.chat(
                message=prompt,
                temperature=0.2
            )

            if response and 'لا توجد' not in response:
                tasks = []
                for line in response.split('\n'):
                    line = line.strip()
                    if line.startswith('-') or line.startswith('•') or line[0:1].isdigit():
                        task = line.lstrip('-•0123456789. ').strip()
                        if task:
                            tasks.append(task)
                return tasks

        except Exception as e:
            app_logger.error(f"Task extraction error: {e}")

        return []

    def suggest_reply(
        self,
        email: 'Email',
        tone: str = "professional",
        language: str = "ar"
    ) -> Optional[str]:
        """
        Suggest a reply to an email.

        Args:
            email: Email to reply to
            tone: Reply tone (professional, friendly, formal)
            language: Reply language (ar, en)

        Returns:
            Suggested reply text
        """
        if not self.is_available:
            return None

        tone_instructions = {
            "professional": "احترافي ومهذب",
            "friendly": "ودي وغير رسمي",
            "formal": "رسمي جداً"
        }

        lang_instructions = {
            "ar": "باللغة العربية",
            "en": "in English"
        }

        prompt = f"""اكتب رد مقترح على الإيميل التالي.
الأسلوب: {tone_instructions.get(tone, 'احترافي')}
اللغة: {lang_instructions.get(language, 'العربية')}

الإيميل الأصلي:
الموضوع: {email.subject}
المرسل: {email.sender_name}
المحتوى:
{email.body[:1500]}

الرد المقترح:"""

        try:
            return self._client.chat(
                message=prompt,
                system="أنت كاتب إيميلات محترف. اكتب ردوداً مناسبة ومختصرة.",
                temperature=0.5
            )
        except Exception as e:
            app_logger.error(f"Reply suggestion error: {e}")
            return None

    def batch_analyze(
        self,
        emails: List['Email'],
        quick: bool = True
    ) -> List[Tuple['Email', EmailAnalysis]]:
        """
        Analyze multiple emails.

        Args:
            emails: List of emails to analyze
            quick: If True, only get summary and priority

        Returns:
            List of (email, analysis) tuples
        """
        results = []

        for email in emails:
            if quick:
                # Quick analysis - just summary and priority
                summary = self.summarize_email(email, max_words=30)
                if summary:
                    # Try to detect priority from keywords
                    priority = EmailPriorityAI.NORMAL
                    urgent_keywords = ['عاجل', 'فوري', 'مهم جداً', 'urgent', 'asap']
                    if any(kw in email.subject.lower() or kw in email.body[:500].lower()
                           for kw in urgent_keywords):
                        priority = EmailPriorityAI.URGENT

                    analysis = EmailAnalysis(
                        summary=summary,
                        category=EmailCategory.OTHER,
                        priority=priority,
                        tasks=[],
                        key_points=[]
                    )
                    results.append((email, analysis))
            else:
                # Full analysis
                analysis = self.analyze_email(email)
                if analysis:
                    results.append((email, analysis))

        return results

    def categorize_emails(
        self,
        emails: List['Email']
    ) -> Dict[EmailCategory, List['Email']]:
        """
        Categorize emails into groups.

        Args:
            emails: List of emails to categorize

        Returns:
            Dictionary mapping categories to emails
        """
        categories = {cat: [] for cat in EmailCategory}

        for email in emails:
            analysis = self.analyze_email(email)
            if analysis:
                categories[analysis.category].append(email)
            else:
                categories[EmailCategory.OTHER].append(email)

        return categories


# Singleton instance
_agent: Optional[EmailAgent] = None


def get_email_agent() -> EmailAgent:
    """Get the singleton email agent."""
    global _agent
    if _agent is None:
        _agent = EmailAgent()
    return _agent


def analyze_email(email: 'Email') -> Optional[EmailAnalysis]:
    """Quick function to analyze an email."""
    return get_email_agent().analyze_email(email)


def summarize_email(email: 'Email', **kwargs) -> Optional[str]:
    """Quick function to summarize an email."""
    return get_email_agent().summarize_email(email, **kwargs)


def extract_email_tasks(email: 'Email') -> List[str]:
    """Quick function to extract tasks from an email."""
    return get_email_agent().extract_tasks(email)


def suggest_email_reply(email: 'Email', **kwargs) -> Optional[str]:
    """Quick function to suggest a reply."""
    return get_email_agent().suggest_reply(email, **kwargs)
