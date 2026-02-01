# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════
🏥 INTEGRA - Health Check & Infrastructure Diagnostic
═══════════════════════════════════════════════════════════════
فحص شامل للبنية التحتية على كل جهاز
شغّل على كل جهاز (البيت والشغل) وابعتلي النتيجة

الاستخدام:
  cd D:\Projects\Integra
  venv\Scripts\activate
  python INTEGRA_HEALTH_CHECK.py
═══════════════════════════════════════════════════════════════
"""

import os
import sys
import platform
import subprocess
import shutil
import socket
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# الإعدادات
# ═══════════════════════════════════════════════════════════

PROJECT_ROOT = Path(r"D:\Projects\Integra")
VENV_DIR = PROJECT_ROOT / "venv"
UPDATES_DIR = PROJECT_ROOT / "Updates"
APP_DIR = UPDATES_DIR  # integra_v2.1 inside Updates

# النتائج
results = []
warnings = []
errors = []
info_items = []

PASS = "✅"
FAIL = "❌"
WARN = "⚠️"
INFO = "ℹ️"


def log(status, category, message, detail=""):
    """تسجيل نتيجة الفحص."""
    entry = f"  {status} [{category}] {message}"
    if detail:
        entry += f"\n      → {detail}"
    results.append(entry)
    
    if status == FAIL:
        errors.append(f"[{category}] {message}")
    elif status == WARN:
        warnings.append(f"[{category}] {message}")
    elif status == INFO:
        info_items.append(f"[{category}] {message}")


def run_cmd(cmd, timeout=15):
    """تشغيل أمر وإرجاع النتيجة."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, 
            timeout=timeout, shell=True
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", -1
    except Exception as e:
        return "", str(e), -1


def section(title):
    """عنوان قسم."""
    results.append("")
    results.append(f"{'─' * 60}")
    results.append(f"  📋 {title}")
    results.append(f"{'─' * 60}")


# ═══════════════════════════════════════════════════════════
# 1. معلومات الجهاز
# ═══════════════════════════════════════════════════════════

def check_machine_info():
    section("معلومات الجهاز")
    
    hostname = socket.gethostname()
    log(INFO, "MACHINE", f"اسم الجهاز: {hostname}")
    log(INFO, "MACHINE", f"نظام التشغيل: {platform.platform()}")
    log(INFO, "MACHINE", f"المعالج: {platform.processor()}")
    log(INFO, "MACHINE", f"تاريخ الفحص: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # تحديد هل البيت ولا الشغل
    log(INFO, "MACHINE", f"⬆️ حدد: هل هذا جهاز البيت أم الشغل؟ (الاسم: {hostname})")


# ═══════════════════════════════════════════════════════════
# 2. فحص Python
# ═══════════════════════════════════════════════════════════

def check_python():
    section("Python")
    
    # Python version
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    log(INFO, "PYTHON", f"الإصدار: {py_version}")
    
    if sys.version_info >= (3, 11):
        log(PASS, "PYTHON", f"Python {py_version} - متوافق")
    else:
        log(FAIL, "PYTHON", f"Python {py_version} - مطلوب 3.11+")
    
    # Python path
    log(INFO, "PYTHON", f"المسار: {sys.executable}")
    
    # هل شغال من الـ venv؟
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    if in_venv:
        log(PASS, "VENV", "الـ Virtual Environment مفعّل")
        log(INFO, "VENV", f"مسار الـ venv: {sys.prefix}")
    else:
        log(WARN, "VENV", "الـ Virtual Environment غير مفعّل!",
            "شغّل: venv\\Scripts\\activate")
    
    # pip version
    stdout, _, rc = run_cmd(f'"{sys.executable}" -m pip --version')
    if rc == 0:
        log(PASS, "PIP", f"pip متاح: {stdout.split()[1] if stdout else 'unknown'}")
    else:
        log(FAIL, "PIP", "pip غير متاح!")


# ═══════════════════════════════════════════════════════════
# 3. فحص المكتبات
# ═══════════════════════════════════════════════════════════

def check_libraries():
    section("المكتبات (Python Packages)")
    
    # المكتبات الأساسية المطلوبة
    required = {
        # Core
        'PyQt5': 'PyQt5',
        'psycopg2': 'psycopg2-binary',
        'sqlalchemy': 'SQLAlchemy',
        'alembic': 'alembic',
        # Data
        'pandas': 'pandas',
        'numpy': 'numpy',
        # File readers
        'openpyxl': 'openpyxl',
        'xlrd': 'xlrd',
        'PyPDF2': 'PyPDF2',
        'pdfplumber': 'pdfplumber',
        'docx': 'python-docx',
        'PIL': 'Pillow',
        'tika': 'tika',
        # Utilities
        'dotenv': 'python-dotenv',
    }
    
    # مكتبات إضافية مفيدة
    optional = {
        'loguru': 'loguru',
        'rich': 'rich',
        'pydantic': 'pydantic',
    }
    
    missing_required = []
    missing_optional = []
    
    for module, package in required.items():
        try:
            mod = __import__(module)
            version = getattr(mod, '__version__', getattr(mod, 'VERSION', '?'))
            log(PASS, "LIB", f"{package} ({version})")
        except ImportError:
            log(FAIL, "LIB", f"{package} - غير مثبتة!", f"pip install {package}")
            missing_required.append(package)
    
    results.append("")
    results.append("  📦 مكتبات إضافية (اختيارية):")
    
    for module, package in optional.items():
        try:
            mod = __import__(module)
            version = getattr(mod, '__version__', '?')
            log(PASS, "OPT", f"{package} ({version})")
        except ImportError:
            log(WARN, "OPT", f"{package} - غير مثبتة", f"pip install {package}")
            missing_optional.append(package)
    
    if missing_required:
        results.append("")
        results.append(f"  🔧 أمر تثبيت المكتبات الناقصة:")
        results.append(f"     pip install {' '.join(missing_required)}")
    
    if missing_optional:
        results.append(f"     pip install {' '.join(missing_optional)}  (اختيارية)")


# ═══════════════════════════════════════════════════════════
# 4. فحص PostgreSQL
# ═══════════════════════════════════════════════════════════

def check_postgresql():
    section("PostgreSQL")
    
    # فحص psql
    stdout, stderr, rc = run_cmd('psql --version')
    if rc == 0:
        log(PASS, "PG", f"PostgreSQL CLI: {stdout}")
    else:
        # محاولة بالمسار الكامل
        stdout2, _, rc2 = run_cmd('"C:\\Program Files\\PostgreSQL\\16\\bin\\psql.exe" --version')
        if rc2 == 0:
            log(PASS, "PG", f"PostgreSQL CLI: {stdout2}")
            log(WARN, "PG", "psql مش في الـ PATH - استخدم المسار الكامل")
        else:
            log(FAIL, "PG", "PostgreSQL غير متاح!", 
                "تأكد إن PostgreSQL 16 مثبت")
    
    # فحص الخدمة
    stdout, _, rc = run_cmd('sc query postgresql-x64-16')
    if rc == 0 and "RUNNING" in stdout:
        log(PASS, "PG", "خدمة PostgreSQL شغالة")
    elif rc == 0:
        log(FAIL, "PG", "خدمة PostgreSQL موجودة بس مش شغالة!",
            "شغّلها من services.msc")
    else:
        # محاولة أسماء تانية
        for name in ['postgresql-x64-17', 'postgresql-x64-15', 'postgresql']:
            stdout, _, rc = run_cmd(f'sc query {name}')
            if rc == 0:
                if "RUNNING" in stdout:
                    log(PASS, "PG", f"خدمة PostgreSQL شغالة ({name})")
                else:
                    log(WARN, "PG", f"خدمة PostgreSQL موجودة بس مش شغالة ({name})")
                break
        else:
            log(WARN, "PG", "مش قادر أتحقق من خدمة PostgreSQL",
                "تأكد يدوياً من services.msc")
    
    # فحص الاتصال بقاعدة البيانات
    try:
        import psycopg2
        
        # محاولة من .env
        password = None
        env_file = PROJECT_ROOT / ".env"
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('DB_PASSWORD='):
                        password = line.strip().split('=', 1)[1]
                        break
        
        if password:
            try:
                conn = psycopg2.connect(
                    host='localhost',
                    port=5432,
                    dbname='integra',
                    user='postgres',
                    password=password,
                    connect_timeout=5
                )
                cursor = conn.cursor()
                
                # إصدار PostgreSQL
                cursor.execute("SELECT version();")
                pg_ver = cursor.fetchone()[0]
                log(PASS, "DB", f"متصل بقاعدة البيانات integra")
                log(INFO, "DB", f"إصدار: {pg_ver[:50]}...")
                
                # عدد الجداول
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """)
                tables = [row[0] for row in cursor.fetchall()]
                log(INFO, "DB", f"عدد الجداول: {len(tables)}")
                
                # فحص الجداول المهمة وعدد السجلات
                important_tables = [
                    'employees', 'nationalities', 'departments', 
                    'job_titles', 'banks', 'companies', 'employee_statuses'
                ]
                
                results.append("")
                results.append("  📊 جداول البيانات:")
                
                for table in important_tables:
                    if table in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        log(PASS, "TABLE", f"{table}: {count} سجل")
                    else:
                        log(FAIL, "TABLE", f"{table}: غير موجود!")
                
                # جداول إضافية موجودة
                extra = [t for t in tables if t not in important_tables]
                if extra:
                    log(INFO, "TABLE", f"جداول إضافية: {', '.join(extra)}")
                
                conn.close()
                
            except psycopg2.OperationalError as e:
                log(FAIL, "DB", f"فشل الاتصال: {str(e)[:100]}")
        else:
            log(WARN, "DB", "ملف .env غير موجود أو بدون كلمة سر",
                "أنشئ ملف .env في مجلد المشروع")
            
    except ImportError:
        log(FAIL, "DB", "psycopg2 غير مثبتة - مش قادر أفحص الداتابيز")


# ═══════════════════════════════════════════════════════════
# 5. فحص Java (للـ Tika)
# ═══════════════════════════════════════════════════════════

def check_java():
    section("Java (مطلوب لـ Apache Tika)")
    
    stdout, stderr, rc = run_cmd('java -version')
    # java -version يكتب في stderr
    output = stderr if stderr and "version" in stderr.lower() else stdout
    
    if "version" in output.lower():
        log(PASS, "JAVA", f"Java متاح: {output.split(chr(10))[0]}")
    else:
        log(WARN, "JAVA", "Java غير متاح",
            "مطلوب لتشغيل Apache Tika - ثبت JDK 25")


# ═══════════════════════════════════════════════════════════
# 6. فحص Git
# ═══════════════════════════════════════════════════════════

def check_git():
    section("Git & GitHub")
    
    # Git version
    stdout, _, rc = run_cmd('git --version')
    if rc == 0:
        log(PASS, "GIT", f"Git متاح: {stdout}")
    else:
        log(FAIL, "GIT", "Git غير مثبت!")
        return
    
    # هل المجلد git repo؟
    os.chdir(PROJECT_ROOT)
    stdout, _, rc = run_cmd('git rev-parse --is-inside-work-tree')
    if rc == 0:
        log(PASS, "GIT", "المشروع Git repository")
    else:
        log(FAIL, "GIT", "المشروع مش Git repository!",
            "شغّل: git init ثم git remote add origin URL")
        return
    
    # Remote
    stdout, _, rc = run_cmd('git remote -v')
    if stdout:
        log(PASS, "GIT", f"Remote: {stdout.split()[1] if stdout else 'none'}")
    else:
        log(FAIL, "GIT", "مفيش remote محدد!",
            "git remote add origin https://github.com/Insightify2029/integra.git")
    
    # Branch
    stdout, _, rc = run_cmd('git branch --show-current')
    if stdout:
        log(INFO, "GIT", f"الفرع الحالي: {stdout}")
    
    # Status
    stdout, _, rc = run_cmd('git status --porcelain')
    if rc == 0:
        if stdout:
            changed = len(stdout.strip().split('\n'))
            log(WARN, "GIT", f"في {changed} تغيير غير محفوظ!",
                "اعمل SYNC قبل ما تنتقل للجهاز التاني")
        else:
            log(PASS, "GIT", "كل التغييرات محفوظة ✓")
    
    # Last commit
    stdout, _, rc = run_cmd('git log --oneline -1')
    if rc == 0 and stdout:
        log(INFO, "GIT", f"آخر commit: {stdout}")
    
    # Push/Pull status
    stdout, _, rc = run_cmd('git status -sb')
    if rc == 0:
        if 'ahead' in stdout:
            log(WARN, "GIT", "في commits محلية لم تُرفع! (git push)")
        elif 'behind' in stdout:
            log(WARN, "GIT", "في تحديثات على GitHub لم تُنزّل! (git pull)")
    
    # Git config
    stdout_name, _, _ = run_cmd('git config user.name')
    stdout_email, _, _ = run_cmd('git config user.email')
    if stdout_name:
        log(INFO, "GIT", f"المستخدم: {stdout_name} <{stdout_email}>")
    else:
        log(WARN, "GIT", "Git user غير محدد",
            "git config user.name 'Insightify2029'")
    
    # .gitignore
    gitignore = PROJECT_ROOT / ".gitignore"
    if gitignore.exists():
        with open(gitignore, 'r') as f:
            content = f.read()
        
        log(PASS, "GIT", ".gitignore موجود")
        
        # تحقق من محتويات مهمة
        must_ignore = ['.env', '__pycache__', 'venv', 'SYNC.bat']
        missing_ignore = [item for item in must_ignore if item not in content]
        if missing_ignore:
            log(WARN, "GIT", f".gitignore ناقص: {', '.join(missing_ignore)}")
    else:
        log(WARN, "GIT", ".gitignore غير موجود!")


# ═══════════════════════════════════════════════════════════
# 7. فحص بنية المشروع
# ═══════════════════════════════════════════════════════════

def check_project_structure():
    section("بنية المشروع (Project Structure)")
    
    if not PROJECT_ROOT.exists():
        log(FAIL, "PROJ", f"مجلد المشروع غير موجود: {PROJECT_ROOT}")
        return
    
    log(PASS, "PROJ", f"مجلد المشروع: {PROJECT_ROOT}")
    
    # الملفات الأساسية في الجذر
    root_files = {
        'INTEGRA.bat': 'مُشغّل البرنامج',
        'CURRENT_STATUS.txt': 'حالة المشروع',
        'TECHNICAL_CONFIG.txt': 'الإعدادات التقنية',
        'INTEGRA_DEV_TOOLKIT.md': 'دليل التطوير',
        '.env': 'إعدادات سرية (كلمة السر)',
        '.gitignore': 'ملفات Git المستثناة',
    }
    
    results.append("")
    results.append("  📁 الملفات الأساسية:")
    
    for filename, desc in root_files.items():
        filepath = PROJECT_ROOT / filename
        if filepath.exists():
            size = filepath.stat().st_size
            log(PASS, "FILE", f"{filename} ({size:,} bytes) - {desc}")
        else:
            if filename in ['.env', '.gitignore']:
                log(WARN, "FILE", f"{filename} - غير موجود! ({desc})")
            else:
                log(INFO, "FILE", f"{filename} - غير موجود ({desc})")
    
    # مجلد Updates
    results.append("")
    results.append("  📁 مجلد Updates:")
    
    if UPDATES_DIR.exists():
        log(PASS, "DIR", "مجلد Updates موجود")
        
        # البحث عن مجلد التطبيق
        app_folders = list(UPDATES_DIR.glob("integra_*"))
        if app_folders:
            for folder in app_folders:
                if (folder / "main.py").exists():
                    log(PASS, "APP", f"التطبيق: {folder.name}")
                    
                    # فحص بنية التطبيق
                    check_app_structure(folder)
                else:
                    log(WARN, "APP", f"مجلد بدون main.py: {folder.name}")
        else:
            # هل في ZIP؟
            zips = list(UPDATES_DIR.glob("*.zip"))
            if zips:
                log(INFO, "APP", f"في {len(zips)} ملف ZIP ينتظر الفك")
            else:
                log(FAIL, "APP", "مفيش تطبيق في مجلد Updates!")
    else:
        log(FAIL, "DIR", "مجلد Updates غير موجود!")
    
    # مجلد venv
    results.append("")
    results.append("  📁 Virtual Environment:")
    
    if VENV_DIR.exists():
        python_exe = VENV_DIR / "Scripts" / "python.exe"
        if python_exe.exists():
            log(PASS, "VENV", f"venv موجود ومكتمل")
        else:
            log(WARN, "VENV", "venv موجود لكن python.exe مفقود!")
    else:
        log(FAIL, "VENV", "venv غير موجود!",
            "أنشئه: python -m venv venv")


def check_app_structure(app_dir: Path):
    """فحص بنية التطبيق داخل مجلد Updates."""
    
    # المجلدات المطلوبة
    required_dirs = [
        "core",
        "core/config",
        "core/database",
        "core/database/connection",
        "core/database/queries",
        "core/themes",
        "ui",
        "ui/windows",
        "ui/windows/launcher",
        "ui/components",
        "ui/components/tables",
        "ui/dialogs",
        "modules",
        "modules/mostahaqat",
        "modules/mostahaqat/window",
        "modules/mostahaqat/screens",
        "modules/mostahaqat/screens/employees_list",
        "modules/mostahaqat/screens/employee_profile",
    ]
    
    results.append("")
    results.append("  📂 بنية التطبيق:")
    
    missing_dirs = []
    for dir_path in required_dirs:
        full = app_dir / dir_path
        if full.exists():
            # تحقق من وجود __init__.py
            init_file = full / "__init__.py"
            if not init_file.exists() and not dir_path.startswith("core/config"):
                log(WARN, "STRUCT", f"{dir_path}/ - ناقص __init__.py")
        else:
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        for d in missing_dirs:
            log(FAIL, "STRUCT", f"{d}/ - غير موجود!")
    else:
        log(PASS, "STRUCT", f"كل المجلدات المطلوبة موجودة ({len(required_dirs)} مجلد)")
    
    # فحص edit_employee screen
    edit_dir = app_dir / "modules" / "mostahaqat" / "screens" / "edit_employee"
    if edit_dir.exists():
        edit_screen = edit_dir / "edit_employee_screen.py"
        if edit_screen.exists():
            log(PASS, "SCREEN", "شاشة تعديل الموظف (edit_employee) مثبتة")
        else:
            log(WARN, "SCREEN", "مجلد edit_employee موجود بس الملف ناقص")
    else:
        log(INFO, "SCREEN", "شاشة تعديل الموظف لم تُثبت بعد")
    
    # عدد ملفات Python
    py_files = list(app_dir.rglob("*.py"))
    log(INFO, "STRUCT", f"عدد ملفات Python: {len(py_files)}")
    
    # فحص main.py
    main_py = app_dir / "main.py"
    if main_py.exists():
        with open(main_py, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'PyQt5' in content and 'LauncherWindow' in content:
            log(PASS, "MAIN", "main.py سليم (PyQt5 + LauncherWindow)")
        else:
            log(WARN, "MAIN", "main.py موجود لكن المحتوى غير متوقع")


# ═══════════════════════════════════════════════════════════
# 8. فحص الـ SYNC
# ═══════════════════════════════════════════════════════════

def check_sync():
    section("نظام المزامنة (Sync)")
    
    sync_bat = PROJECT_ROOT / "SYNC.bat"
    restore_bat = PROJECT_ROOT / "RESTORE.bat"
    
    if sync_bat.exists():
        log(PASS, "SYNC", "SYNC.bat موجود")
        
        with open(sync_bat, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # تحقق من المكونات
        checks = {
            'git pull': 'جلب التحديثات',
            'pg_dump': 'نسخ احتياطي للداتابيز',
            'git push': 'رفع التغييرات',
            'git add': 'إضافة الملفات',
        }
        for cmd, desc in checks.items():
            if cmd in content:
                log(PASS, "SYNC", f"  {desc} ({cmd})")
            else:
                log(WARN, "SYNC", f"  {desc} ناقص ({cmd})")
    else:
        log(WARN, "SYNC", "SYNC.bat غير موجود!",
            "راجع INTEGRA_DEV_TOOLKIT.md للنسخة المحسّنة")
    
    if restore_bat.exists():
        log(PASS, "SYNC", "RESTORE.bat موجود")
    else:
        log(INFO, "SYNC", "RESTORE.bat غير موجود (اختياري)")
    
    # فحص database_backup.sql
    backup_sql = PROJECT_ROOT / "database_backup.sql"
    if backup_sql.exists():
        size = backup_sql.stat().st_size
        mod_time = datetime.fromtimestamp(backup_sql.stat().st_mtime)
        age_hours = (datetime.now() - mod_time).total_seconds() / 3600
        
        log(PASS, "BACKUP", f"database_backup.sql ({size:,} bytes)")
        log(INFO, "BACKUP", f"آخر تحديث: {mod_time.strftime('%Y-%m-%d %H:%M')} ({age_hours:.0f} ساعة)")
        
        if age_hours > 48:
            log(WARN, "BACKUP", "النسخة الاحتياطية قديمة (أكثر من 48 ساعة)!",
                "شغّل SYNC.bat لتحديثها")
    else:
        log(WARN, "BACKUP", "مفيش نسخة احتياطية للداتابيز")


# ═══════════════════════════════════════════════════════════
# 9. فحص VS Code
# ═══════════════════════════════════════════════════════════

def check_vscode():
    section("VS Code")
    
    stdout, _, rc = run_cmd('code --version')
    if rc == 0:
        version = stdout.split('\n')[0] if stdout else 'unknown'
        log(PASS, "VSCODE", f"VS Code متاح: v{version}")
        
        # فحص الإضافات المهمة
        stdout, _, rc = run_cmd('code --list-extensions')
        if rc == 0 and stdout:
            extensions = stdout.lower().split('\n')
            
            essential = {
                'ms-python.python': 'Python',
                'eamodio.gitlens': 'GitLens',
                'mhutchie.git-graph': 'Git Graph',
                'ms-python.black-formatter': 'Black Formatter',
            }
            
            useful = {
                'usernamehw.errorlens': 'Error Lens',
                'gruntfuggly.todo-tree': 'TODO Tree',
                'njpwerner.autodocstring': 'AutoDocstring',
                'formulahendry.code-runner': 'Code Runner',
            }
            
            results.append("")
            results.append("  🔌 إضافات أساسية:")
            for ext_id, name in essential.items():
                if ext_id.lower() in extensions:
                    log(PASS, "EXT", name)
                else:
                    log(WARN, "EXT", f"{name} غير مثبتة",
                        f"code --install-extension {ext_id}")
            
            results.append("")
            results.append("  🔌 إضافات مفيدة:")
            for ext_id, name in useful.items():
                if ext_id.lower() in extensions:
                    log(PASS, "EXT", name)
                else:
                    log(INFO, "EXT", f"{name} غير مثبتة (اختيارية)")
    else:
        log(WARN, "VSCODE", "VS Code غير متاح من سطر الأوامر",
            "تأكد إنه مثبت وفي الـ PATH")


# ═══════════════════════════════════════════════════════════
# 10. فحص Tesseract OCR
# ═══════════════════════════════════════════════════════════

def check_tesseract():
    section("Tesseract OCR (اختياري)")
    
    tesseract_path = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if tesseract_path.exists():
        stdout, stderr, rc = run_cmd(f'"{tesseract_path}" --version')
        output = stdout or stderr
        version = output.split('\n')[0] if output else 'unknown'
        log(PASS, "OCR", f"Tesseract متاح: {version}")
    else:
        log(INFO, "OCR", "Tesseract غير مثبت (اختياري - للمستقبل)")


# ═══════════════════════════════════════════════════════════
# 11. فحص مساحة القرص
# ═══════════════════════════════════════════════════════════

def check_disk():
    section("مساحة القرص")
    
    try:
        if PROJECT_ROOT.exists():
            drive = PROJECT_ROOT.anchor  # e.g. "D:\"
        else:
            drive = "D:\\"
        
        total, used, free = shutil.disk_usage(drive)
        free_gb = free / (1024**3)
        total_gb = total / (1024**3)
        
        log(INFO, "DISK", f"القرص {drive} إجمالي: {total_gb:.1f} GB - متاح: {free_gb:.1f} GB")
        
        if free_gb < 5:
            log(WARN, "DISK", f"المساحة المتاحة قليلة ({free_gb:.1f} GB)!")
        else:
            log(PASS, "DISK", f"المساحة كافية ({free_gb:.1f} GB متاح)")
    except Exception as e:
        log(INFO, "DISK", f"مش قادر أفحص المساحة: {e}")


# ═══════════════════════════════════════════════════════════
# 12. فحص الشبكة
# ═══════════════════════════════════════════════════════════

def check_network():
    section("الشبكة والاتصال")
    
    # GitHub
    try:
        sock = socket.create_connection(("github.com", 443), timeout=5)
        sock.close()
        log(PASS, "NET", "الاتصال بـ GitHub يعمل")
    except (socket.timeout, OSError):
        log(WARN, "NET", "مش قادر أوصل لـ GitHub",
            "تأكد من الاتصال بالإنترنت")
    
    # PostgreSQL localhost
    try:
        sock = socket.create_connection(("localhost", 5432), timeout=3)
        sock.close()
        log(PASS, "NET", "PostgreSQL يستمع على بورت 5432")
    except (socket.timeout, OSError):
        log(FAIL, "NET", "PostgreSQL مش شغال على بورت 5432!",
            "تأكد إن خدمة PostgreSQL شغالة")


# ═══════════════════════════════════════════════════════════
# التقرير النهائي
# ═══════════════════════════════════════════════════════════

def generate_report():
    """إنشاء التقرير النهائي."""
    
    report = []
    report.append("")
    report.append("═" * 60)
    report.append("  🏥 INTEGRA - تقرير الفحص الشامل")
    report.append("═" * 60)
    report.append(f"  📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"  💻 الجهاز: {socket.gethostname()}")
    report.append(f"  🖥️ النظام: {platform.platform()}")
    report.append("═" * 60)
    
    # النتائج التفصيلية
    report.extend(results)
    
    # الملخص
    report.append("")
    report.append("═" * 60)
    report.append("  📊 الملخص")
    report.append("═" * 60)
    report.append(f"  ❌ أخطاء تحتاج إصلاح: {len(errors)}")
    report.append(f"  ⚠️ تحذيرات: {len(warnings)}")
    report.append(f"  ℹ️ معلومات: {len(info_items)}")
    
    if errors:
        report.append("")
        report.append("  🔴 الأخطاء (يجب إصلاحها):")
        for i, err in enumerate(errors, 1):
            report.append(f"    {i}. {err}")
    
    if warnings:
        report.append("")
        report.append("  🟡 التحذيرات (يُنصح بإصلاحها):")
        for i, warn in enumerate(warnings, 1):
            report.append(f"    {i}. {warn}")
    
    # التوصية
    report.append("")
    report.append("─" * 60)
    if not errors:
        report.append("  🎉 البنية التحتية جاهزة! يمكن متابعة التطوير.")
    elif len(errors) <= 3:
        report.append("  ⚡ في مشاكل بسيطة - صلّحها وبعدين كمّل.")
    else:
        report.append("  🚨 في مشاكل كتير - لازم تتصلح الأول.")
    report.append("─" * 60)
    
    report.append("")
    report.append("  💡 انسخ هذا التقرير كامل وابعته لـ Claude")
    report.append("     عشان يساعدك في إصلاح أي مشاكل")
    report.append("")
    report.append("═" * 60)
    
    return "\n".join(report)


# ═══════════════════════════════════════════════════════════
# التشغيل
# ═══════════════════════════════════════════════════════════

def main():
    print("")
    print("═" * 60)
    print("  🏥 INTEGRA - فحص شامل للبنية التحتية")
    print("═" * 60)
    print("  جاري الفحص... انتظر لحظة")
    print("")
    
    # تشغيل كل الفحوصات
    check_machine_info()
    check_python()
    check_libraries()
    check_postgresql()
    check_java()
    check_git()
    check_project_structure()
    check_sync()
    check_vscode()
    check_tesseract()
    check_disk()
    check_network()
    
    # التقرير
    report = generate_report()
    print(report)
    
    # حفظ التقرير في ملف
    try:
        hostname = socket.gethostname()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = PROJECT_ROOT / f"health_check_{hostname}_{timestamp}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n  💾 التقرير محفوظ في: {report_file}")
    except Exception as e:
        print(f"\n  ⚠️ مش قادر أحفظ التقرير: {e}")
    
    print("")
    input("اضغط Enter للإغلاق...")


if __name__ == "__main__":
    main()
