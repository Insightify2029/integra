#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
INTEGRA - Build Script
======================
سكريبت بناء الملف التنفيذي وإنشاء الاختصارات

الاستخدام:
    python build.py              # بناء كامل
    python build.py --exe        # بناء EXE فقط
    python build.py --shortcut   # إنشاء اختصار فقط
    python build.py --clean      # تنظيف ملفات البناء
    python build.py --run        # تشغيل البرنامج
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# الإعدادات
# ─────────────────────────────────────────────────────────────

APP_NAME = "INTEGRA"
APP_VERSION = "2.1.0"
BASE_DIR = Path(__file__).parent.absolute()
DIST_DIR = BASE_DIR / "dist"
BUILD_DIR = BASE_DIR / "build"
SPEC_FILE = BASE_DIR / "INTEGRA.spec"
ICON_FILE = BASE_DIR / "resources" / "icons" / "integra.ico"
EXE_FILE = DIST_DIR / "INTEGRA.exe"


# ─────────────────────────────────────────────────────────────
# الألوان للـ Console
# ─────────────────────────────────────────────────────────────

class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_header(text):
    """طباعة عنوان"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'═' * 50}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}  {text}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'═' * 50}{Colors.RESET}\n")


def print_success(text):
    """طباعة نجاح"""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text):
    """طباعة خطأ"""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_info(text):
    """طباعة معلومة"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")


def print_warning(text):
    """طباعة تحذير"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


# ─────────────────────────────────────────────────────────────
# وظائف البناء
# ─────────────────────────────────────────────────────────────

def check_requirements():
    """التحقق من المتطلبات"""
    print_info("التحقق من المتطلبات...")

    # PyInstaller
    try:
        import PyInstaller
        print_success(f"PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print_error("PyInstaller غير مثبت! قم بتثبيته: pip install pyinstaller")
        return False

    # الأيقونة
    if ICON_FILE.exists():
        print_success(f"الأيقونة موجودة: {ICON_FILE.name}")
    else:
        print_warning("الأيقونة غير موجودة، سيتم استخدام الأيقونة الافتراضية")

    # main.py
    if (BASE_DIR / "main.py").exists():
        print_success("main.py موجود")
    else:
        print_error("main.py غير موجود!")
        return False

    return True


def clean_build():
    """تنظيف ملفات البناء"""
    print_header("تنظيف ملفات البناء")

    dirs_to_clean = [DIST_DIR, BUILD_DIR]
    files_to_clean = list(BASE_DIR.glob("*.spec.bak"))

    for d in dirs_to_clean:
        if d.exists():
            shutil.rmtree(d)
            print_success(f"تم حذف: {d.name}/")

    for f in files_to_clean:
        f.unlink()
        print_success(f"تم حذف: {f.name}")

    # تنظيف __pycache__
    for cache_dir in BASE_DIR.rglob("__pycache__"):
        shutil.rmtree(cache_dir)

    print_success("تم التنظيف بنجاح!")


def build_exe():
    """بناء الملف التنفيذي"""
    print_header(f"بناء {APP_NAME} v{APP_VERSION}")

    if not check_requirements():
        return False

    print_info("جاري البناء... (قد يستغرق بضع دقائق)")

    # أمر PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        str(SPEC_FILE)
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            if EXE_FILE.exists():
                size_mb = EXE_FILE.stat().st_size / (1024 * 1024)
                print_success(f"تم البناء بنجاح!")
                print_success(f"الملف: {EXE_FILE}")
                print_success(f"الحجم: {size_mb:.1f} MB")
                return True
            else:
                print_error("فشل البناء - الملف غير موجود")
                return False
        else:
            print_error("فشل البناء!")
            print(result.stderr)
            return False

    except Exception as e:
        print_error(f"خطأ: {e}")
        return False


def create_shortcut():
    """إنشاء اختصار على سطح المكتب"""
    print_header("إنشاء اختصار سطح المكتب")

    if not EXE_FILE.exists():
        print_error(f"الملف التنفيذي غير موجود: {EXE_FILE}")
        print_info("قم بالبناء أولاً: python build.py --exe")
        return False

    # تحديد مسار سطح المكتب
    if sys.platform == "win32":
        desktop = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
    else:
        desktop = Path.home() / "Desktop"

    if not desktop.exists():
        print_error(f"مجلد سطح المكتب غير موجود: {desktop}")
        return False

    shortcut_path = desktop / f"{APP_NAME}.lnk"

    if sys.platform == "win32":
        # Windows - استخدام PowerShell
        ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{EXE_FILE}"
$Shortcut.WorkingDirectory = "{BASE_DIR}"
$Shortcut.IconLocation = "{ICON_FILE}"
$Shortcut.Description = "INTEGRA - Integrated Management System"
$Shortcut.Save()
'''
        try:
            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print_success(f"تم إنشاء الاختصار: {shortcut_path}")
                return True
            else:
                print_error(f"فشل إنشاء الاختصار: {result.stderr}")
                return False
        except Exception as e:
            print_error(f"خطأ: {e}")
            return False
    else:
        # Linux/Mac - إنشاء symbolic link
        shortcut_path = desktop / APP_NAME
        try:
            if shortcut_path.exists():
                shortcut_path.unlink()
            shortcut_path.symlink_to(EXE_FILE)
            print_success(f"تم إنشاء الاختصار: {shortcut_path}")
            return True
        except Exception as e:
            print_error(f"خطأ: {e}")
            return False


def run_app():
    """تشغيل البرنامج"""
    print_header("تشغيل INTEGRA")

    if EXE_FILE.exists():
        print_info(f"تشغيل: {EXE_FILE}")
        if sys.platform == "win32":
            os.startfile(str(EXE_FILE))
        else:
            subprocess.Popen([str(EXE_FILE)])
        print_success("تم التشغيل!")
    else:
        print_warning("الملف التنفيذي غير موجود، تشغيل من main.py...")
        subprocess.Popen([sys.executable, str(BASE_DIR / "main.py")])
        print_success("تم التشغيل!")


def show_status():
    """عرض حالة البناء"""
    print_header("حالة البناء")

    print(f"  المشروع: {BASE_DIR}")
    print(f"  الإصدار: {APP_VERSION}")
    print()

    # الملف التنفيذي
    if EXE_FILE.exists():
        size_mb = EXE_FILE.stat().st_size / (1024 * 1024)
        print_success(f"EXE موجود: {EXE_FILE.name} ({size_mb:.1f} MB)")
    else:
        print_warning("EXE غير موجود")

    # الأيقونة
    if ICON_FILE.exists():
        print_success(f"الأيقونة: {ICON_FILE.name}")
    else:
        print_warning("الأيقونة غير موجودة")

    # الاختصار
    if sys.platform == "win32":
        desktop = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
    else:
        desktop = Path.home() / "Desktop"

    shortcut = desktop / f"{APP_NAME}.lnk" if sys.platform == "win32" else desktop / APP_NAME
    if shortcut.exists():
        print_success(f"الاختصار موجود على سطح المكتب")
    else:
        print_warning("الاختصار غير موجود")


# ─────────────────────────────────────────────────────────────
# نقطة الدخول
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="INTEGRA Build Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
أمثلة:
    python build.py              # بناء كامل + اختصار
    python build.py --exe        # بناء EXE فقط
    python build.py --shortcut   # إنشاء اختصار فقط
    python build.py --clean      # تنظيف ملفات البناء
    python build.py --run        # تشغيل البرنامج
    python build.py --status     # عرض الحالة
        """
    )

    parser.add_argument("--exe", action="store_true", help="بناء الملف التنفيذي فقط")
    parser.add_argument("--shortcut", action="store_true", help="إنشاء اختصار سطح المكتب فقط")
    parser.add_argument("--clean", action="store_true", help="تنظيف ملفات البناء")
    parser.add_argument("--run", action="store_true", help="تشغيل البرنامج")
    parser.add_argument("--status", action="store_true", help="عرض حالة البناء")

    args = parser.parse_args()

    # تنظيف
    if args.clean:
        clean_build()
        return

    # عرض الحالة
    if args.status:
        show_status()
        return

    # تشغيل
    if args.run:
        run_app()
        return

    # بناء EXE فقط
    if args.exe:
        build_exe()
        return

    # إنشاء اختصار فقط
    if args.shortcut:
        create_shortcut()
        return

    # البناء الكامل (الافتراضي)
    print_header(f"INTEGRA Build System v{APP_VERSION}")

    # 1. تنظيف
    clean_build()

    # 2. بناء
    if build_exe():
        # 3. إنشاء اختصار
        create_shortcut()

        print()
        print_header("اكتمل البناء!")
        print(f"  {Colors.GREEN}✓{Colors.RESET} الملف التنفيذي: {EXE_FILE}")
        print(f"  {Colors.GREEN}✓{Colors.RESET} يمكنك تشغيل البرنامج من سطح المكتب")
        print()
    else:
        print_error("فشل البناء!")
        sys.exit(1)


if __name__ == "__main__":
    main()
