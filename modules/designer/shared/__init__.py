"""
Shared utilities and definitions for the Form Designer system.

Provides common schema definitions, constants, and utilities
used by both FormBuilder and FormRenderer.
"""

from modules.designer.shared.form_schema import (
    FORM_SCHEMA_VERSION,
    SUPPORTED_WIDGET_TYPES,
    SUPPORTED_LAYOUT_MODES,
    SUPPORTED_VALIDATION_RULES,
    SUPPORTED_ACTION_TYPES,
    SUPPORTED_DATA_TYPES,
    DEFAULT_FORM_SETTINGS,
    DEFAULT_FIELD_LAYOUT,
    DEFAULT_FIELD_PROPERTIES,
    validate_form_schema,
    get_default_form,
)

__all__ = [
    "FORM_SCHEMA_VERSION",
    "SUPPORTED_WIDGET_TYPES",
    "SUPPORTED_LAYOUT_MODES",
    "SUPPORTED_VALIDATION_RULES",
    "SUPPORTED_ACTION_TYPES",
    "SUPPORTED_DATA_TYPES",
    "DEFAULT_FORM_SETTINGS",
    "DEFAULT_FIELD_LAYOUT",
    "DEFAULT_FIELD_PROPERTIES",
    "validate_form_schema",
    "get_default_form",
]
