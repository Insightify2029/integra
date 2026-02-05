"""
Learning System
===============
System for learning from user behavior and preferences.
"""

from .manager import LearningSystem, get_learning_system
from .types import UserPreference, LearningEvent, PatternType

__all__ = [
    "LearningSystem",
    "get_learning_system",
    "UserPreference",
    "LearningEvent",
    "PatternType"
]
