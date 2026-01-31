"""
Dialog Stylesheet - Dark Theme
==============================
"""

DIALOG_BACKGROUND = "#1e293b"
DIALOG_BORDER = "1px solid #334155"


def get_dialog_stylesheet():
    """Get complete dialog stylesheet."""
    return f"""
        QDialog {{
            background-color: {DIALOG_BACKGROUND};
            border: {DIALOG_BORDER};
            border-radius: 12px;
        }}
        
        QGroupBox {{
            color: #06b6d4;
            font-weight: 600;
            border: 1px solid #334155;
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
            background-color: #1e293b;
            color: #f1f5f9;
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 10px;
            font-size: 13px;
        }}
        
        QComboBox:hover {{
            border-color: #475569;
        }}
        
        QComboBox::drop-down {{
            border: none;
            padding-right: 10px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: #1e293b;
            color: #f1f5f9;
            border: 1px solid #334155;
            selection-background-color: #2563eb;
        }}
    """
