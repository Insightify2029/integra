"""
Learning Types
==============
Data types for the learning system.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import uuid


class PatternType(Enum):
    """Types of learned patterns."""
    NAVIGATION = "navigation"  # Screen navigation patterns
    ACTION = "action"  # Common actions
    QUERY = "query"  # Common queries
    TIME = "time"  # Time-based patterns
    PREFERENCE = "preference"  # User preferences
    CORRECTION = "correction"  # User corrections to AI


class EventType(Enum):
    """Types of learning events."""
    QUERY_ACCEPTED = "query_accepted"
    QUERY_REJECTED = "query_rejected"
    ACTION_APPROVED = "action_approved"
    ACTION_REJECTED = "action_rejected"
    SUGGESTION_CLICKED = "suggestion_clicked"
    SUGGESTION_DISMISSED = "suggestion_dismissed"
    CORRECTION_MADE = "correction_made"
    PREFERENCE_SET = "preference_set"
    SCREEN_VISITED = "screen_visited"
    FEATURE_USED = "feature_used"


@dataclass
class LearningEvent:
    """An event to learn from."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.FEATURE_USED
    category: str = ""
    action: str = ""
    value: Any = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "category": self.category,
            "action": self.action,
            "value": str(self.value) if self.value is not None else None,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id
        }


@dataclass
class UserPreference:
    """A learned user preference."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    key: str = ""
    value: Any = None
    confidence: float = 0.0  # 0.0 to 1.0
    source: str = "learned"  # learned, explicit, default
    learned_from: List[str] = field(default_factory=list)  # Event IDs
    first_observed: datetime = field(default_factory=datetime.now)
    last_observed: datetime = field(default_factory=datetime.now)
    observation_count: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value,
            "confidence": self.confidence,
            "source": self.source,
            "observation_count": self.observation_count,
            "first_observed": self.first_observed.isoformat(),
            "last_observed": self.last_observed.isoformat()
        }

    def reinforce(self):
        """Reinforce the preference (increases confidence)."""
        self.observation_count += 1
        self.last_observed = datetime.now()
        # Increase confidence with diminishing returns
        self.confidence = min(1.0, self.confidence + (1.0 - self.confidence) * 0.1)

    def weaken(self):
        """Weaken the preference (decreases confidence)."""
        self.confidence = max(0.0, self.confidence - 0.1)


@dataclass
class LearnedPattern:
    """A learned behavioral pattern."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pattern_type: PatternType = PatternType.ACTION
    name: str = ""
    description: str = ""

    # Pattern data
    trigger: Dict[str, Any] = field(default_factory=dict)  # What triggers this pattern
    action: Dict[str, Any] = field(default_factory=dict)  # What action is taken
    frequency: int = 0
    confidence: float = 0.0

    # Time patterns
    common_hours: List[int] = field(default_factory=list)
    common_days: List[int] = field(default_factory=list)  # 0=Monday, 6=Sunday

    # Timestamps
    first_observed: datetime = field(default_factory=datetime.now)
    last_observed: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "pattern_type": self.pattern_type.value,
            "name": self.name,
            "trigger": self.trigger,
            "action": self.action,
            "frequency": self.frequency,
            "confidence": self.confidence,
            "common_hours": self.common_hours,
            "common_days": self.common_days
        }

    def observe(self):
        """Record an observation of this pattern."""
        self.frequency += 1
        self.last_observed = datetime.now()
        self.confidence = min(1.0, self.confidence + 0.05)

        # Track time patterns
        hour = datetime.now().hour
        day = datetime.now().weekday()

        if hour not in self.common_hours:
            self.common_hours.append(hour)
            self.common_hours = self.common_hours[-5:]  # Keep last 5

        if day not in self.common_days:
            self.common_days.append(day)
            self.common_days = self.common_days[-3:]  # Keep last 3
