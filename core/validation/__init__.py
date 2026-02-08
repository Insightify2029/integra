"""
Validation Module
=================
Pydantic schemas for data validation.

Usage:
    from core.validation import (
        EmployeeCreate,
        EmployeeUpdate,
        validate_employee_create,
        PayrollCreate,
        validate_payroll_create
    )

    # Validate new employee
    is_valid, employee, errors = validate_employee_create(data)
    if is_valid:
        # Use employee.model_dump()
        pass
    else:
        # Handle errors
        pass

    # Validate payroll
    is_valid, payroll, errors = validate_payroll_create(data)
"""

from .schemas.employee import (
    EmployeeBase,
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    EmployeeListItem,
    validate_employee_create,
    validate_employee_update
)

from .schemas.payroll import (
    PayrollStatus,
    PayrollBase,
    PayrollCreate,
    PayrollUpdate,
    PayrollResponse,
    PayrollSummary,
    validate_payroll_create,
    validate_payroll_update
)

__all__ = [
    # Employee schemas
    'EmployeeBase',
    'EmployeeCreate',
    'EmployeeUpdate',
    'EmployeeResponse',
    'EmployeeListItem',
    'validate_employee_create',
    'validate_employee_update',
    # Payroll schemas
    'PayrollStatus',
    'PayrollBase',
    'PayrollCreate',
    'PayrollUpdate',
    'PayrollResponse',
    'PayrollSummary',
    'validate_payroll_create',
    'validate_payroll_update',
]
