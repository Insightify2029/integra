"""
Form Schema Definition v2.0 for INTEGRA Form Designer.

Defines the JSON schema structure for .iform files, including
validation, defaults, and helper functions.

Schema supports:
- Bilingual labels (Arabic/English) with RTL
- Section-based layouts (cards/groups)
- Data binding to database tables
- Validation rules
- Conditional logic (show/hide fields)
- Custom styling overrides
- Action buttons
- Event handlers
"""

from __future__ import annotations

import json
import copy
from typing import Any, Optional

from core.logging import app_logger


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FORM_SCHEMA_VERSION = "2.0"

SUPPORTED_WIDGET_TYPES: tuple[str, ...] = (
    "text_input",
    "text_area",
    "number_input",
    "decimal_input",
    "combo_box",
    "check_box",
    "radio_group",
    "date_picker",
    "time_picker",
    "datetime_picker",
    "button",
    "label",
    "separator",
    "image",
    "group_box",
    "table",
    "file_picker",
    "color_picker",
    "slider",
    "progress",
    "rich_text",
)

SUPPORTED_LAYOUT_MODES: tuple[str, ...] = (
    "smart_grid",
    "absolute",
    "flow",
)

SUPPORTED_VALIDATION_RULES: tuple[str, ...] = (
    "required",
    "min_length",
    "max_length",
    "min_value",
    "max_value",
    "pattern",
    "email",
    "phone",
    "iban",
    "national_id",
    "date_range",
    "unique",
    "custom",
)

SUPPORTED_ACTION_TYPES: tuple[str, ...] = (
    "primary",
    "secondary",
    "danger",
    "success",
)

SUPPORTED_DATA_TYPES: tuple[str, ...] = (
    "string",
    "integer",
    "decimal",
    "boolean",
    "date",
    "time",
    "datetime",
    "text",
)

SUPPORTED_ACTION_ACTIONS: tuple[str, ...] = (
    "save",
    "cancel",
    "custom",
    "navigate",
    "delete",
    "print",
)

SUPPORTED_RULE_ACTIONS: tuple[str, ...] = (
    "hide_field",
    "show_field",
    "hide_section",
    "show_section",
    "enable_field",
    "disable_field",
    "set_value",
    "set_required",
)

SUPPORTED_EVENT_KEYS: tuple[str, ...] = (
    "on_load",
    "on_save",
    "on_validate",
    "on_close",
    "on_field_change",
)

SUPPORTED_COMBO_SOURCE_TYPES: tuple[str, ...] = (
    "query",
    "static",
    "api",
)

SUPPORTED_SAVE_BUTTON_POSITIONS: tuple[str, ...] = (
    "bottom_left",
    "bottom_right",
    "bottom_center",
    "top_right",
)

SUPPORTED_ALIGNMENTS: tuple[str, ...] = (
    "stretch",
    "left",
    "center",
    "right",
)

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_FORM_SETTINGS: dict[str, Any] = {
    "direction": "rtl",
    "layout_mode": "smart_grid",
    "columns": 2,
    "column_gap": 20,
    "row_gap": 15,
    "margins": {
        "top": 20,
        "right": 20,
        "bottom": 20,
        "left": 20,
    },
    "min_width": 600,
    "max_width": 1200,
    "scrollable": True,
    "show_required_indicator": True,
    "save_button_position": "bottom_left",
}

DEFAULT_FIELD_LAYOUT: dict[str, Any] = {
    "row": 0,
    "col": 0,
    "colspan": 1,
    "rowspan": 1,
    "width": None,
    "min_width": None,
    "max_width": None,
    "height": None,
    "alignment": "stretch",
}

DEFAULT_FIELD_PROPERTIES: dict[str, Any] = {
    "readonly": False,
    "enabled": True,
    "visible": True,
    "tooltip_ar": None,
    "tooltip_en": None,
    "icon": None,
    "prefix": None,
    "suffix": None,
    "mask": None,
}

DEFAULT_STYLE_OVERRIDE: dict[str, Any] = {
    "font_size": None,
    "font_weight": None,
    "text_color": None,
    "background": None,
    "border_color": None,
    "border_radius": None,
    "custom_css": None,
}


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

def _validate_field(field: dict[str, Any], section_id: str, errors: list[str]) -> None:
    """Validate a single field definition."""
    field_id = field.get("id")
    if not field_id or not isinstance(field_id, str):
        errors.append(
            f"Section '{section_id}': field missing valid 'id'"
        )
        return

    prefix = f"Section '{section_id}', field '{field_id}'"

    widget_type = field.get("widget_type")
    if widget_type not in SUPPORTED_WIDGET_TYPES:
        errors.append(
            f"{prefix}: unsupported widget_type '{widget_type}'"
        )

    if not field.get("label_ar") and not field.get("label_en"):
        errors.append(f"{prefix}: must have at least label_ar or label_en")

    # Validate layout if present
    layout = field.get("layout")
    if layout:
        alignment = layout.get("alignment")
        if alignment and alignment not in SUPPORTED_ALIGNMENTS:
            errors.append(f"{prefix}: unsupported alignment '{alignment}'")

    # Validate validation rules if present
    validations = field.get("validation", [])
    for rule in validations:
        rule_name = rule.get("rule")
        if rule_name and rule_name not in SUPPORTED_VALIDATION_RULES:
            errors.append(f"{prefix}: unsupported validation rule '{rule_name}'")

    # Validate data_binding if present
    binding = field.get("data_binding")
    if binding:
        # Support both "type" (used in .iform files) and "data_type" (legacy)
        data_type = binding.get("type") or binding.get("data_type")
        if data_type and data_type not in SUPPORTED_DATA_TYPES:
            errors.append(f"{prefix}: unsupported data_type '{data_type}'")

    # Validate combo_source if present
    combo_src = field.get("combo_source")
    if combo_src:
        src_type = combo_src.get("type")
        if src_type and src_type not in SUPPORTED_COMBO_SOURCE_TYPES:
            errors.append(f"{prefix}: unsupported combo_source type '{src_type}'")


def _validate_section(section: dict[str, Any], errors: list[str]) -> None:
    """Validate a single section definition."""
    section_id = section.get("id")
    if not section_id or not isinstance(section_id, str):
        errors.append("Section missing valid 'id'")
        return

    if not section.get("title_ar") and not section.get("title_en"):
        errors.append(f"Section '{section_id}': must have at least title_ar or title_en")

    fields = section.get("fields", [])
    if not isinstance(fields, list):
        errors.append(f"Section '{section_id}': 'fields' must be a list")
        return

    seen_ids: set[str] = set()
    for field in fields:
        fid = field.get("id", "")
        if fid in seen_ids:
            errors.append(
                f"Section '{section_id}': duplicate field id '{fid}'"
            )
        seen_ids.add(fid)
        _validate_field(field, section_id, errors)


def _validate_action(action: dict[str, Any], errors: list[str]) -> None:
    """Validate a single action button definition."""
    action_id = action.get("id")
    if not action_id:
        errors.append("Action missing 'id'")
        return

    action_type = action.get("type")
    if action_type and action_type not in SUPPORTED_ACTION_TYPES:
        errors.append(f"Action '{action_id}': unsupported type '{action_type}'")

    action_action = action.get("action")
    if action_action and action_action not in SUPPORTED_ACTION_ACTIONS:
        errors.append(f"Action '{action_id}': unsupported action '{action_action}'")


def _validate_rule(rule: dict[str, Any], errors: list[str]) -> None:
    """Validate a conditional logic rule."""
    rule_id = rule.get("id")
    if not rule_id:
        errors.append("Rule missing 'id'")
        return

    action = rule.get("action")
    if action and action not in SUPPORTED_RULE_ACTIONS:
        errors.append(f"Rule '{rule_id}': unsupported action '{action}'")

    if not rule.get("trigger_field"):
        errors.append(f"Rule '{rule_id}': missing 'trigger_field'")

    if not rule.get("target"):
        errors.append(f"Rule '{rule_id}': missing 'target'")


def validate_form_schema(form_data: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate a form definition against the v2.0 schema.

    Args:
        form_data: The parsed form dictionary.

    Returns:
        Tuple of (is_valid, error_messages).
    """
    errors: list[str] = []

    if not isinstance(form_data, dict):
        return False, ["Form data must be a dictionary"]

    # Version check
    version = form_data.get("version")
    if version and version != FORM_SCHEMA_VERSION:
        errors.append(f"Unsupported schema version '{version}' (expected {FORM_SCHEMA_VERSION})")

    # Required top-level fields
    if not form_data.get("form_id"):
        errors.append("Missing required field 'form_id'")

    if not form_data.get("form_name_ar") and not form_data.get("form_name_en"):
        errors.append("Must have at least 'form_name_ar' or 'form_name_en'")

    # Settings validation
    settings = form_data.get("settings", {})
    if settings:
        layout_mode = settings.get("layout_mode")
        if layout_mode and layout_mode not in SUPPORTED_LAYOUT_MODES:
            errors.append(f"Unsupported layout_mode '{layout_mode}'")

        direction = settings.get("direction")
        if direction and direction not in ("rtl", "ltr"):
            errors.append(f"Unsupported direction '{direction}'")

        save_pos = settings.get("save_button_position")
        if save_pos and save_pos not in SUPPORTED_SAVE_BUTTON_POSITIONS:
            errors.append(f"Unsupported save_button_position '{save_pos}'")

    # Sections validation
    sections = form_data.get("sections", [])
    if not isinstance(sections, list):
        errors.append("'sections' must be a list")
    else:
        seen_section_ids: set[str] = set()
        for section in sections:
            sid = section.get("id", "")
            if sid in seen_section_ids:
                errors.append(f"Duplicate section id '{sid}'")
            seen_section_ids.add(sid)
            _validate_section(section, errors)

    # Actions validation
    actions = form_data.get("actions", [])
    if isinstance(actions, list):
        for action in actions:
            _validate_action(action, errors)

    # Rules validation
    rules = form_data.get("rules", [])
    if isinstance(rules, list):
        for rule in rules:
            _validate_rule(rule, errors)

    # Events validation
    events = form_data.get("events")
    if events and isinstance(events, dict):
        for event_key in events:
            if event_key not in SUPPORTED_EVENT_KEYS:
                errors.append(f"Unsupported event key '{event_key}'")

    is_valid = len(errors) == 0
    if not is_valid:
        app_logger.warning(
            f"Form schema validation failed with {len(errors)} error(s): "
            f"{'; '.join(errors[:5])}"
        )

    return is_valid, errors


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_default_form(
    form_id: str = "new_form",
    form_name_ar: str = "نموذج جديد",
    form_name_en: str = "New Form",
    target_table: Optional[str] = None,
) -> dict[str, Any]:
    """
    Create a minimal valid form definition with defaults.

    Args:
        form_id: Unique form identifier.
        form_name_ar: Arabic form name.
        form_name_en: English form name.
        target_table: Optional database table name.

    Returns:
        A dictionary conforming to the v2.0 schema.
    """
    return {
        "version": FORM_SCHEMA_VERSION,
        "form_id": form_id,
        "form_name_ar": form_name_ar,
        "form_name_en": form_name_en,
        "target_table": target_table,
        "settings": copy.deepcopy(DEFAULT_FORM_SETTINGS),
        "sections": [],
        "actions": [],
        "rules": [],
        "events": {
            "on_load": None,
            "on_save": None,
            "on_validate": None,
            "on_close": None,
            "on_field_change": {},
        },
    }


def load_form_file(file_path: str) -> tuple[Optional[dict[str, Any]], str]:
    """
    Load and parse a .iform JSON file.

    Args:
        file_path: Path to the .iform file.

    Returns:
        Tuple of (form_data, error_message).
        On success form_data is a dict and error_message is empty.
        On failure form_data is None and error_message describes the issue.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        msg = f"Form file not found: {file_path}"
        app_logger.error(msg)
        return None, msg
    except json.JSONDecodeError as exc:
        msg = f"Invalid JSON in form file '{file_path}': {exc}"
        app_logger.error(msg)
        return None, msg
    except OSError as exc:
        msg = f"Error reading form file '{file_path}': {exc}"
        app_logger.error(msg)
        return None, msg

    is_valid, errors = validate_form_schema(data)
    if not is_valid:
        msg = f"Schema validation failed for '{file_path}': {'; '.join(errors)}"
        app_logger.error(msg)
        return None, msg

    return data, ""


def save_form_file(file_path: str, form_data: dict[str, Any]) -> tuple[bool, str]:
    """
    Save a form definition to a .iform JSON file.

    Args:
        file_path: Destination file path.
        form_data: Form definition dictionary.

    Returns:
        Tuple of (success, error_message).
    """
    is_valid, errors = validate_form_schema(form_data)
    if not is_valid:
        msg = f"Cannot save invalid form: {'; '.join(errors)}"
        app_logger.error(msg)
        return False, msg

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(form_data, f, ensure_ascii=False, indent=2)
    except OSError as exc:
        msg = f"Error writing form file '{file_path}': {exc}"
        app_logger.error(msg)
        return False, msg

    app_logger.info(f"Form saved to '{file_path}'")
    return True, ""


def merge_with_defaults(
    field_def: dict[str, Any],
) -> dict[str, Any]:
    """
    Merge a field definition with defaults so missing keys get
    default values. Returns a new dict (does not mutate input).
    """
    result = copy.deepcopy(field_def)

    # Merge layout defaults
    layout = result.get("layout", {})
    for key, default in DEFAULT_FIELD_LAYOUT.items():
        layout.setdefault(key, default)
    result["layout"] = layout

    # Merge properties defaults
    props = result.get("properties", {})
    for key, default in DEFAULT_FIELD_PROPERTIES.items():
        props.setdefault(key, default)
    result["properties"] = props

    # Merge style_override defaults
    style = result.get("style_override", {})
    for key, default in DEFAULT_STYLE_OVERRIDE.items():
        style.setdefault(key, default)
    result["style_override"] = style

    # Ensure lists exist
    result.setdefault("validation", [])
    result.setdefault("data_binding", None)
    result.setdefault("combo_source", None)

    return result
