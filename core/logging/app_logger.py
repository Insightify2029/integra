# core/logging/app_logger.py
"""
INTEGRA - اللوجر الرئيسي
=========================
بيسجل كل اللي بيحصل في البرنامج (زي دفتر اليومية).

الاستخدام:
    from core.logging.app_logger import app_logger
    
    app_logger.info("البرنامج اشتغل")
    app_logger.warning("تحذير")
    app_logger.error("خطأ")
"""

import sys
from pathlib import Path
from loguru import logger


# شكل السطر في الملف
LOG_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
    "{level: <8} | "
    "{module}:{function}:{line} | "
    "{message}"
)

# شكل السطر في الكونسول (بألوان)
CONSOLE_FORMAT = (
    "<green>{time:HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{module}</cyan>:<cyan>{function}</cyan> | "
    "<level>{message}</level>"
)


class AppLogger:
    """اللوجر الرئيسي لبرنامج INTEGRA"""
    
    _initialized = False
    
    @classmethod
    def setup(cls, log_dir: str = None, debug_mode: bool = False,
              console_output: bool = True):
        """
        تهيئة - يُستدعى مرة واحدة في main.py
        
        debug_mode=True   → أثناء التطوير (يسجل كل التفاصيل)
        debug_mode=False  → في الإنتاج (يسجل INFO وأعلى بس)
        """
        if cls._initialized:
            return
        
        log_path = Path(log_dir) if log_dir else Path("logs")
        log_path.mkdir(parents=True, exist_ok=True)
        
        # إزالة الافتراضي
        logger.remove()
        
        # 1) ملف التطبيق الرئيسي (app_YYYY-MM-DD.log)
        logger.add(
            str(log_path / "app_{time:YYYY-MM-DD}.log"),
            rotation="10 MB",
            retention="30 days",
            level="INFO",
            format=LOG_FORMAT,
            encoding="utf-8",
            backtrace=True,
            diagnose=False,
            enqueue=True,
        )
        
        # 2) ملف التطوير (debug_YYYY-MM-DD.log) - لو debug_mode مفعّل
        if debug_mode:
            logger.add(
                str(log_path / "debug_{time:YYYY-MM-DD}.log"),
                rotation="10 MB",
                retention="7 days",
                level="DEBUG",
                format=LOG_FORMAT,
                encoding="utf-8",
                backtrace=True,
                diagnose=True,
                enqueue=True,
            )
        
        # 3) ملف الأخطاء JSON (errors.json)
        logger.add(
            str(log_path / "errors.json"),
            rotation="10 MB",
            retention="30 days",
            level="WARNING",
            serialize=True,
            encoding="utf-8",
            enqueue=True,
        )
        
        # 4) الكونسول
        if console_output:
            logger.add(
                sys.stderr,
                level="DEBUG" if debug_mode else "INFO",
                format=CONSOLE_FORMAT,
                colorize=True,
            )
        
        cls._initialized = True
        logger.info("═" * 50)
        logger.info("INTEGRA - نظام التسجيل جاهز")
        logger.info(f"اللوجات: {log_path.resolve()}")
        logger.info(f"وضع التطوير: {'مفعّل' if debug_mode else 'مغلق'}")
        logger.info("═" * 50)
    
    @classmethod
    def get_logger(cls):
        """إرجاع الـ logger"""
        if not cls._initialized:
            cls.setup()
        return logger
    
    @classmethod
    def shutdown(cls):
        """تنظيف عند الإغلاق"""
        if cls._initialized:
            logger.info("INTEGRA - إغلاق نظام التسجيل")
            logger.complete()
            cls._initialized = False


class _LoggerProxy:
    """وسيط عشان تقدر تستخدم app_logger.info() مباشرة"""
    def __getattr__(self, name):
        return getattr(AppLogger.get_logger(), name)

app_logger = _LoggerProxy()
