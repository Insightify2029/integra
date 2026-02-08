"""
G4: Email Search & Analytics
=============================
بحث ذكي وتحليلات للإيميلات.

Features:
- بحث ذكي بالمعنى (semantic search) مع AI
- تحليلات الإيميلات (أكثر مرسل، أوقات الذروة، اتجاهات)
- تتبع المحادثات (conversation threading)
- ربط الإيميلات بالموظفين
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import re
import threading

from core.logging import app_logger

try:
    from core.ai import get_ollama_client, is_ollama_available
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

try:
    from core.email import Email, get_email_cache
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    Email = None


@dataclass
class SearchResult:
    """نتيجة بحث"""
    email: 'Email'
    relevance_score: float = 0.0
    match_reason: str = ""
    highlighted_text: str = ""


@dataclass
class ConversationThread:
    """سلسلة محادثة"""
    conversation_id: str
    subject: str
    participants: List[str] = field(default_factory=list)
    emails: List['Email'] = field(default_factory=list)
    last_activity: Optional[datetime] = None
    message_count: int = 0

    @property
    def is_active(self) -> bool:
        if not self.last_activity:
            return False
        return (datetime.now() - self.last_activity).days < 7


@dataclass
class SenderStats:
    """إحصائيات مرسل"""
    email: str
    name: str = ""
    total_emails: int = 0
    unread_count: int = 0
    avg_response_time_hours: Optional[float] = None
    last_email_date: Optional[datetime] = None
    categories: Dict[str, int] = field(default_factory=dict)
    top_subjects: List[str] = field(default_factory=list)


@dataclass
class EmailAnalyticsReport:
    """تقرير تحليلات الإيميل"""
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    # Volume
    total_emails: int = 0
    sent_count: int = 0
    received_count: int = 0
    unread_count: int = 0

    # Top senders/recipients
    top_senders: List[SenderStats] = field(default_factory=list)
    top_recipients: List[Dict] = field(default_factory=list)

    # Time distribution
    emails_by_hour: Dict[int, int] = field(default_factory=dict)
    emails_by_day: Dict[str, int] = field(default_factory=dict)
    peak_hour: Optional[int] = None
    peak_day: Optional[str] = None

    # Categories
    by_category: Dict[str, int] = field(default_factory=dict)

    # Response
    avg_response_time_hours: Optional[float] = None
    emails_needing_response: int = 0

    # Conversations
    active_conversations: int = 0
    longest_thread: int = 0

    # Trends
    daily_volume: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "period": {
                "start": self.period_start.isoformat() if self.period_start else None,
                "end": self.period_end.isoformat() if self.period_end else None,
            },
            "volume": {
                "total": self.total_emails,
                "sent": self.sent_count,
                "received": self.received_count,
                "unread": self.unread_count,
            },
            "top_senders": [
                {"email": s.email, "name": s.name, "count": s.total_emails}
                for s in self.top_senders[:10]
            ],
            "time_distribution": {
                "by_hour": self.emails_by_hour,
                "by_day": self.emails_by_day,
                "peak_hour": self.peak_hour,
                "peak_day": self.peak_day,
            },
            "categories": self.by_category,
            "avg_response_time_hours": self.avg_response_time_hours,
            "active_conversations": self.active_conversations,
        }


class EmailSearchEngine:
    """
    محرك البحث الذكي (G4 - Search)

    يوفر بحث ذكي بالمعنى مع ترتيب النتائج حسب الأهمية.

    Usage:
        engine = get_email_search_engine()
        results = engine.search("طلبات الإجازة الشهر الماضي")
        results = engine.search_by_sender("ahmed@company.com")
        thread = engine.get_conversation_thread(conversation_id)
    """

    _instance: Optional['EmailSearchEngine'] = None
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
                app_logger.warning(f"Ollama not available for search: {e}")

        self._initialized = True
        app_logger.info("EmailSearchEngine (G4) initialized")

    def search(
        self,
        query: str,
        emails: Optional[List['Email']] = None,
        limit: int = 50,
        folder: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[SearchResult]:
        """
        بحث ذكي في الإيميلات.

        يدعم:
        - بحث بالكلمات العادية
        - بحث بالمعنى (إذا AI متوفر)
        - فلترة بالتاريخ والمجلد

        Args:
            query: نص البحث
            emails: قائمة إيميلات (إذا None يبحث في الـ cache)
            limit: عدد النتائج
            folder: تصفية بالمجلد
            date_from: من تاريخ
            date_to: إلى تاريخ
        """
        # Get emails from cache if not provided
        if emails is None and EMAIL_AVAILABLE:
            try:
                cache = get_email_cache()
                emails = cache.get_emails(folder_name=folder, limit=500)
            except Exception as e:
                app_logger.error(f"Failed to get emails from cache: {e}")
                return []

        if not emails:
            return []

        # Filter by date
        if date_from or date_to:
            emails = self._filter_by_date(emails, date_from, date_to)

        # Score emails
        results = []
        for email in emails:
            score, reason = self._score_email(email, query)
            if score > 0:
                results.append(SearchResult(
                    email=email,
                    relevance_score=score,
                    match_reason=reason,
                    highlighted_text=self._highlight_match(email, query),
                ))

        # Sort by relevance
        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results[:limit]

    def search_by_sender(
        self, sender_email: str, emails: Optional[List['Email']] = None, limit: int = 50
    ) -> List['Email']:
        """بحث حسب المرسل."""
        if emails is None and EMAIL_AVAILABLE:
            try:
                cache = get_email_cache()
                emails = cache.get_emails(limit=500)
            except Exception:
                return []

        if not emails:
            return []

        results = [
            e for e in emails
            if sender_email.lower() in (e.sender_email or "").lower()
        ]
        results.sort(
            key=lambda e: e.received_time or datetime.min, reverse=True
        )
        return results[:limit]

    def get_conversation_thread(
        self, conversation_id: str, emails: Optional[List['Email']] = None
    ) -> Optional[ConversationThread]:
        """الحصول على سلسلة محادثة."""
        if not conversation_id:
            return None

        if emails is None and EMAIL_AVAILABLE:
            try:
                cache = get_email_cache()
                emails = cache.get_emails(limit=1000)
            except Exception:
                return []

        if not emails:
            return None

        thread_emails = [
            e for e in emails
            if e.conversation_id == conversation_id
        ]

        if not thread_emails:
            return None

        thread_emails.sort(
            key=lambda e: e.received_time or datetime.min
        )

        participants = set()
        for e in thread_emails:
            participants.add(e.sender_email or "")
            participants.update(e.to)

        participants.discard("")

        return ConversationThread(
            conversation_id=conversation_id,
            subject=thread_emails[0].subject if thread_emails else "",
            participants=list(participants),
            emails=thread_emails,
            last_activity=thread_emails[-1].received_time if thread_emails else None,
            message_count=len(thread_emails),
        )

    def get_all_conversations(
        self, emails: List['Email']
    ) -> List[ConversationThread]:
        """الحصول على كل المحادثات."""
        conversations: Dict[str, List['Email']] = defaultdict(list)

        for email in emails:
            conv_id = email.conversation_id or email.entry_id
            conversations[conv_id].append(email)

        threads = []
        for conv_id, conv_emails in conversations.items():
            conv_emails.sort(key=lambda e: e.received_time or datetime.min)
            participants = set()
            for e in conv_emails:
                participants.add(e.sender_email or "")
                participants.update(e.to)
            participants.discard("")

            threads.append(ConversationThread(
                conversation_id=conv_id,
                subject=conv_emails[0].subject if conv_emails else "",
                participants=list(participants),
                emails=conv_emails,
                last_activity=conv_emails[-1].received_time if conv_emails else None,
                message_count=len(conv_emails),
            ))

        threads.sort(key=lambda t: t.last_activity or datetime.min, reverse=True)
        return threads

    def find_related_emails(
        self, email: 'Email', emails: List['Email'], limit: int = 10
    ) -> List['Email']:
        """إيجاد إيميلات ذات صلة."""
        related = []

        for other in emails:
            if other.entry_id == email.entry_id:
                continue

            score = 0

            # Same conversation
            if email.conversation_id and other.conversation_id == email.conversation_id:
                score += 5

            # Same sender
            if email.sender_email and other.sender_email == email.sender_email:
                score += 2

            # Similar subject
            if email.subject and other.subject:
                common = set(email.subject.lower().split()) & set(other.subject.lower().split())
                score += len(common)

            if score > 0:
                related.append((score, other))

        related.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in related[:limit]]

    # --- Private methods ---

    def _score_email(self, email: 'Email', query: str) -> Tuple[float, str]:
        """حساب درجة تطابق إيميل مع البحث."""
        query_lower = query.lower()
        words = query_lower.split()
        score = 0.0
        reasons = []

        subject = (email.subject or "").lower()
        body = (email.body or "").lower()
        sender = f"{email.sender_name or ''} {email.sender_email or ''}".lower()

        # Exact match in subject (highest weight)
        if query_lower in subject:
            score += 10.0
            reasons.append("تطابق في الموضوع")

        # Exact match in sender
        if query_lower in sender:
            score += 8.0
            reasons.append("تطابق في المرسل")

        # Exact match in body
        if query_lower in body:
            score += 5.0
            reasons.append("تطابق في المحتوى")

        # Word-level matching
        for word in words:
            if len(word) < 2:
                continue
            if word in subject:
                score += 3.0
            if word in sender:
                score += 2.0
            if word in body[:1000]:
                score += 1.0

        # Recency boost
        if email.received_time:
            days_old = (datetime.now() - email.received_time).days
            if days_old < 1:
                score *= 1.5
            elif days_old < 7:
                score *= 1.2

        # Importance boost
        if email.importance and email.importance.value >= 2:
            score *= 1.3

        return score, " | ".join(reasons) if reasons else ""

    def _filter_by_date(
        self,
        emails: List['Email'],
        date_from: Optional[datetime],
        date_to: Optional[datetime],
    ) -> List['Email']:
        """فلترة بالتاريخ."""
        filtered = []
        for email in emails:
            dt = email.received_time or email.sent_time
            if not dt:
                continue
            if date_from and dt < date_from:
                continue
            if date_to and dt > date_to:
                continue
            filtered.append(email)
        return filtered

    def _highlight_match(self, email: 'Email', query: str) -> str:
        """تمييز نص المطابقة."""
        body = email.body or ""
        query_lower = query.lower()
        body_lower = body.lower()

        idx = body_lower.find(query_lower)
        if idx >= 0:
            start = max(0, idx - 50)
            end = min(len(body), idx + len(query) + 50)
            snippet = body[start:end]
            if start > 0:
                snippet = "..." + snippet
            if end < len(body):
                snippet = snippet + "..."
            return snippet

        return body[:150] + "..." if len(body) > 150 else body


class EmailAnalytics:
    """
    تحليلات الإيميل (G4 - Analytics)

    يوفر إحصائيات وتحليلات شاملة عن البريد.

    Usage:
        analytics = get_email_analytics()
        report = analytics.generate_report(emails, days=30)
        print(f"إجمالي: {report.total_emails}")
        print(f"أكثر مرسل: {report.top_senders[0].name}")
    """

    _instance: Optional['EmailAnalytics'] = None
    _lock = threading.Lock()

    DAY_NAMES_AR = {
        0: "الإثنين", 1: "الثلاثاء", 2: "الأربعاء",
        3: "الخميس", 4: "الجمعة", 5: "السبت", 6: "الأحد",
    }

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        app_logger.info("EmailAnalytics (G4) initialized")

    def generate_report(
        self,
        emails: List['Email'],
        days: int = 30,
    ) -> EmailAnalyticsReport:
        """
        توليد تقرير تحليلات.

        Args:
            emails: قائمة الإيميلات
            days: فترة التقرير بالأيام

        Returns:
            EmailAnalyticsReport
        """
        now = datetime.now()
        period_start = now - timedelta(days=days)

        # Filter to period
        period_emails = [
            e for e in emails
            if (e.received_time or e.sent_time or datetime.min) >= period_start
        ]

        report = EmailAnalyticsReport(
            period_start=period_start,
            period_end=now,
            total_emails=len(period_emails),
        )

        # Sent vs Received
        for email in period_emails:
            if email.folder_name and 'sent' in email.folder_name.lower():
                report.sent_count += 1
            else:
                report.received_count += 1
            if not email.is_read:
                report.unread_count += 1

        # Top senders
        report.top_senders = self._analyze_senders(period_emails)

        # Time distribution
        report.emails_by_hour, report.emails_by_day = self._time_distribution(period_emails)
        if report.emails_by_hour:
            report.peak_hour = max(report.emails_by_hour, key=report.emails_by_hour.get)
        if report.emails_by_day:
            report.peak_day = max(report.emails_by_day, key=report.emails_by_day.get)

        # Daily volume
        report.daily_volume = self._daily_volume(period_emails)

        # Conversations
        conversations = self._count_conversations(period_emails)
        report.active_conversations = len(conversations)
        if conversations:
            report.longest_thread = max(conversations.values())

        return report

    def get_sender_profile(
        self, sender_email: str, emails: List['Email']
    ) -> SenderStats:
        """الحصول على ملف مرسل."""
        sender_emails = [
            e for e in emails
            if (e.sender_email or "").lower() == sender_email.lower()
        ]

        if not sender_emails:
            return SenderStats(email=sender_email)

        name = sender_emails[0].sender_name or sender_email
        last_date = max(
            (e.received_time for e in sender_emails if e.received_time),
            default=None,
        )

        # Top subjects
        subjects = Counter(e.subject for e in sender_emails if e.subject)
        top_subjects = [s for s, _ in subjects.most_common(5)]

        return SenderStats(
            email=sender_email,
            name=name,
            total_emails=len(sender_emails),
            unread_count=sum(1 for e in sender_emails if not e.is_read),
            last_email_date=last_date,
            top_subjects=top_subjects,
        )

    # --- Private methods ---

    def _analyze_senders(self, emails: List['Email']) -> List[SenderStats]:
        """تحليل المرسلين."""
        sender_map: Dict[str, List['Email']] = defaultdict(list)
        for email in emails:
            if email.sender_email:
                sender_map[email.sender_email.lower()].append(email)

        stats = []
        for sender_email, sender_emails in sender_map.items():
            name = sender_emails[0].sender_name or sender_email
            last_date = max(
                (e.received_time for e in sender_emails if e.received_time),
                default=None,
            )
            stats.append(SenderStats(
                email=sender_email,
                name=name,
                total_emails=len(sender_emails),
                unread_count=sum(1 for e in sender_emails if not e.is_read),
                last_email_date=last_date,
            ))

        stats.sort(key=lambda s: s.total_emails, reverse=True)
        return stats[:20]

    def _time_distribution(
        self, emails: List['Email']
    ) -> Tuple[Dict[int, int], Dict[str, int]]:
        """توزيع الإيميلات على الساعات والأيام."""
        by_hour: Dict[int, int] = defaultdict(int)
        by_day: Dict[str, int] = defaultdict(int)

        for email in emails:
            dt = email.received_time or email.sent_time
            if not dt:
                continue
            by_hour[dt.hour] += 1
            day_name = self.DAY_NAMES_AR.get(dt.weekday(), "غير محدد")
            by_day[day_name] += 1

        return dict(by_hour), dict(by_day)

    def _daily_volume(self, emails: List['Email']) -> Dict[str, int]:
        """حجم الإيميلات اليومي."""
        volume: Dict[str, int] = defaultdict(int)
        for email in emails:
            dt = email.received_time or email.sent_time
            if dt:
                volume[dt.strftime('%Y-%m-%d')] += 1
        return dict(sorted(volume.items()))

    def _count_conversations(self, emails: List['Email']) -> Dict[str, int]:
        """حساب المحادثات."""
        conversations: Dict[str, int] = defaultdict(int)
        for email in emails:
            conv_id = email.conversation_id or email.entry_id
            conversations[conv_id] += 1
        return dict(conversations)


# Singletons
_search_engine: Optional[EmailSearchEngine] = None
_search_lock = threading.Lock()

_analytics: Optional[EmailAnalytics] = None
_analytics_lock = threading.Lock()


def get_email_search_engine() -> EmailSearchEngine:
    """Get singleton EmailSearchEngine."""
    global _search_engine
    with _search_lock:
        if _search_engine is None:
            _search_engine = EmailSearchEngine()
        return _search_engine


def get_email_analytics() -> EmailAnalytics:
    """Get singleton EmailAnalytics."""
    global _analytics
    with _analytics_lock:
        if _analytics is None:
            _analytics = EmailAnalytics()
        return _analytics
