"""
PDF Generator
=============
Generate professional PDF reports using ReportLab and WeasyPrint.

Features:
- ReportLab for direct PDF generation
- WeasyPrint for HTML-to-PDF conversion
- RTL and Arabic support
- Tables with styling
- Headers and footers
- Page numbers
- Images and charts
- Custom fonts

Usage:
    from core.reporting import PDFGenerator, PDFConfig

    # Basic usage
    pdf = PDFGenerator()
    pdf.add_heading("تقرير الموظفين")
    pdf.add_table(data, headers=["الاسم", "الراتب"])
    pdf.save("report.pdf")

    # With configuration
    config = PDFConfig(
        title="كشف الرواتب",
        orientation="landscape",
        show_page_numbers=True
    )
    pdf = PDFGenerator(config)
    pdf.add_heading("كشف رواتب شهر يناير")
    pdf.add_table(employees)
    pdf.save("salaries.pdf")
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime
import io
import os

from core.logging import app_logger


# Check available PDF libraries
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, A3, A5, letter, legal, landscape, portrait
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm, mm
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        Image, PageBreak, KeepTogether, HRFlowable
    )
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

PDF_AVAILABLE = REPORTLAB_AVAILABLE or WEASYPRINT_AVAILABLE


# Paper sizes mapping
PAPER_SIZES = {
    'A4': A4 if REPORTLAB_AVAILABLE else (595, 842),
    'A3': A3 if REPORTLAB_AVAILABLE else (842, 1191),
    'A5': A5 if REPORTLAB_AVAILABLE else (420, 595),
    'Letter': letter if REPORTLAB_AVAILABLE else (612, 792),
    'Legal': legal if REPORTLAB_AVAILABLE else (612, 1008),
}


@dataclass
class PDFConfig:
    """PDF generation configuration."""
    # Document info
    title: str = ""
    subtitle: str = ""
    author: str = "INTEGRA"
    subject: str = ""

    # Page setup
    paper_size: str = "A4"
    orientation: str = "portrait"  # portrait or landscape
    margins: Tuple[float, float, float, float] = (72, 72, 72, 72)  # top, right, bottom, left

    # Styling
    rtl: bool = True
    font_family: str = "Cairo"
    font_size: int = 12
    heading_color: str = "#2563eb"
    text_color: str = "#000000"
    table_header_bg: str = "#2563eb"
    table_header_fg: str = "#ffffff"
    table_row_alt_bg: str = "#f5f5f5"
    primary_color: str = "#2563eb"

    # Header/Footer
    show_header: bool = True
    show_footer: bool = True
    show_page_numbers: bool = True
    header_text: str = ""
    footer_text: str = "INTEGRA - نظام الإدارة المتكامل"
    logo_path: Optional[str] = None

    # Advanced
    compress: bool = True
    encrypt: bool = False
    password: Optional[str] = None


class PDFGenerator:
    """
    Generate PDF reports using ReportLab.

    Supports RTL Arabic text, tables, images, and professional formatting.
    """

    def __init__(self, config: PDFConfig = None):
        """
        Initialize PDF generator.

        Args:
            config: PDF configuration
        """
        if not PDF_AVAILABLE:
            raise ImportError(
                "PDF libraries not installed. Run: pip install reportlab weasyprint"
            )

        self.config = config or PDFConfig()
        self._elements = []
        self._styles = None
        self._page_size = None
        self._fonts_registered = False

        self._setup()
        app_logger.info("PDFGenerator initialized")

    def _setup(self) -> None:
        """Setup PDF generator."""
        if REPORTLAB_AVAILABLE:
            self._setup_page_size()
            self._setup_styles()
            self._register_fonts()

    def _setup_page_size(self) -> None:
        """Setup page size and orientation."""
        base_size = PAPER_SIZES.get(self.config.paper_size, A4)

        if self.config.orientation == "landscape":
            self._page_size = landscape(base_size) if REPORTLAB_AVAILABLE else (base_size[1], base_size[0])
        else:
            self._page_size = portrait(base_size) if REPORTLAB_AVAILABLE else base_size

    def _setup_styles(self) -> None:
        """Setup paragraph styles."""
        if not REPORTLAB_AVAILABLE:
            return

        self._styles = getSampleStyleSheet()

        # RTL alignment
        align = TA_RIGHT if self.config.rtl else TA_LEFT

        # Normal style
        self._styles.add(ParagraphStyle(
            name='Normal_RTL',
            parent=self._styles['Normal'],
            fontName=self.config.font_family if self._fonts_registered else 'Helvetica',
            fontSize=self.config.font_size,
            alignment=align,
            wordWrap='RTL' if self.config.rtl else 'LTR',
            leading=self.config.font_size * 1.5
        ))

        # Heading styles
        for i in range(1, 6):
            size = {1: 24, 2: 20, 3: 16, 4: 14, 5: 12}.get(i, 12)
            self._styles.add(ParagraphStyle(
                name=f'Heading{i}_RTL',
                parent=self._styles['Normal'],
                fontName=self.config.font_family if self._fonts_registered else 'Helvetica',
                fontSize=size,
                alignment=align,
                textColor=colors.HexColor(self.config.heading_color),
                spaceAfter=12,
                spaceBefore=12 if i > 1 else 0,
                leading=size * 1.3
            ))

        # Title style
        self._styles.add(ParagraphStyle(
            name='Title_RTL',
            parent=self._styles['Normal'],
            fontName=self.config.font_family if self._fonts_registered else 'Helvetica',
            fontSize=28,
            alignment=TA_CENTER,
            textColor=colors.HexColor(self.config.heading_color),
            spaceAfter=20
        ))

        # Table cell style
        self._styles.add(ParagraphStyle(
            name='TableCell_RTL',
            parent=self._styles['Normal'],
            fontName=self.config.font_family if self._fonts_registered else 'Helvetica',
            fontSize=10,
            alignment=align,
            wordWrap='RTL' if self.config.rtl else 'LTR'
        ))

    def _register_fonts(self) -> None:
        """Register Arabic fonts."""
        if not REPORTLAB_AVAILABLE:
            return

        # Try to find and register Cairo font
        font_paths = [
            # Windows
            "C:/Windows/Fonts/Cairo-Regular.ttf",
            "C:/Windows/Fonts/Cairo-Bold.ttf",
            # Common locations
            "/usr/share/fonts/truetype/cairo/Cairo-Regular.ttf",
            "/usr/local/share/fonts/Cairo-Regular.ttf",
            # Project fonts directory
            Path(__file__).parent.parent.parent / "assets" / "fonts" / "Cairo-Regular.ttf",
        ]

        cairo_found = False
        for font_path in font_paths:
            if Path(font_path).exists():
                try:
                    pdfmetrics.registerFont(TTFont('Cairo', str(font_path)))
                    cairo_found = True
                    self._fonts_registered = True
                    app_logger.debug(f"Registered Cairo font from: {font_path}")
                    break
                except Exception as e:
                    app_logger.debug(f"Failed to register font {font_path}: {e}")

        if not cairo_found:
            # Fallback to Arabic-supporting fonts
            try:
                # Try Arial which supports Arabic on Windows
                if os.path.exists("C:/Windows/Fonts/arial.ttf"):
                    pdfmetrics.registerFont(TTFont('Cairo', "C:/Windows/Fonts/arial.ttf"))
                    self._fonts_registered = True
                    app_logger.debug("Using Arial as fallback Arabic font")
            except Exception:
                app_logger.warning("No Arabic font found, using Helvetica fallback")
                self.config.font_family = 'Helvetica'

    def add_heading(
        self,
        text: str,
        level: int = 1,
        alignment: str = None
    ) -> 'PDFGenerator':
        """
        Add heading to document.

        Args:
            text: Heading text
            level: Heading level (1-5)
            alignment: Override alignment (left, center, right)

        Returns:
            Self for chaining
        """
        if not REPORTLAB_AVAILABLE:
            return self

        style_name = f'Heading{level}_RTL'
        if style_name not in self._styles:
            style_name = 'Heading1_RTL'

        style = self._styles[style_name]

        # Override alignment if specified
        if alignment:
            align_map = {'left': TA_LEFT, 'center': TA_CENTER, 'right': TA_RIGHT}
            style = ParagraphStyle(
                name=f'{style_name}_custom',
                parent=style,
                alignment=align_map.get(alignment, TA_RIGHT)
            )

        self._elements.append(Paragraph(text, style))
        return self

    def add_text(
        self,
        text: str,
        font_size: int = None,
        bold: bool = False,
        italic: bool = False,
        color: str = None,
        alignment: str = None
    ) -> 'PDFGenerator':
        """
        Add text paragraph.

        Args:
            text: Text content
            font_size: Font size (optional)
            bold: Bold text
            italic: Italic text
            color: Text color
            alignment: Text alignment

        Returns:
            Self for chaining
        """
        if not REPORTLAB_AVAILABLE:
            return self

        # Apply formatting tags
        if bold:
            text = f"<b>{text}</b>"
        if italic:
            text = f"<i>{text}</i>"
        if color:
            text = f'<font color="{color}">{text}</font>'

        style = ParagraphStyle(
            name='Custom_Text',
            parent=self._styles['Normal_RTL'],
            fontSize=font_size or self.config.font_size,
            alignment={
                'left': TA_LEFT,
                'center': TA_CENTER,
                'right': TA_RIGHT,
                'justify': TA_JUSTIFY
            }.get(alignment, TA_RIGHT if self.config.rtl else TA_LEFT)
        )

        self._elements.append(Paragraph(text, style))
        return self

    def add_paragraph(self, text: str, **kwargs) -> 'PDFGenerator':
        """Alias for add_text."""
        return self.add_text(text, **kwargs)

    def add_table(
        self,
        data: List[Dict],
        headers: List[str] = None,
        column_widths: List[float] = None,
        style: str = "grid"
    ) -> 'PDFGenerator':
        """
        Add table to document.

        Args:
            data: List of row dictionaries
            headers: Column headers (uses dict keys if not provided)
            column_widths: Column widths in points
            style: Table style (grid, simple, minimal)

        Returns:
            Self for chaining
        """
        if not REPORTLAB_AVAILABLE or not data:
            return self

        # Get headers
        if headers is None:
            headers = list(data[0].keys())

        # Reverse headers for RTL
        if self.config.rtl:
            headers = headers[::-1]

        # Build table data
        table_data = [headers]

        for row in data:
            row_values = [str(row.get(h, '')) for h in (headers[::-1] if self.config.rtl else headers)]
            if self.config.rtl:
                row_values = row_values[::-1]
            table_data.append(row_values)

        # Calculate column widths if not provided
        if column_widths is None:
            available_width = self._page_size[0] - self.config.margins[1] - self.config.margins[3]
            column_widths = [available_width / len(headers)] * len(headers)

        # Create table
        table = Table(table_data, colWidths=column_widths)

        # Define table style
        style_commands = [
            # Header style
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.config.table_header_bg)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor(self.config.table_header_fg)),
            ('FONTNAME', (0, 0), (-1, 0), self.config.font_family if self._fonts_registered else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTNAME', (0, 1), (-1, -1), self.config.font_family if self._fonts_registered else 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT' if self.config.rtl else 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]

        # Add borders based on style
        if style == "grid":
            style_commands.extend([
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dddddd')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ])
        elif style == "simple":
            style_commands.extend([
                ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor(self.config.primary_color)),
                ('LINEBELOW', (0, -1), (-1, -1), 1, colors.HexColor('#cccccc')),
            ])
        elif style == "minimal":
            style_commands.extend([
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor(self.config.primary_color)),
            ])

        # Alternating row colors
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                style_commands.append(
                    ('BACKGROUND', (0, i), (-1, i), colors.HexColor(self.config.table_row_alt_bg))
                )

        table.setStyle(TableStyle(style_commands))
        self._elements.append(table)

        return self

    def add_image(
        self,
        image_path: str,
        width: float = None,
        height: float = None,
        alignment: str = "center"
    ) -> 'PDFGenerator':
        """
        Add image to document.

        Args:
            image_path: Path to image file
            width: Image width in points
            height: Image height in points
            alignment: Image alignment

        Returns:
            Self for chaining
        """
        if not REPORTLAB_AVAILABLE:
            return self

        try:
            if not Path(image_path).exists():
                app_logger.warning(f"Image not found: {image_path}")
                return self

            img = Image(image_path)

            # Maintain aspect ratio
            if width and not height:
                ratio = width / img.drawWidth
                img.drawWidth = width
                img.drawHeight = img.drawHeight * ratio
            elif height and not width:
                ratio = height / img.drawHeight
                img.drawHeight = height
                img.drawWidth = img.drawWidth * ratio
            elif width and height:
                img.drawWidth = width
                img.drawHeight = height

            # Wrap in table for alignment
            if alignment == "center":
                align_table = Table([[img]], colWidths=[self._page_size[0] - self.config.margins[1] - self.config.margins[3]])
                align_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                self._elements.append(align_table)
            else:
                self._elements.append(img)

        except Exception as e:
            app_logger.error(f"Failed to add image: {e}")

        return self

    def add_spacer(self, height: float = 20) -> 'PDFGenerator':
        """
        Add vertical spacer.

        Args:
            height: Spacer height in points

        Returns:
            Self for chaining
        """
        if REPORTLAB_AVAILABLE:
            self._elements.append(Spacer(1, height))
        return self

    def add_line(
        self,
        width: str = "100%",
        thickness: float = 1,
        color: str = "#cccccc"
    ) -> 'PDFGenerator':
        """
        Add horizontal line.

        Args:
            width: Line width (percentage or points)
            thickness: Line thickness
            color: Line color

        Returns:
            Self for chaining
        """
        if REPORTLAB_AVAILABLE:
            line = HRFlowable(
                width=width,
                thickness=thickness,
                color=colors.HexColor(color),
                spaceBefore=10,
                spaceAfter=10
            )
            self._elements.append(line)
        return self

    def add_page_break(self) -> 'PDFGenerator':
        """Add page break."""
        if REPORTLAB_AVAILABLE:
            self._elements.append(PageBreak())
        return self

    def _header_footer(self, canvas, doc) -> None:
        """Draw header and footer on each page."""
        canvas.saveState()

        page_width = self._page_size[0]
        page_height = self._page_size[1]

        # Header
        if self.config.show_header:
            # Logo
            if self.config.logo_path and Path(self.config.logo_path).exists():
                try:
                    canvas.drawImage(
                        self.config.logo_path,
                        self.config.margins[3],
                        page_height - self.config.margins[0] + 10,
                        width=60,
                        height=30,
                        preserveAspectRatio=True
                    )
                except Exception:
                    pass

            # Header text
            if self.config.header_text:
                canvas.setFont(self.config.font_family if self._fonts_registered else 'Helvetica', 10)
                canvas.drawCentredString(
                    page_width / 2,
                    page_height - self.config.margins[0] / 2,
                    self.config.header_text
                )

            # Header line
            canvas.setStrokeColor(colors.HexColor(self.config.primary_color))
            canvas.setLineWidth(0.5)
            canvas.line(
                self.config.margins[3],
                page_height - self.config.margins[0] + 5,
                page_width - self.config.margins[1],
                page_height - self.config.margins[0] + 5
            )

        # Footer
        if self.config.show_footer:
            # Footer line
            canvas.setStrokeColor(colors.HexColor('#cccccc'))
            canvas.setLineWidth(0.5)
            canvas.line(
                self.config.margins[3],
                self.config.margins[2] - 5,
                page_width - self.config.margins[1],
                self.config.margins[2] - 5
            )

            # Footer text
            if self.config.footer_text:
                canvas.setFont(self.config.font_family if self._fonts_registered else 'Helvetica', 8)
                canvas.setFillColor(colors.HexColor('#666666'))
                canvas.drawCentredString(
                    page_width / 2,
                    self.config.margins[2] / 2,
                    self.config.footer_text
                )

            # Page number
            if self.config.show_page_numbers:
                canvas.setFont(self.config.font_family if self._fonts_registered else 'Helvetica', 8)
                page_num = canvas.getPageNumber()
                canvas.drawString(
                    self.config.margins[3],
                    self.config.margins[2] / 2,
                    f"صفحة {page_num}"
                )

        canvas.restoreState()

    def save(self, output_path: str) -> bool:
        """
        Save PDF to file.

        Args:
            output_path: Output file path

        Returns:
            True if successful
        """
        if not REPORTLAB_AVAILABLE:
            app_logger.error("ReportLab not available")
            return False

        try:
            # Ensure directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # Create document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=self._page_size,
                topMargin=self.config.margins[0],
                rightMargin=self.config.margins[1],
                bottomMargin=self.config.margins[2],
                leftMargin=self.config.margins[3],
                title=self.config.title,
                author=self.config.author,
                subject=self.config.subject
            )

            # Build PDF
            doc.build(
                self._elements,
                onFirstPage=self._header_footer,
                onLaterPages=self._header_footer
            )

            app_logger.info(f"PDF saved: {output_path}")
            return True

        except Exception as e:
            app_logger.error(f"Failed to save PDF: {e}", exc_info=True)
            return False

    def to_bytes(self) -> bytes:
        """
        Generate PDF as bytes.

        Returns:
            PDF content as bytes
        """
        if not REPORTLAB_AVAILABLE:
            return b''

        try:
            buffer = io.BytesIO()

            doc = SimpleDocTemplate(
                buffer,
                pagesize=self._page_size,
                topMargin=self.config.margins[0],
                rightMargin=self.config.margins[1],
                bottomMargin=self.config.margins[2],
                leftMargin=self.config.margins[3]
            )

            doc.build(
                self._elements,
                onFirstPage=self._header_footer,
                onLaterPages=self._header_footer
            )

            return buffer.getvalue()

        except Exception as e:
            app_logger.error(f"Failed to generate PDF bytes: {e}")
            return b''


def create_pdf_report(
    data: List[Dict],
    output_path: str,
    title: str = "",
    headers: List[str] = None,
    **config_kwargs
) -> bool:
    """
    Quick function to create PDF report.

    Args:
        data: Report data
        output_path: Output file path
        title: Report title
        headers: Table headers
        **config_kwargs: Additional PDFConfig options

    Returns:
        True if successful
    """
    try:
        config = PDFConfig(title=title, **config_kwargs)
        pdf = PDFGenerator(config)

        if title:
            pdf.add_heading(title, level=1)
            pdf.add_spacer(10)

        # Add date
        pdf.add_text(
            f"التاريخ: {datetime.now().strftime('%Y-%m-%d')}",
            font_size=10,
            alignment="left"
        )
        pdf.add_line()
        pdf.add_spacer(20)

        # Add table
        if data:
            pdf.add_table(data, headers=headers)

        return pdf.save(output_path)

    except Exception as e:
        app_logger.error(f"Failed to create PDF report: {e}")
        return False


class WeasyPrintGenerator:
    """
    Generate PDF from HTML using WeasyPrint.

    Useful for complex layouts with CSS styling.
    """

    def __init__(self, config: PDFConfig = None):
        """Initialize WeasyPrint generator."""
        if not WEASYPRINT_AVAILABLE:
            raise ImportError("WeasyPrint not installed. Run: pip install weasyprint")

        self.config = config or PDFConfig()
        self._html_content = ""
        self._css_content = ""

    def set_html(self, html: str) -> 'WeasyPrintGenerator':
        """Set HTML content."""
        self._html_content = html
        return self

    def set_css(self, css: str) -> 'WeasyPrintGenerator':
        """Set CSS content."""
        self._css_content = css
        return self

    def save(self, output_path: str) -> bool:
        """Save PDF to file."""
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            html = HTML(string=self._html_content)
            css = CSS(string=self._css_content) if self._css_content else None

            if css:
                html.write_pdf(output_path, stylesheets=[css])
            else:
                html.write_pdf(output_path)

            app_logger.info(f"WeasyPrint PDF saved: {output_path}")
            return True

        except Exception as e:
            app_logger.error(f"WeasyPrint failed: {e}")
            return False
