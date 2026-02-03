-- =====================================================
-- INTEGRA Audit Trail Schema
-- =====================================================
-- جدول سجل التدقيق لتتبع كل التغييرات
-- =====================================================

-- Create audit schema if not exists
CREATE SCHEMA IF NOT EXISTS audit;

-- =====================================================
-- Main audit log table
-- =====================================================
CREATE TABLE IF NOT EXISTS audit.logged_actions (
    id              BIGSERIAL PRIMARY KEY,

    -- What was changed
    schema_name     TEXT NOT NULL,
    table_name      TEXT NOT NULL,
    record_id       INTEGER,

    -- Type of change
    action          TEXT NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),

    -- The data
    old_data        JSONB,
    new_data        JSONB,
    changed_fields  TEXT[],

    -- Who and when
    changed_by      TEXT DEFAULT current_user,
    app_user        TEXT,
    changed_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Context
    client_ip       INET,
    session_id      TEXT,
    transaction_id  BIGINT DEFAULT txid_current()
);

-- =====================================================
-- Indexes for efficient querying
-- =====================================================

-- Index for table lookups
CREATE INDEX IF NOT EXISTS idx_audit_table
    ON audit.logged_actions(schema_name, table_name);

-- Index for record history
CREATE INDEX IF NOT EXISTS idx_audit_record
    ON audit.logged_actions(table_name, record_id);

-- Index for time-based queries
CREATE INDEX IF NOT EXISTS idx_audit_time
    ON audit.logged_actions(changed_at DESC);

-- Index for user queries
CREATE INDEX IF NOT EXISTS idx_audit_user
    ON audit.logged_actions(app_user);

-- Index for JSONB searches (GIN index)
CREATE INDEX IF NOT EXISTS idx_audit_old_data
    ON audit.logged_actions USING GIN (old_data);

CREATE INDEX IF NOT EXISTS idx_audit_new_data
    ON audit.logged_actions USING GIN (new_data);

-- =====================================================
-- Helper functions
-- =====================================================

-- Function to get changed fields between old and new
CREATE OR REPLACE FUNCTION audit.get_changed_fields(old_data JSONB, new_data JSONB)
RETURNS TEXT[] AS $$
DECLARE
    result TEXT[] := ARRAY[]::TEXT[];
    key TEXT;
BEGIN
    -- For INSERT, all fields are "changed"
    IF old_data IS NULL THEN
        SELECT array_agg(k) INTO result FROM jsonb_object_keys(new_data) k;
        RETURN result;
    END IF;

    -- For DELETE, no fields changed
    IF new_data IS NULL THEN
        RETURN result;
    END IF;

    -- For UPDATE, find differences
    FOR key IN SELECT jsonb_object_keys(new_data) UNION SELECT jsonb_object_keys(old_data)
    LOOP
        IF (old_data->key)::TEXT IS DISTINCT FROM (new_data->key)::TEXT THEN
            result := array_append(result, key);
        END IF;
    END LOOP;

    RETURN result;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =====================================================
-- Main audit trigger function
-- =====================================================
CREATE OR REPLACE FUNCTION audit.log_changes()
RETURNS TRIGGER AS $$
DECLARE
    old_data JSONB;
    new_data JSONB;
    changed_fields TEXT[];
    record_id INTEGER;
    v_app_user TEXT;
BEGIN
    -- Get app user from session variable (set by application)
    BEGIN
        v_app_user := current_setting('app.current_user', true);
    EXCEPTION WHEN OTHERS THEN
        v_app_user := NULL;
    END;

    -- Handle different operations
    IF TG_OP = 'INSERT' THEN
        new_data := to_jsonb(NEW);
        old_data := NULL;
        record_id := NEW.id;
        changed_fields := audit.get_changed_fields(NULL, new_data);

    ELSIF TG_OP = 'UPDATE' THEN
        old_data := to_jsonb(OLD);
        new_data := to_jsonb(NEW);
        record_id := NEW.id;
        changed_fields := audit.get_changed_fields(old_data, new_data);

        -- Skip if no actual changes
        IF old_data = new_data THEN
            RETURN NEW;
        END IF;

    ELSIF TG_OP = 'DELETE' THEN
        old_data := to_jsonb(OLD);
        new_data := NULL;
        record_id := OLD.id;
        changed_fields := ARRAY[]::TEXT[];
    END IF;

    -- Insert audit record
    INSERT INTO audit.logged_actions (
        schema_name,
        table_name,
        record_id,
        action,
        old_data,
        new_data,
        changed_fields,
        app_user
    ) VALUES (
        TG_TABLE_SCHEMA,
        TG_TABLE_NAME,
        record_id,
        TG_OP,
        old_data,
        new_data,
        changed_fields,
        v_app_user
    );

    -- Return appropriate record
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =====================================================
-- Function to enable audit on a table
-- =====================================================
CREATE OR REPLACE FUNCTION audit.enable_audit(target_table TEXT, target_schema TEXT DEFAULT 'public')
RETURNS VOID AS $$
DECLARE
    trigger_name TEXT;
BEGIN
    trigger_name := 'audit_trigger_' || target_table;

    -- Drop existing trigger if exists
    EXECUTE format(
        'DROP TRIGGER IF EXISTS %I ON %I.%I',
        trigger_name, target_schema, target_table
    );

    -- Create new trigger
    EXECUTE format(
        'CREATE TRIGGER %I
         AFTER INSERT OR UPDATE OR DELETE ON %I.%I
         FOR EACH ROW EXECUTE FUNCTION audit.log_changes()',
        trigger_name, target_schema, target_table
    );

    RAISE NOTICE 'Audit enabled for %.%', target_schema, target_table;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Function to disable audit on a table
-- =====================================================
CREATE OR REPLACE FUNCTION audit.disable_audit(target_table TEXT, target_schema TEXT DEFAULT 'public')
RETURNS VOID AS $$
DECLARE
    trigger_name TEXT;
BEGIN
    trigger_name := 'audit_trigger_' || target_table;

    EXECUTE format(
        'DROP TRIGGER IF EXISTS %I ON %I.%I',
        trigger_name, target_schema, target_table
    );

    RAISE NOTICE 'Audit disabled for %.%', target_schema, target_table;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- View for easier querying
-- =====================================================
CREATE OR REPLACE VIEW audit.recent_changes AS
SELECT
    id,
    table_name,
    record_id,
    action,
    changed_fields,
    app_user,
    changed_at,
    CASE
        WHEN action = 'INSERT' THEN new_data
        WHEN action = 'DELETE' THEN old_data
        ELSE jsonb_build_object(
            'before', old_data,
            'after', new_data
        )
    END AS data_summary
FROM audit.logged_actions
ORDER BY changed_at DESC
LIMIT 100;

-- =====================================================
-- Cleanup function (retention policy)
-- =====================================================
CREATE OR REPLACE FUNCTION audit.cleanup_old_records(retention_days INTEGER DEFAULT 365)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM audit.logged_actions
    WHERE changed_at < now() - (retention_days || ' days')::INTERVAL;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Comments
-- =====================================================
COMMENT ON TABLE audit.logged_actions IS 'سجل تدقيق لتتبع كل التغييرات في الجداول المراقبة';
COMMENT ON FUNCTION audit.log_changes() IS 'وظيفة الـ trigger لتسجيل التغييرات تلقائياً';
COMMENT ON FUNCTION audit.enable_audit(TEXT, TEXT) IS 'تفعيل التدقيق على جدول معين';
COMMENT ON FUNCTION audit.disable_audit(TEXT, TEXT) IS 'إيقاف التدقيق على جدول معين';
