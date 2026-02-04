"""
Design Canvas
=============
WYSIWYG canvas for report design with drag & drop support.

Features:
- Report bands (Header, Detail, Footer, Group)
- Element placement with grid snapping
- Selection and multi-selection
- Resize handles
- Undo/Redo support
- Copy/Paste
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from PyQt5.QtWidgets import (
    QWidget, QGraphicsView, QGraphicsScene, QGraphicsItem,
    QGraphicsRectItem, QGraphicsTextItem, QGraphicsPixmapItem,
    QGraphicsLineItem, QMenu, QAction, QUndoStack, QUndoCommand
)
from PyQt5.QtCore import Qt, QRectF, QPointF, QSizeF, pyqtSignal, QMimeData
from PyQt5.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPixmap,
    QTransform, QDrag, QCursor
)

from core.logging import app_logger


class BandType(Enum):
    """Report band types."""
    PAGE_HEADER = "page_header"
    REPORT_HEADER = "report_header"
    GROUP_HEADER = "group_header"
    DETAIL = "detail"
    GROUP_FOOTER = "group_footer"
    REPORT_FOOTER = "report_footer"
    PAGE_FOOTER = "page_footer"


class ElementType(Enum):
    """Canvas element types."""
    TEXT = "text"
    FIELD = "field"
    TABLE = "table"
    IMAGE = "image"
    LINE = "line"
    RECTANGLE = "rectangle"
    CHART = "chart"
    BARCODE = "barcode"
    FORMULA = "formula"


@dataclass
class ElementStyle:
    """Element visual style."""
    font_family: str = "Cairo"
    font_size: int = 12
    font_color: str = "#000000"
    background_color: Optional[str] = None
    border_color: Optional[str] = "#cccccc"
    border_width: float = 0
    bold: bool = False
    italic: bool = False
    underline: bool = False
    alignment: str = "right"  # left, center, right
    padding: Tuple[int, int, int, int] = (4, 4, 4, 4)  # top, right, bottom, left


@dataclass
class CanvasElement:
    """Element on the design canvas."""
    id: str
    element_type: ElementType
    x: float
    y: float
    width: float
    height: float
    content: Any = None
    style: ElementStyle = field(default_factory=ElementStyle)
    properties: Dict[str, Any] = field(default_factory=dict)
    band: str = "detail"

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.element_type.value,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "content": self.content,
            "style": {
                "font_family": self.style.font_family,
                "font_size": self.style.font_size,
                "font_color": self.style.font_color,
                "background_color": self.style.background_color,
                "border_color": self.style.border_color,
                "border_width": self.style.border_width,
                "bold": self.style.bold,
                "italic": self.style.italic,
                "underline": self.style.underline,
                "alignment": self.style.alignment,
                "padding": self.style.padding
            },
            "properties": self.properties,
            "band": self.band
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'CanvasElement':
        """Create from dictionary."""
        style_data = data.get("style", {})
        style = ElementStyle(
            font_family=style_data.get("font_family", "Cairo"),
            font_size=style_data.get("font_size", 12),
            font_color=style_data.get("font_color", "#000000"),
            background_color=style_data.get("background_color"),
            border_color=style_data.get("border_color"),
            border_width=style_data.get("border_width", 0),
            bold=style_data.get("bold", False),
            italic=style_data.get("italic", False),
            underline=style_data.get("underline", False),
            alignment=style_data.get("alignment", "right"),
            padding=tuple(style_data.get("padding", (4, 4, 4, 4)))
        )

        return cls(
            id=data.get("id", ""),
            element_type=ElementType(data.get("type", "text")),
            x=data.get("x", 0),
            y=data.get("y", 0),
            width=data.get("width", 100),
            height=data.get("height", 30),
            content=data.get("content"),
            style=style,
            properties=data.get("properties", {}),
            band=data.get("band", "detail")
        )


@dataclass
class ReportBand:
    """Report band definition."""
    band_type: BandType
    height: float = 80
    visible: bool = True
    background_color: str = "#ffffff"
    elements: List[CanvasElement] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "type": self.band_type.value,
            "height": self.height,
            "visible": self.visible,
            "background_color": self.background_color,
            "elements": [e.to_dict() for e in self.elements]
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ReportBand':
        """Create from dictionary."""
        return cls(
            band_type=BandType(data.get("type", "detail")),
            height=data.get("height", 80),
            visible=data.get("visible", True),
            background_color=data.get("background_color", "#ffffff"),
            elements=[CanvasElement.from_dict(e) for e in data.get("elements", [])]
        )


class DesignElementItem(QGraphicsRectItem):
    """Graphics item representing a design element."""

    def __init__(self, element: CanvasElement, parent=None):
        super().__init__(parent)

        self.element = element
        self._resizing = False
        self._resize_handle = None
        self._handle_size = 8

        self.setRect(0, 0, element.width, element.height)
        self.setPos(element.x, element.y)

        # Enable selection and movement
        self.setFlags(
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemSendsGeometryChanges
        )

        self.setAcceptHoverEvents(True)
        self._update_appearance()

    def _update_appearance(self) -> None:
        """Update visual appearance based on element style."""
        style = self.element.style

        # Background
        if style.background_color:
            self.setBrush(QBrush(QColor(style.background_color)))
        else:
            self.setBrush(QBrush(Qt.transparent))

        # Border
        if style.border_width > 0 and style.border_color:
            self.setPen(QPen(QColor(style.border_color), style.border_width))
        else:
            self.setPen(QPen(QColor("#cccccc"), 1, Qt.DashLine))

    def paint(self, painter: QPainter, option, widget=None) -> None:
        """Custom painting."""
        # Draw background and border
        super().paint(painter, option, widget)

        style = self.element.style
        rect = self.rect()

        # Draw content based on type
        painter.save()

        # Set font
        font = QFont(style.font_family, style.font_size)
        font.setBold(style.bold)
        font.setItalic(style.italic)
        font.setUnderline(style.underline)
        painter.setFont(font)
        painter.setPen(QColor(style.font_color))

        # Text alignment
        align_map = {
            "left": Qt.AlignLeft,
            "center": Qt.AlignHCenter,
            "right": Qt.AlignRight
        }
        alignment = align_map.get(style.alignment, Qt.AlignRight) | Qt.AlignVCenter

        # Draw text content
        padding = style.padding
        content_rect = QRectF(
            padding[3],
            padding[0],
            rect.width() - padding[1] - padding[3],
            rect.height() - padding[0] - padding[2]
        )

        if self.element.element_type == ElementType.TEXT:
            text = str(self.element.content or "نص")
            painter.drawText(content_rect, alignment, text)

        elif self.element.element_type == ElementType.FIELD:
            field_name = self.element.properties.get("field_name", "حقل")
            painter.setPen(QColor("#2563eb"))
            painter.drawText(content_rect, alignment, f"[{field_name}]")

        elif self.element.element_type == ElementType.IMAGE:
            # Draw placeholder
            painter.setPen(QColor("#999999"))
            painter.drawRect(content_rect)
            painter.drawText(content_rect, Qt.AlignCenter, "صورة")

        elif self.element.element_type == ElementType.TABLE:
            painter.setPen(QColor("#999999"))
            painter.drawRect(content_rect)
            painter.drawText(content_rect, Qt.AlignCenter, "جدول")

        elif self.element.element_type == ElementType.CHART:
            painter.setPen(QColor("#10b981"))
            painter.drawRect(content_rect)
            painter.drawText(content_rect, Qt.AlignCenter, "رسم بياني")

        elif self.element.element_type == ElementType.LINE:
            painter.setPen(QPen(QColor(style.font_color), 2))
            painter.drawLine(
                int(content_rect.left()),
                int(content_rect.center().y()),
                int(content_rect.right()),
                int(content_rect.center().y())
            )

        elif self.element.element_type == ElementType.FORMULA:
            formula = self.element.properties.get("formula", "=SUM()")
            painter.setPen(QColor("#f59e0b"))
            painter.drawText(content_rect, alignment, formula)

        painter.restore()

        # Draw selection handles
        if self.isSelected():
            self._draw_selection_handles(painter)

    def _draw_selection_handles(self, painter: QPainter) -> None:
        """Draw resize handles when selected."""
        painter.save()
        painter.setPen(QPen(QColor("#2563eb"), 1))
        painter.setBrush(QBrush(Qt.white))

        rect = self.rect()
        size = self._handle_size

        # Corner handles
        handles = [
            QRectF(0, 0, size, size),  # Top-left
            QRectF(rect.width() - size, 0, size, size),  # Top-right
            QRectF(0, rect.height() - size, size, size),  # Bottom-left
            QRectF(rect.width() - size, rect.height() - size, size, size),  # Bottom-right
            # Edge handles
            QRectF(rect.width() / 2 - size / 2, 0, size, size),  # Top
            QRectF(rect.width() / 2 - size / 2, rect.height() - size, size, size),  # Bottom
            QRectF(0, rect.height() / 2 - size / 2, size, size),  # Left
            QRectF(rect.width() - size, rect.height() / 2 - size / 2, size, size),  # Right
        ]

        for handle in handles:
            painter.drawRect(handle)

        painter.restore()

    def _get_resize_handle(self, pos: QPointF) -> Optional[str]:
        """Get resize handle at position."""
        rect = self.rect()
        size = self._handle_size

        handles = {
            "top_left": QRectF(0, 0, size, size),
            "top_right": QRectF(rect.width() - size, 0, size, size),
            "bottom_left": QRectF(0, rect.height() - size, size, size),
            "bottom_right": QRectF(rect.width() - size, rect.height() - size, size, size),
            "top": QRectF(rect.width() / 2 - size / 2, 0, size, size),
            "bottom": QRectF(rect.width() / 2 - size / 2, rect.height() - size, size, size),
            "left": QRectF(0, rect.height() / 2 - size / 2, size, size),
            "right": QRectF(rect.width() - size, rect.height() / 2 - size / 2, size, size),
        }

        for name, handle_rect in handles.items():
            if handle_rect.contains(pos):
                return name

        return None

    def hoverMoveEvent(self, event) -> None:
        """Update cursor on hover."""
        if self.isSelected():
            handle = self._get_resize_handle(event.pos())
            cursor_map = {
                "top_left": Qt.SizeFDiagCursor,
                "top_right": Qt.SizeBDiagCursor,
                "bottom_left": Qt.SizeBDiagCursor,
                "bottom_right": Qt.SizeFDiagCursor,
                "top": Qt.SizeVerCursor,
                "bottom": Qt.SizeVerCursor,
                "left": Qt.SizeHorCursor,
                "right": Qt.SizeHorCursor,
            }
            if handle:
                self.setCursor(cursor_map.get(handle, Qt.ArrowCursor))
            else:
                self.setCursor(Qt.SizeAllCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

        super().hoverMoveEvent(event)

    def mousePressEvent(self, event) -> None:
        """Handle mouse press for resizing."""
        if self.isSelected() and event.button() == Qt.LeftButton:
            self._resize_handle = self._get_resize_handle(event.pos())
            if self._resize_handle:
                self._resizing = True
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move for resizing."""
        if self._resizing:
            pos = event.pos()
            rect = self.rect()

            # Calculate new size based on handle
            if self._resize_handle == "right":
                rect.setWidth(max(30, pos.x()))
            elif self._resize_handle == "bottom":
                rect.setHeight(max(20, pos.y()))
            elif self._resize_handle == "bottom_right":
                rect.setWidth(max(30, pos.x()))
                rect.setHeight(max(20, pos.y()))
            elif self._resize_handle == "left":
                delta = pos.x()
                new_width = rect.width() - delta
                if new_width >= 30:
                    self.setPos(self.x() + delta, self.y())
                    rect.setWidth(new_width)
            elif self._resize_handle == "top":
                delta = pos.y()
                new_height = rect.height() - delta
                if new_height >= 20:
                    self.setPos(self.x(), self.y() + delta)
                    rect.setHeight(new_height)

            self.setRect(rect)

            # Update element data
            self.element.width = rect.width()
            self.element.height = rect.height()
            self.element.x = self.x()
            self.element.y = self.y()

            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release."""
        if self._resizing:
            self._resizing = False
            self._resize_handle = None
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def itemChange(self, change, value):
        """Handle item changes."""
        if change == QGraphicsItem.ItemPositionChange:
            # Snap to grid
            grid_size = 10
            x = round(value.x() / grid_size) * grid_size
            y = round(value.y() / grid_size) * grid_size
            value = QPointF(x, y)

            # Update element data
            self.element.x = x
            self.element.y = y

        return super().itemChange(change, value)


class BandItem(QGraphicsRectItem):
    """Graphics item representing a report band."""

    def __init__(self, band: ReportBand, y_position: float, width: float, parent=None):
        super().__init__(parent)

        self.band = band
        self.y_position = y_position

        self.setRect(0, y_position, width, band.height)
        self.setBrush(QBrush(QColor(band.background_color)))
        self.setPen(QPen(QColor("#e5e7eb"), 1))

        # Band label
        self._label = band.band_type.value.replace("_", " ").title()

    def paint(self, painter: QPainter, option, widget=None) -> None:
        """Custom painting with band label."""
        super().paint(painter, option, widget)

        # Draw band label
        painter.save()
        painter.setFont(QFont("Cairo", 9))
        painter.setPen(QColor("#64748b"))

        label_rect = QRectF(5, self.y_position + 5, 150, 20)
        painter.drawText(label_rect, Qt.AlignLeft | Qt.AlignTop, self._label)

        # Draw separator line
        painter.setPen(QPen(QColor("#e5e7eb"), 1, Qt.DashLine))
        y = self.y_position + self.band.height
        painter.drawLine(0, int(y), int(self.rect().width()), int(y))

        painter.restore()


class DesignCanvas(QGraphicsView):
    """
    Main design canvas for report editing.

    Signals:
        element_selected: Emitted when an element is selected
        element_changed: Emitted when an element is modified
        canvas_changed: Emitted when canvas content changes
    """

    element_selected = pyqtSignal(object)  # CanvasElement or None
    element_changed = pyqtSignal(object)  # CanvasElement
    canvas_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        # Canvas settings
        self._page_width = 595  # A4 width in points
        self._page_height = 842  # A4 height in points
        self._grid_size = 10
        self._show_grid = True

        # Report bands
        self._bands: Dict[BandType, ReportBand] = {}
        self._elements: Dict[str, CanvasElement] = {}
        self._element_items: Dict[str, DesignElementItem] = {}
        self._next_element_id = 1

        # Undo/Redo
        self._undo_stack = QUndoStack(self)

        self._setup_ui()
        self._setup_default_bands()

        app_logger.info("DesignCanvas initialized")

    def _setup_ui(self) -> None:
        """Setup canvas UI."""
        # View settings
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

        # Scene rectangle
        self._scene.setSceneRect(0, 0, self._page_width, self._page_height)

        # Background color
        self.setBackgroundBrush(QBrush(QColor("#f3f4f6")))

        # Accept drops
        self.setAcceptDrops(True)

        # Selection change
        self._scene.selectionChanged.connect(self._on_selection_changed)

    def _setup_default_bands(self) -> None:
        """Setup default report bands."""
        self._bands = {
            BandType.PAGE_HEADER: ReportBand(BandType.PAGE_HEADER, height=60),
            BandType.REPORT_HEADER: ReportBand(BandType.REPORT_HEADER, height=80),
            BandType.DETAIL: ReportBand(BandType.DETAIL, height=40),
            BandType.REPORT_FOOTER: ReportBand(BandType.REPORT_FOOTER, height=60),
            BandType.PAGE_FOOTER: ReportBand(BandType.PAGE_FOOTER, height=40),
        }

        self._redraw_bands()

    def _redraw_bands(self) -> None:
        """Redraw all bands."""
        # Clear existing band items (keep element items)
        for item in self._scene.items():
            if isinstance(item, BandItem):
                self._scene.removeItem(item)

        # Draw page background
        page_bg = QGraphicsRectItem(0, 0, self._page_width, self._page_height)
        page_bg.setBrush(QBrush(Qt.white))
        page_bg.setPen(QPen(QColor("#d1d5db"), 1))
        page_bg.setZValue(-100)
        self._scene.addItem(page_bg)

        # Draw bands
        y = 0
        band_order = [
            BandType.PAGE_HEADER,
            BandType.REPORT_HEADER,
            BandType.DETAIL,
            BandType.REPORT_FOOTER,
            BandType.PAGE_FOOTER
        ]

        for band_type in band_order:
            band = self._bands.get(band_type)
            if band and band.visible:
                band_item = BandItem(band, y, self._page_width)
                band_item.setZValue(-50)
                self._scene.addItem(band_item)
                y += band.height

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        """Draw grid background."""
        super().drawBackground(painter, rect)

        if not self._show_grid:
            return

        # Draw grid
        painter.save()
        painter.setPen(QPen(QColor("#e5e7eb"), 0.5))

        # Vertical lines
        x = 0
        while x <= self._page_width:
            painter.drawLine(int(x), 0, int(x), int(self._page_height))
            x += self._grid_size

        # Horizontal lines
        y = 0
        while y <= self._page_height:
            painter.drawLine(0, int(y), int(self._page_width), int(y))
            y += self._grid_size

        painter.restore()

    def add_element(
        self,
        element_type: ElementType,
        x: float = 50,
        y: float = 100,
        width: float = 150,
        height: float = 30,
        content: Any = None,
        band: BandType = BandType.DETAIL
    ) -> CanvasElement:
        """
        Add new element to canvas.

        Args:
            element_type: Type of element
            x: X position
            y: Y position
            width: Element width
            height: Element height
            content: Element content
            band: Band to add element to

        Returns:
            Created CanvasElement
        """
        # Generate unique ID
        element_id = f"element_{self._next_element_id}"
        self._next_element_id += 1

        # Create element
        element = CanvasElement(
            id=element_id,
            element_type=element_type,
            x=x,
            y=y,
            width=width,
            height=height,
            content=content,
            band=band.value
        )

        # Create graphics item
        item = DesignElementItem(element)
        self._scene.addItem(item)

        # Store references
        self._elements[element_id] = element
        self._element_items[element_id] = item

        # Emit change signal
        self.canvas_changed.emit()

        app_logger.debug(f"Added element: {element_id} ({element_type.value})")
        return element

    def remove_element(self, element_id: str) -> None:
        """Remove element from canvas."""
        if element_id in self._element_items:
            item = self._element_items[element_id]
            self._scene.removeItem(item)
            del self._element_items[element_id]

        if element_id in self._elements:
            del self._elements[element_id]

        self.canvas_changed.emit()

    def get_element(self, element_id: str) -> Optional[CanvasElement]:
        """Get element by ID."""
        return self._elements.get(element_id)

    def get_selected_elements(self) -> List[CanvasElement]:
        """Get currently selected elements."""
        elements = []
        for item in self._scene.selectedItems():
            if isinstance(item, DesignElementItem):
                elements.append(item.element)
        return elements

    def update_element(self, element: CanvasElement) -> None:
        """Update element appearance."""
        if element.id in self._element_items:
            item = self._element_items[element.id]
            item.setRect(0, 0, element.width, element.height)
            item.setPos(element.x, element.y)
            item._update_appearance()
            item.update()

        self.element_changed.emit(element)
        self.canvas_changed.emit()

    def _on_selection_changed(self) -> None:
        """Handle selection changes."""
        selected = self.get_selected_elements()
        if len(selected) == 1:
            self.element_selected.emit(selected[0])
        else:
            self.element_selected.emit(None)

    def dragEnterEvent(self, event) -> None:
        """Handle drag enter."""
        if event.mimeData().hasFormat("application/x-element-type"):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event) -> None:
        """Handle drag move."""
        if event.mimeData().hasFormat("application/x-element-type"):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event) -> None:
        """Handle element drop."""
        if event.mimeData().hasFormat("application/x-element-type"):
            element_type_str = event.mimeData().data("application/x-element-type").data().decode()
            try:
                element_type = ElementType(element_type_str)
            except ValueError:
                element_type = ElementType.TEXT

            # Get drop position
            pos = self.mapToScene(event.pos())

            # Add element at drop position
            self.add_element(element_type, x=pos.x(), y=pos.y())

            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def set_grid_visible(self, visible: bool) -> None:
        """Show/hide grid."""
        self._show_grid = visible
        self.viewport().update()

    def set_page_size(self, width: float, height: float) -> None:
        """Set page size."""
        self._page_width = width
        self._page_height = height
        self._scene.setSceneRect(0, 0, width, height)
        self._redraw_bands()

    def clear(self) -> None:
        """Clear all elements."""
        for element_id in list(self._element_items.keys()):
            self.remove_element(element_id)
        self._next_element_id = 1
        self.canvas_changed.emit()

    def to_dict(self) -> Dict:
        """Export canvas to dictionary."""
        return {
            "page_width": self._page_width,
            "page_height": self._page_height,
            "bands": {k.value: v.to_dict() for k, v in self._bands.items()},
            "elements": [e.to_dict() for e in self._elements.values()]
        }

    def from_dict(self, data: Dict) -> None:
        """Import canvas from dictionary."""
        self.clear()

        # Set page size
        self._page_width = data.get("page_width", 595)
        self._page_height = data.get("page_height", 842)
        self._scene.setSceneRect(0, 0, self._page_width, self._page_height)

        # Load bands
        bands_data = data.get("bands", {})
        for band_type_str, band_data in bands_data.items():
            try:
                band_type = BandType(band_type_str)
                self._bands[band_type] = ReportBand.from_dict(band_data)
            except ValueError:
                pass

        self._redraw_bands()

        # Load elements
        for element_data in data.get("elements", []):
            element = CanvasElement.from_dict(element_data)
            self._elements[element.id] = element

            item = DesignElementItem(element)
            self._scene.addItem(item)
            self._element_items[element.id] = item

            # Update next ID
            try:
                num = int(element.id.split("_")[-1])
                self._next_element_id = max(self._next_element_id, num + 1)
            except ValueError:
                pass

        self.canvas_changed.emit()

    def get_undo_stack(self) -> QUndoStack:
        """Get undo stack."""
        return self._undo_stack

    def contextMenuEvent(self, event) -> None:
        """Show context menu."""
        menu = QMenu(self)

        # Get item at position
        item = self.itemAt(event.pos())

        if isinstance(item, DesignElementItem):
            # Element context menu
            delete_action = QAction("حذف", self)
            delete_action.triggered.connect(lambda: self.remove_element(item.element.id))
            menu.addAction(delete_action)

            menu.addSeparator()

            copy_action = QAction("نسخ", self)
            menu.addAction(copy_action)

            cut_action = QAction("قص", self)
            menu.addAction(cut_action)

            menu.addSeparator()

            bring_front = QAction("إحضار للأمام", self)
            bring_front.triggered.connect(lambda: item.setZValue(item.zValue() + 1))
            menu.addAction(bring_front)

            send_back = QAction("إرسال للخلف", self)
            send_back.triggered.connect(lambda: item.setZValue(item.zValue() - 1))
            menu.addAction(send_back)

        else:
            # Canvas context menu
            paste_action = QAction("لصق", self)
            menu.addAction(paste_action)

            menu.addSeparator()

            # Add element submenu
            add_menu = menu.addMenu("إضافة عنصر")

            for elem_type in ElementType:
                action = QAction(elem_type.value, self)
                pos = self.mapToScene(event.pos())
                action.triggered.connect(
                    lambda checked, t=elem_type, p=pos: self.add_element(t, x=p.x(), y=p.y())
                )
                add_menu.addAction(action)

        menu.exec_(event.globalPos())
