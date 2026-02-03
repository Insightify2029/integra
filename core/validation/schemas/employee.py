"""
Employee Validation Schemas
===========================
Pydantic models for validating employee data.

Features:
- Data validation with clear Arabic error messages
- Type coercion and normalization
- Optional/required field handling
- Custom validators

Usage:
    from core.validation.schemas import EmployeeCreate, EmployeeUpdate

    # Validate new employee
    try:
        employee = EmployeeCreate(
            name_ar="محمد أحمد",
            employee_number="EMP001",
            salary=5000
        )
        data = employee.model_dump()
    except ValidationError as e:
        print(e.errors())

    # Validate update
    update = EmployeeUpdate(salary=6000)
"""

from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
import re

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    ConfigDict,
    EmailStr
)

from core.logging import app_logger


# Arabic error messages
ARABIC_ERRORS = {
    "required": "هذا الحقل مطلوب",
    "invalid_type": "نوع البيانات غير صحيح",
    "min_length": "الحد الأدنى للطول هو {min_length} حرف",
    "max_length": "الحد الأقصى للطول هو {max_length} حرف",
    "invalid_email": "البريد الإلكتروني غير صحيح",
    "invalid_phone": "رقم الهاتف غير صحيح",
    "invalid_iban": "رقم الحساب البنكي غير صحيح",
    "negative_salary": "الراتب يجب أن يكون أكبر من صفر",
    "future_date": "التاريخ لا يمكن أن يكون في المستقبل",
}


class EmployeeBase(BaseModel):
    """Base employee schema with common fields."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="ignore"
    )

    name_ar: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="الاسم بالعربي"
    )

    name_en: Optional[str] = Field(
        None,
        max_length=100,
        description="الاسم بالإنجليزي"
    )

    employee_number: Optional[str] = Field(
        None,
        max_length=20,
        description="رقم الموظف"
    )

    national_id: Optional[str] = Field(
        None,
        max_length=20,
        description="رقم الهوية"
    )

    phone: Optional[str] = Field(
        None,
        max_length=20,
        description="رقم الهاتف"
    )

    email: Optional[EmailStr] = Field(
        None,
        description="البريد الإلكتروني"
    )

    salary: Optional[Decimal] = Field(
        None,
        ge=0,
        description="الراتب الأساسي"
    )

    hire_date: Optional[date] = Field(
        None,
        description="تاريخ التعيين"
    )

    birth_date: Optional[date] = Field(
        None,
        description="تاريخ الميلاد"
    )

    iban: Optional[str] = Field(
        None,
        max_length=34,
        description="رقم الحساب البنكي (IBAN)"
    )

    address: Optional[str] = Field(
        None,
        max_length=500,
        description="العنوان"
    )

    notes: Optional[str] = Field(
        None,
        description="ملاحظات"
    )

    # Foreign keys
    company_id: Optional[int] = Field(None, description="الشركة")
    department_id: Optional[int] = Field(None, description="القسم")
    job_title_id: Optional[int] = Field(None, description="المسمى الوظيفي")
    nationality_id: Optional[int] = Field(None, description="الجنسية")
    bank_id: Optional[int] = Field(None, description="البنك")
    status_id: Optional[int] = Field(None, description="الحالة")

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format."""
        if v is None:
            return None

        # Remove spaces and dashes
        cleaned = re.sub(r'[\s\-]', '', v)

        # Check if it's a valid phone (Saudi format or international)
        if not re.match(r'^(\+?966|05|5)?\d{8,9}$', cleaned):
            # Allow if it looks like a phone number
            if not re.match(r'^\+?\d{8,15}$', cleaned):
                raise ValueError(ARABIC_ERRORS["invalid_phone"])

        return cleaned

    @field_validator('iban')
    @classmethod
    def validate_iban(cls, v: Optional[str]) -> Optional[str]:
        """Validate IBAN format."""
        if v is None:
            return None

        # Remove spaces
        cleaned = v.replace(' ', '').upper()

        # Saudi IBAN: SA + 2 check digits + 22 alphanumeric
        if cleaned.startswith('SA'):
            if not re.match(r'^SA\d{2}[A-Z0-9]{22}$', cleaned):
                raise ValueError(ARABIC_ERRORS["invalid_iban"])
        else:
            # Generic IBAN validation (2 letters + 2 digits + up to 30 chars)
            if not re.match(r'^[A-Z]{2}\d{2}[A-Z0-9]{1,30}$', cleaned):
                raise ValueError(ARABIC_ERRORS["invalid_iban"])

        return cleaned

    @field_validator('salary')
    @classmethod
    def validate_salary(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Validate salary is positive."""
        if v is not None and v < 0:
            raise ValueError(ARABIC_ERRORS["negative_salary"])
        return v

    @field_validator('hire_date', 'birth_date')
    @classmethod
    def validate_date_not_future(cls, v: Optional[date]) -> Optional[date]:
        """Validate date is not in future."""
        if v is not None and v > date.today():
            raise ValueError(ARABIC_ERRORS["future_date"])
        return v


class EmployeeCreate(EmployeeBase):
    """Schema for creating new employee."""

    name_ar: str = Field(
        ...,  # Required
        min_length=2,
        max_length=100,
        description="الاسم بالعربي (مطلوب)"
    )

    employee_number: str = Field(
        ...,  # Required
        max_length=20,
        description="رقم الموظف (مطلوب)"
    )

    @model_validator(mode='after')
    def check_required_fields(self):
        """Validate required fields for new employee."""
        if not self.name_ar or len(self.name_ar.strip()) < 2:
            raise ValueError("الاسم بالعربي مطلوب")

        if not self.employee_number:
            raise ValueError("رقم الموظف مطلوب")

        return self


class EmployeeUpdate(EmployeeBase):
    """Schema for updating employee (all fields optional)."""

    # All fields inherited from EmployeeBase are already optional
    pass


class EmployeeResponse(EmployeeBase):
    """Schema for employee response (includes ID and timestamps)."""

    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Related names (from joins)
    company_name: Optional[str] = None
    department_name: Optional[str] = None
    job_title_name: Optional[str] = None
    nationality_name: Optional[str] = None
    bank_name: Optional[str] = None
    status_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class EmployeeListItem(BaseModel):
    """Minimal schema for employee list views."""

    id: int
    name_ar: Optional[str] = None
    employee_number: Optional[str] = None
    department_name: Optional[str] = None
    job_title_name: Optional[str] = None
    salary: Optional[Decimal] = None
    status_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# Validation helper functions

def validate_employee_create(data: dict) -> tuple[bool, Optional[EmployeeCreate], List[str]]:
    """
    Validate data for creating employee.

    Args:
        data: Employee data dictionary

    Returns:
        Tuple of (is_valid, validated_model, errors)
    """
    try:
        employee = EmployeeCreate(**data)
        return True, employee, []
    except Exception as e:
        errors = []
        if hasattr(e, 'errors'):
            for err in e.errors():
                field = err.get('loc', ['unknown'])[0]
                msg = err.get('msg', 'خطأ في التحقق')
                errors.append(f"{field}: {msg}")
        else:
            errors.append(str(e))

        app_logger.warning(f"Employee validation failed: {errors}")
        return False, None, errors


def validate_employee_update(data: dict) -> tuple[bool, Optional[EmployeeUpdate], List[str]]:
    """
    Validate data for updating employee.

    Args:
        data: Employee data dictionary

    Returns:
        Tuple of (is_valid, validated_model, errors)
    """
    try:
        employee = EmployeeUpdate(**data)
        return True, employee, []
    except Exception as e:
        errors = []
        if hasattr(e, 'errors'):
            for err in e.errors():
                field = err.get('loc', ['unknown'])[0]
                msg = err.get('msg', 'خطأ في التحقق')
                errors.append(f"{field}: {msg}")
        else:
            errors.append(str(e))

        app_logger.warning(f"Employee update validation failed: {errors}")
        return False, None, errors
