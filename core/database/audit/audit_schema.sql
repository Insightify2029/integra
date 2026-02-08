-- =================================================================
-- INTEGRA Audit Trail Schema
-- =================================================================
-- Creates the audit schema, logged_actions table, and indexes
-- for tracking all changes to sensitive database tables.
--
-- Run this ONCE during initial database setup.
-- =================================================================

-- Create audit schema
CREATE SCHEMA IF NOT EXISTS audit;

-- Create the main audit log table
CREATE TABLE IF NOT EXISTS audit.logged_actions (
    id              BIGSERIAL PRIMARY KEY,
    schema_name     TEXT NOT NULL,
    table_name      TEXT NOT NULL,
    record_id       INTEGER,
    action_type     TEXT NOT NULL CHECK (action_type IN ('INSERT', 'UPDATE', 'DELETE')),
    old_data        JSONB,
    new_data        JSONB,
    changed_fields  TEXT[],
    action_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    db_user         TEXT DEFAULT current_user,
    app_user        TEXT,
    app_user_id     INTEGER,
    client_ip       INET,
    session_id      TEXT,
    notes           TEXT
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_audit_table_name
    ON audit.logged_actions(table_name);

CREATE INDEX IF NOT EXISTS idx_audit_record_id
    ON audit.logged_actions(record_id);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp
    ON audit.logged_actions(action_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_audit_action_type
    ON audit.logged_actions(action_type);

CREATE INDEX IF NOT EXISTS idx_audit_app_user_id
    ON audit.logged_actions(app_user_id);

-- Composite index for common query patterns
CREATE INDEX IF NOT EXISTS idx_audit_table_record
    ON audit.logged_actions(table_name, record_id);

CREATE INDEX IF NOT EXISTS idx_audit_table_timestamp
    ON audit.logged_actions(table_name, action_timestamp DESC);

-- Comment on table
COMMENT ON TABLE audit.logged_actions IS
    'Audit trail - tracks all INSERT/UPDATE/DELETE on monitored tables';

COMMENT ON COLUMN audit.logged_actions.old_data IS
    'JSONB snapshot of the row BEFORE the change (NULL for INSERT)';

COMMENT ON COLUMN audit.logged_actions.new_data IS
    'JSONB snapshot of the row AFTER the change (NULL for DELETE)';

COMMENT ON COLUMN audit.logged_actions.changed_fields IS
    'Array of column names that were modified (UPDATE only)';

COMMENT ON COLUMN audit.logged_actions.app_user IS
    'Application-level username (set via SET LOCAL app.current_user)';
