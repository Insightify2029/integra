"""
Audit Trail Module
==================
Track all changes to database tables.

Usage:
    from core.database.audit import AuditManager, get_audit_history, setup_audit_system

    # Setup (run once)
    setup_audit_system(["employees", "payroll"])

    # Get history
    history = get_audit_history("employees", record_id=123)

    # Initialize on app startup
    from core.database.audit import initialize_audit
    initialize_audit()
"""

from .audit_manager import (
    AuditManager,
    get_audit_manager,
    get_audit_history,
    setup_audit_system,
    DEFAULT_AUDITED_TABLES,
)
from .audit_setup import initialize_audit

__all__ = [
    'AuditManager',
    'get_audit_manager',
    'get_audit_history',
    'setup_audit_system',
    'initialize_audit',
    'DEFAULT_AUDITED_TABLES',
]
