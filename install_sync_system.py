# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
🔄 INTEGRA - Install Sync System v2 (Full Automation)
═══════════════════════════════════════════════════════════════
نظام مزامنة فائق التطور - أتمتة كاملة
يشمل: Git + Database Backup + Database Restore

عند الفتح: git pull → استعادة الداتابيز تلقائياً
عند الإغلاق: نسخ احتياطي للداتابيز → git push
مزامنة يدوية/دورية: نسخ + رفع

شغّل من مجلد المشروع: python install_sync_system.py
═══════════════════════════════════════════════════════════════
"""

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))

print("=" * 60)
print("   🔄 INTEGRA - تثبيت نظام المزامنة v2")
print("   ⚡ Full Automation Edition")
print("=" * 60)
print()

# ══════════════════════════════════════════════════════════
# الخطوة 1: إنشاء مجلد core/sync
# ══════════════════════════════════════════════════════════

print("[1/8] إنشاء مجلد core/sync...")

SYNC_DIR = os.path.join(BASE, "core", "sync")
os.makedirs(SYNC_DIR, exist_ok=True)

# __init__.py
with open(os.path.join(SYNC_DIR, "__init__.py"), "w", encoding="utf-8") as f:
    f.write('''"""
Sync Module - v2 Full Automation
=================================
نظام المزامنة الكامل بين الأجهزة
يشمل: Git + Database Backup + Database Restore
"""

from .sync_config import load_sync_config, save_sync_config
from .sync_worker import SyncWorker

__all__ = ['load_sync_config', 'save_sync_config', 'SyncWorker']
''')
print("  ✅ __init__.py")

# ══════════════════════════════════════════════════════════
# الخطوة 2: sync_config.py
# ══════════════════════════════════════════════════════════

print("[2/8] إنشاء sync_config.py...")

with open(os.path.join(SYNC_DIR, "sync_config.py"), "w", encoding="utf-8") as f:
    f.write('''# -*- coding: utf-8 -*-
"""
Sync Configuration
==================
تحميل وحفظ إعدادات المزامنة
"""

import json
from pathlib import Path


# ملف الإعدادات في مجلد المشروع
_CONFIG_FILE = Path(__file__).parent.parent.parent / "sync_settings.json"

# الإعدادات الافتراضية
_DEFAULTS = {
    "sync_on_startup": True,
    "sync_on_exit": True,
    "auto_sync_enabled": False,
    "auto_sync_interval_minutes": 30,
    "last_sync_time": "",
    "last_sync_direction": ""
}


def load_sync_config() -> dict:
    """تحميل إعدادات المزامنة."""
    if _CONFIG_FILE.exists():
        try:
            with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            return {**_DEFAULTS, **config}
        except Exception:
            pass
    return dict(_DEFAULTS)


def save_sync_config(config: dict) -> bool:
    """حفظ إعدادات المزامنة."""
    try:
        with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False
''')
print("  ✅ sync_config.py")

# ══════════════════════════════════════════════════════════
# الخطوة 3: sync_runner.py (المحرك الرئيسي)
# ══════════════════════════════════════════════════════════

print("[3/8] إنشاء sync_runner.py (Full Automation)...")

with open(os.path.join(SYNC_DIR, "sync_runner.py"), "w", encoding="utf-8") as f:
    f.write(r'''# -*- coding: utf-8 -*-
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
            timeout=30, cwd=str(PROJECT_ROOT)
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
            timeout=15, cwd=str(PROJECT_ROOT)
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
            timeout=15, cwd=str(PROJECT_ROOT)
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
            timeout=30, cwd=str(PROJECT_ROOT)
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
            timeout=60, env=env
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
            timeout=120, env=env
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
''')
print("  ✅ sync_runner.py (Full Automation)")

# ══════════════════════════════════════════════════════════
# الخطوة 4: sync_worker.py (يدعم الأوضاع المختلفة)
# ══════════════════════════════════════════════════════════

print("[4/8] إنشاء sync_worker.py...")

with open(os.path.join(SYNC_DIR, "sync_worker.py"), "w", encoding="utf-8") as f:
    f.write('''# -*- coding: utf-8 -*-
"""
Sync Worker - v2
================
تشغيل المزامنة في thread منفصل (عشان الواجهة متقفش)
يدعم 3 أوضاع: pull / push / full
"""

from PyQt5.QtCore import QThread, pyqtSignal
from .sync_runner import run_sync_pull, run_sync_push, run_sync_full


class SyncWorker(QThread):
    """
    Worker thread للمزامنة.

    Args:
        mode: "pull" / "push" / "full"

    Signals:
        finished(bool, list): نتيجة المزامنة (نجاح, سجل العمليات)
        log_message(str): رسالة لحظية أثناء المزامنة
    """

    finished = pyqtSignal(bool, list)
    log_message = pyqtSignal(str)

    def __init__(self, mode: str = "push", parent=None):
        super().__init__(parent)
        self._mode = mode

    def run(self):
        """تنفيذ المزامنة حسب الوضع."""
        try:
            if self._mode == "pull":
                success, logs = run_sync_pull()
            elif self._mode == "full":
                success, logs = run_sync_full()
            else:
                success, logs = run_sync_push()

            self.finished.emit(success, logs)
        except Exception as e:
            self.finished.emit(False, [f"\\u274c Error: {e}"])
''')
print("  ✅ sync_worker.py")

# ══════════════════════════════════════════════════════════
# الخطوة 5: شاشة إعدادات المزامنة
# ══════════════════════════════════════════════════════════

print("[5/8] إنشاء شاشة إعدادات المزامنة...")

SYNC_DIALOG_DIR = os.path.join(BASE, "ui", "dialogs", "sync_settings")
os.makedirs(SYNC_DIALOG_DIR, exist_ok=True)

# __init__.py
with open(os.path.join(SYNC_DIALOG_DIR, "__init__.py"), "w", encoding="utf-8") as f:
    f.write('''"""Sync Settings Dialog."""

from .sync_settings_dialog import SyncSettingsDialog

__all__ = ['SyncSettingsDialog']
''')

# sync_settings_dialog.py
with open(os.path.join(SYNC_DIALOG_DIR, "sync_settings_dialog.py"), "w", encoding="utf-8") as f:
    f.write('''# -*- coding: utf-8 -*-
"""
Sync Settings Dialog - v2
=========================
شاشة إعدادات المزامنة مع دعم كامل للأوضاع المختلفة
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QSpinBox, QFrame,
    QTextEdit, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.themes import get_current_theme
from core.sync import load_sync_config, save_sync_config, SyncWorker


class SyncSettingsDialog(QDialog):
    """شاشة إعدادات المزامنة."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("\\U0001f504 \\u0625\\u0639\\u062f\\u0627\\u062f\\u0627\\u062a \\u0627\\u0644\\u0645\\u0632\\u0627\\u0645\\u0646\\u0629")
        self.setMinimumSize(600, 600)
        self._worker = None
        self._config = load_sync_config()

        self._setup_ui()
        self._apply_theme()
        self._load_settings()

    def _setup_ui(self):
        """بناء الواجهة."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # === العنوان ===
        title = QLabel("\\U0001f504 \\u0625\\u0639\\u062f\\u0627\\u062f\\u0627\\u062a \\u0627\\u0644\\u0645\\u0632\\u0627\\u0645\\u0646\\u0629")
        title.setFont(QFont("Cairo", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("dialogTitle")
        layout.addWidget(title)

        # === شرح مختصر ===
        desc = QLabel(
            "\\U0001f4e1 \\u0627\\u0644\\u0645\\u0632\\u0627\\u0645\\u0646\\u0629 \\u0628\\u062a\\u0646\\u0642\\u0644 \\u0627\\u0644\\u0643\\u0648\\u062f \\u0648\\u0627\\u0644\\u062f\\u0627\\u062a\\u0627\\u0628\\u064a\\u0632 \\u0628\\u064a\\u0646 \\u0627\\u0644\\u0623\\u062c\\u0647\\u0632\\u0629 \\u062a\\u0644\\u0642\\u0627\\u0626\\u064a\\u0627\\u064b"
        )
        desc.setFont(QFont("Cairo", 10))
        desc.setAlignment(Qt.AlignCenter)
        desc.setObjectName("descLabel")
        layout.addWidget(desc)

        # === خيارات الأتمتة ===
        auto_group = QGroupBox("\\u2699\\ufe0f \\u0627\\u0644\\u0623\\u062a\\u0645\\u062a\\u0629")
        auto_group.setFont(QFont("Cairo", 12, QFont.Bold))
        auto_group.setObjectName("optionsGroup")
        auto_layout = QVBoxLayout(auto_group)
        auto_layout.setSpacing(12)
        auto_layout.setContentsMargins(20, 20, 20, 20)

        # خيار 1: عند فتح البرنامج
        self._chk_startup = QCheckBox(
            "\\U0001f504 \\u0639\\u0646\\u062f \\u0627\\u0644\\u0641\\u062a\\u062d: \\u062c\\u0644\\u0628 \\u0627\\u0644\\u062a\\u062d\\u062f\\u064a\\u062b\\u0627\\u062a + \\u0627\\u0633\\u062a\\u0639\\u0627\\u062f\\u0629 \\u0627\\u0644\\u062f\\u0627\\u062a\\u0627\\u0628\\u064a\\u0632  (git pull + restore)"
        )
        self._chk_startup.setFont(QFont("Cairo", 11))
        auto_layout.addWidget(self._chk_startup)

        # خيار 2: عند إغلاق البرنامج
        self._chk_exit = QCheckBox(
            "\\U0001f6aa \\u0639\\u0646\\u062f \\u0627\\u0644\\u0625\\u063a\\u0644\\u0627\\u0642: \\u0646\\u0633\\u062e \\u0627\\u0644\\u062f\\u0627\\u062a\\u0627\\u0628\\u064a\\u0632 + \\u0631\\u0641\\u0639 \\u0627\\u0644\\u062a\\u063a\\u064a\\u064a\\u0631\\u0627\\u062a  (backup + git push)"
        )
        self._chk_exit.setFont(QFont("Cairo", 11))
        auto_layout.addWidget(self._chk_exit)

        # خيار 3: مزامنة دورية
        auto_row = QHBoxLayout()
        self._chk_auto = QCheckBox(
            "\\u23f0 \\u0645\\u0632\\u0627\\u0645\\u0646\\u0629 \\u062f\\u0648\\u0631\\u064a\\u0629 (backup + push) \\u0643\\u0644:"
        )
        self._chk_auto.setFont(QFont("Cairo", 11))
        auto_row.addWidget(self._chk_auto)

        self._spin_interval = QSpinBox()
        self._spin_interval.setRange(5, 240)
        self._spin_interval.setValue(30)
        self._spin_interval.setSuffix(" \\u062f\\u0642\\u064a\\u0642\\u0629")
        self._spin_interval.setFont(QFont("Cairo", 11))
        self._spin_interval.setMinimumHeight(35)
        self._spin_interval.setMinimumWidth(120)
        self._spin_interval.setObjectName("intervalSpin")
        auto_row.addWidget(self._spin_interval)
        auto_row.addStretch()
        auto_layout.addLayout(auto_row)

        layout.addWidget(auto_group)

        # === أزرار المزامنة اليدوية ===
        sync_group = QGroupBox("\\U0001f3ae \\u0645\\u0632\\u0627\\u0645\\u0646\\u0629 \\u064a\\u062f\\u0648\\u064a\\u0629")
        sync_group.setFont(QFont("Cairo", 12, QFont.Bold))
        sync_group.setObjectName("optionsGroup")
        sync_layout = QHBoxLayout(sync_group)
        sync_layout.setSpacing(12)
        sync_layout.setContentsMargins(20, 20, 20, 20)

        # زرار Pull
        self._pull_btn = QPushButton("\\u2b07\\ufe0f \\u062c\\u0644\\u0628 + \\u0627\\u0633\\u062a\\u0639\\u0627\\u062f\\u0629")
        self._pull_btn.setFont(QFont("Cairo", 12, QFont.Bold))
        self._pull_btn.setMinimumHeight(45)
        self._pull_btn.setCursor(Qt.PointingHandCursor)
        self._pull_btn.setObjectName("pullBtn")
        self._pull_btn.setToolTip("git pull + database restore")
        self._pull_btn.clicked.connect(lambda: self._on_sync("pull"))
        sync_layout.addWidget(self._pull_btn)

        # زرار Push
        self._push_btn = QPushButton("\\u2b06\\ufe0f \\u0646\\u0633\\u062e + \\u0631\\u0641\\u0639")
        self._push_btn.setFont(QFont("Cairo", 12, QFont.Bold))
        self._push_btn.setMinimumHeight(45)
        self._push_btn.setCursor(Qt.PointingHandCursor)
        self._push_btn.setObjectName("pushBtn")
        self._push_btn.setToolTip("database backup + git push")
        self._push_btn.clicked.connect(lambda: self._on_sync("push"))
        sync_layout.addWidget(self._push_btn)

        # زرار Full
        self._full_btn = QPushButton("\\U0001f504 \\u0645\\u0632\\u0627\\u0645\\u0646\\u0629 \\u0643\\u0627\\u0645\\u0644\\u0629")
        self._full_btn.setFont(QFont("Cairo", 12, QFont.Bold))
        self._full_btn.setMinimumHeight(45)
        self._full_btn.setCursor(Qt.PointingHandCursor)
        self._full_btn.setObjectName("syncNowBtn")
        self._full_btn.setToolTip("pull + restore + backup + push")
        self._full_btn.clicked.connect(lambda: self._on_sync("full"))
        sync_layout.addWidget(self._full_btn)

        layout.addWidget(sync_group)

        # === آخر مزامنة ===
        self._status_label = QLabel("")
        self._status_label.setFont(QFont("Cairo", 11))
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setObjectName("statusLabel")
        layout.addWidget(self._status_label)

        # === سجل العمليات ===
        log_label = QLabel("\\U0001f4cb \\u0633\\u062c\\u0644 \\u0627\\u0644\\u0639\\u0645\\u0644\\u064a\\u0627\\u062a:")
        log_label.setFont(QFont("Cairo", 11))
        log_label.setObjectName("logLabel")
        layout.addWidget(log_label)

        self._log_area = QTextEdit()
        self._log_area.setReadOnly(True)
        self._log_area.setFont(QFont("Consolas", 10))
        self._log_area.setMinimumHeight(120)
        self._log_area.setObjectName("logArea")
        self._log_area.setPlaceholderText(
            "\\u0627\\u062e\\u062a\\u0631 \\u0646\\u0648\\u0639 \\u0627\\u0644\\u0645\\u0632\\u0627\\u0645\\u0646\\u0629 \\u0644\\u0639\\u0631\\u0636 \\u0627\\u0644\\u0646\\u062a\\u0627\\u0626\\u062c..."
        )
        layout.addWidget(self._log_area)

        # === أزرار حفظ وإلغاء ===
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("\\u0625\\u0644\\u063a\\u0627\\u0621")
        cancel_btn.setFont(QFont("Cairo", 12))
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setMinimumWidth(120)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("\\U0001f4be \\u062d\\u0641\\u0638 \\u0627\\u0644\\u0625\\u0639\\u062f\\u0627\\u062f\\u0627\\u062a")
        save_btn.setFont(QFont("Cairo", 12, QFont.Bold))
        save_btn.setMinimumHeight(40)
        save_btn.setMinimumWidth(160)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setObjectName("saveBtn")
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _load_settings(self):
        """تحميل الإعدادات الحالية."""
        self._chk_startup.setChecked(self._config.get("sync_on_startup", True))
        self._chk_exit.setChecked(self._config.get("sync_on_exit", True))
        self._chk_auto.setChecked(self._config.get("auto_sync_enabled", False))
        self._spin_interval.setValue(self._config.get("auto_sync_interval_minutes", 30))

        last = self._config.get("last_sync_time", "")
        direction = self._config.get("last_sync_direction", "")
        if last:
            dir_text = {"pull": "\\u2b07\\ufe0f \\u062c\\u0644\\u0628", "push": "\\u2b06\\ufe0f \\u0631\\u0641\\u0639", "full": "\\U0001f504 \\u0643\\u0627\\u0645\\u0644\\u0629"}.get(direction, "")
            self._status_label.setText(f"\\u0622\\u062e\\u0631 \\u0645\\u0632\\u0627\\u0645\\u0646\\u0629: {last} {dir_text} \\u2705")
        else:
            self._status_label.setText("\\u0644\\u0645 \\u062a\\u062a\\u0645 \\u0645\\u0632\\u0627\\u0645\\u0646\\u0629 \\u0628\\u0639\\u062f")

    def _on_save(self):
        """حفظ الإعدادات."""
        self._config["sync_on_startup"] = self._chk_startup.isChecked()
        self._config["sync_on_exit"] = self._chk_exit.isChecked()
        self._config["auto_sync_enabled"] = self._chk_auto.isChecked()
        self._config["auto_sync_interval_minutes"] = self._spin_interval.value()
        save_sync_config(self._config)
        self.accept()

    def _on_sync(self, mode: str):
        """تشغيل المزامنة."""
        if self._worker and self._worker.isRunning():
            return

        # تعطيل الأزرار
        self._pull_btn.setEnabled(False)
        self._push_btn.setEnabled(False)
        self._full_btn.setEnabled(False)

        mode_names = {"pull": "\\u062c\\u0644\\u0628 + \\u0627\\u0633\\u062a\\u0639\\u0627\\u062f\\u0629", "push": "\\u0646\\u0633\\u062e + \\u0631\\u0641\\u0639", "full": "\\u0645\\u0632\\u0627\\u0645\\u0646\\u0629 \\u0643\\u0627\\u0645\\u0644\\u0629"}
        self._log_area.clear()
        self._log_area.append(f"\\u23f3 \\u062c\\u0627\\u0631\\u064a: {mode_names.get(mode, mode)}...\\n")

        self._current_mode = mode
        self._worker = SyncWorker(mode=mode)
        self._worker.finished.connect(self._on_sync_finished)
        self._worker.start()

    def _on_sync_finished(self, success, logs):
        """بعد انتهاء المزامنة."""
        from datetime import datetime

        for log in logs:
            self._log_area.append(f"  {log}")

        self._log_area.append("")
        if success:
            self._log_area.append("\\u2705 \\u062a\\u0645\\u062a \\u0627\\u0644\\u0645\\u0632\\u0627\\u0645\\u0646\\u0629 \\u0628\\u0646\\u062c\\u0627\\u062d!")
        else:
            self._log_area.append("\\u26a0\\ufe0f \\u0627\\u0644\\u0645\\u0632\\u0627\\u0645\\u0646\\u0629 \\u0644\\u0645 \\u062a\\u0643\\u062a\\u0645\\u0644 \\u0628\\u0646\\u062c\\u0627\\u062d")

        # تحديث وقت آخر مزامنة
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        self._config["last_sync_time"] = now
        self._config["last_sync_direction"] = getattr(self, "_current_mode", "")
        save_sync_config(self._config)

        mode = getattr(self, "_current_mode", "")
        dir_text = {"pull": "\\u2b07\\ufe0f \\u062c\\u0644\\u0628", "push": "\\u2b06\\ufe0f \\u0631\\u0641\\u0639", "full": "\\U0001f504 \\u0643\\u0627\\u0645\\u0644\\u0629"}.get(mode, "")
        self._status_label.setText(f"\\u0622\\u062e\\u0631 \\u0645\\u0632\\u0627\\u0645\\u0646\\u0629: {now} {dir_text} \\u2705")

        # تفعيل الأزرار
        self._pull_btn.setEnabled(True)
        self._push_btn.setEnabled(True)
        self._full_btn.setEnabled(True)

    def _apply_theme(self):
        """تطبيق الثيم."""
        theme = get_current_theme()

        if theme == "dark":
            self.setStyleSheet("""
                QDialog { background-color: #0f172a; }
                QLabel { color: #f1f5f9; background: transparent; }
                QLabel#dialogTitle { color: #38bdf8; }
                QLabel#descLabel { color: #64748b; }
                QLabel#statusLabel { color: #94a3b8; }
                QLabel#logLabel { color: #94a3b8; }

                QGroupBox {
                    color: #06b6d4;
                    border: 1px solid #334155;
                    border-radius: 10px;
                    margin-top: 10px;
                    padding-top: 15px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 15px;
                    padding: 0 8px;
                }

                QCheckBox { color: #f1f5f9; spacing: 10px; }
                QCheckBox::indicator {
                    width: 22px; height: 22px;
                    border: 2px solid #475569;
                    border-radius: 4px;
                    background: #1e293b;
                }
                QCheckBox::indicator:checked {
                    background: #06b6d4;
                    border-color: #06b6d4;
                }
                QCheckBox::indicator:hover { border-color: #06b6d4; }

                QSpinBox {
                    background: #1e293b; color: #f1f5f9;
                    border: 2px solid #334155; border-radius: 6px;
                    padding: 5px 10px;
                }
                QSpinBox:focus { border-color: #06b6d4; }

                QPushButton#pullBtn {
                    background: #0d9488; color: #ffffff;
                    border: none; border-radius: 10px;
                }
                QPushButton#pullBtn:hover { background: #14b8a6; }
                QPushButton#pullBtn:disabled { background: #334155; color: #64748b; }

                QPushButton#pushBtn {
                    background: #7c3aed; color: #ffffff;
                    border: none; border-radius: 10px;
                }
                QPushButton#pushBtn:hover { background: #8b5cf6; }
                QPushButton#pushBtn:disabled { background: #334155; color: #64748b; }

                QPushButton#syncNowBtn {
                    background: #0891b2; color: #ffffff;
                    border: none; border-radius: 10px;
                }
                QPushButton#syncNowBtn:hover { background: #06b6d4; }
                QPushButton#syncNowBtn:disabled { background: #334155; color: #64748b; }

                QPushButton#saveBtn {
                    background: #10b981; color: #ffffff;
                    border: none; border-radius: 8px;
                    padding: 8px 20px;
                }
                QPushButton#saveBtn:hover { background: #059669; }

                QPushButton#cancelBtn {
                    background: #334155; color: #f1f5f9;
                    border: none; border-radius: 8px;
                    padding: 8px 20px;
                }
                QPushButton#cancelBtn:hover { background: #475569; }

                QTextEdit#logArea {
                    background: #1e293b; color: #e2e8f0;
                    border: 1px solid #334155; border-radius: 8px;
                    padding: 10px;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog { background-color: #f8fafc; }
                QLabel { color: #1e293b; background: transparent; }
                QLabel#dialogTitle { color: #0891b2; }
                QLabel#descLabel { color: #94a3b8; }
                QLabel#statusLabel { color: #64748b; }
                QLabel#logLabel { color: #64748b; }

                QGroupBox {
                    color: #0891b2;
                    border: 1px solid #e2e8f0;
                    border-radius: 10px;
                    margin-top: 10px;
                    padding-top: 15px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 15px;
                    padding: 0 8px;
                }

                QCheckBox { color: #1e293b; spacing: 10px; }
                QCheckBox::indicator {
                    width: 22px; height: 22px;
                    border: 2px solid #cbd5e1;
                    border-radius: 4px;
                    background: #ffffff;
                }
                QCheckBox::indicator:checked {
                    background: #0891b2;
                    border-color: #0891b2;
                }

                QSpinBox {
                    background: #ffffff; color: #1e293b;
                    border: 2px solid #e2e8f0; border-radius: 6px;
                    padding: 5px 10px;
                }

                QPushButton#pullBtn {
                    background: #0d9488; color: #ffffff;
                    border: none; border-radius: 10px;
                }
                QPushButton#pullBtn:hover { background: #14b8a6; }
                QPushButton#pullBtn:disabled { background: #e2e8f0; color: #94a3b8; }

                QPushButton#pushBtn {
                    background: #7c3aed; color: #ffffff;
                    border: none; border-radius: 10px;
                }
                QPushButton#pushBtn:hover { background: #8b5cf6; }
                QPushButton#pushBtn:disabled { background: #e2e8f0; color: #94a3b8; }

                QPushButton#syncNowBtn {
                    background: #0891b2; color: #ffffff;
                    border: none; border-radius: 10px;
                }
                QPushButton#syncNowBtn:hover { background: #06b6d4; }
                QPushButton#syncNowBtn:disabled { background: #e2e8f0; color: #94a3b8; }

                QPushButton#saveBtn {
                    background: #10b981; color: #ffffff;
                    border: none; border-radius: 8px;
                    padding: 8px 20px;
                }
                QPushButton#cancelBtn {
                    background: #e2e8f0; color: #1e293b;
                    border: none; border-radius: 8px;
                    padding: 8px 20px;
                }

                QTextEdit#logArea {
                    background: #ffffff; color: #334155;
                    border: 1px solid #e2e8f0; border-radius: 8px;
                    padding: 10px;
                }
            """)
''')
print("  ✅ sync_settings_dialog.py")

# ══════════════════════════════════════════════════════════
# الخطوة 6: تحديث ui/dialogs/__init__.py
# ══════════════════════════════════════════════════════════

print("[6/8] تحديث ui/dialogs/__init__.py...")

DIALOGS_INIT = os.path.join(BASE, "ui", "dialogs", "__init__.py")

new_dialogs_init = '''"""
Dialogs
=======
All application dialogs.
"""

from .settings import SettingsDialog
from .themes import ThemesDialog
from .sync_settings import SyncSettingsDialog
from .message import show_info, show_warning, show_error, show_success, confirm

__all__ = [
    'SettingsDialog',
    'ThemesDialog',
    'SyncSettingsDialog',
    'show_info',
    'show_warning',
    'show_error',
    'show_success',
    'confirm'
]
'''

with open(DIALOGS_INIT, "w", encoding="utf-8") as f:
    f.write(new_dialogs_init)
print("  ✅ تم التحديث")

# ══════════════════════════════════════════════════════════
# الخطوة 7: تحديث launcher_window.py
# ══════════════════════════════════════════════════════════

print("[7/8] تحديث launcher_window.py...")

LW_FILE = os.path.join(BASE, "ui", "windows", "launcher", "launcher_window.py")

new_launcher = '''"""
Launcher Window
===============
Main application launcher window.
Includes full sync automation (Git + Database).
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer

from ui.windows.base import BaseWindow
from ui.dialogs import SettingsDialog, ThemesDialog, SyncSettingsDialog

from .launcher_menu import create_launcher_menu
from .launcher_header import create_launcher_header
from .launcher_cards_area import LauncherCardsArea
from .launcher_statusbar import LauncherStatusBar

from core.database.connection import connect
from core.themes import get_stylesheet, apply_theme
from core.sync import SyncWorker, load_sync_config, save_sync_config


class LauncherWindow(BaseWindow):
    """
    Main launcher window.
    Shows module cards and provides navigation.
    Includes automated sync system (Git + Database).
    """

    # Store references to open module windows
    _open_windows = {}

    def __init__(self):
        super().__init__()

        # Connect to database
        connect()

        # Sync system
        self._sync_worker = None
        self._sync_timer = QTimer()
        self._sync_timer.timeout.connect(self._auto_sync)

        # Setup UI
        self._setup_ui()
        self._setup_connections()

        # Maximize on start
        self.showMaximized()

        # Startup sync (PULL mode: git pull + database restore)
        self._init_sync()

    def _setup_ui(self):
        """Setup the window UI."""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        # Main layout
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header (INTEGRA logo)
        header = create_launcher_header()
        layout.addWidget(header)

        # Cards area
        self.cards_area = LauncherCardsArea()
        layout.addWidget(self.cards_area, 1)

        # Spacer
        layout.addStretch()

        # Menu bar
        self.menu_actions = create_launcher_menu(self)

        # Sync menu
        sync_menu = self.menuBar().addMenu("\\U0001f504 \\u0627\\u0644\\u0645\\u0632\\u0627\\u0645\\u0646\\u0629")
        self._sync_pull_action = sync_menu.addAction(
            "\\u2b07\\ufe0f \\u062c\\u0644\\u0628 + \\u0627\\u0633\\u062a\\u0639\\u0627\\u062f\\u0629 (Pull)"
        )
        self._sync_push_action = sync_menu.addAction(
            "\\u2b06\\ufe0f \\u0646\\u0633\\u062e + \\u0631\\u0641\\u0639 (Push)"
        )
        self._sync_full_action = sync_menu.addAction(
            "\\U0001f504 \\u0645\\u0632\\u0627\\u0645\\u0646\\u0629 \\u0643\\u0627\\u0645\\u0644\\u0629 (Full)"
        )
        sync_menu.addSeparator()
        self._sync_settings_action = sync_menu.addAction(
            "\\u2699\\ufe0f \\u0625\\u0639\\u062f\\u0627\\u062f\\u0627\\u062a \\u0627\\u0644\\u0645\\u0632\\u0627\\u0645\\u0646\\u0629"
        )

        # Status bar
        self.status_bar = LauncherStatusBar()
        self.setStatusBar(self.status_bar)

    def _setup_connections(self):
        """Setup signal connections."""
        # Menu actions
        self.menu_actions['settings'].triggered.connect(self._show_settings)
        self.menu_actions['themes'].triggered.connect(self._show_themes)
        self.menu_actions['exit'].triggered.connect(self.close)

        # Module cards
        self.cards_area.module_clicked.connect(self._open_module)

        # Sync actions
        self._sync_pull_action.triggered.connect(lambda: self._run_sync("pull"))
        self._sync_push_action.triggered.connect(lambda: self._run_sync("push"))
        self._sync_full_action.triggered.connect(lambda: self._run_sync("full"))
        self._sync_settings_action.triggered.connect(self._show_sync_settings)

    # ═══════════════════════════════════════════════════════
    # Sync Methods - Full Automation
    # ═══════════════════════════════════════════════════════

    def _init_sync(self):
        """تهيئة نظام المزامنة عند بدء البرنامج."""
        config = load_sync_config()

        # تشغيل المزامنة الدورية لو مفعّلة
        if config.get("auto_sync_enabled", False):
            interval = config.get("auto_sync_interval_minutes", 30)
            self._sync_timer.start(interval * 60 * 1000)

        # مزامنة عند الفتح (PULL: git pull + database restore)
        if config.get("sync_on_startup", True):
            self.status_bar.showMessage(
                "\\U0001f504 \\u062c\\u0627\\u0631\\u064a \\u062c\\u0644\\u0628 \\u0627\\u0644\\u062a\\u062d\\u062f\\u064a\\u062b\\u0627\\u062a + \\u0627\\u0633\\u062a\\u0639\\u0627\\u062f\\u0629 \\u0627\\u0644\\u062f\\u0627\\u062a\\u0627\\u0628\\u064a\\u0632..."
            )
            self._run_sync("pull")

    def _auto_sync(self):
        """مزامنة دورية تلقائية (PUSH mode)."""
        if self._sync_worker and self._sync_worker.isRunning():
            return
        self.status_bar.showMessage(
            "\\U0001f504 \\u0645\\u0632\\u0627\\u0645\\u0646\\u0629 \\u062f\\u0648\\u0631\\u064a\\u0629..."
        )
        self._run_sync("push")

    def _run_sync(self, mode: str = "push"):
        """تشغيل المزامنة في الخلفية."""
        if self._sync_worker and self._sync_worker.isRunning():
            return

        self._current_sync_mode = mode
        self._sync_worker = SyncWorker(mode=mode)
        self._sync_worker.finished.connect(self._on_sync_finished)
        self._sync_worker.start()

        mode_names = {
            "pull": "\\u062c\\u0644\\u0628 + \\u0627\\u0633\\u062a\\u0639\\u0627\\u062f\\u0629",
            "push": "\\u0646\\u0633\\u062e + \\u0631\\u0641\\u0639",
            "full": "\\u0645\\u0632\\u0627\\u0645\\u0646\\u0629 \\u0643\\u0627\\u0645\\u0644\\u0629"
        }
        self.status_bar.showMessage(
            f"\\U0001f504 \\u062c\\u0627\\u0631\\u064a: {mode_names.get(mode, mode)}..."
        )

    def _on_sync_finished(self, success, logs):
        """بعد انتهاء المزامنة."""
        from datetime import datetime

        # تحديث وقت آخر مزامنة
        config = load_sync_config()
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        config["last_sync_time"] = now
        config["last_sync_direction"] = getattr(self, "_current_sync_mode", "")
        save_sync_config(config)

        mode = getattr(self, "_current_sync_mode", "")
        mode_icons = {"pull": "\\u2b07\\ufe0f", "push": "\\u2b06\\ufe0f", "full": "\\U0001f504"}
        icon = mode_icons.get(mode, "\\U0001f504")

        if success:
            self.status_bar.showMessage(
                f"\\u2705 \\u062a\\u0645\\u062a \\u0627\\u0644\\u0645\\u0632\\u0627\\u0645\\u0646\\u0629 {icon} - {now}"
            )
        else:
            self.status_bar.showMessage(
                f"\\u26a0\\ufe0f \\u0627\\u0644\\u0645\\u0632\\u0627\\u0645\\u0646\\u0629 \\u0644\\u0645 \\u062a\\u0643\\u062a\\u0645\\u0644 {icon}"
            )

        # طباعة السجل في الكونسول
        for log in logs:
            print(f"  [SYNC] {log}")

    def _show_sync_settings(self):
        """عرض شاشة إعدادات المزامنة."""
        dialog = SyncSettingsDialog(self)
        if dialog.exec_():
            # إعادة ضبط المؤقت حسب الإعدادات الجديدة
            config = load_sync_config()
            if config.get("auto_sync_enabled", False):
                interval = config.get("auto_sync_interval_minutes", 30)
                self._sync_timer.start(interval * 60 * 1000)
            else:
                self._sync_timer.stop()

    # ═══════════════════════════════════════════════════════
    # Existing Methods
    # ═══════════════════════════════════════════════════════

    def _show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self)
        dialog.exec_()

    def _show_themes(self):
        """Show themes dialog."""
        dialog = ThemesDialog(self)
        if dialog.exec_():
            # Refresh theme
            self.setStyleSheet(get_stylesheet())

            # Refresh all open windows
            for window in self._open_windows.values():
                if window and window.isVisible():
                    window.setStyleSheet(get_stylesheet())

    def _open_module(self, module_id):
        """Open a module window."""
        # Check if already open
        if module_id in self._open_windows:
            window = self._open_windows[module_id]
            if window and window.isVisible():
                window.activateWindow()
                window.raise_()
                return

        # Open new window based on module
        if module_id == "mostahaqat":
            from modules.mostahaqat import MostahaqatWindow
            window = MostahaqatWindow()
            window.show()
            self._open_windows[module_id] = window
        else:
            # Module not implemented yet
            from ui.dialogs import show_info
            show_info(self, "\\u0642\\u0631\\u064a\\u0628\\u0627\\u064b", f"\\u0645\\u0648\\u062f\\u064a\\u0648\\u0644 {module_id} \\u0642\\u064a\\u062f \\u0627\\u0644\\u062a\\u0637\\u0648\\u064a\\u0631")

    def closeEvent(self, event):
        """Handle window close - PUSH sync if enabled."""
        # مزامنة عند الإغلاق (PUSH: backup + commit + push)
        try:
            config = load_sync_config()
            if config.get("sync_on_exit", True):
                self.status_bar.showMessage(
                    "\\U0001f504 \\u062c\\u0627\\u0631\\u064a \\u0646\\u0633\\u062e \\u0627\\u0644\\u062f\\u0627\\u062a\\u0627\\u0628\\u064a\\u0632 + \\u0631\\u0641\\u0639 \\u0627\\u0644\\u062a\\u063a\\u064a\\u064a\\u0631\\u0627\\u062a..."
                )
                self.repaint()

                # تشغيل متزامن (مش في الخلفية) عشان البرنامج مش يقفل قبل ما يخلص
                from core.sync.sync_runner import run_sync_push
                success, logs = run_sync_push()

                for log in logs:
                    print(f"  [EXIT SYNC] {log}")

                # تحديث وقت آخر مزامنة
                from datetime import datetime
                config["last_sync_time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                config["last_sync_direction"] = "push"
                save_sync_config(config)

        except Exception as e:
            print(f"[SYNC] Exit sync error: {e}")

        # إغلاق كل النوافذ المفتوحة
        for window in self._open_windows.values():
            if window:
                window.close()

        # إيقاف المؤقت
        self._sync_timer.stop()

        event.accept()
'''

with open(LW_FILE, "w", encoding="utf-8") as f:
    f.write(new_launcher)
print("  ✅ تم التحديث")

# ══════════════════════════════════════════════════════════
# الخطوة 8: التحقق
# ══════════════════════════════════════════════════════════

print()
print("[8/8] التحقق من الملفات...")

files_to_check = [
    os.path.join(SYNC_DIR, "__init__.py"),
    os.path.join(SYNC_DIR, "sync_config.py"),
    os.path.join(SYNC_DIR, "sync_runner.py"),
    os.path.join(SYNC_DIR, "sync_worker.py"),
    os.path.join(SYNC_DIALOG_DIR, "__init__.py"),
    os.path.join(SYNC_DIALOG_DIR, "sync_settings_dialog.py"),
    DIALOGS_INIT,
    LW_FILE,
]

all_ok = True
for f_path in files_to_check:
    if os.path.exists(f_path):
        size = os.path.getsize(f_path)
        name = os.path.relpath(f_path, BASE)
        print(f"  ✅ {name} ({size:,} bytes)")
    else:
        print(f"  ❌ {f_path} - غير موجود!")
        all_ok = False

print()
print("=" * 60)
if all_ok:
    print("   ✅ تم تثبيت نظام المزامنة v2 بنجاح!")
    print()
    print("   ⚡ الأتمتة الكاملة:")
    print("   ┌─────────────────────────────────────────┐")
    print("   │ فتح البرنامج → git pull + DB restore    │")
    print("   │ إغلاق البرنامج → DB backup + git push   │")
    print("   │ مزامنة دورية → DB backup + git push     │")
    print("   │ مزامنة يدوية → اختر Pull/Push/Full      │")
    print("   └─────────────────────────────────────────┘")
    print()
    print("   شغّل البرنامج: python main.py")
    print("   يمكنك حذف: install_sync_system.py")
else:
    print("   ⚠️ بعض الملفات ناقصة - راجع الأخطاء")
print("=" * 60)

input("\nاضغط Enter للإغلاق...")
