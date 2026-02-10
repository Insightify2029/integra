# -*- coding: utf-8 -*-
"""
Form Designer Template Manager
===============================
Manages built-in and user-defined form templates for the INTEGRA Form Designer.

Provides:
- Template discovery from builtin/ directory and configurable user directory
- Template metadata via TemplateInfo dataclass
- Saving / deleting user templates
- Thread-safe singleton access via get_template_manager()

Author: Mohamed
Version: 1.0.0
Date: February 2026
"""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from core.logging import app_logger


# ============================================================================
# Constants
# ============================================================================

TEMPLATE_FILE_EXTENSION = ".iform"

TEMPLATE_CATEGORIES: Dict[str, str] = {
    "employee": "\u0627\u0644\u0645\u0648\u0638\u0641\u064a\u0646",
    "master_data": "\u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a \u0627\u0644\u0631\u0626\u064a\u0633\u064a\u0629",
    "search": "\u0627\u0644\u0628\u062d\u062b",
    "settings": "\u0627\u0644\u0625\u0639\u062f\u0627\u062f\u0627\u062a",
    "report": "\u0627\u0644\u062a\u0642\u0627\u0631\u064a\u0631",
    "blank": "\u0641\u0627\u0631\u063a",
}

DEFAULT_USER_TEMPLATES_DIR = "modules/designer/templates/user"

_METADATA_FILE = "_template_meta.json"


# ============================================================================
# TemplateInfo dataclass
# ============================================================================

@dataclass
class TemplateInfo:
    """Lightweight metadata about a single form template."""

    template_id: str
    name_ar: str
    name_en: str
    description_ar: str
    description_en: str
    category: str          # one of TEMPLATE_CATEGORIES keys
    icon: str
    is_builtin: bool
    file_path: str
    columns: int           # form columns count


# ============================================================================
# TemplateManager
# ============================================================================

class TemplateManager:
    """
    Thread-safe manager for form designer templates.

    Discovers built-in templates from the ``builtin/`` sub-directory and
    user templates from a configurable directory.  All public methods that
    mutate shared state are protected by a threading lock (Rule #3/#4).
    """

    def __init__(
        self,
        builtin_dir: Optional[str] = None,
        user_dir: Optional[str] = None,
    ) -> None:
        self._lock = threading.Lock()

        project_root = Path(__file__).resolve().parents[3]

        if builtin_dir is not None:
            self._builtin_dir = Path(builtin_dir)
        else:
            self._builtin_dir = (
                Path(__file__).resolve().parent / "builtin"
            )

        if user_dir is not None:
            self._user_dir = Path(user_dir)
        else:
            self._user_dir = project_root / DEFAULT_USER_TEMPLATES_DIR

        # In-memory caches keyed by template_id
        self._builtin_cache: Dict[str, TemplateInfo] = {}
        self._user_cache: Dict[str, TemplateInfo] = {}

        # Ensure directories exist
        self._builtin_dir.mkdir(parents=True, exist_ok=True)
        self._user_dir.mkdir(parents=True, exist_ok=True)

        # Initial load
        self._load_builtin_templates()
        self._load_user_templates()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_template_info(
        self, file_path: Path, is_builtin: bool
    ) -> Optional[TemplateInfo]:
        """Parse a .iform file and return its TemplateInfo, or None on error."""
        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                data: dict = json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            app_logger.error(
                f"Failed to read template file '{file_path}': {exc}"
            )
            return None

        template_id = data.get("form_id", file_path.stem)
        category = data.get("category", "blank")
        if category not in TEMPLATE_CATEGORIES:
            category = "blank"

        settings = data.get("settings", {})
        columns = settings.get("columns", 2)
        if not isinstance(columns, int) or columns < 1:
            columns = 2

        return TemplateInfo(
            template_id=template_id,
            name_ar=data.get("form_name_ar", ""),
            name_en=data.get("form_name_en", ""),
            description_ar=data.get("description_ar", ""),
            description_en=data.get("description_en", ""),
            category=category,
            icon=data.get("icon", "file-alt"),
            is_builtin=is_builtin,
            file_path=str(file_path),
            columns=columns,
        )

    def _load_builtin_templates(self) -> None:
        """Scan the builtin directory and populate the cache."""
        cache: Dict[str, TemplateInfo] = {}
        if not self._builtin_dir.is_dir():
            app_logger.warning(
                f"Built-in templates directory not found: {self._builtin_dir}"
            )
            with self._lock:
                self._builtin_cache = cache
            return

        for file_path in sorted(self._builtin_dir.glob(f"*{TEMPLATE_FILE_EXTENSION}")):
            info = self._extract_template_info(file_path, is_builtin=True)
            if info is not None:
                cache[info.template_id] = info

        with self._lock:
            self._builtin_cache = cache

        app_logger.info(
            f"Loaded {len(cache)} built-in template(s) from '{self._builtin_dir}'"
        )

    def _load_user_templates(self) -> None:
        """Scan the user templates directory and populate the cache."""
        cache: Dict[str, TemplateInfo] = {}
        if not self._user_dir.is_dir():
            with self._lock:
                self._user_cache = cache
            return

        for file_path in sorted(self._user_dir.glob(f"*{TEMPLATE_FILE_EXTENSION}")):
            info = self._extract_template_info(file_path, is_builtin=False)
            if info is not None:
                cache[info.template_id] = info

        with self._lock:
            self._user_cache = cache

        app_logger.info(
            f"Loaded {len(cache)} user template(s) from '{self._user_dir}'"
        )

    # ------------------------------------------------------------------
    # Public read API
    # ------------------------------------------------------------------

    def get_builtin_templates(self) -> List[TemplateInfo]:
        """Return a list of all discovered built-in templates."""
        with self._lock:
            return list(self._builtin_cache.values())

    def get_user_templates(self) -> List[TemplateInfo]:
        """Return a list of all discovered user templates."""
        with self._lock:
            return list(self._user_cache.values())

    def get_all_templates(self) -> List[TemplateInfo]:
        """Return the combined list of built-in + user templates."""
        with self._lock:
            combined = list(self._builtin_cache.values())
            combined.extend(self._user_cache.values())
        return combined

    def get_template(self, template_id: str) -> Optional[dict]:
        """
        Load and return the full template data (JSON dict) for *template_id*.

        Returns ``None`` if the template is not found or cannot be read.
        """
        with self._lock:
            info = self._builtin_cache.get(template_id)
            if info is None:
                info = self._user_cache.get(template_id)

        if info is None:
            app_logger.warning(f"Template not found: {template_id}")
            return None

        file_path = Path(info.file_path)
        if not file_path.is_file():
            app_logger.error(
                f"Template file missing on disk: {file_path}"
            )
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                data: dict = json.load(fh)
            return data
        except (json.JSONDecodeError, OSError) as exc:
            app_logger.error(
                f"Failed to load template '{template_id}': {exc}"
            )
            return None

    # ------------------------------------------------------------------
    # Public write API
    # ------------------------------------------------------------------

    def save_as_template(
        self,
        form_data: dict,
        name: str,
        description: str,
        category: str,
    ) -> bool:
        """
        Save *form_data* as a new user template.

        A unique template ID is generated automatically.  The file is
        written to the user templates directory and the cache is updated.

        Args:
            form_data: Full form definition dictionary.
            name: Display name (used for both name_ar and name_en).
            description: Template description (both languages).
            category: One of TEMPLATE_CATEGORIES keys.

        Returns:
            ``True`` on success, ``False`` on any error.
        """
        if category not in TEMPLATE_CATEGORIES:
            app_logger.error(
                f"Invalid template category '{category}'. "
                f"Valid: {list(TEMPLATE_CATEGORIES.keys())}"
            )
            return False

        if not isinstance(form_data, dict):
            app_logger.error("form_data must be a dictionary")
            return False

        template_id = f"user_{uuid.uuid4().hex[:12]}"

        # Inject metadata into the form data copy
        data_to_save = dict(form_data)
        data_to_save["form_id"] = template_id
        data_to_save["form_name_ar"] = name
        data_to_save["form_name_en"] = name
        data_to_save["description_ar"] = description
        data_to_save["description_en"] = description
        data_to_save["category"] = category
        data_to_save["icon"] = data_to_save.get("icon", "file-alt")
        data_to_save["saved_at"] = datetime.now().isoformat()

        file_name = f"{template_id}{TEMPLATE_FILE_EXTENSION}"
        file_path = self._user_dir / file_name

        try:
            self._user_dir.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as fh:
                json.dump(data_to_save, fh, ensure_ascii=False, indent=2)
        except OSError as exc:
            app_logger.error(
                f"Failed to write user template '{file_path}': {exc}"
            )
            return False

        settings = data_to_save.get("settings", {})
        columns = settings.get("columns", 2)
        if not isinstance(columns, int) or columns < 1:
            columns = 2

        info = TemplateInfo(
            template_id=template_id,
            name_ar=name,
            name_en=name,
            description_ar=description,
            description_en=description,
            category=category,
            icon=data_to_save.get("icon", "file-alt"),
            is_builtin=False,
            file_path=str(file_path),
            columns=columns,
        )

        with self._lock:
            self._user_cache[template_id] = info

        app_logger.info(
            f"Saved user template '{name}' (id={template_id}) to '{file_path}'"
        )
        return True

    def delete_user_template(self, template_id: str) -> bool:
        """
        Delete a user template by ID.

        Built-in templates cannot be deleted.

        Args:
            template_id: The ID of the template to delete.

        Returns:
            ``True`` if the template was deleted, ``False`` otherwise.
        """
        with self._lock:
            info = self._user_cache.get(template_id)

        if info is None:
            app_logger.warning(
                f"Cannot delete template '{template_id}': "
                "not found in user templates"
            )
            return False

        if info.is_builtin:
            app_logger.warning(
                f"Cannot delete built-in template '{template_id}'"
            )
            return False

        file_path = Path(info.file_path)
        try:
            if file_path.is_file():
                file_path.unlink()
        except OSError as exc:
            app_logger.error(
                f"Failed to delete template file '{file_path}': {exc}"
            )
            return False

        with self._lock:
            self._user_cache.pop(template_id, None)

        app_logger.info(f"Deleted user template '{template_id}'")
        return True

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def reload(self) -> None:
        """Re-scan both template directories and refresh caches."""
        self._load_builtin_templates()
        self._load_user_templates()

    def get_categories(self) -> Dict[str, str]:
        """Return the mapping of category key -> Arabic display name."""
        return dict(TEMPLATE_CATEGORIES)


# ============================================================================
# Thread-safe singleton (Rule #4)
# ============================================================================

_template_manager_lock = threading.Lock()
_template_manager_instance: Optional[TemplateManager] = None


def get_template_manager() -> TemplateManager:
    """
    Return the singleton TemplateManager instance.

    Thread-safe: always acquires the lock (Rule #4).
    """
    global _template_manager_instance
    with _template_manager_lock:
        if _template_manager_instance is None:
            _template_manager_instance = TemplateManager()
    return _template_manager_instance
