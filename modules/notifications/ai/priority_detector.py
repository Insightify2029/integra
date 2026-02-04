"""
INTEGRA - AI Priority Detector
المحور J5: تحديد الأولوية بالذكاء الاصطناعي

يحلل محتوى الإشعار ويحدد:
- الأولوية (عاجل، مهم، عادي، منخفض)
- التصنيف (مالي، قانوني، تشغيلي، شخصي)
- الإجراء المقترح
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum
import re

from core.logging import app_logger
from ..models.notification_models import NotificationPriority


class NotificationCategory(Enum):
    """تصنيفات الإشعارات"""
    FINANCIAL = "financial"      # مالي
    LEGAL = "legal"              # قانوني
    OPERATIONAL = "operational"  # تشغيلي
    HR = "hr"                    # موارد بشرية
    PERSONAL = "personal"        # شخصي
    TECHNICAL = "technical"      # تقني
    URGENT = "urgent"            # طوارئ
    GENERAL = "general"          # عام


@dataclass
class PriorityAnalysis:
    """نتيجة تحليل الأولوية"""
    priority: NotificationPriority
    priority_score: float          # 0.0 - 1.0
    category: NotificationCategory
    suggested_action: Optional[str] = None
    keywords_found: list[str] = None
    reasoning: Optional[str] = None

    def __post_init__(self):
        if self.keywords_found is None:
            self.keywords_found = []


class PriorityDetector:
    """
    كاشف الأولوية الذكي

    يحلل النص ويحدد الأولوية باستخدام:
    1. الكلمات المفتاحية
    2. AI (إذا متاح)
    3. قواعد محددة
    """

    # كلمات مفتاحية للأولوية
    URGENT_KEYWORDS = {
        "ar": [
            "عاجل", "فوري", "طوارئ", "ضروري", "حرج", "خطير",
            "الآن", "فوراً", "بأسرع وقت", "ملح", "هام جداً",
            "اليوم", "قبل نهاية اليوم", "آخر موعد",
        ],
        "en": [
            "urgent", "asap", "immediately", "critical", "emergency",
            "now", "today", "deadline", "important", "priority",
        ],
    }

    HIGH_KEYWORDS = {
        "ar": [
            "مهم", "يرجى", "مطلوب", "لازم", "ضرورة",
            "متابعة", "تذكير", "انتباه", "ملاحظة هامة",
            "قريباً", "غداً", "هذا الأسبوع",
        ],
        "en": [
            "important", "please", "required", "needed", "attention",
            "follow up", "reminder", "notice", "soon", "this week",
        ],
    }

    LOW_KEYWORDS = {
        "ar": [
            "للعلم", "لاحقاً", "عند الفراغ", "غير مستعجل",
            "معلومة", "إحاطة", "نسخة", "للاطلاع",
        ],
        "en": [
            "fyi", "later", "when possible", "not urgent",
            "info", "notification", "copy", "for your information",
        ],
    }

    # كلمات للتصنيف
    CATEGORY_KEYWORDS = {
        NotificationCategory.FINANCIAL: [
            "راتب", "مستحقات", "تسوية", "مالي", "دفع", "فاتورة",
            "ميزانية", "تكلفة", "salary", "payment", "invoice", "budget",
        ],
        NotificationCategory.LEGAL: [
            "عقد", "قانوني", "تعاقد", "إجراء قانوني", "محكمة",
            "contract", "legal", "court", "agreement",
        ],
        NotificationCategory.HR: [
            "موظف", "إجازة", "تعيين", "ترقية", "تقييم", "تدريب",
            "employee", "leave", "hire", "promotion", "training",
        ],
        NotificationCategory.TECHNICAL: [
            "تقني", "نظام", "خطأ", "صيانة", "تحديث", "bug",
            "technical", "system", "error", "maintenance", "update",
        ],
        NotificationCategory.OPERATIONAL: [
            "تشغيل", "عمليات", "تسليم", "مشروع", "مهمة",
            "operation", "delivery", "project", "task",
        ],
    }

    # أنماط الموعد النهائي
    DEADLINE_PATTERNS = [
        r"قبل\s+(\d+)",
        r"خلال\s+(\d+)",
        r"آخر\s+موعد",
        r"deadline",
        r"due\s+date",
        r"by\s+\d{1,2}[/\-]\d{1,2}",
    ]

    def __init__(self, use_ai: bool = True):
        """
        Args:
            use_ai: استخدام AI للتحليل المتقدم
        """
        self.use_ai = use_ai
        self._ai_available = False
        self._check_ai_availability()

    def _check_ai_availability(self):
        """التحقق من توفر AI"""
        if self.use_ai:
            try:
                from core.ai import is_ollama_available
                self._ai_available = is_ollama_available()
            except ImportError:
                self._ai_available = False

    def analyze(
        self,
        title: str,
        body: Optional[str] = None,
        sender: Optional[str] = None,
        notification_type: Optional[str] = None,
    ) -> PriorityAnalysis:
        """
        تحليل الأولوية

        Args:
            title: عنوان الإشعار
            body: محتوى الإشعار
            sender: المرسل
            notification_type: نوع الإشعار

        Returns:
            نتيجة التحليل
        """
        text = f"{title} {body or ''}"

        # 1. تحليل بالكلمات المفتاحية
        keywords_result = self._analyze_keywords(text)

        # 2. تحليل بالأنماط
        has_deadline = self._check_deadline_patterns(text)

        # 3. تحليل بالـ AI إذا متاح
        if self._ai_available and self.use_ai:
            try:
                ai_result = self._analyze_with_ai(title, body)
                if ai_result:
                    return ai_result
            except Exception as e:
                app_logger.debug(f"AI analysis failed, using keywords: {e}")

        # حساب النتيجة النهائية
        priority, score = self._calculate_priority(keywords_result, has_deadline)
        category = self._detect_category(text)
        action = self._suggest_action(priority, category, notification_type)

        return PriorityAnalysis(
            priority=priority,
            priority_score=score,
            category=category,
            suggested_action=action,
            keywords_found=keywords_result["keywords"],
            reasoning=f"تم الكشف عن {len(keywords_result['keywords'])} كلمة مفتاحية",
        )

    def _analyze_keywords(self, text: str) -> dict:
        """تحليل الكلمات المفتاحية"""
        text_lower = text.lower()
        found_keywords = []
        urgent_count = 0
        high_count = 0
        low_count = 0

        # البحث عن كلمات عاجلة
        for lang in ["ar", "en"]:
            for keyword in self.URGENT_KEYWORDS[lang]:
                if keyword in text_lower:
                    found_keywords.append(keyword)
                    urgent_count += 1

        # البحث عن كلمات مهمة
        for lang in ["ar", "en"]:
            for keyword in self.HIGH_KEYWORDS[lang]:
                if keyword in text_lower:
                    found_keywords.append(keyword)
                    high_count += 1

        # البحث عن كلمات منخفضة
        for lang in ["ar", "en"]:
            for keyword in self.LOW_KEYWORDS[lang]:
                if keyword in text_lower:
                    found_keywords.append(keyword)
                    low_count += 1

        return {
            "keywords": list(set(found_keywords)),
            "urgent": urgent_count,
            "high": high_count,
            "low": low_count,
        }

    def _check_deadline_patterns(self, text: str) -> bool:
        """التحقق من وجود موعد نهائي"""
        text_lower = text.lower()
        for pattern in self.DEADLINE_PATTERNS:
            if re.search(pattern, text_lower):
                return True
        return False

    def _calculate_priority(self, keywords_result: dict, has_deadline: bool) -> tuple:
        """حساب الأولوية النهائية"""
        urgent = keywords_result["urgent"]
        high = keywords_result["high"]
        low = keywords_result["low"]

        # حساب النقاط
        score = 0.5  # القاعدة

        if urgent > 0:
            score = min(1.0, 0.8 + (urgent * 0.05))
        elif high > 0:
            score = min(0.79, 0.6 + (high * 0.05))
        elif low > 0:
            score = max(0.2, 0.4 - (low * 0.05))

        if has_deadline:
            score = min(1.0, score + 0.15)

        # تحديد الأولوية
        if score >= 0.8:
            priority = NotificationPriority.URGENT
        elif score >= 0.6:
            priority = NotificationPriority.HIGH
        elif score <= 0.3:
            priority = NotificationPriority.LOW
        else:
            priority = NotificationPriority.NORMAL

        return priority, round(score, 2)

    def _detect_category(self, text: str) -> NotificationCategory:
        """اكتشاف التصنيف"""
        text_lower = text.lower()
        scores = {}

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw in text_lower)
            if count > 0:
                scores[category] = count

        if scores:
            return max(scores, key=scores.get)
        return NotificationCategory.GENERAL

    def _suggest_action(
        self,
        priority: NotificationPriority,
        category: NotificationCategory,
        notification_type: Optional[str],
    ) -> Optional[str]:
        """اقتراح إجراء"""
        if priority == NotificationPriority.URGENT:
            return "يتطلب انتباه فوري"

        if category == NotificationCategory.FINANCIAL:
            return "راجع التفاصيل المالية"
        elif category == NotificationCategory.HR:
            return "راجع بيانات الموظف"
        elif category == NotificationCategory.LEGAL:
            return "استشر القسم القانوني"

        if notification_type == "email":
            if priority == NotificationPriority.HIGH:
                return "يحتاج رد سريع"
            return "راجع الإيميل"
        elif notification_type == "task":
            return "ابدأ العمل على المهمة"

        return None

    def _analyze_with_ai(
        self,
        title: str,
        body: Optional[str]
    ) -> Optional[PriorityAnalysis]:
        """تحليل باستخدام AI"""
        try:
            from core.ai import get_ai_service

            service = get_ai_service()

            prompt = f"""حلل الإشعار التالي وحدد:
1. الأولوية (urgent/high/normal/low)
2. التصنيف (financial/legal/hr/technical/operational/general)
3. الإجراء المقترح

العنوان: {title}
المحتوى: {body or 'غير متوفر'}

أجب بصيغة JSON فقط:
{{"priority": "...", "category": "...", "action": "...", "score": 0.0-1.0}}"""

            response = service.chat(prompt, max_tokens=200)

            # محاولة استخراج JSON
            import json
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                data = json.loads(json_match.group())

                priority_map = {
                    "urgent": NotificationPriority.URGENT,
                    "high": NotificationPriority.HIGH,
                    "normal": NotificationPriority.NORMAL,
                    "low": NotificationPriority.LOW,
                }

                category_map = {
                    "financial": NotificationCategory.FINANCIAL,
                    "legal": NotificationCategory.LEGAL,
                    "hr": NotificationCategory.HR,
                    "technical": NotificationCategory.TECHNICAL,
                    "operational": NotificationCategory.OPERATIONAL,
                    "general": NotificationCategory.GENERAL,
                }

                return PriorityAnalysis(
                    priority=priority_map.get(data.get("priority", "normal"), NotificationPriority.NORMAL),
                    priority_score=float(data.get("score", 0.5)),
                    category=category_map.get(data.get("category", "general"), NotificationCategory.GENERAL),
                    suggested_action=data.get("action"),
                    reasoning="تحليل AI",
                )

        except Exception as e:
            app_logger.debug(f"AI priority analysis error: {e}")

        return None


# ========================
# Singleton & Convenience
# ========================

_detector_instance: Optional[PriorityDetector] = None


def get_priority_detector(use_ai: bool = True) -> PriorityDetector:
    """الحصول على كاشف الأولوية"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = PriorityDetector(use_ai=use_ai)
    return _detector_instance


def detect_priority(
    title: str,
    body: Optional[str] = None,
) -> tuple[NotificationPriority, float]:
    """
    كشف الأولوية (دالة مختصرة)

    Args:
        title: عنوان الإشعار
        body: محتوى الإشعار

    Returns:
        (الأولوية, النقاط)

    Example:
        >>> priority, score = detect_priority("عاجل: اجتماع الآن")
        >>> print(priority)  # NotificationPriority.URGENT
    """
    detector = get_priority_detector()
    result = detector.analyze(title, body)
    return result.priority, result.priority_score


def analyze_notification(
    title: str,
    body: Optional[str] = None,
    sender: Optional[str] = None,
    notification_type: Optional[str] = None,
) -> PriorityAnalysis:
    """
    تحليل إشعار كامل (دالة مختصرة)

    Args:
        title: عنوان الإشعار
        body: محتوى الإشعار
        sender: المرسل
        notification_type: نوع الإشعار

    Returns:
        نتيجة التحليل

    Example:
        >>> result = analyze_notification(
        ...     "طلب تسوية مستحقات",
        ...     "يرجى تسوية مستحقات الموظف أحمد قبل نهاية الشهر",
        ...     notification_type="email"
        ... )
        >>> print(result.priority)
        >>> print(result.category)
        >>> print(result.suggested_action)
    """
    detector = get_priority_detector()
    return detector.analyze(title, body, sender, notification_type)
