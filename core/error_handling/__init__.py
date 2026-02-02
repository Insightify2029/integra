# core/error_handling/__init__.py
"""
INTEGRA - معالجة الأخطاء
=========================
الاستخدام:
    from core.error_handling import install_exception_handler
    install_exception_handler()  # مرة واحدة في main.py
"""

from core.error_handling.exception_hook import install_exception_handler

__all__ = ["install_exception_handler"]
