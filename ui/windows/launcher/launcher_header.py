"""
Launcher Header
===============
The INTEGRA logo and subtitle.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt

from ui.components.labels import LogoLabel


def create_launcher_header():
    """
    Create the launcher header widget.
    
    Returns:
        QWidget: The header widget
    """
    header = QWidget()
    layout = QVBoxLayout(header)
    layout.setContentsMargins(0, 30, 0, 30)
    layout.setAlignment(Qt.AlignCenter)
    
    # Logo
    logo = LogoLabel("I N T E G R A")
    layout.addWidget(logo)
    
    return header
