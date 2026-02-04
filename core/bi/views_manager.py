# -*- coding: utf-8 -*-
"""
BI Views Manager
================
Manages creation and maintenance of optimized SQL Views for Power BI.

This module:
- Creates bi_views schema in PostgreSQL
- Installs optimized analytical views
- Supports view refresh and validation

Author: Mohamed
Version: 1.0.0
Date: February 2026
"""

from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from core.database import select_all, select_one, execute_query
from core.logging import app_logger


# =============================================================================
# SQL View Definitions
# =============================================================================

SQL_CREATE_SCHEMA = """
CREATE SCHEMA IF NOT EXISTS bi_views;
"""

SQL_VIEWS = {
    "employees_summary": """
-- View: Comprehensive Employee Summary
CREATE OR REPLACE VIEW bi_views.employees_summary AS
SELECT
    e.id AS employee_id,
    e.employee_number,
    e.name_ar,
    e.name_en,
    e.national_id,
    c.id AS company_id,
    c.name_ar AS company_name_ar,
    c.name_en AS company_name_en,
    d.id AS department_id,
    d.name_ar AS department_name_ar,
    d.name_en AS department_name_en,
    j.id AS job_title_id,
    j.name_ar AS job_title_ar,
    j.name_en AS job_title_en,
    n.id AS nationality_id,
    n.name_ar AS nationality_ar,
    n.name_en AS nationality_en,
    b.id AS bank_id,
    b.name_ar AS bank_name_ar,
    b.name_en AS bank_name_en,
    e.bank_account,
    es.id AS status_id,
    es.name_ar AS status_ar,
    es.name_en AS status_en,
    e.hire_date,
    e.salary,
    e.allowances,
    e.deductions,
    (e.salary + COALESCE(e.allowances, 0) - COALESCE(e.deductions, 0)) AS net_salary,
    e.phone,
    e.email,
    e.address,
    e.notes,
    e.created_at,
    e.updated_at,
    -- Calculated fields
    EXTRACT(YEAR FROM AGE(CURRENT_DATE, e.hire_date)) AS years_of_service,
    EXTRACT(MONTH FROM AGE(CURRENT_DATE, e.hire_date)) AS months_of_service,
    CASE
        WHEN e.status_id = 1 THEN 'Active'
        WHEN e.status_id = 2 THEN 'Terminated'
        WHEN e.status_id = 3 THEN 'On Leave'
        ELSE 'Unknown'
    END AS status_label_en,
    CASE
        WHEN e.status_id = 1 THEN 'نشط'
        WHEN e.status_id = 2 THEN 'منتهي'
        WHEN e.status_id = 3 THEN 'إجازة'
        ELSE 'غير محدد'
    END AS status_label_ar,
    EXTRACT(YEAR FROM e.hire_date) AS hire_year,
    EXTRACT(MONTH FROM e.hire_date) AS hire_month,
    TO_CHAR(e.hire_date, 'YYYY-MM') AS hire_period
FROM employees e
LEFT JOIN companies c ON e.company_id = c.id
LEFT JOIN departments d ON e.department_id = d.id
LEFT JOIN job_titles j ON e.job_title_id = j.id
LEFT JOIN nationalities n ON e.nationality_id = n.id
LEFT JOIN banks b ON e.bank_id = b.id
LEFT JOIN employee_statuses es ON e.status_id = es.id;
""",

    "department_stats": """
-- View: Department Statistics
CREATE OR REPLACE VIEW bi_views.department_stats AS
SELECT
    d.id AS department_id,
    d.name_ar AS department_name_ar,
    d.name_en AS department_name_en,
    c.id AS company_id,
    c.name_ar AS company_name_ar,
    COUNT(e.id) AS employee_count,
    COUNT(CASE WHEN e.status_id = 1 THEN 1 END) AS active_count,
    COUNT(CASE WHEN e.status_id = 2 THEN 1 END) AS terminated_count,
    COALESCE(AVG(e.salary), 0) AS avg_salary,
    COALESCE(MIN(e.salary), 0) AS min_salary,
    COALESCE(MAX(e.salary), 0) AS max_salary,
    COALESCE(SUM(e.salary), 0) AS total_salaries,
    COALESCE(SUM(e.salary + COALESCE(e.allowances, 0) - COALESCE(e.deductions, 0)), 0) AS total_net_salaries,
    MIN(e.hire_date) AS oldest_hire_date,
    MAX(e.hire_date) AS newest_hire_date,
    COALESCE(AVG(EXTRACT(YEAR FROM AGE(CURRENT_DATE, e.hire_date))), 0) AS avg_years_of_service
FROM departments d
LEFT JOIN employees e ON e.department_id = d.id AND e.status_id = 1
LEFT JOIN companies c ON d.company_id = c.id
GROUP BY d.id, d.name_ar, d.name_en, c.id, c.name_ar;
""",

    "payroll_analysis": """
-- View: Payroll Analysis
CREATE OR REPLACE VIEW bi_views.payroll_analysis AS
SELECT
    c.id AS company_id,
    c.name_ar AS company_name,
    d.id AS department_id,
    d.name_ar AS department_name,
    j.id AS job_title_id,
    j.name_ar AS job_title,
    COUNT(e.id) AS employee_count,
    SUM(e.salary) AS total_base_salary,
    SUM(COALESCE(e.allowances, 0)) AS total_allowances,
    SUM(COALESCE(e.deductions, 0)) AS total_deductions,
    SUM(e.salary + COALESCE(e.allowances, 0) - COALESCE(e.deductions, 0)) AS total_net_salary,
    AVG(e.salary) AS avg_base_salary,
    AVG(e.salary + COALESCE(e.allowances, 0) - COALESCE(e.deductions, 0)) AS avg_net_salary,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY e.salary) AS median_salary,
    STDDEV(e.salary) AS salary_stddev,
    -- Salary ranges
    COUNT(CASE WHEN e.salary < 5000 THEN 1 END) AS salary_under_5k,
    COUNT(CASE WHEN e.salary >= 5000 AND e.salary < 10000 THEN 1 END) AS salary_5k_10k,
    COUNT(CASE WHEN e.salary >= 10000 AND e.salary < 20000 THEN 1 END) AS salary_10k_20k,
    COUNT(CASE WHEN e.salary >= 20000 THEN 1 END) AS salary_over_20k
FROM employees e
JOIN companies c ON e.company_id = c.id
JOIN departments d ON e.department_id = d.id
JOIN job_titles j ON e.job_title_id = j.id
WHERE e.status_id = 1
GROUP BY c.id, c.name_ar, d.id, d.name_ar, j.id, j.name_ar;
""",

    "monthly_trends": """
-- View: Monthly Hiring and Termination Trends
CREATE OR REPLACE VIEW bi_views.monthly_trends AS
WITH months AS (
    SELECT generate_series(
        DATE_TRUNC('month', CURRENT_DATE - INTERVAL '12 months'),
        DATE_TRUNC('month', CURRENT_DATE),
        '1 month'::interval
    )::date AS month_date
),
hires AS (
    SELECT
        DATE_TRUNC('month', hire_date)::date AS month_date,
        COUNT(*) AS hire_count,
        SUM(salary) AS hired_salary_total
    FROM employees
    WHERE hire_date >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY DATE_TRUNC('month', hire_date)
),
terminations AS (
    SELECT
        DATE_TRUNC('month', updated_at)::date AS month_date,
        COUNT(*) AS termination_count
    FROM employees
    WHERE status_id = 2 AND updated_at >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY DATE_TRUNC('month', updated_at)
)
SELECT
    m.month_date,
    TO_CHAR(m.month_date, 'YYYY-MM') AS period,
    TO_CHAR(m.month_date, 'Month YYYY') AS period_label,
    EXTRACT(YEAR FROM m.month_date) AS year,
    EXTRACT(MONTH FROM m.month_date) AS month,
    COALESCE(h.hire_count, 0) AS hires,
    COALESCE(h.hired_salary_total, 0) AS hired_salary_total,
    COALESCE(t.termination_count, 0) AS terminations,
    COALESCE(h.hire_count, 0) - COALESCE(t.termination_count, 0) AS net_change
FROM months m
LEFT JOIN hires h ON h.month_date = m.month_date
LEFT JOIN terminations t ON t.month_date = m.month_date
ORDER BY m.month_date;
""",

    "company_summary": """
-- View: Company Summary
CREATE OR REPLACE VIEW bi_views.company_summary AS
SELECT
    c.id AS company_id,
    c.name_ar AS company_name_ar,
    c.name_en AS company_name_en,
    COUNT(DISTINCT d.id) AS department_count,
    COUNT(e.id) AS total_employees,
    COUNT(CASE WHEN e.status_id = 1 THEN 1 END) AS active_employees,
    COUNT(CASE WHEN e.status_id = 2 THEN 1 END) AS terminated_employees,
    COALESCE(SUM(e.salary), 0) AS total_salaries,
    COALESCE(AVG(e.salary), 0) AS avg_salary,
    MIN(e.hire_date) AS oldest_employee_date,
    MAX(e.hire_date) AS newest_employee_date,
    -- Headcount by nationality
    COUNT(DISTINCT e.nationality_id) AS nationality_count
FROM companies c
LEFT JOIN departments d ON d.company_id = c.id
LEFT JOIN employees e ON e.company_id = c.id
GROUP BY c.id, c.name_ar, c.name_en;
""",

    "job_title_analysis": """
-- View: Job Title Analysis
CREATE OR REPLACE VIEW bi_views.job_title_analysis AS
SELECT
    j.id AS job_title_id,
    j.name_ar AS job_title_ar,
    j.name_en AS job_title_en,
    COUNT(e.id) AS employee_count,
    COUNT(CASE WHEN e.status_id = 1 THEN 1 END) AS active_count,
    COALESCE(AVG(e.salary), 0) AS avg_salary,
    COALESCE(MIN(e.salary), 0) AS min_salary,
    COALESCE(MAX(e.salary), 0) AS max_salary,
    COALESCE(SUM(e.salary), 0) AS total_salaries,
    COALESCE(AVG(EXTRACT(YEAR FROM AGE(CURRENT_DATE, e.hire_date))), 0) AS avg_tenure_years
FROM job_titles j
LEFT JOIN employees e ON e.job_title_id = j.id
GROUP BY j.id, j.name_ar, j.name_en;
""",

    "nationality_distribution": """
-- View: Nationality Distribution
CREATE OR REPLACE VIEW bi_views.nationality_distribution AS
SELECT
    n.id AS nationality_id,
    n.name_ar AS nationality_ar,
    n.name_en AS nationality_en,
    COUNT(e.id) AS employee_count,
    COUNT(CASE WHEN e.status_id = 1 THEN 1 END) AS active_count,
    ROUND(COUNT(e.id) * 100.0 / NULLIF(SUM(COUNT(e.id)) OVER(), 0), 2) AS percentage,
    COALESCE(AVG(e.salary), 0) AS avg_salary
FROM nationalities n
LEFT JOIN employees e ON e.nationality_id = n.id
GROUP BY n.id, n.name_ar, n.name_en
ORDER BY employee_count DESC;
"""
}


# =============================================================================
# View Status
# =============================================================================

class ViewStatus(Enum):
    """Status of a BI View."""
    NOT_EXISTS = "not_exists"
    EXISTS = "exists"
    ERROR = "error"


@dataclass
class ViewInfo:
    """Information about a BI View."""
    name: str
    name_ar: str
    name_en: str
    status: ViewStatus
    row_count: int = 0
    last_refresh: str = ""
    error: str = ""


# =============================================================================
# BI Views Manager
# =============================================================================

class BIViewsManager:
    """
    Manages BI Views in PostgreSQL.

    Provides methods to create, refresh, and validate
    analytical views for Power BI integration.
    """

    def __init__(self):
        """Initialize the Views Manager."""
        self._views_info: Dict[str, ViewInfo] = {}

    def create_schema(self) -> bool:
        """Create the bi_views schema if not exists."""
        try:
            execute_query(SQL_CREATE_SCHEMA)
            app_logger.info("BI Views schema created/verified")
            return True
        except Exception as e:
            app_logger.error(f"Failed to create BI schema: {e}")
            return False

    def create_view(self, view_name: str) -> bool:
        """Create a specific BI View."""
        if view_name not in SQL_VIEWS:
            app_logger.error(f"Unknown view: {view_name}")
            return False

        try:
            sql = SQL_VIEWS[view_name]
            execute_query(sql)
            app_logger.info(f"Created BI view: {view_name}")
            return True
        except Exception as e:
            app_logger.error(f"Failed to create view {view_name}: {e}")
            return False

    def create_all_views(self) -> Tuple[int, int]:
        """
        Create all BI Views.

        Returns:
            Tuple of (success_count, failure_count)
        """
        # First create schema
        if not self.create_schema():
            return (0, len(SQL_VIEWS))

        success = 0
        failed = 0

        for view_name in SQL_VIEWS:
            if self.create_view(view_name):
                success += 1
            else:
                failed += 1

        app_logger.info(f"BI Views created: {success} success, {failed} failed")
        return (success, failed)

    def check_view_exists(self, view_name: str) -> bool:
        """Check if a view exists in the database."""
        try:
            sql = """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.views
                WHERE table_schema = 'bi_views'
                AND table_name = %s
            )
            """
            columns, rows = select_all(sql, (view_name,))
            return rows[0][0] if rows else False
        except Exception:
            return False

    def get_view_row_count(self, view_name: str) -> int:
        """Get the row count of a view."""
        try:
            sql = f"SELECT COUNT(*) FROM bi_views.{view_name}"
            columns, rows = select_all(sql)
            return rows[0][0] if rows else 0
        except Exception:
            return 0

    def get_view_info(self, view_name: str) -> ViewInfo:
        """Get detailed information about a view."""
        from .connection_config import BI_VIEWS_CONFIG

        view_config = BI_VIEWS_CONFIG["views"].get(view_name, {})
        name_ar = view_config.get("name_ar", view_name)
        name_en = view_config.get("name_en", view_name)

        try:
            if self.check_view_exists(view_name):
                row_count = self.get_view_row_count(view_name)
                return ViewInfo(
                    name=view_name,
                    name_ar=name_ar,
                    name_en=name_en,
                    status=ViewStatus.EXISTS,
                    row_count=row_count
                )
            else:
                return ViewInfo(
                    name=view_name,
                    name_ar=name_ar,
                    name_en=name_en,
                    status=ViewStatus.NOT_EXISTS
                )
        except Exception as e:
            return ViewInfo(
                name=view_name,
                name_ar=name_ar,
                name_en=name_en,
                status=ViewStatus.ERROR,
                error=str(e)
            )

    def get_all_views_info(self) -> List[ViewInfo]:
        """Get information about all BI Views."""
        return [self.get_view_info(name) for name in SQL_VIEWS.keys()]

    def refresh_view(self, view_name: str) -> bool:
        """Refresh a view (recreate it)."""
        return self.create_view(view_name)

    def refresh_all_views(self) -> Tuple[int, int]:
        """Refresh all views."""
        return self.create_all_views()

    def drop_view(self, view_name: str) -> bool:
        """Drop a specific view."""
        try:
            sql = f"DROP VIEW IF EXISTS bi_views.{view_name} CASCADE"
            execute_query(sql)
            app_logger.info(f"Dropped BI view: {view_name}")
            return True
        except Exception as e:
            app_logger.error(f"Failed to drop view {view_name}: {e}")
            return False

    def drop_all_views(self) -> bool:
        """Drop all BI Views."""
        try:
            for view_name in SQL_VIEWS:
                self.drop_view(view_name)
            return True
        except Exception:
            return False

    def get_view_data(self, view_name: str, limit: int = 1000) -> Tuple[List[str], List[Tuple]]:
        """
        Get data from a view.

        Args:
            view_name: Name of the view
            limit: Maximum rows to return

        Returns:
            Tuple of (column_names, rows)
        """
        try:
            sql = f"SELECT * FROM bi_views.{view_name} LIMIT %s"
            return select_all(sql, (limit,))
        except Exception as e:
            app_logger.error(f"Failed to get data from {view_name}: {e}")
            return ([], [])


# =============================================================================
# Singleton Instance
# =============================================================================

_views_manager_instance: Optional[BIViewsManager] = None


def get_bi_views_manager() -> BIViewsManager:
    """Get the singleton BIViewsManager instance."""
    global _views_manager_instance
    if _views_manager_instance is None:
        _views_manager_instance = BIViewsManager()
    return _views_manager_instance
