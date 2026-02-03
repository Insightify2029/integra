# -*- coding: utf-8 -*-
"""
Validation Module
=================
Pydantic-based validation with Arabic error messages.

Components:
  - BaseSchema: Base class for all schemas
  - Employee schemas: EmployeeCreate, EmployeeUpdate
  - Validation utilities
"""

from .base import (
    BaseSchema,
    ValidationError,
    validate_data,
    get_validation_errors,
)
from .schemas.employee import (
    EmployeeBase,
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
)

__all__ = [
    # Base
    "BaseSchema",
    "ValidationError",
    "validate_data",
    "get_validation_errors",
    # Employee
    "EmployeeBase",
    "EmployeeCreate",
    "EmployeeUpdate",
    "EmployeeResponse",
]
