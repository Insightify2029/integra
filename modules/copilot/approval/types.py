"""
Approval Types
==============
Data types for the approval workflow.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import uuid


class ApprovalDecision(Enum):
    """Possible approval decisions."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"
    EXPIRED = "expired"


class RiskLevel(Enum):
    """Risk level of an action."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ApprovalPolicy:
    """Policy for automatic approval decisions."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""

    # Auto-approve conditions
    auto_approve_low_risk: bool = True
    auto_approve_categories: List[str] = field(default_factory=list)
    auto_reject_categories: List[str] = field(default_factory=list)

    # Timeouts
    approval_timeout_minutes: int = 60
    auto_reject_on_timeout: bool = False

    # Risk thresholds
    require_confirmation_above: RiskLevel = RiskLevel.MEDIUM

    # Additional rules
    max_changes_for_auto_approve: int = 5
    blocked_targets: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "auto_approve_low_risk": self.auto_approve_low_risk,
            "auto_approve_categories": self.auto_approve_categories,
            "auto_reject_categories": self.auto_reject_categories,
            "approval_timeout_minutes": self.approval_timeout_minutes,
            "require_confirmation_above": self.require_confirmation_above.value
        }


@dataclass
class ApprovalRequest:
    """A request for approval."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action_id: str = ""
    action_title: str = ""
    action_description: str = ""
    action_category: str = ""

    # Risk assessment
    risk_level: RiskLevel = RiskLevel.LOW
    risk_factors: List[str] = field(default_factory=list)

    # Impact
    affected_records: int = 0
    change_count: int = 0
    is_destructive: bool = False

    # Preview
    preview_summary: str = ""

    # State
    decision: ApprovalDecision = ApprovalDecision.PENDING
    decision_reason: str = ""
    decided_at: Optional[datetime] = None
    decided_by: str = ""

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "action_id": self.action_id,
            "action_title": self.action_title,
            "action_category": self.action_category,
            "risk_level": self.risk_level.value,
            "risk_factors": self.risk_factors,
            "affected_records": self.affected_records,
            "change_count": self.change_count,
            "is_destructive": self.is_destructive,
            "decision": self.decision.value,
            "decision_reason": self.decision_reason,
            "created_at": self.created_at.isoformat(),
            "decided_at": self.decided_at.isoformat() if self.decided_at else None
        }

    def approve(self, reason: str = "", by: str = "user"):
        """Approve the request."""
        self.decision = ApprovalDecision.APPROVED
        self.decision_reason = reason
        self.decided_at = datetime.now()
        self.decided_by = by

    def reject(self, reason: str = "", by: str = "user"):
        """Reject the request."""
        self.decision = ApprovalDecision.REJECTED
        self.decision_reason = reason
        self.decided_at = datetime.now()
        self.decided_by = by

    def auto_approve(self, reason: str = ""):
        """Auto-approve the request."""
        self.decision = ApprovalDecision.AUTO_APPROVED
        self.decision_reason = reason
        self.decided_at = datetime.now()
        self.decided_by = "system"

    def is_pending(self) -> bool:
        """Check if still pending."""
        return self.decision == ApprovalDecision.PENDING

    def is_approved(self) -> bool:
        """Check if approved."""
        return self.decision in [ApprovalDecision.APPROVED, ApprovalDecision.AUTO_APPROVED]

    def get_risk_label(self) -> str:
        """Get Arabic label for risk level."""
        labels = {
            RiskLevel.LOW: "منخفض",
            RiskLevel.MEDIUM: "متوسط",
            RiskLevel.HIGH: "عالي",
            RiskLevel.CRITICAL: "حرج"
        }
        return labels.get(self.risk_level, "غير معروف")
