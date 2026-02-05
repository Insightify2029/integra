"""
Time-based Triggers
===================
Automatic event triggers based on time conditions.
"""

import json
import os
import uuid
from datetime import date, datetime, timedelta
from typing import Optional, Callable
from pathlib import Path


class TimeTrigger:
    """Represents a single time-based trigger."""

    def __init__(
        self,
        trigger_type: str,
        action: str,
        target_date: Optional[date] = None,
        offset_days: int = 0,
        data: Optional[dict] = None,
        trigger_id: Optional[str] = None,
        enabled: bool = True,
        recurring_interval: Optional[str] = None,
    ):
        self.id = trigger_id or str(uuid.uuid4())[:8]
        self.type = trigger_type  # before_date, on_date, after_date, recurring
        self.action = action
        self.target_date = target_date
        self.offset_days = offset_days
        self.data = data or {}
        self.enabled = enabled
        self.recurring_interval = recurring_interval  # daily, weekly, monthly
        self.last_fired_at = None

    def to_dict(self) -> dict:
        """Serialize trigger to dict."""
        return {
            "id": self.id,
            "type": self.type,
            "action": self.action,
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "offset_days": self.offset_days,
            "data": self.data,
            "enabled": self.enabled,
            "recurring_interval": self.recurring_interval,
            "last_fired_at": self.last_fired_at.isoformat() if self.last_fired_at else None,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TimeTrigger":
        """Deserialize trigger from dict."""
        trigger = cls(
            trigger_type=d["type"],
            action=d["action"],
            target_date=date.fromisoformat(d["target_date"]) if d.get("target_date") else None,
            offset_days=d.get("offset_days", 0),
            data=d.get("data", {}),
            trigger_id=d.get("id"),
            enabled=d.get("enabled", True),
            recurring_interval=d.get("recurring_interval"),
        )
        if d.get("last_fired_at"):
            trigger.last_fired_at = datetime.fromisoformat(d["last_fired_at"])
        return trigger


class TimeTriggers:
    """Manages time-based triggers."""

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            data_dir = str(Path.home() / ".integra" / "triggers")
        self.data_dir = data_dir
        self.triggers: list[TimeTrigger] = []
        self._action_handlers: dict[str, Callable] = {}
        self._ensure_data_dir()
        self._load_triggers()

    def _ensure_data_dir(self):
        """Ensure data directory exists."""
        os.makedirs(self.data_dir, exist_ok=True)

    def _get_data_file(self) -> str:
        """Get path to triggers data file."""
        return os.path.join(self.data_dir, "triggers.json")

    def _load_triggers(self):
        """Load triggers from disk."""
        data_file = self._get_data_file()
        if os.path.exists(data_file):
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.triggers = [TimeTrigger.from_dict(t) for t in data]
            except (json.JSONDecodeError, IOError):
                self.triggers = []

    def _save_triggers(self):
        """Save triggers to disk."""
        data_file = self._get_data_file()
        try:
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(
                    [t.to_dict() for t in self.triggers],
                    f, ensure_ascii=False, indent=2
                )
        except IOError:
            pass

    def register_handler(self, action_type: str, handler: Callable):
        """Register a handler function for an action type."""
        self._action_handlers[action_type] = handler

    def register_trigger(self, trigger: TimeTrigger) -> str:
        """Register a new trigger. Returns trigger ID."""
        self.triggers.append(trigger)
        self._save_triggers()
        return trigger.id

    def remove_trigger(self, trigger_id: str) -> bool:
        """Remove a trigger by ID."""
        original_len = len(self.triggers)
        self.triggers = [t for t in self.triggers if t.id != trigger_id]
        if len(self.triggers) < original_len:
            self._save_triggers()
            return True
        return False

    def enable_trigger(self, trigger_id: str) -> bool:
        """Enable a trigger."""
        for trigger in self.triggers:
            if trigger.id == trigger_id:
                trigger.enabled = True
                self._save_triggers()
                return True
        return False

    def disable_trigger(self, trigger_id: str) -> bool:
        """Disable a trigger."""
        for trigger in self.triggers:
            if trigger.id == trigger_id:
                trigger.enabled = False
                self._save_triggers()
                return True
        return False

    def check_triggers(self) -> list:
        """Check all triggers and fire those that match."""
        today = date.today()
        now = datetime.now()
        fired = []

        for trigger in self.triggers:
            if not trigger.enabled:
                continue

            should_fire = False

            if trigger.type == "before_date" and trigger.target_date:
                target = trigger.target_date - timedelta(days=trigger.offset_days)
                should_fire = today >= target and (
                    trigger.last_fired_at is None or trigger.last_fired_at.date() < today
                )

            elif trigger.type == "on_date" and trigger.target_date:
                should_fire = today == trigger.target_date and (
                    trigger.last_fired_at is None or trigger.last_fired_at.date() < today
                )

            elif trigger.type == "after_date" and trigger.target_date:
                should_fire = today > trigger.target_date and (
                    trigger.last_fired_at is None or trigger.last_fired_at.date() < today
                )

            elif trigger.type == "recurring":
                should_fire = self._check_recurring(trigger, today)

            if should_fire:
                trigger.last_fired_at = now
                fired.append(trigger)
                self._execute_trigger(trigger)

        if fired:
            self._save_triggers()

        return [t.to_dict() for t in fired]

    def _check_recurring(self, trigger: TimeTrigger, today: date) -> bool:
        """Check if a recurring trigger should fire."""
        if trigger.last_fired_at and trigger.last_fired_at.date() >= today:
            return False

        interval = trigger.recurring_interval
        if interval == "daily":
            return True
        elif interval == "weekly":
            if trigger.last_fired_at:
                days_since = (today - trigger.last_fired_at.date()).days
                return days_since >= 7
            return True
        elif interval == "monthly":
            if trigger.last_fired_at:
                last_month = trigger.last_fired_at.date().month
                return today.month != last_month or today.year != trigger.last_fired_at.date().year
            return True
        return False

    def _execute_trigger(self, trigger: TimeTrigger):
        """Execute a trigger's action."""
        handler = self._action_handlers.get(trigger.action)
        if handler:
            try:
                handler(trigger.data)
            except Exception:
                pass

    # Convenience methods for common triggers

    def create_contract_expiry_trigger(
        self,
        employee_id: int,
        employee_name: str,
        expiry_date: date,
        days_before: int = 30,
    ) -> str:
        """Create a trigger for employee contract expiry."""
        trigger = TimeTrigger(
            trigger_type="before_date",
            action="notify_contract_expiry",
            target_date=expiry_date,
            offset_days=days_before,
            data={
                "employee_id": employee_id,
                "employee_name": employee_name,
                "expiry_date": expiry_date.isoformat(),
            },
        )
        return self.register_trigger(trigger)

    def create_reminder(
        self,
        reminder_date: date,
        message: str,
        task_id: Optional[int] = None,
    ) -> str:
        """Create a reminder trigger."""
        trigger = TimeTrigger(
            trigger_type="on_date",
            action="show_reminder",
            target_date=reminder_date,
            data={
                "message": message,
                "task_id": task_id,
            },
        )
        return self.register_trigger(trigger)

    def create_recurring_trigger(
        self,
        action: str,
        interval: str = "daily",
        data: Optional[dict] = None,
    ) -> str:
        """Create a recurring trigger."""
        trigger = TimeTrigger(
            trigger_type="recurring",
            action=action,
            recurring_interval=interval,
            data=data or {},
        )
        return self.register_trigger(trigger)

    def get_active_triggers(self) -> list:
        """Get all active (enabled) triggers."""
        return [t.to_dict() for t in self.triggers if t.enabled]

    def get_upcoming_triggers(self, days: int = 7) -> list:
        """Get triggers that will fire within the next N days."""
        today = date.today()
        cutoff = today + timedelta(days=days)
        upcoming = []

        for trigger in self.triggers:
            if not trigger.enabled:
                continue

            fire_date = None
            if trigger.type == "before_date" and trigger.target_date:
                fire_date = trigger.target_date - timedelta(days=trigger.offset_days)
            elif trigger.type == "on_date" and trigger.target_date:
                fire_date = trigger.target_date

            if fire_date and today <= fire_date <= cutoff:
                upcoming.append({
                    **trigger.to_dict(),
                    "fire_date": fire_date.isoformat(),
                    "days_until": (fire_date - today).days,
                })

        upcoming.sort(key=lambda x: x.get("days_until", 999))
        return upcoming


class TriggerExecutor:
    """Executes trigger actions and manages handlers."""

    def __init__(self):
        self._handlers = {}

    def register(self, action_type: str, handler: Callable):
        """Register an action handler."""
        self._handlers[action_type] = handler

    def execute(self, action_type: str, data: dict) -> bool:
        """Execute a trigger action."""
        handler = self._handlers.get(action_type)
        if handler:
            try:
                handler(data)
                return True
            except Exception:
                return False
        return False


# Singletons
_triggers: Optional[TimeTriggers] = None
_executor: Optional[TriggerExecutor] = None


def get_time_triggers() -> TimeTriggers:
    """Get singleton TimeTriggers instance."""
    global _triggers
    if _triggers is None:
        _triggers = TimeTriggers()
    return _triggers


def get_trigger_executor() -> TriggerExecutor:
    """Get singleton TriggerExecutor instance."""
    global _executor
    if _executor is None:
        _executor = TriggerExecutor()
    return _executor
