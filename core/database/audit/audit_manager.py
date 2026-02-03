# -*- coding: utf-8 -*-
"""
Audit Manager
=============
Python interface for the PostgreSQL audit trail system.

Features:
  - Initialize audit schema
  - Enable/disable audit on tables
  - Query audit history
  - Set application user for tracking
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

from core.database import get_connection, select_all, select_one, get_scalar


class AuditManager:
    """
    Manager for audit trail operations.

    Usage:
        manager = AuditManager()
        manager.initialize()  # First time setup
        manager.enable_table("employees")

        # Later, query history
        history = manager.get_table_history("employees", limit=50)
    """

    SCHEMA_FILE = Path(__file__).parent / "audit_schema.sql"
    TRIGGERS_FILE = Path(__file__).parent / "audit_triggers.sql"

    def __init__(self):
        self._initialized = False

    def initialize(self) -> Tuple[bool, str]:
        """
        Initialize the audit schema in the database.

        Creates audit schema, tables, functions, and indexes.

        Returns:
            (success, message)
        """
        try:
            conn = get_connection()
            if not conn:
                return False, "Database not connected"

            # Read and execute schema SQL
            with open(self.SCHEMA_FILE, "r", encoding="utf-8") as f:
                schema_sql = f.read()

            with conn.cursor() as cur:
                cur.execute(schema_sql)
                conn.commit()

            self._initialized = True
            return True, "Audit schema initialized successfully"

        except FileNotFoundError:
            return False, f"Schema file not found: {self.SCHEMA_FILE}"
        except Exception as e:
            return False, f"Error initializing audit: {e}"

    def setup_triggers(self) -> Tuple[bool, str]:
        """
        Set up audit triggers on default tables.

        Returns:
            (success, message)
        """
        try:
            conn = get_connection()
            if not conn:
                return False, "Database not connected"

            with open(self.TRIGGERS_FILE, "r", encoding="utf-8") as f:
                triggers_sql = f.read()

            with conn.cursor() as cur:
                cur.execute(triggers_sql)
                conn.commit()

            return True, "Audit triggers set up successfully"

        except FileNotFoundError:
            return False, f"Triggers file not found: {self.TRIGGERS_FILE}"
        except Exception as e:
            return False, f"Error setting up triggers: {e}"

    def enable_table(self, table_name: str, schema_name: str = "public") -> Tuple[bool, str]:
        """
        Enable audit on a specific table.

        Args:
            table_name: Name of the table
            schema_name: Schema name (default: public)

        Returns:
            (success, message)
        """
        try:
            conn = get_connection()
            if not conn:
                return False, "Database not connected"

            with conn.cursor() as cur:
                cur.execute(
                    "SELECT audit.enable_audit(%s, %s)",
                    (table_name, schema_name)
                )
                conn.commit()

            return True, f"Audit enabled for {schema_name}.{table_name}"

        except Exception as e:
            return False, f"Error enabling audit: {e}"

    def disable_table(self, table_name: str, schema_name: str = "public") -> Tuple[bool, str]:
        """
        Disable audit on a specific table.

        Args:
            table_name: Name of the table
            schema_name: Schema name (default: public)

        Returns:
            (success, message)
        """
        try:
            conn = get_connection()
            if not conn:
                return False, "Database not connected"

            with conn.cursor() as cur:
                cur.execute(
                    "SELECT audit.disable_audit(%s, %s)",
                    (table_name, schema_name)
                )
                conn.commit()

            return True, f"Audit disabled for {schema_name}.{table_name}"

        except Exception as e:
            return False, f"Error disabling audit: {e}"

    def set_app_user(self, username: str) -> bool:
        """
        Set the application user for the current session.

        This user will be recorded in audit logs.

        Args:
            username: The user identifier

        Returns:
            True if successful
        """
        try:
            conn = get_connection()
            if not conn:
                return False

            with conn.cursor() as cur:
                cur.execute(
                    "SET LOCAL app.current_user = %s",
                    (username,)
                )

            return True
        except Exception:
            return False

    def get_table_history(
        self,
        table_name: str,
        limit: int = 100,
        offset: int = 0,
        action: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get audit history for a table.

        Args:
            table_name: Table to get history for
            limit: Maximum records to return
            offset: Records to skip
            action: Filter by action (INSERT/UPDATE/DELETE)
            since: Only records after this time

        Returns:
            List of audit records
        """
        query = """
            SELECT
                id,
                table_name,
                record_id,
                action,
                old_data,
                new_data,
                changed_fields,
                app_user,
                changed_at
            FROM audit.logged_actions
            WHERE table_name = %s
        """
        params = [table_name]

        if action:
            query += " AND action = %s"
            params.append(action.upper())

        if since:
            query += " AND changed_at >= %s"
            params.append(since)

        query += " ORDER BY changed_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        columns, rows = select_all(query, tuple(params))
        if not rows:
            return []

        return [dict(zip(columns, row)) for row in rows]

    def get_record_history(
        self,
        table_name: str,
        record_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get complete history for a specific record.

        Args:
            table_name: Table name
            record_id: Record ID

        Returns:
            List of all changes to this record, oldest first
        """
        query = """
            SELECT
                id,
                action,
                old_data,
                new_data,
                changed_fields,
                app_user,
                changed_at
            FROM audit.logged_actions
            WHERE table_name = %s AND record_id = %s
            ORDER BY changed_at ASC
        """

        columns, rows = select_all(query, (table_name, record_id))
        if not rows:
            return []

        return [dict(zip(columns, row)) for row in rows]

    def get_user_activity(
        self,
        username: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all changes made by a specific user.

        Args:
            username: The app user to query
            limit: Maximum records

        Returns:
            List of audit records
        """
        query = """
            SELECT
                id,
                table_name,
                record_id,
                action,
                changed_fields,
                changed_at
            FROM audit.logged_actions
            WHERE app_user = %s
            ORDER BY changed_at DESC
            LIMIT %s
        """

        columns, rows = select_all(query, (username, limit))
        if not rows:
            return []

        return [dict(zip(columns, row)) for row in rows]

    def get_recent_changes(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get most recent changes across all tables.

        Args:
            limit: Maximum records

        Returns:
            List of recent audit records
        """
        query = """
            SELECT
                id,
                table_name,
                record_id,
                action,
                changed_fields,
                app_user,
                changed_at
            FROM audit.logged_actions
            ORDER BY changed_at DESC
            LIMIT %s
        """

        columns, rows = select_all(query, (limit,))
        if not rows:
            return []

        return [dict(zip(columns, row)) for row in rows]

    def get_audit_stats(self) -> Dict[str, Any]:
        """
        Get audit statistics.

        Returns:
            Dictionary with stats (total records, by action, by table)
        """
        stats = {}

        # Total count
        stats["total"] = get_scalar(
            "SELECT COUNT(*) FROM audit.logged_actions"
        ) or 0

        # By action
        query = """
            SELECT action, COUNT(*) as count
            FROM audit.logged_actions
            GROUP BY action
        """
        _, rows = select_all(query)
        stats["by_action"] = {row[0]: row[1] for row in (rows or [])}

        # By table
        query = """
            SELECT table_name, COUNT(*) as count
            FROM audit.logged_actions
            GROUP BY table_name
            ORDER BY count DESC
            LIMIT 10
        """
        _, rows = select_all(query)
        stats["by_table"] = {row[0]: row[1] for row in (rows or [])}

        return stats

    def cleanup(self, retention_days: int = 365) -> int:
        """
        Clean up old audit records.

        Args:
            retention_days: Keep records newer than this

        Returns:
            Number of deleted records
        """
        result = get_scalar(
            "SELECT audit.cleanup_old_records(%s)",
            (retention_days,)
        )
        return result or 0

    def is_audit_enabled(self, table_name: str, schema_name: str = "public") -> bool:
        """
        Check if audit is enabled for a table.

        Args:
            table_name: Table name
            schema_name: Schema name

        Returns:
            True if audit trigger exists
        """
        query = """
            SELECT EXISTS(
                SELECT 1 FROM information_schema.triggers
                WHERE trigger_name = %s
                AND event_object_table = %s
                AND event_object_schema = %s
            )
        """
        trigger_name = f"audit_trigger_{table_name}"
        return get_scalar(query, (trigger_name, table_name, schema_name)) or False


# Singleton instance
_audit_manager: Optional[AuditManager] = None


def get_audit_manager() -> AuditManager:
    """Get the global AuditManager instance."""
    global _audit_manager
    if _audit_manager is None:
        _audit_manager = AuditManager()
    return _audit_manager


# Convenience functions

def get_audit_history(
    table_name: str,
    limit: int = 100,
    **kwargs
) -> List[Dict[str, Any]]:
    """Get audit history for a table."""
    return get_audit_manager().get_table_history(table_name, limit, **kwargs)


def get_record_history(
    table_name: str,
    record_id: int
) -> List[Dict[str, Any]]:
    """Get complete history for a specific record."""
    return get_audit_manager().get_record_history(table_name, record_id)
