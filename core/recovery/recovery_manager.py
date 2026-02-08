"""
Recovery Manager
================
Manages recovery of unsaved data on application startup.

Features:
- Detects recoverable data at startup
- Shows recovery dialog to user
- Restores data to appropriate forms
- Cleans up old recovery files

Usage:
    from core.recovery import RecoveryManager

    # At application startup
    recovery = RecoveryManager()

    if recovery.has_recoverable_data():
        # Show dialog and let user choose
        recovery.show_recovery_dialog(parent_window)

    # Or handle programmatically
    recoverable = recovery.get_recoverable_items()
    for item in recoverable:
        print(f"Found: {item['form_id']} from {item['timestamp']}")
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path

from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem,
    QMessageBox
)

from core.logging import app_logger
from .auto_save import RECOVERY_DIR, get_all_recovery_files, clear_all_recovery_files


# Recovery file retention (days)
RECOVERY_RETENTION_DAYS = 7


class RecoveryManager(QObject):
    """
    Manages recovery of unsaved data.

    Signals:
        recovery_available: Emitted when recoverable data is found
        recovery_completed: Emitted when recovery is done
    """

    recovery_available = pyqtSignal(list)  # List of recoverable items
    recovery_completed = pyqtSignal(int)   # Number of items recovered

    def __init__(self, parent: Optional[QObject] = None):
        """Initialize recovery manager."""
        super().__init__(parent)

        self._recovery_handlers: Dict[str, Callable] = {}
        self._cleanup_old_files()

    def _cleanup_old_files(self) -> None:
        """Remove recovery files older than retention period."""
        try:
            if not RECOVERY_DIR.exists():
                return

            cutoff = datetime.now() - timedelta(days=RECOVERY_RETENTION_DAYS)

            for file_path in RECOVERY_DIR.glob("*.recovery.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    timestamp_str = data.get("timestamp")
                    if timestamp_str:
                        timestamp = datetime.fromisoformat(timestamp_str)
                        if timestamp < cutoff:
                            file_path.unlink()
                            app_logger.info(
                                f"Cleaned old recovery file: {file_path.name}"
                            )
                except (json.JSONDecodeError, OSError, ValueError) as e:
                    app_logger.warning(f"Skipping corrupt recovery file {file_path.name}: {e}")
                    continue

        except OSError as e:
            app_logger.error(f"Recovery cleanup failed: {e}")

    def has_recoverable_data(self) -> bool:
        """Check if there is recoverable data."""
        items = get_all_recovery_files()
        return len(items) > 0

    def get_recoverable_items(self) -> List[Dict[str, Any]]:
        """
        Get list of recoverable items.

        Returns:
            List of dicts with form_id, timestamp, file_path
        """
        items = get_all_recovery_files()

        # Parse and format timestamps
        for item in items:
            if item.get("timestamp"):
                try:
                    dt = datetime.fromisoformat(item["timestamp"])
                    item["timestamp_display"] = dt.strftime("%Y-%m-%d %H:%M")
                    item["timestamp_dt"] = dt
                except Exception:
                    item["timestamp_display"] = item["timestamp"]

        # Sort by timestamp (newest first)
        items.sort(
            key=lambda x: x.get("timestamp_dt", datetime.min),
            reverse=True
        )

        return items

    def register_recovery_handler(
        self,
        form_pattern: str,
        handler: Callable[[Dict[str, Any]], bool]
    ) -> None:
        """
        Register a handler for recovering specific form types.

        Args:
            form_pattern: Pattern to match form_id (e.g., "edit_employee_")
            handler: Function to call with recovery data, returns True if handled
        """
        self._recovery_handlers[form_pattern] = handler
        app_logger.debug(f"Registered recovery handler for: {form_pattern}")

    def recover_item(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Load recovery data from file.

        Args:
            file_path: Path to recovery file

        Returns:
            Recovery data dict or None
        """
        try:
            path = Path(file_path)

            if not path.exists():
                return None

            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return data

        except Exception as e:
            app_logger.error(f"Failed to recover item: {e}")
            return None

    def delete_recovery_item(self, file_path: str) -> bool:
        """
        Delete a recovery file.

        Args:
            file_path: Path to recovery file

        Returns:
            True if deleted, False otherwise
        """
        try:
            path = Path(file_path)

            if path.exists():
                path.unlink()
                app_logger.info(f"Deleted recovery file: {path.name}")
                return True

            return False

        except Exception as e:
            app_logger.error(f"Failed to delete recovery item: {e}")
            return False

    def clear_all(self) -> int:
        """
        Clear all recovery files.

        Returns:
            Number of files deleted
        """
        return clear_all_recovery_files()

    def show_recovery_dialog(self, parent=None) -> List[Dict[str, Any]]:
        """
        Show recovery dialog to user.

        Args:
            parent: Parent widget

        Returns:
            List of items user chose to recover
        """
        items = self.get_recoverable_items()

        if not items:
            return []

        dialog = RecoveryDialog(items, parent)
        result = dialog.exec_()

        if result == QDialog.Accepted:
            recovered = dialog.get_selected_items()
            self.recovery_completed.emit(len(recovered))
            return recovered

        return []


class RecoveryDialog(QDialog):
    """Dialog for recovering unsaved data."""

    def __init__(self, items: List[Dict[str, Any]], parent=None):
        super().__init__(parent)

        self.items = items
        self.selected_items = []

        self._setup_ui()

    def _setup_ui(self):
        """Setup dialog UI."""
        self.setWindowTitle("استرجاع البيانات غير المحفوظة")
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)

        layout = QVBoxLayout(self)

        # Header
        header = QLabel(
            "تم العثور على بيانات غير محفوظة من جلسة سابقة.\n"
            "اختر البيانات التي تريد استرجاعها:"
        )
        header.setStyleSheet("font-size: 14px; margin-bottom: 10px; padding: 5px;")
        layout.addWidget(header)

        # List of recoverable items
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)

        for item in self.items:
            form_id = item.get("form_id", "غير معروف")
            timestamp = item.get("timestamp_display", "")

            # Format display text
            display_text = f"{form_id}"
            if timestamp:
                display_text += f"  ({timestamp})"

            list_item = QListWidgetItem(display_text)
            list_item.setData(Qt.UserRole, item)  # Store full item data
            self.list_widget.addItem(list_item)

            # Select by default
            list_item.setSelected(True)

        layout.addWidget(self.list_widget)

        # Buttons
        button_layout = QHBoxLayout()

        select_all_btn = QPushButton("تحديد الكل")
        select_all_btn.clicked.connect(self._select_all)
        button_layout.addWidget(select_all_btn)

        clear_btn = QPushButton("إلغاء التحديد")
        clear_btn.clicked.connect(self._clear_selection)
        button_layout.addWidget(clear_btn)

        button_layout.addStretch()

        recover_btn = QPushButton("استرجاع المحدد")
        highlight = self.palette().color(QPalette.Highlight).name()
        highlight_text = self.palette().color(QPalette.HighlightedText).name()
        recover_btn.setStyleSheet(
            f"background-color: {highlight}; color: {highlight_text}; font-weight: bold;"
        )
        recover_btn.clicked.connect(self._recover)
        button_layout.addWidget(recover_btn)

        discard_btn = QPushButton("تجاهل الكل")
        discard_btn.clicked.connect(self._discard)
        button_layout.addWidget(discard_btn)

        layout.addLayout(button_layout)

    def _select_all(self):
        """Select all items."""
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setSelected(True)

    def _clear_selection(self):
        """Clear selection."""
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setSelected(False)

    def _recover(self):
        """Recover selected items."""
        self.selected_items = []

        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.isSelected():
                self.selected_items.append(item.data(Qt.UserRole))

        self.accept()

    def _discard(self):
        """Discard all recovery data."""
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            "هل أنت متأكد من حذف جميع البيانات غير المحفوظة؟\n"
            "لا يمكن التراجع عن هذا الإجراء.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            clear_all_recovery_files()
            self.selected_items = []
            self.reject()

    def get_selected_items(self) -> List[Dict[str, Any]]:
        """Get list of selected items."""
        return self.selected_items


def check_and_recover(parent=None) -> List[Dict[str, Any]]:
    """
    Convenience function to check for and recover data at startup.

    Args:
        parent: Parent widget for dialog

    Returns:
        List of recovered items
    """
    manager = RecoveryManager()

    if manager.has_recoverable_data():
        return manager.show_recovery_dialog(parent)

    return []
