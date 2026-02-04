"""
Widget Toolbox
==============
Draggable widget palette for form builder.

Features:
- Categorized widgets
- Drag & drop support
- Tool tips
- Icons
"""

from typing import List, Dict
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea,
    QGridLayout, QToolButton
)
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QDrag, QPixmap, QPainter, QColor, QFont, QCursor

from core.logging import app_logger
from .form_canvas import WidgetType


# Widget definitions
WIDGET_DEFINITIONS = {
    WidgetType.LABEL: {
        "name_ar": "نص",
        "icon": "Aa",
        "description": "عنصر نص ثابت",
        "category": "basic"
    },
    WidgetType.TEXT_INPUT: {
        "name_ar": "حقل نصي",
        "icon": "[__]",
        "description": "حقل إدخال نص",
        "category": "input"
    },
    WidgetType.TEXT_AREA: {
        "name_ar": "منطقة نص",
        "icon": "[===]",
        "description": "منطقة نص متعددة الأسطر",
        "category": "input"
    },
    WidgetType.NUMBER_INPUT: {
        "name_ar": "رقم",
        "icon": "123",
        "description": "حقل إدخال أرقام",
        "category": "input"
    },
    WidgetType.DECIMAL_INPUT: {
        "name_ar": "عشري",
        "icon": "1.2",
        "description": "حقل أرقام عشرية",
        "category": "input"
    },
    WidgetType.COMBO_BOX: {
        "name_ar": "قائمة",
        "icon": "[▼]",
        "description": "قائمة منسدلة",
        "category": "selection"
    },
    WidgetType.CHECK_BOX: {
        "name_ar": "اختيار",
        "icon": "☑",
        "description": "مربع اختيار",
        "category": "selection"
    },
    WidgetType.RADIO_BUTTON: {
        "name_ar": "راديو",
        "icon": "◉",
        "description": "زر راديو",
        "category": "selection"
    },
    WidgetType.DATE_PICKER: {
        "name_ar": "تاريخ",
        "icon": "📅",
        "description": "منتقي التاريخ",
        "category": "datetime"
    },
    WidgetType.TIME_PICKER: {
        "name_ar": "وقت",
        "icon": "🕐",
        "description": "منتقي الوقت",
        "category": "datetime"
    },
    WidgetType.BUTTON: {
        "name_ar": "زر",
        "icon": "[OK]",
        "description": "زر ضغط",
        "category": "action"
    },
    WidgetType.GROUP_BOX: {
        "name_ar": "مجموعة",
        "icon": "⬜",
        "description": "إطار مجموعة",
        "category": "layout"
    },
    WidgetType.SEPARATOR: {
        "name_ar": "فاصل",
        "icon": "—",
        "description": "خط فاصل",
        "category": "layout"
    },
    WidgetType.IMAGE: {
        "name_ar": "صورة",
        "icon": "🖼",
        "description": "عنصر صورة",
        "category": "media"
    },
    WidgetType.TABLE: {
        "name_ar": "جدول",
        "icon": "⊞",
        "description": "جدول بيانات",
        "category": "data"
    }
}

CATEGORIES = {
    "basic": {"name_ar": "أساسي", "icon": "📝"},
    "input": {"name_ar": "إدخال", "icon": "✏️"},
    "selection": {"name_ar": "اختيار", "icon": "☑️"},
    "datetime": {"name_ar": "تاريخ/وقت", "icon": "📅"},
    "action": {"name_ar": "إجراءات", "icon": "▶️"},
    "layout": {"name_ar": "تخطيط", "icon": "⬜"},
    "media": {"name_ar": "وسائط", "icon": "🖼"},
    "data": {"name_ar": "بيانات", "icon": "📊"}
}


class DraggableWidgetButton(QToolButton):
    """Draggable button for widget type."""

    def __init__(self, widget_type: WidgetType, parent=None):
        super().__init__(parent)

        self.widget_type = widget_type
        self._definition = WIDGET_DEFINITIONS.get(widget_type, {})

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup button UI."""
        self.setFixedSize(70, 60)

        self.setStyleSheet("""
            QToolButton {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
            }
            QToolButton:hover {
                background: #f3f4f6;
                border-color: #2563eb;
            }
        """)

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
        painter.setFont(QFont("Segoe UI Emoji", 16))
        painter.setPen(QColor("#2563eb"))
        painter.drawText(self.rect().adjusted(0, -8, 0, 0), Qt.AlignHCenter | Qt.AlignVCenter, icon)

        # Draw label
        name = self._definition.get("name_ar", "")
        painter.setFont(QFont("Cairo", 8))
        painter.setPen(QColor("#374151"))
        painter.drawText(self.rect().adjusted(0, 20, 0, 0), Qt.AlignHCenter | Qt.AlignBottom, name)

    def mousePressEvent(self, event) -> None:
        """Start drag."""
        if event.button() == Qt.LeftButton:
            self.setCursor(QCursor(Qt.ClosedHandCursor))
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """Handle drag."""
        if event.buttons() & Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()

            mime_data.setData(
                "application/x-widget-type",
                self.widget_type.value.encode()
            )

            drag.setMimeData(mime_data)

            # Create drag pixmap
            pixmap = QPixmap(60, 50)
            pixmap.fill(Qt.transparent)

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QColor("#f0f9ff"))
            painter.setPen(QColor("#2563eb"))
            painter.drawRoundedRect(2, 2, 56, 46, 6, 6)

            icon = self._definition.get("icon", "?")
            painter.setFont(QFont("Segoe UI Emoji", 18))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, icon)
            painter.end()

            drag.setPixmap(pixmap)
            drag.setHotSpot(pixmap.rect().center())

            drag.exec_(Qt.CopyAction)
            self.setCursor(QCursor(Qt.OpenHandCursor))

    def mouseReleaseEvent(self, event) -> None:
        """Reset cursor."""
        self.setCursor(QCursor(Qt.OpenHandCursor))
        super().mouseReleaseEvent(event)


class WidgetToolbox(QWidget):
    """Widget toolbox for form builder."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup toolbox UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Title
        title = QLabel("الأدوات")
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
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 5, 0)
        content_layout.setSpacing(10)

        # Group widgets by category
        categories_widgets: Dict[str, List[WidgetType]] = {}

        for widget_type, definition in WIDGET_DEFINITIONS.items():
            category = definition.get("category", "basic")
            if category not in categories_widgets:
                categories_widgets[category] = []
            categories_widgets[category].append(widget_type)

        # Create category sections
        category_order = ["basic", "input", "selection", "datetime", "action", "layout", "media", "data"]

        for category_id in category_order:
            if category_id in categories_widgets:
                category = CATEGORIES.get(category_id, {})

                # Category header
                header = QLabel(f"{category.get('icon', '')} {category.get('name_ar', '')}")
                header.setStyleSheet("""
                    font-weight: bold;
                    color: #374151;
                    padding: 5px;
                    background: #f3f4f6;
                    border-radius: 4px;
                """)
                content_layout.addWidget(header)

                # Widgets grid
                grid = QWidget()
                grid_layout = QGridLayout(grid)
                grid_layout.setContentsMargins(5, 5, 5, 5)
                grid_layout.setSpacing(6)

                row, col = 0, 0
                for widget_type in categories_widgets[category_id]:
                    btn = DraggableWidgetButton(widget_type)
                    grid_layout.addWidget(btn, row, col)

                    col += 1
                    if col >= 2:
                        col = 0
                        row += 1

                content_layout.addWidget(grid)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Style
        self.setStyleSheet("""
            WidgetToolbox {
                background: #ffffff;
                border-left: 1px solid #e5e7eb;
            }
        """)

        self.setMinimumWidth(180)
        self.setMaximumWidth(200)
