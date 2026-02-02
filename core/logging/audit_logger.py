# core/logging/audit_logger.py
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
