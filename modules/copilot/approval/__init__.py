"""
Approval Workflow
=================
Workflow for approving AI-suggested actions.
"""

from .manager import ApprovalManager, get_approval_manager
from .types import ApprovalRequest, ApprovalDecision, ApprovalPolicy

__all__ = [
    "ApprovalManager",
    "get_approval_manager",
    "ApprovalRequest",
    "ApprovalDecision",
    "ApprovalPolicy"
]
