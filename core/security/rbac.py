# -*- coding: utf-8 -*-
"""
Role-Based Access Control (RBAC)
================================
Permission and role management system.

Features:
  - Permission definitions
  - Role definitions with permissions
  - Permission checking
  - Decorator for protected functions
"""

from typing import Dict, List, Set, Optional, Callable
from enum import Enum, auto
from dataclasses import dataclass, field
from functools import wraps


class Permission(Enum):
    """
    Application permissions.

    Naming: MODULE_ACTION
    """
    # System
    SYSTEM_ADMIN = auto()
    SYSTEM_SETTINGS = auto()

    # Employees
    EMPLOYEES_VIEW = auto()
    EMPLOYEES_CREATE = auto()
    EMPLOYEES_EDIT = auto()
    EMPLOYEES_DELETE = auto()
    EMPLOYEES_EXPORT = auto()

    # Payroll (sensitive)
    PAYROLL_VIEW = auto()
    PAYROLL_CREATE = auto()
    PAYROLL_EDIT = auto()
    PAYROLL_APPROVE = auto()

    # Reports
    REPORTS_VIEW = auto()
    REPORTS_CREATE = auto()
    REPORTS_EXPORT = auto()

    # Audit
    AUDIT_VIEW = auto()

    # Email Module
    EMAIL_VIEW = auto()
    EMAIL_SEND = auto()
    EMAIL_DELETE = auto()

    # Sync
    SYNC_MANUAL = auto()
    SYNC_SETTINGS = auto()


@dataclass
class Role:
    """
    A role with a set of permissions.

    Attributes:
        id: Role identifier
        name_ar: Arabic name
        name_en: English name
        permissions: Set of granted permissions
        description: Role description
    """
    id: str
    name_ar: str
    name_en: str
    permissions: Set[Permission] = field(default_factory=set)
    description: str = ""

    def has_permission(self, permission: Permission) -> bool:
        """Check if role has a permission."""
        # SYSTEM_ADMIN has all permissions
        if Permission.SYSTEM_ADMIN in self.permissions:
            return True
        return permission in self.permissions

    def grant(self, permission: Permission):
        """Grant a permission to this role."""
        self.permissions.add(permission)

    def revoke(self, permission: Permission):
        """Revoke a permission from this role."""
        self.permissions.discard(permission)


# Predefined roles
ROLES = {
    "admin": Role(
        id="admin",
        name_ar="مدير النظام",
        name_en="Administrator",
        permissions={Permission.SYSTEM_ADMIN},
        description="Full system access"
    ),
    "hr_manager": Role(
        id="hr_manager",
        name_ar="مدير الموارد البشرية",
        name_en="HR Manager",
        permissions={
            Permission.EMPLOYEES_VIEW,
            Permission.EMPLOYEES_CREATE,
            Permission.EMPLOYEES_EDIT,
            Permission.EMPLOYEES_DELETE,
            Permission.EMPLOYEES_EXPORT,
            Permission.PAYROLL_VIEW,
            Permission.PAYROLL_CREATE,
            Permission.PAYROLL_EDIT,
            Permission.REPORTS_VIEW,
            Permission.REPORTS_CREATE,
            Permission.REPORTS_EXPORT,
            Permission.AUDIT_VIEW,
        },
        description="HR department manager"
    ),
    "hr_staff": Role(
        id="hr_staff",
        name_ar="موظف موارد بشرية",
        name_en="HR Staff",
        permissions={
            Permission.EMPLOYEES_VIEW,
            Permission.EMPLOYEES_CREATE,
            Permission.EMPLOYEES_EDIT,
            Permission.REPORTS_VIEW,
        },
        description="HR department staff"
    ),
    "accountant": Role(
        id="accountant",
        name_ar="محاسب",
        name_en="Accountant",
        permissions={
            Permission.EMPLOYEES_VIEW,
            Permission.PAYROLL_VIEW,
            Permission.PAYROLL_CREATE,
            Permission.REPORTS_VIEW,
            Permission.REPORTS_EXPORT,
        },
        description="Finance/Accounting staff"
    ),
    "viewer": Role(
        id="viewer",
        name_ar="مستعرض",
        name_en="Viewer",
        permissions={
            Permission.EMPLOYEES_VIEW,
            Permission.REPORTS_VIEW,
        },
        description="Read-only access"
    ),
}


class RBACManager:
    """
    Role-Based Access Control manager.

    Usage:
        rbac = RBACManager()

        # Check permission
        if rbac.has_permission(user_roles, Permission.EMPLOYEES_EDIT):
            # Allow edit
            pass

        # Get all permissions for roles
        perms = rbac.get_permissions(["hr_manager", "accountant"])
    """

    def __init__(self):
        """Initialize RBAC manager."""
        self._roles: Dict[str, Role] = ROLES.copy()
        self._current_roles: List[str] = []

    def add_role(self, role: Role):
        """Add or update a role."""
        self._roles[role.id] = role

    def get_role(self, role_id: str) -> Optional[Role]:
        """Get a role by ID."""
        return self._roles.get(role_id)

    def get_all_roles(self) -> List[Role]:
        """Get all defined roles."""
        return list(self._roles.values())

    def set_current_roles(self, role_ids: List[str]):
        """Set current user's roles (for permission checks)."""
        self._current_roles = role_ids

    def has_permission(
        self,
        permission: Permission,
        role_ids: List[str] = None
    ) -> bool:
        """
        Check if given roles have a permission.

        Args:
            permission: The permission to check
            role_ids: List of role IDs (if None, uses current roles)

        Returns:
            True if any role has the permission
        """
        if role_ids is None:
            role_ids = self._current_roles

        for role_id in role_ids:
            role = self._roles.get(role_id)
            if role and role.has_permission(permission):
                return True

        return False

    def get_permissions(self, role_ids: List[str]) -> Set[Permission]:
        """
        Get all permissions for a list of roles.

        Args:
            role_ids: List of role IDs

        Returns:
            Combined set of permissions
        """
        permissions = set()

        for role_id in role_ids:
            role = self._roles.get(role_id)
            if role:
                # Admin has all permissions
                if Permission.SYSTEM_ADMIN in role.permissions:
                    return set(Permission)
                permissions.update(role.permissions)

        return permissions

    def get_missing_permissions(
        self,
        required: List[Permission],
        role_ids: List[str] = None
    ) -> List[Permission]:
        """
        Get list of permissions that user is missing.

        Args:
            required: Required permissions
            role_ids: User's roles (if None, uses current roles)

        Returns:
            List of missing permissions
        """
        if role_ids is None:
            role_ids = self._current_roles

        user_perms = self.get_permissions(role_ids)

        # Admin has all
        if Permission.SYSTEM_ADMIN in user_perms:
            return []

        return [p for p in required if p not in user_perms]


# Singleton instance
_rbac_manager: Optional[RBACManager] = None


def get_rbac_manager() -> RBACManager:
    """Get the global RBACManager instance."""
    global _rbac_manager
    if _rbac_manager is None:
        _rbac_manager = RBACManager()
    return _rbac_manager


def require_permission(*permissions: Permission):
    """
    Decorator to require permissions for a function.

    Usage:
        @require_permission(Permission.EMPLOYEES_EDIT)
        def update_employee(employee_id, data):
            # Only runs if user has permission
            pass

    Raises:
        PermissionError: If user lacks required permission
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            rbac = get_rbac_manager()

            missing = rbac.get_missing_permissions(list(permissions))

            if missing:
                perm_names = ", ".join(p.name for p in missing)
                raise PermissionError(
                    f"صلاحيات غير كافية. مطلوب: {perm_names}"
                )

            return func(*args, **kwargs)
        return wrapper
    return decorator


def check_permission(permission: Permission) -> bool:
    """
    Quick check if current user has a permission.

    Args:
        permission: Permission to check

    Returns:
        True if permission granted
    """
    return get_rbac_manager().has_permission(permission)
