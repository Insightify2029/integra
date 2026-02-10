"""
Form Data Bridge for INTEGRA FormRenderer.

Provides the interface between the form and the database:
- Load records from DB → populate form fields
- Save form data → INSERT or UPDATE in DB
- Load combo box data from queries (async)
- Check unique constraints (async)
- Delete records with confirmation

All database operations run in background threads (Rule #13)
using parameterized queries (Rule #2) with proper connection
management (Rule #8) and error logging (Rule #9).
"""

from __future__ import annotations

import re
import threading
from typing import Any, Optional

from PyQt5.QtCore import QObject, pyqtSignal

from psycopg2 import sql as psql

from core.logging import app_logger, audit_logger
from core.database import (
    select_all,
    select_one,
    insert_returning_id,
    update_returning_count,
    delete_returning_count,
    get_scalar,
)
from core.threading import run_in_background

# Regex to detect dangerous SQL keywords (case-insensitive, word-boundary)
_DANGEROUS_SQL_RE = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|EXEC|EXECUTE|GRANT|REVOKE"
    r"|COPY|LOAD|REPLACE|MERGE|CALL|SET|COMMIT|ROLLBACK|SAVEPOINT)\b",
    re.IGNORECASE,
)


class FormDataBridge(QObject):
    """
    Bridge between the form UI and the PostgreSQL database.

    All operations are asynchronous and communicate results through
    Qt signals.

    Signals:
        record_loaded(dict): Emitted when a record is loaded from DB.
        record_saved(int, dict): Emitted with (record_id, data) on save.
        record_deleted(int): Emitted with record_id on delete.
        combo_data_loaded(str, list): Emitted with (field_id, items) for combo.
        unique_checked(str, bool): Emitted with (field_id, is_unique).
        error_occurred(str, str): Emitted with (operation, error_message).
    """

    record_loaded = pyqtSignal(dict)
    record_saved = pyqtSignal(int, dict)
    record_deleted = pyqtSignal(int)
    combo_data_loaded = pyqtSignal(str, list)
    unique_checked = pyqtSignal(str, bool)
    error_occurred = pyqtSignal(str, str)

    # Lock for thread-safe access to class-level _ALLOWED_TABLES (Rule #3)
    _table_lock = threading.Lock()

    # Allowed tables to prevent injection through dynamic table names
    _ALLOWED_TABLES: set[str] = {
        "employees", "companies", "departments", "job_titles",
        "nationalities", "banks", "employee_statuses",
    }

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._lock = threading.Lock()

    # -----------------------------------------------------------------------
    # Table whitelist management
    # -----------------------------------------------------------------------

    @classmethod
    def register_table(cls, table_name: str) -> None:
        """Register an additional allowed table name (thread-safe)."""
        with cls._table_lock:
            cls._ALLOWED_TABLES.add(table_name)

    def _validate_table(self, table_name: str) -> bool:
        """Check if a table name is in the whitelist (thread-safe)."""
        with self._table_lock:
            allowed = table_name in self._ALLOWED_TABLES
        if not allowed:
            app_logger.error(f"Table '{table_name}' is not in the allowed tables list")
        return allowed

    # -----------------------------------------------------------------------
    # Load record
    # -----------------------------------------------------------------------

    def load_record(
        self,
        table: str,
        record_id: int,
        columns: Optional[list[str]] = None,
    ) -> None:
        """
        Load a single record from the database asynchronously.

        Args:
            table: Table name (must be in allowed list).
            record_id: Primary key value.
            columns: Optional list of columns to fetch. None = all.
        """
        if not self._validate_table(table):
            self.error_occurred.emit("load", f"Table '{table}' not allowed")
            return

        def _do_load() -> dict:
            if columns:
                cols_sql = psql.SQL(", ").join(
                    psql.Identifier(c) for c in columns
                )
                query = psql.SQL("SELECT {} FROM {} WHERE id = %s").format(
                    cols_sql, psql.Identifier(table)
                )
            else:
                query = psql.SQL("SELECT * FROM {} WHERE id = %s").format(
                    psql.Identifier(table)
                )

            col_names, rows = select_all(query.as_string(None), (record_id,))
            if rows:
                return dict(zip(col_names, rows[0]))
            return {}

        def _on_finished(result: dict) -> None:
            if result:
                self.record_loaded.emit(result)
                app_logger.info(f"Loaded record {record_id} from '{table}'")
            else:
                self.error_occurred.emit(
                    "load", f"Record {record_id} not found in '{table}'"
                )

        def _on_error(error_type: str, message: str, tb: str) -> None:
            app_logger.error(f"Error loading record: {message}")
            self.error_occurred.emit("load", message)

        run_in_background(
            _do_load,
            on_finished=_on_finished,
            on_error=_on_error,
        )

    # -----------------------------------------------------------------------
    # Save record (INSERT or UPDATE)
    # -----------------------------------------------------------------------

    def save_record(
        self,
        table: str,
        data: dict[str, Any],
        record_id: Optional[int] = None,
    ) -> None:
        """
        Save form data to the database asynchronously.

        If record_id is provided, performs UPDATE. Otherwise INSERT.

        Args:
            table: Table name (must be in allowed list).
            data: Dict mapping column_name -> value.
            record_id: Record ID for update, None for insert.
        """
        if not self._validate_table(table):
            self.error_occurred.emit("save", f"Table '{table}' not allowed")
            return

        if not data:
            self.error_occurred.emit("save", "No data to save")
            return

        def _do_save() -> tuple[int, dict]:
            if record_id is not None:
                return self._do_update(table, data, record_id)
            else:
                return self._do_insert(table, data)

        def _on_finished(result: tuple[int, dict]) -> None:
            rid, saved_data = result
            if rid > 0:
                self.record_saved.emit(rid, saved_data)
                app_logger.info(f"Saved record {rid} in '{table}'")

                # Audit log
                try:
                    action = "UPDATE" if record_id else "INSERT"
                    audit_logger.log(
                        action=action,
                        entity=table,
                        entity_id=rid,
                        details=f"{action} record in {table}",
                        new_values=saved_data,
                    )
                except Exception:
                    app_logger.warning("Failed to write audit log", exc_info=True)
            else:
                self.error_occurred.emit("save", "Failed to save record")

        def _on_error(error_type: str, message: str, tb: str) -> None:
            app_logger.error(f"Error saving record: {message}")
            self.error_occurred.emit("save", message)

        run_in_background(
            _do_save,
            on_finished=_on_finished,
            on_error=_on_error,
        )

    def _do_insert(self, table: str, data: dict[str, Any]) -> tuple[int, dict]:
        """Perform INSERT with parameterized query."""
        columns = list(data.keys())
        values = list(data.values())

        cols_sql = psql.SQL(", ").join(psql.Identifier(c) for c in columns)
        placeholders = psql.SQL(", ").join(psql.Placeholder() * len(values))

        query = psql.SQL(
            "INSERT INTO {} ({}) VALUES ({}) RETURNING id"
        ).format(
            psql.Identifier(table),
            cols_sql,
            placeholders,
        )

        new_id = insert_returning_id(query.as_string(None), tuple(values))
        if new_id is not None:
            return new_id, data
        return -1, data

    def _do_update(
        self, table: str, data: dict[str, Any], record_id: int
    ) -> tuple[int, dict]:
        """Perform UPDATE with parameterized query."""
        columns = list(data.keys())
        values = list(data.values())

        set_clause = psql.SQL(", ").join(
            psql.SQL("{} = %s").format(psql.Identifier(c))
            for c in columns
        )

        query = psql.SQL("UPDATE {} SET {} WHERE id = %s").format(
            psql.Identifier(table),
            set_clause,
        )

        affected = update_returning_count(
            query.as_string(None), tuple(values) + (record_id,)
        )
        if affected > 0:
            return record_id, data
        return -1, data

    # -----------------------------------------------------------------------
    # Delete record
    # -----------------------------------------------------------------------

    def delete_record(self, table: str, record_id: int) -> None:
        """
        Delete a record from the database asynchronously.

        Args:
            table: Table name (must be in allowed list).
            record_id: Record ID to delete.
        """
        if not self._validate_table(table):
            self.error_occurred.emit("delete", f"Table '{table}' not allowed")
            return

        def _do_delete() -> int:
            query = psql.SQL("DELETE FROM {} WHERE id = %s").format(
                psql.Identifier(table)
            )
            return delete_returning_count(query.as_string(None), (record_id,))

        def _on_finished(count: int) -> None:
            if count > 0:
                self.record_deleted.emit(record_id)
                app_logger.info(f"Deleted record {record_id} from '{table}'")

                try:
                    audit_logger.log(
                        action="DELETE",
                        entity=table,
                        entity_id=record_id,
                        details=f"Deleted record {record_id} from {table}",
                    )
                except Exception:
                    app_logger.warning("Failed to write audit log", exc_info=True)
            else:
                self.error_occurred.emit(
                    "delete", f"Record {record_id} not found in '{table}'"
                )

        def _on_error(error_type: str, message: str, tb: str) -> None:
            app_logger.error(f"Error deleting record: {message}")
            self.error_occurred.emit("delete", message)

        run_in_background(
            _do_delete,
            on_finished=_on_finished,
            on_error=_on_error,
        )

    # -----------------------------------------------------------------------
    # Combo box data loading
    # -----------------------------------------------------------------------

    def load_combo_data(
        self,
        field_id: str,
        query_str: str,
        value_column: str = "id",
        display_column: str = "name_ar",
    ) -> None:
        """
        Load combo box data from a database query asynchronously.

        Args:
            field_id: The field identifier (to route the result).
            query_str: SQL SELECT query string.
            value_column: Column name for the combo value.
            display_column: Column name for the display text.
        """
        # Sanitize: must start with SELECT
        clean = query_str.strip()
        if not clean.upper().startswith("SELECT"):
            self.error_occurred.emit(
                "combo_load", "Only SELECT queries allowed for combo data"
            )
            return

        # Reject semicolons (prevents multi-statement injection)
        if ";" in clean:
            app_logger.error(
                f"Combo query for '{field_id}' rejected: contains semicolons"
            )
            self.error_occurred.emit(
                "combo_load", "Query must not contain semicolons"
            )
            return

        # Reject dangerous SQL keywords (INSERT, DROP, DELETE, etc.)
        if _DANGEROUS_SQL_RE.search(clean):
            app_logger.error(
                f"Combo query for '{field_id}' rejected: contains dangerous keywords"
            )
            self.error_occurred.emit(
                "combo_load", "Query contains disallowed SQL keywords"
            )
            return

        def _do_load() -> list[tuple[Any, str]]:
            col_names, rows = select_all(query_str)
            if not col_names or not rows:
                return []

            # Find column indices
            try:
                val_idx = col_names.index(value_column)
                disp_idx = col_names.index(display_column)
            except ValueError:
                app_logger.warning(
                    f"Combo columns '{value_column}'/'{display_column}' "
                    f"not found in query results for '{field_id}'"
                )
                return []

            return [(row[val_idx], str(row[disp_idx])) for row in rows]

        def _on_finished(items: list[tuple[Any, str]]) -> None:
            self.combo_data_loaded.emit(field_id, items)

        def _on_error(error_type: str, message: str, tb: str) -> None:
            app_logger.error(f"Error loading combo data for '{field_id}': {message}")
            self.error_occurred.emit("combo_load", message)

        run_in_background(
            _do_load,
            on_finished=_on_finished,
            on_error=_on_error,
        )

    # -----------------------------------------------------------------------
    # Unique check
    # -----------------------------------------------------------------------

    def check_unique(
        self,
        field_id: str,
        table: str,
        column: str,
        value: Any,
        exclude_id: Optional[int] = None,
    ) -> None:
        """
        Check if a value is unique in a table column asynchronously.

        Args:
            field_id: The field identifier.
            table: Table name.
            column: Column name.
            value: Value to check.
            exclude_id: Optional record ID to exclude from check.
        """
        if not self._validate_table(table):
            self.error_occurred.emit("unique_check", f"Table '{table}' not allowed")
            return

        def _do_check() -> bool:
            if exclude_id is not None:
                query = psql.SQL(
                    "SELECT COUNT(*) FROM {} WHERE {} = %s AND id != %s"
                ).format(
                    psql.Identifier(table),
                    psql.Identifier(column),
                )
                count = get_scalar(query.as_string(None), (value, exclude_id))
            else:
                query = psql.SQL(
                    "SELECT COUNT(*) FROM {} WHERE {} = %s"
                ).format(
                    psql.Identifier(table),
                    psql.Identifier(column),
                )
                count = get_scalar(query.as_string(None), (value,))

            return (count or 0) == 0

        def _on_finished(is_unique: bool) -> None:
            self.unique_checked.emit(field_id, is_unique)

        def _on_error(error_type: str, message: str, tb: str) -> None:
            app_logger.error(f"Error checking uniqueness for '{field_id}': {message}")
            self.error_occurred.emit("unique_check", message)

        run_in_background(
            _do_check,
            on_finished=_on_finished,
            on_error=_on_error,
        )

    # -----------------------------------------------------------------------
    # Synchronous unique check (for validation engine callback)
    # -----------------------------------------------------------------------

    def check_unique_sync(
        self,
        table: str,
        column: str,
        value: Any,
        exclude_id: Optional[int] = None,
    ) -> bool:
        """
        Synchronous unique check. Use in background threads only.

        WARNING: Do NOT call from the main Qt thread (Rule #13).
        """
        if not self._validate_table(table):
            return True  # Default to allowing on error

        try:
            if exclude_id is not None:
                query = psql.SQL(
                    "SELECT COUNT(*) FROM {} WHERE {} = %s AND id != %s"
                ).format(
                    psql.Identifier(table),
                    psql.Identifier(column),
                )
                count = get_scalar(query.as_string(None), (value, exclude_id))
            else:
                query = psql.SQL(
                    "SELECT COUNT(*) FROM {} WHERE {} = %s"
                ).format(
                    psql.Identifier(table),
                    psql.Identifier(column),
                )
                count = get_scalar(query.as_string(None), (value,))

            return (count or 0) == 0
        except Exception:
            app_logger.error(
                f"Error in sync unique check for '{table}.{column}'",
                exc_info=True,
            )
            return True
