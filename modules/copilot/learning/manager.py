"""
Learning System Manager
=======================
Manages learning from user behavior and preferences.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import json
import os

from PyQt5.QtCore import QObject, pyqtSignal

from core.logging import app_logger
from .types import (
    LearningEvent, UserPreference, LearnedPattern,
    EventType, PatternType
)


class LearningSystem(QObject):
    """
    Learning System for AI Copilot.

    Learns from user behavior to:
    - Predict user needs
    - Personalize suggestions
    - Improve AI responses
    - Optimize workflows

    Usage:
        system = get_learning_system()
        system.initialize()

        # Record events
        system.record_event(EventType.ACTION_APPROVED, "create", "employee")

        # Get preferences
        pref = system.get_preference("default_module")

        # Get suggestions based on patterns
        suggestions = system.get_suggestions_for_context(context)
    """

    _instance = None
    _lock = threading.Lock()

    # Signals
    pattern_detected = pyqtSignal(object)  # LearnedPattern
    preference_updated = pyqtSignal(object)  # UserPreference

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._obj_initialized = False
        return cls._instance

    def __init__(self):
        if hasattr(self, '_obj_initialized') and self._obj_initialized:
            return

        super().__init__()
        self._events: List[LearningEvent] = []
        self._preferences: Dict[str, UserPreference] = {}
        self._patterns: Dict[str, LearnedPattern] = {}
        self._action_counts: Dict[str, int] = defaultdict(int)
        self._query_history: List[str] = []
        self._data_path: Optional[str] = None
        self._ready = False
        self._init_lock = threading.RLock()

        self._obj_initialized = True

    def initialize(self, data_path: Optional[str] = None) -> bool:
        """Initialize the learning system."""
        with self._init_lock:
            if self._ready:
                return True

            try:
                self._data_path = data_path or self._get_default_data_path()
                self._load_data()
                self._ready = True
                app_logger.info("Learning system initialized")
                return True
            except Exception as e:
                app_logger.error(f"Failed to initialize learning system: {e}")
                return False

    def _get_default_data_path(self) -> str:
        """Get default data storage path."""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        data_dir = os.path.join(base_dir, "data", "copilot")
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, "learning_data.json")

    def is_ready(self) -> bool:
        """Check if system is ready."""
        return self._ready

    def record_event(
        self,
        event_type: EventType,
        action: str = "",
        category: str = "",
        value: Any = None,
        context: Optional[Dict[str, Any]] = None
    ) -> LearningEvent:
        """
        Record a learning event.

        Args:
            event_type: Type of event
            action: Action taken
            category: Category of action
            value: Associated value
            context: Additional context

        Returns:
            Created LearningEvent
        """
        event = LearningEvent(
            event_type=event_type,
            action=action,
            category=category,
            value=value,
            context=context or {}
        )

        self._events.append(event)
        self._action_counts[f"{category}:{action}"] += 1

        # Keep last 1000 events
        if len(self._events) > 1000:
            self._events = self._events[-1000:]

        # Process event for learning
        self._process_event(event)

        # Periodic save
        if len(self._events) % 50 == 0:
            self._save_data()

        return event

    def _process_event(self, event: LearningEvent):
        """Process an event for learning."""
        # Learn from queries
        if event.event_type == EventType.QUERY_ACCEPTED:
            self._learn_from_query(event)

        # Learn from corrections
        elif event.event_type == EventType.CORRECTION_MADE:
            self._learn_from_correction(event)

        # Learn from actions
        elif event.event_type in [EventType.ACTION_APPROVED, EventType.ACTION_REJECTED]:
            self._learn_from_action(event)

        # Learn from suggestions
        elif event.event_type in [EventType.SUGGESTION_CLICKED, EventType.SUGGESTION_DISMISSED]:
            self._learn_from_suggestion(event)

        # Detect patterns
        self._detect_patterns()

    def _learn_from_query(self, event: LearningEvent):
        """Learn from accepted queries."""
        query = event.value
        if query:
            self._query_history.append(query)
            if len(self._query_history) > 100:
                self._query_history = self._query_history[-100:]

    def _learn_from_correction(self, event: LearningEvent):
        """Learn from user corrections."""
        correction = event.context.get("correction", {})
        original = correction.get("original")
        corrected = correction.get("corrected")

        if original and corrected:
            # Store correction as preference
            key = f"correction:{original[:50]}"
            self.set_preference(key, corrected, source="correction")

    def _learn_from_action(self, event: LearningEvent):
        """Learn from action approvals/rejections."""
        action_key = f"{event.category}:{event.action}"

        if event.event_type == EventType.ACTION_APPROVED:
            # Reinforce this action pattern
            pref = self.get_preference(f"action:{action_key}")
            if pref:
                pref.reinforce()
            else:
                self.set_preference(f"action:{action_key}", True, confidence=0.5)

        elif event.event_type == EventType.ACTION_REJECTED:
            # Weaken this action pattern
            pref = self.get_preference(f"action:{action_key}")
            if pref:
                pref.weaken()

    def _learn_from_suggestion(self, event: LearningEvent):
        """Learn from suggestion interactions."""
        suggestion_type = event.context.get("suggestion_type")

        if event.event_type == EventType.SUGGESTION_CLICKED:
            pref = self.get_preference(f"suggestion:{suggestion_type}")
            if pref:
                pref.reinforce()
            else:
                self.set_preference(f"suggestion:{suggestion_type}", True, confidence=0.6)

        elif event.event_type == EventType.SUGGESTION_DISMISSED:
            pref = self.get_preference(f"suggestion:{suggestion_type}")
            if pref:
                pref.weaken()

    def _detect_patterns(self):
        """Detect behavioral patterns from events."""
        if len(self._events) < 10:
            return

        recent = self._events[-20:]

        # Detect action sequences
        actions = [e for e in recent if e.event_type in [
            EventType.ACTION_APPROVED,
            EventType.FEATURE_USED
        ]]

        if len(actions) >= 3:
            # Look for repeated sequences
            sequence = [f"{a.category}:{a.action}" for a in actions[-3:]]
            sequence_key = "->".join(sequence)

            pattern_id = f"sequence:{sequence_key}"
            if pattern_id in self._patterns:
                self._patterns[pattern_id].observe()
            else:
                pattern = LearnedPattern(
                    id=pattern_id,
                    pattern_type=PatternType.ACTION,
                    name=f"Action Sequence",
                    trigger={"sequence": sequence[:-1]},
                    action={"next": sequence[-1]},
                    frequency=1,
                    confidence=0.3
                )
                self._patterns[pattern_id] = pattern
                self.pattern_detected.emit(pattern)

    def set_preference(
        self,
        key: str,
        value: Any,
        source: str = "learned",
        confidence: float = 0.5
    ) -> UserPreference:
        """
        Set a user preference.

        Args:
            key: Preference key
            value: Preference value
            source: Source of preference
            confidence: Initial confidence

        Returns:
            UserPreference
        """
        if key in self._preferences:
            pref = self._preferences[key]
            pref.value = value
            pref.reinforce()
        else:
            pref = UserPreference(
                key=key,
                value=value,
                confidence=confidence,
                source=source
            )
            self._preferences[key] = pref

        self.preference_updated.emit(pref)
        return pref

    def get_preference(self, key: str) -> Optional[UserPreference]:
        """Get a user preference."""
        return self._preferences.get(key)

    def get_preference_value(self, key: str, default: Any = None) -> Any:
        """Get a preference value with default."""
        pref = self._preferences.get(key)
        return pref.value if pref else default

    def get_all_preferences(self) -> Dict[str, UserPreference]:
        """Get all preferences."""
        return dict(self._preferences)

    def get_high_confidence_preferences(self, min_confidence: float = 0.7) -> Dict[str, UserPreference]:
        """Get preferences above confidence threshold."""
        return {
            k: v for k, v in self._preferences.items()
            if v.confidence >= min_confidence
        }

    def get_common_actions(self, limit: int = 10) -> List[tuple]:
        """Get most common actions."""
        sorted_actions = sorted(
            self._action_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_actions[:limit]

    def get_suggestions_for_context(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get suggestions based on current context.

        Args:
            context: Current application context

        Returns:
            List of suggestions
        """
        suggestions = []

        current_screen = context.get("screen", "")
        current_module = context.get("module", "")

        # Check for relevant patterns
        for pattern in self._patterns.values():
            if pattern.confidence < 0.5:
                continue

            trigger = pattern.trigger
            if trigger.get("screen") == current_screen or trigger.get("module") == current_module:
                suggestions.append({
                    "type": "pattern",
                    "title": pattern.name,
                    "action": pattern.action,
                    "confidence": pattern.confidence
                })

        # Check common actions for this context
        for action_key, count in self._action_counts.items():
            if count > 5:
                category, action = action_key.split(":", 1) if ":" in action_key else ("", action_key)
                if category == current_module:
                    suggestions.append({
                        "type": "common_action",
                        "title": f"إجراء شائع: {action}",
                        "action": action,
                        "count": count
                    })

        return suggestions[:5]

    def _load_data(self):
        """Load learning data from disk."""
        if not self._data_path or not os.path.exists(self._data_path):
            return

        try:
            with open(self._data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Load preferences
            for pref_data in data.get("preferences", []):
                pref = UserPreference(
                    id=pref_data["id"],
                    key=pref_data["key"],
                    value=pref_data["value"],
                    confidence=pref_data["confidence"],
                    source=pref_data.get("source", "learned"),
                    observation_count=pref_data.get("observation_count", 1)
                )
                self._preferences[pref.key] = pref

            # Load action counts
            self._action_counts = defaultdict(int, data.get("action_counts", {}))

            # Load query history
            self._query_history = data.get("query_history", [])

            app_logger.debug(f"Loaded {len(self._preferences)} preferences")

        except Exception as e:
            app_logger.error(f"Error loading learning data: {e}")

    def _save_data(self):
        """Save learning data to disk."""
        if not self._data_path:
            return

        try:
            data = {
                "version": 1,
                "saved_at": datetime.now().isoformat(),
                "preferences": [p.to_dict() for p in self._preferences.values()],
                "action_counts": dict(self._action_counts),
                "query_history": self._query_history[-50:]
            }

            with open(self._data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            app_logger.error(f"Error saving learning data: {e}")

    def clear(self):
        """Clear all learning data."""
        self._events.clear()
        self._preferences.clear()
        self._patterns.clear()
        self._action_counts.clear()
        self._query_history.clear()

        if self._data_path and os.path.exists(self._data_path):
            os.remove(self._data_path)


# Singleton instance
_system: Optional[LearningSystem] = None


def get_learning_system() -> LearningSystem:
    """Get the singleton learning system instance."""
    global _system
    if _system is None:
        _system = LearningSystem()
    return _system


def record_event(event_type: EventType, **kwargs) -> LearningEvent:
    """Record an event (convenience function)."""
    system = get_learning_system()
    if not system.is_ready():
        system.initialize()
    return system.record_event(event_type, **kwargs)
