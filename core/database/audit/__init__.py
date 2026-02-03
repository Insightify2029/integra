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
"""

from .audit_manager import (
    AuditManager,
    get_audit_history,
    setup_audit_system
)

__all__ = [
    'AuditManager',
    'get_audit_history',
    'setup_audit_system'
]
