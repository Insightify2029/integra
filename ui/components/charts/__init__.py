"""
Charts Components
=================
Interactive chart widgets using Plotly.

Usage:
    from ui.components.charts import PlotlyChart, create_pie_chart

    # Create chart widget
    chart = PlotlyChart(self)
    chart.pie_chart(values, labels, title)
    layout.addWidget(chart)

    # Or use convenience functions
    chart = create_pie_chart(values, labels, title, parent=self)
"""

from .plotly_widget import (
    PlotlyChart,
    create_pie_chart,
    create_bar_chart,
    create_line_chart,
    DEFAULT_COLORS
)

__all__ = [
    'PlotlyChart',
    'create_pie_chart',
    'create_bar_chart',
    'create_line_chart',
    'DEFAULT_COLORS'
]
