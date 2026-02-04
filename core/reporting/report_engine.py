"""
Report Engine
=============
Central report generation engine for INTEGRA.

Provides unified interface for generating reports in multiple formats.

Features:
- Multi-format output (PDF, Excel, Word, HTML)
- Template-based reports
- Data binding
- RTL and Arabic support
- Charts and calculations
- Header/Footer customization
- Page numbering
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Callable, Union
from pathlib import Path
from datetime import datetime
import threading

from core.logging import app_logger


class ElementType(Enum):
    """Report element types."""
    TEXT = "text"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    IMAGE = "image"
    CHART = "chart"
    LINE = "line"
    PAGE_BREAK = "page_break"
    SPACER = "spacer"
    FORMULA = "formula"
    FIELD = "field"
    GROUP = "group"


class Alignment(Enum):
    """Text alignment options."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


class PaperSize(Enum):
    """Paper size options."""
    A4 = "A4"
    A3 = "A3"
    A5 = "A5"
    LETTER = "Letter"
    LEGAL = "Legal"


class Orientation(Enum):
    """Page orientation."""
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


@dataclass
class ReportStyle:
    """Style configuration for report elements."""
    font_family: str = "Cairo"
    font_size: int = 12
    font_color: str = "#000000"
    background_color: Optional[str] = None
    bold: bool = False
    italic: bool = False
    underline: bool = False
    alignment: Alignment = Alignment.RIGHT
    padding: tuple = (5, 5, 5, 5)  # top, right, bottom, left
    margin: tuple = (0, 0, 0, 0)
    border: Optional[str] = None
    border_color: str = "#000000"
    border_width: float = 1.0


@dataclass
class ReportElement:
    """Single element in a report."""
    element_type: ElementType
    content: Any = None
    style: ReportStyle = field(default_factory=ReportStyle)
    properties: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def text(cls, text: str, **style_kwargs) -> 'ReportElement':
        """Create text element."""
        style = ReportStyle(**style_kwargs) if style_kwargs else ReportStyle()
        return cls(ElementType.TEXT, text, style)

    @classmethod
    def heading(cls, text: str, level: int = 1, **style_kwargs) -> 'ReportElement':
        """Create heading element."""
        # Default heading sizes
        sizes = {1: 24, 2: 20, 3: 16, 4: 14, 5: 12}
        style = ReportStyle(
            font_size=sizes.get(level, 12),
            bold=True,
            **style_kwargs
        )
        return cls(ElementType.HEADING, text, style, {"level": level})

    @classmethod
    def paragraph(cls, text: str, **style_kwargs) -> 'ReportElement':
        """Create paragraph element."""
        style = ReportStyle(**style_kwargs) if style_kwargs else ReportStyle()
        return cls(ElementType.PARAGRAPH, text, style)

    @classmethod
    def table(
        cls,
        data: List[Dict],
        headers: List[str] = None,
        column_widths: List[float] = None,
        **style_kwargs
    ) -> 'ReportElement':
        """Create table element."""
        style = ReportStyle(**style_kwargs) if style_kwargs else ReportStyle()
        props = {
            "headers": headers,
            "column_widths": column_widths
        }
        return cls(ElementType.TABLE, data, style, props)

    @classmethod
    def image(cls, path: str, width: float = None, height: float = None) -> 'ReportElement':
        """Create image element."""
        return cls(ElementType.IMAGE, path, properties={"width": width, "height": height})

    @classmethod
    def chart(
        cls,
        chart_type: str,
        data: Dict,
        title: str = None,
        width: float = 400,
        height: float = 300
    ) -> 'ReportElement':
        """Create chart element."""
        return cls(ElementType.CHART, data, properties={
            "chart_type": chart_type,
            "title": title,
            "width": width,
            "height": height
        })

    @classmethod
    def line(cls, thickness: float = 1, color: str = "#000000") -> 'ReportElement':
        """Create horizontal line element."""
        return cls(ElementType.LINE, properties={"thickness": thickness, "color": color})

    @classmethod
    def page_break(cls) -> 'ReportElement':
        """Create page break element."""
        return cls(ElementType.PAGE_BREAK)

    @classmethod
    def spacer(cls, height: float = 20) -> 'ReportElement':
        """Create spacer element."""
        return cls(ElementType.SPACER, properties={"height": height})

    @classmethod
    def formula(cls, expression: str, format_type: str = "number") -> 'ReportElement':
        """Create formula/calculated field element."""
        return cls(ElementType.FORMULA, expression, properties={"format": format_type})

    @classmethod
    def field(cls, field_name: str, format_type: str = None) -> 'ReportElement':
        """Create data field element."""
        return cls(ElementType.FIELD, field_name, properties={"format": format_type})


@dataclass
class ReportSection:
    """Section of a report (header, detail, footer, group)."""
    name: str
    elements: List[ReportElement] = field(default_factory=list)
    visible: bool = True
    repeat: bool = False  # Repeat for each data row
    condition: Optional[Callable] = None  # Conditional visibility

    def add(self, element: ReportElement) -> 'ReportSection':
        """Add element to section."""
        self.elements.append(element)
        return self

    def add_text(self, text: str, **kwargs) -> 'ReportSection':
        """Add text element."""
        self.elements.append(ReportElement.text(text, **kwargs))
        return self

    def add_heading(self, text: str, level: int = 1, **kwargs) -> 'ReportSection':
        """Add heading element."""
        self.elements.append(ReportElement.heading(text, level, **kwargs))
        return self

    def add_table(self, data: List[Dict], headers: List[str] = None, **kwargs) -> 'ReportSection':
        """Add table element."""
        self.elements.append(ReportElement.table(data, headers, **kwargs))
        return self

    def add_image(self, path: str, width: float = None, height: float = None) -> 'ReportSection':
        """Add image element."""
        self.elements.append(ReportElement.image(path, width, height))
        return self

    def add_chart(self, chart_type: str, data: Dict, **kwargs) -> 'ReportSection':
        """Add chart element."""
        self.elements.append(ReportElement.chart(chart_type, data, **kwargs))
        return self

    def add_line(self, thickness: float = 1, color: str = "#000000") -> 'ReportSection':
        """Add horizontal line."""
        self.elements.append(ReportElement.line(thickness, color))
        return self

    def add_page_break(self) -> 'ReportSection':
        """Add page break."""
        self.elements.append(ReportElement.page_break())
        return self

    def add_spacer(self, height: float = 20) -> 'ReportSection':
        """Add spacer."""
        self.elements.append(ReportElement.spacer(height))
        return self


@dataclass
class ReportConfig:
    """Report configuration."""
    # Basic info
    title: str = ""
    subtitle: str = ""
    author: str = "INTEGRA"
    created_date: datetime = field(default_factory=datetime.now)

    # Page setup
    paper_size: PaperSize = PaperSize.A4
    orientation: Orientation = Orientation.PORTRAIT
    margins: tuple = (72, 72, 72, 72)  # top, right, bottom, left (in points)

    # Styling
    rtl: bool = True
    font_family: str = "Cairo"
    primary_color: str = "#2563eb"
    secondary_color: str = "#64748b"

    # Header/Footer
    show_header: bool = True
    show_footer: bool = True
    show_page_numbers: bool = True
    header_text: str = ""
    footer_text: str = ""
    logo_path: Optional[str] = None

    # Output
    output_format: 'ReportFormat' = None  # Set dynamically
    template_name: Optional[str] = None

    # Data
    group_by: Optional[str] = None
    sort_by: Optional[str] = None
    sort_desc: bool = False

    # Totals
    calculate_totals: bool = False
    total_fields: List[str] = field(default_factory=list)


class ReportEngine:
    """
    Central report generation engine.

    Provides unified interface for creating reports in multiple formats.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize report engine."""
        if self._initialized:
            return

        self._generators = {}
        self._templates = {}
        self._filters = {}
        self._initialized = True

        # Register built-in filters
        self._register_builtin_filters()

        app_logger.info("ReportEngine initialized")

    def _register_builtin_filters(self):
        """Register built-in Jinja2-style filters."""
        from core.utils.formatters import (
            format_currency,
            format_number,
            format_date,
            format_percentage
        )

        self._filters = {
            "currency": format_currency,
            "number": format_number,
            "date": format_date,
            "percentage": format_percentage,
            "upper": lambda x: str(x).upper(),
            "lower": lambda x: str(x).lower(),
            "title": lambda x: str(x).title(),
        }

    def register_filter(self, name: str, func: Callable) -> None:
        """Register custom filter function."""
        self._filters[name] = func

    def get_filter(self, name: str) -> Optional[Callable]:
        """Get filter function by name."""
        return self._filters.get(name)

    def apply_filter(self, value: Any, filter_name: str) -> Any:
        """Apply filter to value."""
        filter_func = self._filters.get(filter_name)
        if filter_func:
            try:
                return filter_func(value)
            except Exception:
                return value
        return value

    def generate(
        self,
        data: Union[List[Dict], Dict],
        output_path: str,
        config: ReportConfig = None,
        **kwargs
    ) -> bool:
        """
        Generate report.

        Args:
            data: Report data
            output_path: Output file path
            config: Report configuration
            **kwargs: Additional options

        Returns:
            True if successful
        """
        from . import ReportFormat

        if config is None:
            config = ReportConfig()

        # Determine format from output path if not specified
        if config.output_format is None:
            ext = Path(output_path).suffix.lower()
            format_map = {
                '.pdf': ReportFormat.PDF,
                '.xlsx': ReportFormat.EXCEL,
                '.xls': ReportFormat.EXCEL,
                '.docx': ReportFormat.WORD,
                '.doc': ReportFormat.WORD,
                '.html': ReportFormat.HTML,
                '.csv': ReportFormat.CSV,
            }
            config.output_format = format_map.get(ext, ReportFormat.PDF)

        # Process data
        processed_data = self._process_data(data, config)

        # Generate based on format
        try:
            if config.output_format == ReportFormat.PDF:
                return self._generate_pdf(processed_data, output_path, config, **kwargs)
            elif config.output_format == ReportFormat.EXCEL:
                return self._generate_excel(processed_data, output_path, config, **kwargs)
            elif config.output_format == ReportFormat.WORD:
                return self._generate_word(processed_data, output_path, config, **kwargs)
            elif config.output_format == ReportFormat.HTML:
                return self._generate_html(processed_data, output_path, config, **kwargs)
            elif config.output_format == ReportFormat.CSV:
                return self._generate_csv(processed_data, output_path, config, **kwargs)
            else:
                app_logger.error(f"Unsupported format: {config.output_format}")
                return False

        except Exception as e:
            app_logger.error(f"Report generation failed: {e}", exc_info=True)
            return False

    def _process_data(
        self,
        data: Union[List[Dict], Dict],
        config: ReportConfig
    ) -> List[Dict]:
        """Process and prepare data for report."""
        # Ensure list format
        if isinstance(data, dict):
            data = [data]

        # Sort if specified
        if config.sort_by and data:
            try:
                data = sorted(
                    data,
                    key=lambda x: x.get(config.sort_by, ''),
                    reverse=config.sort_desc
                )
            except Exception:
                pass

        return data

    def _generate_pdf(
        self,
        data: List[Dict],
        output_path: str,
        config: ReportConfig,
        **kwargs
    ) -> bool:
        """Generate PDF report."""
        from .pdf_generator import PDFGenerator, PDFConfig

        pdf_config = PDFConfig(
            title=config.title,
            subtitle=config.subtitle,
            author=config.author,
            paper_size=config.paper_size.value,
            orientation=config.orientation.value,
            margins=config.margins,
            rtl=config.rtl,
            font_family=config.font_family,
            show_header=config.show_header,
            show_footer=config.show_footer,
            show_page_numbers=config.show_page_numbers,
            header_text=config.header_text,
            footer_text=config.footer_text,
            logo_path=config.logo_path,
            primary_color=config.primary_color
        )

        generator = PDFGenerator(pdf_config)

        # Add title
        if config.title:
            generator.add_heading(config.title, level=1)

        if config.subtitle:
            generator.add_text(config.subtitle, font_size=14, color=config.secondary_color)
            generator.add_spacer(10)

        # Add date
        generator.add_text(
            f"التاريخ: {config.created_date.strftime('%Y-%m-%d')}",
            font_size=10,
            alignment="left"
        )
        generator.add_line()
        generator.add_spacer(20)

        # Add data table if list
        if data and isinstance(data, list):
            headers = kwargs.get('headers', list(data[0].keys()) if data else [])
            generator.add_table(data, headers=headers)

        # Calculate totals if enabled
        if config.calculate_totals and config.total_fields and data:
            generator.add_spacer(20)
            generator.add_line()
            for field_name in config.total_fields:
                total = sum(
                    float(row.get(field_name, 0) or 0)
                    for row in data
                    if row.get(field_name) is not None
                )
                generator.add_text(
                    f"إجمالي {field_name}: {self.apply_filter(total, 'currency')}",
                    bold=True
                )

        return generator.save(output_path)

    def _generate_excel(
        self,
        data: List[Dict],
        output_path: str,
        config: ReportConfig,
        **kwargs
    ) -> bool:
        """Generate Excel report."""
        from .excel_generator import ExcelGenerator, ExcelConfig

        excel_config = ExcelConfig(
            title=config.title,
            author=config.author,
            rtl=config.rtl
        )

        generator = ExcelGenerator(excel_config)

        # Add main sheet with data
        sheet_name = kwargs.get('sheet_name', 'البيانات')
        headers = kwargs.get('headers', list(data[0].keys()) if data else [])

        generator.add_sheet(sheet_name, data, headers=headers)

        # Add totals if enabled
        if config.calculate_totals and config.total_fields:
            generator.add_totals_row(config.total_fields)

        return generator.save(output_path)

    def _generate_word(
        self,
        data: List[Dict],
        output_path: str,
        config: ReportConfig,
        **kwargs
    ) -> bool:
        """Generate Word report."""
        from .word_generator import WordGenerator, WordConfig

        word_config = WordConfig(
            title=config.title,
            author=config.author,
            rtl=config.rtl,
            font_family=config.font_family
        )

        generator = WordGenerator(word_config)

        # Add title
        if config.title:
            generator.add_heading(config.title, level=1)

        if config.subtitle:
            generator.add_paragraph(config.subtitle)

        # Add date
        generator.add_paragraph(f"التاريخ: {config.created_date.strftime('%Y-%m-%d')}")
        generator.add_line()

        # Add data table
        if data and isinstance(data, list):
            headers = kwargs.get('headers', list(data[0].keys()) if data else [])
            generator.add_table(data, headers=headers)

        return generator.save(output_path)

    def _generate_html(
        self,
        data: List[Dict],
        output_path: str,
        config: ReportConfig,
        **kwargs
    ) -> bool:
        """Generate HTML report."""
        try:
            html_content = self._render_html_template(data, config, **kwargs)

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            app_logger.info(f"HTML report saved: {output_path}")
            return True

        except Exception as e:
            app_logger.error(f"HTML generation failed: {e}")
            return False

    def _generate_csv(
        self,
        data: List[Dict],
        output_path: str,
        config: ReportConfig,
        **kwargs
    ) -> bool:
        """Generate CSV report."""
        import csv

        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            if not data:
                return False

            headers = kwargs.get('headers', list(data[0].keys()))

            with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(data)

            app_logger.info(f"CSV report saved: {output_path}")
            return True

        except Exception as e:
            app_logger.error(f"CSV generation failed: {e}")
            return False

    def _render_html_template(
        self,
        data: List[Dict],
        config: ReportConfig,
        **kwargs
    ) -> str:
        """Render HTML template."""
        headers = kwargs.get('headers', list(data[0].keys()) if data else [])

        direction = "rtl" if config.rtl else "ltr"
        align = "right" if config.rtl else "left"

        # Build table rows
        rows_html = ""
        for row in data:
            cells = "".join(f"<td>{row.get(h, '')}</td>" for h in headers)
            rows_html += f"<tr>{cells}</tr>\n"

        # Build header cells
        header_cells = "".join(f"<th>{h}</th>" for h in headers)

        html = f"""<!DOCTYPE html>
<html dir="{direction}" lang="ar">
<head>
    <meta charset="UTF-8">
    <title>{config.title}</title>
    <style>
        body {{
            font-family: '{config.font_family}', 'Arial', sans-serif;
            direction: {direction};
            text-align: {align};
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: {config.primary_color};
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: {config.secondary_color};
            font-size: 14px;
            margin-bottom: 20px;
        }}
        .date {{
            color: #666;
            font-size: 12px;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px 8px;
            text-align: {align};
        }}
        th {{
            background: {config.primary_color};
            color: white;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background: #f9f9f9;
        }}
        tr:hover {{
            background: #f0f0f0;
        }}
        .footer {{
            margin-top: 30px;
            text-align: center;
            color: #999;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{config.title}</h1>
        <div class="subtitle">{config.subtitle}</div>
        <div class="date">التاريخ: {config.created_date.strftime('%Y-%m-%d')}</div>

        <table>
            <thead>
                <tr>{header_cells}</tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>

        <div class="footer">
            تم إنشاء هذا التقرير بواسطة {config.author}
        </div>
    </div>
</body>
</html>"""

        return html

    def create_from_sections(
        self,
        sections: List[ReportSection],
        output_path: str,
        config: ReportConfig = None
    ) -> bool:
        """
        Create report from defined sections.

        Args:
            sections: List of report sections
            output_path: Output file path
            config: Report configuration

        Returns:
            True if successful
        """
        # TODO: Implement section-based rendering
        raise NotImplementedError("Section-based reports not yet implemented")


# Singleton accessor
def get_report_engine() -> ReportEngine:
    """Get the report engine singleton instance."""
    return ReportEngine()
