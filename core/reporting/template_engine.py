"""
Template Engine
===============
Jinja2-based template engine for report generation.

Features:
- Jinja2 template rendering
- Custom filters for Arabic/formatting
- RTL support
- Multiple template sources (file, string, database)
- Caching for performance
- Built-in report templates
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from jinja2 import (
    Environment, FileSystemLoader, BaseLoader, TemplateNotFound,
    select_autoescape, Template, ChoiceLoader, DictLoader
)

from core.logging import app_logger
from .filters import TEMPLATE_FILTERS


class TemplateSource(Enum):
    """Template source type."""
    FILE = "file"
    STRING = "string"
    DATABASE = "database"


@dataclass
class TemplateConfig:
    """Template rendering configuration."""

    # Template settings
    template_name: str = ""
    template_string: str = ""
    template_source: TemplateSource = TemplateSource.FILE

    # RTL/Language
    rtl: bool = True
    language: str = "ar"
    direction: str = "rtl"

    # Report metadata
    title: str = ""
    subtitle: str = ""
    company_name: str = "INTEGRA"
    logo_path: str = ""

    # Page settings
    page_size: str = "A4"
    orientation: str = "portrait"
    margin_top: float = 2.0
    margin_bottom: float = 2.0
    margin_left: float = 2.0
    margin_right: float = 2.0

    # Header/Footer
    show_header: bool = True
    show_footer: bool = True
    header_text: str = ""
    footer_text: str = ""
    show_page_numbers: bool = True
    show_date: bool = True

    # Styling
    primary_color: str = "#2563eb"
    font_family: str = "Cairo, Arial, sans-serif"
    font_size: int = 12

    # Additional context
    extra_context: Dict[str, Any] = field(default_factory=dict)


class DatabaseTemplateLoader(BaseLoader):
    """
    Load templates from database.

    Expects a table with columns:
    - name: Template name
    - content: Template content
    - updated_at: Last update time
    """

    def __init__(self, table_name: str = "report_templates"):
        self.table_name = table_name
        self._cache: Dict[str, tuple] = {}

    def get_source(self, environment, template):
        """Get template source from database."""
        try:
            from core.database import select_one

            columns, row = select_one(
                f"SELECT content, updated_at FROM {self.table_name} WHERE name = %s",
                (template,)
            )

            if not row:
                raise TemplateNotFound(template)

            content = row[0]
            mtime = row[1].timestamp() if row[1] else 0

            def uptodate():
                _, current = select_one(
                    f"SELECT updated_at FROM {self.table_name} WHERE name = %s",
                    (template,)
                )
                if not current:
                    return False
                current_mtime = current[0].timestamp() if current[0] else 0
                return mtime == current_mtime

            return content, template, uptodate

        except ImportError:
            raise TemplateNotFound(template)
        except Exception as e:
            app_logger.error(f"Error loading template from database: {e}")
            raise TemplateNotFound(template)


class TemplateEngine:
    """
    Main template engine using Jinja2.

    Supports multiple template sources and custom filters.
    """

    def __init__(
        self,
        template_dirs: Optional[List[str]] = None,
        use_database: bool = False,
        cache_size: int = 400,
        auto_reload: bool = True
    ):
        """
        Initialize template engine.

        Args:
            template_dirs: Directories to search for templates
            use_database: Enable database template loader
            cache_size: LRU cache size (0 to disable)
            auto_reload: Auto-reload templates on change
        """
        self._template_dirs = template_dirs or []
        self._use_database = use_database
        self._cache_size = cache_size
        self._auto_reload = auto_reload

        # Add default template directories
        base_path = Path(__file__).parent / "templates"
        if base_path.exists():
            self._template_dirs.insert(0, str(base_path))

        self._env = self._create_environment()
        self._register_filters()
        self._register_globals()

        app_logger.info("TemplateEngine initialized")

    def _create_environment(self) -> Environment:
        """Create Jinja2 environment with loaders."""
        loaders = []

        # File system loaders
        for directory in self._template_dirs:
            if Path(directory).exists():
                loaders.append(FileSystemLoader(directory))

        # Database loader
        if self._use_database:
            loaders.append(DatabaseTemplateLoader())

        # Built-in templates
        loaders.append(DictLoader(BUILTIN_TEMPLATES))

        return Environment(
            loader=ChoiceLoader(loaders) if loaders else None,
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True,
            cache_size=self._cache_size,
            auto_reload=self._auto_reload
        )

    def _register_filters(self) -> None:
        """Register custom filters."""
        for name, func in TEMPLATE_FILTERS.items():
            self._env.filters[name] = func

    def _register_globals(self) -> None:
        """Register global functions/variables."""
        self._env.globals.update({
            "now": datetime.now,
            "today": lambda: datetime.now().date(),
            "range": range,
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "min": min,
            "max": max,
            "sum": sum,
            "sorted": sorted,
            "enumerate": enumerate,
            "zip": zip
        })

    def render(
        self,
        config: TemplateConfig,
        data: Dict[str, Any]
    ) -> str:
        """
        Render template with data.

        Args:
            config: Template configuration
            data: Data to render

        Returns:
            Rendered HTML string
        """
        try:
            # Build context
            context = self._build_context(config, data)

            # Get template
            if config.template_source == TemplateSource.STRING:
                template = self._env.from_string(config.template_string)
            else:
                template = self._env.get_template(config.template_name)

            # Render
            rendered = template.render(**context)

            app_logger.debug(f"Template rendered: {config.template_name or 'string'}")
            return rendered

        except Exception as e:
            app_logger.error(f"Template render error: {e}")
            raise

    def render_string(
        self,
        template_string: str,
        data: Dict[str, Any],
        config: Optional[TemplateConfig] = None
    ) -> str:
        """
        Render template from string.

        Args:
            template_string: Template content
            data: Data to render
            config: Optional configuration

        Returns:
            Rendered HTML string
        """
        cfg = config or TemplateConfig()
        cfg.template_string = template_string
        cfg.template_source = TemplateSource.STRING

        return self.render(cfg, data)

    def render_file(
        self,
        template_name: str,
        data: Dict[str, Any],
        config: Optional[TemplateConfig] = None
    ) -> str:
        """
        Render template from file.

        Args:
            template_name: Template file name
            data: Data to render
            config: Optional configuration

        Returns:
            Rendered HTML string
        """
        cfg = config or TemplateConfig()
        cfg.template_name = template_name
        cfg.template_source = TemplateSource.FILE

        return self.render(cfg, data)

    def _build_context(
        self,
        config: TemplateConfig,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build template context with config and data."""
        context = {
            # Configuration
            "config": config,
            "rtl": config.rtl,
            "direction": config.direction,
            "language": config.language,

            # Metadata
            "title": config.title,
            "subtitle": config.subtitle,
            "company_name": config.company_name,
            "logo_path": config.logo_path,

            # Page
            "page_size": config.page_size,
            "orientation": config.orientation,

            # Header/Footer
            "show_header": config.show_header,
            "show_footer": config.show_footer,
            "header_text": config.header_text,
            "footer_text": config.footer_text,
            "show_page_numbers": config.show_page_numbers,
            "show_date": config.show_date,

            # Styling
            "primary_color": config.primary_color,
            "font_family": config.font_family,
            "font_size": config.font_size,

            # Timestamps
            "generated_at": datetime.now(),
            "generated_date": datetime.now().strftime("%Y/%m/%d"),
            "generated_time": datetime.now().strftime("%H:%M"),

            # User data
            **data,

            # Extra context
            **config.extra_context
        }

        return context

    def add_template_dir(self, directory: str) -> None:
        """Add a template directory."""
        if Path(directory).exists():
            self._template_dirs.append(directory)
            self._env = self._create_environment()
            self._register_filters()
            self._register_globals()

    def get_template_list(self) -> List[str]:
        """Get list of available templates."""
        templates = []

        # From directories
        for directory in self._template_dirs:
            path = Path(directory)
            if path.exists():
                for f in path.rglob("*.html"):
                    rel_path = f.relative_to(path)
                    templates.append(str(rel_path))

        # Built-in
        templates.extend(BUILTIN_TEMPLATES.keys())

        return sorted(set(templates))


# Built-in template definitions
BUILTIN_TEMPLATES = {
    # Base layout
    "base.html": """
<!DOCTYPE html>
<html lang="{{ language }}" dir="{{ direction }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - {{ company_name }}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: {{ font_family }};
            font-size: {{ font_size }}px;
            direction: {{ direction }};
            line-height: 1.6;
            color: #1f2937;
            background: #ffffff;
        }

        .container {
            max-width: 210mm;
            margin: 0 auto;
            padding: 20mm;
        }

        /* Header */
        .report-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid {{ primary_color }};
            padding-bottom: 15px;
            margin-bottom: 20px;
        }

        .report-header .logo img {
            max-height: 60px;
        }

        .report-header .info {
            text-align: {{ 'left' if direction == 'ltr' else 'right' }};
        }

        .report-header .info h1 {
            color: {{ primary_color }};
            font-size: 24px;
            margin-bottom: 5px;
        }

        .report-header .info h2 {
            color: #6b7280;
            font-size: 14px;
            font-weight: normal;
        }

        .report-header .date {
            color: #9ca3af;
            font-size: 12px;
        }

        /* Content */
        .report-content {
            min-height: 200mm;
        }

        /* Tables */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }

        th, td {
            padding: 10px 12px;
            text-align: {{ 'left' if direction == 'ltr' else 'right' }};
            border: 1px solid #e5e7eb;
        }

        th {
            background: {{ primary_color }};
            color: white;
            font-weight: 600;
        }

        tr:nth-child(even) {
            background: #f9fafb;
        }

        tr:hover {
            background: #f3f4f6;
        }

        /* Footer */
        .report-footer {
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #e5e7eb;
            display: flex;
            justify-content: space-between;
            color: #9ca3af;
            font-size: 11px;
        }

        /* Print styles */
        @media print {
            body {
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }

            .container {
                padding: 10mm;
            }

            .no-print {
                display: none;
            }
        }

        {% block extra_styles %}{% endblock %}
    </style>
</head>
<body>
    <div class="container">
        {% if show_header %}
        <header class="report-header">
            <div class="info">
                <h1>{{ title }}</h1>
                {% if subtitle %}<h2>{{ subtitle }}</h2>{% endif %}
            </div>
            {% if logo_path %}
            <div class="logo">
                <img src="{{ logo_path }}" alt="{{ company_name }}">
            </div>
            {% endif %}
            {% if show_date %}
            <div class="date">{{ generated_date }}</div>
            {% endif %}
        </header>
        {% endif %}

        <main class="report-content">
            {% block content %}{% endblock %}
        </main>

        {% if show_footer %}
        <footer class="report-footer">
            <span>{{ company_name }}</span>
            <span>{{ footer_text or generated_date }}</span>
            {% if show_page_numbers %}
            <span class="page-number"></span>
            {% endif %}
        </footer>
        {% endif %}
    </div>
</body>
</html>
""",

    # Simple table report
    "reports/table_report.html": """
{% extends "base.html" %}

{% block content %}
<table>
    <thead>
        <tr>
            {% for column in columns %}
            <th>{{ column.label }}</th>
            {% endfor %}
        </tr>
    </thead>
    <tbody>
        {% for row in data %}
        <tr>
            {% for column in columns %}
            <td>
                {% if column.type == 'currency' %}
                    {{ row[column.field] | currency }}
                {% elif column.type == 'date' %}
                    {{ row[column.field] | date }}
                {% elif column.type == 'number' %}
                    {{ row[column.field] | number }}
                {% else %}
                    {{ row[column.field] | default('-') }}
                {% endif %}
            </td>
            {% endfor %}
        </tr>
        {% endfor %}
    </tbody>
    {% if show_totals %}
    <tfoot>
        <tr>
            {% for column in columns %}
            <td>
                {% if column.total %}
                    <strong>{{ data | sum_column(column.field) | currency }}</strong>
                {% endif %}
            </td>
            {% endfor %}
        </tr>
    </tfoot>
    {% endif %}
</table>

<div class="summary">
    <p>إجمالي السجلات: {{ data | length }}</p>
</div>
{% endblock %}
""",

    # Employee list report
    "reports/employee_list.html": """
{% extends "base.html" %}

{% block extra_styles %}
.status-active { color: #10b981; }
.status-inactive { color: #ef4444; }
.employee-photo {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    object-fit: cover;
}
{% endblock %}

{% block content %}
<table>
    <thead>
        <tr>
            <th>#</th>
            <th>اسم الموظف</th>
            <th>الرقم الوظيفي</th>
            <th>القسم</th>
            <th>المسمى الوظيفي</th>
            <th>تاريخ التعيين</th>
            <th>الراتب</th>
            <th>الحالة</th>
        </tr>
    </thead>
    <tbody>
        {% for emp in employees %}
        <tr>
            <td>{{ loop.index }}</td>
            <td>{{ emp.name }}</td>
            <td>{{ emp.employee_number }}</td>
            <td>{{ emp.department }}</td>
            <td>{{ emp.job_title }}</td>
            <td>{{ emp.hire_date | date }}</td>
            <td>{{ emp.salary | currency }}</td>
            <td class="status-{{ 'active' if emp.is_active else 'inactive' }}">
                {{ 'نشط' if emp.is_active else 'غير نشط' }}
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<div class="summary">
    <p>إجمالي الموظفين: {{ employees | length }}</p>
    <p>إجمالي الرواتب: {{ employees | sum_column('salary') | currency }}</p>
</div>
{% endblock %}
""",

    # Invoice template
    "reports/invoice.html": """
{% extends "base.html" %}

{% block extra_styles %}
.invoice-info {
    display: flex;
    justify-content: space-between;
    margin-bottom: 30px;
}
.invoice-info div {
    flex: 1;
}
.invoice-total {
    text-align: {{ 'left' if direction == 'ltr' else 'right' }};
    margin-top: 20px;
}
.invoice-total .grand-total {
    font-size: 18px;
    color: {{ primary_color }};
    font-weight: bold;
}
{% endblock %}

{% block content %}
<div class="invoice-info">
    <div>
        <h3>معلومات الفاتورة</h3>
        <p>رقم الفاتورة: {{ invoice.number }}</p>
        <p>التاريخ: {{ invoice.date | date }}</p>
        <p>تاريخ الاستحقاق: {{ invoice.due_date | date }}</p>
    </div>
    <div>
        <h3>العميل</h3>
        <p>{{ invoice.customer_name }}</p>
        <p>{{ invoice.customer_address }}</p>
        <p>{{ invoice.customer_phone | phone }}</p>
    </div>
</div>

<table>
    <thead>
        <tr>
            <th>#</th>
            <th>الصنف</th>
            <th>الوصف</th>
            <th>الكمية</th>
            <th>السعر</th>
            <th>الإجمالي</th>
        </tr>
    </thead>
    <tbody>
        {% for item in invoice.items %}
        <tr>
            <td>{{ loop.index }}</td>
            <td>{{ item.product }}</td>
            <td>{{ item.description }}</td>
            <td>{{ item.quantity | number }}</td>
            <td>{{ item.price | currency }}</td>
            <td>{{ (item.quantity * item.price) | currency }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<div class="invoice-total">
    <p>المجموع الفرعي: {{ invoice.subtotal | currency }}</p>
    {% if invoice.discount %}
    <p>الخصم: {{ invoice.discount | currency }}</p>
    {% endif %}
    <p>الضريبة ({{ invoice.tax_rate }}%): {{ invoice.tax | currency }}</p>
    <p class="grand-total">الإجمالي: {{ invoice.total | currency }}</p>
</div>

{% if invoice.notes %}
<div class="notes">
    <h4>ملاحظات:</h4>
    <p>{{ invoice.notes }}</p>
</div>
{% endif %}
{% endblock %}
""",

    # Summary card report
    "reports/summary_cards.html": """
{% extends "base.html" %}

{% block extra_styles %}
.cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin: 20px 0;
}
.card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
}
.card .value {
    font-size: 28px;
    font-weight: bold;
    color: {{ primary_color }};
}
.card .label {
    color: #6b7280;
    margin-top: 5px;
}
.card .change {
    font-size: 12px;
    margin-top: 10px;
}
.card .change.positive { color: #10b981; }
.card .change.negative { color: #ef4444; }
{% endblock %}

{% block content %}
<div class="cards-grid">
    {% for card in cards %}
    <div class="card">
        <div class="value">
            {% if card.type == 'currency' %}
                {{ card.value | currency }}
            {% elif card.type == 'percentage' %}
                {{ card.value | percentage }}
            {% else %}
                {{ card.value | number }}
            {% endif %}
        </div>
        <div class="label">{{ card.label }}</div>
        {% if card.change %}
        <div class="change {{ 'positive' if card.change > 0 else 'negative' }}">
            {{ card.change | percentage(1, true) }}
        </div>
        {% endif %}
    </div>
    {% endfor %}
</div>

{% if details %}
<h3>التفاصيل</h3>
{{ details | safe }}
{% endif %}
{% endblock %}
"""
}


# Singleton instance
_template_engine: Optional[TemplateEngine] = None


def get_template_engine() -> TemplateEngine:
    """Get singleton template engine instance."""
    global _template_engine
    if _template_engine is None:
        _template_engine = TemplateEngine()
    return _template_engine


def render_template(
    template_name: str,
    data: Dict[str, Any],
    config: Optional[TemplateConfig] = None
) -> str:
    """
    Convenience function to render a template.

    Args:
        template_name: Template name
        data: Data to render
        config: Optional configuration

    Returns:
        Rendered HTML
    """
    engine = get_template_engine()
    return engine.render_file(template_name, data, config)


def render_string_template(
    template_string: str,
    data: Dict[str, Any],
    config: Optional[TemplateConfig] = None
) -> str:
    """
    Convenience function to render a template string.

    Args:
        template_string: Template content
        data: Data to render
        config: Optional configuration

    Returns:
        Rendered HTML
    """
    engine = get_template_engine()
    return engine.render_string(template_string, data, config)
