"""
Deadline Predictor
==================
Predicts whether deadlines will be met and generates early warnings.
"""

from datetime import date, timedelta
from typing import Optional


class DeadlinePredictor:
    """Predicts deadline risks and generates alerts."""

    def __init__(self, productivity_learner=None, working_calendar=None):
        self._learner = productivity_learner
        self._calendar = working_calendar

    @property
    def learner(self):
        if self._learner is None:
            from .productivity_learner import get_productivity_learner
            self._learner = get_productivity_learner()
        return self._learner

    @property
    def calendar(self):
        if self._calendar is None:
            from .working_calendar import get_working_calendar
            self._calendar = get_working_calendar()
        return self._calendar

    def will_meet_deadline(
        self,
        task_type: str,
        deadline: date,
        start_date: Optional[date] = None,
    ) -> dict:
        """Predict whether a task will be completed by its deadline."""
        if start_date is None:
            start_date = date.today()

        # Calculate available working days
        available_days = self.calendar.working_days_between(start_date, deadline)

        # Estimate required time
        estimated_minutes = self.learner.get_average_duration(task_type)
        estimated_days = estimated_minutes / (8 * 60)  # Convert minutes to work days (8h/day)

        # Calculate margin
        margin = available_days - estimated_days

        if margin >= 2:
            status = "safe"
            message = "وقت كافي لإنهاء المهمة"
            icon = "safe"
        elif margin >= 0:
            status = "tight"
            message = "الوقت ضيق - ابدأ قريباً"
            icon = "warning"
        else:
            status = "at_risk"
            message = "خطر تأخير! محتاج تبدأ اليوم أو تطلب تمديد"
            icon = "danger"

        recommended_start = self._calculate_recommended_start(deadline, estimated_days)

        return {
            "status": status,
            "icon": icon,
            "message": message,
            "available_days": available_days,
            "estimated_days": round(estimated_days, 1),
            "margin_days": round(margin, 1),
            "recommended_start": recommended_start.isoformat() if recommended_start else None,
            "deadline": deadline.isoformat(),
        }

    def get_at_risk_tasks(self, tasks: list) -> list:
        """Get tasks that are at risk of being late."""
        at_risk = []
        for task in tasks:
            task_type = task.get("type", "general")
            deadline = task.get("deadline")
            if deadline is None:
                continue

            if isinstance(deadline, str):
                deadline = date.fromisoformat(deadline)

            prediction = self.will_meet_deadline(task_type, deadline)
            if prediction["status"] in ("tight", "at_risk"):
                at_risk.append({
                    "task": task,
                    "prediction": prediction,
                })

        # Sort by margin (most at risk first)
        at_risk.sort(key=lambda x: x["prediction"]["margin_days"])
        return at_risk

    def generate_alerts(self, tasks: list) -> list:
        """Generate deadline alerts for a list of tasks."""
        alerts = []

        for task in tasks:
            task_type = task.get("type", "general")
            deadline = task.get("deadline")
            if deadline is None:
                continue

            if isinstance(deadline, str):
                deadline = date.fromisoformat(deadline)

            prediction = self.will_meet_deadline(task_type, deadline)
            task_title = task.get("title", task.get("name", "مهمة"))

            if prediction["status"] == "at_risk":
                alerts.append({
                    "type": "deadline_risk",
                    "severity": "high",
                    "task_id": task.get("id"),
                    "title": task_title,
                    "message": f"مهمة '{task_title}' معرضة للتأخير!",
                    "action": "ابدأ اليوم أو اطلب تمديد",
                    "deadline": deadline.isoformat(),
                    "margin_days": prediction["margin_days"],
                })
            elif prediction["status"] == "tight":
                alerts.append({
                    "type": "deadline_warning",
                    "severity": "medium",
                    "task_id": task.get("id"),
                    "title": task_title,
                    "message": f"مهمة '{task_title}' - الوقت ضيق",
                    "action": f"ابدأ قبل {prediction['recommended_start']}",
                    "deadline": deadline.isoformat(),
                    "margin_days": prediction["margin_days"],
                })

        # Sort by severity (high first)
        severity_order = {"high": 0, "medium": 1, "low": 2}
        alerts.sort(key=lambda x: severity_order.get(x["severity"], 3))
        return alerts

    def _calculate_recommended_start(self, deadline: date, estimated_days: float) -> Optional[date]:
        """Calculate the recommended start date to meet a deadline."""
        # Add 1 day buffer
        days_needed = int(estimated_days) + 1
        try:
            return self.calendar.subtract_working_days(deadline, days_needed)
        except Exception:
            return deadline - timedelta(days=days_needed + 2)


class AlertGenerator:
    """Generates time-based alerts from various sources."""

    def __init__(self):
        self._predictor = None

    @property
    def predictor(self) -> DeadlinePredictor:
        if self._predictor is None:
            self._predictor = DeadlinePredictor()
        return self._predictor

    def generate_daily_alerts(self, tasks: list) -> list:
        """Generate all daily alerts."""
        alerts = []

        # Deadline alerts
        alerts.extend(self.predictor.generate_alerts(tasks))

        # Check for today's deadlines
        today = date.today()
        for task in tasks:
            deadline = task.get("deadline")
            if deadline is None:
                continue
            if isinstance(deadline, str):
                deadline = date.fromisoformat(deadline)
            if deadline == today:
                alerts.append({
                    "type": "deadline_today",
                    "severity": "high",
                    "task_id": task.get("id"),
                    "title": task.get("title", "مهمة"),
                    "message": f"اليوم آخر موعد لمهمة '{task.get('title', 'مهمة')}'!",
                    "action": "أنهِ المهمة اليوم",
                })

        return alerts

    def format_alert(self, alert: dict) -> str:
        """Format an alert as Arabic text."""
        severity_icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        icon = severity_icons.get(alert.get("severity", "low"), "ℹ️")
        return f"{icon} {alert['message']}"


# Singletons
_predictor: Optional[DeadlinePredictor] = None
_alert_gen: Optional[AlertGenerator] = None


def get_deadline_predictor() -> DeadlinePredictor:
    """Get singleton DeadlinePredictor instance."""
    global _predictor
    if _predictor is None:
        _predictor = DeadlinePredictor()
    return _predictor


def get_alert_generator() -> AlertGenerator:
    """Get singleton AlertGenerator instance."""
    global _alert_gen
    if _alert_gen is None:
        _alert_gen = AlertGenerator()
    return _alert_gen
