"""
Productivity Pattern Learning
=============================
Learns user productivity patterns from task completion data.
"""

import json
import os
from datetime import datetime, date
from typing import Optional
from pathlib import Path


class ProductivityLearner:
    """Learns and predicts user productivity patterns."""

    def __init__(self, user_id: int = 1, data_dir: Optional[str] = None):
        self.user_id = user_id
        if data_dir is None:
            data_dir = str(Path.home() / ".integra" / "productivity")
        self.data_dir = data_dir
        self.patterns = {"tasks": [], "sessions": []}
        self._ensure_data_dir()
        self._load_patterns()

    def _ensure_data_dir(self):
        """Ensure data directory exists."""
        os.makedirs(self.data_dir, exist_ok=True)

    def _get_data_file(self) -> str:
        """Get path to user's data file."""
        return os.path.join(self.data_dir, f"user_{self.user_id}_patterns.json")

    def _load_patterns(self):
        """Load patterns from disk."""
        data_file = self._get_data_file()
        if os.path.exists(data_file):
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    self.patterns = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.patterns = {"tasks": [], "sessions": []}

    def _save_patterns(self):
        """Save patterns to disk."""
        data_file = self._get_data_file()
        try:
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(self.patterns, f, ensure_ascii=False, indent=2, default=str)
        except IOError:
            pass

    def record_task_completion(
        self,
        task_type: str,
        duration_minutes: int,
        completed_at: Optional[datetime] = None,
        was_delayed: bool = False,
    ):
        """Record a task completion for learning."""
        if completed_at is None:
            completed_at = datetime.now()

        self.patterns["tasks"].append({
            "type": task_type,
            "duration": duration_minutes,
            "hour": completed_at.hour,
            "day_of_week": completed_at.weekday(),
            "completed_at": completed_at.isoformat(),
            "was_delayed": was_delayed,
        })

        # Keep last 500 tasks
        if len(self.patterns["tasks"]) > 500:
            self.patterns["tasks"] = self.patterns["tasks"][-500:]

        self._save_patterns()

    def record_session(self, start_time: datetime, end_time: datetime, actions_count: int = 0):
        """Record a work session."""
        duration = (end_time - start_time).total_seconds() / 60

        self.patterns["sessions"].append({
            "start_hour": start_time.hour,
            "end_hour": end_time.hour,
            "day_of_week": start_time.weekday(),
            "duration_minutes": round(duration),
            "actions_count": actions_count,
            "date": start_time.date().isoformat(),
        })

        # Keep last 200 sessions
        if len(self.patterns["sessions"]) > 200:
            self.patterns["sessions"] = self.patterns["sessions"][-200:]

        self._save_patterns()

    def get_best_hours(self, top_n: int = 5) -> list:
        """Get the most productive hours for the user."""
        hour_stats = {}
        for task in self.patterns["tasks"]:
            hour = task["hour"]
            if hour not in hour_stats:
                hour_stats[hour] = {"count": 0, "total_duration": 0}
            hour_stats[hour]["count"] += 1
            hour_stats[hour]["total_duration"] += task["duration"]

        if not hour_stats:
            # Default productive hours
            return [
                {"hour": 10, "label": "10:00", "productivity": "افتراضي"},
                {"hour": 11, "label": "11:00", "productivity": "افتراضي"},
                {"hour": 9, "label": "09:00", "productivity": "افتراضي"},
            ]

        sorted_hours = sorted(
            hour_stats.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )

        return [
            {
                "hour": h,
                "label": f"{h:02d}:00",
                "tasks_completed": stats["count"],
                "avg_duration": round(stats["total_duration"] / stats["count"]),
            }
            for h, stats in sorted_hours[:top_n]
        ]

    def get_best_days(self, top_n: int = 5) -> list:
        """Get the most productive days of the week."""
        from .system_time import DAYS_AR

        day_stats = {}
        for task in self.patterns["tasks"]:
            day = task["day_of_week"]
            if day not in day_stats:
                day_stats[day] = {"count": 0, "total_duration": 0}
            day_stats[day]["count"] += 1
            day_stats[day]["total_duration"] += task["duration"]

        if not day_stats:
            return []

        sorted_days = sorted(
            day_stats.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )

        return [
            {
                "day": d,
                "day_name": DAYS_AR[d],
                "tasks_completed": stats["count"],
                "avg_duration": round(stats["total_duration"] / stats["count"]),
            }
            for d, stats in sorted_days[:top_n]
        ]

    def get_average_duration(self, task_type: str) -> int:
        """Get average duration for a task type in minutes."""
        tasks = [t for t in self.patterns["tasks"] if t["type"] == task_type]
        if not tasks:
            return 30  # Default 30 minutes
        return sum(t["duration"] for t in tasks) // len(tasks)

    def predict_completion_time(self, task_type: str) -> dict:
        """Predict how long a task will take and best time to start."""
        avg_duration = self.get_average_duration(task_type)
        best_hours = self.get_best_hours(3)
        task_count = len([t for t in self.patterns["tasks"] if t["type"] == task_type])

        if task_count >= 20:
            confidence = "high"
        elif task_count >= 5:
            confidence = "medium"
        else:
            confidence = "low"

        return {
            "estimated_minutes": avg_duration,
            "estimated_label": self._format_duration(avg_duration),
            "best_time_to_start": best_hours[0]["hour"] if best_hours else 10,
            "confidence": confidence,
            "based_on_tasks": task_count,
        }

    def get_delay_patterns(self) -> list:
        """Detect patterns in task delays."""
        delayed_tasks = [t for t in self.patterns["tasks"] if t.get("was_delayed", False)]

        if len(delayed_tasks) < 3:
            return []

        patterns = []

        # Check if delays happen on specific days
        day_delays = {}
        for task in delayed_tasks:
            day = task["day_of_week"]
            day_delays[day] = day_delays.get(day, 0) + 1

        if day_delays:
            from .system_time import DAYS_AR
            worst_day = max(day_delays, key=day_delays.get)
            if day_delays[worst_day] >= 3:
                patterns.append({
                    "type": "day_pattern",
                    "message": f"التأخير يحدث غالباً يوم {DAYS_AR[worst_day]}",
                    "day": worst_day,
                    "count": day_delays[worst_day],
                })

        # Check if delays happen at specific hours
        hour_delays = {}
        for task in delayed_tasks:
            hour = task["hour"]
            hour_delays[hour] = hour_delays.get(hour, 0) + 1

        if hour_delays:
            worst_hour = max(hour_delays, key=hour_delays.get)
            if hour_delays[worst_hour] >= 3:
                patterns.append({
                    "type": "hour_pattern",
                    "message": f"التأخير يحدث غالباً في الساعة {worst_hour:02d}:00",
                    "hour": worst_hour,
                    "count": hour_delays[worst_hour],
                })

        # Check if specific task types are always delayed
        type_delays = {}
        for task in delayed_tasks:
            task_type = task["type"]
            type_delays[task_type] = type_delays.get(task_type, 0) + 1

        for task_type, count in type_delays.items():
            total_of_type = len([t for t in self.patterns["tasks"] if t["type"] == task_type])
            if total_of_type > 0 and count / total_of_type > 0.5:
                patterns.append({
                    "type": "task_type_pattern",
                    "message": f"مهام '{task_type}' تتأخر بنسبة {count/total_of_type*100:.0f}%",
                    "task_type": task_type,
                    "delay_rate": round(count / total_of_type, 2),
                })

        return patterns

    def get_productivity_summary(self) -> dict:
        """Get overall productivity summary."""
        tasks = self.patterns["tasks"]
        sessions = self.patterns["sessions"]

        if not tasks:
            return {
                "total_tasks": 0,
                "message": "لا توجد بيانات كافية بعد. سيبدأ التعلم مع استخدامك للبرنامج.",
            }

        total_tasks = len(tasks)
        total_duration = sum(t["duration"] for t in tasks)
        delayed_count = len([t for t in tasks if t.get("was_delayed", False)])

        return {
            "total_tasks": total_tasks,
            "total_hours": round(total_duration / 60, 1),
            "avg_task_duration": round(total_duration / total_tasks),
            "delay_rate": round(delayed_count / total_tasks * 100, 1) if total_tasks else 0,
            "best_hours": self.get_best_hours(3),
            "best_days": self.get_best_days(3),
            "delay_patterns": self.get_delay_patterns(),
            "sessions_count": len(sessions),
        }

    @staticmethod
    def _format_duration(minutes: int) -> str:
        """Format duration in Arabic."""
        if minutes < 60:
            return f"{minutes} دقيقة"
        hours = minutes // 60
        remaining_mins = minutes % 60
        if remaining_mins == 0:
            return f"{hours} ساعة" if hours == 1 else f"{hours} ساعات"
        return f"{hours} ساعة و {remaining_mins} دقيقة"


# Singleton
_learner: Optional[ProductivityLearner] = None


def get_productivity_learner(user_id: int = 1) -> ProductivityLearner:
    """Get singleton ProductivityLearner instance."""
    global _learner
    if _learner is None or _learner.user_id != user_id:
        _learner = ProductivityLearner(user_id=user_id)
    return _learner
