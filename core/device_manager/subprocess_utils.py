"""
Subprocess Utilities for Device Manager
========================================
Provides hidden startupinfo to prevent visible console windows
when running PowerShell or other commands on Windows.
"""

import subprocess
import sys


def get_hidden_startupinfo():
    """Return subprocess startupinfo that hides console windows on Windows.

    Use this for all subprocess.run() calls that invoke PowerShell or other
    console programs to prevent visible cmd/PowerShell windows from popping up.

    Returns:
        subprocess.STARTUPINFO on Windows, None on other platforms.
    """
    if sys.platform == 'win32':
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = subprocess.SW_HIDE
        return si
    return None


# Re-usable startupinfo for all device_manager subprocess calls
HIDDEN_STARTUPINFO = get_hidden_startupinfo()
