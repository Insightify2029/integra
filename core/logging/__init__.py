# core/logging/__init__.py
"""
INTEGRA - حزمة التسجيل
========================
الاستخدام:
    from core.logging import setup_logging, app_logger, audit_logger
    
    setup_logging(debug_mode=True)     # مرة واحدة في main.py
    app_logger.info("رسالة")           # تسجيل عادي
    audit_logger.log(...)              # تسجيل تدقيق
"""

from core.logging.app_logger import AppLogger, app_logger
from core.logging.audit_logger import AuditLogger, audit_logger

# Rich console imports deferred - only loaded when actually used


def __getattr__(name):
    """Lazy import rich_console exports on first access."""
    _rich_names = {
        "console", "print_table", "print_panel", "rich_progress",
        "print_success", "print_error", "print_warning", "print_info",
        "print_startup_banner", "print_stats_table", "print_exception",
        "HAS_RICH",
    }
    if name in _rich_names:
        from core.logging import rich_console
        return getattr(rich_console, name)
    raise AttributeError(f"module 'core.logging' has no attribute {name!r}")


def setup_logging(log_dir: str = None, debug_mode: bool = False,
                  console_output: bool = True):
    """تهيئة كل نظام التسجيل - مرة واحدة في main.py"""
    AppLogger.setup(log_dir=log_dir, debug_mode=debug_mode,
                    console_output=console_output)
    AuditLogger.setup(log_dir=log_dir)


def shutdown_logging():
    """إغلاق نظيف - عند إغلاق البرنامج"""
    AuditLogger.shutdown()
    AppLogger.shutdown()


__all__ = [
    "AppLogger", "AuditLogger",
    "app_logger", "audit_logger",
    "setup_logging", "shutdown_logging",
    "console", "print_table", "print_panel", "rich_progress",
    "print_success", "print_error", "print_warning", "print_info",
    "print_startup_banner", "print_stats_table", "print_exception",
]
