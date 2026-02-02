# Tools/fix_startup.py
"""
═══════════════════════════════════════════════════════════
  INTEGRA - إصلاح مشاكل التشغيل
═══════════════════════════════════════════════════════════
  cd /d D:\\Projects\\Integra
  python Tools\\fix_startup.py
═══════════════════════════════════════════════════════════
"""

import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

print()
print("═" * 60)
print("  INTEGRA - إصلاح مشاكل التشغيل")
print("═" * 60)

# ──────────────────────────────────────────────
# الإصلاح 1: رسالة CRITICAL → INFO
# ──────────────────────────────────────────────
print("\n🔧 إصلاح 1: الرسالة الحمراء...")

hook_file = PROJECT_ROOT / "core" / "error_handling" / "exception_hook.py"

if hook_file.exists():
    code = hook_file.read_text(encoding="utf-8")
    
    if '_log_error("معالج الأخطاء الشامل' in code:
        code = code.replace(
            '_log_error("معالج الأخطاء الشامل - تم التركيب ✅")',
            'if _has_logger:\n            logger.info("معالج الأخطاء الشامل - تم التركيب ✅")'
        )
        hook_file.write_text(code, encoding="utf-8")
        print("  ✅ تم إصلاح الرسالة الحمراء")
    else:
        print("  ✅ الرسالة مصلحة بالفعل")
else:
    print("  ⚠️  ملف exception_hook.py مش موجود")

# ──────────────────────────────────────────────
# الإصلاح 2: إيجاد pythonw.exe
# ──────────────────────────────────────────────
print("\n🔧 إصلاح 2: تشغيل بدون CMD...")

python_dir = Path(sys.executable).parent
pythonw = python_dir / "pythonw.exe"

if pythonw.exists():
    print(f"  ✅ pythonw.exe: {pythonw}")
else:
    print(f"  ❌ pythonw.exe مش موجود في {python_dir}")
    pythonw = Path(sys.executable)

# ──────────────────────────────────────────────
# الإصلاح 3: إنشاء INTEGRA.vbs
# ──────────────────────────────────────────────
print("\n🔧 إصلاح 3: إنشاء INTEGRA.vbs...")

main_py = PROJECT_ROOT / "main.py"

vbs_lines = [
    'Set WshShell = CreateObject("WScript.Shell")',
    f'WshShell.CurrentDirectory = "{PROJECT_ROOT}"',
    f'WshShell.Run Chr(34) & "{pythonw}" & Chr(34) & " " & Chr(34) & "{main_py}" & Chr(34), 0, False',
]

vbs_path = PROJECT_ROOT / "INTEGRA.vbs"
vbs_path.write_text("\r\n".join(vbs_lines) + "\r\n", encoding="utf-8")
print(f"  ✅ INTEGRA.vbs")

# ──────────────────────────────────────────────
# الإصلاح 4: تحديث INTEGRA.bat
# ──────────────────────────────────────────────
print("\n🔧 إصلاح 4: تحديث INTEGRA.bat...")

bat_lines = [
    '@echo off',
    f'cd /d "{PROJECT_ROOT}"',
    f'start "" "{pythonw}" "main.py"',
    'exit',
]

bat_path = PROJECT_ROOT / "INTEGRA.bat"
bat_path.write_text("\r\n".join(bat_lines) + "\r\n", encoding="utf-8")
print(f"  ✅ INTEGRA.bat")

# ──────────────────────────────────────────────
# الإصلاح 5: شورتكات سطح المكتب
# ──────────────────────────────────────────────
print("\n🔧 إصلاح 5: شورتكات سطح المكتب...")

desktop = Path.home() / "Desktop"
if not desktop.exists():
    desktop = Path.home() / "OneDrive" / "Desktop"
if not desktop.exists():
    desktop = Path.home() / "OneDrive" / "سطح المكتب"

ico_path = PROJECT_ROOT / "resources" / "icons" / "integra.ico"

if desktop.exists():
    temp_vbs = PROJECT_ROOT / "Tools" / "_temp_shortcut.vbs"
    shortcut_path = desktop / "INTEGRA.lnk"
    
    sc_lines = [
        'Set WshShell = CreateObject("WScript.Shell")',
        f'Set shortcut = WshShell.CreateShortcut("{shortcut_path}")',
        'shortcut.TargetPath = "wscript.exe"',
        f'shortcut.Arguments = Chr(34) & "{vbs_path}" & Chr(34)',
        f'shortcut.WorkingDirectory = "{PROJECT_ROOT}"',
    ]
    
    if ico_path.exists():
        sc_lines.append(f'shortcut.IconLocation = "{ico_path}"')
    
    sc_lines.append('shortcut.Description = "INTEGRA ERP System"')
    sc_lines.append('shortcut.Save')
    
    temp_vbs.write_text("\r\n".join(sc_lines) + "\r\n", encoding="utf-8")
    
    try:
        subprocess.run(["wscript.exe", str(temp_vbs)], capture_output=True, timeout=10)
        temp_vbs.unlink(missing_ok=True)
        
        if shortcut_path.exists():
            print(f"  ✅ شورتكات على سطح المكتب")
        else:
            print(f"  ⚠️  ما قدرش يعمل شورتكات")
    except Exception as e:
        print(f"  ⚠️  خطأ: {e}")
        temp_vbs.unlink(missing_ok=True)
else:
    print(f"  ⚠️  ما لقيتش مجلد سطح المكتب")

# ──────────────────────────────────────────────
# النتيجة
# ──────────────────────────────────────────────
print()
print("═" * 60)
print("  🎉 تم الإصلاح!")
print("═" * 60)
print()
print("  طرق تشغيل البرنامج (بدون CMD):")
print("  ─────────────────────────────────")
print("  1. شورتكات INTEGRA على سطح المكتب")
print("  2. دبل كليك على INTEGRA.vbs")
print("  3. دبل كليك على INTEGRA.bat")
print()
print("  جرّب دلوقتي!")
print("═" * 60)
