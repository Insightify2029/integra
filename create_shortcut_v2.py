"""
INTEGRA - Desktop Shortcut Creator v2
يستخدم الأيقونة الاحترافية + يفتح بدون CMD
"""
import os
import sys


def create_shortcut(project_dir, icon_path):
    """Create Desktop shortcut using pywin32"""
    try:
        import win32com.client
    except ImportError:
        print("ERROR: pywin32 not found!")
        return False

    desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    shortcut_path = os.path.join(desktop, 'INTEGRA.lnk')

    # Use pythonw.exe - opens WITHOUT CMD window
    python_dir = os.path.dirname(sys.executable)
    pythonw = os.path.join(python_dir, 'pythonw.exe')
    if not os.path.exists(pythonw):
        # Try common locations
        for p in [
            r"C:\Program Files\Python311\pythonw.exe",
            r"C:\Program Files\Python\Python311\pythonw.exe",
            os.path.join(os.path.dirname(sys.executable), 'pythonw.exe'),
        ]:
            if os.path.exists(p):
                pythonw = p
                break
        else:
            pythonw = sys.executable
            print(f"WARNING: pythonw.exe not found, using {pythonw}")

    shell = win32com.client.Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = pythonw
    shortcut.Arguments = 'main.py'
    shortcut.WorkingDirectory = project_dir
    shortcut.IconLocation = icon_path
    shortcut.Description = 'INTEGRA - Integrated Management System'
    shortcut.WindowStyle = 1  # Normal window
    shortcut.save()
    print(f"  Shortcut: {shortcut_path}")
    print(f"  Target: {pythonw}")
    print(f"  Icon: {icon_path}")
    return True


def main():
    project_dir = r"D:\Projects\Integra"
    icons_dir = os.path.join(project_dir, "resources", "icons")
    ico_path = os.path.join(icons_dir, "integra.ico")
    png_path = os.path.join(icons_dir, "integra.png")

    print("=" * 50)
    print("  INTEGRA - Desktop Shortcut Creator v2")
    print("=" * 50)
    print()

    # Check icon files exist
    if not os.path.exists(ico_path):
        print(f"ERROR: Icon not found at {ico_path}")
        print("Make sure integra.ico is in resources/icons/")
        return
    
    print(f"[OK] Icon found: {ico_path}")
    print()

    # Create shortcut
    print("Creating Desktop shortcut...")
    if create_shortcut(project_dir, ico_path):
        print()
        print("=" * 50)
        print("  DONE! Double-click INTEGRA on Desktop")
        print("  No CMD window will appear!")
        print("=" * 50)
    else:
        print("FAILED to create shortcut")


if __name__ == '__main__':
    main()
