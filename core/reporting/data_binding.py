"""
Data Binding System
===================
Connect reports and forms to database data sources.

Features:
- Database query binding
- Data transformations
- Aggregation functions
- Parameters and filters
- Caching support
- Virtual/computed fields
"""

from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, date
from decimal import Decimal
import re

from core.logging import app_logger


class DataSourceType(Enum):
    """Data source types."""
    DATABASE = "database"
    QUERY = "query"
    FUNCTION = "function"
    STATIC = "static"
    API = "api"


class AggregationType(Enum):
    """Aggregation functions."""
    SUM = "sum"
    AVG = "avg"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    FIRST = "first"
    LAST = "last"
    GROUP_CONCAT = "group_concat"


class SortDirection(Enum):
    """Sort direction."""
    ASC = "asc"
    DESC = "desc"


@dataclass
class FieldBinding:
    """
    Binding configuration for a single field.

    Maps a source field to a target field with optional transformations.
    """

    # Source
    source_field: str
    source_table: str = ""

    # Target
    target_field: str = ""

    # Display
    label: str = ""
    format_type: str = ""  # currency, date, number, percentage, etc.
    format_options: Dict[str, Any] = field(default_factory=dict)

    # Transformation
    transform: Optional[Callable] = None
    default_value: Any = None

    # Computed
    is_computed: bool = False
    expression: str = ""

    # Aggregation
    aggregate: Optional[AggregationType] = None
    group_by: str = ""

    def __post_init__(self):
        if not self.target_field:
            self.target_field = self.source_field
        if not self.label:
            self.label = self.source_field


@dataclass
class FilterCondition:
    """Filter condition for data binding."""

    field: str
    operator: str  # =, !=, <, >, <=, >=, LIKE, IN, BETWEEN, IS NULL
    value: Any = None
    value2: Any = None  # For BETWEEN
    parameter: str = ""  # Parameter name if value comes from param


@dataclass
class SortOrder:
    """Sort order for data binding."""

    field: str
    direction: SortDirection = SortDirection.ASC


@dataclass
class DataSourceConfig:
    """
    Data source configuration.

    Defines how to fetch data for reports/forms.
    """

    # Identification
    name: str = ""
    source_type: DataSourceType = DataSourceType.DATABASE

    # Database source
    table: str = ""
    query: str = ""
    stored_procedure: str = ""

    # Joins
    joins: List[Dict[str, str]] = field(default_factory=list)

    # Fields
    fields: List[FieldBinding] = field(default_factory=list)
    field_names: List[str] = field(default_factory=list)

    # Filters
    filters: List[FilterCondition] = field(default_factory=list)

    # Sorting
    order_by: List[SortOrder] = field(default_factory=list)

    # Grouping
    group_by: List[str] = field(default_factory=list)

    # Pagination
    limit: int = 0
    offset: int = 0

    # Parameters
    parameters: Dict[str, Any] = field(default_factory=dict)

    # Caching
    cache_enabled: bool = True
    cache_ttl: int = 300  # seconds

    # Function source
    data_function: Optional[Callable] = None

    # Static data
    static_data: List[Dict] = field(default_factory=list)


class DataBindingManager:
    """
    Manages data binding for reports and forms.

    Handles data fetching, transformation, and formatting.
    """

    def __init__(self):
        """Initialize data binding manager."""
        self._sources: Dict[str, DataSourceConfig] = {}
        self._cache: Dict[str, tuple] = {}  # key: (data, timestamp)
        self._formatters: Dict[str, Callable] = {}
        self._transformers: Dict[str, Callable] = {}

        self._register_default_formatters()
        self._register_default_transformers()

        app_logger.info("DataBindingManager initialized")

    def _register_default_formatters(self) -> None:
        """Register default field formatters."""
        from .filters import (
            format_currency, format_number, format_date,
            format_datetime, format_percentage, yesno, phone_format
        )

        self._formatters = {
            "currency": format_currency,
            "number": format_number,
            "date": format_date,
            "datetime": format_datetime,
            "percentage": format_percentage,
            "boolean": yesno,
            "phone": phone_format
        }

    def _register_default_transformers(self) -> None:
        """Register default data transformers."""
        self._transformers = {
            "upper": lambda x: str(x).upper() if x else "",
            "lower": lambda x: str(x).lower() if x else "",
            "strip": lambda x: str(x).strip() if x else "",
            "title": lambda x: str(x).title() if x else "",
            "int": lambda x: int(x) if x is not None else 0,
            "float": lambda x: float(x) if x is not None else 0.0,
            "str": lambda x: str(x) if x is not None else "",
            "bool": lambda x: bool(x) if x is not None else False,
        }

    def register_source(self, config: DataSourceConfig) -> None:
        """
        Register a data source.

        Args:
            config: Data source configuration
        """
        self._sources[config.name] = config
        app_logger.debug(f"Registered data source: {config.name}")

    def unregister_source(self, name: str) -> None:
        """
        Unregister a data source.

        Args:
            name: Source name
        """
        if name in self._sources:
            del self._sources[name]
            self._invalidate_cache(name)

    def register_formatter(self, name: str, formatter: Callable) -> None:
        """
        Register a custom formatter.

        Args:
            name: Formatter name
            formatter: Formatter function
        """
        self._formatters[name] = formatter

    def register_transformer(self, name: str, transformer: Callable) -> None:
        """
        Register a custom transformer.

        Args:
            name: Transformer name
            transformer: Transformer function
        """
        self._transformers[name] = transformer

    def fetch_data(
        self,
        source_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Fetch data from a registered source.

        Args:
            source_name: Source name
            parameters: Query parameters
            use_cache: Whether to use cache

        Returns:
            List of data dictionaries
        """
        if source_name not in self._sources:
            raise ValueError(f"Unknown data source: {source_name}")

        config = self._sources[source_name]
        params = {**config.parameters, **(parameters or {})}

        # Check cache
        cache_key = f"{source_name}:{hash(str(sorted(params.items())))}"
        if use_cache and config.cache_enabled:
            cached = self._get_from_cache(cache_key, config.cache_ttl)
            if cached is not None:
                return cached

        # Fetch based on source type
        if config.source_type == DataSourceType.DATABASE:
            data = self._fetch_from_database(config, params)
        elif config.source_type == DataSourceType.QUERY:
            data = self._fetch_from_query(config, params)
        elif config.source_type == DataSourceType.FUNCTION:
            data = self._fetch_from_function(config, params)
        elif config.source_type == DataSourceType.STATIC:
            data = config.static_data
        else:
            data = []

        # Apply transformations
        data = self._apply_transformations(data, config)

        # Cache result
        if config.cache_enabled:
            self._cache[cache_key] = (data, datetime.now())

        return data

    def _fetch_from_database(
        self,
        config: DataSourceConfig,
        params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Fetch data from database table."""
        try:
            from core.database import select_all

            # Build field list
            fields = "*"
            if config.field_names:
                fields = ", ".join(config.field_names)
            elif config.fields:
                fields = ", ".join(f.source_field for f in config.fields)

            # Build query
            query = f"SELECT {fields} FROM {config.table}"

            # Add joins
            for join in config.joins:
                join_type = join.get("type", "INNER")
                query += f" {join_type} JOIN {join['table']} ON {join['on']}"

            # Add filters
            where_clauses = []
            query_params = []

            for filter_cond in config.filters:
                clause, param = self._build_filter_clause(filter_cond, params)
                if clause:
                    where_clauses.append(clause)
                    if param is not None:
                        query_params.append(param)

            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)

            # Add GROUP BY
            if config.group_by:
                query += " GROUP BY " + ", ".join(config.group_by)

            # Add ORDER BY
            if config.order_by:
                order_clauses = [
                    f"{o.field} {o.direction.value}"
                    for o in config.order_by
                ]
                query += " ORDER BY " + ", ".join(order_clauses)

            # Add LIMIT/OFFSET
            if config.limit > 0:
                query += f" LIMIT {config.limit}"
            if config.offset > 0:
                query += f" OFFSET {config.offset}"

            # Execute
            columns, rows = select_all(query, tuple(query_params) if query_params else None)

            # Convert to dicts
            return [dict(zip(columns, row)) for row in rows]

        except Exception as e:
            app_logger.error(f"Database fetch error: {e}")
            return []

    def _fetch_from_query(
        self,
        config: DataSourceConfig,
        params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Fetch data from raw query."""
        try:
            from core.database import select_all

            query = config.query

            # Replace named parameters
            query_params = []
            for name, value in params.items():
                placeholder = f":{name}"
                if placeholder in query:
                    query = query.replace(placeholder, "%s")
                    query_params.append(value)

            columns, rows = select_all(query, tuple(query_params) if query_params else None)
            return [dict(zip(columns, row)) for row in rows]

        except Exception as e:
            app_logger.error(f"Query fetch error: {e}")
            return []

    def _fetch_from_function(
        self,
        config: DataSourceConfig,
        params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Fetch data from function."""
        try:
            if config.data_function:
                result = config.data_function(**params)
                if isinstance(result, list):
                    return result
                elif isinstance(result, dict):
                    return [result]
            return []

        except Exception as e:
            app_logger.error(f"Function fetch error: {e}")
            return []

    def _build_filter_clause(
        self,
        filter_cond: FilterCondition,
        params: Dict[str, Any]
    ) -> tuple:
        """Build SQL filter clause."""
        field = filter_cond.field
        op = filter_cond.operator.upper()

        # Get value from params if specified
        value = filter_cond.value
        if filter_cond.parameter:
            value = params.get(filter_cond.parameter, value)

        if op == "IS NULL":
            return f"{field} IS NULL", None
        elif op == "IS NOT NULL":
            return f"{field} IS NOT NULL", None
        elif op == "IN":
            if isinstance(value, (list, tuple)):
                placeholders = ", ".join(["%s"] * len(value))
                return f"{field} IN ({placeholders})", value
        elif op == "BETWEEN":
            value2 = filter_cond.value2
            return f"{field} BETWEEN %s AND %s", (value, value2)
        elif op == "LIKE":
            return f"{field} LIKE %s", value
        else:
            return f"{field} {op} %s", value

    def _apply_transformations(
        self,
        data: List[Dict[str, Any]],
        config: DataSourceConfig
    ) -> List[Dict[str, Any]]:
        """Apply field transformations."""
        if not config.fields:
            return data

        result = []
        for row in data:
            transformed = {}

            for binding in config.fields:
                # Get source value
                value = row.get(binding.source_field, binding.default_value)

                # Apply transform
                if binding.transform:
                    value = binding.transform(value)

                # Compute expression
                if binding.is_computed and binding.expression:
                    value = self._evaluate_expression(binding.expression, row)

                # Apply formatter
                if binding.format_type and binding.format_type in self._formatters:
                    formatter = self._formatters[binding.format_type]
                    value = formatter(value, **binding.format_options)

                transformed[binding.target_field] = value

            # Include unmapped fields
            for key, value in row.items():
                if key not in transformed:
                    transformed[key] = value

            result.append(transformed)

        return result

    def _evaluate_expression(self, expression: str, row: Dict[str, Any]) -> Any:
        """
        Evaluate a computed expression.

        Supports basic math and field references.
        """
        try:
            # Replace field references with values
            expr = expression
            for key, value in row.items():
                if isinstance(value, (int, float, Decimal)):
                    expr = expr.replace(f"{{{key}}}", str(value))
                elif value is None:
                    expr = expr.replace(f"{{{key}}}", "0")

            # Safe evaluation (limited operations)
            allowed = {
                'abs': abs, 'min': min, 'max': max,
                'round': round, 'sum': sum
            }
            return eval(expr, {"__builtins__": {}}, allowed)

        except Exception as e:
            app_logger.warning(f"Expression evaluation failed: {expression} - {e}")
            return None

    def _get_from_cache(self, key: str, ttl: int) -> Optional[List[Dict]]:
        """Get data from cache if valid."""
        if key not in self._cache:
            return None

        data, timestamp = self._cache[key]
        if (datetime.now() - timestamp).total_seconds() > ttl:
            del self._cache[key]
            return None

        return data

    def _invalidate_cache(self, source_name: str) -> None:
        """Invalidate cache for a source."""
        keys_to_remove = [k for k in self._cache if k.startswith(f"{source_name}:")]
        for key in keys_to_remove:
            del self._cache[key]

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()

    def aggregate_data(
        self,
        data: List[Dict[str, Any]],
        field: str,
        aggregation: AggregationType,
        group_by: Optional[str] = None
    ) -> Union[Any, Dict[str, Any]]:
        """
        Aggregate data.

        Args:
            data: Data to aggregate
            field: Field to aggregate
            aggregation: Aggregation function
            group_by: Optional grouping field

        Returns:
            Aggregated value or grouped results
        """
        if not data:
            return 0 if aggregation != AggregationType.GROUP_CONCAT else ""

        if group_by:
            # Group and aggregate
            groups: Dict[str, List] = {}
            for row in data:
                key = row.get(group_by, "")
                if key not in groups:
                    groups[key] = []
                groups[key].append(row)

            return {
                key: self._aggregate_values(
                    [r.get(field) for r in rows],
                    aggregation
                )
                for key, rows in groups.items()
            }
        else:
            # Simple aggregation
            values = [row.get(field) for row in data]
            return self._aggregate_values(values, aggregation)

    def _aggregate_values(self, values: List[Any], aggregation: AggregationType) -> Any:
        """Apply aggregation to values."""
        # Filter out None values for numeric operations
        numeric_values = [
            float(v) for v in values
            if v is not None and isinstance(v, (int, float, Decimal))
        ]

        if aggregation == AggregationType.SUM:
            return sum(numeric_values) if numeric_values else 0
        elif aggregation == AggregationType.AVG:
            return sum(numeric_values) / len(numeric_values) if numeric_values else 0
        elif aggregation == AggregationType.COUNT:
            return len(values)
        elif aggregation == AggregationType.MIN:
            return min(numeric_values) if numeric_values else 0
        elif aggregation == AggregationType.MAX:
            return max(numeric_values) if numeric_values else 0
        elif aggregation == AggregationType.FIRST:
            return values[0] if values else None
        elif aggregation == AggregationType.LAST:
            return values[-1] if values else None
        elif aggregation == AggregationType.GROUP_CONCAT:
            return ", ".join(str(v) for v in values if v is not None)

        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "sources": {
                name: {
                    "name": cfg.name,
                    "source_type": cfg.source_type.value,
                    "table": cfg.table,
                    "query": cfg.query,
                    "field_names": cfg.field_names,
                    "parameters": cfg.parameters,
                    "cache_enabled": cfg.cache_enabled
                }
                for name, cfg in self._sources.items()
            }
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Deserialize from dictionary."""
        self._sources.clear()

        for name, source_data in data.get("sources", {}).items():
            config = DataSourceConfig(
                name=source_data.get("name", name),
                source_type=DataSourceType(source_data.get("source_type", "database")),
                table=source_data.get("table", ""),
                query=source_data.get("query", ""),
                field_names=source_data.get("field_names", []),
                parameters=source_data.get("parameters", {}),
                cache_enabled=source_data.get("cache_enabled", True)
            )
            self._sources[name] = config


# Pre-configured data sources for common INTEGRA entities
def create_employee_source(
    filters: Optional[List[FilterCondition]] = None,
    include_inactive: bool = False
) -> DataSourceConfig:
    """Create employee data source configuration."""
    default_filters = [] if include_inactive else [
        FilterCondition(
            field="employees.status_id",
            operator="=",
            value=1
        )
    ]

    return DataSourceConfig(
        name="employees",
        source_type=DataSourceType.DATABASE,
        table="employees",
        joins=[
            {"table": "companies", "on": "employees.company_id = companies.id", "type": "LEFT"},
            {"table": "departments", "on": "employees.department_id = departments.id", "type": "LEFT"},
            {"table": "job_titles", "on": "employees.job_title_id = job_titles.id", "type": "LEFT"},
            {"table": "employee_statuses", "on": "employees.status_id = employee_statuses.id", "type": "LEFT"}
        ],
        fields=[
            FieldBinding(source_field="employees.id", target_field="id"),
            FieldBinding(source_field="employees.employee_number", target_field="employee_number", label="الرقم الوظيفي"),
            FieldBinding(source_field="employees.name", target_field="name", label="الاسم"),
            FieldBinding(source_field="companies.name", target_field="company", label="الشركة"),
            FieldBinding(source_field="departments.name", target_field="department", label="القسم"),
            FieldBinding(source_field="job_titles.name", target_field="job_title", label="المسمى الوظيفي"),
            FieldBinding(source_field="employees.hire_date", target_field="hire_date", label="تاريخ التعيين", format_type="date"),
            FieldBinding(source_field="employees.basic_salary", target_field="salary", label="الراتب", format_type="currency"),
            FieldBinding(source_field="employee_statuses.name", target_field="status", label="الحالة"),
        ],
        filters=(filters or []) + default_filters,
        order_by=[SortOrder(field="employees.name", direction=SortDirection.ASC)]
    )


def create_department_source() -> DataSourceConfig:
    """Create department data source configuration."""
    return DataSourceConfig(
        name="departments",
        source_type=DataSourceType.DATABASE,
        table="departments",
        joins=[
            {"table": "companies", "on": "departments.company_id = companies.id", "type": "LEFT"}
        ],
        fields=[
            FieldBinding(source_field="departments.id", target_field="id"),
            FieldBinding(source_field="departments.name", target_field="name", label="القسم"),
            FieldBinding(source_field="companies.name", target_field="company", label="الشركة"),
        ],
        order_by=[SortOrder(field="departments.name", direction=SortDirection.ASC)]
    )


def create_company_source() -> DataSourceConfig:
    """Create company data source configuration."""
    return DataSourceConfig(
        name="companies",
        source_type=DataSourceType.DATABASE,
        table="companies",
        fields=[
            FieldBinding(source_field="id", target_field="id"),
            FieldBinding(source_field="name", target_field="name", label="الشركة"),
            FieldBinding(source_field="commercial_registration", target_field="cr", label="السجل التجاري"),
            FieldBinding(source_field="tax_number", target_field="tax", label="الرقم الضريبي"),
        ],
        order_by=[SortOrder(field="name", direction=SortDirection.ASC)]
    )


# Singleton instance
_binding_manager: Optional[DataBindingManager] = None


def get_data_binding_manager() -> DataBindingManager:
    """Get singleton data binding manager instance."""
    global _binding_manager
    if _binding_manager is None:
        _binding_manager = DataBindingManager()
    return _binding_manager
