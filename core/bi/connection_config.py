# -*- coding: utf-8 -*-
"""
BI Connection Configuration
===========================
Configuration settings for Power BI Desktop integration.

This module defines connection parameters, export settings,
and BI Views configuration.

Author: Mohamed
Version: 1.0.0
Date: February 2026
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
BI_SETTINGS_FILE = BASE_DIR / "bi_settings.json"


# =============================================================================
# Connection Configuration
# =============================================================================

BI_CONNECTION_CONFIG = {
    # PostgreSQL connection for Power BI
    "server": "localhost",
    "port": 5432,
    "database": "integra",
    "schema": "public",
    "bi_schema": "bi_views",  # Dedicated schema for BI Views

    # Power BI connection mode
    "mode": "DirectQuery",  # "DirectQuery" or "Import"

    # Connection timeout
    "timeout_seconds": 30,

    # SSL configuration
    "ssl_mode": "prefer",  # "disable", "prefer", "require"
}


# =============================================================================
# Export Configuration
# =============================================================================

BI_EXPORT_CONFIG = {
    # Export directory
    "export_path": str(BASE_DIR / "exports" / "bi_data"),

    # Auto-export settings
    "auto_export_enabled": False,
    "auto_export_time": "06:00",  # Daily at 6 AM
    "auto_export_format": "csv",  # "csv" or "excel"

    # Export retention
    "retention_days": 30,  # Keep exports for 30 days

    # CSV settings
    "csv_encoding": "utf-8-sig",  # For Arabic support in Excel
    "csv_delimiter": ",",

    # Excel settings
    "excel_engine": "openpyxl",
}


# =============================================================================
# BI Views Configuration
# =============================================================================

BI_VIEWS_CONFIG = {
    # Schema for BI Views
    "schema": "bi_views",

    # Available Views
    "views": {
        "employees_summary": {
            "name_ar": "ملخص الموظفين",
            "name_en": "Employees Summary",
            "description": "Comprehensive employee data with joined tables",
            "enabled": True,
            "export_priority": 1
        },
        "department_stats": {
            "name_ar": "إحصائيات الأقسام",
            "name_en": "Department Statistics",
            "description": "Aggregated department statistics",
            "enabled": True,
            "export_priority": 2
        },
        "payroll_analysis": {
            "name_ar": "تحليل الرواتب",
            "name_en": "Payroll Analysis",
            "description": "Salary and payroll analytics",
            "enabled": True,
            "export_priority": 3
        },
        "tasks_productivity": {
            "name_ar": "إنتاجية المهام",
            "name_en": "Tasks Productivity",
            "description": "Task completion and productivity metrics",
            "enabled": True,
            "export_priority": 4
        },
        "attendance_summary": {
            "name_ar": "ملخص الحضور",
            "name_en": "Attendance Summary",
            "description": "Attendance and leave tracking",
            "enabled": True,
            "export_priority": 5
        },
        "monthly_trends": {
            "name_ar": "الاتجاهات الشهرية",
            "name_en": "Monthly Trends",
            "description": "Time-based trends and patterns",
            "enabled": True,
            "export_priority": 6
        }
    },

    # Auto-create views on startup
    "auto_create_views": True,

    # Refresh interval for materialized views (in hours)
    "materialized_refresh_hours": 1
}


# =============================================================================
# Power BI Templates Configuration
# =============================================================================

BI_TEMPLATES_CONFIG = {
    # Templates directory
    "templates_path": str(BASE_DIR / "templates" / "power_bi"),

    # Available templates
    "templates": {
        "employees_dashboard": {
            "name_ar": "لوحة تحكم الموظفين",
            "name_en": "Employees Dashboard",
            "file": "employees_dashboard.pbit",
            "icon": "users",
            "description": "Complete employee analytics dashboard"
        },
        "payroll_analysis": {
            "name_ar": "تحليل الرواتب",
            "name_en": "Payroll Analysis",
            "file": "payroll_analysis.pbit",
            "icon": "dollar-sign",
            "description": "Salary trends and distributions"
        },
        "department_overview": {
            "name_ar": "نظرة عامة الأقسام",
            "name_en": "Department Overview",
            "file": "department_overview.pbit",
            "icon": "building",
            "description": "Departmental performance metrics"
        },
        "executive_summary": {
            "name_ar": "ملخص تنفيذي",
            "name_en": "Executive Summary",
            "file": "executive_summary.pbit",
            "icon": "chart-bar",
            "description": "High-level KPIs for management"
        }
    }
}


# =============================================================================
# Helper Functions
# =============================================================================

_settings_cache: Optional[Dict[str, Any]] = None


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge override into base dict."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _load_settings() -> Dict[str, Any]:
    """Load BI settings from file or create default."""
    global _settings_cache

    if _settings_cache is not None:
        return _settings_cache

    default_settings = {
        "connection": BI_CONNECTION_CONFIG.copy(),
        "export": BI_EXPORT_CONFIG.copy(),
        "views": BI_VIEWS_CONFIG.copy(),
        "templates": BI_TEMPLATES_CONFIG.copy()
    }

    if BI_SETTINGS_FILE.exists():
        try:
            with open(BI_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                # Deep merge with defaults to preserve nested structures
                for key in default_settings:
                    if key in loaded:
                        default_settings[key] = _deep_merge(default_settings[key], loaded[key])
        except Exception:
            pass

    _settings_cache = default_settings
    return _settings_cache


def save_settings(settings: Dict[str, Any]) -> bool:
    """Save BI settings to file."""
    global _settings_cache

    try:
        with open(BI_SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        _settings_cache = settings
        return True
    except Exception:
        return False


def get_bi_config() -> Dict[str, Any]:
    """Get complete BI configuration."""
    return _load_settings()


def get_export_path() -> Path:
    """Get export directory path, create if not exists."""
    settings = _load_settings()
    path = Path(settings["export"]["export_path"])
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_bi_schema() -> str:
    """Get the BI Views schema name."""
    settings = _load_settings()
    return settings["views"]["schema"]


def get_enabled_views() -> Dict[str, Dict]:
    """Get only enabled BI Views."""
    settings = _load_settings()
    views = settings["views"]["views"]
    return {k: v for k, v in views.items() if v.get("enabled", True)}


def get_connection_string() -> str:
    """Get PostgreSQL connection string for Power BI."""
    settings = _load_settings()
    conn = settings["connection"]
    return f"Server={conn['server']};Port={conn['port']};Database={conn['database']}"
