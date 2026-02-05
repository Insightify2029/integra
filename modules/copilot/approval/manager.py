"""
Approval Manager
================
Manages the approval workflow for AI actions.
"""

from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
import threading

from PyQt5.QtCore import QObject, pyqtSignal

from core.logging import app_logger
from .types import ApprovalRequest, ApprovalDecision, ApprovalPolicy, RiskLevel


class ApprovalManager(QObject):
    """
    Approval Workflow Manager.

    Features:
    - Risk-based approval policies
    - Auto-approve for low-risk actions
    - Timeout handling
    - Approval history

    Usage:
        manager = get_approval_manager()

        # Create approval request
        request = manager.create_request(
            action_id="123",
            action_title="Update employee",
            risk_level=RiskLevel.MEDIUM
        )

        # Check if auto-approved
        if request.is_approved():
            # Execute
            pass
        else:
            # Wait for user decision
            manager.approval_required.connect(show_approval_dialog)
    """

    _instance = None
    _lock = threading.Lock()

    # Signals
    approval_required = pyqtSignal(object)  # ApprovalRequest
    approval_granted = pyqtSignal(object)  # ApprovalRequest
    approval_denied = pyqtSignal(object)  # ApprovalRequest
    approval_expired = pyqtSignal(object)  # ApprovalRequest

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
        self._requests: Dict[str, ApprovalRequest] = {}
        self._policy: ApprovalPolicy = ApprovalPolicy(
            name="default",
            description="Default approval policy"
        )
        self._history: List[ApprovalRequest] = []
        self._approval_callbacks: Dict[str, Callable] = {}
        self._init_lock = threading.RLock()

        self._obj_initialized = True

    def get_policy(self) -> ApprovalPolicy:
        """Get the current approval policy."""
        return self._policy

    def set_policy(self, policy: ApprovalPolicy):
        """Set the approval policy."""
        self._policy = policy
        app_logger.info(f"Approval policy updated: {policy.name}")

    def create_request(
        self,
        action_id: str,
        action_title: str,
        action_description: str = "",
        action_category: str = "",
        risk_level: RiskLevel = RiskLevel.LOW,
        risk_factors: Optional[List[str]] = None,
        affected_records: int = 0,
        change_count: int = 0,
        is_destructive: bool = False,
        preview_summary: str = "",
        on_approved: Optional[Callable] = None,
        on_rejected: Optional[Callable] = None
    ) -> ApprovalRequest:
        """
        Create an approval request.

        Args:
            action_id: ID of the action
            action_title: Title of the action
            action_description: Description
            action_category: Category
            risk_level: Risk level
            risk_factors: List of risk factors
            affected_records: Number of affected records
            change_count: Number of changes
            is_destructive: Whether action is destructive
            preview_summary: Summary for preview
            on_approved: Callback when approved
            on_rejected: Callback when rejected

        Returns:
            ApprovalRequest (may be auto-approved)
        """
        request = ApprovalRequest(
            action_id=action_id,
            action_title=action_title,
            action_description=action_description,
            action_category=action_category,
            risk_level=risk_level,
            risk_factors=risk_factors or [],
            affected_records=affected_records,
            change_count=change_count,
            is_destructive=is_destructive,
            preview_summary=preview_summary
        )

        # Set expiration
        if self._policy.approval_timeout_minutes > 0:
            request.expires_at = datetime.now() + timedelta(
                minutes=self._policy.approval_timeout_minutes
            )

        # Check for auto-approval
        auto_decision = self._check_auto_approval(request)

        if auto_decision == ApprovalDecision.AUTO_APPROVED:
            request.auto_approve("Low risk action auto-approved by policy")
            if on_approved:
                on_approved(request)
        elif auto_decision == ApprovalDecision.REJECTED:
            request.reject("Action blocked by policy", by="system")
            if on_rejected:
                on_rejected(request)
        else:
            # Store for manual approval
            self._requests[request.id] = request
            if on_approved:
                self._approval_callbacks[f"{request.id}_approved"] = on_approved
            if on_rejected:
                self._approval_callbacks[f"{request.id}_rejected"] = on_rejected

            # Emit signal for UI
            self.approval_required.emit(request)

        app_logger.info(f"Approval request created: {request.id} - {action_title} - {request.decision.value}")

        return request

    def _check_auto_approval(self, request: ApprovalRequest) -> ApprovalDecision:
        """Check if request should be auto-approved or rejected."""
        policy = self._policy

        # Check blocked categories
        if request.action_category in policy.auto_reject_categories:
            return ApprovalDecision.REJECTED

        # Check destructive actions
        if request.is_destructive and request.risk_level.value in ["high", "critical"]:
            return ApprovalDecision.PENDING

        # Check risk level
        if request.risk_level == RiskLevel.LOW and policy.auto_approve_low_risk:
            if request.change_count <= policy.max_changes_for_auto_approve:
                return ApprovalDecision.AUTO_APPROVED

        # Check auto-approve categories
        if request.action_category in policy.auto_approve_categories:
            if request.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]:
                return ApprovalDecision.AUTO_APPROVED

        return ApprovalDecision.PENDING

    def approve(self, request_id: str, reason: str = "") -> bool:
        """
        Approve a request.

        Args:
            request_id: Request ID
            reason: Approval reason

        Returns:
            True if approved
        """
        request = self._requests.get(request_id)
        if not request:
            return False

        if not request.is_pending():
            return False

        request.approve(reason)

        # Call callback
        callback = self._approval_callbacks.get(f"{request_id}_approved")
        if callback:
            try:
                callback(request)
            except Exception as e:
                app_logger.error(f"Approval callback error: {e}")

        # Move to history
        self._history.append(request)
        del self._requests[request_id]

        app_logger.info(f"Request approved: {request_id}")
        self.approval_granted.emit(request)

        return True

    def reject(self, request_id: str, reason: str = "") -> bool:
        """
        Reject a request.

        Args:
            request_id: Request ID
            reason: Rejection reason

        Returns:
            True if rejected
        """
        request = self._requests.get(request_id)
        if not request:
            return False

        if not request.is_pending():
            return False

        request.reject(reason)

        # Call callback
        callback = self._approval_callbacks.get(f"{request_id}_rejected")
        if callback:
            try:
                callback(request)
            except Exception as e:
                app_logger.error(f"Rejection callback error: {e}")

        # Move to history
        self._history.append(request)
        del self._requests[request_id]

        app_logger.info(f"Request rejected: {request_id} - {reason}")
        self.approval_denied.emit(request)

        return True

    def get_pending_requests(self) -> List[ApprovalRequest]:
        """Get all pending requests."""
        return list(self._requests.values())

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get a specific request."""
        return self._requests.get(request_id)

    def get_history(self, limit: int = 100) -> List[ApprovalRequest]:
        """Get approval history."""
        return self._history[-limit:]

    def check_expirations(self):
        """Check and handle expired requests."""
        now = datetime.now()
        expired = []

        for request_id, request in list(self._requests.items()):
            if request.expires_at and now > request.expires_at:
                if self._policy.auto_reject_on_timeout:
                    request.decision = ApprovalDecision.EXPIRED
                    request.decision_reason = "Request expired"
                    request.decided_at = now
                    expired.append(request_id)

        for request_id in expired:
            request = self._requests.pop(request_id)
            self._history.append(request)
            self.approval_expired.emit(request)
            app_logger.info(f"Request expired: {request_id}")

    def assess_risk(
        self,
        action_category: str,
        change_count: int,
        affected_records: int,
        is_destructive: bool
    ) -> tuple[RiskLevel, List[str]]:
        """
        Assess the risk level of an action.

        Returns:
            (RiskLevel, list of risk factors)
        """
        risk_factors = []
        risk_score = 0

        # Destructive actions
        if is_destructive:
            risk_factors.append("إجراء تدميري (حذف)")
            risk_score += 30

        # Change count
        if change_count > 10:
            risk_factors.append(f"عدد كبير من التغييرات ({change_count})")
            risk_score += 20
        elif change_count > 5:
            risk_score += 10

        # Affected records
        if affected_records > 100:
            risk_factors.append(f"تأثير على {affected_records} سجل")
            risk_score += 30
        elif affected_records > 10:
            risk_score += 15

        # Category-based risk
        high_risk_categories = ["data_delete", "system_config", "file_delete"]
        if action_category in high_risk_categories:
            risk_factors.append(f"فئة عالية المخاطر ({action_category})")
            risk_score += 20

        # Determine level
        if risk_score >= 50:
            level = RiskLevel.CRITICAL
        elif risk_score >= 30:
            level = RiskLevel.HIGH
        elif risk_score >= 15:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW

        return level, risk_factors


# Singleton instance
_manager: Optional[ApprovalManager] = None


def get_approval_manager() -> ApprovalManager:
    """Get the singleton approval manager instance."""
    global _manager
    if _manager is None:
        _manager = ApprovalManager()
    return _manager


def request_approval(
    action_id: str,
    action_title: str,
    **kwargs
) -> ApprovalRequest:
    """Request approval (convenience function)."""
    return get_approval_manager().create_request(action_id, action_title, **kwargs)
