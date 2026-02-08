"""
Role-Based Access Control (RBAC)
================================
Permission system for controlling access to features.

Features:
- Define roles with permissions
- Check user permissions
- Protect UI elements
- Audit access attempts

Usage:
    from core.security import Permission, has_permission, require_permission

    # Check permission
    if has_permission(user_id, Permission.EMPLOYEE_EDIT):
        # Allow edit
        pass

    # Decorator for functions
    @require_permission(Permission.EMPLOYEE_DELETE)
    def delete_employee(employee_id):
        pass

    # In UI
    edit_btn.setEnabled(has_permission(user_id, Permission.EMPLOYEE_EDIT))
"""

import threading
from enum import Enum, auto
from typing import List, Set, Dict, Optional, Callable
from functools import wraps

from core.logging import app_logger, audit_logger


class Permission(Enum):
    """Available permissions in the system."""

    # Employee permissions
    EMPLOYEE_VIEW = auto()
    EMPLOYEE_CREATE = auto()
    EMPLOYEE_EDIT = auto()
    EMPLOYEE_DELETE = auto()
    EMPLOYEE_EXPORT = auto()

    # Salary permissions
    SALARY_VIEW = auto()
    SALARY_EDIT = auto()
    SALARY_APPROVE = auto()

    # Reports permissions
    REPORT_VIEW = auto()
    REPORT_EXPORT = auto()
    REPORT_PRINT = auto()

    # System permissions
    SYSTEM_SETTINGS = auto()
    SYSTEM_BACKUP = auto()
    SYSTEM_AUDIT_VIEW = auto()

    # User management
    USER_VIEW = auto()
    USER_CREATE = auto()
    USER_EDIT = auto()
    USER_DELETE = auto()
    USER_PERMISSIONS = auto()

    # Module access
    MODULE_MOSTAHAQAT = auto()
    MODULE_COSTING = auto()
    MODULE_LOGISTICS = auto()
    MODULE_CUSTODY = auto()
    MODULE_INSURANCE = auto()


class Role(Enum):
    """Predefined roles with permission sets."""

    ADMIN = "مدير النظام"
    MANAGER = "مدير"
    HR = "موارد بشرية"
    ACCOUNTANT = "محاسب"
    VIEWER = "مشاهد"


# Role to permissions mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: set(Permission),  # All permissions

    Role.MANAGER: {
        Permission.EMPLOYEE_VIEW,
        Permission.EMPLOYEE_CREATE,
        Permission.EMPLOYEE_EDIT,
        Permission.EMPLOYEE_EXPORT,
        Permission.SALARY_VIEW,
        Permission.SALARY_EDIT,
        Permission.REPORT_VIEW,
        Permission.REPORT_EXPORT,
        Permission.REPORT_PRINT,
        Permission.MODULE_MOSTAHAQAT,
        Permission.MODULE_COSTING,
        Permission.MODULE_LOGISTICS,
        Permission.MODULE_CUSTODY,
        Permission.MODULE_INSURANCE,
    },

    Role.HR: {
        Permission.EMPLOYEE_VIEW,
        Permission.EMPLOYEE_CREATE,
        Permission.EMPLOYEE_EDIT,
        Permission.EMPLOYEE_EXPORT,
        Permission.SALARY_VIEW,
        Permission.REPORT_VIEW,
        Permission.REPORT_EXPORT,
        Permission.MODULE_MOSTAHAQAT,
    },

    Role.ACCOUNTANT: {
        Permission.EMPLOYEE_VIEW,
        Permission.SALARY_VIEW,
        Permission.SALARY_EDIT,
        Permission.REPORT_VIEW,
        Permission.REPORT_EXPORT,
        Permission.MODULE_MOSTAHAQAT,
        Permission.MODULE_COSTING,
    },

    Role.VIEWER: {
        Permission.EMPLOYEE_VIEW,
        Permission.SALARY_VIEW,
        Permission.REPORT_VIEW,
        Permission.MODULE_MOSTAHAQAT,
    },
}


class AccessControlManager:
    """Manages user permissions and access control."""

    def __init__(self):
        """Initialize access control manager."""
        self._current_user_id: Optional[int] = None
        self._current_user_name: Optional[str] = None
        self._current_role: Optional[Role] = None
        self._custom_permissions: Set[Permission] = set()
        self._denied_permissions: Set[Permission] = set()

        app_logger.debug("AccessControlManager initialized")

    def login(
        self,
        user_id: int,
        user_name: str,
        role: Role,
        custom_permissions: Optional[Set[Permission]] = None,
        denied_permissions: Optional[Set[Permission]] = None
    ) -> None:
        """
        Set current user session.

        Args:
            user_id: User ID
            user_name: User name
            role: User role
            custom_permissions: Additional permissions beyond role
            denied_permissions: Permissions to deny from role
        """
        self._current_user_id = user_id
        self._current_user_name = user_name
        self._current_role = role
        self._custom_permissions = custom_permissions or set()
        self._denied_permissions = denied_permissions or set()

        app_logger.info(f"User logged in: {user_name} (Role: {role.value})")
        audit_logger.log(
            action="LOGIN",
            table="users",
            record_id=user_id,
            details={"role": role.value}
        )

    def logout(self) -> None:
        """Clear current user session."""
        if self._current_user_id:
            audit_logger.log(
                action="LOGOUT",
                table="users",
                record_id=self._current_user_id
            )

        self._current_user_id = None
        self._current_user_name = None
        self._current_role = None
        self._custom_permissions = set()
        self._denied_permissions = set()

        app_logger.info("User logged out")

    @property
    def is_authenticated(self) -> bool:
        """Check if user is logged in."""
        return self._current_user_id is not None

    @property
    def current_user_id(self) -> Optional[int]:
        """Get current user ID."""
        return self._current_user_id

    @property
    def current_user_name(self) -> Optional[str]:
        """Get current user name."""
        return self._current_user_name

    @property
    def current_role(self) -> Optional[Role]:
        """Get current user role."""
        return self._current_role

    def get_user_permissions(self) -> Set[Permission]:
        """Get all permissions for current user."""
        if not self._current_role:
            return set()

        # Start with role permissions
        permissions = ROLE_PERMISSIONS.get(self._current_role, set()).copy()

        # Add custom permissions
        permissions |= self._custom_permissions

        # Remove denied permissions
        permissions -= self._denied_permissions

        return permissions

    def has_permission(self, permission: Permission) -> bool:
        """
        Check if current user has permission.

        Args:
            permission: Permission to check

        Returns:
            True if user has permission
        """
        if not self.is_authenticated:
            return False

        # Admin has all permissions
        if self._current_role == Role.ADMIN:
            return True

        has_perm = permission in self.get_user_permissions()

        # Log access attempt for sensitive permissions
        if permission in {
            Permission.EMPLOYEE_DELETE,
            Permission.SALARY_APPROVE,
            Permission.SYSTEM_SETTINGS,
            Permission.USER_PERMISSIONS
        }:
            audit_logger.log(
                action="ACCESS_CHECK",
                table="permissions",
                record_id=self._current_user_id,
                details={
                    "permission": permission.name,
                    "granted": has_perm
                }
            )

        return has_perm

    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if user has any of the given permissions."""
        return any(self.has_permission(p) for p in permissions)

    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """Check if user has all of the given permissions."""
        return all(self.has_permission(p) for p in permissions)

    def has_module_access(self, module_name: str) -> bool:
        """
        Check if user has access to a module.

        Args:
            module_name: Module name (mostahaqat, costing, etc.)

        Returns:
            True if user has access
        """
        module_permissions = {
            "mostahaqat": Permission.MODULE_MOSTAHAQAT,
            "costing": Permission.MODULE_COSTING,
            "logistics": Permission.MODULE_LOGISTICS,
            "custody": Permission.MODULE_CUSTODY,
            "insurance": Permission.MODULE_INSURANCE,
        }

        permission = module_permissions.get(module_name.lower())
        if permission:
            return self.has_permission(permission)

        return False


# Thread-safe singleton
_acm: Optional[AccessControlManager] = None
_acm_lock = threading.Lock()


def get_access_control_manager() -> AccessControlManager:
    """Get the AccessControlManager singleton (thread-safe)."""
    global _acm
    if _acm is None:
        with _acm_lock:
            if _acm is None:
                _acm = AccessControlManager()
    return _acm


# Convenience functions

def login_user(
    user_id: int,
    user_name: str,
    role: Role,
    **kwargs
) -> None:
    """Login user to the system."""
    get_access_control_manager().login(user_id, user_name, role, **kwargs)


def logout_user() -> None:
    """Logout current user."""
    get_access_control_manager().logout()


def is_authenticated() -> bool:
    """Check if user is authenticated."""
    return get_access_control_manager().is_authenticated


def get_current_user() -> Optional[Dict]:
    """Get current user info."""
    acm = get_access_control_manager()
    if not acm.is_authenticated:
        return None

    return {
        "id": acm.current_user_id,
        "name": acm.current_user_name,
        "role": acm.current_role.value if acm.current_role else None
    }


def has_permission(permission: Permission) -> bool:
    """Check if current user has permission."""
    return get_access_control_manager().has_permission(permission)


def has_module_access(module_name: str) -> bool:
    """Check if current user has module access."""
    return get_access_control_manager().has_module_access(module_name)


def require_permission(permission: Permission):
    """
    Decorator to require permission for a function.

    Usage:
        @require_permission(Permission.EMPLOYEE_DELETE)
        def delete_employee(employee_id):
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            acm = get_access_control_manager()
            if not acm.has_permission(permission):
                app_logger.warning(
                    f"Permission denied: {permission.name} "
                    f"for user {acm.current_user_id}"
                )
                raise PermissionError(
                    f"ليس لديك صلاحية: {permission.name}"
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(*permissions: Permission):
    """Decorator to require any of the given permissions."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not get_access_control_manager().has_any_permission(list(permissions)):
                raise PermissionError("ليس لديك الصلاحيات المطلوبة")
            return func(*args, **kwargs)
        return wrapper
    return decorator
