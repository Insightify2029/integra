"""
Table Toolbar
=============
شريط أدوات الجدول فائق التطور
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel,
    QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from core.themes import get_current_theme
from .search_box import SearchBox


class TableToolbar(QWidget):
    """
    Toolbar for Enterprise Table.
    Contains search, filters, and action buttons.
    
    Signals:
        search_changed(str): Search text changed
        filter_clicked(): Filter button clicked
        columns_clicked(): Column chooser button clicked
        export_clicked(): Export button clicked
        refresh_clicked(): Refresh button clicked
        add_clicked(): Add new item clicked
    """
    
    # Signals
    search_changed = pyqtSignal(str)
    filter_clicked = pyqtSignal()
    columns_clicked = pyqtSignal()
    export_clicked = pyqtSignal()
    refresh_clicked = pyqtSignal()
    add_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._show_add_button = False
        self._title = ""
        
        self._setup_ui()
        self._apply_theme()
    
    def _setup_ui(self):
        """Setup toolbar UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)
        
        # Title label
        self._title_label = QLabel()
        self._title_label.setFont(QFont("Cairo", 16, QFont.Bold))
        layout.addWidget(self._title_label)
        
        # Spacer
        layout.addStretch()
        
        # Row count label
        self._count_label = QLabel()
        self._count_label.setFont(QFont("Cairo", 11))
        layout.addWidget(self._count_label)
        
        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.VLine)
        sep1.setFixedWidth(1)
        layout.addWidget(sep1)
        
        # Search box
        self._search_box = SearchBox()
        self._search_box.setFixedWidth(300)
        self._search_box.search_changed.connect(self.search_changed.emit)
        layout.addWidget(self._search_box)
        
        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.VLine)
        sep2.setFixedWidth(1)
        layout.addWidget(sep2)
        
        # Action buttons
        self._filter_btn = self._create_button("🔽 تصفية", self.filter_clicked.emit)
        layout.addWidget(self._filter_btn)
        
        self._columns_btn = self._create_button("📊 الأعمدة", self.columns_clicked.emit)
        layout.addWidget(self._columns_btn)
        
        self._export_btn = self._create_button("📤 تصدير", self.export_clicked.emit)
        layout.addWidget(self._export_btn)
        
        self._refresh_btn = self._create_button("🔄 تحديث", self.refresh_clicked.emit)
        layout.addWidget(self._refresh_btn)
        
        # Add button (optional)
        self._add_btn = self._create_button("➕ إضافة", self.add_clicked.emit, primary=True)
        self._add_btn.setVisible(False)
        layout.addWidget(self._add_btn)
    
    def _create_button(self, text: str, callback, primary: bool = False) -> QPushButton:
        """Create a toolbar button."""
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(callback)
        btn.setProperty("primary", primary)
        return btn
    
    def _apply_theme(self):
        """Apply current theme."""
        theme = get_current_theme()
        
        if theme == 'dark':
            self.setStyleSheet("""
                QWidget {
                    background-color: #1e293b;
                    border-bottom: 1px solid #334155;
                }
                
                QLabel {
                    color: #f1f5f9;
                    background: transparent;
                    border: none;
                }
                
                QFrame[frameShape="5"] {
                    background-color: #334155;
                }
                
                QPushButton {
                    background-color: #334155;
                    color: #f1f5f9;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 13px;
                    font-weight: 500;
                }
                
                QPushButton:hover {
                    background-color: #475569;
                }
                
                QPushButton:pressed {
                    background-color: #2563eb;
                }
                
                QPushButton[primary="true"] {
                    background-color: #2563eb;
                    color: #ffffff;
                }
                
                QPushButton[primary="true"]:hover {
                    background-color: #1d4ed8;
                }
            """)
            self._count_label.setStyleSheet("color: #94a3b8;")
        else:
            self.setStyleSheet("""
                QWidget {
                    background-color: #f8fafc;
                    border-bottom: 1px solid #e2e8f0;
                }
                
                QLabel {
                    color: #1e293b;
                    background: transparent;
                    border: none;
                }
                
                QFrame[frameShape="5"] {
                    background-color: #e2e8f0;
                }
                
                QPushButton {
                    background-color: #e2e8f0;
                    color: #1e293b;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 13px;
                    font-weight: 500;
                }
                
                QPushButton:hover {
                    background-color: #cbd5e1;
                }
                
                QPushButton:pressed {
                    background-color: #2563eb;
                    color: #ffffff;
                }
                
                QPushButton[primary="true"] {
                    background-color: #2563eb;
                    color: #ffffff;
                }
                
                QPushButton[primary="true"]:hover {
                    background-color: #1d4ed8;
                }
            """)
            self._count_label.setStyleSheet("color: #64748b;")
    
    # ═══════════════════════════════════════════════════════════════
    # Public API
    # ═══════════════════════════════════════════════════════════════
    
    def set_title(self, title: str):
        """Set toolbar title."""
        self._title = title
        self._title_label.setText(title)
    
    def set_row_count(self, total: int, visible: int = None):
        """Set row count display."""
        if visible is not None and visible != total:
            self._count_label.setText(f"عرض {visible} من {total}")
        else:
            self._count_label.setText(f"إجمالي: {total}")
    
    def show_add_button(self, show: bool = True):
        """Show or hide add button."""
        self._show_add_button = show
        self._add_btn.setVisible(show)
    
    def set_add_button_text(self, text: str):
        """Set add button text."""
        self._add_btn.setText(text)
    
    def get_search_text(self) -> str:
        """Get current search text."""
        return self._search_box.get_text()
    
    def clear_search(self):
        """Clear search box."""
        self._search_box.clear()
    
    def set_search_placeholder(self, text: str):
        """Set search placeholder text."""
        self._search_box.set_placeholder(text)
