"""
Mostahaqat Toolbar
==================
Toolbar for the module window.
"""

from PyQt5.QtWidgets import QToolBar, QAction


def create_mostahaqat_toolbar(window):
    """
    Create the module toolbar.
    
    Args:
        window: The parent window
    
    Returns:
        tuple: (toolbar, actions dict)
    """
    toolbar = QToolBar("Mostahaqat Toolbar")
    toolbar.setMovable(False)
    
    actions = {}
    
    # Employees
    actions['employees'] = QAction("👥 الموظفين", window)
    toolbar.addAction(actions['employees'])
    
    # Add
    actions['add'] = QAction("➕ إضافة", window)
    toolbar.addAction(actions['add'])
    
    toolbar.addSeparator()
    
    # Leave Settlement
    actions['leave'] = QAction("🏖️ تسوية إجازة", window)
    toolbar.addAction(actions['leave'])
    
    # Overtime
    actions['overtime'] = QAction("⏰ إضافي", window)
    toolbar.addAction(actions['overtime'])
    
    # End of Service
    actions['eos'] = QAction("📋 نهاية خدمة", window)
    toolbar.addAction(actions['eos'])
    
    toolbar.addSeparator()
    
    # Reports
    actions['reports'] = QAction("📊 تقارير", window)
    toolbar.addAction(actions['reports'])
    
    # Refresh
    actions['refresh'] = QAction("🔄 تحديث", window)
    toolbar.addAction(actions['refresh'])
    
    return toolbar, actions
