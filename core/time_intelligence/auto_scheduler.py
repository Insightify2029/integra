"""
Smart Auto-Scheduler
====================
Automatic task rescheduling and schedule optimization.
"""

from datetime import date, timedelta
from typing import Optional


class AutoScheduler:
    """Smart auto-rescheduling and schedule optimization."""

    def __init__(self, working_calendar=None, productivity_learner=None):
        self._calendar = working_calendar
        self._learner = productivity_learner

    @property
    def calendar(self):
        if self._calendar is None:
            from .working_calendar import get_working_calendar
            self._calendar = get_working_calendar()
        return self._calendar

    @property
    def learner(self):
        if self._learner is None:
            from .productivity_learner import get_productivity_learner
            self._learner = get_productivity_learner()
        return self._learner

    def reschedule_on_delay(self, delayed_task: dict, other_tasks: list) -> list:
        """Reschedule dependent tasks when a task is delayed."""
        rescheduled = []

        original_deadline = delayed_task.get("original_deadline")
        new_deadline = delayed_task.get("new_deadline")

        if isinstance(original_deadline, str):
            original_deadline = date.fromisoformat(original_deadline)
        if isinstance(new_deadline, str):
            new_deadline = date.fromisoformat(new_deadline)

        if not original_deadline or not new_deadline:
            return []

        delay_days = (new_deadline - original_deadline).days
        if delay_days <= 0:
            return []

        for task in other_tasks:
            task_start = task.get("start_date")
            task_deadline = task.get("deadline")

            if isinstance(task_start, str):
                task_start = date.fromisoformat(task_start)
            if isinstance(task_deadline, str):
                task_deadline = date.fromisoformat(task_deadline)

            if not task_deadline:
                continue

            # Only affect tasks that start after original deadline
            if task_start and task_start > original_deadline:
                continue

            # Move the task
            new_start = self.calendar.add_working_days(task_start, delay_days) if task_start else None
            new_task_deadline = self.calendar.add_working_days(task_deadline, delay_days)

            rescheduled.append({
                "task_id": task.get("id"),
                "task_title": task.get("title", "مهمة"),
                "original_start": task_start.isoformat() if task_start else None,
                "new_start": new_start.isoformat() if new_start else None,
                "original_deadline": task_deadline.isoformat(),
                "new_deadline": new_task_deadline.isoformat(),
                "delay_days": delay_days,
                "reason": f"تأخر مهمة '{delayed_task.get('title', '')}'",
            })

        return rescheduled

    def optimize_schedule(self, tasks: list) -> list:
        """Optimize task schedule based on priority and productivity patterns."""
        if not tasks:
            return []

        # Sort by priority (desc) then deadline (asc)
        sorted_tasks = sorted(tasks, key=lambda t: (
            -t.get("priority", 0),
            t.get("deadline", "9999-12-31"),
        ))

        optimized = []
        best_hours = self.learner.get_best_hours(3)
        best_hour = best_hours[0]["hour"] if best_hours else 10

        current_date = date.today()

        for task in sorted_tasks:
            task_type = task.get("type", "general")
            estimated = self.learner.get_average_duration(task_type)

            # Find best slot
            suggested_date = current_date
            while not self.calendar.is_working_day(suggested_date):
                suggested_date += timedelta(days=1)

            optimized.append({
                "task": task,
                "suggested_start": suggested_date.isoformat(),
                "suggested_time": f"{best_hour:02d}:00",
                "estimated_duration": estimated,
                "reason": self._get_optimization_reason(task, suggested_date),
            })

            # Move to next slot based on estimated duration
            hours_needed = estimated / 60
            if hours_needed >= 4:
                current_date = self.calendar.next_working_day(suggested_date)
            # else: same day, next task fits

        return optimized

    def suggest_meeting_time(
        self,
        duration_minutes: int = 60,
        earliest_date: Optional[date] = None,
        preferred_hours: Optional[list] = None,
    ) -> list:
        """Suggest optimal meeting times."""
        if earliest_date is None:
            earliest_date = date.today()

        if preferred_hours is None:
            preferred_hours = [10, 11, 14, 15]

        suggestions = []

        for day_offset in range(14):  # Look 2 weeks ahead
            check_date = earliest_date + timedelta(days=day_offset)

            if not self.calendar.is_working_day(check_date):
                continue

            for hour in preferred_hours:
                suggestions.append({
                    "date": check_date.isoformat(),
                    "time": f"{hour:02d}:00",
                    "duration": duration_minutes,
                    "day_name": self._get_day_name(check_date),
                    "score": self._score_meeting_slot(check_date, hour),
                })

        # Sort by score (best first)
        suggestions.sort(key=lambda x: x["score"], reverse=True)
        return suggestions[:5]

    def suggest_task_time(self, task_type: str) -> dict:
        """Suggest the best time to work on a specific task type."""
        prediction = self.learner.predict_completion_time(task_type)
        best_hours = self.learner.get_best_hours(3)

        today = date.today()
        suggested_date = today
        if not self.calendar.is_working_day(suggested_date):
            suggested_date = self.calendar.next_working_day(suggested_date)

        best_hour = best_hours[0]["hour"] if best_hours else 10

        return {
            "suggested_date": suggested_date.isoformat(),
            "suggested_time": f"{best_hour:02d}:00",
            "estimated_duration": prediction["estimated_minutes"],
            "estimated_label": f"~{prediction['estimated_label']}",
            "confidence": prediction["confidence"],
            "reason": f"أفضل وقت لإنتاجيتك هو الساعة {best_hour:02d}:00",
        }

    def _get_optimization_reason(self, task: dict, suggested_date: date) -> str:
        """Generate Arabic reason for optimization suggestion."""
        priority = task.get("priority", 0)
        deadline = task.get("deadline")

        if priority >= 3:
            return "أولوية عالية - يُفضل البدء فوراً"
        elif deadline:
            if isinstance(deadline, str):
                deadline = date.fromisoformat(deadline)
            days_left = (deadline - date.today()).days
            if days_left <= 3:
                return f"موعد قريب - باقي {days_left} يوم"
            return "حسب الأولوية والموعد النهائي"
        return "جُدولت بناءً على الأولوية"

    def _score_meeting_slot(self, check_date: date, hour: int) -> float:
        """Score a meeting slot (higher is better)."""
        score = 50.0

        # Prefer mid-morning and early afternoon
        if hour in (10, 11):
            score += 20
        elif hour in (14, 15):
            score += 10

        # Prefer earlier in the week
        weekday = check_date.weekday()
        if weekday <= 2:  # Mon-Wed
            score += 10
        elif weekday <= 3:  # Thu
            score += 5

        # Prefer sooner dates
        days_away = (check_date - date.today()).days
        if days_away <= 2:
            score += 15
        elif days_away <= 5:
            score += 10

        return score

    @staticmethod
    def _get_day_name(d: date) -> str:
        """Get Arabic day name."""
        from .system_time import DAYS_AR
        return DAYS_AR[d.weekday()]


class ScheduleOptimizer:
    """Advanced schedule optimization utilities."""

    def __init__(self, auto_scheduler: Optional[AutoScheduler] = None):
        self._scheduler = auto_scheduler

    @property
    def scheduler(self) -> AutoScheduler:
        if self._scheduler is None:
            self._scheduler = AutoScheduler()
        return self._scheduler

    def balance_workload(self, tasks: list, days: int = 5) -> dict:
        """Distribute tasks evenly across working days."""
        today = date.today()
        daily_plan = {}

        working_dates = []
        current = today
        while len(working_dates) < days:
            if self.scheduler.calendar.is_working_day(current):
                working_dates.append(current)
            current += timedelta(days=1)

        # Sort tasks by deadline urgency
        sorted_tasks = sorted(tasks, key=lambda t: t.get("deadline", "9999-12-31"))

        # Distribute
        for i, task in enumerate(sorted_tasks):
            day_idx = i % len(working_dates)
            day = working_dates[day_idx]
            day_key = day.isoformat()
            if day_key not in daily_plan:
                daily_plan[day_key] = {
                    "date": day_key,
                    "day_name": self.scheduler._get_day_name(day),
                    "tasks": [],
                }
            daily_plan[day_key]["tasks"].append(task)

        return {
            "plan": list(daily_plan.values()),
            "total_tasks": len(tasks),
            "days": days,
            "tasks_per_day": round(len(tasks) / days, 1) if days else 0,
        }


# Singletons
_auto_scheduler: Optional[AutoScheduler] = None
_optimizer: Optional[ScheduleOptimizer] = None


def get_auto_scheduler() -> AutoScheduler:
    """Get singleton AutoScheduler instance."""
    global _auto_scheduler
    if _auto_scheduler is None:
        _auto_scheduler = AutoScheduler()
    return _auto_scheduler


def get_schedule_optimizer() -> ScheduleOptimizer:
    """Get singleton ScheduleOptimizer instance."""
    global _optimizer
    if _optimizer is None:
        _optimizer = ScheduleOptimizer()
    return _optimizer
