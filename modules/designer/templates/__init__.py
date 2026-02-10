# -*- coding: utf-8 -*-
"""
Form Designer Templates
=======================
Template library for the INTEGRA Form Designer.

Provides built-in and user-defined form templates, managed
through the thread-safe singleton :func:`get_template_manager`.

Usage::

    from modules.designer.templates import get_template_manager, TemplateInfo

    tm = get_template_manager()

    # List all available templates
    for info in tm.get_all_templates():
        print(info.name_en, info.category, info.is_builtin)

    # Load full template data
    data = tm.get_template("employee_basic")

    # Save current form as a user template
    tm.save_as_template(form_data, name="My Form", description="...", category="employee")

    # Delete a user template
    tm.delete_user_template("user_abc123def456")
"""

from modules.designer.templates.template_manager import (
    TemplateInfo,
    TemplateManager,
    get_template_manager,
)

__all__ = [
    "TemplateInfo",
    "TemplateManager",
    "get_template_manager",
]
