# -*- coding: utf-8 -*-
"""
BI Template Manager
===================
Manages Power BI template files (.pbit) for INTEGRA.

This module provides:
- Template discovery and registration
- Template metadata management
- Template opening and launching

Author: Mohamed
Version: 1.0.0
Date: February 2026
"""

import os
import subprocess
import platform
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum

from core.logging import app_logger


class TemplateCategory(Enum):
    """Categories for BI templates."""
    HR = "hr"
    FINANCE = "finance"
    OPERATIONS = "operations"
    EXECUTIVE = "executive"
    CUSTOM = "custom"


@dataclass
class BITemplate:
    """Represents a Power BI template."""
    id: str
    name_ar: str
    name_en: str
    description: str
    file_name: str
    category: TemplateCategory
    icon: str = "chart-bar"
    views_used: List[str] = field(default_factory=list)
    preview_image: str = ""
    version: str = "1.0"

    @property
    def exists(self) -> bool:
        """Check if template file exists."""
        from .connection_config import BI_TEMPLATES_CONFIG
        templates_path = Path(BI_TEMPLATES_CONFIG["templates_path"])
        return (templates_path / self.file_name).exists()


# =============================================================================
# Built-in Templates
# =============================================================================

BUILTIN_TEMPLATES = [
    BITemplate(
        id="employees_dashboard",
        name_ar="لوحة تحكم الموظفين",
        name_en="Employees Dashboard",
        description="Comprehensive employee analytics including headcount, demographics, and tenure analysis",
        file_name="employees_dashboard.pbit",
        category=TemplateCategory.HR,
        icon="users",
        views_used=["employees_summary", "department_stats", "nationality_distribution"],
        version="1.0"
    ),
    BITemplate(
        id="payroll_analysis",
        name_ar="تحليل الرواتب",
        name_en="Payroll Analysis",
        description="Salary trends, distributions, and departmental payroll insights",
        file_name="payroll_analysis.pbit",
        category=TemplateCategory.FINANCE,
        icon="dollar-sign",
        views_used=["payroll_analysis", "department_stats", "job_title_analysis"],
        version="1.0"
    ),
    BITemplate(
        id="department_overview",
        name_ar="نظرة عامة الأقسام",
        name_en="Department Overview",
        description="Department-level metrics, headcount, and performance indicators",
        file_name="department_overview.pbit",
        category=TemplateCategory.OPERATIONS,
        icon="building",
        views_used=["department_stats", "employees_summary"],
        version="1.0"
    ),
    BITemplate(
        id="executive_summary",
        name_ar="ملخص تنفيذي",
        name_en="Executive Summary",
        description="High-level KPIs and trends for leadership",
        file_name="executive_summary.pbit",
        category=TemplateCategory.EXECUTIVE,
        icon="chart-line",
        views_used=["company_summary", "monthly_trends", "payroll_analysis"],
        version="1.0"
    ),
    BITemplate(
        id="hiring_trends",
        name_ar="اتجاهات التوظيف",
        name_en="Hiring Trends",
        description="Monthly hiring patterns, turnover rates, and workforce growth",
        file_name="hiring_trends.pbit",
        category=TemplateCategory.HR,
        icon="user-plus",
        views_used=["monthly_trends", "employees_summary"],
        version="1.0"
    )
]


class BITemplateManager:
    """
    Manages Power BI templates for INTEGRA.

    Provides template discovery, metadata access,
    and template launching capabilities.
    """

    def __init__(self):
        """Initialize the template manager."""
        from .connection_config import BI_TEMPLATES_CONFIG

        self._templates_path = Path(BI_TEMPLATES_CONFIG["templates_path"])
        self._templates: Dict[str, BITemplate] = {}
        self._custom_templates: List[BITemplate] = []

        # Register built-in templates
        for template in BUILTIN_TEMPLATES:
            self._templates[template.id] = template

        # Ensure templates directory exists
        self._templates_path.mkdir(parents=True, exist_ok=True)

    @property
    def templates_path(self) -> Path:
        """Get the templates directory path."""
        return self._templates_path

    def get_all_templates(self) -> List[BITemplate]:
        """Get all registered templates."""
        return list(self._templates.values())

    def get_template(self, template_id: str) -> Optional[BITemplate]:
        """Get a specific template by ID."""
        return self._templates.get(template_id)

    def get_templates_by_category(self, category: TemplateCategory) -> List[BITemplate]:
        """Get templates filtered by category."""
        return [t for t in self._templates.values() if t.category == category]

    def get_available_templates(self) -> List[BITemplate]:
        """Get only templates that exist on disk."""
        return [t for t in self._templates.values() if t.exists]

    def get_missing_templates(self) -> List[BITemplate]:
        """Get templates that are registered but not found on disk."""
        return [t for t in self._templates.values() if not t.exists]

    def register_template(self, template: BITemplate) -> bool:
        """
        Register a custom template.

        Args:
            template: BITemplate to register

        Returns:
            True if registration was successful
        """
        if template.id in self._templates:
            app_logger.warning(f"Template {template.id} already registered")
            return False

        self._templates[template.id] = template
        self._custom_templates.append(template)
        app_logger.info(f"Registered custom template: {template.id}")
        return True

    def unregister_template(self, template_id: str) -> bool:
        """Remove a custom template registration."""
        if template_id not in self._templates:
            return False

        template = self._templates[template_id]
        if template not in self._custom_templates:
            app_logger.warning(f"Cannot unregister built-in template: {template_id}")
            return False

        del self._templates[template_id]
        self._custom_templates.remove(template)
        return True

    def get_template_path(self, template_id: str) -> Optional[Path]:
        """Get the full path to a template file."""
        template = self.get_template(template_id)
        if not template:
            return None
        return self._templates_path / template.file_name

    def open_template(self, template_id: str) -> bool:
        """
        Open a template in Power BI Desktop.

        Args:
            template_id: ID of the template to open

        Returns:
            True if template was opened successfully
        """
        template = self.get_template(template_id)
        if not template:
            app_logger.error(f"Template not found: {template_id}")
            return False

        template_path = self._templates_path / template.file_name

        if not template_path.exists():
            app_logger.error(f"Template file not found: {template_path}")
            return False

        return self._launch_file(template_path)

    def open_template_file(self, file_path: str) -> bool:
        """
        Open a template file directly.

        Args:
            file_path: Path to the .pbit or .pbix file

        Returns:
            True if file was opened successfully
        """
        path = Path(file_path)
        if not path.exists():
            app_logger.error(f"File not found: {file_path}")
            return False

        return self._launch_file(path)

    def _launch_file(self, file_path: Path) -> bool:
        """Launch a file with the system's default application."""
        try:
            system = platform.system()

            if system == "Windows":
                os.startfile(str(file_path))
            elif system == "Darwin":  # macOS
                subprocess.run(["open", str(file_path)], check=True)
            else:  # Linux
                subprocess.run(["xdg-open", str(file_path)], check=True)

            app_logger.info(f"Opened template: {file_path.name}")
            return True

        except Exception as e:
            app_logger.error(f"Failed to open template: {e}")
            return False

    def create_template_placeholder(self, template_id: str) -> bool:
        """
        Create a placeholder file for a template.

        This creates a text file with setup instructions
        since actual .pbit files need Power BI Desktop.

        Args:
            template_id: ID of the template

        Returns:
            True if placeholder was created
        """
        template = self.get_template(template_id)
        if not template:
            return False

        # Create readme file instead of .pbit
        readme_path = self._templates_path / f"{template.id}_README.txt"

        content = f"""
Power BI Template: {template.name_en}
=====================================
Arabic Name: {template.name_ar}
Category: {template.category.value}
Description: {template.description}

Required Views:
{chr(10).join(f'  - bi_views.{v}' for v in template.views_used)}

Setup Instructions:
1. Open Power BI Desktop
2. Click "Get Data" > "PostgreSQL database"
3. Enter connection details:
   - Server: localhost
   - Database: integra
4. Select the required views from bi_views schema
5. Build your visualizations
6. Save as {template.file_name}

Connection String:
Server=localhost;Port=5432;Database=integra

For more information, see docs/power_bi_setup.md
"""

        try:
            readme_path.write_text(content, encoding='utf-8')
            app_logger.info(f"Created template placeholder: {readme_path.name}")
            return True
        except Exception as e:
            app_logger.error(f"Failed to create placeholder: {e}")
            return False

    def create_all_placeholders(self) -> int:
        """Create placeholders for all missing templates."""
        count = 0
        for template in self.get_missing_templates():
            if self.create_template_placeholder(template.id):
                count += 1
        return count

    def scan_custom_templates(self) -> List[BITemplate]:
        """
        Scan templates directory for unregistered .pbit files.

        Returns:
            List of discovered templates
        """
        discovered = []

        for file_path in self._templates_path.glob("*.pbit"):
            # Check if already registered
            file_name = file_path.name
            already_registered = any(
                t.file_name == file_name for t in self._templates.values()
            )

            if not already_registered:
                # Create template entry
                template = BITemplate(
                    id=file_path.stem,
                    name_ar=file_path.stem,
                    name_en=file_path.stem.replace("_", " ").title(),
                    description="Custom template",
                    file_name=file_name,
                    category=TemplateCategory.CUSTOM,
                    icon="file"
                )
                discovered.append(template)

        return discovered

    def auto_register_custom_templates(self) -> int:
        """Scan and register any custom templates found."""
        discovered = self.scan_custom_templates()
        count = 0

        for template in discovered:
            if self.register_template(template):
                count += 1

        if count > 0:
            app_logger.info(f"Auto-registered {count} custom templates")

        return count


# =============================================================================
# Singleton Instance
# =============================================================================

_template_manager_instance: Optional[BITemplateManager] = None
_template_manager_lock = __import__('threading').Lock()


def get_template_manager() -> BITemplateManager:
    """Get the singleton BITemplateManager instance (thread-safe)."""
    global _template_manager_instance
    if _template_manager_instance is None:
        with _template_manager_lock:
            if _template_manager_instance is None:
                _template_manager_instance = BITemplateManager()
    return _template_manager_instance
