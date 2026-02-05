"""
Time Intelligence
=================
Hyper Time Intelligence system for INTEGRA.
Provides comprehensive time awareness for AI Copilot and business operations.

Components:
- SystemTime: Core time utilities (Gregorian + Hijri)
- WorkingCalendar: Working days, hours, and holidays
- NaturalTimeParser: Arabic natural language time expressions
- TimeAnalytics: YoY, MoM, QoQ, YTD comparisons
- PeriodCalculator: Date range calculations
- ProductivityLearner: User productivity pattern learning
- PatternAnalyzer: Time-series pattern analysis
- DeadlinePredictor: Deadline risk prediction
- AutoScheduler: Smart task scheduling
- TimeTriggers: Time-based event triggers
"""

from .system_time import SystemTime, get_system_time
from .hijri_utils import (
    hijri_today, hijri_for_date, gregorian_from_hijri,
    days_until_ramadan, days_until_eid_fitr, days_until_eid_adha,
    get_upcoming_islamic_events,
)
from .working_calendar import WorkingCalendar, get_working_calendar
from .time_parser import NaturalTimeParser, get_time_parser
from .time_analytics import TimeAnalytics, get_time_analytics
from .period_calculator import PeriodCalculator, get_period_calculator
from .productivity_learner import ProductivityLearner, get_productivity_learner
from .pattern_analyzer import PatternAnalyzer, get_pattern_analyzer
from .deadline_predictor import (
    DeadlinePredictor, get_deadline_predictor,
    AlertGenerator, get_alert_generator,
)
from .auto_scheduler import (
    AutoScheduler, get_auto_scheduler,
    ScheduleOptimizer, get_schedule_optimizer,
)
from .time_triggers import (
    TimeTrigger, TimeTriggers, get_time_triggers,
    TriggerExecutor, get_trigger_executor,
)

__all__ = [
    # Core
    'SystemTime', 'get_system_time',
    # Hijri
    'hijri_today', 'hijri_for_date', 'gregorian_from_hijri',
    'days_until_ramadan', 'days_until_eid_fitr', 'days_until_eid_adha',
    'get_upcoming_islamic_events',
    # Calendar
    'WorkingCalendar', 'get_working_calendar',
    # Parser
    'NaturalTimeParser', 'get_time_parser',
    # Analytics
    'TimeAnalytics', 'get_time_analytics',
    'PeriodCalculator', 'get_period_calculator',
    # Productivity
    'ProductivityLearner', 'get_productivity_learner',
    'PatternAnalyzer', 'get_pattern_analyzer',
    # Deadlines
    'DeadlinePredictor', 'get_deadline_predictor',
    'AlertGenerator', 'get_alert_generator',
    # Scheduler
    'AutoScheduler', 'get_auto_scheduler',
    'ScheduleOptimizer', 'get_schedule_optimizer',
    # Triggers
    'TimeTrigger', 'TimeTriggers', 'get_time_triggers',
    'TriggerExecutor', 'get_trigger_executor',
]


def get_time_context() -> dict:
    """Get comprehensive time context for AI Copilot integration."""
    system_time = get_system_time()
    calendar = get_working_calendar()
    learner = get_productivity_learner()

    return {
        "system": system_time.get_full_context(),
        "work": calendar.get_context(),
        "productivity": {
            "best_hours": learner.get_best_hours(3),
            "summary": learner.get_productivity_summary(),
        },
    }
