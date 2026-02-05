"""
Action Sandbox Manager
======================
Manages the sandbox for previewing and executing AI actions.
"""

from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import threading

from PyQt5.QtCore import QObject, pyqtSignal

from core.logging import app_logger
from .types import SandboxAction, SandboxSession, SandboxState, ActionCategory, ActionChange


class ActionSandbox(QObject):
    """
    Action Sandbox Manager.

    Provides a safe environment for AI-suggested actions:
    - Preview changes before applying
    - Approve/reject workflow
    - Execute with rollback support
    - Audit trail

    Usage:
        sandbox = get_action_sandbox()

        # Create an action
        action = sandbox.create_action(
            category=ActionCategory.DATA_UPDATE,
            title="تحديث بيانات الموظف",
            target_type="employee",
            target_id="123"
        )

        # Add changes
        action.add_change("salary", 5000, 6000)

        # Submit for approval
        sandbox.submit_for_approval(action.id)

        # Approve and execute
        sandbox.approve_action(action.id)
        result = sandbox.execute_action(action.id)
    """

    _instance = None
    _lock = threading.Lock()

    # Signals
    action_created = pyqtSignal(object)  # SandboxAction
    action_submitted = pyqtSignal(object)  # SandboxAction
    action_approved = pyqtSignal(object)  # SandboxAction
    action_rejected = pyqtSignal(object)  # SandboxAction
    action_executed = pyqtSignal(object, bool)  # SandboxAction, success
    action_rolled_back = pyqtSignal(object)  # SandboxAction

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
        self._sessions: Dict[str, SandboxSession] = {}
        self._current_session: Optional[SandboxSession] = None
        self._action_executors: Dict[ActionCategory, Callable] = {}
        self._rollback_executors: Dict[ActionCategory, Callable] = {}
        self._init_lock = threading.RLock()

        # Create default session
        self._create_new_session()

        self._obj_initialized = True

    def _create_new_session(self, description: str = "") -> SandboxSession:
        """Create a new sandbox session."""
        session = SandboxSession(description=description)
        self._sessions[session.id] = session
        self._current_session = session
        return session

    def get_current_session(self) -> SandboxSession:
        """Get the current session."""
        if not self._current_session or not self._current_session.is_active:
            self._create_new_session()
        return self._current_session

    def create_action(
        self,
        category: ActionCategory,
        title: str,
        description: str = "",
        target_type: str = "",
        target_id: Optional[str] = None,
        target_name: str = "",
        data: Optional[Dict[str, Any]] = None
    ) -> SandboxAction:
        """
        Create a new sandbox action.

        Args:
            category: Action category
            title: Action title
            description: Action description
            target_type: Type of target (e.g., "employee")
            target_id: ID of the target
            target_name: Name of the target
            data: Additional data

        Returns:
            Created SandboxAction
        """
        action = SandboxAction(
            category=category,
            title=title,
            description=description,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            data=data or {}
        )

        session = self.get_current_session()
        session.add_action(action)

        app_logger.info(f"Created sandbox action: {action.id} - {title}")
        self.action_created.emit(action)

        return action

    def get_action(self, action_id: str) -> Optional[SandboxAction]:
        """Get an action by ID."""
        session = self.get_current_session()
        return session.get_action(action_id)

    def update_action(
        self,
        action_id: str,
        changes: Optional[List[Dict[str, Any]]] = None,
        preview_before: Optional[str] = None,
        preview_after: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update an action.

        Args:
            action_id: Action ID
            changes: List of changes (field, old_value, new_value)
            preview_before: Before preview text
            preview_after: After preview text
            data: Additional data

        Returns:
            True if updated
        """
        action = self.get_action(action_id)
        if not action:
            return False

        if action.state not in [SandboxState.DRAFT, SandboxState.PENDING_APPROVAL]:
            app_logger.warning(f"Cannot update action in state: {action.state}")
            return False

        if changes:
            for change in changes:
                action.add_change(
                    field=change.get("field", ""),
                    old_value=change.get("old_value"),
                    new_value=change.get("new_value"),
                    change_type=change.get("change_type", "update")
                )

        if preview_before is not None or preview_after is not None:
            action.set_preview(
                preview_before or action.preview_before,
                preview_after or action.preview_after
            )

        if data:
            action.data.update(data)
            action.updated_at = datetime.now()

        return True

    def submit_for_approval(self, action_id: str) -> bool:
        """
        Submit an action for approval.

        Args:
            action_id: Action ID

        Returns:
            True if submitted
        """
        action = self.get_action(action_id)
        if not action:
            return False

        if action.state != SandboxState.DRAFT:
            return False

        action.state = SandboxState.PENDING_APPROVAL
        action.updated_at = datetime.now()

        app_logger.info(f"Action submitted for approval: {action_id}")
        self.action_submitted.emit(action)

        return True

    def approve_action(self, action_id: str) -> bool:
        """
        Approve an action.

        Args:
            action_id: Action ID

        Returns:
            True if approved
        """
        action = self.get_action(action_id)
        if not action:
            return False

        if action.state != SandboxState.PENDING_APPROVAL:
            return False

        action.approve()

        app_logger.info(f"Action approved: {action_id}")
        self.action_approved.emit(action)

        return True

    def reject_action(self, action_id: str, reason: str = "") -> bool:
        """
        Reject an action.

        Args:
            action_id: Action ID
            reason: Rejection reason

        Returns:
            True if rejected
        """
        action = self.get_action(action_id)
        if not action:
            return False

        if action.state != SandboxState.PENDING_APPROVAL:
            return False

        action.reject()
        if reason:
            action.error_message = reason

        app_logger.info(f"Action rejected: {action_id} - {reason}")
        self.action_rejected.emit(action)

        return True

    def execute_action(self, action_id: str) -> Dict[str, Any]:
        """
        Execute an approved action.

        Args:
            action_id: Action ID

        Returns:
            Execution result
        """
        action = self.get_action(action_id)
        if not action:
            return {"success": False, "error": "Action not found"}

        if action.state != SandboxState.APPROVED:
            return {"success": False, "error": "Action not approved"}

        action.state = SandboxState.EXECUTING
        action.updated_at = datetime.now()

        try:
            # Get executor
            executor = action.executor or self._action_executors.get(action.category)

            if not executor:
                # Default execution based on category
                result = self._default_execute(action)
            else:
                result = executor(action)

            action.state = SandboxState.COMPLETED
            action.executed_at = datetime.now()

            app_logger.info(f"Action executed: {action_id}")
            self.action_executed.emit(action, True)

            return {"success": True, "result": result}

        except Exception as e:
            action.state = SandboxState.FAILED
            action.error_message = str(e)
            action.updated_at = datetime.now()

            app_logger.error(f"Action execution failed: {action_id} - {e}")
            self.action_executed.emit(action, False)

            return {"success": False, "error": str(e)}

    def rollback_action(self, action_id: str) -> Dict[str, Any]:
        """
        Rollback an executed action.

        Args:
            action_id: Action ID

        Returns:
            Rollback result
        """
        action = self.get_action(action_id)
        if not action:
            return {"success": False, "error": "Action not found"}

        if action.state not in [SandboxState.COMPLETED, SandboxState.FAILED]:
            return {"success": False, "error": "Action cannot be rolled back"}

        if not action.can_rollback:
            return {"success": False, "error": "Action does not support rollback"}

        try:
            # Get rollback executor
            rollback_executor = action.rollback_executor or self._rollback_executors.get(action.category)

            if rollback_executor:
                rollback_executor(action)

            action.state = SandboxState.ROLLED_BACK
            action.updated_at = datetime.now()

            app_logger.info(f"Action rolled back: {action_id}")
            self.action_rolled_back.emit(action)

            return {"success": True}

        except Exception as e:
            app_logger.error(f"Action rollback failed: {action_id} - {e}")
            return {"success": False, "error": str(e)}

    def _default_execute(self, action: SandboxAction) -> Any:
        """Default execution for actions without custom executor."""
        # Log the action
        app_logger.info(f"Default execution for: {action.category.value} - {action.title}")

        # For now, just return the action data
        return action.data

    def register_executor(
        self,
        category: ActionCategory,
        executor: Callable[[SandboxAction], Any],
        rollback_executor: Optional[Callable[[SandboxAction], None]] = None
    ):
        """
        Register an executor for an action category.

        Args:
            category: Action category
            executor: Function to execute the action
            rollback_executor: Function to rollback the action
        """
        self._action_executors[category] = executor
        if rollback_executor:
            self._rollback_executors[category] = rollback_executor

    def get_pending_actions(self) -> List[SandboxAction]:
        """Get all pending approval actions."""
        session = self.get_current_session()
        return session.get_pending_actions()

    def get_all_actions(self) -> List[SandboxAction]:
        """Get all actions in current session."""
        session = self.get_current_session()
        return session.actions

    def clear_session(self):
        """Clear the current session and start new."""
        if self._current_session:
            self._current_session.is_active = False
        self._create_new_session()


# Singleton instance
_sandbox: Optional[ActionSandbox] = None


def get_action_sandbox() -> ActionSandbox:
    """Get the singleton action sandbox instance."""
    global _sandbox
    if _sandbox is None:
        _sandbox = ActionSandbox()
    return _sandbox


def create_action(
    category: ActionCategory,
    title: str,
    **kwargs
) -> SandboxAction:
    """Create a sandbox action (convenience function)."""
    return get_action_sandbox().create_action(category, title, **kwargs)


def execute_with_approval(
    category: ActionCategory,
    title: str,
    executor: Callable,
    **kwargs
) -> SandboxAction:
    """Create, submit, and return an action for approval (convenience function)."""
    sandbox = get_action_sandbox()
    action = sandbox.create_action(category, title, **kwargs)
    action.executor = executor
    sandbox.submit_for_approval(action.id)
    return action
