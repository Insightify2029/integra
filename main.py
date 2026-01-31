"""
INTEGRA - Integrated Management System
======================================
Entry Point
Version: 2.1.0
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    
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
