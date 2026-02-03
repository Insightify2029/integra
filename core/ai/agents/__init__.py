"""
AI Agents
=========
Specialized agents for different tasks.
"""

from .data_agent import (
    DataAgent,
    get_data_agent,
    analyze_employees,
    analyze_salaries,
    find_anomalies,
    generate_insights
)

__all__ = [
    'DataAgent',
    'get_data_agent',
    'analyze_employees',
    'analyze_salaries',
    'find_anomalies',
    'generate_insights'
]
