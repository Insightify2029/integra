"""
INTEGRA - Calendar AI Agent
وكيل التقويم الذكي
المحور I

التاريخ: 4 فبراير 2026

القدرات:
- اقتراح أفضل وقت للمهمة/الاجتماع
- اكتشاف تعارضات المواعيد
- اقتراح إعادة جدولة
- تحليل أنماط العمل
- اقتراح فترات راحة
"""

from dataclasses import dataclass, field
from datetime import datetime, date, time, timedelta
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
import json

from core.logging import app_logger


class ConflictSeverity(Enum):
    """درجة خطورة التعارض"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def label_ar(self) -> str:
        labels = {
            "none": "لا يوجد",
            "low": "منخفض",
            "medium": "متوسط",
            "high": "مرتفع",
            "critical": "حرج"
        }
        return labels.get(self.value, self.value)


@dataclass
class TimeSlotSuggestion:
    """اقتراح وقت"""
    start_datetime: datetime
    end_datetime: datetime
    score: float  # 0-1 - كلما ارتفع كان أفضل
    reason: str
    conflicts_count: int = 0


@dataclass
class ConflictAnalysis:
    """تحليل التعارضات"""
    has_conflicts: bool = False
    severity: ConflictSeverity = ConflictSeverity.NONE
    conflicting_events: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    alternative_slots: List[TimeSlotSuggestion] = field(default_factory=list)


@dataclass
class WorkPatternAnalysis:
    """تحليل أنماط العمل"""
    busiest_day: Optional[str] = None
    busiest_hour: Optional[int] = None
    avg_events_per_day: float = 0.0
    avg_event_duration: float = 0.0  # بالدقائق
    meeting_heavy_days: List[str] = field(default_factory=list)
    free_slots: List[Tuple[time, time]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class SchedulingSuggestion:
    """اقتراح جدولة"""
    original_datetime: datetime
    suggested_datetime: datetime
    reason: str
    score: float
    benefits: List[str] = field(default_factory=list)


class CalendarAgent:
    """وكيل التقويم الذكي"""

    # ساعات العمل الافتراضية
    DEFAULT_WORK_START = 8
    DEFAULT_WORK_END = 17

    # أيام العمل (0=الأحد، 4=الخميس)
    DEFAULT_WORK_DAYS = [0, 1, 2, 3, 4]

    def __init__(self):
        self._ollama_available = self._check_ollama()
        self.work_start_hour = self.DEFAULT_WORK_START
        self.work_end_hour = self.DEFAULT_WORK_END
        self.work_days = self.DEFAULT_WORK_DAYS

    def _check_ollama(self) -> bool:
        """التحقق من توفر Ollama"""
        try:
            from core.ai import is_ollama_available
            return is_ollama_available()
        except ImportError:
            return False

    def suggest_best_time(
        self,
        duration_minutes: int,
        preferred_date: Optional[date] = None,
        existing_events: Optional[List[Dict[str, Any]]] = None,
        priority: str = "normal",
        num_suggestions: int = 3
    ) -> List[TimeSlotSuggestion]:
        """
        اقتراح أفضل وقت لحدث جديد

        Args:
            duration_minutes: مدة الحدث بالدقائق
            preferred_date: التاريخ المفضل
            existing_events: الأحداث الموجودة
            priority: أولوية الحدث
            num_suggestions: عدد الاقتراحات

        Returns:
            قائمة باقتراحات الأوقات مرتبة بالأفضل
        """
        suggestions = []

        if not preferred_date:
            preferred_date = date.today()

        existing_events = existing_events or []

        # تحويل الأحداث إلى فترات مشغولة
        busy_slots = self._extract_busy_slots(existing_events, preferred_date)

        # البحث عن فترات فارغة
        free_slots = self._find_free_slots(
            preferred_date,
            busy_slots,
            duration_minutes
        )

        # ترتيب الفترات حسب الأفضلية
        for slot_start, slot_end in free_slots[:num_suggestions]:
            score = self._calculate_slot_score(slot_start, priority)
            reason = self._generate_slot_reason(slot_start, score)

            suggestions.append(TimeSlotSuggestion(
                start_datetime=slot_start,
                end_datetime=slot_end,
                score=score,
                reason=reason,
                conflicts_count=0
            ))

        # ترتيب حسب الدرجة
        suggestions.sort(key=lambda s: s.score, reverse=True)

        return suggestions[:num_suggestions]

    def check_conflicts(
        self,
        start_datetime: datetime,
        end_datetime: datetime,
        existing_events: List[Dict[str, Any]],
        exclude_event_id: Optional[int] = None
    ) -> ConflictAnalysis:
        """
        التحقق من تعارض موعد مع أحداث أخرى

        Args:
            start_datetime: بداية الموعد
            end_datetime: نهاية الموعد
            existing_events: الأحداث الموجودة
            exclude_event_id: استثناء حدث معين

        Returns:
            تحليل التعارضات
        """
        analysis = ConflictAnalysis()
        conflicts = []

        for event in existing_events:
            if exclude_event_id and event.get("id") == exclude_event_id:
                continue

            event_start = event.get("start_datetime")
            event_end = event.get("end_datetime")

            if not event_start:
                continue

            # التحقق من التعارض
            if self._times_overlap(start_datetime, end_datetime, event_start, event_end):
                conflicts.append({
                    "id": event.get("id"),
                    "title": event.get("title"),
                    "start": event_start,
                    "end": event_end
                })

        if conflicts:
            analysis.has_conflicts = True
            analysis.conflicting_events = conflicts

            # تحديد درجة الخطورة
            if len(conflicts) >= 3:
                analysis.severity = ConflictSeverity.CRITICAL
            elif len(conflicts) == 2:
                analysis.severity = ConflictSeverity.HIGH
            elif len(conflicts) == 1:
                # التحقق من تداخل كبير أو صغير
                overlap = self._calculate_overlap_percentage(
                    start_datetime, end_datetime,
                    conflicts[0]["start"], conflicts[0]["end"]
                )
                if overlap > 0.5:
                    analysis.severity = ConflictSeverity.MEDIUM
                else:
                    analysis.severity = ConflictSeverity.LOW

            # اقتراحات
            analysis.suggestions = self._generate_conflict_suggestions(
                start_datetime, end_datetime, conflicts
            )

            # أوقات بديلة
            analysis.alternative_slots = self.suggest_best_time(
                duration_minutes=int((end_datetime - start_datetime).total_seconds() / 60),
                preferred_date=start_datetime.date(),
                existing_events=existing_events
            )

        return analysis

    def suggest_rescheduling(
        self,
        event: Dict[str, Any],
        existing_events: List[Dict[str, Any]],
        reason: str = "conflict"
    ) -> List[SchedulingSuggestion]:
        """
        اقتراح إعادة جدولة لحدث

        Args:
            event: الحدث المراد إعادة جدولته
            existing_events: الأحداث الموجودة
            reason: سبب إعادة الجدولة

        Returns:
            قائمة باقتراحات إعادة الجدولة
        """
        suggestions = []

        original_start = event.get("start_datetime")
        original_end = event.get("end_datetime")

        if not original_start:
            return suggestions

        duration = original_end - original_start if original_end else timedelta(hours=1)

        # البحث عن أوقات بديلة
        time_suggestions = self.suggest_best_time(
            duration_minutes=int(duration.total_seconds() / 60),
            preferred_date=original_start.date(),
            existing_events=existing_events,
            num_suggestions=5
        )

        for ts in time_suggestions:
            benefits = []

            # تحديد الفوائد
            if ts.start_datetime.hour >= self.work_start_hour and ts.start_datetime.hour < 12:
                benefits.append("وقت الصباح - إنتاجية عالية")
            elif ts.start_datetime.hour >= 14 and ts.start_datetime.hour < 16:
                benefits.append("بعد الظهر - وقت مناسب للاجتماعات")

            if ts.conflicts_count == 0:
                benefits.append("لا يوجد تعارضات")

            suggestions.append(SchedulingSuggestion(
                original_datetime=original_start,
                suggested_datetime=ts.start_datetime,
                reason=ts.reason,
                score=ts.score,
                benefits=benefits
            ))

        return suggestions

    def analyze_work_patterns(
        self,
        events: List[Dict[str, Any]],
        days_back: int = 30
    ) -> WorkPatternAnalysis:
        """
        تحليل أنماط العمل من الأحداث

        Args:
            events: قائمة الأحداث
            days_back: عدد الأيام للتحليل

        Returns:
            تحليل أنماط العمل
        """
        analysis = WorkPatternAnalysis()

        if not events:
            return analysis

        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_events = [
            e for e in events
            if e.get("start_datetime") and e["start_datetime"] >= cutoff_date
        ]

        if not recent_events:
            return analysis

        # تحليل الأيام
        day_counts = {}
        hour_counts = {}
        durations = []

        day_names = ["الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"]

        for event in recent_events:
            start = event.get("start_datetime")
            end = event.get("end_datetime")

            if not start:
                continue

            # حساب اليوم
            day_index = (start.weekday() + 1) % 7
            day_name = day_names[day_index]
            day_counts[day_name] = day_counts.get(day_name, 0) + 1

            # حساب الساعة
            hour = start.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

            # حساب المدة
            if end:
                duration = (end - start).total_seconds() / 60
                durations.append(duration)

        # اليوم الأكثر ازدحاماً
        if day_counts:
            analysis.busiest_day = max(day_counts, key=day_counts.get)

        # الساعة الأكثر ازدحاماً
        if hour_counts:
            analysis.busiest_hour = max(hour_counts, key=hour_counts.get)

        # متوسط الأحداث يومياً
        analysis.avg_events_per_day = len(recent_events) / days_back

        # متوسط المدة
        if durations:
            analysis.avg_event_duration = sum(durations) / len(durations)

        # أيام كثيفة الاجتماعات
        avg_per_day = len(recent_events) / 7
        analysis.meeting_heavy_days = [
            day for day, count in day_counts.items()
            if count > avg_per_day * 1.5
        ]

        # التوصيات
        analysis.recommendations = self._generate_pattern_recommendations(analysis)

        return analysis

    def suggest_break_times(
        self,
        events: List[Dict[str, Any]],
        target_date: Optional[date] = None
    ) -> List[Tuple[time, time]]:
        """
        اقتراح أوقات راحة

        Args:
            events: الأحداث في اليوم
            target_date: التاريخ المستهدف

        Returns:
            قائمة بفترات الراحة المقترحة
        """
        break_times = []

        if not target_date:
            target_date = date.today()

        # تصفية أحداث اليوم
        day_events = [
            e for e in events
            if e.get("start_datetime") and e["start_datetime"].date() == target_date
        ]

        # ترتيب حسب الوقت
        day_events.sort(key=lambda e: e["start_datetime"])

        # البحث عن فجوات
        prev_end = datetime.combine(target_date, time(self.work_start_hour, 0))

        for event in day_events:
            start = event.get("start_datetime")
            end = event.get("end_datetime") or (start + timedelta(hours=1))

            # فجوة قبل هذا الحدث
            gap = (start - prev_end).total_seconds() / 60

            # إذا كانت الفجوة 15 دقيقة أو أكثر
            if gap >= 15:
                break_times.append((prev_end.time(), start.time()))

            prev_end = end

        # فحص نهاية اليوم
        work_end = datetime.combine(target_date, time(self.work_end_hour, 0))
        if prev_end < work_end:
            gap = (work_end - prev_end).total_seconds() / 60
            if gap >= 15:
                break_times.append((prev_end.time(), work_end.time()))

        return break_times

    def analyze_with_ai(
        self,
        events: List[Dict[str, Any]],
        query: str
    ) -> str:
        """
        تحليل التقويم باستخدام AI

        Args:
            events: الأحداث للتحليل
            query: السؤال أو الطلب

        Returns:
            إجابة AI
        """
        if not self._ollama_available:
            return "خدمة AI غير متاحة حالياً"

        try:
            from core.ai import get_ai_service

            # تحضير ملخص الأحداث
            events_summary = self._summarize_events_for_ai(events)

            prompt = f"""أنت مساعد ذكي للتقويم. لديك المعلومات التالية عن الأحداث:

{events_summary}

السؤال: {query}

أجب بشكل مختصر ومفيد بالعربية."""

            service = get_ai_service()
            response = service.chat(prompt)
            return response

        except Exception as e:
            app_logger.error(f"خطأ في تحليل AI للتقويم: {e}")
            return "حدث خطأ في التحليل"

    # ═══════════════════════════════════════════════════════════════
    # Private Methods
    # ═══════════════════════════════════════════════════════════════

    def _extract_busy_slots(
        self,
        events: List[Dict[str, Any]],
        target_date: date
    ) -> List[Tuple[datetime, datetime]]:
        """استخراج الفترات المشغولة"""
        slots = []

        for event in events:
            start = event.get("start_datetime")
            end = event.get("end_datetime")

            if not start:
                continue

            if start.date() == target_date:
                if not end:
                    end = start + timedelta(hours=1)
                slots.append((start, end))

        return sorted(slots, key=lambda s: s[0])

    def _find_free_slots(
        self,
        target_date: date,
        busy_slots: List[Tuple[datetime, datetime]],
        duration_minutes: int
    ) -> List[Tuple[datetime, datetime]]:
        """البحث عن الفترات الفارغة"""
        free_slots = []

        work_start = datetime.combine(target_date, time(self.work_start_hour, 0))
        work_end = datetime.combine(target_date, time(self.work_end_hour, 0))

        current_time = work_start

        for busy_start, busy_end in busy_slots:
            if current_time < busy_start:
                gap = (busy_start - current_time).total_seconds() / 60
                if gap >= duration_minutes:
                    slot_end = current_time + timedelta(minutes=duration_minutes)
                    free_slots.append((current_time, slot_end))

            current_time = max(current_time, busy_end)

        # التحقق من نهاية اليوم
        if current_time < work_end:
            gap = (work_end - current_time).total_seconds() / 60
            if gap >= duration_minutes:
                slot_end = current_time + timedelta(minutes=duration_minutes)
                free_slots.append((current_time, slot_end))

        return free_slots

    def _calculate_slot_score(
        self,
        slot_start: datetime,
        priority: str
    ) -> float:
        """حساب درجة الفترة الزمنية"""
        score = 0.5

        hour = slot_start.hour

        # ساعات الصباح أفضل للمهام المهمة
        if 9 <= hour <= 11:
            score += 0.2
        elif 8 <= hour < 9:
            score += 0.1

        # تجنب وقت الغداء
        if 12 <= hour <= 13:
            score -= 0.15

        # بعد الظهر جيد للاجتماعات
        if 14 <= hour <= 16:
            score += 0.1

        # تجنب نهاية اليوم
        if hour >= 16:
            score -= 0.1

        # الأولوية العالية تفضل الصباح
        if priority in ["urgent", "high"] and hour <= 10:
            score += 0.15

        return min(1.0, max(0.0, score))

    def _generate_slot_reason(self, slot_start: datetime, score: float) -> str:
        """توليد سبب للاقتراح"""
        hour = slot_start.hour

        reasons = []

        if 9 <= hour <= 11:
            reasons.append("وقت الصباح - إنتاجية عالية")
        elif 14 <= hour <= 16:
            reasons.append("فترة بعد الظهر المثالية")
        elif hour < 9:
            reasons.append("بداية اليوم")
        else:
            reasons.append("وقت متاح")

        if score >= 0.7:
            reasons.append("درجة ممتازة")
        elif score >= 0.5:
            reasons.append("درجة جيدة")

        return " - ".join(reasons)

    def _times_overlap(
        self,
        start1: datetime, end1: datetime,
        start2: datetime, end2: datetime
    ) -> bool:
        """التحقق من تداخل فترتين"""
        if not end2:
            end2 = start2 + timedelta(hours=1)
        return start1 < end2 and start2 < end1

    def _calculate_overlap_percentage(
        self,
        start1: datetime, end1: datetime,
        start2: datetime, end2: datetime
    ) -> float:
        """حساب نسبة التداخل"""
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)

        if overlap_start >= overlap_end:
            return 0.0

        overlap_duration = (overlap_end - overlap_start).total_seconds()
        event1_duration = (end1 - start1).total_seconds()

        return overlap_duration / event1_duration if event1_duration > 0 else 0.0

    def _generate_conflict_suggestions(
        self,
        start: datetime,
        end: datetime,
        conflicts: List[Dict[str, Any]]
    ) -> List[str]:
        """توليد اقتراحات لحل التعارضات"""
        suggestions = []

        suggestions.append(f"يوجد تعارض مع {len(conflicts)} حدث/أحداث")

        for conflict in conflicts[:3]:
            suggestions.append(f"تعارض مع: {conflict.get('title', 'حدث')}")

        suggestions.append("يمكنك اختيار وقت بديل من الاقتراحات")

        return suggestions

    def _generate_pattern_recommendations(
        self,
        analysis: WorkPatternAnalysis
    ) -> List[str]:
        """توليد توصيات من تحليل الأنماط"""
        recommendations = []

        if analysis.avg_events_per_day > 5:
            recommendations.append("جدولك مزدحم - حاول تقليل الاجتماعات غير الضرورية")

        if analysis.avg_event_duration > 90:
            recommendations.append("اجتماعاتك طويلة - جرب تقصيرها إلى 45-60 دقيقة")

        if analysis.meeting_heavy_days:
            days = "، ".join(analysis.meeting_heavy_days)
            recommendations.append(f"أيام {days} مزدحمة - وزع الاجتماعات على الأسبوع")

        if analysis.busiest_hour and (analysis.busiest_hour < 10 or analysis.busiest_hour > 15):
            recommendations.append("حاول جدولة الاجتماعات في ساعات الذروة (10-15)")

        if not recommendations:
            recommendations.append("جدولك متوازن - استمر!")

        return recommendations

    def _summarize_events_for_ai(
        self,
        events: List[Dict[str, Any]]
    ) -> str:
        """تلخيص الأحداث للـ AI"""
        if not events:
            return "لا توجد أحداث"

        lines = []
        for event in events[:20]:  # حد أقصى 20 حدث
            title = event.get("title", "بدون عنوان")
            start = event.get("start_datetime")
            if start:
                lines.append(f"- {title} ({start.strftime('%Y-%m-%d %H:%M')})")
            else:
                lines.append(f"- {title}")

        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# Singleton Instance
# ═══════════════════════════════════════════════════════════════

_agent_instance: Optional[CalendarAgent] = None


def get_calendar_agent() -> CalendarAgent:
    """الحصول على مثيل وكيل التقويم"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = CalendarAgent()
    return _agent_instance


# ═══════════════════════════════════════════════════════════════
# Convenience Functions
# ═══════════════════════════════════════════════════════════════

def suggest_best_time(
    duration_minutes: int,
    preferred_date: Optional[date] = None,
    existing_events: Optional[List[Dict[str, Any]]] = None,
    priority: str = "normal"
) -> List[TimeSlotSuggestion]:
    """اقتراح أفضل وقت"""
    return get_calendar_agent().suggest_best_time(
        duration_minutes, preferred_date, existing_events, priority
    )


def check_calendar_conflicts(
    start_datetime: datetime,
    end_datetime: datetime,
    existing_events: List[Dict[str, Any]]
) -> ConflictAnalysis:
    """التحقق من التعارضات"""
    return get_calendar_agent().check_conflicts(
        start_datetime, end_datetime, existing_events
    )


def analyze_work_patterns(
    events: List[Dict[str, Any]],
    days_back: int = 30
) -> WorkPatternAnalysis:
    """تحليل أنماط العمل"""
    return get_calendar_agent().analyze_work_patterns(events, days_back)


def suggest_break_times(
    events: List[Dict[str, Any]],
    target_date: Optional[date] = None
) -> List[Tuple[time, time]]:
    """اقتراح أوقات راحة"""
    return get_calendar_agent().suggest_break_times(events, target_date)
