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

# إخفاء نافذة CMD عند تشغيل subprocess على Windows
CREATE_NO_WINDOW = 0x08000000


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

    logs.append("\u25b6 PULL Mode - \u062c\u0644\u0628 \u0627\u0644\u062a\u062d\u062f\u064a\u062b\u0627\u062a...")
    logs.append("")

    # --- 1. Git Pull ---
    pull_result = _git_pull(logs)

    # --- 2. استعادة الداتابيز ---
    if BACKUP_FILE.exists():
        restore_result = _db_restore(logs)
        if not restore_result:
            success = False
    else:
        logs.append("\u2139\ufe0f \u0644\u0627 \u064a\u0648\u062c\u062f \u0645\u0644\u0641 \u0628\u0627\u0643\u0628 - \u062a\u0645 \u062a\u062e\u0637\u064a \u0627\u0644\u0627\u0633\u062a\u0639\u0627\u062f\u0629")

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

    logs.append("\u25b6 PUSH Mode - \u0631\u0641\u0639 \u0627\u0644\u062a\u063a\u064a\u064a\u0631\u0627\u062a...")
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

    logs.append("\u25b6 FULL Sync - \u0645\u0632\u0627\u0645\u0646\u0629 \u0643\u0627\u0645\u0644\u0629...")
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
            timeout=30, cwd=str(PROJECT_ROOT),
            creationflags=CREATE_NO_WINDOW
        )
        if result.returncode == 0:
            msg = result.stdout.strip()
            if "Already up to date" in msg:
                logs.append("\u2705 Pull: \u0644\u0627 \u062a\u0648\u062c\u062f \u062a\u062d\u062f\u064a\u062b\u0627\u062a \u062c\u062f\u064a\u062f\u0629")
            else:
                logs.append(f"\u2705 Pull: \u062a\u0645 \u062c\u0644\u0628 \u0627\u0644\u062a\u062d\u062f\u064a\u062b\u0627\u062a")
                logs.append(f"   {msg[:120]}")
            return True
        else:
            logs.append(f"\u26a0\ufe0f Pull: {result.stderr.strip()[:120]}")
            return False
    except subprocess.TimeoutExpired:
        logs.append("\u26a0\ufe0f Pull: \u0627\u0646\u062a\u0647\u0649 \u0627\u0644\u0648\u0642\u062a (timeout)")
        return False
    except FileNotFoundError:
        logs.append("\u274c Pull: Git \u063a\u064a\u0631 \u0645\u062b\u0628\u062a!")
        return False
    except Exception as e:
        logs.append(f"\u274c Pull: {e}")
        return False


def _git_add(logs: list):
    """إضافة كل التغييرات."""
    try:
        subprocess.run(
            ["git", "add", "--all"],
            capture_output=True, text=True,
            timeout=15, cwd=str(PROJECT_ROOT),
            creationflags=CREATE_NO_WINDOW
        )
        logs.append("\u2705 Git Add: \u062a\u0645\u062a \u0625\u0636\u0627\u0641\u0629 \u0627\u0644\u0645\u0644\u0641\u0627\u062a")
    except Exception as e:
        logs.append(f"\u26a0\ufe0f Git Add: {e}")


def _git_commit(logs: list):
    """حفظ التغييرات."""
    try:
        msg = f"Sync {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        result = subprocess.run(
            ["git", "commit", "-m", msg],
            capture_output=True, text=True,
            timeout=15, cwd=str(PROJECT_ROOT),
            creationflags=CREATE_NO_WINDOW
        )
        output = result.stdout.strip()
        if "nothing to commit" in output:
            logs.append("\u2139\ufe0f Commit: \u0644\u0627 \u062a\u0648\u062c\u062f \u062a\u063a\u064a\u064a\u0631\u0627\u062a")
        elif result.returncode == 0:
            logs.append(f"\u2705 Commit: {msg}")
        else:
            logs.append(f"\u2139\ufe0f Commit: {output[:80]}")
    except Exception as e:
        logs.append(f"\u274c Commit: {e}")


def _git_push(logs: list) -> bool:
    """رفع التغييرات على GitHub."""
    try:
        result = subprocess.run(
            ["git", "push"],
            capture_output=True, text=True,
            timeout=30, cwd=str(PROJECT_ROOT),
            creationflags=CREATE_NO_WINDOW
        )
        if result.returncode == 0:
            logs.append("\u2705 Push: \u062a\u0645 \u0627\u0644\u0631\u0641\u0639 \u0639\u0644\u0649 GitHub")
            return True
        else:
            err = result.stderr.strip()
            if "Everything up-to-date" in err:
                logs.append("\u2139\ufe0f Push: \u0643\u0644 \u0634\u064a\u0621 \u0645\u062d\u062f\u062b")
                return True
            else:
                logs.append(f"\u26a0\ufe0f Push: {err[:120]}")
                return False
    except subprocess.TimeoutExpired:
        logs.append("\u26a0\ufe0f Push: \u0627\u0646\u062a\u0647\u0649 \u0627\u0644\u0648\u0642\u062a")
        return False
    except Exception as e:
        logs.append(f"\u274c Push: {e}")
        return False


# ═══════════════════════════════════════════════════════
# Database Operations
# ═══════════════════════════════════════════════════════

def _db_backup(logs: list) -> bool:
    """نسخ احتياطي لقاعدة البيانات."""
    try:
        pg_dump = _find_pg_tool("pg_dump")
        if not pg_dump:
            logs.append("\u26a0\ufe0f Backup: pg_dump \u063a\u064a\u0631 \u0645\u0648\u062c\u0648\u062f - \u062a\u0645 \u0627\u0644\u062a\u062e\u0637\u064a")
            return False

        env = os.environ.copy()
        env["PGPASSWORD"] = _get_db_password()

        result = subprocess.run(
            [pg_dump, "-U", "postgres", "-d", "integra",
             "--clean", "--if-exists",
             "-f", str(BACKUP_FILE)],
            capture_output=True, text=True,
            timeout=60, env=env,
            creationflags=CREATE_NO_WINDOW
        )
        if result.returncode == 0:
            size_kb = BACKUP_FILE.stat().st_size / 1024
            logs.append(f"\u2705 Backup: \u062a\u0645 \u0627\u0644\u0646\u0633\u062e ({size_kb:.0f} KB)")
            return True
        else:
            logs.append(f"\u26a0\ufe0f Backup: {result.stderr.strip()[:120]}")
            return False
    except subprocess.TimeoutExpired:
        logs.append("\u26a0\ufe0f Backup: \u0627\u0646\u062a\u0647\u0649 \u0627\u0644\u0648\u0642\u062a")
        return False
    except Exception as e:
        logs.append(f"\u274c Backup: {e}")
        return False


def _db_restore(logs: list) -> bool:
    """استعادة قاعدة البيانات من النسخة الاحتياطية."""
    try:
        psql = _find_pg_tool("psql")
        if not psql:
            logs.append("\u26a0\ufe0f Restore: psql \u063a\u064a\u0631 \u0645\u0648\u062c\u0648\u062f - \u062a\u0645 \u0627\u0644\u062a\u062e\u0637\u064a")
            return False

        if not BACKUP_FILE.exists():
            logs.append("\u2139\ufe0f Restore: \u0644\u0627 \u064a\u0648\u062c\u062f \u0645\u0644\u0641 \u0628\u0627\u0643\u0628")
            return False

        env = os.environ.copy()
        env["PGPASSWORD"] = _get_db_password()

        size_kb = BACKUP_FILE.stat().st_size / 1024
        logs.append(f"\u23f3 Restore: \u062c\u0627\u0631\u064a \u0627\u0633\u062a\u0639\u0627\u062f\u0629 \u0627\u0644\u062f\u0627\u062a\u0627\u0628\u064a\u0632 ({size_kb:.0f} KB)...")

        result = subprocess.run(
            [psql, "-U", "postgres", "-d", "integra",
             "-f", str(BACKUP_FILE),
             "--quiet"],
            capture_output=True, text=True,
            timeout=120, env=env,
            creationflags=CREATE_NO_WINDOW
        )

        if result.returncode == 0:
            logs.append("\u2705 Restore: \u062a\u0645 \u0627\u0633\u062a\u0639\u0627\u062f\u0629 \u0627\u0644\u062f\u0627\u062a\u0627\u0628\u064a\u0632 \u0628\u0646\u062c\u0627\u062d")
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
                logs.append("\u2705 Restore: \u062a\u0645 \u0627\u0633\u062a\u0639\u0627\u062f\u0629 \u0627\u0644\u062f\u0627\u062a\u0627\u0628\u064a\u0632 \u0628\u0646\u062c\u0627\u062d")
                return True
            else:
                logs.append(f"\u26a0\ufe0f Restore: \u062a\u0645\u062a \u0645\u0639 \u062a\u062d\u0630\u064a\u0631\u0627\u062a ({len(error_lines)})")
                for line in error_lines[:3]:
                    logs.append(f"   {line[:100]}")
                return True  # الاستعادة تمت حتى لو في تحذيرات

    except subprocess.TimeoutExpired:
        logs.append("\u26a0\ufe0f Restore: \u0627\u0646\u062a\u0647\u0649 \u0627\u0644\u0648\u0642\u062a (120s)")
        return False
    except Exception as e:
        logs.append(f"\u274c Restore: {e}")
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
            capture_output=True, text=True, timeout=5,
            creationflags=CREATE_NO_WINDOW
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
