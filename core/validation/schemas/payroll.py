"""
Payroll Validation Schemas
===========================
Pydantic models for validating payroll and salary data.

Features:
- Data validation with clear Arabic error messages
- Salary component validation (base, allowances, deductions)
- Date range validation
- Cross-field validation (e.g., net = gross - deductions)

Usage:
    from core.validation.schemas import PayrollCreate, PayrollUpdate

    # Validate new payroll entry
    try:
        payroll = PayrollCreate(
            employee_id=123,
            month=1,
            year=2026,
            basic_salary=Decimal("5000"),
            housing_allowance=Decimal("1250")
        )
        data = payroll.model_dump()
    except ValidationError as e:
        print(e.errors())

    # Validate update
    is_valid, payroll, errors = validate_payroll_create(data_dict)
"""

from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    ConfigDict,
)

from core.logging import app_logger


# Arabic error messages
PAYROLL_ERRORS = {
    "invalid_month": "الشهر يجب أن يكون بين 1 و 12",
    "invalid_year": "السنة يجب أن تكون بين 2000 و 2100",
    "negative_amount": "المبلغ لا يمكن أن يكون سالباً",
    "deductions_exceed": "إجمالي الخصومات يتجاوز إجمالي الراتب",
    "missing_employee": "رقم الموظف مطلوب",
    "invalid_period": "الفترة غير صحيحة",
    "duplicate_period": "يوجد سجل راتب لهذه الفترة مسبقاً",
}


class PayrollStatus(str, Enum):
    """Payroll record status."""
    DRAFT = "مسودة"
    PENDING = "قيد المراجعة"
    APPROVED = "معتمد"
    PAID = "مدفوع"
    CANCELLED = "ملغي"


class PayrollBase(BaseModel):
    """Base payroll schema with common fields."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="ignore"
    )

    employee_id: Optional[int] = Field(
        None,
        gt=0,
        description="رقم الموظف"
    )

    month: Optional[int] = Field(
        None,
        ge=1,
        le=12,
        description="الشهر"
    )

    year: Optional[int] = Field(
        None,
        ge=2000,
        le=2100,
        description="السنة"
    )

    # Salary Components
    basic_salary: Optional[Decimal] = Field(
        None,
        ge=0,
        description="الراتب الأساسي"
    )

    housing_allowance: Optional[Decimal] = Field(
        Decimal("0"),
        ge=0,
        description="بدل السكن"
    )

    transportation_allowance: Optional[Decimal] = Field(
        Decimal("0"),
        ge=0,
        description="بدل النقل"
    )

    food_allowance: Optional[Decimal] = Field(
        Decimal("0"),
        ge=0,
        description="بدل الطعام"
    )

    other_allowances: Optional[Decimal] = Field(
        Decimal("0"),
        ge=0,
        description="بدلات أخرى"
    )

    overtime_amount: Optional[Decimal] = Field(
        Decimal("0"),
        ge=0,
        description="مبلغ الإضافي"
    )

    overtime_hours: Optional[Decimal] = Field(
        Decimal("0"),
        ge=0,
        description="ساعات العمل الإضافي"
    )

    # Deductions
    social_insurance: Optional[Decimal] = Field(
        Decimal("0"),
        ge=0,
        description="التأمينات الاجتماعية"
    )

    tax_deduction: Optional[Decimal] = Field(
        Decimal("0"),
        ge=0,
        description="ضريبة الدخل"
    )

    absence_deduction: Optional[Decimal] = Field(
        Decimal("0"),
        ge=0,
        description="خصم الغياب"
    )

    loan_deduction: Optional[Decimal] = Field(
        Decimal("0"),
        ge=0,
        description="خصم السلفة"
    )

    other_deductions: Optional[Decimal] = Field(
        Decimal("0"),
        ge=0,
        description="خصومات أخرى"
    )

    # Calculated fields
    gross_salary: Optional[Decimal] = Field(
        None,
        ge=0,
        description="إجمالي الراتب"
    )

    total_deductions: Optional[Decimal] = Field(
        None,
        ge=0,
        description="إجمالي الخصومات"
    )

    net_salary: Optional[Decimal] = Field(
        None,
        description="صافي الراتب"
    )

    # Metadata
    status: Optional[PayrollStatus] = Field(
        PayrollStatus.DRAFT,
        description="حالة السجل"
    )

    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="ملاحظات"
    )

    payment_date: Optional[date] = Field(
        None,
        description="تاريخ الصرف"
    )

    @field_validator('month')
    @classmethod
    def validate_month(cls, v: Optional[int]) -> Optional[int]:
        """Validate month is between 1 and 12."""
        if v is not None and not (1 <= v <= 12):
            raise ValueError(PAYROLL_ERRORS["invalid_month"])
        return v

    @field_validator('year')
    @classmethod
    def validate_year(cls, v: Optional[int]) -> Optional[int]:
        """Validate year is reasonable."""
        if v is not None and not (2000 <= v <= 2100):
            raise ValueError(PAYROLL_ERRORS["invalid_year"])
        return v

    @model_validator(mode='after')
    def calculate_totals(self):
        """Calculate gross, deductions, and net salary."""
        if self.basic_salary is not None:
            # Calculate gross
            gross = (
                self.basic_salary
                + (self.housing_allowance or Decimal("0"))
                + (self.transportation_allowance or Decimal("0"))
                + (self.food_allowance or Decimal("0"))
                + (self.other_allowances or Decimal("0"))
                + (self.overtime_amount or Decimal("0"))
            )
            self.gross_salary = gross

            # Calculate total deductions
            deductions = (
                (self.social_insurance or Decimal("0"))
                + (self.tax_deduction or Decimal("0"))
                + (self.absence_deduction or Decimal("0"))
                + (self.loan_deduction or Decimal("0"))
                + (self.other_deductions or Decimal("0"))
            )
            self.total_deductions = deductions

            # Calculate net salary
            self.net_salary = gross - deductions

        return self


class PayrollCreate(PayrollBase):
    """Schema for creating new payroll record."""

    employee_id: int = Field(
        ...,
        gt=0,
        description="رقم الموظف (مطلوب)"
    )

    month: int = Field(
        ...,
        ge=1,
        le=12,
        description="الشهر (مطلوب)"
    )

    year: int = Field(
        ...,
        ge=2000,
        le=2100,
        description="السنة (مطلوب)"
    )

    basic_salary: Decimal = Field(
        ...,
        ge=0,
        description="الراتب الأساسي (مطلوب)"
    )

    @model_validator(mode='after')
    def validate_create(self):
        """Validate required fields and business rules for creation."""
        if self.total_deductions and self.gross_salary:
            if self.total_deductions > self.gross_salary:
                raise ValueError(PAYROLL_ERRORS["deductions_exceed"])
        return self


class PayrollUpdate(PayrollBase):
    """Schema for updating payroll record (all fields optional)."""
    pass


class PayrollResponse(PayrollBase):
    """Schema for payroll response (includes ID and timestamps)."""

    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Related names (from joins)
    employee_name: Optional[str] = None
    employee_number: Optional[str] = None
    department_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PayrollSummary(BaseModel):
    """Summary schema for payroll list views."""

    id: int
    employee_id: int
    employee_name: Optional[str] = None
    employee_number: Optional[str] = None
    month: int
    year: int
    gross_salary: Optional[Decimal] = None
    net_salary: Optional[Decimal] = None
    status: Optional[PayrollStatus] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Validation Helper Functions
# ============================================================

def validate_payroll_create(data: dict) -> tuple[bool, Optional[PayrollCreate], List[str]]:
    """
    Validate data for creating payroll record.

    Args:
        data: Payroll data dictionary

    Returns:
        Tuple of (is_valid, validated_model, errors)
    """
    try:
        payroll = PayrollCreate(**data)
        return True, payroll, []
    except Exception as e:
        errors = []
        if hasattr(e, 'errors'):
            for err in e.errors():
                field = err.get('loc', ['unknown'])[0]
                msg = err.get('msg', 'خطأ في التحقق')
                errors.append(f"{field}: {msg}")
        else:
            errors.append(str(e))

        app_logger.warning(f"Payroll validation failed: {errors}")
        return False, None, errors


def validate_payroll_update(data: dict) -> tuple[bool, Optional[PayrollUpdate], List[str]]:
    """
    Validate data for updating payroll record.

    Args:
        data: Payroll data dictionary

    Returns:
        Tuple of (is_valid, validated_model, errors)
    """
    try:
        payroll = PayrollUpdate(**data)
        return True, payroll, []
    except Exception as e:
        errors = []
        if hasattr(e, 'errors'):
            for err in e.errors():
                field = err.get('loc', ['unknown'])[0]
                msg = err.get('msg', 'خطأ في التحقق')
                errors.append(f"{field}: {msg}")
        else:
            errors.append(str(e))

        app_logger.warning(f"Payroll update validation failed: {errors}")
        return False, None, errors
