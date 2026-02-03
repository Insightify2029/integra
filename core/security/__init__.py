"""
Security Module
===============
Role-based access control and security features.

Usage:
    from core.security import (
        Permission,
        Role,
        has_permission,
        require_permission,
        login_user,
        logout_user
    )

    # Login
    login_user(user_id=1, user_name="محمد", role=Role.HR)

    # Check permission
    if has_permission(Permission.EMPLOYEE_EDIT):
        # Allow edit
        pass

    # Decorator
    @require_permission(Permission.EMPLOYEE_DELETE)
    def delete_employee(employee_id):
        pass

    # UI protection
    edit_btn.setEnabled(has_permission(Permission.EMPLOYEE_EDIT))
"""

from .rbac import (
    # Enums
    Permission,
    Role,
    # Manager
    AccessControlManager,
    # Functions
    login_user,
    logout_user,
    is_authenticated,
    get_current_user,
    has_permission,
    has_module_access,
    # Decorators
    require_permission,
    require_any_permission,
    # Constants
    ROLE_PERMISSIONS
)

__all__ = [
    # Enums
    'Permission',
    'Role',
    # Manager
    'AccessControlManager',
    # Functions
    'login_user',
    'logout_user',
    'is_authenticated',
    'get_current_user',
    'has_permission',
    'has_module_access',
    # Decorators
    'require_permission',
    'require_any_permission',
    # Constants
    'ROLE_PERMISSIONS'
]
