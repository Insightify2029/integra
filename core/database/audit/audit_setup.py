"""
Audit System Setup
==================
One-time setup and initialization for the audit trail system.

Call `initialize_audit()` during application startup to ensure
the audit schema, tables, and triggers are ready.

Usage:
    from core.database.audit.audit_setup import initialize_audit

    # During app startup (after DB connection is established)
    initialize_audit()
"""

from typing import List, Optional

from core.logging import app_logger
from .audit_manager import (
    AuditManager,
    get_audit_manager,
    DEFAULT_AUDITED_TABLES,
)


def initialize_audit(
    tables: Optional[List[str]] = None,
    skip_if_exists: bool = True,
) -> bool:
    """
    Initialize the audit system during application startup.

    Steps:
    1. Check if audit schema exists
    2. Create schema + table if needed
    3. Create/update trigger function
    4. Enable triggers on specified tables

    Args:
        tables: Tables to audit (default: DEFAULT_AUDITED_TABLES)
        skip_if_exists: If True, skip schema creation if already set up

    Returns:
        True if audit system is ready
    """
    if tables is None:
        tables = DEFAULT_AUDITED_TABLES

    manager = get_audit_manager()

    try:
        # Check if already set up
        if skip_if_exists and manager.is_audit_setup():
            app_logger.info("Audit system already initialized")
            _ensure_triggers(manager, tables)
            return True

        # Full setup
        app_logger.info("Setting up audit system...")

        if not manager.setup_audit_tables():
            app_logger.error("Failed to create audit schema/tables")
            return False

        # Enable triggers
        _ensure_triggers(manager, tables)

        app_logger.info("Audit system initialization complete")
        return True

    except Exception as e:
        app_logger.error(f"Audit initialization failed: {e}")
        return False


def _ensure_triggers(manager: AuditManager, tables: List[str]) -> None:
    """Enable audit triggers on all specified tables."""
    current = set(manager.get_audited_tables())

    for table in tables:
        if table not in current:
            if manager.enable_audit(table):
                app_logger.info(f"Audit trigger enabled for: {table}")
            else:
                app_logger.warning(f"Could not enable audit for: {table}")
