"""
Recovery Module
===============
Auto-save and recovery system for preventing data loss.

Features:
- Automatic periodic saving of form data
- Recovery of unsaved data on startup
- User-friendly recovery dialog

Usage - Auto-Save:
    from core.recovery import AutoSaveManager

    # In a form/window class
    def __init__(self):
        self.auto_save = AutoSaveManager(
            form_id=f"edit_employee_{self.employee_id}",
            save_callback=self.get_form_data,
            interval_seconds=60
        )
        self.auto_save.start()

    def get_form_data(self):
        return {
            "name": self.name_input.text(),
            "salary": self.salary_input.value(),
            # ... other fields
        }

    def save_clicked(self):
        # Save to database
        self.save_to_db()
        # Clear recovery data
        self.auto_save.clear_recovery()
        self.auto_save.stop()

Usage - Recovery at Startup:
    from core.recovery import check_and_recover, RecoveryManager

    # Simple approach
    recovered = check_and_recover(main_window)
    for item in recovered:
        print(f"Recovered: {item}")

    # Or use manager directly
    recovery = RecoveryManager()
    if recovery.has_recoverable_data():
        items = recovery.get_recoverable_items()
        # Handle items...
"""

from .auto_save import (
    AutoSaveManager,
    get_all_recovery_files,
    clear_all_recovery_files,
    DEFAULT_INTERVAL_SECONDS,
    RECOVERY_DIR
)

from .recovery_manager import (
    RecoveryManager,
    RecoveryDialog,
    check_and_recover,
    RECOVERY_RETENTION_DAYS
)

__all__ = [
    # Auto-save
    'AutoSaveManager',
    'get_all_recovery_files',
    'clear_all_recovery_files',
    'DEFAULT_INTERVAL_SECONDS',
    'RECOVERY_DIR',
    # Recovery
    'RecoveryManager',
    'RecoveryDialog',
    'check_and_recover',
    'RECOVERY_RETENTION_DAYS'
]
