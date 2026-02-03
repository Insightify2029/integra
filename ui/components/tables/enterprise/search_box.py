"""
Search Box
==========
صندوق بحث فوري مع تأخير ذكي
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit
)
from PyQt5.QtCore import pyqtSignal, QTimer

from core.themes import get_current_theme


class SearchBox(QWidget):
    """
    Smart search box with debounce.
    
    Signals:
        search_changed(str): Emitted when search text changes (debounced)
        search_submitted(str): Emitted when Enter is pressed
    """
    
    # Signals
    search_changed = pyqtSignal(str)
    search_submitted = pyqtSignal(str)
    
    def __init__(self, parent=None, debounce_ms: int = 300):
        super().__init__(parent)
        
        self._debounce_ms = debounce_ms
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._emit_search)
        
        self._setup_ui()
        self._apply_theme()
    
    def _setup_ui(self):
        """Setup UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Search input
        self._input = QLineEdit()
        self._input.setPlaceholderText("🔍 بحث...")
        self._input.setClearButtonEnabled(True)
        self._input.textChanged.connect(self._on_text_changed)
        self._input.returnPressed.connect(self._on_return_pressed)
        layout.addWidget(self._input)
    
    def _apply_theme(self):
        """Apply current theme."""
        theme = get_current_theme()
        
        if theme == 'dark':
            self._input.setStyleSheet("""
                QLineEdit {
                    background-color: #0f172a;
                    color: #f1f5f9;
                    border: 1px solid #334155;
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-size: 13px;
                }
                
                QLineEdit:focus {
                    border: 2px solid #2563eb;
                }
                
                QLineEdit::placeholder {
                    color: #64748b;
                }
            """)
        else:
            self._input.setStyleSheet("""
                QLineEdit {
                    background-color: #ffffff;
                    color: #1e293b;
                    border: 1px solid #e2e8f0;
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-size: 13px;
                }
                
                QLineEdit:focus {
                    border: 2px solid #2563eb;
                }
                
                QLineEdit::placeholder {
                    color: #94a3b8;
                }
            """)
    
    def _on_text_changed(self, text: str):
        """Handle text change with debounce."""
        self._debounce_timer.stop()
        self._debounce_timer.start(self._debounce_ms)
    
    def _on_return_pressed(self):
        """Handle Enter key."""
        self._debounce_timer.stop()
        text = self._input.text()
        self.search_submitted.emit(text)
        self.search_changed.emit(text)
    
    def _emit_search(self):
        """Emit search signal after debounce."""
        text = self._input.text()
        self.search_changed.emit(text)
    
    # ═══════════════════════════════════════════════════════════════
    # Public API
    # ═══════════════════════════════════════════════════════════════
    
    def get_text(self) -> str:
        """Get current search text."""
        return self._input.text()
    
    def set_text(self, text: str):
        """Set search text."""
        self._input.setText(text)
    
    def clear(self):
        """Clear search box."""
        self._input.clear()
    
    def set_placeholder(self, text: str):
        """Set placeholder text."""
        self._input.setPlaceholderText(text)
    
    def set_focus(self):
        """Set focus to search input."""
        self._input.setFocus()
