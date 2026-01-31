"""
Input Stylesheet - Dark Theme
=============================
"""

INPUT_BACKGROUND = "#1e293b"
INPUT_TEXT_COLOR = "#f1f5f9"
INPUT_BORDER = "1px solid #334155"
INPUT_BORDER_FOCUS = "2px solid #2563eb"
INPUT_BORDER_RADIUS = "6px"
INPUT_PADDING = "10px"
INPUT_PLACEHOLDER = "#64748b"


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
            border-color: #475569;
        }}
        
        QLineEdit:disabled, QTextEdit:disabled {{
            background-color: #0f172a;
            color: #64748b;
        }}
    """
