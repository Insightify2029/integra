"""
Audit Trail System
==================
Track all changes to sensitive database tables.

Features:
- Log all INSERT, UPDATE, DELETE operations
- Store old and new values (JSONB)
- Track user who made the change
- Query audit history with filters
- Statistics and maintenance

Usage:
    from core.database.audit import AuditManager, get_audit_history

    # Get audit history for a record
    history = get_audit_history("employees", record_id=123)

    # Get recent changes
    recent = get_audit_history("employees", limit=50)

    # Setup audit triggers (run once)
    manager = AuditManager()
    manager.setup_audit_tables()
    manager.enable_audit("employees")
"""

import threading
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from psycopg2 import sql as psycopg2_sql

from core.database import select_all, get_scalar, get_count, execute_query
from core.database.connection import get_connection, return_connection
from core.logging import app_logger


# Default tables to audit
DEFAULT_AUDITED_TABLES = [
    "employees",
    "companies",
    "departments",
    "job_titles",
    "banks",
    "employee_statuses",
    "nationalities",
]


# SQL for creating audit schema and table
AUDIT_SCHEMA_SQL = """
-- Create audit schema if not exists
CREATE SCHEMA IF NOT EXISTS audit;

-- Create audit log table
CREATE TABLE IF NOT EXISTS audit.logged_actions (
    id BIGSERIAL PRIMARY KEY,
    schema_name TEXT NOT NULL,
    table_name TEXT NOT NULL,
    record_id INTEGER,
    action_type TEXT NOT NULL CHECK (action_type IN ('INSERT', 'UPDATE', 'DELETE')),
    old_data JSONB,
    new_data JSONB,
    changed_fields TEXT[],
    action_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    db_user TEXT DEFAULT current_user,
    app_user TEXT,
    app_user_id INTEGER,
    client_ip INET,
    session_id TEXT,
    notes TEXT
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_audit_table_name ON audit.logged_actions(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_record_id ON audit.logged_actions(record_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit.logged_actions(action_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_action_type ON audit.logged_actions(action_type);
CREATE INDEX IF NOT EXISTS idx_audit_app_user_id ON audit.logged_actions(app_user_id);
CREATE INDEX IF NOT EXISTS idx_audit_table_record ON audit.logged_actions(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_audit_table_timestamp ON audit.logged_actions(table_name, action_timestamp DESC);
"""

# SQL for creating audit trigger function
AUDIT_TRIGGER_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION audit.log_changes()
RETURNS TRIGGER AS $$
DECLARE
    v_old_data JSONB;
    v_new_data JSONB;
    v_changed TEXT[];
    v_record_id INTEGER;
BEGIN
    -- Get record ID and data
    IF TG_OP = 'DELETE' THEN
        v_record_id := OLD.id;
        v_old_data := to_jsonb(OLD);
        v_new_data := NULL;
    ELSIF TG_OP = 'INSERT' THEN
        v_record_id := NEW.id;
        v_old_data := NULL;
        v_new_data := to_jsonb(NEW);
    ELSIF TG_OP = 'UPDATE' THEN
        v_record_id := NEW.id;
        v_old_data := to_jsonb(OLD);
        v_new_data := to_jsonb(NEW);

        -- Get list of changed fields
        SELECT array_agg(key) INTO v_changed
        FROM (
            SELECT key
            FROM jsonb_each(to_jsonb(OLD)) AS o(key, value)
            FULL OUTER JOIN jsonb_each(to_jsonb(NEW)) AS n(key, value) USING (key)
            WHERE o.value IS DISTINCT FROM n.value
        ) AS changes;
    END IF;

    -- Insert audit record
    INSERT INTO audit.logged_actions (
        schema_name,
        table_name,
        record_id,
        action_type,
        old_data,
        new_data,
        changed_fields,
        db_user,
        app_user,
        app_user_id
    ) VALUES (
        TG_TABLE_SCHEMA,
        TG_TABLE_NAME,
        v_record_id,
        TG_OP,
        v_old_data,
        v_new_data,
        v_changed,
        current_user,
        current_setting('app.current_user', true),
        NULLIF(current_setting('app.current_user_id', true), '')::INTEGER
    );

    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
"""


# Thread-safe singleton
_lock = threading.Lock()
_instance: Optional["AuditManager"] = None


def get_audit_manager() -> "AuditManager":
    """Get thread-safe singleton AuditManager instance."""
    global _instance
    with _lock:
        if _instance is None:
            _instance = AuditManager()
    return _instance


class AuditManager:
    """Manage audit trail setup and queries."""

    def __init__(self):
        """Initialize audit manager."""
        app_logger.debug("AuditManager initialized")

    def setup_audit_tables(self) -> bool:
        """
        Create audit schema and tables.
        Run this once during initial setup.

        Returns:
            True if successful
        """
        conn = None
        cursor = None
        try:
            conn = get_connection()
            if conn is None:
                app_logger.error("Cannot setup audit tables: no database connection")
                return False

            cursor = conn.cursor()

            # Create schema and table
            cursor.execute(AUDIT_SCHEMA_SQL)

            # Create trigger function
            cursor.execute(AUDIT_TRIGGER_FUNCTION_SQL)

            conn.commit()
            app_logger.info("Audit tables and trigger function created successfully")
            return True

        except Exception as e:
            app_logger.error(f"Failed to setup audit tables: {e}")
            if conn:
                try:
                    conn.rollback()
                except Exception as rb_err:
                    app_logger.warning(f"Rollback failed: {rb_err}")
            return False
        finally:
            if cursor:
                cursor.close()
            return_connection(conn)

    def enable_audit(self, table_name: str, schema: str = "public") -> bool:
        """
        Enable audit logging for a table by creating a trigger.

        Args:
            table_name: Table to audit
            schema: Schema name (default: public)

        Returns:
            True if successful
        """
        conn = None
        cursor = None
        try:
            conn = get_connection()
            if conn is None:
                app_logger.error(f"Cannot enable audit for {table_name}: no connection")
                return False

            cursor = conn.cursor()

            trigger_name = f"audit_trigger_{table_name}"
            trigger_sql = psycopg2_sql.SQL(
                "DROP TRIGGER IF EXISTS {trigger} ON {schema}.{table};"
                " CREATE TRIGGER {trigger}"
                " AFTER INSERT OR UPDATE OR DELETE ON {schema}.{table}"
                " FOR EACH ROW EXECUTE FUNCTION audit.log_changes();"
            ).format(
                trigger=psycopg2_sql.Identifier(trigger_name),
                schema=psycopg2_sql.Identifier(schema),
                table=psycopg2_sql.Identifier(table_name),
            )
            cursor.execute(trigger_sql)

            conn.commit()
            app_logger.info(f"Audit enabled for {schema}.{table_name}")
            return True

        except Exception as e:
            app_logger.error(f"Failed to enable audit for {table_name}: {e}")
            if conn:
                try:
                    conn.rollback()
                except Exception as rb_err:
                    app_logger.warning(f"Rollback failed: {rb_err}")
            return False
        finally:
            if cursor:
                cursor.close()
            return_connection(conn)

    def disable_audit(self, table_name: str, schema: str = "public") -> bool:
        """
        Disable audit logging for a table.

        Args:
            table_name: Table name
            schema: Schema name

        Returns:
            True if successful
        """
        conn = None
        cursor = None
        try:
            conn = get_connection()
            if conn is None:
                return False

            cursor = conn.cursor()

            trigger_name = f"audit_trigger_{table_name}"
            drop_sql = psycopg2_sql.SQL(
                "DROP TRIGGER IF EXISTS {} ON {}.{};"
            ).format(
                psycopg2_sql.Identifier(trigger_name),
                psycopg2_sql.Identifier(schema),
                psycopg2_sql.Identifier(table_name),
            )
            cursor.execute(drop_sql)

            conn.commit()
            app_logger.info(f"Audit disabled for {schema}.{table_name}")
            return True

        except Exception as e:
            app_logger.error(f"Failed to disable audit for {table_name}: {e}")
            if conn:
                try:
                    conn.rollback()
                except Exception as rb_err:
                    app_logger.warning(f"Rollback failed: {rb_err}")
            return False
        finally:
            if cursor:
                cursor.close()
            return_connection(conn)

    def set_app_user(self, user_name: str, user_id: int) -> None:
        """
        Set current application user for audit logging.
        Call this when user logs in.

        Uses session-level SET (not SET LOCAL) so the values persist
        across transactions on the same connection.

        Args:
            user_name: User name
            user_id: User ID
        """
        conn = None
        cursor = None
        try:
            conn = get_connection()
            if conn is None:
                return

            cursor = conn.cursor()
            # Use session-level SET so values persist across transactions
            cursor.execute("SET app.current_user = %s", (user_name,))
            cursor.execute("SET app.current_user_id = %s", (str(user_id),))
            conn.commit()

        except Exception as e:
            app_logger.error(f"Failed to set app user: {e}")
        finally:
            if cursor:
                cursor.close()
            return_connection(conn)

    def get_audit_history(
        self,
        table_name: Optional[str] = None,
        record_id: Optional[int] = None,
        action_type: Optional[str] = None,
        user_id: Optional[int] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get audit history with flexible filters.

        Args:
            table_name: Filter by table name (None = all tables)
            record_id: Filter by record ID
            action_type: Filter by action (INSERT, UPDATE, DELETE)
            user_id: Filter by user
            from_date: Start date
            to_date: End date
            limit: Max records
            offset: Offset for pagination

        Returns:
            List of audit records as dicts
        """
        try:
            conditions: List[str] = []
            params: List[Any] = []

            if table_name:
                conditions.append("table_name = %s")
                params.append(table_name)

            if record_id is not None:
                conditions.append("record_id = %s")
                params.append(record_id)

            if action_type:
                conditions.append("action_type = %s")
                params.append(action_type.upper())

            if user_id is not None:
                conditions.append("app_user_id = %s")
                params.append(user_id)

            if from_date:
                conditions.append("action_timestamp >= %s")
                params.append(from_date)

            if to_date:
                conditions.append("action_timestamp <= %s")
                params.append(to_date)

            where_clause = " AND ".join(conditions) if conditions else "TRUE"
            params.extend([limit, offset])

            # Build query using psycopg2.sql to avoid f-string SQL patterns
            base = psycopg2_sql.SQL(
                "SELECT id, schema_name, table_name, record_id,"
                " action_type, old_data, new_data, changed_fields,"
                " action_timestamp, db_user, app_user, app_user_id,"
                " notes"
                " FROM audit.logged_actions"
                " WHERE {where}"
                " ORDER BY action_timestamp DESC"
                " LIMIT %s OFFSET %s"
            ).format(
                where=psycopg2_sql.SQL(where_clause),
            )

            columns, rows = select_all(base, tuple(params))

            if not rows:
                return []

            return [dict(zip(columns, row)) for row in rows]

        except Exception as e:
            app_logger.error(f"Failed to get audit history: {e}")
            return []

    def get_record_changes(
        self,
        table_name: str,
        record_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get all changes for a specific record.

        Args:
            table_name: Table name
            record_id: Record ID

        Returns:
            List of changes
        """
        return self.get_audit_history(table_name, record_id=record_id)

    def get_user_activity(
        self,
        user_id: int,
        days: int = 30,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get user's recent activity across all tables.

        Args:
            user_id: User ID
            days: Number of days to look back
            limit: Max records

        Returns:
            List of user actions
        """
        from_date = datetime.now() - timedelta(days=days)

        try:
            sql = """
                SELECT
                    id, table_name, record_id, action_type,
                    changed_fields, action_timestamp, app_user
                FROM audit.logged_actions
                WHERE app_user_id = %s AND action_timestamp >= %s
                ORDER BY action_timestamp DESC
                LIMIT %s
            """

            columns, rows = select_all(sql, (user_id, from_date, limit))

            if not rows:
                return []

            return [dict(zip(columns, row)) for row in rows]

        except Exception as e:
            app_logger.error(f"Failed to get user activity: {e}")
            return []

    def get_audited_tables(self) -> List[str]:
        """
        Get list of tables that have audit triggers enabled.

        Returns:
            List of table names with active audit triggers
        """
        try:
            sql = """
                SELECT DISTINCT event_object_table
                FROM information_schema.triggers
                WHERE trigger_name LIKE 'audit_trigger_%'
                  AND action_statement LIKE '%audit.log_changes%'
                ORDER BY event_object_table
            """
            columns, rows = select_all(sql)

            if not rows:
                return []

            return [row[0] for row in rows]

        except Exception as e:
            app_logger.error(f"Failed to get audited tables: {e}")
            return []

    def get_audit_statistics(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get audit statistics for dashboard display.

        Args:
            days: Number of days to include

        Returns:
            Dict with statistics
        """
        from_date = datetime.now() - timedelta(days=days)

        try:
            # Total records
            total_sql = """
                SELECT COUNT(*) FROM audit.logged_actions
                WHERE action_timestamp >= %s
            """
            total = get_scalar(total_sql, (from_date,)) or 0

            # By action type
            action_sql = """
                SELECT action_type, COUNT(*)
                FROM audit.logged_actions
                WHERE action_timestamp >= %s
                GROUP BY action_type
                ORDER BY COUNT(*) DESC
            """
            _, action_rows = select_all(action_sql, (from_date,))
            by_action = {row[0]: row[1] for row in action_rows} if action_rows else {}

            # By table
            table_sql = """
                SELECT table_name, COUNT(*)
                FROM audit.logged_actions
                WHERE action_timestamp >= %s
                GROUP BY table_name
                ORDER BY COUNT(*) DESC
            """
            _, table_rows = select_all(table_sql, (from_date,))
            by_table = {row[0]: row[1] for row in table_rows} if table_rows else {}

            # Recent activity (last 24 hours)
            recent_sql = """
                SELECT COUNT(*) FROM audit.logged_actions
                WHERE action_timestamp >= %s
            """
            recent_date = datetime.now() - timedelta(days=1)
            recent = get_scalar(recent_sql, (recent_date,)) or 0

            return {
                "total": total,
                "by_action": by_action,
                "by_table": by_table,
                "recent_24h": recent,
                "period_days": days,
                "audited_tables": self.get_audited_tables(),
            }

        except Exception as e:
            app_logger.error(f"Failed to get audit statistics: {e}")
            return {
                "total": 0,
                "by_action": {},
                "by_table": {},
                "recent_24h": 0,
                "period_days": days,
                "audited_tables": [],
            }

    def get_total_count(
        self,
        table_name: Optional[str] = None,
        action_type: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> int:
        """
        Get total count of audit records matching filters.
        Used for pagination.

        Returns:
            Total record count
        """
        try:
            conditions: List[str] = []
            params: List[Any] = []

            if table_name:
                conditions.append("table_name = %s")
                params.append(table_name)

            if action_type:
                conditions.append("action_type = %s")
                params.append(action_type.upper())

            if from_date:
                conditions.append("action_timestamp >= %s")
                params.append(from_date)

            if to_date:
                conditions.append("action_timestamp <= %s")
                params.append(to_date)

            where_clause = " AND ".join(conditions) if conditions else "TRUE"

            count_sql = psycopg2_sql.SQL(
                "SELECT COUNT(*) FROM audit.logged_actions WHERE {where}"
            ).format(where=psycopg2_sql.SQL(where_clause))
            return get_scalar(count_sql, tuple(params)) or 0

        except Exception as e:
            app_logger.error(f"Failed to get audit count: {e}")
            return 0

    def purge_old_records(self, days: int = 365) -> int:
        """
        Remove audit records older than specified days.
        Use for database maintenance.

        Args:
            days: Keep records newer than this many days

        Returns:
            Number of records deleted
        """
        conn = None
        cursor = None
        try:
            cutoff = datetime.now() - timedelta(days=days)
            conn = get_connection()
            if conn is None:
                return 0

            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM audit.logged_actions WHERE action_timestamp < %s",
                (cutoff,)
            )
            deleted = cursor.rowcount
            conn.commit()

            app_logger.info(f"Purged {deleted} audit records older than {days} days")
            return deleted

        except Exception as e:
            app_logger.error(f"Failed to purge audit records: {e}")
            if conn:
                try:
                    conn.rollback()
                except Exception as rb_err:
                    app_logger.warning(f"Rollback failed: {rb_err}")
            return 0
        finally:
            if cursor:
                cursor.close()
            return_connection(conn)

    def is_audit_setup(self) -> bool:
        """
        Check if audit schema and tables exist.

        Returns:
            True if audit system is set up
        """
        try:
            sql = """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'audit'
                    AND table_name = 'logged_actions'
                )
            """
            result = get_scalar(sql)
            return bool(result)

        except Exception as e:
            app_logger.error(f"Failed to check audit setup: {e}")
            return False


# ============================================================
# Convenience functions
# ============================================================

def get_audit_history(
    table_name: Optional[str] = None,
    record_id: Optional[int] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Get audit history for a table/record."""
    manager = get_audit_manager()
    return manager.get_audit_history(
        table_name=table_name, record_id=record_id, limit=limit
    )


def setup_audit_system(tables: Optional[List[str]] = None) -> bool:
    """
    Setup complete audit system: schema + triggers.

    Args:
        tables: Tables to enable audit for (default: DEFAULT_AUDITED_TABLES)

    Returns:
        True if successful
    """
    if tables is None:
        tables = DEFAULT_AUDITED_TABLES

    manager = get_audit_manager()

    # Check if already set up
    if manager.is_audit_setup():
        app_logger.info("Audit system already set up, ensuring triggers are active")
    else:
        # Setup tables
        if not manager.setup_audit_tables():
            return False

    # Enable for specified tables
    success = True
    for table in tables:
        if not manager.enable_audit(table):
            app_logger.warning(f"Failed to enable audit for {table}")
            success = False

    if success:
        app_logger.info(
            f"Audit system fully configured for {len(tables)} tables: "
            f"{', '.join(tables)}"
        )

    return success
