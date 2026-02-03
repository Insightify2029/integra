"""
Audit Trail System
==================
Track all changes to sensitive database tables.

Features:
- Log all INSERT, UPDATE, DELETE operations
- Store old and new values
- Track user who made the change
- Query audit history

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

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from core.database import select_all, get_connection
from core.logging import app_logger, audit_logger


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
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit.logged_actions(action_timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_action_type ON audit.logged_actions(action_type);
CREATE INDEX IF NOT EXISTS idx_audit_app_user_id ON audit.logged_actions(app_user_id);
"""

# SQL for creating audit trigger function
AUDIT_TRIGGER_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION audit.log_changes()
RETURNS TRIGGER AS $$
DECLARE
    old_data JSONB;
    new_data JSONB;
    changed_fields TEXT[];
    record_id INTEGER;
BEGIN
    -- Get record ID
    IF TG_OP = 'DELETE' THEN
        record_id := OLD.id;
        old_data := to_jsonb(OLD);
        new_data := NULL;
    ELSIF TG_OP = 'INSERT' THEN
        record_id := NEW.id;
        old_data := NULL;
        new_data := to_jsonb(NEW);
    ELSIF TG_OP = 'UPDATE' THEN
        record_id := NEW.id;
        old_data := to_jsonb(OLD);
        new_data := to_jsonb(NEW);

        -- Get list of changed fields
        SELECT array_agg(key) INTO changed_fields
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
        record_id,
        TG_OP,
        old_data,
        new_data,
        changed_fields,
        current_user,
        current_setting('app.current_user', true),
        NULLIF(current_setting('app.current_user_id', true), '')::INTEGER
    );

    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
"""

# SQL template for creating trigger on a table
AUDIT_TRIGGER_SQL = """
DROP TRIGGER IF EXISTS audit_trigger_{table} ON {schema}.{table};

CREATE TRIGGER audit_trigger_{table}
AFTER INSERT OR UPDATE OR DELETE ON {schema}.{table}
FOR EACH ROW EXECUTE FUNCTION audit.log_changes();
"""


class AuditManager:
    """Manage audit trail setup and queries."""

    def __init__(self):
        """Initialize audit manager."""
        self._connection = None
        app_logger.debug("AuditManager initialized")

    def _get_connection(self):
        """Get database connection."""
        if self._connection is None or self._connection.closed:
            self._connection = get_connection()
        return self._connection

    def setup_audit_tables(self) -> bool:
        """
        Create audit schema and tables.
        Run this once during initial setup.

        Returns:
            True if successful
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Create schema and table
            cursor.execute(AUDIT_SCHEMA_SQL)

            # Create trigger function
            cursor.execute(AUDIT_TRIGGER_FUNCTION_SQL)

            conn.commit()
            cursor.close()

            app_logger.info("Audit tables created successfully")
            return True

        except Exception as e:
            app_logger.error(f"Failed to setup audit tables: {e}")
            if conn:
                conn.rollback()
            return False

    def enable_audit(self, table_name: str, schema: str = "public") -> bool:
        """
        Enable audit logging for a table.

        Args:
            table_name: Table to audit
            schema: Schema name (default: public)

        Returns:
            True if successful
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            sql = AUDIT_TRIGGER_SQL.format(table=table_name, schema=schema)
            cursor.execute(sql)

            conn.commit()
            cursor.close()

            app_logger.info(f"Audit enabled for {schema}.{table_name}")
            return True

        except Exception as e:
            app_logger.error(f"Failed to enable audit for {table_name}: {e}")
            if conn:
                conn.rollback()
            return False

    def disable_audit(self, table_name: str, schema: str = "public") -> bool:
        """
        Disable audit logging for a table.

        Args:
            table_name: Table name
            schema: Schema name

        Returns:
            True if successful
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            sql = f"DROP TRIGGER IF EXISTS audit_trigger_{table_name} ON {schema}.{table_name};"
            cursor.execute(sql)

            conn.commit()
            cursor.close()

            app_logger.info(f"Audit disabled for {schema}.{table_name}")
            return True

        except Exception as e:
            app_logger.error(f"Failed to disable audit for {table_name}: {e}")
            return False

    def set_app_user(self, user_name: str, user_id: int) -> None:
        """
        Set current application user for audit logging.
        Call this when user logs in.

        Args:
            user_name: User name
            user_id: User ID
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(f"SET LOCAL app.current_user = %s", (user_name,))
            cursor.execute(f"SET LOCAL app.current_user_id = %s", (str(user_id),))

            cursor.close()

        except Exception as e:
            app_logger.error(f"Failed to set app user: {e}")

    def get_audit_history(
        self,
        table_name: str,
        record_id: Optional[int] = None,
        action_type: Optional[str] = None,
        user_id: Optional[int] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get audit history.

        Args:
            table_name: Table name to query
            record_id: Filter by record ID
            action_type: Filter by action (INSERT, UPDATE, DELETE)
            user_id: Filter by user
            from_date: Start date
            to_date: End date
            limit: Max records
            offset: Offset for pagination

        Returns:
            List of audit records
        """
        try:
            conditions = ["table_name = %s"]
            params = [table_name]

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

            where_clause = " AND ".join(conditions)
            params.extend([limit, offset])

            sql = f"""
                SELECT
                    id, schema_name, table_name, record_id,
                    action_type, old_data, new_data, changed_fields,
                    action_timestamp, db_user, app_user, app_user_id
                FROM audit.logged_actions
                WHERE {where_clause}
                ORDER BY action_timestamp DESC
                LIMIT %s OFFSET %s
            """

            columns, rows = select_all(sql, tuple(params))

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
        Get user's recent activity.

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
                    changed_fields, action_timestamp
                FROM audit.logged_actions
                WHERE app_user_id = %s AND action_timestamp >= %s
                ORDER BY action_timestamp DESC
                LIMIT %s
            """

            columns, rows = select_all(sql, (user_id, from_date, limit))
            return [dict(zip(columns, row)) for row in rows]

        except Exception as e:
            app_logger.error(f"Failed to get user activity: {e}")
            return []


# Convenience functions

def get_audit_history(
    table_name: str,
    record_id: Optional[int] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Get audit history for a table/record."""
    manager = AuditManager()
    return manager.get_audit_history(table_name, record_id=record_id, limit=limit)


def setup_audit_system(tables: List[str] = None) -> bool:
    """
    Setup complete audit system.

    Args:
        tables: Tables to enable audit for (default: employees)

    Returns:
        True if successful
    """
    if tables is None:
        tables = ["employees"]

    manager = AuditManager()

    # Setup tables
    if not manager.setup_audit_tables():
        return False

    # Enable for specified tables
    for table in tables:
        if not manager.enable_audit(table):
            app_logger.warning(f"Failed to enable audit for {table}")

    return True
