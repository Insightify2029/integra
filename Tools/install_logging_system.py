# Tools/install_logging_system.py
"""
═══════════════════════════════════════════════════════════
  INTEGRA A1 - تركيب نظام الـ Logging تلقائياً
═══════════════════════════════════════════════════════════

الاستخدام:
  1. افتح CMD أو Terminal
  2. اكتب:
     cd D:\\Projects\\Integra
     python Tools\\install_logging_system.py

  أو من VS Code:
  1. افتح مجلد D:\\Projects\\Integra
  2. كليك يمين على الملف ده → Run Python File

هيعمل إيه:
  ✅ ينشئ مجلد core/logging/
  ✅ ينشئ 3 ملفات (app_logger + audit_logger + __init__)
  ✅ ينشئ مجلد logs/
  ✅ يضيف logs/ في .gitignore
  ✅ يشغّل اختبار سريع يتأكد كل حاجة شغالة
═══════════════════════════════════════════════════════════
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# ──────────────────────────────────────────────
# تحديد مسار المشروع
# ──────────────────────────────────────────────
# الملف ده في Tools/ → المشروع = مجلد فوق
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

print()
print("═" * 60)
print("  INTEGRA A1 - تركيب نظام الـ Logging")
print("═" * 60)
print(f"  مسار المشروع: {PROJECT_ROOT}")
print(f"  التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("═" * 60)


# ──────────────────────────────────────────────
# الخطوة 1: إنشاء المجلدات
# ──────────────────────────────────────────────
print("\n📁 الخطوة 1: إنشاء المجلدات...")

folders = [
    PROJECT_ROOT / "core" / "logging",
    PROJECT_ROOT / "logs",
]

for folder in folders:
    folder.mkdir(parents=True, exist_ok=True)
    print(f"  ✅ {folder.relative_to(PROJECT_ROOT)}")


# ──────────────────────────────────────────────
# الخطوة 2: إنشاء الملفات
# ──────────────────────────────────────────────
print("\n📄 الخطوة 2: إنشاء الملفات...")

# ─── ملف 1: app_logger.py ───
APP_LOGGER_CODE = r'''# core/logging/app_logger.py
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
'''

# ─── ملف 2: audit_logger.py ───
AUDIT_LOGGER_CODE = r'''# core/logging/audit_logger.py
"""
INTEGRA - سجل التدقيق
======================
بيسجل العمليات الحساسة (زي سجل المراجعة):
- مين غيّر إيه
- القيم القديمة والجديدة
- إمتى

الاستخدام:
    from core.logging.audit_logger import audit_logger, ACTION_UPDATE, ENTITY_EMPLOYEE
    
    audit_logger.log(
        action=ACTION_UPDATE,
        entity=ENTITY_EMPLOYEE,
        entity_id=101,
        details="تعديل الراتب",
        old_values={"salary": 5000},
        new_values={"salary": 5500}
    )
"""

import json
from pathlib import Path
from typing import Any
from loguru import logger


# ─── أنواع الإجراءات ───
ACTION_CREATE = "CREATE"
ACTION_UPDATE = "UPDATE"
ACTION_DELETE = "DELETE"
ACTION_VIEW = "VIEW"
ACTION_EXPORT = "EXPORT"
ACTION_IMPORT = "IMPORT"
ACTION_LOGIN = "LOGIN"
ACTION_LOGOUT = "LOGOUT"
ACTION_LOGIN_FAIL = "LOGIN_FAIL"
ACTION_PROCESS = "PROCESS"
ACTION_APPROVE = "APPROVE"
ACTION_REJECT = "REJECT"

# ─── أنواع الكيانات ───
ENTITY_EMPLOYEE = "EMPLOYEE"
ENTITY_PAYROLL = "PAYROLL"
ENTITY_CONTRACT = "CONTRACT"
ENTITY_LEAVE = "LEAVE"
ENTITY_OVERTIME = "OVERTIME"
ENTITY_EOS = "END_OF_SERVICE"
ENTITY_ALLOWANCE = "ALLOWANCE"
ENTITY_DEDUCTION = "DEDUCTION"
ENTITY_DEPARTMENT = "DEPARTMENT"
ENTITY_SETTINGS = "SETTINGS"
ENTITY_USER = "USER"
ENTITY_REPORT = "REPORT"
ENTITY_BACKUP = "BACKUP"

# شكل سطر التدقيق
AUDIT_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
    "AUDIT | "
    "{extra[user]: <15} | "
    "{extra[action]: <15} | "
    "{extra[entity]: <20} | "
    "{extra[entity_id]} | "
    "{message}"
)


class AuditLogger:
    """سجل التدقيق لبرنامج INTEGRA"""
    
    _initialized = False
    _current_user = "SYSTEM"
    
    @classmethod
    def setup(cls, log_dir: str = None):
        """تهيئة - يُستدعى مرة واحدة عند بدء البرنامج"""
        if cls._initialized:
            return
        
        log_path = Path(log_dir) if log_dir else Path("logs")
        log_path.mkdir(parents=True, exist_ok=True)
        
        def audit_filter(record):
            return record["extra"].get("is_audit", False)
        
        # ملف التدقيق النصي (مقروء)
        logger.add(
            str(log_path / "audit_{time:YYYY-MM-DD}.log"),
            rotation="10 MB",
            retention="90 days",
            level="INFO",
            format=AUDIT_FORMAT,
            filter=audit_filter,
            encoding="utf-8",
            enqueue=True,
        )
        
        # ملف التدقيق JSON (للتحليل)
        logger.add(
            str(log_path / "audit.json"),
            rotation="10 MB",
            retention="90 days",
            level="INFO",
            filter=audit_filter,
            serialize=True,
            encoding="utf-8",
            enqueue=True,
        )
        
        cls._initialized = True
    
    @classmethod
    def set_current_user(cls, username: str):
        """تحديد المستخدم الحالي (بعد تسجيل الدخول)"""
        cls._current_user = username
    
    @classmethod
    def log(cls, action: str, entity: str, entity_id: int = 0,
            details: str = "", old_values: dict = None,
            new_values: dict = None, user: str = None):
        """
        تسجيل عملية في سجل التدقيق
        
        مثال:
            audit_logger.log(
                action=ACTION_UPDATE,
                entity=ENTITY_EMPLOYEE,
                entity_id=101,
                details="تعديل الراتب",
                old_values={"salary": 5000},
                new_values={"salary": 5500}
            )
        """
        if not cls._initialized:
            cls.setup()
        
        audit_user = user or cls._current_user
        
        # بناء الرسالة
        parts = [details] if details else []
        if old_values and new_values:
            changes = cls._compute_changes(old_values, new_values)
            if changes:
                parts.append(f"التغييرات: {json.dumps(changes, ensure_ascii=False)}")
        elif new_values:
            parts.append(f"القيم: {json.dumps(new_values, ensure_ascii=False)}")
        
        message = " | ".join(parts) if parts else f"{action} on {entity}#{entity_id}"
        
        logger.bind(
            is_audit=True,
            user=audit_user,
            action=action,
            entity=entity,
            entity_id=entity_id,
        ).info(message)
    
    # ─── اختصارات ───
    
    @classmethod
    def log_login(cls, username: str, success: bool):
        """تسجيل دخول/فشل"""
        cls.log(
            user=username,
            action=ACTION_LOGIN if success else ACTION_LOGIN_FAIL,
            entity=ENTITY_USER,
            details=f"{'نجاح' if success else 'فشل'} تسجيل الدخول"
        )
    
    @classmethod
    def log_employee_change(cls, employee_id: int, field: str,
                            old_value: Any, new_value: Any, details: str = ""):
        """تسجيل تعديل بيانات موظف"""
        cls.log(
            action=ACTION_UPDATE,
            entity=ENTITY_EMPLOYEE,
            entity_id=employee_id,
            details=details or f"تعديل {field}",
            old_values={field: str(old_value)},
            new_values={field: str(new_value)}
        )
    
    @classmethod
    def log_payroll_action(cls, employee_id: int, action: str,
                           period: str = "", details: str = "",
                           old_values: dict = None, new_values: dict = None):
        """تسجيل عملية رواتب"""
        msg = f"الفترة: {period} | {details}" if period else details
        cls.log(action=action, entity=ENTITY_PAYROLL, entity_id=employee_id,
                details=msg, old_values=old_values, new_values=new_values)
    
    @classmethod
    def log_export(cls, entity: str, record_count: int,
                   format: str, filename: str = ""):
        """تسجيل تصدير"""
        cls.log(
            action=ACTION_EXPORT, entity=entity,
            details=f"تصدير {record_count} سجل بصيغة {format}"
                    + (f" → {filename}" if filename else "")
        )
    
    @classmethod
    def log_import(cls, entity: str, record_count: int,
                   filename: str, errors: int = 0):
        """تسجيل استيراد"""
        status = f"نجاح: {record_count}" + (f" | أخطاء: {errors}" if errors else "")
        cls.log(action=ACTION_IMPORT, entity=entity,
                details=f"استيراد من {filename} | {status}")
    
    @staticmethod
    def _compute_changes(old: dict, new: dict) -> dict:
        """حساب الفرق بين القديم والجديد"""
        changes = {}
        for key in set(list(old.keys()) + list(new.keys())):
            if str(old.get(key)) != str(new.get(key)):
                changes[key] = {"from": old.get(key), "to": new.get(key)}
        return changes
    
    @classmethod
    def shutdown(cls):
        if cls._initialized:
            cls.log(user="SYSTEM", action="SHUTDOWN", entity="SYSTEM",
                    details="إيقاف سجل التدقيق")
            cls._initialized = False


audit_logger = AuditLogger()
'''

# ─── ملف 3: __init__.py ───
INIT_CODE = r'''# core/logging/__init__.py
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
]
'''

# ──────────────────────────────────────────────
# كتابة الملفات
# ──────────────────────────────────────────────
files_to_create = {
    PROJECT_ROOT / "core" / "logging" / "app_logger.py": APP_LOGGER_CODE,
    PROJECT_ROOT / "core" / "logging" / "audit_logger.py": AUDIT_LOGGER_CODE,
    PROJECT_ROOT / "core" / "logging" / "__init__.py": INIT_CODE,
}

for filepath, code in files_to_create.items():
    # لو الملف موجود، اعمل نسخة احتياطية
    if filepath.exists():
        backup = filepath.with_suffix(f".backup_{datetime.now():%Y%m%d_%H%M%S}")
        filepath.rename(backup)
        print(f"  ⚠️  {filepath.name} كان موجود → نسخة احتياطية: {backup.name}")
    
    filepath.write_text(code.strip() + "\n", encoding="utf-8")
    print(f"  ✅ {filepath.relative_to(PROJECT_ROOT)}")


# ──────────────────────────────────────────────
# الخطوة 3: تحديث .gitignore
# ──────────────────────────────────────────────
print("\n📝 الخطوة 3: تحديث .gitignore...")

gitignore_path = PROJECT_ROOT / ".gitignore"
gitignore_entries = ["logs/", "*.log"]

if gitignore_path.exists():
    existing = gitignore_path.read_text(encoding="utf-8")
else:
    existing = ""

added = []
for entry in gitignore_entries:
    if entry not in existing:
        added.append(entry)

if added:
    with open(gitignore_path, "a", encoding="utf-8") as f:
        f.write("\n# Logging (A1)\n")
        for entry in added:
            f.write(f"{entry}\n")
    print(f"  ✅ أضفنا {added} في .gitignore")
else:
    print(f"  ✅ .gitignore محدّث بالفعل")


# ──────────────────────────────────────────────
# الخطوة 4: اختبار سريع
# ──────────────────────────────────────────────
print("\n🧪 الخطوة 4: اختبار سريع...")

# نضيف مسار المشروع عشان الاستيراد يشتغل
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from core.logging import setup_logging, shutdown_logging, app_logger, audit_logger
    from core.logging.audit_logger import ACTION_UPDATE, ENTITY_EMPLOYEE
    
    setup_logging(log_dir=str(PROJECT_ROOT / "logs"), debug_mode=True)
    
    app_logger.info("اختبار - البرنامج اشتغل")
    app_logger.warning("اختبار - تحذير")
    app_logger.error("اختبار - خطأ")
    
    audit_logger.set_current_user("محمد")
    audit_logger.log(
        action=ACTION_UPDATE,
        entity=ENTITY_EMPLOYEE,
        entity_id=101,
        details="اختبار - تعديل الراتب",
        old_values={"salary": 5000},
        new_values={"salary": 5500}
    )
    audit_logger.log_export(ENTITY_EMPLOYEE, 180, "Excel", "test.xlsx")
    
    shutdown_logging()
    
    import time
    time.sleep(0.5)
    
    # تحقق من الملفات
    log_files = list((PROJECT_ROOT / "logs").glob("*"))
    print(f"\n  📂 ملفات اللوج ({len(log_files)} ملفات):")
    for f in sorted(log_files):
        size_kb = f.stat().st_size / 1024
        print(f"     📄 {f.name} ({size_kb:.1f} KB)")
    
    print("\n  ✅ الاختبار نجح!")

except Exception as e:
    print(f"\n  ❌ الاختبار فشل: {e}")
    import traceback
    traceback.print_exc()


# ──────────────────────────────────────────────
# النتيجة النهائية
# ──────────────────────────────────────────────
print("\n" + "═" * 60)
print("  🎉 تم تركيب نظام الـ Logging بنجاح!")
print("═" * 60)
print()
print("  الملفات اللي اتعملت:")
print("  ─────────────────────")
print("  core/logging/app_logger.py    → اللوجر الرئيسي")
print("  core/logging/audit_logger.py  → سجل التدقيق")
print("  core/logging/__init__.py      → ملف التهيئة")
print("  logs/                         → مجلد ملفات اللوج")
print()
print("  ▶ الخطوة الجاية:")
print("  ─────────────────")
print("  افتح main.py وأضف السطرين دول في أول الملف:")
print()
print('    from core.logging import setup_logging')
print('    setup_logging(debug_mode=True)')
print()
print("═" * 60)
