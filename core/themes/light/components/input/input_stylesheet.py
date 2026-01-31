"""
Input Stylesheet - Light Theme
==============================
"""

INPUT_BACKGROUND = "#ffffff"
INPUT_TEXT_COLOR = "#1e293b"
INPUT_BORDER = "1px solid #cbd5e1"
INPUT_BORDER_FOCUS = "2px solid #2563eb"
INPUT_BORDER_RADIUS = "6px"
INPUT_PADDING = "10px"


def get_input_stylesheet():
    """Get complete input stylesheet."""
    return f"""
        QLineEdit, QTextEdit {{
            background-color: {INPUT_BACKGROUND};
            color: {INPUT_TEXT_COLOR};
            border: {INPUT_BORDER};
            border-radius: {INPUT_BORDER_RADIUS};
            padding: {INPUT_PADDING};
            font-size: 13px;
        }}
        
        QLineEdit:focus, QTextEdit:focus {{
            border: {INPUT_BORDER_FOCUS};
        }}
        
        QLineEdit:hover, QTextEdit:hover {{
            border-color: #94a3b8;
        }}
        
        QLineEdit:disabled, QTextEdit:disabled {{
            background-color: #f1f5f9;
            color: #94a3b8;
        }}
    """
