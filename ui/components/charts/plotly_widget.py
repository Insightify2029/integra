"""
Plotly Charts Widget
====================
Interactive charts for PyQt5 using Plotly.

Features:
- Pie charts, bar charts, line charts
- Interactive HTML rendering
- Arabic labels support
- Export to image

Usage:
    from ui.components.charts import PlotlyChart, create_pie_chart

    # In a window
    chart = PlotlyChart(self)
    chart.pie_chart(
        values=[30, 25, 20, 25],
        labels=["الإدارة", "المبيعات", "الإنتاج", "الدعم"],
        title="توزيع الموظفين حسب القسم"
    )
    layout.addWidget(chart)

    # Or quick function
    chart = create_pie_chart(values, labels, title)
"""

from typing import List, Dict, Any, Optional
import json

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import QUrl

try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False

from core.logging import app_logger


# Default colors for charts (professional palette)
DEFAULT_COLORS = [
    '#2563eb',  # Blue
    '#10b981',  # Green
    '#f59e0b',  # Amber
    '#ef4444',  # Red
    '#8b5cf6',  # Purple
    '#06b6d4',  # Cyan
    '#f97316',  # Orange
    '#ec4899',  # Pink
    '#6366f1',  # Indigo
    '#14b8a6',  # Teal
]


class PlotlyChart(QWidget):
    """Interactive Plotly chart widget for PyQt5."""

    def __init__(self, parent=None):
        """
        Initialize chart widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        if not PLOTLY_AVAILABLE:
            raise ImportError("plotly not installed. Run: pip install plotly")

        if not WEBENGINE_AVAILABLE:
            raise ImportError(
                "PyQtWebEngine not installed. Run: pip install PyQtWebEngine"
            )

        self._setup_ui()
        self._current_figure = None

        app_logger.debug("PlotlyChart widget initialized")

    def _setup_ui(self) -> None:
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._web_view = QWebEngineView()
        self._web_view.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        layout.addWidget(self._web_view)

    def _render(self, fig: go.Figure) -> None:
        """
        Render Plotly figure to the widget.

        Args:
            fig: Plotly figure object
        """
        self._current_figure = fig

        # Configure for RTL and Arabic
        fig.update_layout(
            font=dict(family="Arial, Cairo, sans-serif"),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )

        # Convert to HTML
        html = fig.to_html(
            include_plotlyjs='cdn',
            full_html=True,
            config={
                'responsive': True,
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['lasso2d', 'select2d']
            }
        )

        self._web_view.setHtml(html)

    def pie_chart(
        self,
        values: List[float],
        labels: List[str],
        title: str = "",
        colors: Optional[List[str]] = None,
        hole: float = 0.3
    ) -> None:
        """
        Create pie/donut chart.

        Args:
            values: Data values
            labels: Labels for each slice
            title: Chart title
            colors: Custom colors (optional)
            hole: Hole size for donut (0 = pie, 0.3 = donut)
        """
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=hole,
            marker=dict(colors=colors or DEFAULT_COLORS[:len(values)]),
            textinfo='label+percent',
            textposition='inside',
            insidetextorientation='radial'
        )])

        fig.update_layout(
            title=dict(text=title, x=0.5, xanchor='center'),
            showlegend=True,
            legend=dict(orientation='h', y=-0.1)
        )

        self._render(fig)

    def bar_chart(
        self,
        x: List[str],
        y: List[float],
        title: str = "",
        x_title: str = "",
        y_title: str = "",
        colors: Optional[List[str]] = None,
        horizontal: bool = False
    ) -> None:
        """
        Create bar chart.

        Args:
            x: X-axis labels
            y: Y-axis values
            title: Chart title
            x_title: X-axis title
            y_title: Y-axis title
            colors: Bar colors
            horizontal: Horizontal bars
        """
        if horizontal:
            fig = go.Figure(data=[go.Bar(
                y=x, x=y,
                orientation='h',
                marker_color=colors or DEFAULT_COLORS[0]
            )])
        else:
            fig = go.Figure(data=[go.Bar(
                x=x, y=y,
                marker_color=colors or DEFAULT_COLORS[0]
            )])

        fig.update_layout(
            title=dict(text=title, x=0.5, xanchor='center'),
            xaxis_title=x_title,
            yaxis_title=y_title
        )

        self._render(fig)

    def grouped_bar_chart(
        self,
        categories: List[str],
        datasets: List[Dict[str, Any]],
        title: str = "",
        x_title: str = "",
        y_title: str = ""
    ) -> None:
        """
        Create grouped bar chart.

        Args:
            categories: X-axis categories
            datasets: List of {"name": str, "values": List[float]}
            title: Chart title
            x_title: X-axis title
            y_title: Y-axis title
        """
        fig = go.Figure()

        for i, dataset in enumerate(datasets):
            fig.add_trace(go.Bar(
                name=dataset['name'],
                x=categories,
                y=dataset['values'],
                marker_color=DEFAULT_COLORS[i % len(DEFAULT_COLORS)]
            ))

        fig.update_layout(
            title=dict(text=title, x=0.5, xanchor='center'),
            xaxis_title=x_title,
            yaxis_title=y_title,
            barmode='group'
        )

        self._render(fig)

    def line_chart(
        self,
        x: List[Any],
        y: List[float],
        title: str = "",
        x_title: str = "",
        y_title: str = "",
        fill: bool = False
    ) -> None:
        """
        Create line chart.

        Args:
            x: X-axis values
            y: Y-axis values
            title: Chart title
            x_title: X-axis title
            y_title: Y-axis title
            fill: Fill area under line
        """
        fig = go.Figure(data=[go.Scatter(
            x=x, y=y,
            mode='lines+markers',
            fill='tozeroy' if fill else None,
            line=dict(color=DEFAULT_COLORS[0], width=2),
            marker=dict(size=8)
        )])

        fig.update_layout(
            title=dict(text=title, x=0.5, xanchor='center'),
            xaxis_title=x_title,
            yaxis_title=y_title
        )

        self._render(fig)

    def multi_line_chart(
        self,
        x: List[Any],
        datasets: List[Dict[str, Any]],
        title: str = "",
        x_title: str = "",
        y_title: str = ""
    ) -> None:
        """
        Create multi-line chart.

        Args:
            x: X-axis values (shared)
            datasets: List of {"name": str, "values": List[float]}
            title: Chart title
            x_title: X-axis title
            y_title: Y-axis title
        """
        fig = go.Figure()

        for i, dataset in enumerate(datasets):
            fig.add_trace(go.Scatter(
                x=x,
                y=dataset['values'],
                name=dataset['name'],
                mode='lines+markers',
                line=dict(color=DEFAULT_COLORS[i % len(DEFAULT_COLORS)])
            ))

        fig.update_layout(
            title=dict(text=title, x=0.5, xanchor='center'),
            xaxis_title=x_title,
            yaxis_title=y_title
        )

        self._render(fig)

    def gauge_chart(
        self,
        value: float,
        title: str = "",
        min_val: float = 0,
        max_val: float = 100,
        threshold_good: float = 70,
        threshold_warning: float = 40
    ) -> None:
        """
        Create gauge/meter chart.

        Args:
            value: Current value
            title: Chart title
            min_val: Minimum value
            max_val: Maximum value
            threshold_good: Value above which is good (green)
            threshold_warning: Value above which is warning (yellow)
        """
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=value,
            title={'text': title},
            gauge={
                'axis': {'range': [min_val, max_val]},
                'bar': {'color': DEFAULT_COLORS[0]},
                'steps': [
                    {'range': [min_val, threshold_warning], 'color': '#fecaca'},
                    {'range': [threshold_warning, threshold_good], 'color': '#fef08a'},
                    {'range': [threshold_good, max_val], 'color': '#bbf7d0'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': value
                }
            }
        ))

        self._render(fig)

    def set_figure(self, fig: go.Figure) -> None:
        """
        Set a custom Plotly figure.

        Args:
            fig: Plotly figure object
        """
        self._render(fig)

    def get_figure(self) -> Optional[go.Figure]:
        """Get current figure."""
        return self._current_figure

    def save_image(self, path: str, format: str = "png") -> bool:
        """
        Save chart as image.

        Args:
            path: Output file path
            format: Image format (png, jpeg, svg, pdf)

        Returns:
            True if successful
        """
        if self._current_figure is None:
            return False

        try:
            self._current_figure.write_image(path, format=format)
            return True
        except Exception as e:
            app_logger.error(f"Failed to save chart image: {e}")
            return False

    def clear(self) -> None:
        """Clear the chart."""
        self._web_view.setHtml("")
        self._current_figure = None


# Convenience functions

def create_pie_chart(
    values: List[float],
    labels: List[str],
    title: str = "",
    parent=None
) -> PlotlyChart:
    """Create and return a pie chart widget."""
    chart = PlotlyChart(parent)
    chart.pie_chart(values, labels, title)
    return chart


def create_bar_chart(
    x: List[str],
    y: List[float],
    title: str = "",
    parent=None
) -> PlotlyChart:
    """Create and return a bar chart widget."""
    chart = PlotlyChart(parent)
    chart.bar_chart(x, y, title)
    return chart


def create_line_chart(
    x: List[Any],
    y: List[float],
    title: str = "",
    parent=None
) -> PlotlyChart:
    """Create and return a line chart widget."""
    chart = PlotlyChart(parent)
    chart.line_chart(x, y, title)
    return chart
