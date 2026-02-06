"""
DB Importer
============
Import cleaned Excel/CSV data into PostgreSQL database.
Supports: append, replace, and upsert modes.
"""

from typing import Dict, List, Any, Optional
from core.logging import app_logger


class DBImporter:
    """Import tabular data into the database."""

    def __init__(self):
        self._last_result = None

    def import_data(self, df, table_name: str,
                    column_mapping: Dict[str, str],
                    mode: str = "append",
                    key_columns: List[str] = None) -> Dict[str, Any]:
        """
        Import DataFrame into a database table.

        Args:
            df: pandas DataFrame with the data
            table_name: Target database table name
            column_mapping: Dict mapping DataFrame columns to DB columns
            mode: 'append' (insert new), 'replace' (truncate+insert), 'update' (upsert)
            key_columns: Key columns for upsert mode

        Returns:
            Dict with import results
        """
        try:
            from core.database import select_all, insert

            # Apply column mapping
            df_mapped = df.rename(columns=column_mapping)
            valid_columns = list(column_mapping.values())
            df_final = df_mapped[valid_columns].copy()

            if mode == "replace":
                return self._import_replace(df_final, table_name, valid_columns)
            elif mode == "update" and key_columns:
                return self._import_upsert(df_final, table_name, valid_columns, key_columns)
            else:
                return self._import_append(df_final, table_name, valid_columns)

        except Exception as e:
            app_logger.error(f"Import failed: {e}")
            return {"success": False, "message": str(e), "imported_rows": 0}

    def _import_append(self, df, table_name: str,
                       columns: List[str]) -> Dict[str, Any]:
        """Insert new rows."""
        from core.database import insert

        imported = 0
        errors = []

        cols_str = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))
        query = f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders})"

        for idx, row in df.iterrows():
            try:
                values = tuple(
                    None if _is_nan(row[col]) else row[col]
                    for col in columns
                )
                insert(query, values)
                imported += 1
            except Exception as e:
                errors.append({"row": int(idx), "error": str(e)})

        result = {
            "success": True,
            "mode": "append",
            "table": table_name,
            "imported_rows": imported,
            "error_rows": len(errors),
            "errors": errors[:10],  # First 10 errors
        }
        self._last_result = result
        app_logger.info(f"Imported {imported} rows into {table_name}")
        return result

    def _import_replace(self, df, table_name: str,
                        columns: List[str]) -> Dict[str, Any]:
        """Truncate and insert."""
        from core.database import insert, select_all

        # Get current count
        try:
            _, rows = select_all(f"SELECT COUNT(*) FROM {table_name}")
            old_count = rows[0][0] if rows else 0
        except Exception:
            old_count = 0

        # Truncate
        try:
            insert(f"TRUNCATE TABLE {table_name} CASCADE")
        except Exception as e:
            return {"success": False, "message": f"Truncate failed: {e}"}

        # Insert all
        result = self._import_append(df, table_name, columns)
        result["mode"] = "replace"
        result["previous_rows"] = old_count
        return result

    def _import_upsert(self, df, table_name: str,
                       columns: List[str],
                       key_columns: List[str]) -> Dict[str, Any]:
        """Upsert (insert or update on conflict)."""
        from core.database import insert

        imported = 0
        updated = 0
        errors = []

        cols_str = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))
        key_str = ", ".join(key_columns)
        update_cols = [c for c in columns if c not in key_columns]
        update_str = ", ".join([f"{c} = EXCLUDED.{c}" for c in update_cols])

        query = f"""
            INSERT INTO {table_name} ({cols_str})
            VALUES ({placeholders})
            ON CONFLICT ({key_str}) DO UPDATE SET {update_str}
        """

        for idx, row in df.iterrows():
            try:
                values = tuple(
                    None if _is_nan(row[col]) else row[col]
                    for col in columns
                )
                insert(query, values)
                imported += 1
            except Exception as e:
                errors.append({"row": int(idx), "error": str(e)})

        result = {
            "success": True,
            "mode": "upsert",
            "table": table_name,
            "imported_rows": imported,
            "error_rows": len(errors),
            "errors": errors[:10],
        }
        self._last_result = result
        return result

    def preview_mapping(self, df, column_mapping: Dict[str, str],
                        rows: int = 5) -> Dict[str, Any]:
        """
        Preview the mapped data before importing.

        Args:
            df: Source DataFrame
            column_mapping: Column mapping dict
            rows: Number of preview rows

        Returns:
            Dict with preview data
        """
        df_mapped = df.rename(columns=column_mapping)
        valid_columns = list(column_mapping.values())
        preview_df = df_mapped[valid_columns].head(rows)

        return {
            "columns": valid_columns,
            "rows": preview_df.values.tolist(),
            "total_rows": len(df),
        }

    @property
    def last_result(self) -> Optional[Dict[str, Any]]:
        """Get the last import result."""
        return self._last_result


def _is_nan(value) -> bool:
    """Check if a value is NaN."""
    try:
        import math
        if isinstance(value, float) and math.isnan(value):
            return True
    except (TypeError, ValueError):
        pass

    try:
        import pandas as pd
        if pd.isna(value):
            return True
    except (ImportError, TypeError, ValueError):
        pass

    return False
