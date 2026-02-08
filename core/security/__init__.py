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
    get_access_control_manager,
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

from .encryption import (
    # Manager
    Encryptor,
    get_encryptor,
    is_encryption_available,
    # Basic functions
    encrypt,
    decrypt,
    encrypt_sensitive_fields,
    decrypt_sensitive_fields,
    # File encryption
    encrypt_file,
    decrypt_file,
    # Password hashing
    hash_password,
    verify_password,
    # Sensitive data helpers
    encrypt_iban,
    decrypt_iban,
    mask_iban,
    encrypt_db_password,
    decrypt_db_password,
)

from .auth_manager import (
    AuthManager,
    get_auth_manager,
    is_argon2_available,
)

from .credential_store import (
    CredentialStore,
    get_credential_store,
)

__all__ = [
    # RBAC - Enums
    'Permission',
    'Role',
    # RBAC - Manager
    'AccessControlManager',
    'get_access_control_manager',
    # RBAC - Functions
    'login_user',
    'logout_user',
    'is_authenticated',
    'get_current_user',
    'has_permission',
    'has_module_access',
    # RBAC - Decorators
    'require_permission',
    'require_any_permission',
    # RBAC - Constants
    'ROLE_PERMISSIONS',
    # Encryption - Manager
    'Encryptor',
    'get_encryptor',
    'is_encryption_available',
    # Encryption - Basic
    'encrypt',
    'decrypt',
    'encrypt_sensitive_fields',
    'decrypt_sensitive_fields',
    # Encryption - File
    'encrypt_file',
    'decrypt_file',
    # Encryption - Password
    'hash_password',
    'verify_password',
    # Encryption - Helpers
    'encrypt_iban',
    'decrypt_iban',
    'mask_iban',
    'encrypt_db_password',
    'decrypt_db_password',
    # Authentication
    'AuthManager',
    'get_auth_manager',
    'is_argon2_available',
    # Credential Store
    'CredentialStore',
    'get_credential_store',
]
