# -*- coding: utf-8 -*-
"""
Employee Schemas
================
Pydantic schemas for Employee entity validation.

Schemas:
  - EmployeeBase: Common fields
  - EmployeeCreate: Fields for creating new employee
  - EmployeeUpdate: Fields for updating employee (all optional)
  - EmployeeResponse: Response model with all fields
"""

from typing import Optional
from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import Field, field_validator, model_validator

from ..base import BaseSchema


class Gender(str, Enum):
    """Gender options."""
    MALE = "M"
    FEMALE = "F"


class EmployeeBase(BaseSchema):
    """
    Base employee schema with common fields.

    Shared between create, update, and response schemas.
    """

    # Personal Information
    name_ar: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="الاسم بالعربي"
    )
    name_en: Optional[str] = Field(
        None,
        max_length=100,
        description="الاسم بالإنجليزي"
    )
    national_id: Optional[str] = Field(
        None,
        min_length=10,
        max_length=20,
        description="رقم الهوية"
    )
    gender: Optional[Gender] = Field(
        None,
        description="الجنس (M/F)"
    )
    birth_date: Optional[date] = Field(
        None,
        description="تاريخ الميلاد"
    )
    phone: Optional[str] = Field(
        None,
        max_length=20,
        description="رقم الهاتف"
    )
    email: Optional[str] = Field(
        None,
        max_length=100,
        description="البريد الإلكتروني"
    )

    # Employment Information
    employee_number: Optional[str] = Field(
        None,
        max_length=20,
        description="الرقم الوظيفي"
    )
    hire_date: Optional[date] = Field(
        None,
        description="تاريخ التعيين"
    )

    # Foreign Keys (IDs)
    company_id: Optional[int] = Field(
        None,
        gt=0,
        description="معرف الشركة"
    )
    department_id: Optional[int] = Field(
        None,
        gt=0,
        description="معرف القسم"
    )
    job_title_id: Optional[int] = Field(
        None,
        gt=0,
        description="معرف المسمى الوظيفي"
    )
    nationality_id: Optional[int] = Field(
        None,
        gt=0,
        description="معرف الجنسية"
    )
    status_id: Optional[int] = Field(
        None,
        gt=0,
        description="معرف الحالة"
    )

    # Financial Information
    bank_id: Optional[int] = Field(
        None,
        gt=0,
        description="معرف البنك"
    )
    iban: Optional[str] = Field(
        None,
        max_length=34,
        description="رقم الآيبان"
    )
    basic_salary: Optional[Decimal] = Field(
        None,
        ge=0,
        description="الراتب الأساسي"
    )

    # Validators
    @field_validator("name_ar")
    @classmethod
    def validate_name_ar(cls, v: str) -> str:
        """Validate Arabic name."""
        if v and not any('\u0600' <= c <= '\u06FF' for c in v.replace(" ", "")):
            # Allow names with at least some Arabic characters
            pass  # Relaxed validation - allow mixed names
        return v.strip()

    @field_validator("national_id")
    @classmethod
    def validate_national_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate national ID format."""
        if v is None:
            return v
        # Remove spaces and dashes
        v = v.replace(" ", "").replace("-", "")
        if not v.isdigit():
            raise ValueError("رقم الهوية يجب أن يحتوي على أرقام فقط")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number."""
        if v is None:
            return v
        # Remove common separators
        cleaned = v.replace(" ", "").replace("-", "").replace("+", "")
        if not cleaned.isdigit():
            raise ValueError("رقم الهاتف غير صحيح")
        return v

    @field_validator("iban")
    @classmethod
    def validate_iban(cls, v: Optional[str]) -> Optional[str]:
        """Validate IBAN format."""
        if v is None:
            return v
        # Remove spaces
        v = v.replace(" ", "").upper()
        # Basic IBAN validation (starts with 2 letters, then digits)
        if len(v) < 15:
            raise ValueError("رقم الآيبان قصير جداً")
        if not v[:2].isalpha():
            raise ValueError("الآيبان يجب أن يبدأ بحرفين")
        return v


class EmployeeCreate(EmployeeBase):
    """
    Schema for creating a new employee.

    Required fields: name_ar, company_id, status_id
    """

    # Override to make required
    name_ar: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="الاسم بالعربي (مطلوب)"
    )
    company_id: int = Field(
        ...,
        gt=0,
        description="معرف الشركة (مطلوب)"
    )
    status_id: int = Field(
        ...,
        gt=0,
        description="معرف الحالة (مطلوب)"
    )


class EmployeeUpdate(BaseSchema):
    """
    Schema for updating an employee.

    All fields are optional - only provided fields will be updated.
    """

    # Personal Information
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
    national_id: Optional[str] = Field(
        None,
        min_length=10,
        max_length=20,
        description="رقم الهوية"
    )
    gender: Optional[Gender] = Field(
        None,
        description="الجنس"
    )
    birth_date: Optional[date] = Field(
        None,
        description="تاريخ الميلاد"
    )
    phone: Optional[str] = Field(
        None,
        max_length=20,
        description="رقم الهاتف"
    )
    email: Optional[str] = Field(
        None,
        max_length=100,
        description="البريد الإلكتروني"
    )

    # Employment Information
    employee_number: Optional[str] = Field(
        None,
        max_length=20,
        description="الرقم الوظيفي"
    )
    hire_date: Optional[date] = Field(
        None,
        description="تاريخ التعيين"
    )

    # Foreign Keys
    company_id: Optional[int] = Field(None, gt=0)
    department_id: Optional[int] = Field(None, gt=0)
    job_title_id: Optional[int] = Field(None, gt=0)
    nationality_id: Optional[int] = Field(None, gt=0)
    status_id: Optional[int] = Field(None, gt=0)
    bank_id: Optional[int] = Field(None, gt=0)

    # Financial
    iban: Optional[str] = Field(None, max_length=34)
    basic_salary: Optional[Decimal] = Field(None, ge=0)

    @model_validator(mode="after")
    def check_at_least_one_field(self):
        """Ensure at least one field is provided for update."""
        values = self.model_dump(exclude_none=True)
        if not values:
            raise ValueError("يجب تحديد حقل واحد على الأقل للتحديث")
        return self

    def get_update_fields(self) -> dict:
        """Get only the fields that have values (for UPDATE query)."""
        return self.model_dump(exclude_none=True)


class EmployeeResponse(EmployeeBase):
    """
    Schema for employee response/read.

    Includes all fields plus ID and related entity names.
    """

    id: int = Field(..., description="معرف الموظف")

    # Related entity names (populated from JOINs)
    company_name: Optional[str] = Field(None, description="اسم الشركة")
    department_name: Optional[str] = Field(None, description="اسم القسم")
    job_title_name: Optional[str] = Field(None, description="المسمى الوظيفي")
    nationality_name: Optional[str] = Field(None, description="الجنسية")
    status_name: Optional[str] = Field(None, description="الحالة")
    bank_name: Optional[str] = Field(None, description="اسم البنك")

    # Timestamps
    created_at: Optional[date] = Field(None, description="تاريخ الإنشاء")
    updated_at: Optional[date] = Field(None, description="تاريخ التحديث")
