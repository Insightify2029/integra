"""
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
        f.write(f"Startup Error: {e}\n")
        traceback.print_exc(file=f)
