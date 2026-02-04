# -*- coding: utf-8 -*-
"""
INTEGRA BI Integration Module
=============================
Power BI Desktop Integration for Advanced Analytics

This module provides:
- Connection configuration for Power BI Desktop
- Optimized SQL Views for analytics
- Auto-export functionality (CSV/Excel)
- Template management for .pbix files

Usage:
------
    from core.bi import (
        # Configuration
        BI_CONNECTION_CONFIG,
        get_bi_config,

        # Views Manager
        BIViewsManager,
        get_bi_views_manager,

        # Data Export
        BIDataExporter,
        get_bi_exporter,
        ExportScheduler,

        # Template Management
        BITemplateManager,
        get_template_manager
    )

Author: Mohamed
Version: 1.0.0
Date: February 2026
"""

from .connection_config import (
    BI_CONNECTION_CONFIG,
    BI_EXPORT_CONFIG,
    BI_VIEWS_CONFIG,
    get_bi_config,
    get_export_path,
    get_bi_schema
)

from .views_manager import (
    BIViewsManager,
    get_bi_views_manager
)

from .data_exporter import (
    BIDataExporter,
    get_bi_exporter
)

from .export_scheduler import (
    ExportScheduler,
    get_export_scheduler
)

from .template_manager import (
    BITemplateManager,
    get_template_manager,
    BITemplate
)

__all__ = [
    # Configuration
    'BI_CONNECTION_CONFIG',
    'BI_EXPORT_CONFIG',
    'BI_VIEWS_CONFIG',
    'get_bi_config',
    'get_export_path',
    'get_bi_schema',

    # Views Manager
    'BIViewsManager',
    'get_bi_views_manager',

    # Data Export
    'BIDataExporter',
    'get_bi_exporter',

    # Export Scheduler
    'ExportScheduler',
    'get_export_scheduler',

    # Template Management
    'BITemplateManager',
    'get_template_manager',
    'BITemplate'
]

__version__ = '1.0.0'
__author__ = 'Mohamed'
