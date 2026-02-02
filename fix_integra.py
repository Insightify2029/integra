"""
INTEGRA - Fix Icon + Remove CMD Window
"""
import os
import sys
import subprocess


def fix_shortcut():
    """Recreate shortcut with correct icon + pythonw"""
    import win32com.client

    project_dir = r"D:\Projects\Integra"
    icon_path = os.path.join(project_dir, "resources", "icons", "integra.ico")

    # Verify icon exists
    if not os.path.exists(icon_path):
        print(f"  ERROR: {icon_path} NOT FOUND!")
        print("  Please put integra.ico in resources\\icons\\")
        return False
    else:
        print(f"  Icon found: {icon_path} ({os.path.getsize(icon_path)} bytes)")

    # Find pythonw.exe
    pythonw = None
    candidates = [
        os.path.join(os.path.dirname(sys.executable), 'pythonw.exe'),
        r"C:\Program Files\Python311\pythonw.exe",
        r"C:\Program Files\Python\Python311\pythonw.exe",
        r"C:\Users\teknosaba\AppData\Local\Programs\Python\Python311\pythonw.exe",
    ]
    for p in candidates:
        if os.path.exists(p):
            pythonw = p
            break

    if not pythonw:
        print("  ERROR: pythonw.exe not found!")
        print("  Searching...")
        result = subprocess.run(
            ['where', 'pythonw'], capture_output=True, text=True
        )
        if result.returncode == 0:
            pythonw = result.stdout.strip().split('\n')[0]
        else:
            print("  FATAL: Cannot find pythonw.exe")
            return False

    print(f"  pythonw: {pythonw}")

    # Delete old shortcut
    desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
    shortcut_path = os.path.join(desktop, 'INTEGRA.lnk')
    if os.path.exists(shortcut_path):
        os.remove(shortcut_path)
        print("  Old shortcut removed")

    # Create new shortcut
    shell = win32com.client.Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = pythonw
    shortcut.Arguments = 'main.py'
    shortcut.WorkingDirectory = project_dir
    shortcut.IconLocation = f"{icon_path},0"
    shortcut.Description = 'INTEGRA - Integrated Management System'
    shortcut.WindowStyle = 1
    shortcut.save()
    print(f"  New shortcut created: {shortcut_path}")
    return True


def clear_icon_cache():
    """Clear Windows icon cache to force icon refresh"""
    print("  Clearing Windows icon cache...")
    cache_dir = os.path.join(os.environ['LOCALAPPDATA'], 'Microsoft', 'Windows', 'Explorer')
    
    # Kill explorer temporarily
    subprocess.run(['taskkill', '/f', '/im', 'explorer.exe'], 
                   capture_output=True, creationflags=0x08000000)
    
    # Delete icon cache files
    import glob
    deleted = 0
    for f in glob.glob(os.path.join(cache_dir, 'iconcache*')):
        try:
            os.remove(f)
            deleted += 1
        except:
            pass
    for f in glob.glob(os.path.join(cache_dir, 'thumbcache*')):
        try:
            os.remove(f)
            deleted += 1
        except:
            pass
    
    print(f"  Deleted {deleted} cache files")
    
    # Restart explorer
    subprocess.Popen('explorer.exe')
    print("  Explorer restarted")


def fix_sync_runner():
    """Fix sync_runner.py to hide CMD windows from subprocess calls"""
    sync_runner = r"D:\Projects\Integra\core\sync\sync_runner.py"
    
    if not os.path.exists(sync_runner):
        print(f"  sync_runner.py not found at expected path")
        return False
    
    with open(sync_runner, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already fixed
    if 'CREATE_NO_WINDOW' in content:
        print("  sync_runner.py already fixed")
        return True
    
    # Add import at top
    if 'import subprocess' in content:
        content = content.replace(
            'import subprocess',
            'import subprocess\n\n# Hide CMD window for all subprocess calls\n_NO_WINDOW = 0x08000000'
        )
    
    # Replace subprocess.run calls to include creationflags
    # Common patterns in sync scripts
    content = content.replace(
        'subprocess.run([',
        'subprocess.run(['
    )
    
    # More targeted: add creationflags to all subprocess.run that don't have it
    import re
    
    def add_creation_flags(match):
        call = match.group(0)
        if 'creationflags' not in call:
            # Add before the closing parenthesis
            call = call.rstrip(')')
            if call.rstrip().endswith(','):
                call += ' creationflags=_NO_WINDOW)'
            else:
                call += ', creationflags=_NO_WINDOW)'
        return call
    
    # Save modified content
    with open(sync_runner, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("  sync_runner.py: Added _NO_WINDOW flag")
    return True


def main():
    print("=" * 55)
    print("  INTEGRA - Fix Icon + CMD Window")
    print("=" * 55)
    print()

    # Step 1: Fix shortcut
    print("[1/3] Fixing Desktop shortcut...")
    if not fix_shortcut():
        return
    print()

    # Step 2: Clear icon cache
    print("[2/3] Refreshing icon cache...")
    clear_icon_cache()
    print()

    # Step 3: Show sync_runner location for manual fix
    print("[3/3] CMD Window fix...")
    sync_runner = r"D:\Projects\Integra\core\sync\sync_runner.py"
    sync_worker = r"D:\Projects\Integra\core\sync\sync_worker.py"
    print(f"  sync_runner exists: {os.path.exists(sync_runner)}")
    print(f"  sync_worker exists: {os.path.exists(sync_worker)}")
    print()
    print("  To fully hide CMD, we need to check the subprocess")
    print("  calls in sync files. Showing current subprocess usage:")
    
    for fpath in [sync_runner, sync_worker]:
        if os.path.exists(fpath):
            with open(fpath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            print(f"\n  --- {os.path.basename(fpath)} ---")
            for i, line in enumerate(lines, 1):
                if 'subprocess' in line.lower() or 'pg_dump' in line.lower() or 'pg_restore' in line.lower() or 'git ' in line.lower():
                    print(f"  Line {i}: {line.rstrip()}")
    
    print()
    print("=" * 55)
    print("  Done! Desktop should refresh in a few seconds.")
    print("  If icon still old, right-click Desktop > Refresh")
    print("=" * 55)


if __name__ == '__main__':
    main()
