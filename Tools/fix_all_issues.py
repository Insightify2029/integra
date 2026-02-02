# Tools/fix_all_issues.py
"""
═══════════════════════════════════════════════════════════
  INTEGRA - إصلاح شامل لكل المشاكل
═══════════════════════════════════════════════════════════
  cd /d D:\\Projects\\Integra
  python Tools\\fix_all_issues.py
═══════════════════════════════════════════════════════════
"""

import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent

print()
print("═" * 60)
print("  INTEGRA - إصلاح شامل")
print("═" * 60)
print(f"  المسار: {PROJECT_ROOT}")
print(f"  التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("═" * 60)

issues_fixed = 0

# ══════════════════════════════════════════════
# 1. إصلاح main.py - حماية مجلد logs
# ══════════════════════════════════════════════
print("\n🔧 1. إصلاح main.py...")

MAIN_PY_CODE = '''"""
INTEGRA - Integrated Management System
=======================================
Entry Point
Version: 2.1.0
"""

import sys
import os

# التأكد إن مجلد logs موجود (مهم قبل أي حاجة)
_logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(_logs_dir, exist_ok=True)

# إخفاء الكونسول: لو مفيش stderr (pythonw) نوجهه لملف
if sys.stderr is None:
    sys.stderr = open(os.path.join(_logs_dir, "stderr.log"), "w", encoding="utf-8")
if sys.stdout is None:
    sys.stdout = open(os.path.join(_logs_dir, "stdout.log"), "w", encoding="utf-8")

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from core.logging import setup_logging

setup_logging(debug_mode=True)


def main():
    """Application entry point."""
    app = QApplication(sys.argv)

    # تركيب معالج الأخطاء (لازم يكون بعد QApplication)
    from core.error_handling import install_exception_handler
    install_exception_handler()

    # Set application info
    app.setApplicationName("INTEGRA")
    app.setApplicationVersion("2.1.0")
    app.setOrganizationName("INTEGRA")

    # Set default font
    font = QFont("Cairo", 11)
    app.setFont(font)

    # Import and show launcher
    from ui.windows.launcher import LauncherWindow

    window = LauncherWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
'''

main_path = PROJECT_ROOT / "main.py"
main_path.write_text(MAIN_PY_CODE.strip() + "\n", encoding="utf-8")
print("  ✅ main.py - أضفنا حماية مجلد logs + encoding للملفات")
issues_fixed += 1

# ══════════════════════════════════════════════
# 2. إصلاح INTEGRA.pyw - تشغيل مباشر بدل subprocess
# ══════════════════════════════════════════════
print("\n🔧 2. إصلاح INTEGRA.pyw...")

PYW_CODE = '''"""
INTEGRA - تشغيل بدون كونسول
الملف ده بيشغل البرنامج بدون ما يظهر CMD.
اعمله شورتكات على سطح المكتب.
"""
import os
import sys

# التأكد إن المسار صح
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# التأكد إن مجلد logs موجود
os.makedirs("logs", exist_ok=True)

# توجيه الـ output لملفات (عشان pythonw مالوش كونسول)
if sys.stderr is None or sys.stderr.name == "<stderr>":
    try:
        sys.stderr = open("logs/stderr.log", "w", encoding="utf-8")
    except Exception:
        pass
if sys.stdout is None or sys.stdout.name == "<stdout>":
    try:
        sys.stdout = open("logs/stdout.log", "w", encoding="utf-8")
    except Exception:
        pass

# تشغيل البرنامج مباشرة (مش subprocess)
try:
    exec(open("main.py", encoding="utf-8").read())
except Exception as e:
    # لو حصل خطأ، نسجله
    with open("logs/startup_error.log", "w", encoding="utf-8") as f:
        import traceback
        f.write(f"Startup Error: {e}\\n")
        traceback.print_exc(file=f)
'''

pyw_path = PROJECT_ROOT / "INTEGRA.pyw"
pyw_path.write_text(PYW_CODE.strip() + "\n", encoding="utf-8")
print("  ✅ INTEGRA.pyw - تشغيل مباشر + حماية من الأخطاء")
issues_fixed += 1

# ══════════════════════════════════════════════
# 3. إصلاح exception_hook.py - رسالة CRITICAL
# ══════════════════════════════════════════════
print("\n🔧 3. إصلاح رسالة CRITICAL...")

hook_file = PROJECT_ROOT / "core" / "error_handling" / "exception_hook.py"

if hook_file.exists():
    code = hook_file.read_text(encoding="utf-8")
    
    if '_log_error("معالج الأخطاء الشامل' in code:
        code = code.replace(
            '_log_error("معالج الأخطاء الشامل - تم التركيب ✅")',
            'if _has_logger:\n            logger.info("معالج الأخطاء الشامل - تم التركيب ✅")'
        )
        hook_file.write_text(code, encoding="utf-8")
        print("  ✅ تم إصلاح CRITICAL → INFO")
        issues_fixed += 1
    else:
        print("  ✅ مصلحة بالفعل")
else:
    print("  ⚠️  الملف مش موجود")

# ══════════════════════════════════════════════
# 4. تنظيف الملفات المؤقتة
# ══════════════════════════════════════════════
print("\n🔧 4. تنظيف ملفات مؤقتة...")

temp_files = [
    PROJECT_ROOT / "INTEGRA.vbs",
    PROJECT_ROOT / "Tools" / "fix_startup.py",
    PROJECT_ROOT / "Tools" / "fix_exception_hook.py",
    PROJECT_ROOT / "Tools" / "_temp_shortcut.vbs",
    PROJECT_ROOT / "Tools" / "_create_shortcut_temp.vbs",
]

for f in temp_files:
    if f.exists():
        f.unlink()
        print(f"  🗑️  حذف {f.name}")
        issues_fixed += 1

if issues_fixed == 0:
    print("  ✅ مفيش ملفات مؤقتة")

# ══════════════════════════════════════════════
# 5. تحديث .gitignore
# ══════════════════════════════════════════════
print("\n🔧 5. تحديث .gitignore...")

gitignore_path = PROJECT_ROOT / ".gitignore"
existing = gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else ""

new_entries = []
entries_to_check = ["logs/", "*.log", "stderr.log", "stdout.log", "startup_error.log"]

for entry in entries_to_check:
    if entry not in existing:
        new_entries.append(entry)

if new_entries:
    with open(gitignore_path, "a", encoding="utf-8") as f:
        f.write("\n# Logs\n")
        for entry in new_entries:
            f.write(f"{entry}\n")
    print(f"  ✅ أضفنا {new_entries}")
    issues_fixed += 1
else:
    print("  ✅ محدّث بالفعل")

# ══════════════════════════════════════════════
# 6. التأكد من مجلد logs
# ══════════════════════════════════════════════
print("\n🔧 6. التأكد من مجلد logs...")

logs_dir = PROJECT_ROOT / "logs"
logs_dir.mkdir(exist_ok=True)
print(f"  ✅ مجلد logs موجود")

# ══════════════════════════════════════════════
# النتيجة
# ══════════════════════════════════════════════
print()
print("═" * 60)
print(f"  🎉 تم إصلاح {issues_fixed} مشكلة!")
print("═" * 60)
print()
print("  ▶ جرّب دلوقتي:")
print("  ─────────────────")
print("  1. دبل كليك على INTEGRA.pyw (بدون CMD)")
print("  2. أو من CMD: python main.py")
print()
print("  ▶ شورتكات سطح المكتب:")
print("  ─────────────────────")
print("  كليك يمين على INTEGRA.pyw → Send to → Desktop (create shortcut)")
print()
print("  ▶ رفع على GitHub:")
print("  ──────────────────")
print("  cd /d D:\\Projects\\Integra")
print('  git add --all && git commit -m "A1+A2: Infrastructure fixes" && git push')
print()
print("═" * 60)
