"""
Dialog Stylesheet - Light Theme
===============================
"""

DIALOG_BACKGROUND = "#ffffff"
DIALOG_BORDER = "1px solid #e2e8f0"


def get_dialog_stylesheet():
    """Get complete dialog stylesheet."""
    return f"""
        QDialog {{
            background-color: {DIALOG_BACKGROUND};
            border: {DIALOG_BORDER};
            border-radius: 12px;
        }}
        
        QGroupBox {{
            color: #0891b2;
            font-weight: 600;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            margin-top: 15px;
            padding-top: 15px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 15px;
            padding: 0 5px;
        }}
        
        QComboBox {{
            background-color: #ffffff;
            color: #1e293b;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 10px;
            font-size: 13px;
        }}
        
        QComboBox:hover {{
            border-color: #94a3b8;
        }}
        
        QComboBox::drop-down {{
            border: none;
            padding-right: 10px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: #ffffff;
            color: #1e293b;
            border: 1px solid #e2e8f0;
            selection-background-color: #2563eb;
            selection-color: white;
        }}
    """
