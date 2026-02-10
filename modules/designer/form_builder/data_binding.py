"""
Data Binding Manager
====================
Manages data binding between form widgets and database fields.

Features:
- Database schema discovery (hardcoded fallback + live introspection)
- Dynamic PostgreSQL information_schema introspection
- Column name suggestions for auto-complete
- Data preview for tables
- Field binding configuration
- Data loading and saving
- Validation
- Thread-safe schema access
"""

import threading
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable
from enum import Enum

from PyQt5.QtCore import QObject, pyqtSignal

from core.logging import app_logger


# ══════════════════════════════════════════════════════════════
# Data Types
# ══════════════════════════════════════════════════════════════

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


# Mapping from PostgreSQL data_type strings to DataType enum
_PG_TYPE_MAP: Dict[str, DataType] = {
    "character varying": DataType.STRING,
    "varchar": DataType.STRING,
    "char": DataType.STRING,
    "character": DataType.STRING,
    "text": DataType.STRING,
    "integer": DataType.INTEGER,
    "bigint": DataType.INTEGER,
    "smallint": DataType.INTEGER,
    "serial": DataType.INTEGER,
    "bigserial": DataType.INTEGER,
    "numeric": DataType.DECIMAL,
    "decimal": DataType.DECIMAL,
    "real": DataType.DECIMAL,
    "double precision": DataType.DECIMAL,
    "money": DataType.DECIMAL,
    "boolean": DataType.BOOLEAN,
    "date": DataType.DATE,
    "time without time zone": DataType.TIME,
    "time with time zone": DataType.TIME,
    "time": DataType.TIME,
    "timestamp without time zone": DataType.DATETIME,
    "timestamp with time zone": DataType.DATETIME,
    "timestamp": DataType.DATETIME,
}


# ══════════════════════════════════════════════════════════════
# Data Classes
# ══════════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════════
# DataBindingManager
# ══════════════════════════════════════════════════════════════

class DataBindingManager(QObject):
    """
    Manages data binding for form widgets.

    Features:
    - Discover database schema (hardcoded fallback + live introspection)
    - Bind widgets to database columns
    - Load data into forms
    - Save form data to database
    - Column name suggestions
    - Data preview

    Thread Safety:
    - _schemas is protected by _schemas_lock (Rule #3)
    - _bindings is protected by _bindings_lock (Rule #3)
    """

    # Signal emitted when database introspection completes.
    # Carries a list of discovered table names.
    schema_discovered = pyqtSignal(list)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)

        self._bindings: Dict[str, FieldBinding] = {}
        self._schemas: Dict[str, TableSchema] = {}
        self._validators: Dict[str, Callable] = {}

        # Thread safety locks (Rule #3)
        self._schemas_lock = threading.Lock()
        self._bindings_lock = threading.Lock()

        # Load hardcoded fallback schemas
        self._discover_schemas()

    # ──────────────────────────────────────────────────────────
    # Hardcoded fallback schemas
    # ──────────────────────────────────────────────────────────

    def _discover_schemas(self) -> None:
        """Populate hardcoded fallback schemas for common INTEGRA tables."""
        with self._schemas_lock:
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
                ),
            }

    # ──────────────────────────────────────────────────────────
    # Live database introspection (NEW)
    # ──────────────────────────────────────────────────────────

    def discover_schemas_from_db(self) -> None:
        """
        Query PostgreSQL information_schema to discover all public tables
        and their columns dynamically.

        Runs the actual DB work in a background thread (Rule #13) and emits
        schema_discovered(list[str]) when done.

        Falls back to keeping the hardcoded schemas if the DB is unavailable.
        """
        from core.threading import run_in_background

        run_in_background(
            self._introspect_db,
            on_finished=self._on_introspection_finished,
            on_error=self._on_introspection_error,
            task_name="discover_schemas_from_db",
        )

    def _introspect_db(self) -> Dict[str, TableSchema]:
        """
        Background worker: queries information_schema for tables and columns.

        Returns:
            Dict mapping table_name -> TableSchema
        """
        from core.database.connection import get_connection, return_connection

        conn = get_connection()
        if conn is None:
            app_logger.warning(
                "discover_schemas_from_db: no DB connection, keeping fallback schemas"
            )
            return {}

        cursor = None
        try:
            cursor = conn.cursor()

            # 1. Discover all public base tables
            cursor.execute(
                "SELECT table_name "
                "FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
                "ORDER BY table_name"
            )
            table_rows = cursor.fetchall()

            discovered: Dict[str, TableSchema] = {}

            for (tbl_name,) in table_rows:
                # 2. Discover columns for each table (parameterized - Rule #2)
                cursor.execute(
                    "SELECT column_name, data_type, is_nullable "
                    "FROM information_schema.columns "
                    "WHERE table_schema = 'public' AND table_name = %s "
                    "ORDER BY ordinal_position",
                    (tbl_name,),
                )
                col_rows = cursor.fetchall()

                columns: List[Dict[str, Any]] = []
                for col_name, pg_type, is_nullable in col_rows:
                    data_type = _PG_TYPE_MAP.get(pg_type, DataType.STRING)
                    columns.append({
                        "name": col_name,
                        "type": data_type,
                        "label": col_name,  # default label = column name
                        "nullable": is_nullable == "YES",
                        "pg_type": pg_type,
                    })

                # Use table_name as display_name; existing hardcoded
                # display names will be preserved in the merge step.
                discovered[tbl_name] = TableSchema(
                    table_name=tbl_name,
                    display_name=tbl_name,
                    columns=columns,
                )

            return discovered

        except Exception as e:
            app_logger.error(f"discover_schemas_from_db introspection error: {e}")
            return {}
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception as e:
                    app_logger.error(f"Error closing cursor: {e}")
            return_connection(conn)

    def _on_introspection_finished(self, discovered: Dict[str, TableSchema]) -> None:
        """Merge discovered schemas with existing ones (preserving display names)."""
        if not discovered:
            # DB was unreachable or returned nothing; keep fallback schemas
            app_logger.info("No schemas discovered from DB; keeping fallback schemas")
            with self._schemas_lock:
                table_names = list(self._schemas.keys())
            self.schema_discovered.emit(table_names)
            return

        with self._schemas_lock:
            # Preserve existing Arabic display names when merging
            for tbl_name, schema in discovered.items():
                existing = self._schemas.get(tbl_name)
                if existing is not None:
                    schema.display_name = existing.display_name
                self._schemas[tbl_name] = schema

            table_names = list(self._schemas.keys())

        app_logger.info(
            f"Database introspection complete: {len(table_names)} tables discovered"
        )
        self.schema_discovered.emit(table_names)

    def _on_introspection_error(
        self, error_type: str, message: str, tb: str
    ) -> None:
        """Handle introspection worker error."""
        app_logger.error(
            f"discover_schemas_from_db worker error: {error_type}: {message}\n{tb}"
        )
        # Emit signal with current (fallback) schemas so callers are notified
        with self._schemas_lock:
            table_names = list(self._schemas.keys())
        self.schema_discovered.emit(table_names)

    # ──────────────────────────────────────────────────────────
    # Column suggestions (NEW)
    # ──────────────────────────────────────────────────────────

    def get_column_suggestions(
        self, table_name: str, partial_name: str
    ) -> List[Dict[str, Any]]:
        """
        Suggest matching columns for auto-complete.

        Args:
            table_name: The table to search in.
            partial_name: Partial column name typed by the user.

        Returns:
            List of column dicts whose name starts with (or contains)
            the partial string (case-insensitive).
        """
        with self._schemas_lock:
            schema = self._schemas.get(table_name)

        if schema is None:
            return []

        partial_lower = partial_name.lower()
        suggestions: List[Dict[str, Any]] = []

        for col in schema.columns:
            col_name_lower = col["name"].lower()
            if partial_lower in col_name_lower:
                suggestions.append(col)

        # Sort: columns that *start with* the partial first, then contains
        suggestions.sort(
            key=lambda c: (
                0 if c["name"].lower().startswith(partial_lower) else 1,
                c["name"].lower(),
            )
        )

        return suggestions

    # ──────────────────────────────────────────────────────────
    # Data preview (NEW) - must run in background thread (Rule #13)
    # ──────────────────────────────────────────────────────────

    def preview_data(
        self,
        table_name: str,
        limit: int = 5,
        on_finished: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ) -> None:
        """
        Preview the first N records from a table.

        Runs the query in a background thread (Rule #13) and delivers
        the result via on_finished callback.

        Args:
            table_name: Table to preview (must be in _schemas).
            limit: Maximum number of rows to fetch (default 5).
            on_finished: Callback receiving (columns: List[str], rows: List[tuple]).
            on_error: Callback receiving (error_type, message, traceback).
        """
        from core.threading import run_in_background

        # Validate table_name against known schemas to prevent injection
        with self._schemas_lock:
            if table_name not in self._schemas:
                app_logger.error(f"preview_data: unknown table '{table_name}'")
                if on_error is not None:
                    on_error("ValueError", f"Unknown table: {table_name}", "")
                return

        run_in_background(
            self._fetch_preview,
            args=(table_name, limit),
            on_finished=on_finished,
            on_error=on_error,
            task_name=f"preview_data_{table_name}",
        )

    def _fetch_preview(
        self, table_name: str, limit: int
    ) -> tuple:
        """
        Background worker: fetch preview rows from a table.

        Uses psycopg2.sql for safe identifier quoting (Rule #2).
        Returns connection in finally block (Rule #8).

        Returns:
            (columns: List[str], rows: List[tuple])
        """
        from psycopg2 import sql as psql
        from core.database.connection import get_connection, return_connection

        conn = get_connection()
        if conn is None:
            app_logger.error("preview_data: no database connection")
            return ([], [])

        cursor = None
        try:
            cursor = conn.cursor()

            query = psql.SQL("SELECT * FROM {} LIMIT %s").format(
                psql.Identifier(table_name)
            )
            cursor.execute(query, (limit,))

            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            return (columns, rows)

        except Exception as e:
            app_logger.error(f"preview_data query error for '{table_name}': {e}")
            return ([], [])
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception as e:
                    app_logger.error(f"Error closing cursor in preview_data: {e}")
            return_connection(conn)

    # ──────────────────────────────────────────────────────────
    # Schema access (existing, now thread-safe)
    # ──────────────────────────────────────────────────────────

    def get_tables(self) -> List[TableSchema]:
        """Get available tables."""
        with self._schemas_lock:
            return list(self._schemas.values())

    def get_table(self, table_name: str) -> Optional[TableSchema]:
        """Get table schema by name."""
        with self._schemas_lock:
            return self._schemas.get(table_name)

    def get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Get columns for a table."""
        with self._schemas_lock:
            schema = self._schemas.get(table_name)
        return schema.columns if schema else []

    # ──────────────────────────────────────────────────────────
    # Binding management (existing, now thread-safe)
    # ──────────────────────────────────────────────────────────

    def add_binding(self, binding: FieldBinding) -> None:
        """Add field binding."""
        with self._bindings_lock:
            self._bindings[binding.widget_id] = binding
        app_logger.debug(
            f"Added binding: {binding.widget_id} -> "
            f"{binding.table_name}.{binding.column_name}"
        )

    def remove_binding(self, widget_id: str) -> None:
        """Remove field binding."""
        with self._bindings_lock:
            if widget_id in self._bindings:
                del self._bindings[widget_id]

    def get_binding(self, widget_id: str) -> Optional[FieldBinding]:
        """Get binding for widget."""
        with self._bindings_lock:
            return self._bindings.get(widget_id)

    def get_all_bindings(self) -> Dict[str, FieldBinding]:
        """Get all bindings."""
        with self._bindings_lock:
            return self._bindings.copy()

    # ──────────────────────────────────────────────────────────
    # Data operations (existing, enhanced with lock protection)
    # ──────────────────────────────────────────────────────────

    def load_data(self, table_name: str, record_id: int) -> Dict[str, Any]:
        """
        Load data from database.

        Args:
            table_name: Table name (must exist in _schemas).
            record_id: Record ID.

        Returns:
            Dictionary of column values, or empty dict on failure.
        """
        try:
            from core.database import select_one
            from psycopg2 import sql as psql

            # Validate table_name against known schemas to prevent injection
            with self._schemas_lock:
                if table_name not in self._schemas:
                    app_logger.error(f"load_data: unknown table '{table_name}'")
                    return {}

            query = psql.SQL("SELECT * FROM {} WHERE id = %s").format(
                psql.Identifier(table_name)
            )

            result = select_one(query, (record_id,))

            if result is not None:
                # select_one returns a tuple; we need column names from schema
                with self._schemas_lock:
                    schema = self._schemas.get(table_name)
                if schema is not None:
                    col_names = [c["name"] for c in schema.columns]
                    # If the result has more columns than the schema knows about
                    # (e.g. after introspection added new columns), handle gracefully
                    if len(result) == len(col_names):
                        return dict(zip(col_names, result))

                # Fallback: return indexed dict
                return {f"col_{i}": v for i, v in enumerate(result)}

            return {}

        except Exception as e:
            app_logger.error(f"Failed to load data from '{table_name}': {e}")
            return {}

    def save_data(
        self,
        table_name: str,
        data: Dict[str, Any],
        record_id: Optional[int] = None,
    ) -> Optional[int]:
        """
        Save data to database.

        Args:
            table_name: Table name (must exist in _schemas).
            data: Column values.
            record_id: Record ID for update (None for insert).

        Returns:
            Record ID or None on failure.
        """
        try:
            from core.database import insert_returning_id, update
            from psycopg2 import sql as psql

            # Validate table_name against known schemas to prevent injection
            with self._schemas_lock:
                if table_name not in self._schemas:
                    app_logger.error(f"save_data: unknown table '{table_name}'")
                    return None

            if record_id:
                # Update - use psql.Identifier for table and column names
                set_clause = psql.SQL(", ").join(
                    psql.SQL("{} = %s").format(psql.Identifier(k))
                    for k in data.keys()
                )
                query = psql.SQL("UPDATE {} SET {} WHERE id = %s").format(
                    psql.Identifier(table_name),
                    set_clause,
                )
                update(query, (*data.values(), record_id))
                return record_id
            else:
                # Insert - use psql.Identifier for table and column names
                columns = psql.SQL(", ").join(
                    psql.Identifier(k) for k in data.keys()
                )
                placeholders = psql.SQL(", ").join(
                    psql.Placeholder() for _ in data
                )
                query = psql.SQL(
                    "INSERT INTO {} ({}) VALUES ({}) RETURNING id"
                ).format(
                    psql.Identifier(table_name),
                    columns,
                    placeholders,
                )
                return insert_returning_id(query, tuple(data.values()))

        except Exception as e:
            app_logger.error(f"Failed to save data to '{table_name}': {e}")
            return None

    # ──────────────────────────────────────────────────────────
    # Validation (existing)
    # ──────────────────────────────────────────────────────────

    def validate_data(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate data against bindings.

        Args:
            data: Data to validate.

        Returns:
            List of error messages.
        """
        errors: List[str] = []

        with self._bindings_lock:
            bindings_snapshot = list(self._bindings.items())

        for widget_id, binding in bindings_snapshot:
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
                        errors.append(
                            f"الحقل {binding.column_name} يجب أن يكون رقما صحيحا"
                        )

                elif binding.data_type == DataType.DECIMAL:
                    try:
                        float(value)
                    except (ValueError, TypeError):
                        errors.append(
                            f"الحقل {binding.column_name} يجب أن يكون رقما"
                        )

        return errors

    # ──────────────────────────────────────────────────────────
    # Serialization (existing)
    # ──────────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Export bindings to dictionary."""
        with self._bindings_lock:
            bindings_list = list(self._bindings.values())

        return {
            "bindings": [
                {
                    "widget_id": b.widget_id,
                    "table_name": b.table_name,
                    "column_name": b.column_name,
                    "data_type": b.data_type.value,
                    "required": b.required,
                    "default_value": b.default_value,
                    "format_string": b.format_string,
                }
                for b in bindings_list
            ]
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Import bindings from dictionary."""
        with self._bindings_lock:
            self._bindings.clear()

            for binding_data in data.get("bindings", []):
                try:
                    data_type = DataType(binding_data.get("data_type", "string"))
                except ValueError:
                    app_logger.error(
                        f"Unknown data type '{binding_data.get('data_type')}', "
                        f"defaulting to STRING"
                    )
                    data_type = DataType.STRING

                binding = FieldBinding(
                    widget_id=binding_data.get("widget_id", ""),
                    table_name=binding_data.get("table_name", ""),
                    column_name=binding_data.get("column_name", ""),
                    data_type=data_type,
                    required=binding_data.get("required", False),
                    default_value=binding_data.get("default_value"),
                    format_string=binding_data.get("format_string"),
                )
                self._bindings[binding.widget_id] = binding
