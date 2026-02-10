"""
Validation Engine for INTEGRA FormRenderer.

Executes validation rules defined in .iform JSON against widget values.

Supports:
- Real-time validation on field change
- Full form validation before save
- Arabic error messages
- Visual error feedback (red borders, error labels)
- Focus on first invalid field with scroll
- All errors collected (doesn't stop at first)

Rules supported:
    required, min_length, max_length, min_value, max_value,
    pattern, email, phone, iban, national_id, date_range,
    unique, custom
"""

from __future__ import annotations

import re
from typing import Any, Callable, Optional

from PyQt5.QtWidgets import QWidget, QLabel, QScrollArea
from PyQt5.QtCore import Qt

from core.logging import app_logger
from core.themes import get_current_palette, get_font, FONT_SIZE_SMALL


class ValidationError:
    """Represents a single validation error."""

    __slots__ = ("field_id", "rule", "message")

    def __init__(self, field_id: str, rule: str, message: str) -> None:
        self.field_id = field_id
        self.rule = rule
        self.message = message

    def __repr__(self) -> str:
        return f"ValidationError({self.field_id!r}, {self.rule!r}, {self.message!r})"


class ValidationEngine:
    """
    Validates form data against the rules defined in field definitions.

    Usage::

        engine = ValidationEngine()
        # Register a unique-check callback (async-safe)
        engine.set_unique_checker(my_async_checker)

        errors = engine.validate_field(field_def, value)
        all_errors = engine.validate_all(fields, values)
    """

    def __init__(self) -> None:
        self._unique_checker: Optional[Callable] = None
        self._custom_validators: dict[str, Callable] = {}
        self._error_labels: dict[str, QLabel] = {}
        self._error_widgets: dict[str, QWidget] = {}

    # -----------------------------------------------------------------------
    # Configuration
    # -----------------------------------------------------------------------

    def set_unique_checker(
        self,
        checker: Callable[[str, str, Any, Optional[int]], bool],
    ) -> None:
        """
        Set a callback for unique validation.

        The checker signature:
            checker(table, column, value, exclude_id) -> bool
            Returns True if value is unique.
        """
        self._unique_checker = checker

    def register_custom_validator(
        self,
        name: str,
        validator: Callable[[Any], tuple[bool, str]],
    ) -> None:
        """
        Register a custom validation function.

        The validator signature:
            validator(value) -> (is_valid, error_message)
        """
        self._custom_validators[name] = validator

    # -----------------------------------------------------------------------
    # Single field validation
    # -----------------------------------------------------------------------

    def validate_field(
        self,
        field_def: dict[str, Any],
        value: Any,
        record_id: Optional[int] = None,
    ) -> list[ValidationError]:
        """
        Validate a single field's value against its rules.

        Args:
            field_def: The field definition containing 'validation' list.
            value: The current value of the field.
            record_id: Current record ID (for unique checks to exclude self).

        Returns:
            List of ValidationError objects (empty if valid).
        """
        field_id = field_def.get("id", "unknown")
        rules = field_def.get("validation", [])
        errors: list[ValidationError] = []

        for rule_def in rules:
            rule_name = rule_def.get("rule", "")
            rule_value = rule_def.get("value")
            message_ar = rule_def.get("message_ar", "")
            message_en = rule_def.get("message_en", "")
            message = message_ar or message_en

            error = self._check_rule(
                field_id, rule_name, rule_value, value, message,
                field_def, record_id,
            )
            if error:
                errors.append(error)

        return errors

    # -----------------------------------------------------------------------
    # Full form validation
    # -----------------------------------------------------------------------

    def validate_all(
        self,
        fields: list[dict[str, Any]],
        values: dict[str, Any],
        record_id: Optional[int] = None,
    ) -> list[ValidationError]:
        """
        Validate all fields in the form.

        Args:
            fields: List of all field definitions.
            values: Dict mapping field_id -> current value.
            record_id: Current record ID for unique checks.

        Returns:
            List of all ValidationError objects.
        """
        all_errors: list[ValidationError] = []

        for field_def in fields:
            field_id = field_def.get("id", "")
            props = field_def.get("properties", {})

            # Skip hidden or disabled fields
            if not props.get("visible", True):
                continue
            if not props.get("enabled", True):
                continue

            value = values.get(field_id)
            errors = self.validate_field(field_def, value, record_id)
            all_errors.extend(errors)

        return all_errors

    # -----------------------------------------------------------------------
    # Visual feedback
    # -----------------------------------------------------------------------

    def show_field_error(
        self,
        field_id: str,
        widget: QWidget,
        error_message: str,
        error_container: Optional[QWidget] = None,
    ) -> None:
        """
        Show error styling on a widget and display error message below it.

        Args:
            field_id: The field identifier.
            widget: The input widget to highlight.
            error_message: The error text to show.
            error_container: Optional parent for the error label.
        """
        palette = get_current_palette()
        danger = palette.get("danger", "#ef4444")

        # Red border on widget
        widget.setStyleSheet(
            widget.styleSheet() + f"\nborder: 1px solid {danger};"
        )
        self._error_widgets[field_id] = widget

        # Error label
        if error_container:
            label = self._error_labels.get(field_id)
            if not label:
                label = QLabel(error_container)
                label.setFont(get_font(size=FONT_SIZE_SMALL))
                label.setStyleSheet(f"color: {danger}; padding: 2px 0;")
                label.setWordWrap(True)
                self._error_labels[field_id] = label

            label.setText(error_message)
            label.setVisible(True)

    def clear_field_error(self, field_id: str) -> None:
        """Remove error styling and message from a field."""
        widget = self._error_widgets.pop(field_id, None)
        if widget:
            # Remove only the border override (keep other styles)
            current = widget.styleSheet()
            current = re.sub(r"border:\s*1px\s+solid\s+#[a-fA-F0-9]+;", "", current)
            widget.setStyleSheet(current.strip())

        label = self._error_labels.get(field_id)
        if label:
            label.setVisible(False)
            label.setText("")

    def clear_all_errors(self) -> None:
        """Remove all error indicators from the form."""
        for field_id in list(self._error_widgets.keys()):
            self.clear_field_error(field_id)

    def focus_first_error(
        self,
        errors: list[ValidationError],
        widget_map: dict[str, QWidget],
        scroll_area: Optional[QScrollArea] = None,
    ) -> None:
        """
        Focus on and scroll to the first field with an error.

        Args:
            errors: List of validation errors.
            widget_map: Dict mapping field_id -> widget.
            scroll_area: Optional QScrollArea to scroll into view.
        """
        if not errors:
            return

        first_id = errors[0].field_id
        widget = widget_map.get(first_id)
        if not widget:
            return

        widget.setFocus()

        if scroll_area:
            scroll_area.ensureWidgetVisible(widget, 50, 50)

    # -----------------------------------------------------------------------
    # Rule implementations
    # -----------------------------------------------------------------------

    def _check_rule(
        self,
        field_id: str,
        rule_name: str,
        rule_value: Any,
        value: Any,
        message: str,
        field_def: dict[str, Any],
        record_id: Optional[int],
    ) -> Optional[ValidationError]:
        """Check a single validation rule. Returns an error or None."""
        checker = self._RULE_CHECKERS.get(rule_name)
        if checker:
            return checker(self, field_id, rule_value, value, message, field_def, record_id)

        app_logger.warning(f"Unknown validation rule '{rule_name}' for field '{field_id}'")
        return None

    def _check_required(
        self, field_id: str, rule_value: Any, value: Any,
        message: str, field_def: dict, record_id: Optional[int],
    ) -> Optional[ValidationError]:
        if value is None or (isinstance(value, str) and not value.strip()):
            return ValidationError(
                field_id, "required",
                message or "هذا الحقل مطلوب",
            )
        return None

    def _check_min_length(
        self, field_id: str, rule_value: Any, value: Any,
        message: str, field_def: dict, record_id: Optional[int],
    ) -> Optional[ValidationError]:
        if value is None:
            return None
        text = str(value)
        min_len = int(rule_value) if rule_value is not None else 0
        if len(text) < min_len:
            return ValidationError(
                field_id, "min_length",
                message or f"الحد الأدنى {min_len} حرف",
            )
        return None

    def _check_max_length(
        self, field_id: str, rule_value: Any, value: Any,
        message: str, field_def: dict, record_id: Optional[int],
    ) -> Optional[ValidationError]:
        if value is None:
            return None
        text = str(value)
        max_len = int(rule_value) if rule_value is not None else 9999
        if len(text) > max_len:
            return ValidationError(
                field_id, "max_length",
                message or f"الحد الأقصى {max_len} حرف",
            )
        return None

    def _check_min_value(
        self, field_id: str, rule_value: Any, value: Any,
        message: str, field_def: dict, record_id: Optional[int],
    ) -> Optional[ValidationError]:
        if value is None:
            return None
        try:
            num = float(value)
            min_val = float(rule_value) if rule_value is not None else 0
            if num < min_val:
                return ValidationError(
                    field_id, "min_value",
                    message or f"الحد الأدنى {min_val}",
                )
        except (ValueError, TypeError):
            pass
        return None

    def _check_max_value(
        self, field_id: str, rule_value: Any, value: Any,
        message: str, field_def: dict, record_id: Optional[int],
    ) -> Optional[ValidationError]:
        if value is None:
            return None
        try:
            num = float(value)
            max_val = float(rule_value) if rule_value is not None else 999999999
            if num > max_val:
                return ValidationError(
                    field_id, "max_value",
                    message or f"الحد الأقصى {max_val}",
                )
        except (ValueError, TypeError):
            pass
        return None

    def _check_pattern(
        self, field_id: str, rule_value: Any, value: Any,
        message: str, field_def: dict, record_id: Optional[int],
    ) -> Optional[ValidationError]:
        if value is None or not isinstance(value, str) or not value.strip():
            return None
        if rule_value:
            try:
                if not re.match(str(rule_value), value):
                    return ValidationError(
                        field_id, "pattern",
                        message or "القيمة لا تتطابق مع الصيغة المطلوبة",
                    )
            except re.error:
                app_logger.warning(
                    f"Invalid regex pattern '{rule_value}' for field '{field_id}'"
                )
        return None

    def _check_email(
        self, field_id: str, rule_value: Any, value: Any,
        message: str, field_def: dict, record_id: Optional[int],
    ) -> Optional[ValidationError]:
        if value is None or not isinstance(value, str) or not value.strip():
            return None
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, value):
            return ValidationError(
                field_id, "email",
                message or "صيغة البريد الإلكتروني غير صحيحة",
            )
        return None

    def _check_phone(
        self, field_id: str, rule_value: Any, value: Any,
        message: str, field_def: dict, record_id: Optional[int],
    ) -> Optional[ValidationError]:
        if value is None or not isinstance(value, str) or not value.strip():
            return None
        # Accept digits, +, -, spaces, parens
        phone_pattern = r"^[\d\s\+\-\(\)]{7,20}$"
        if not re.match(phone_pattern, value):
            return ValidationError(
                field_id, "phone",
                message or "صيغة رقم الهاتف غير صحيحة",
            )
        return None

    def _check_iban(
        self, field_id: str, rule_value: Any, value: Any,
        message: str, field_def: dict, record_id: Optional[int],
    ) -> Optional[ValidationError]:
        if value is None or not isinstance(value, str) or not value.strip():
            return None
        # Basic IBAN: 2 letters + 2 digits + up to 30 alphanumeric
        iban_pattern = r"^[A-Z]{2}\d{2}[A-Z0-9]{4,30}$"
        clean = value.replace(" ", "").upper()
        if not re.match(iban_pattern, clean):
            return ValidationError(
                field_id, "iban",
                message or "صيغة IBAN غير صحيحة",
            )
        return None

    def _check_national_id(
        self, field_id: str, rule_value: Any, value: Any,
        message: str, field_def: dict, record_id: Optional[int],
    ) -> Optional[ValidationError]:
        if value is None or not isinstance(value, str) or not value.strip():
            return None
        # Egyptian national ID: 14 digits
        if not re.match(r"^\d{14}$", value):
            return ValidationError(
                field_id, "national_id",
                message or "الرقم القومي يجب أن يكون 14 رقم",
            )
        return None

    def _check_date_range(
        self, field_id: str, rule_value: Any, value: Any,
        message: str, field_def: dict, record_id: Optional[int],
    ) -> Optional[ValidationError]:
        if value is None or not isinstance(value, str) or not value.strip():
            return None
        if isinstance(rule_value, dict):
            from datetime import date as dt_date

            try:
                val_date = dt_date.fromisoformat(value)
            except (ValueError, TypeError):
                return ValidationError(
                    field_id, "date_range",
                    message or "صيغة التاريخ غير صحيحة",
                )

            min_date_str = rule_value.get("min")
            max_date_str = rule_value.get("max")

            if min_date_str:
                try:
                    min_date = dt_date.fromisoformat(min_date_str)
                    if val_date < min_date:
                        return ValidationError(
                            field_id, "date_range",
                            message or f"التاريخ يجب أن يكون بعد {min_date_str}",
                        )
                except ValueError:
                    pass

            if max_date_str:
                try:
                    max_date = dt_date.fromisoformat(max_date_str)
                    if val_date > max_date:
                        return ValidationError(
                            field_id, "date_range",
                            message or f"التاريخ يجب أن يكون قبل {max_date_str}",
                        )
                except ValueError:
                    pass

        return None

    def _check_unique(
        self, field_id: str, rule_value: Any, value: Any,
        message: str, field_def: dict, record_id: Optional[int],
    ) -> Optional[ValidationError]:
        if value is None or (isinstance(value, str) and not value.strip()):
            return None

        if not self._unique_checker:
            app_logger.warning(
                f"Unique validation requested for '{field_id}' but no checker set"
            )
            return None

        binding = field_def.get("data_binding", {})
        if not binding:
            return None

        table = binding.get("table", "")
        column = binding.get("column", "")

        if not table or not column:
            return None

        try:
            is_unique = self._unique_checker(table, column, value, record_id)
            if not is_unique:
                return ValidationError(
                    field_id, "unique",
                    message or "هذه القيمة موجودة مسبقاً",
                )
        except Exception:
            app_logger.error(
                f"Error checking uniqueness for field '{field_id}'",
                exc_info=True,
            )

        return None

    def _check_custom(
        self, field_id: str, rule_value: Any, value: Any,
        message: str, field_def: dict, record_id: Optional[int],
    ) -> Optional[ValidationError]:
        validator_name = str(rule_value) if rule_value else ""
        validator = self._custom_validators.get(validator_name)
        if not validator:
            app_logger.warning(
                f"Custom validator '{validator_name}' not registered for field '{field_id}'"
            )
            return None

        try:
            is_valid, err_msg = validator(value)
            if not is_valid:
                return ValidationError(
                    field_id, "custom",
                    err_msg or message or "قيمة غير صالحة",
                )
        except Exception:
            app_logger.error(
                f"Error in custom validator '{validator_name}' for field '{field_id}'",
                exc_info=True,
            )

        return None

    # -----------------------------------------------------------------------
    # Rule checker registry
    # -----------------------------------------------------------------------

    _RULE_CHECKERS: dict[str, Callable] = {
        "required": _check_required,
        "min_length": _check_min_length,
        "max_length": _check_max_length,
        "min_value": _check_min_value,
        "max_value": _check_max_value,
        "pattern": _check_pattern,
        "email": _check_email,
        "phone": _check_phone,
        "iban": _check_iban,
        "national_id": _check_national_id,
        "date_range": _check_date_range,
        "unique": _check_unique,
        "custom": _check_custom,
    }
