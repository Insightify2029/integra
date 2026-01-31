"""
Employees Queries
=================
Database queries for employees.
"""

from core.database import select_all, get_scalar


def get_all_employees():
    """
    Get all employees with related data.
    
    Returns:
        tuple: (columns, rows)
    """
    query = """
    SELECT 
        e.employee_code as "الكود",
        e.name_ar as "الاسم",
        e.name_en as "Name",
        n.name_ar as "الجنسية",
        d.name_en as "القسم",
        j.name_ar as "الوظيفة",
        b.name_en as "البنك",
        e.iban as "IBAN",
        e.hire_date as "تاريخ التعيين",
        c.name_en as "الشركة",
        s.name_ar as "الحالة"
    FROM employees e
    LEFT JOIN nationalities n ON e.nationality_id = n.id
    LEFT JOIN departments d ON e.department_id = d.id
    LEFT JOIN job_titles j ON e.job_title_id = j.id
    LEFT JOIN banks b ON e.bank_id = b.id
    LEFT JOIN companies c ON e.company_id = c.id
    LEFT JOIN employee_statuses s ON e.status_id = s.id
    ORDER BY e.employee_code
    """
    return select_all(query)


def get_employees_count():
    """Get total employees count."""
    return get_scalar("SELECT COUNT(*) FROM employees") or 0


def get_active_employees_count():
    """Get active employees count."""
    return get_scalar("SELECT COUNT(*) FROM employees WHERE status_id = 1") or 0


def get_nationalities_count():
    """Get distinct nationalities count."""
    return get_scalar("SELECT COUNT(DISTINCT nationality_id) FROM employees") or 0


def get_departments_count():
    """Get distinct departments count."""
    return get_scalar("SELECT COUNT(DISTINCT department_id) FROM employees") or 0


def get_jobs_count():
    """Get distinct job titles count."""
    return get_scalar("SELECT COUNT(DISTINCT job_title_id) FROM employees") or 0
