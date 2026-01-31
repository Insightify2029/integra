"""
Employees Module
================
"""

from .list import EmployeesListTable
from .queries import (
    get_all_employees,
    get_employees_count,
    get_active_employees_count,
    get_nationalities_count,
    get_departments_count,
    get_jobs_count
)

__all__ = [
    'EmployeesListTable',
    'get_all_employees',
    'get_employees_count',
    'get_active_employees_count',
    'get_nationalities_count',
    'get_departments_count',
    'get_jobs_count'
]
