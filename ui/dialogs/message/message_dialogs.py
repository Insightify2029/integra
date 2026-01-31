"""
Message Dialogs
===============
Various message dialogs.
"""

from PyQt5.QtWidgets import QMessageBox


def show_info(parent, title: str, message: str):
    """Show info message."""
    QMessageBox.information(parent, title, message)


def show_warning(parent, title: str, message: str):
    """Show warning message."""
    QMessageBox.warning(parent, title, message)


def show_error(parent, title: str, message: str):
    """Show error message."""
    QMessageBox.critical(parent, title, message)


def show_success(parent, title: str, message: str):
    """Show success message."""
    QMessageBox.information(parent, f"✅ {title}", message)


def confirm(parent, title: str, message: str) -> bool:
    """Show confirmation dialog. Returns True if confirmed."""
    result = QMessageBox.question(
        parent, title, message,
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )
    return result == QMessageBox.Yes
