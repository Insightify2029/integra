"""
G1: AI Email Assistant
======================
مساعد الإيميل الذكي - تحليل تلقائي، تصنيف ذكي، استخراج مهام ومواعيد.

Features:
- تحليل تفصيلي لكل إيميل جديد
- تصنيف ذكي (عمل/شخصي/عاجل/spam)
- استخراج المهام والمواعيد تلقائياً
- اقتراح ردود ذكية
- تحليل المشاعر والنبرة
- كشف الإيميلات المشبوهة
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple
import json
import threading
import re

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


class EmailClassification(Enum):
    """تصنيفات الإيميل الذكية"""
    WORK_URGENT = "work_urgent"
    WORK_NORMAL = "work_normal"
    WORK_FYI = "work_fyi"
    MEETING_REQUEST = "meeting_request"
    TASK_REQUEST = "task_request"
    APPROVAL_REQUEST = "approval_request"
    HR_REQUEST = "hr_request"
    FINANCIAL = "financial"
    PERSONAL = "personal"
    NEWSLETTER = "newsletter"
    AUTOMATED = "automated"
    SPAM_SUSPICIOUS = "spam_suspicious"
    OTHER = "other"

    @property
    def label_ar(self) -> str:
        labels = {
            "work_urgent": "عمل - عاجل",
            "work_normal": "عمل - عادي",
            "work_fyi": "عمل - للعلم",
            "meeting_request": "طلب اجتماع",
            "task_request": "طلب مهمة",
            "approval_request": "طلب اعتماد",
            "hr_request": "طلب HR",
            "financial": "مالي",
            "personal": "شخصي",
            "newsletter": "نشرة إخبارية",
            "automated": "تلقائي",
            "spam_suspicious": "مشبوه/سبام",
            "other": "أخرى",
        }
        return labels.get(self.value, "أخرى")

    @property
    def color(self) -> str:
        colors = {
            "work_urgent": "#e74c3c",
            "work_normal": "#3498db",
            "work_fyi": "#95a5a6",
            "meeting_request": "#9b59b6",
            "task_request": "#2ecc71",
            "approval_request": "#f39c12",
            "hr_request": "#e67e22",
            "financial": "#c0392b",
            "personal": "#1abc9c",
            "newsletter": "#bdc3c7",
            "automated": "#7f8c8d",
            "spam_suspicious": "#e74c3c",
            "other": "#95a5a6",
        }
        return colors.get(self.value, "#95a5a6")

    @property
    def requires_action(self) -> bool:
        return self.value in (
            "work_urgent", "task_request", "approval_request",
            "hr_request", "meeting_request", "financial",
        )


class SentimentType(Enum):
    """أنواع المشاعر"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    URGENT = "urgent"
    FORMAL = "formal"


@dataclass
class ExtractedTask:
    """مهمة مستخرجة من الإيميل"""
    title: str
    description: str = ""
    priority: str = "normal"
    due_date: Optional[str] = None
    assignee_hint: Optional[str] = None


@dataclass
class ExtractedMeeting:
    """موعد مستخرج من الإيميل"""
    title: str
    date_hint: Optional[str] = None
    time_hint: Optional[str] = None
    location: Optional[str] = None
    attendees: List[str] = field(default_factory=list)


@dataclass
class DetailedEmailAnalysis:
    """نتيجة التحليل التفصيلي للإيميل"""
    # Basic
    email_id: str
    summary: str
    classification: EmailClassification
    sentiment: SentimentType
    confidence_score: float = 0.0

    # Extracted info
    tasks: List[ExtractedTask] = field(default_factory=list)
    meetings: List[ExtractedMeeting] = field(default_factory=list)
    key_points: List[str] = field(default_factory=list)
    deadlines: List[str] = field(default_factory=list)
    mentioned_names: List[str] = field(default_factory=list)
    mentioned_amounts: List[str] = field(default_factory=list)

    # Action suggestions
    suggested_reply: Optional[str] = None
    suggested_actions: List[str] = field(default_factory=list)
    requires_response: bool = False
    urgency_reason: Optional[str] = None

    # Metadata
    analyzed_at: Optional[datetime] = None
    language: str = "ar"
    is_suspicious: bool = False
    suspicious_reason: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "email_id": self.email_id,
            "summary": self.summary,
            "classification": self.classification.value,
            "sentiment": self.sentiment.value,
            "confidence_score": self.confidence_score,
            "tasks": [{"title": t.title, "description": t.description,
                       "priority": t.priority, "due_date": t.due_date}
                      for t in self.tasks],
            "meetings": [{"title": m.title, "date_hint": m.date_hint,
                         "time_hint": m.time_hint, "location": m.location}
                        for m in self.meetings],
            "key_points": self.key_points,
            "deadlines": self.deadlines,
            "suggested_reply": self.suggested_reply,
            "suggested_actions": self.suggested_actions,
            "requires_response": self.requires_response,
            "urgency_reason": self.urgency_reason,
            "is_suspicious": self.is_suspicious,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
        }


class EmailAssistant:
    """
    مساعد الإيميل الذكي (G1)

    يوفر تحليل تفصيلي وتصنيف ذكي لكل إيميل.

    Usage:
        assistant = get_email_assistant()
        analysis = assistant.analyze(email)
        print(analysis.summary)
        print(analysis.classification.label_ar)
        for task in analysis.tasks:
            print(f"- {task.title}")
    """

    _instance: Optional['EmailAssistant'] = None
    _lock = threading.Lock()

    URGENT_KEYWORDS_AR = [
        'عاجل', 'فوري', 'مستعجل', 'ضروري', 'طارئ',
        'الآن', 'حالاً', 'فوراً', 'بأسرع وقت', 'آخر موعد',
    ]
    URGENT_KEYWORDS_EN = [
        'urgent', 'asap', 'immediately', 'critical', 'deadline',
        'time-sensitive', 'emergency', 'priority',
    ]
    MEETING_KEYWORDS = [
        'اجتماع', 'لقاء', 'meeting', 'مقابلة', 'جلسة',
        'conference', 'call', 'مكالمة', 'زووم', 'zoom', 'teams',
    ]
    TASK_KEYWORDS = [
        'يرجى', 'المطلوب', 'أرجو', 'نرجو', 'please',
        'required', 'action needed', 'kindly', 'مطلوب',
        'أحتاج', 'نحتاج', 'تأكد', 'تابع', 'أرسل',
    ]
    FINANCIAL_KEYWORDS = [
        'راتب', 'مستحقات', 'تسوية', 'فاتورة', 'دفعة',
        'salary', 'payment', 'invoice', 'budget', 'ميزانية',
        'تكلفة', 'مبلغ', 'ريال', 'SAR', 'USD',
    ]
    HR_KEYWORDS = [
        'إجازة', 'استقالة', 'تعيين', 'ترقية', 'نقل',
        'تقييم', 'تدريب', 'حضور', 'غياب', 'vacation',
        'leave', 'resignation', 'hire', 'promotion',
    ]
    SUSPICIOUS_PATTERNS = [
        r'click\s+here\s+immediately',
        r'verify\s+your\s+account',
        r'won\s+a\s+prize',
        r'confirm\s+your\s+password',
        r'فز.*جائزة',
        r'تحقق.*حسابك.*فوراً',
    ]

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

        self._analysis_cache: Dict[str, DetailedEmailAnalysis] = {}
        self._cache_lock = threading.Lock()
        self._initialized = True
        app_logger.info("EmailAssistant (G1) initialized")

    @property
    def is_ai_available(self) -> bool:
        return self._client is not None and AI_AVAILABLE and self._client.is_available()

    def analyze(self, email: 'Email') -> DetailedEmailAnalysis:
        """
        تحليل تفصيلي لإيميل واحد.

        يستخدم AI إذا متوفر، وإلا يعتمد على التحليل القاعدي (rule-based).
        """
        if not email:
            return self._empty_analysis("")

        # Check cache
        with self._cache_lock:
            if email.entry_id in self._analysis_cache:
                return self._analysis_cache[email.entry_id]

        # Run analysis
        if self.is_ai_available:
            analysis = self._analyze_with_ai(email)
        else:
            analysis = self._analyze_rule_based(email)

        # Cache result
        with self._cache_lock:
            self._analysis_cache[email.entry_id] = analysis

        return analysis

    def analyze_batch(
        self, emails: List['Email'], quick: bool = False
    ) -> List[DetailedEmailAnalysis]:
        """تحليل مجموعة إيميلات."""
        results = []
        for email in emails:
            try:
                if quick:
                    results.append(self._analyze_rule_based(email))
                else:
                    results.append(self.analyze(email))
            except Exception as e:
                app_logger.error(f"Batch analysis error for {email.entry_id}: {e}")
                results.append(self._empty_analysis(email.entry_id))
        return results

    def get_daily_summary(
        self, emails: List['Email']
    ) -> Dict:
        """ملخص يومي لقائمة إيميلات."""
        analyses = self.analyze_batch(emails, quick=True)

        summary = {
            "total": len(emails),
            "urgent": 0,
            "requires_action": 0,
            "tasks_found": 0,
            "meetings_found": 0,
            "by_classification": {},
            "top_senders": {},
            "action_items": [],
        }

        for email, analysis in zip(emails, analyses):
            cls_name = analysis.classification.label_ar
            summary["by_classification"][cls_name] = (
                summary["by_classification"].get(cls_name, 0) + 1
            )

            if analysis.classification == EmailClassification.WORK_URGENT:
                summary["urgent"] += 1

            if analysis.classification.requires_action:
                summary["requires_action"] += 1

            summary["tasks_found"] += len(analysis.tasks)
            summary["meetings_found"] += len(analysis.meetings)

            sender = email.sender_email
            summary["top_senders"][sender] = (
                summary["top_senders"].get(sender, 0) + 1
            )

            for task in analysis.tasks:
                summary["action_items"].append({
                    "task": task.title,
                    "from": email.sender_name,
                    "priority": task.priority,
                })

        # Sort top senders
        summary["top_senders"] = dict(
            sorted(summary["top_senders"].items(),
                   key=lambda x: x[1], reverse=True)[:10]
        )

        return summary

    def clear_cache(self):
        """مسح cache التحليلات."""
        with self._cache_lock:
            self._analysis_cache.clear()

    # --- Private methods ---

    def _analyze_with_ai(self, email: 'Email') -> DetailedEmailAnalysis:
        """تحليل باستخدام Ollama AI."""
        prompt = f"""حلل الإيميل التالي بدقة وأعد النتيجة بتنسيق JSON فقط:

الموضوع: {email.subject}
المرسل: {email.sender_name} <{email.sender_email}>
التاريخ: {email.received_time.strftime('%Y-%m-%d %H:%M') if email.received_time else 'غير محدد'}
المحتوى:
---
{email.body[:3000]}
---

أعد JSON بالشكل التالي (بدون أي نص إضافي):
{{
  "summary": "ملخص مختصر",
  "classification": "work_urgent|work_normal|work_fyi|meeting_request|task_request|approval_request|hr_request|financial|personal|newsletter|automated|spam_suspicious|other",
  "sentiment": "positive|neutral|negative|urgent|formal",
  "confidence": 0.85,
  "key_points": ["نقطة 1", "نقطة 2"],
  "tasks": [{{"title": "عنوان المهمة", "priority": "high|normal|low", "due_date": "إذا ذُكر"}}],
  "meetings": [{{"title": "عنوان الاجتماع", "date_hint": "إذا ذُكر", "time_hint": "إذا ذُكر"}}],
  "deadlines": ["أي مواعيد نهائية مذكورة"],
  "requires_response": true,
  "suggested_reply": "اقتراح رد مختصر",
  "suggested_actions": ["إجراء 1", "إجراء 2"]
}}"""

        try:
            response = self._client.chat(
                message=prompt,
                system="أنت محلل إيميلات محترف. أعد النتائج بتنسيق JSON فقط بدون أي شرح إضافي.",
                temperature=0.2
            )

            if response:
                return self._parse_ai_response(email.entry_id, response, email)

        except Exception as e:
            app_logger.error(f"AI email analysis failed: {e}")

        # Fallback to rule-based
        return self._analyze_rule_based(email)

    def _parse_ai_response(
        self, email_id: str, response: str, email: 'Email'
    ) -> DetailedEmailAnalysis:
        """Parse AI JSON response."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if not json_match:
                return self._analyze_rule_based(email)

            data = json.loads(json_match.group())

            # Parse classification
            try:
                classification = EmailClassification(
                    data.get("classification", "other")
                )
            except ValueError:
                classification = EmailClassification.OTHER

            # Parse sentiment
            try:
                sentiment = SentimentType(data.get("sentiment", "neutral"))
            except ValueError:
                sentiment = SentimentType.NEUTRAL

            # Parse tasks
            tasks = []
            for t in data.get("tasks", []):
                if isinstance(t, dict) and t.get("title"):
                    tasks.append(ExtractedTask(
                        title=t["title"],
                        priority=t.get("priority", "normal"),
                        due_date=t.get("due_date"),
                    ))

            # Parse meetings
            meetings = []
            for m in data.get("meetings", []):
                if isinstance(m, dict) and m.get("title"):
                    meetings.append(ExtractedMeeting(
                        title=m["title"],
                        date_hint=m.get("date_hint"),
                        time_hint=m.get("time_hint"),
                    ))

            # Check suspicious
            is_suspicious, suspicious_reason = self._check_suspicious(email)

            return DetailedEmailAnalysis(
                email_id=email_id,
                summary=data.get("summary", ""),
                classification=classification,
                sentiment=sentiment,
                confidence_score=float(data.get("confidence", 0.8)),
                tasks=tasks,
                meetings=meetings,
                key_points=data.get("key_points", []),
                deadlines=data.get("deadlines", []),
                suggested_reply=data.get("suggested_reply"),
                suggested_actions=data.get("suggested_actions", []),
                requires_response=data.get("requires_response", False),
                analyzed_at=datetime.now(),
                is_suspicious=is_suspicious,
                suspicious_reason=suspicious_reason,
            )

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            app_logger.warning(f"Failed to parse AI response: {e}")
            return self._analyze_rule_based(email)

    def _analyze_rule_based(self, email: 'Email') -> DetailedEmailAnalysis:
        """تحليل قاعدي بدون AI - يعتمد على كلمات مفتاحية."""
        subject = (email.subject or "").lower()
        body = (email.body or "")[:2000].lower()
        combined = f"{subject} {body}"

        # Classification
        classification = self._classify_rule_based(subject, body, email)

        # Sentiment
        sentiment = self._detect_sentiment_rules(combined)

        # Tasks extraction
        tasks = self._extract_tasks_rules(email)

        # Meetings extraction
        meetings = self._extract_meetings_rules(email)

        # Deadlines
        deadlines = self._extract_deadlines(combined)

        # Suspicious check
        is_suspicious, suspicious_reason = self._check_suspicious(email)

        # Check if response needed
        requires_response = classification.requires_action

        # Summary
        summary = self._generate_rule_summary(email, classification)

        return DetailedEmailAnalysis(
            email_id=email.entry_id,
            summary=summary,
            classification=classification,
            sentiment=sentiment,
            confidence_score=0.6,
            tasks=tasks,
            meetings=meetings,
            key_points=self._extract_key_points(email),
            deadlines=deadlines,
            requires_response=requires_response,
            analyzed_at=datetime.now(),
            is_suspicious=is_suspicious,
            suspicious_reason=suspicious_reason,
        )

    def _classify_rule_based(
        self, subject: str, body: str, email: 'Email'
    ) -> EmailClassification:
        """تصنيف قاعدي."""
        combined = f"{subject} {body}"

        # Check urgent
        if any(kw in combined for kw in self.URGENT_KEYWORDS_AR + self.URGENT_KEYWORDS_EN):
            return EmailClassification.WORK_URGENT

        # Check meeting
        if any(kw in combined for kw in self.MEETING_KEYWORDS):
            return EmailClassification.MEETING_REQUEST

        # Check HR
        if any(kw in combined for kw in self.HR_KEYWORDS):
            return EmailClassification.HR_REQUEST

        # Check financial
        if any(kw in combined for kw in self.FINANCIAL_KEYWORDS):
            return EmailClassification.FINANCIAL

        # Check approval
        if 'اعتماد' in combined or 'approve' in combined or 'موافقة' in combined:
            return EmailClassification.APPROVAL_REQUEST

        # Check task request
        if any(kw in combined for kw in self.TASK_KEYWORDS):
            return EmailClassification.TASK_REQUEST

        # Check newsletter
        if 'unsubscribe' in body or 'إلغاء الاشتراك' in body:
            return EmailClassification.NEWSLETTER

        # Check automated
        if 'noreply' in (email.sender_email or '').lower():
            return EmailClassification.AUTOMATED

        # Check suspicious
        if any(re.search(p, combined) for p in self.SUSPICIOUS_PATTERNS):
            return EmailClassification.SPAM_SUSPICIOUS

        return EmailClassification.WORK_NORMAL

    def _detect_sentiment_rules(self, text: str) -> SentimentType:
        """كشف المشاعر."""
        urgent_words = ['عاجل', 'فوري', 'urgent', 'asap', 'ضروري']
        positive_words = ['شكراً', 'ممتاز', 'رائع', 'thank', 'great', 'excellent']
        negative_words = ['مشكلة', 'خطأ', 'problem', 'issue', 'error', 'شكوى']

        if any(w in text for w in urgent_words):
            return SentimentType.URGENT
        if any(w in text for w in positive_words):
            return SentimentType.POSITIVE
        if any(w in text for w in negative_words):
            return SentimentType.NEGATIVE
        return SentimentType.NEUTRAL

    def _extract_tasks_rules(self, email: 'Email') -> List[ExtractedTask]:
        """استخراج المهام بالقواعد."""
        tasks = []
        body = email.body or ""

        task_patterns = [
            r'(?:يرجى|المطلوب|أرجو|نرجو|please|kindly)\s+(.+?)(?:\.|$)',
            r'(?:مطلوب|مهمة|task)[:：]\s*(.+?)(?:\.|$)',
        ]

        for pattern in task_patterns:
            matches = re.finditer(pattern, body, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                title = match.group(1).strip()
                if len(title) > 5 and len(title) < 200:
                    priority = "high" if any(
                        kw in title.lower()
                        for kw in self.URGENT_KEYWORDS_AR + self.URGENT_KEYWORDS_EN
                    ) else "normal"
                    tasks.append(ExtractedTask(title=title, priority=priority))

        return tasks[:10]

    def _extract_meetings_rules(self, email: 'Email') -> List[ExtractedMeeting]:
        """استخراج الاجتماعات بالقواعد."""
        meetings = []
        combined = f"{email.subject or ''} {email.body or ''}"

        if any(kw in combined.lower() for kw in self.MEETING_KEYWORDS):
            title = email.subject or "اجتماع"

            # Try to find date
            date_match = re.search(
                r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})', combined
            )
            time_match = re.search(
                r'(\d{1,2}:\d{2})\s*(?:ص|م|AM|PM)?', combined
            )

            meetings.append(ExtractedMeeting(
                title=title,
                date_hint=date_match.group(1) if date_match else None,
                time_hint=time_match.group(1) if time_match else None,
            ))

        return meetings

    def _extract_deadlines(self, text: str) -> List[str]:
        """استخراج المواعيد النهائية."""
        deadlines = []

        patterns = [
            r'(?:آخر موعد|الموعد النهائي|deadline|due date)[:：\s]+(.+?)(?:\.|$)',
            r'(?:قبل|before)\s+(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                deadlines.append(match.group(1).strip())

        return deadlines[:5]

    def _extract_key_points(self, email: 'Email') -> List[str]:
        """استخراج النقاط الرئيسية."""
        points = []
        body = email.body or ""

        # Split into sentences and pick meaningful ones
        sentences = re.split(r'[.،\n]', body)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and len(sentence) < 200:
                # Check if it contains important keywords
                important = any(
                    kw in sentence.lower()
                    for kw in self.TASK_KEYWORDS + self.FINANCIAL_KEYWORDS + self.HR_KEYWORDS
                )
                if important:
                    points.append(sentence)

        return points[:5]

    def _check_suspicious(self, email: 'Email') -> Tuple[bool, Optional[str]]:
        """فحص الإيميلات المشبوهة."""
        combined = f"{email.subject or ''} {email.body or ''}".lower()

        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, combined, re.IGNORECASE):
                return True, f"نمط مشبوه: {pattern}"

        # Check for mismatched sender
        sender_email = (email.sender_email or "").lower()
        sender_name = (email.sender_name or "").lower()

        # Check free email domains claiming to be from companies
        free_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        company_keywords = ['bank', 'بنك', 'ministry', 'وزارة', 'official', 'رسمي']

        sender_domain = sender_email.split('@')[-1] if '@' in sender_email else ''
        if any(d in sender_domain for d in free_domains):
            if any(kw in sender_name for kw in company_keywords):
                return True, "المرسل يدّعي أنه جهة رسمية لكن يستخدم بريد مجاني"

        return False, None

    def _generate_rule_summary(
        self, email: 'Email', classification: EmailClassification
    ) -> str:
        """توليد ملخص قاعدي."""
        sender = email.sender_name or email.sender_email or "مجهول"
        subject = email.subject or "بدون موضوع"

        type_desc = classification.label_ar
        return f"{type_desc} من {sender}: {subject}"

    def _empty_analysis(self, email_id: str) -> DetailedEmailAnalysis:
        return DetailedEmailAnalysis(
            email_id=email_id,
            summary="لم يتم التحليل",
            classification=EmailClassification.OTHER,
            sentiment=SentimentType.NEUTRAL,
            analyzed_at=datetime.now(),
        )


# Singleton
_assistant: Optional[EmailAssistant] = None
_assistant_lock = threading.Lock()


def get_email_assistant() -> EmailAssistant:
    """Get singleton EmailAssistant."""
    global _assistant
    with _assistant_lock:
        if _assistant is None:
            _assistant = EmailAssistant()
        return _assistant
