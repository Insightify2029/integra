"""
Data Binding Manager
====================
Manages data binding between form widgets and database fields.

Features:
- Database schema discovery
- Field binding configuration
- Data loading and saving
- Validation
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable
from enum import Enum

from core.logging import app_logger


class DataType(Enum):
    """Data types for binding."""
    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    TEXT = "text"


@dataclass
class FieldBinding:
    """Field binding configuration."""
    widget_id: str
    table_name: str
    column_name: str
    data_type: DataType = DataType.STRING
    required: bool = False
    default_value: Any = None
    format_string: Optional[str] = None


@dataclass
class TableSchema:
    """Database table schema."""
    table_name: str
    display_name: str
    columns: List[Dict[str, Any]]


class DataBindingManager:
    """
    Manages data binding for form widgets.

    Features:
    - Discover database schema
    - Bind widgets to database columns
    - Load data into forms
    - Save form data to database
    """

    def __init__(self):
        self._bindings: Dict[str, FieldBinding] = {}
        self._schemas: Dict[str, TableSchema] = {}
        self._validators: Dict[str, Callable] = {}

        self._discover_schemas()

    def _discover_schemas(self) -> None:
        """Discover available database schemas."""
        # Common INTEGRA tables
        self._schemas = {
            "employees": TableSchema(
                table_name="employees",
                display_name="الموظفين",
                columns=[
                    {"name": "id", "type": DataType.INTEGER, "label": "المعرّف"},
                    {"name": "name_ar", "type": DataType.STRING, "label": "الاسم بالعربي"},
                    {"name": "name_en", "type": DataType.STRING, "label": "الاسم بالإنجليزي"},
                    {"name": "employee_number", "type": DataType.STRING, "label": "رقم الموظف"},
                    {"name": "department_id", "type": DataType.INTEGER, "label": "القسم"},
                    {"name": "job_title_id", "type": DataType.INTEGER, "label": "المسمى الوظيفي"},
                    {"name": "salary", "type": DataType.DECIMAL, "label": "الراتب"},
                    {"name": "hire_date", "type": DataType.DATE, "label": "تاريخ التعيين"},
                    {"name": "phone", "type": DataType.STRING, "label": "الهاتف"},
                    {"name": "email", "type": DataType.STRING, "label": "البريد الإلكتروني"},
                    {"name": "iban", "type": DataType.STRING, "label": "رقم الحساب"},
                    {"name": "status_id", "type": DataType.INTEGER, "label": "الحالة"},
                ]
            ),
            "departments": TableSchema(
                table_name="departments",
                display_name="الأقسام",
                columns=[
                    {"name": "id", "type": DataType.INTEGER, "label": "المعرّف"},
                    {"name": "name", "type": DataType.STRING, "label": "اسم القسم"},
                    {"name": "manager_id", "type": DataType.INTEGER, "label": "المدير"},
                ]
            ),
            "companies": TableSchema(
                table_name="companies",
                display_name="الشركات",
                columns=[
                    {"name": "id", "type": DataType.INTEGER, "label": "المعرّف"},
                    {"name": "name", "type": DataType.STRING, "label": "اسم الشركة"},
                    {"name": "address", "type": DataType.TEXT, "label": "العنوان"},
                    {"name": "phone", "type": DataType.STRING, "label": "الهاتف"},
                ]
            )
        }

    def get_tables(self) -> List[TableSchema]:
        """Get available tables."""
        return list(self._schemas.values())

    def get_table(self, table_name: str) -> Optional[TableSchema]:
        """Get table schema by name."""
        return self._schemas.get(table_name)

    def get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Get columns for a table."""
        schema = self._schemas.get(table_name)
        return schema.columns if schema else []

    def add_binding(self, binding: FieldBinding) -> None:
        """Add field binding."""
        self._bindings[binding.widget_id] = binding
        app_logger.debug(f"Added binding: {binding.widget_id} -> {binding.table_name}.{binding.column_name}")

    def remove_binding(self, widget_id: str) -> None:
        """Remove field binding."""
        if widget_id in self._bindings:
            del self._bindings[widget_id]

    def get_binding(self, widget_id: str) -> Optional[FieldBinding]:
        """Get binding for widget."""
        return self._bindings.get(widget_id)

    def get_all_bindings(self) -> Dict[str, FieldBinding]:
        """Get all bindings."""
        return self._bindings.copy()

    def load_data(self, table_name: str, record_id: int) -> Dict[str, Any]:
        """
        Load data from database.

        Args:
            table_name: Table name
            record_id: Record ID

        Returns:
            Dictionary of column values
        """
        try:
            from core.database import select_one
            from psycopg2 import sql

            # Validate table_name against known schemas to prevent injection
            if table_name not in self._schemas:
                app_logger.error(f"Unknown table: {table_name}")
                return {}

            query = sql.SQL("SELECT * FROM {} WHERE id = %s").format(
                sql.Identifier(table_name)
            )

            columns, row = select_one(query, (record_id,))

            if row:
                return dict(zip(columns, row))

            return {}

        except Exception as e:
            app_logger.error(f"Failed to load data: {e}")
            return {}

    def save_data(
        self,
        table_name: str,
        data: Dict[str, Any],
        record_id: int = None
    ) -> Optional[int]:
        """
        Save data to database.

        Args:
            table_name: Table name
            data: Column values
            record_id: Record ID for update (None for insert)

        Returns:
            Record ID or None on failure
        """
        try:
            from core.database import insert_returning_id, update
            from psycopg2 import sql

            # Validate table_name against known schemas to prevent injection
            if table_name not in self._schemas:
                app_logger.error(f"Unknown table: {table_name}")
                return None

            if record_id:
                # Update - use sql.Identifier for table and column names
                set_clause = sql.SQL(", ").join(
                    sql.SQL("{} = %s").format(sql.Identifier(k))
                    for k in data.keys()
                )
                query = sql.SQL("UPDATE {} SET {} WHERE id = %s").format(
                    sql.Identifier(table_name),
                    set_clause
                )
                update(query, (*data.values(), record_id))
                return record_id
            else:
                # Insert - use sql.Identifier for table and column names
                columns = sql.SQL(", ").join(
                    sql.Identifier(k) for k in data.keys()
                )
                placeholders = sql.SQL(", ").join(
                    sql.Placeholder() for _ in data
                )
                query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING id").format(
                    sql.Identifier(table_name),
                    columns,
                    placeholders
                )
                return insert_returning_id(query, tuple(data.values()))

        except Exception as e:
            app_logger.error(f"Failed to save data: {e}")
            return None

    def validate_data(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate data against bindings.

        Args:
            data: Data to validate

        Returns:
            List of error messages
        """
        errors = []

        for widget_id, binding in self._bindings.items():
            value = data.get(binding.column_name)

            # Required check
            if binding.required and (value is None or value == ""):
                errors.append(f"الحقل {binding.column_name} مطلوب")

            # Type check
            if value is not None and value != "":
                if binding.data_type == DataType.INTEGER:
                    try:
                        int(value)
                    except (ValueError, TypeError):
                        errors.append(f"الحقل {binding.column_name} يجب أن يكون رقماً صحيحاً")

                elif binding.data_type == DataType.DECIMAL:
                    try:
                        float(value)
                    except (ValueError, TypeError):
                        errors.append(f"الحقل {binding.column_name} يجب أن يكون رقماً")

        return errors

    def to_dict(self) -> Dict:
        """Export bindings to dictionary."""
        return {
            "bindings": [
                {
                    "widget_id": b.widget_id,
                    "table_name": b.table_name,
                    "column_name": b.column_name,
                    "data_type": b.data_type.value,
                    "required": b.required,
                    "default_value": b.default_value,
                    "format_string": b.format_string
                }
                for b in self._bindings.values()
            ]
        }

    def from_dict(self, data: Dict) -> None:
        """Import bindings from dictionary."""
        self._bindings.clear()

        for binding_data in data.get("bindings", []):
            binding = FieldBinding(
                widget_id=binding_data.get("widget_id", ""),
                table_name=binding_data.get("table_name", ""),
                column_name=binding_data.get("column_name", ""),
                data_type=DataType(binding_data.get("data_type", "string")),
                required=binding_data.get("required", False),
                default_value=binding_data.get("default_value"),
                format_string=binding_data.get("format_string")
            )
            self._bindings[binding.widget_id] = binding
