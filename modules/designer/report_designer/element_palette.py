"""
Element Palette
===============
Draggable element palette for report designer.

Features:
- Element categories
- Drag & drop support
- Tool tips
- Icons
"""

from enum import Enum
from typing import List, Dict, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout, QToolButton, QButtonGroup
)
from PyQt5.QtCore import Qt, QMimeData, pyqtSignal
from PyQt5.QtGui import QDrag, QPixmap, QPainter, QColor, QFont, QCursor

from core.logging import app_logger


class ElementType(Enum):
    """Report element types."""
    TEXT = "text"
    FIELD = "field"
    TABLE = "table"
    IMAGE = "image"
    LINE = "line"
    RECTANGLE = "rectangle"
    CHART = "chart"
    BARCODE = "barcode"
    FORMULA = "formula"
    DATE = "date"
    PAGE_NUMBER = "page_number"
    TOTAL = "total"


# Element definitions
ELEMENT_DEFINITIONS = {
    ElementType.TEXT: {
        "name_ar": "نص",
        "name_en": "Text",
        "icon": "T",
        "description": "إضافة نص ثابت",
        "category": "basic",
        "default_width": 150,
        "default_height": 30
    },
    ElementType.FIELD: {
        "name_ar": "حقل بيانات",
        "name_en": "Field",
        "icon": "[F]",
        "description": "حقل مرتبط بقاعدة البيانات",
        "category": "data",
        "default_width": 150,
        "default_height": 30
    },
    ElementType.TABLE: {
        "name_ar": "جدول",
        "name_en": "Table",
        "icon": "⊞",
        "description": "جدول بيانات",
        "category": "data",
        "default_width": 400,
        "default_height": 150
    },
    ElementType.IMAGE: {
        "name_ar": "صورة",
        "name_en": "Image",
        "icon": "🖼",
        "description": "إدراج صورة",
        "category": "media",
        "default_width": 150,
        "default_height": 100
    },
    ElementType.LINE: {
        "name_ar": "خط",
        "name_en": "Line",
        "icon": "—",
        "description": "خط أفقي أو عمودي",
        "category": "shapes",
        "default_width": 200,
        "default_height": 10
    },
    ElementType.RECTANGLE: {
        "name_ar": "مستطيل",
        "name_en": "Rectangle",
        "icon": "□",
        "description": "شكل مستطيل",
        "category": "shapes",
        "default_width": 150,
        "default_height": 80
    },
    ElementType.CHART: {
        "name_ar": "رسم بياني",
        "name_en": "Chart",
        "icon": "📊",
        "description": "رسم بياني تفاعلي",
        "category": "data",
        "default_width": 300,
        "default_height": 200
    },
    ElementType.BARCODE: {
        "name_ar": "باركود",
        "name_en": "Barcode",
        "icon": "|||",
        "description": "باركود أو QR Code",
        "category": "media",
        "default_width": 120,
        "default_height": 60
    },
    ElementType.FORMULA: {
        "name_ar": "صيغة",
        "name_en": "Formula",
        "icon": "∑",
        "description": "حقل محسوب (SUM, AVG, etc.)",
        "category": "calculations",
        "default_width": 120,
        "default_height": 30
    },
    ElementType.DATE: {
        "name_ar": "تاريخ",
        "name_en": "Date",
        "icon": "📅",
        "description": "التاريخ الحالي",
        "category": "system",
        "default_width": 120,
        "default_height": 30
    },
    ElementType.PAGE_NUMBER: {
        "name_ar": "رقم الصفحة",
        "name_en": "Page Number",
        "icon": "#",
        "description": "رقم الصفحة الحالية",
        "category": "system",
        "default_width": 80,
        "default_height": 25
    },
    ElementType.TOTAL: {
        "name_ar": "المجموع",
        "name_en": "Total",
        "icon": "Σ",
        "description": "مجموع حقل",
        "category": "calculations",
        "default_width": 120,
        "default_height": 30
    }
}

# Category definitions
CATEGORIES = {
    "basic": {"name_ar": "أساسي", "name_en": "Basic", "icon": "📝"},
    "data": {"name_ar": "بيانات", "name_en": "Data", "icon": "📊"},
    "media": {"name_ar": "وسائط", "name_en": "Media", "icon": "🖼"},
    "shapes": {"name_ar": "أشكال", "name_en": "Shapes", "icon": "⬜"},
    "calculations": {"name_ar": "حسابات", "name_en": "Calculations", "icon": "🔢"},
    "system": {"name_ar": "نظام", "name_en": "System", "icon": "⚙"}
}


class DraggableElementButton(QToolButton):
    """Draggable button representing an element type."""

    def __init__(self, element_type: ElementType, parent=None):
        super().__init__(parent)

        self.element_type = element_type
        self._definition = ELEMENT_DEFINITIONS.get(element_type, {})

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup button UI."""
        self.setFixedSize(70, 70)
        self.setCheckable(False)

        # Style
        self.setStyleSheet("""
            QToolButton {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px;
            }
            QToolButton:hover {
                background: #f3f4f6;
                border-color: #2563eb;
            }
            QToolButton:pressed {
                background: #e5e7eb;
            }
        """)

        # Tooltip
        self.setToolTip(
            f"{self._definition.get('name_ar', '')}\n{self._definition.get('description', '')}"
        )

        self.setCursor(QCursor(Qt.OpenHandCursor))

    def paintEvent(self, event) -> None:
        """Custom painting."""
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw icon
        icon = self._definition.get("icon", "?")
        painter.setFont(QFont("Segoe UI Emoji", 20))
        painter.setPen(QColor("#2563eb"))
        painter.drawText(self.rect().adjusted(0, -10, 0, 0), Qt.AlignHCenter | Qt.AlignVCenter, icon)

        # Draw label
        name = self._definition.get("name_ar", "")
        painter.setFont(QFont("Cairo", 9))
        painter.setPen(QColor("#374151"))
        painter.drawText(self.rect().adjusted(0, 25, 0, 0), Qt.AlignHCenter | Qt.AlignBottom, name)

    def mousePressEvent(self, event) -> None:
        """Start drag operation."""
        if event.button() == Qt.LeftButton:
            self.setCursor(QCursor(Qt.ClosedHandCursor))
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """Handle drag."""
        if event.buttons() & Qt.LeftButton:
            # Create drag
            drag = QDrag(self)
            mime_data = QMimeData()

            # Set element type
            mime_data.setData(
                "application/x-element-type",
                self.element_type.value.encode()
            )

            drag.setMimeData(mime_data)

            # Create drag pixmap
            pixmap = QPixmap(70, 70)
            pixmap.fill(Qt.transparent)

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)

            # Draw background
            painter.setBrush(QColor("#f0f9ff"))
            painter.setPen(QColor("#2563eb"))
            painter.drawRoundedRect(2, 2, 66, 66, 8, 8)

            # Draw icon
            icon = self._definition.get("icon", "?")
            painter.setFont(QFont("Segoe UI Emoji", 24))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, icon)

            painter.end()

            drag.setPixmap(pixmap)
            drag.setHotSpot(pixmap.rect().center())

            # Execute drag
            drag.exec_(Qt.CopyAction)

            self.setCursor(QCursor(Qt.OpenHandCursor))

    def mouseReleaseEvent(self, event) -> None:
        """Reset cursor."""
        self.setCursor(QCursor(Qt.OpenHandCursor))
        super().mouseReleaseEvent(event)


class CategorySection(QFrame):
    """Collapsible category section."""

    def __init__(self, category_id: str, elements: List[ElementType], parent=None):
        super().__init__(parent)

        self.category_id = category_id
        self.elements = elements
        self._expanded = True

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup section UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 10)
        layout.setSpacing(5)

        # Header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(5, 5, 5, 5)

        category = CATEGORIES.get(self.category_id, {})

        # Expand/collapse button
        self._toggle_btn = QPushButton("▼")
        self._toggle_btn.setFixedSize(20, 20)
        self._toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #64748b;
                font-size: 10px;
            }
        """)
        self._toggle_btn.clicked.connect(self._toggle)
        header_layout.addWidget(self._toggle_btn)

        # Category icon and name
        icon_label = QLabel(category.get("icon", ""))
        header_layout.addWidget(icon_label)

        name_label = QLabel(category.get("name_ar", ""))
        name_label.setStyleSheet("font-weight: bold; color: #374151;")
        header_layout.addWidget(name_label)

        header_layout.addStretch()
        layout.addWidget(header)

        # Elements grid
        self._grid_widget = QWidget()
        grid_layout = QGridLayout(self._grid_widget)
        grid_layout.setContentsMargins(5, 5, 5, 5)
        grid_layout.setSpacing(8)

        row, col = 0, 0
        max_cols = 2

        for element_type in self.elements:
            btn = DraggableElementButton(element_type)
            grid_layout.addWidget(btn, row, col)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        layout.addWidget(self._grid_widget)

        # Style
        self.setStyleSheet("""
            CategorySection {
                background: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }
        """)

    def _toggle(self) -> None:
        """Toggle expand/collapse."""
        self._expanded = not self._expanded
        self._grid_widget.setVisible(self._expanded)
        self._toggle_btn.setText("▼" if self._expanded else "▶")


class ElementPalette(QWidget):
    """
    Element palette widget for report designer.

    Provides draggable elements organized by category.

    Signals:
        element_clicked: Emitted when an element is clicked
    """

    element_clicked = pyqtSignal(object)  # ElementType

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup palette UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Title
        title = QLabel("عناصر التقرير")
        title.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #1f2937;
            padding: 5px;
        """)
        layout.addWidget(title)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        # Content widget
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 5, 0)
        content_layout.setSpacing(10)

        # Group elements by category
        categories_elements: Dict[str, List[ElementType]] = {}

        for element_type, definition in ELEMENT_DEFINITIONS.items():
            category = definition.get("category", "basic")
            if category not in categories_elements:
                categories_elements[category] = []
            categories_elements[category].append(element_type)

        # Create category sections
        category_order = ["basic", "data", "calculations", "shapes", "media", "system"]

        for category_id in category_order:
            if category_id in categories_elements:
                section = CategorySection(category_id, categories_elements[category_id])
                content_layout.addWidget(section)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Style
        self.setStyleSheet("""
            ElementPalette {
                background: #ffffff;
                border-left: 1px solid #e5e7eb;
            }
        """)

        self.setMinimumWidth(180)
        self.setMaximumWidth(200)

    def get_element_definition(self, element_type: ElementType) -> Dict:
        """Get element definition."""
        return ELEMENT_DEFINITIONS.get(element_type, {})
