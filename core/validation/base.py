# -*- coding: utf-8 -*-
"""
Base Validation
===============
Base schema class and validation utilities.

Features:
  - Arabic error messages
  - Custom validators
  - Utility functions
"""

from typing import Any, Dict, List, Optional, Type, TypeVar
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator, ValidationError as PydanticValidationError


# Re-export ValidationError for convenience
ValidationError = PydanticValidationError

# Type variable for generic schema operations
T = TypeVar("T", bound="BaseSchema")


# Arabic error messages mapping
ERROR_MESSAGES_AR = {
    # Required fields
    "missing": "هذا الحقل مطلوب",
    "none_required": "القيمة يجب ألا تكون فارغة",

    # String errors
    "string_too_short": "النص قصير جداً (الحد الأدنى: {min_length} حرف)",
    "string_too_long": "النص طويل جداً (الحد الأقصى: {max_length} حرف)",
    "string_pattern_mismatch": "صيغة غير صحيحة",

    # Number errors
    "greater_than": "القيمة يجب أن تكون أكبر من {gt}",
    "greater_than_equal": "القيمة يجب أن تكون {ge} أو أكبر",
    "less_than": "القيمة يجب أن تكون أقل من {lt}",
    "less_than_equal": "القيمة يجب أن تكون {le} أو أقل",

    # Type errors
    "int_type": "يجب أن يكون رقم صحيح",
    "float_type": "يجب أن يكون رقم",
    "decimal_type": "يجب أن يكون رقم عشري",
    "string_type": "يجب أن يكون نص",
    "bool_type": "يجب أن يكون صح أو خطأ",
    "date_type": "يجب أن يكون تاريخ صحيح",
    "datetime_type": "يجب أن يكون تاريخ ووقت صحيح",

    # Email
    "value_error.email": "بريد إلكتروني غير صحيح",

    # General
    "value_error": "قيمة غير صحيحة",
    "assertion_error": "فشل التحقق",
}


def translate_error(error_type: str, ctx: Optional[Dict] = None) -> str:
    """
    Translate Pydantic error type to Arabic message.

    Args:
        error_type: The Pydantic error type
        ctx: Context dictionary with values like min_length, max_length, etc.

    Returns:
        Arabic error message
    """
    message = ERROR_MESSAGES_AR.get(error_type, f"خطأ في التحقق: {error_type}")

    if ctx:
        try:
            message = message.format(**ctx)
        except (KeyError, ValueError):
            pass

    return message


class BaseSchema(BaseModel):
    """
    Base schema for all Pydantic models.

    Features:
      - Arabic error messages
      - JSON serialization settings
      - Common validation methods
    """

    model_config = ConfigDict(
        # Allow population by field name
        populate_by_name=True,
        # Validate on assignment
        validate_assignment=True,
        # Use enum values
        use_enum_values=True,
        # Arbitrary types allowed (for custom classes)
        arbitrary_types_allowed=True,
        # Strip whitespace from strings
        str_strip_whitespace=True,
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return self.model_dump(exclude_none=True)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return self.model_dump_json(exclude_none=True)

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create instance from dictionary."""
        return cls.model_validate(data)

    @classmethod
    def get_field_names(cls) -> List[str]:
        """Get list of field names."""
        return list(cls.model_fields.keys())

    @classmethod
    def get_required_fields(cls) -> List[str]:
        """Get list of required field names."""
        return [
            name for name, field in cls.model_fields.items()
            if field.is_required()
        ]


def validate_data(
    data: Dict[str, Any],
    schema_class: Type[T],
    raise_on_error: bool = True
) -> tuple[Optional[T], List[Dict[str, str]]]:
    """
    Validate data against a schema.

    Args:
        data: Data to validate
        schema_class: Schema class to validate against
        raise_on_error: Whether to raise exception on validation error

    Returns:
        (validated_instance, errors)
        - If valid: (instance, [])
        - If invalid and raise_on_error=False: (None, error_list)

    Raises:
        ValidationError: If invalid and raise_on_error=True
    """
    try:
        instance = schema_class.model_validate(data)
        return instance, []
    except PydanticValidationError as e:
        errors = get_validation_errors(e)
        if raise_on_error:
            raise
        return None, errors


def get_validation_errors(error: PydanticValidationError) -> List[Dict[str, str]]:
    """
    Extract validation errors with Arabic messages.

    Args:
        error: Pydantic ValidationError

    Returns:
        List of error dictionaries with field, message, and type
    """
    errors = []
    for err in error.errors():
        field = ".".join(str(loc) for loc in err["loc"])
        error_type = err["type"]
        ctx = err.get("ctx", {})

        errors.append({
            "field": field,
            "message": translate_error(error_type, ctx),
            "type": error_type,
        })

    return errors


def format_errors_html(errors: List[Dict[str, str]]) -> str:
    """
    Format validation errors as HTML for display.

    Args:
        errors: List of error dictionaries

    Returns:
        HTML formatted error list
    """
    if not errors:
        return ""

    lines = ["<ul style='color: #ef4444; margin: 0; padding-right: 20px;'>"]
    for err in errors:
        lines.append(f"<li><b>{err['field']}</b>: {err['message']}</li>")
    lines.append("</ul>")

    return "\n".join(lines)


def format_errors_text(errors: List[Dict[str, str]]) -> str:
    """
    Format validation errors as plain text.

    Args:
        errors: List of error dictionaries

    Returns:
        Text formatted error list
    """
    if not errors:
        return ""

    return "\n".join(f"• {err['field']}: {err['message']}" for err in errors)
