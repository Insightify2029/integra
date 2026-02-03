# -*- coding: utf-8 -*-
"""
Security Module
===============
Authentication, authorization, and credential management.

Components:
  - AuthManager: User authentication with Argon2 password hashing
  - CredentialStore: Secure credential storage using OS keyring
  - RBAC: Role-Based Access Control
"""

from .auth_manager import (
    AuthManager,
    get_auth_manager,
    hash_password,
    verify_password,
)
from .credential_store import (
    CredentialStore,
    get_credential_store,
)
from .rbac import (
    Permission,
    Role,
    RBACManager,
    get_rbac_manager,
    require_permission,
)

__all__ = [
    # Auth
    "AuthManager",
    "get_auth_manager",
    "hash_password",
    "verify_password",
    # Credentials
    "CredentialStore",
    "get_credential_store",
    # RBAC
    "Permission",
    "Role",
    "RBACManager",
    "get_rbac_manager",
    "require_permission",
]
