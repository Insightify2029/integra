-- =====================================================
-- INTEGRA Audit Triggers Setup
-- =====================================================
-- تفعيل التدقيق على الجداول الحساسة
-- =====================================================

-- Make sure schema and functions exist first
-- Run audit_schema.sql before this file

-- =====================================================
-- Enable audit on sensitive tables
-- =====================================================

-- Core employee data
SELECT audit.enable_audit('employees', 'public');

-- Company and organizational structure
SELECT audit.enable_audit('companies', 'public');
SELECT audit.enable_audit('departments', 'public');

-- Job and status information
SELECT audit.enable_audit('job_titles', 'public');
SELECT audit.enable_audit('employee_statuses', 'public');

-- Financial data (when tables exist)
-- SELECT audit.enable_audit('payroll', 'public');
-- SELECT audit.enable_audit('salary_history', 'public');
-- SELECT audit.enable_audit('deductions', 'public');
-- SELECT audit.enable_audit('allowances', 'public');

-- Contracts (when table exists)
-- SELECT audit.enable_audit('contracts', 'public');

-- =====================================================
-- Verify triggers are created
-- =====================================================
DO $$
DECLARE
    trigger_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO trigger_count
    FROM information_schema.triggers
    WHERE trigger_name LIKE 'audit_trigger_%';

    RAISE NOTICE 'Total audit triggers created: %', trigger_count;
END $$;
