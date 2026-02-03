# -*- coding: utf-8 -*-
"""
Database Audit Module
=====================
Audit trail system using PostgreSQL triggers.

Features:
  - Automatic logging of INSERT/UPDATE/DELETE
  - Old and new values stored as JSONB
  - User tracking
  - Queryable audit history
"""

from .audit_manager import (
    AuditManager,
    get_audit_manager,
    get_audit_history,
    get_record_history,
)

__all__ = [
    "AuditManager",
    "get_audit_manager",
    "get_audit_history",
    "get_record_history",
]
