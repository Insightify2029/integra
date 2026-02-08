-- =================================================================
-- INTEGRA Audit Trail Triggers
-- =================================================================
-- Creates the trigger function and applies it to sensitive tables.
--
-- The trigger function captures:
--   - WHO made the change (db_user + app_user)
--   - WHAT changed (old_data, new_data, changed_fields)
--   - WHEN it happened (action_timestamp)
--   - WHICH record (table_name, record_id)
--   - WHAT type of change (INSERT, UPDATE, DELETE)
--
-- Run AFTER audit_schema.sql
-- =================================================================

-- Create or replace the audit trigger function
CREATE OR REPLACE FUNCTION audit.log_changes()
RETURNS TRIGGER AS $$
DECLARE
    v_old_data   JSONB;
    v_new_data   JSONB;
    v_changed    TEXT[];
    v_record_id  INTEGER;
BEGIN
    -- Determine record ID and data based on operation type
    IF TG_OP = 'DELETE' THEN
        v_record_id := OLD.id;
        v_old_data  := to_jsonb(OLD);
        v_new_data  := NULL;

    ELSIF TG_OP = 'INSERT' THEN
        v_record_id := NEW.id;
        v_old_data  := NULL;
        v_new_data  := to_jsonb(NEW);

    ELSIF TG_OP = 'UPDATE' THEN
        v_record_id := NEW.id;
        v_old_data  := to_jsonb(OLD);
        v_new_data  := to_jsonb(NEW);

        -- Build array of changed field names
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

    RETURN NULL;  -- AFTER trigger, return value is ignored
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Comment on function
COMMENT ON FUNCTION audit.log_changes() IS
    'Generic audit trigger function - logs all row changes to audit.logged_actions';

-- =================================================================
-- Apply triggers to sensitive tables
-- =================================================================

-- employees table
DROP TRIGGER IF EXISTS audit_trigger_employees ON public.employees;
CREATE TRIGGER audit_trigger_employees
    AFTER INSERT OR UPDATE OR DELETE ON public.employees
    FOR EACH ROW EXECUTE FUNCTION audit.log_changes();

-- companies table
DROP TRIGGER IF EXISTS audit_trigger_companies ON public.companies;
CREATE TRIGGER audit_trigger_companies
    AFTER INSERT OR UPDATE OR DELETE ON public.companies
    FOR EACH ROW EXECUTE FUNCTION audit.log_changes();

-- departments table
DROP TRIGGER IF EXISTS audit_trigger_departments ON public.departments;
CREATE TRIGGER audit_trigger_departments
    AFTER INSERT OR UPDATE OR DELETE ON public.departments
    FOR EACH ROW EXECUTE FUNCTION audit.log_changes();

-- job_titles table
DROP TRIGGER IF EXISTS audit_trigger_job_titles ON public.job_titles;
CREATE TRIGGER audit_trigger_job_titles
    AFTER INSERT OR UPDATE OR DELETE ON public.job_titles
    FOR EACH ROW EXECUTE FUNCTION audit.log_changes();

-- banks table
DROP TRIGGER IF EXISTS audit_trigger_banks ON public.banks;
CREATE TRIGGER audit_trigger_banks
    AFTER INSERT OR UPDATE OR DELETE ON public.banks
    FOR EACH ROW EXECUTE FUNCTION audit.log_changes();

-- employee_statuses table
DROP TRIGGER IF EXISTS audit_trigger_employee_statuses ON public.employee_statuses;
CREATE TRIGGER audit_trigger_employee_statuses
    AFTER INSERT OR UPDATE OR DELETE ON public.employee_statuses
    FOR EACH ROW EXECUTE FUNCTION audit.log_changes();

-- nationalities table
DROP TRIGGER IF EXISTS audit_trigger_nationalities ON public.nationalities;
CREATE TRIGGER audit_trigger_nationalities
    AFTER INSERT OR UPDATE OR DELETE ON public.nationalities
    FOR EACH ROW EXECUTE FUNCTION audit.log_changes();
