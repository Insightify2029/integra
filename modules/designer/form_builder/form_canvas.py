"""
Form Canvas
===========
Design canvas for form builder with drag & drop support.

Features:
- Grid-based layout
- Widget placement and alignment
- Selection and multi-selection
- Resize handles
- Form preview mode
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QLabel, QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QRadioButton, QDateEdit, QTimeEdit,
    QPushButton, QGroupBox, QFrame, QMenu, QAction
)
from PyQt5.QtCore import Qt, QRect, QPoint, QSize, pyqtSignal, QMimeData
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QDrag, QCursor

from core.logging import app_logger
from core.themes import get_current_palette


class WidgetType(Enum):
    """Form widget types."""
    LABEL = "label"
    TEXT_INPUT = "text_input"
    TEXT_AREA = "text_area"
    NUMBER_INPUT = "number_input"
    DECIMAL_INPUT = "decimal_input"
    COMBO_BOX = "combo_box"
    CHECK_BOX = "check_box"
    RADIO_BUTTON = "radio_button"
    DATE_PICKER = "date_picker"
    TIME_PICKER = "time_picker"
    BUTTON = "button"
    GROUP_BOX = "group_box"
    SEPARATOR = "separator"
    IMAGE = "image"
    TABLE = "table"


@dataclass
class WidgetStyle:
    """Widget visual style."""
    font_family: str = "Cairo"
    font_size: int = 12
    font_color: str = "#000000"
    background_color: str = "#ffffff"
    border_color: str = "#d1d5db"
    border_width: int = 1
    border_radius: int = 4
    padding: int = 8


@dataclass
class ValidationRule:
    """Validation rule for widget."""
    rule_type: str  # required, min, max, pattern, custom
    value: Any = None
    message: str = ""


@dataclass
class FormWidget:
    """Widget definition in form."""
    id: str
    widget_type: WidgetType
    x: int
    y: int
    width: int
    height: int
    label: str = ""
    placeholder: str = ""
    default_value: Any = None
    style: WidgetStyle = field(default_factory=WidgetStyle)
    properties: Dict[str, Any] = field(default_factory=dict)
    validation: List[ValidationRule] = field(default_factory=list)
    data_binding: Optional[str] = None  # table.column

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.widget_type.value,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "label": self.label,
            "placeholder": self.placeholder,
            "default_value": self.default_value,
            "style": {
                "font_family": self.style.font_family,
                "font_size": self.style.font_size,
                "font_color": self.style.font_color,
                "background_color": self.style.background_color,
                "border_color": self.style.border_color,
                "border_width": self.style.border_width,
                "border_radius": self.style.border_radius,
                "padding": self.style.padding
            },
            "properties": self.properties,
            "validation": [
                {"type": v.rule_type, "value": v.value, "message": v.message}
                for v in self.validation
            ],
            "data_binding": self.data_binding
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'FormWidget':
        """Create from dictionary."""
        style_data = data.get("style", {})
        style = WidgetStyle(
            font_family=style_data.get("font_family", "Cairo"),
            font_size=style_data.get("font_size", 12),
            font_color=style_data.get("font_color", "#000000"),
            background_color=style_data.get("background_color", "#ffffff"),
            border_color=style_data.get("border_color", "#d1d5db"),
            border_width=style_data.get("border_width", 1),
            border_radius=style_data.get("border_radius", 4),
            padding=style_data.get("padding", 8)
        )

        validation = [
            ValidationRule(
                rule_type=v.get("type", "required"),
                value=v.get("value"),
                message=v.get("message", "")
            )
            for v in data.get("validation", [])
        ]

        return cls(
            id=data.get("id", ""),
            widget_type=WidgetType(data.get("type", "label")),
            x=data.get("x", 0),
            y=data.get("y", 0),
            width=data.get("width", 200),
            height=data.get("height", 40),
            label=data.get("label", ""),
            placeholder=data.get("placeholder", ""),
            default_value=data.get("default_value"),
            style=style,
            properties=data.get("properties", {}),
            validation=validation,
            data_binding=data.get("data_binding")
        )


class DesignWidgetItem(QFrame):
    """Widget item on design canvas."""

    selected = pyqtSignal(object)  # FormWidget
    moved = pyqtSignal(object, int, int)  # FormWidget, new_x, new_y
    resized = pyqtSignal(object, int, int)  # FormWidget, new_width, new_height
    delete_requested = pyqtSignal(str)  # widget_id

    def __init__(self, widget: FormWidget, parent=None):
        super().__init__(parent)

        self.widget = widget
        self._selected = False
        self._dragging = False
        self._resizing = False
        self._resize_edge = None
        self._drag_start = QPoint()
        self._handle_size = 8

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup widget UI."""
        self.setGeometry(
            self.widget.x,
            self.widget.y,
            self.widget.width,
            self.widget.height
        )

        self.setMouseTracking(True)
        self.setAcceptDrops(False)

        # Create inner widget based on type
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        # Label if specified
        if self.widget.label and self.widget.widget_type != WidgetType.LABEL:
            label = QLabel(self.widget.label)
            label.setStyleSheet(f"color: {self.widget.style.font_color}; font-size: 11px;")
            layout.addWidget(label)

        # Create control based on type
        control = self._create_control()
        if control:
            layout.addWidget(control)

        self._update_style()

    def _create_control(self) -> Optional[QWidget]:
        """Create the actual control widget."""
        wt = self.widget.widget_type

        if wt == WidgetType.LABEL:
            ctrl = QLabel(self.widget.label or "نص")
            ctrl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            return ctrl

        elif wt == WidgetType.TEXT_INPUT:
            ctrl = QLineEdit()
            ctrl.setPlaceholderText(self.widget.placeholder or "أدخل النص...")
            ctrl.setEnabled(False)  # Disabled in design mode
            return ctrl

        elif wt == WidgetType.TEXT_AREA:
            ctrl = QTextEdit()
            ctrl.setPlaceholderText(self.widget.placeholder or "أدخل النص...")
            ctrl.setEnabled(False)
            return ctrl

        elif wt == WidgetType.NUMBER_INPUT:
            ctrl = QSpinBox()
            ctrl.setEnabled(False)
            return ctrl

        elif wt == WidgetType.DECIMAL_INPUT:
            ctrl = QDoubleSpinBox()
            ctrl.setEnabled(False)
            return ctrl

        elif wt == WidgetType.COMBO_BOX:
            ctrl = QComboBox()
            ctrl.addItems(self.widget.properties.get("items", ["عنصر 1", "عنصر 2"]))
            ctrl.setEnabled(False)
            return ctrl

        elif wt == WidgetType.CHECK_BOX:
            ctrl = QCheckBox(self.widget.label or "خيار")
            ctrl.setEnabled(False)
            return ctrl

        elif wt == WidgetType.RADIO_BUTTON:
            ctrl = QRadioButton(self.widget.label or "خيار")
            ctrl.setEnabled(False)
            return ctrl

        elif wt == WidgetType.DATE_PICKER:
            ctrl = QDateEdit()
            ctrl.setCalendarPopup(True)
            ctrl.setEnabled(False)
            return ctrl

        elif wt == WidgetType.TIME_PICKER:
            ctrl = QTimeEdit()
            ctrl.setEnabled(False)
            return ctrl

        elif wt == WidgetType.BUTTON:
            ctrl = QPushButton(self.widget.label or "زر")
            ctrl.setEnabled(False)
            return ctrl

        elif wt == WidgetType.GROUP_BOX:
            ctrl = QGroupBox(self.widget.label or "مجموعة")
            return ctrl

        elif wt == WidgetType.SEPARATOR:
            ctrl = QFrame()
            ctrl.setFrameShape(QFrame.HLine)
            ctrl.setFrameShadow(QFrame.Sunken)
            return ctrl

        return None

    def _update_style(self) -> None:
        """Update widget style."""
        style = self.widget.style

        if self._selected:
            p = get_current_palette()
            border = f"2px solid {p['primary']}"
        else:
            border = f"{style.border_width}px solid {style.border_color}"

        self.setStyleSheet(f"""
            DesignWidgetItem {{
                background: {style.background_color};
                border: {border};
                border-radius: {style.border_radius}px;
            }}
        """)

    def set_selected(self, selected: bool) -> None:
        """Set selection state."""
        self._selected = selected
        self._update_style()
        self.update()

    def paintEvent(self, event) -> None:
        """Custom painting."""
        super().paintEvent(event)

        if self._selected:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            # Draw resize handles
            p = get_current_palette()
            painter.setPen(QPen(QColor(p['primary']), 1))
            painter.setBrush(QBrush(QColor(p['bg_card'])))

            size = self._handle_size
            rect = self.rect()

            handles = [
                QRect(0, 0, size, size),
                QRect(rect.width() - size, 0, size, size),
                QRect(0, rect.height() - size, size, size),
                QRect(rect.width() - size, rect.height() - size, size, size),
            ]

            for handle in handles:
                painter.drawRect(handle)

    def _get_resize_edge(self, pos: QPoint) -> Optional[str]:
        """Get resize edge at position."""
        size = self._handle_size
        rect = self.rect()

        if QRect(rect.width() - size, rect.height() - size, size, size).contains(pos):
            return "bottom_right"
        if QRect(0, rect.height() - size, size, size).contains(pos):
            return "bottom_left"
        if QRect(rect.width() - size, 0, size, size).contains(pos):
            return "top_right"
        if QRect(0, 0, size, size).contains(pos):
            return "top_left"

        return None

    def mousePressEvent(self, event) -> None:
        """Handle mouse press."""
        if event.button() == Qt.LeftButton:
            self.selected.emit(self.widget)

            if self._selected:
                edge = self._get_resize_edge(event.pos())
                if edge:
                    self._resizing = True
                    self._resize_edge = edge
                else:
                    self._dragging = True

            self._drag_start = event.pos()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move."""
        if self._dragging:
            delta = event.pos() - self._drag_start
            new_pos = self.pos() + delta

            # Snap to grid
            grid = 10
            new_x = round(new_pos.x() / grid) * grid
            new_y = round(new_pos.y() / grid) * grid

            self.move(new_x, new_y)

            self.widget.x = new_x
            self.widget.y = new_y

            self.moved.emit(self.widget, new_x, new_y)

        elif self._resizing:
            delta = event.pos() - self._drag_start

            new_width = self.width()
            new_height = self.height()

            if "right" in self._resize_edge:
                new_width = max(50, self.width() + delta.x())
            if "bottom" in self._resize_edge:
                new_height = max(30, self.height() + delta.y())

            self.resize(new_width, new_height)
            self._drag_start = event.pos()

            self.widget.width = new_width
            self.widget.height = new_height

            self.resized.emit(self.widget, new_width, new_height)

        else:
            # Update cursor
            if self._selected:
                edge = self._get_resize_edge(event.pos())
                if edge:
                    self.setCursor(Qt.SizeFDiagCursor)
                else:
                    self.setCursor(Qt.SizeAllCursor)
            else:
                self.setCursor(Qt.ArrowCursor)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release."""
        self._dragging = False
        self._resizing = False
        self._resize_edge = None
        self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event) -> None:
        """Show context menu."""
        menu = QMenu(self)

        delete_action = QAction("حذف", self)
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.widget.id))
        menu.addAction(delete_action)

        menu.addSeparator()

        copy_action = QAction("نسخ", self)
        menu.addAction(copy_action)

        cut_action = QAction("قص", self)
        menu.addAction(cut_action)

        menu.exec_(event.globalPos())


class FormCanvas(QScrollArea):
    """
    Form design canvas.

    Signals:
        widget_selected: Emitted when a widget is selected
        widget_changed: Emitted when a widget is modified
        canvas_changed: Emitted when canvas changes
    """

    widget_selected = pyqtSignal(object)  # FormWidget or None
    widget_changed = pyqtSignal(object)  # FormWidget
    canvas_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._widgets: Dict[str, FormWidget] = {}
        self._widget_items: Dict[str, DesignWidgetItem] = {}
        self._selected_widget: Optional[str] = None
        self._next_widget_id = 1
        self._grid_size = 10
        self._show_grid = True

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup canvas UI."""
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Canvas widget
        self._canvas = QWidget()
        self._canvas.setMinimumSize(800, 600)
        self._canvas.setAcceptDrops(True)
        self._canvas.setMouseTracking(True)

        # Override canvas events
        self._canvas.paintEvent = self._paint_canvas
        self._canvas.dragEnterEvent = self._drag_enter
        self._canvas.dragMoveEvent = self._drag_move
        self._canvas.dropEvent = self._drop
        self._canvas.mousePressEvent = self._canvas_click

        self.setWidget(self._canvas)

        # Style
        p = get_current_palette()
        self._p = p
        self._canvas.setStyleSheet(f"background: {p['bg_main']};")
        self.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {p['border']};
            }}
        """)

    def _paint_canvas(self, event) -> None:
        """Paint canvas with grid."""
        painter = QPainter(self._canvas)

        # Background
        p = self._p
        painter.fillRect(self._canvas.rect(), QColor(p['bg_main']))

        # Form area
        form_rect = QRect(20, 20, 600, 500)
        painter.fillRect(form_rect, QColor(p['bg_card']))
        painter.setPen(QPen(QColor(p['border']), 1))
        painter.drawRect(form_rect)

        # Grid
        if self._show_grid:
            painter.setPen(QPen(QColor(p['border_light']), 1))

            for x in range(form_rect.left(), form_rect.right(), self._grid_size):
                painter.drawLine(x, form_rect.top(), x, form_rect.bottom())

            for y in range(form_rect.top(), form_rect.bottom(), self._grid_size):
                painter.drawLine(form_rect.left(), y, form_rect.right(), y)

    def _drag_enter(self, event) -> None:
        """Handle drag enter."""
        if event.mimeData().hasFormat("application/x-widget-type"):
            event.acceptProposedAction()

    def _drag_move(self, event) -> None:
        """Handle drag move."""
        if event.mimeData().hasFormat("application/x-widget-type"):
            event.acceptProposedAction()

    def _drop(self, event) -> None:
        """Handle widget drop."""
        if event.mimeData().hasFormat("application/x-widget-type"):
            widget_type_str = event.mimeData().data("application/x-widget-type").data().decode()

            try:
                widget_type = WidgetType(widget_type_str)
            except ValueError:
                widget_type = WidgetType.LABEL

            # Get drop position
            pos = event.pos()

            # Snap to grid
            x = round(pos.x() / self._grid_size) * self._grid_size
            y = round(pos.y() / self._grid_size) * self._grid_size

            # Add widget
            self.add_widget(widget_type, x, y)

            event.acceptProposedAction()

    def _canvas_click(self, event) -> None:
        """Handle canvas click (deselect)."""
        if event.button() == Qt.LeftButton:
            self._deselect_all()
            self.widget_selected.emit(None)

    def add_widget(
        self,
        widget_type: WidgetType,
        x: int = 50,
        y: int = 50,
        width: int = None,
        height: int = None,
        label: str = ""
    ) -> FormWidget:
        """
        Add new widget to canvas.

        Args:
            widget_type: Type of widget
            x: X position
            y: Y position
            width: Widget width
            height: Widget height
            label: Widget label

        Returns:
            Created FormWidget
        """
        # Generate unique ID
        widget_id = f"widget_{self._next_widget_id}"
        self._next_widget_id += 1

        # Default sizes
        default_sizes = {
            WidgetType.LABEL: (150, 30),
            WidgetType.TEXT_INPUT: (200, 35),
            WidgetType.TEXT_AREA: (200, 100),
            WidgetType.NUMBER_INPUT: (120, 35),
            WidgetType.COMBO_BOX: (200, 35),
            WidgetType.CHECK_BOX: (150, 30),
            WidgetType.RADIO_BUTTON: (150, 30),
            WidgetType.DATE_PICKER: (150, 35),
            WidgetType.TIME_PICKER: (120, 35),
            WidgetType.BUTTON: (100, 40),
            WidgetType.GROUP_BOX: (300, 200),
            WidgetType.SEPARATOR: (300, 10),
        }

        default_w, default_h = default_sizes.get(widget_type, (200, 40))

        # Default labels
        default_labels = {
            WidgetType.LABEL: "نص",
            WidgetType.TEXT_INPUT: "حقل نصي",
            WidgetType.TEXT_AREA: "منطقة نص",
            WidgetType.NUMBER_INPUT: "رقم",
            WidgetType.COMBO_BOX: "قائمة منسدلة",
            WidgetType.CHECK_BOX: "مربع اختيار",
            WidgetType.RADIO_BUTTON: "زر راديو",
            WidgetType.DATE_PICKER: "تاريخ",
            WidgetType.TIME_PICKER: "وقت",
            WidgetType.BUTTON: "زر",
            WidgetType.GROUP_BOX: "مجموعة",
        }

        # Create widget
        widget = FormWidget(
            id=widget_id,
            widget_type=widget_type,
            x=x,
            y=y,
            width=width or default_w,
            height=height or default_h,
            label=label or default_labels.get(widget_type, "")
        )

        # Create visual item
        item = DesignWidgetItem(widget, self._canvas)
        item.selected.connect(self._on_widget_selected)
        item.moved.connect(self._on_widget_moved)
        item.resized.connect(self._on_widget_resized)
        item.delete_requested.connect(self.remove_widget)
        item.show()

        # Store references
        self._widgets[widget_id] = widget
        self._widget_items[widget_id] = item

        self.canvas_changed.emit()

        app_logger.debug(f"Added form widget: {widget_id} ({widget_type.value})")
        return widget

    def remove_widget(self, widget_id: str) -> None:
        """Remove widget from canvas."""
        if widget_id in self._widget_items:
            self._widget_items[widget_id].deleteLater()
            del self._widget_items[widget_id]

        if widget_id in self._widgets:
            del self._widgets[widget_id]

        if self._selected_widget == widget_id:
            self._selected_widget = None
            self.widget_selected.emit(None)

        self.canvas_changed.emit()

    def get_widget(self, widget_id: str) -> Optional[FormWidget]:
        """Get widget by ID."""
        return self._widgets.get(widget_id)

    def get_selected_widget(self) -> Optional[FormWidget]:
        """Get currently selected widget."""
        if self._selected_widget:
            return self._widgets.get(self._selected_widget)
        return None

    def _on_widget_selected(self, widget: FormWidget) -> None:
        """Handle widget selection."""
        self._deselect_all()

        self._selected_widget = widget.id
        if widget.id in self._widget_items:
            self._widget_items[widget.id].set_selected(True)

        self.widget_selected.emit(widget)

    def _on_widget_moved(self, widget: FormWidget, x: int, y: int) -> None:
        """Handle widget move."""
        self.widget_changed.emit(widget)
        self.canvas_changed.emit()

    def _on_widget_resized(self, widget: FormWidget, width: int, height: int) -> None:
        """Handle widget resize."""
        self.widget_changed.emit(widget)
        self.canvas_changed.emit()

    def _deselect_all(self) -> None:
        """Deselect all widgets."""
        for item in self._widget_items.values():
            item.set_selected(False)
        self._selected_widget = None

    def update_widget(self, widget: FormWidget) -> None:
        """Update widget appearance."""
        if widget.id in self._widget_items:
            item = self._widget_items[widget.id]
            item.setGeometry(widget.x, widget.y, widget.width, widget.height)
            item._update_style()
            item.update()

        self.widget_changed.emit(widget)
        self.canvas_changed.emit()

    def set_grid_visible(self, visible: bool) -> None:
        """Show/hide grid."""
        self._show_grid = visible
        self._canvas.update()

    def clear(self) -> None:
        """Clear all widgets."""
        for widget_id in list(self._widget_items.keys()):
            self.remove_widget(widget_id)
        self._next_widget_id = 1

    def to_dict(self) -> Dict:
        """Export canvas to dictionary."""
        return {
            "canvas_width": self._canvas.width(),
            "canvas_height": self._canvas.height(),
            "widgets": [w.to_dict() for w in self._widgets.values()]
        }

    def from_dict(self, data: Dict) -> None:
        """Import canvas from dictionary."""
        self.clear()

        # Set canvas size
        self._canvas.setMinimumSize(
            data.get("canvas_width", 800),
            data.get("canvas_height", 600)
        )

        # Load widgets
        for widget_data in data.get("widgets", []):
            widget = FormWidget.from_dict(widget_data)
            self._widgets[widget.id] = widget

            item = DesignWidgetItem(widget, self._canvas)
            item.selected.connect(self._on_widget_selected)
            item.moved.connect(self._on_widget_moved)
            item.resized.connect(self._on_widget_resized)
            item.delete_requested.connect(self.remove_widget)
            item.show()

            self._widget_items[widget.id] = item

            # Update next ID
            try:
                num = int(widget.id.split("_")[-1])
                self._next_widget_id = max(self._next_widget_id, num + 1)
            except ValueError:
                pass

        self.canvas_changed.emit()
