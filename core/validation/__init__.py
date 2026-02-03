"""
Validation Module
=================
Pydantic schemas for data validation.

Usage:
    from core.validation import (
        EmployeeCreate,
        EmployeeUpdate,
        validate_employee_create
    )

    # Validate new employee
    is_valid, employee, errors = validate_employee_create(data)
    if is_valid:
        # Use employee.model_dump()
        pass
    else:
        # Handle errors
        pass
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

__all__ = [
    # Employee schemas
    'EmployeeBase',
    'EmployeeCreate',
    'EmployeeUpdate',
    'EmployeeResponse',
    'EmployeeListItem',
    # Validation functions
    'validate_employee_create',
    'validate_employee_update'
]
