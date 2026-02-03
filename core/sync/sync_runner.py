# -*- coding: utf-8 -*-
"""
Sync Runner - v2 Full Automation
=================================
محرك المزامنة الكامل

وضعين للتشغيل:
  PULL: git pull → استعادة الداتابيز (عند فتح البرنامج)
  PUSH: نسخ احتياطي للداتابيز → git commit → git push (عند الإغلاق/يدوي)
"""

import os
import subprocess
from pathlib import Path
from datetime import datetime


# مجلد المشروع
PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKUP_FILE = PROJECT_ROOT / "database_backup.sql"


# ═══════════════════════════════════════════════════════
# PULL Mode - عند فتح البرنامج
# ═══════════════════════════════════════════════════════

def run_sync_pull() -> tuple:
    """
    مزامنة عند الفتح: جلب التحديثات + استعادة الداتابيز.
    Returns:
        (success: bool, logs: list[str])
    """
    logs = []
    success = True

    logs.append("▶ PULL Mode - جلب التحديثات...")
    logs.append("")

    # --- 1. Git Pull ---
    _git_pull(logs)

    # --- 2. استعادة الداتابيز ---
    if BACKUP_FILE.exists():
        restore_result = _db_restore(logs)
        if not restore_result:
            success = False
    else:
        logs.append("ℹ️ لا يوجد ملف باكب - تم تخطي الاستعادة")

    return success, logs


# ═══════════════════════════════════════════════════════
# PUSH Mode - عند الإغلاق / يدوي / دوري
# ═══════════════════════════════════════════════════════

def run_sync_push() -> tuple:
    """
    مزامنة عند الإغلاق: نسخ احتياطي + رفع التغييرات.
    Returns:
        (success: bool, logs: list[str])
    """
    logs = []
    success = True

    logs.append("▶ PUSH Mode - رفع التغييرات...")
    logs.append("")

    # --- 1. Database Backup ---
    _db_backup(logs)

    # --- 2. Git Add ---
    _git_add(logs)

    # --- 3. Git Commit ---
    _git_commit(logs)

    # --- 4. Git Push ---
    push_ok = _git_push(logs)
    if not push_ok:
        success = False

    return success, logs


# ═══════════════════════════════════════════════════════
# Full Sync - يدوي (Pull ثم Push)
# ═══════════════════════════════════════════════════════

def run_sync_full() -> tuple:
    """
    مزامنة كاملة: جلب + نسخ + رفع.
    Returns:
        (success: bool, logs: list[str])
    """
    logs = []
    success = True

    logs.append("▶ FULL Sync - مزامنة كاملة...")
    logs.append("")

    # --- 1. Git Pull ---
    _git_pull(logs)

    # --- 2. Database Restore (لو في ملف backup أحدث) ---
    if BACKUP_FILE.exists():
        _db_restore(logs)

    # --- 3. Database Backup (نسخة جديدة) ---
    _db_backup(logs)

    # --- 4. Git Add + Commit + Push ---
    _git_add(logs)
    _git_commit(logs)
    push_ok = _git_push(logs)
    if not push_ok:
        success = False

    return success, logs


# ═══════════════════════════════════════════════════════
# Git Operations
# ═══════════════════════════════════════════════════════

def _git_pull(logs: list) -> bool:
    """جلب آخر التغييرات من GitHub."""
    try:
        result = subprocess.run(
            ["git", "pull"],
            capture_output=True, text=True,
            timeout=30, cwd=str(PROJECT_ROOT)
        )
        if result.returncode == 0:
            msg = result.stdout.strip()
            if "Already up to date" in msg:
                logs.append("✅ Pull: لا توجد تحديثات جديدة")
            else:
                logs.append("✅ Pull: تم جلب التحديثات")
                logs.append(f"   {msg[:120]}")
            return True
        else:
            logs.append(f"⚠️ Pull: {result.stderr.strip()[:120]}")
            return False
    except subprocess.TimeoutExpired:
        logs.append("⚠️ Pull: انتهى الوقت (timeout)")
        return False
    except FileNotFoundError:
        logs.append("❌ Pull: Git غير مثبت!")
        return False
    except Exception as e:
        logs.append(f"❌ Pull: {e}")
        return False


def _git_add(logs: list):
    """إضافة كل التغييرات."""
    try:
        subprocess.run(
            ["git", "add", "--all"],
            capture_output=True, text=True,
            timeout=15, cwd=str(PROJECT_ROOT)
        )
        logs.append("✅ Git Add: تمت إضافة الملفات")
    except Exception as e:
        logs.append(f"⚠️ Git Add: {e}")


def _git_commit(logs: list):
    """حفظ التغييرات."""
    try:
        msg = f"Sync {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        result = subprocess.run(
            ["git", "commit", "-m", msg],
            capture_output=True, text=True,
            timeout=15, cwd=str(PROJECT_ROOT)
        )
        output = result.stdout.strip()
        if "nothing to commit" in output:
            logs.append("ℹ️ Commit: لا توجد تغييرات")
        elif result.returncode == 0:
            logs.append(f"✅ Commit: {msg}")
        else:
            logs.append(f"ℹ️ Commit: {output[:80]}")
    except Exception as e:
        logs.append(f"❌ Commit: {e}")


def _git_push(logs: list) -> bool:
    """رفع التغييرات على GitHub."""
    try:
        result = subprocess.run(
            ["git", "push"],
            capture_output=True, text=True,
            timeout=30, cwd=str(PROJECT_ROOT)
        )
        if result.returncode == 0:
            logs.append("✅ Push: تم الرفع على GitHub")
            return True
        else:
            err = result.stderr.strip()
            if "Everything up-to-date" in err:
                logs.append("ℹ️ Push: كل شيء محدث")
                return True
            else:
                logs.append(f"⚠️ Push: {err[:120]}")
                return False
    except subprocess.TimeoutExpired:
        logs.append("⚠️ Push: انتهى الوقت")
        return False
    except Exception as e:
        logs.append(f"❌ Push: {e}")
        return False


# ═══════════════════════════════════════════════════════
# Database Operations
# ═══════════════════════════════════════════════════════

def _db_backup(logs: list) -> bool:
    """نسخ احتياطي لقاعدة البيانات."""
    try:
        pg_dump = _find_pg_tool("pg_dump")
        if not pg_dump:
            logs.append("⚠️ Backup: pg_dump غير موجود - تم التخطي")
            return False

        env = os.environ.copy()
        env["PGPASSWORD"] = _get_db_password()

        result = subprocess.run(
            [pg_dump, "-U", "postgres", "-d", "integra",
             "--clean", "--if-exists",
             "-f", str(BACKUP_FILE)],
            capture_output=True, text=True,
            timeout=60, env=env
        )
        if result.returncode == 0:
            size_kb = BACKUP_FILE.stat().st_size / 1024
            logs.append(f"✅ Backup: تم النسخ ({size_kb:.0f} KB)")
            return True
        else:
            logs.append(f"⚠️ Backup: {result.stderr.strip()[:120]}")
            return False
    except subprocess.TimeoutExpired:
        logs.append("⚠️ Backup: انتهى الوقت")
        return False
    except Exception as e:
        logs.append(f"❌ Backup: {e}")
        return False


def _db_restore(logs: list) -> bool:
    """استعادة قاعدة البيانات من النسخة الاحتياطية."""
    try:
        psql = _find_pg_tool("psql")
        if not psql:
            logs.append("⚠️ Restore: psql غير موجود - تم التخطي")
            return False

        if not BACKUP_FILE.exists():
            logs.append("ℹ️ Restore: لا يوجد ملف باكب")
            return False

        env = os.environ.copy()
        env["PGPASSWORD"] = _get_db_password()

        size_kb = BACKUP_FILE.stat().st_size / 1024
        logs.append(f"⏳ Restore: جاري استعادة الداتابيز ({size_kb:.0f} KB)...")

        result = subprocess.run(
            [psql, "-U", "postgres", "-d", "integra",
             "-f", str(BACKUP_FILE),
             "--quiet"],
            capture_output=True, text=True,
            timeout=120, env=env
        )

        if result.returncode == 0:
            logs.append("✅ Restore: تم استعادة الداتابيز بنجاح")
            return True
        else:
            # psql بيرجع errors بس الاستعادة ممكن تكون نجحت جزئياً
            stderr = result.stderr.strip()
            # نتجاهل أخطاء DROP TABLE لأن --clean بيحاول يمسح أولاً
            error_lines = [
                line for line in stderr.split('\n')
                if line.strip()
                and 'NOTICE' not in line
                and 'does not exist' not in line
                and 'already exists' not in line
            ]
            if not error_lines:
                logs.append("✅ Restore: تم استعادة الداتابيز بنجاح")
                return True
            else:
                logs.append(f"⚠️ Restore: تمت مع تحذيرات ({len(error_lines)})")
                for line in error_lines[:3]:
                    logs.append(f"   {line[:100]}")
                return True  # الاستعادة تمت حتى لو في تحذيرات

    except subprocess.TimeoutExpired:
        logs.append("⚠️ Restore: انتهى الوقت (120s)")
        return False
    except Exception as e:
        logs.append(f"❌ Restore: {e}")
        return False


# ═══════════════════════════════════════════════════════
# Utility Functions
# ═══════════════════════════════════════════════════════

def _find_pg_tool(tool_name: str) -> str:
    """البحث عن أداة PostgreSQL (pg_dump أو psql)."""
    if tool_name not in ("pg_dump", "psql"):
        return ""

    exe_name = f"{tool_name}.exe"

    # البحث في المسارات المعروفة
    for version in ["16", "17", "15", "14"]:
        path = rf"C:\Program Files\PostgreSQL\{version}\bin\{exe_name}"
        if os.path.exists(path):
            return path

    # محاولة من PATH
    try:
        result = subprocess.run(
            ["where", tool_name],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip().split("\n")[0]
    except Exception:
        pass

    return ""


def _get_db_password() -> str:
    """قراءة كلمة سر الداتابيز من ملف .env"""
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        try:
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("DB_PASSWORD="):
                        return line.split("=", 1)[1]
        except Exception:
            pass
    return ""
