"""
Form Canvas (Enhanced - Phase 2)
=================================
Design canvas for form builder with advanced features.

Phase 2 enhancements:
- QUndoStack for all design operations
- Multi-select with rubber band
- Alignment guides and smart snapping
- Zoom in/out
- Copy/Paste support
"""

import copy
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Set, Tuple
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QLabel, QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QRadioButton, QDateEdit, QTimeEdit,
    QPushButton, QGroupBox, QFrame, QMenu, QAction,
    QRubberBand, QApplication, QUndoStack, QUndoCommand
)
from PyQt5.QtCore import (
    Qt, QRect, QPoint, QSize, pyqtSignal, QMimeData
)
from PyQt5.QtGui import (
    QPainter, QPen, QBrush, QColor, QDrag, QCursor,
    QKeySequence
)

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

        try:
            wt = WidgetType(data.get("type", "label"))
        except ValueError:
            app_logger.warning(f"Unknown widget type '{data.get('type')}', defaulting to LABEL")
            wt = WidgetType.LABEL

        return cls(
            id=data.get("id", ""),
            widget_type=wt,
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

    def clone(self) -> 'FormWidget':
        """Create a deep copy of this widget."""
        return FormWidget(
            id=self.id,
            widget_type=self.widget_type,
            x=self.x,
            y=self.y,
            width=self.width,
            height=self.height,
            label=self.label,
            placeholder=self.placeholder,
            default_value=self.default_value,
            style=WidgetStyle(
                font_family=self.style.font_family,
                font_size=self.style.font_size,
                font_color=self.style.font_color,
                background_color=self.style.background_color,
                border_color=self.style.border_color,
                border_width=self.style.border_width,
                border_radius=self.style.border_radius,
                padding=self.style.padding
            ),
            properties=dict(self.properties),
            validation=[
                ValidationRule(v.rule_type, v.value, v.message)
                for v in self.validation
            ],
            data_binding=self.data_binding
        )


# ---------------------------------------------------------------------------
# Undo Commands
# ---------------------------------------------------------------------------

class AddWidgetCommand(QUndoCommand):
    """Undo command for adding a widget."""

    def __init__(self, canvas: 'FormCanvas', widget: FormWidget, description: str = ""):
        super().__init__(description or f"Add {widget.widget_type.value}")
        self._canvas = canvas
        self._widget_data = widget.to_dict()
        self._widget_id = widget.id

    def redo(self) -> None:
        widget = FormWidget.from_dict(self._widget_data)
        self._canvas._add_widget_internal(widget)

    def undo(self) -> None:
        self._canvas._remove_widget_internal(self._widget_id)


class RemoveWidgetCommand(QUndoCommand):
    """Undo command for removing a widget."""

    def __init__(self, canvas: 'FormCanvas', widget: FormWidget, description: str = ""):
        super().__init__(description or f"Remove {widget.widget_type.value}")
        self._canvas = canvas
        self._widget_data = widget.to_dict()
        self._widget_id = widget.id

    def redo(self) -> None:
        self._canvas._remove_widget_internal(self._widget_id)

    def undo(self) -> None:
        widget = FormWidget.from_dict(self._widget_data)
        self._canvas._add_widget_internal(widget)


class MoveWidgetCommand(QUndoCommand):
    """Undo command for moving a widget."""

    def __init__(
        self, canvas: 'FormCanvas', widget_id: str,
        old_x: int, old_y: int, new_x: int, new_y: int,
        description: str = ""
    ):
        super().__init__(description or "Move widget")
        self._canvas = canvas
        self._widget_id = widget_id
        self._old_x = old_x
        self._old_y = old_y
        self._new_x = new_x
        self._new_y = new_y

    def redo(self) -> None:
        self._canvas._move_widget_internal(self._widget_id, self._new_x, self._new_y)

    def undo(self) -> None:
        self._canvas._move_widget_internal(self._widget_id, self._old_x, self._old_y)


class ResizeWidgetCommand(QUndoCommand):
    """Undo command for resizing a widget."""

    def __init__(
        self, canvas: 'FormCanvas', widget_id: str,
        old_w: int, old_h: int, new_w: int, new_h: int,
        description: str = ""
    ):
        super().__init__(description or "Resize widget")
        self._canvas = canvas
        self._widget_id = widget_id
        self._old_w = old_w
        self._old_h = old_h
        self._new_w = new_w
        self._new_h = new_h

    def redo(self) -> None:
        self._canvas._resize_widget_internal(self._widget_id, self._new_w, self._new_h)

    def undo(self) -> None:
        self._canvas._resize_widget_internal(self._widget_id, self._old_w, self._old_h)


class ChangePropertyCommand(QUndoCommand):
    """Undo command for changing a widget property."""

    def __init__(
        self, canvas: 'FormCanvas', widget_id: str,
        old_data: Dict, new_data: Dict,
        description: str = ""
    ):
        super().__init__(description or "Change property")
        self._canvas = canvas
        self._widget_id = widget_id
        self._old_data = old_data
        self._new_data = new_data

    def redo(self) -> None:
        self._canvas._apply_widget_data(self._widget_id, self._new_data)

    def undo(self) -> None:
        self._canvas._apply_widget_data(self._widget_id, self._old_data)


# ---------------------------------------------------------------------------
# Design Widget Item
# ---------------------------------------------------------------------------

class DesignWidgetItem(QFrame):
    """Widget item on design canvas."""

    selected = pyqtSignal(object)  # FormWidget
    moved = pyqtSignal(object, int, int)  # FormWidget, new_x, new_y
    resized = pyqtSignal(object, int, int)  # FormWidget, new_width, new_height
    delete_requested = pyqtSignal(str)  # widget_id
    move_started = pyqtSignal(str, int, int)  # widget_id, start_x, start_y
    move_finished = pyqtSignal(str, int, int)  # widget_id, end_x, end_y
    resize_started = pyqtSignal(str, int, int)  # widget_id, start_w, start_h
    resize_finished = pyqtSignal(str, int, int)  # widget_id, end_w, end_h
    copy_requested = pyqtSignal(str)  # widget_id

    def __init__(self, widget: FormWidget, parent=None):
        super().__init__(parent)

        self.widget = widget
        self._selected = False
        self._dragging = False
        self._resizing = False
        self._resize_edge = None
        self._drag_start = QPoint()
        self._handle_size = 8
        self._start_x = 0
        self._start_y = 0
        self._start_w = 0
        self._start_h = 0
        self._zoom = 1.0

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
            ctrl.setEnabled(False)
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

            p = get_current_palette()
            painter.setPen(QPen(QColor(p['primary']), 1))
            painter.setBrush(QBrush(QColor(p['bg_card'])))

            size = self._handle_size
            rect = self.rect()

            # 8 resize handles
            handles = [
                QRect(0, 0, size, size),                                        # top-left
                QRect(int(rect.width() / 2 - size / 2), 0, size, size),         # top-center
                QRect(rect.width() - size, 0, size, size),                      # top-right
                QRect(0, int(rect.height() / 2 - size / 2), size, size),        # mid-left
                QRect(rect.width() - size, int(rect.height() / 2 - size / 2), size, size),  # mid-right
                QRect(0, rect.height() - size, size, size),                     # bottom-left
                QRect(int(rect.width() / 2 - size / 2), rect.height() - size, size, size),  # bottom-center
                QRect(rect.width() - size, rect.height() - size, size, size),   # bottom-right
            ]

            for handle in handles:
                painter.drawRect(handle)

    def _get_resize_edge(self, pos: QPoint) -> Optional[str]:
        """Get resize edge at position."""
        size = self._handle_size
        rect = self.rect()
        mid_x = int(rect.width() / 2 - size / 2)
        mid_y = int(rect.height() / 2 - size / 2)

        if QRect(rect.width() - size, rect.height() - size, size, size).contains(pos):
            return "bottom_right"
        if QRect(0, rect.height() - size, size, size).contains(pos):
            return "bottom_left"
        if QRect(rect.width() - size, 0, size, size).contains(pos):
            return "top_right"
        if QRect(0, 0, size, size).contains(pos):
            return "top_left"
        if QRect(mid_x, 0, size, size).contains(pos):
            return "top"
        if QRect(mid_x, rect.height() - size, size, size).contains(pos):
            return "bottom"
        if QRect(0, mid_y, size, size).contains(pos):
            return "left"
        if QRect(rect.width() - size, mid_y, size, size).contains(pos):
            return "right"

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
                    self._start_w = self.widget.width
                    self._start_h = self.widget.height
                    self.resize_started.emit(self.widget.id, self.widget.width, self.widget.height)
                else:
                    self._dragging = True
                    self._start_x = self.widget.x
                    self._start_y = self.widget.y
                    self.move_started.emit(self.widget.id, self.widget.x, self.widget.y)

            self._drag_start = event.pos()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move."""
        if self._dragging:
            delta = event.pos() - self._drag_start
            new_pos = self.pos() + delta

            # Snap to visual grid (scaled by zoom)
            visual_grid = max(1, int(10 * self._zoom))
            new_x = round(new_pos.x() / visual_grid) * visual_grid
            new_y = round(new_pos.y() / visual_grid) * visual_grid

            self.move(new_x, new_y)

            # Store logical coordinates (divide by zoom)
            zoom = self._zoom if self._zoom > 0 else 1.0
            self.widget.x = int(new_x / zoom)
            self.widget.y = int(new_y / zoom)

            self.moved.emit(self.widget, self.widget.x, self.widget.y)

        elif self._resizing:
            delta = event.pos() - self._drag_start

            new_width = self.width()
            new_height = self.height()

            if self._resize_edge in ("right", "top_right", "bottom_right"):
                new_width = max(50, self.width() + delta.x())
            if self._resize_edge in ("left", "top_left", "bottom_left"):
                new_width = max(50, self.width() - delta.x())
            if self._resize_edge in ("bottom", "bottom_left", "bottom_right"):
                new_height = max(30, self.height() + delta.y())
            if self._resize_edge in ("top", "top_left", "top_right"):
                new_height = max(30, self.height() - delta.y())

            self.resize(new_width, new_height)
            self._drag_start = event.pos()

            # Store logical dimensions (divide by zoom)
            zoom = self._zoom if self._zoom > 0 else 1.0
            self.widget.width = int(new_width / zoom)
            self.widget.height = int(new_height / zoom)

            self.resized.emit(self.widget, self.widget.width, self.widget.height)

        else:
            # Update cursor
            if self._selected:
                edge = self._get_resize_edge(event.pos())
                if edge in ("top_left", "bottom_right"):
                    self.setCursor(Qt.SizeFDiagCursor)
                elif edge in ("top_right", "bottom_left"):
                    self.setCursor(Qt.SizeBDiagCursor)
                elif edge in ("top", "bottom"):
                    self.setCursor(Qt.SizeVerCursor)
                elif edge in ("left", "right"):
                    self.setCursor(Qt.SizeHorCursor)
                elif edge:
                    self.setCursor(Qt.SizeFDiagCursor)
                else:
                    self.setCursor(Qt.SizeAllCursor)
            else:
                self.setCursor(Qt.ArrowCursor)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release."""
        if self._dragging:
            self._dragging = False
            self.move_finished.emit(self.widget.id, self.widget.x, self.widget.y)

        if self._resizing:
            self._resizing = False
            self.resize_finished.emit(self.widget.id, self.widget.width, self.widget.height)

        self._resize_edge = None
        self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event) -> None:
        """Show context menu."""
        menu = QMenu(self)

        copy_action = QAction("نسخ", self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(lambda: self.copy_requested.emit(self.widget.id))
        menu.addAction(copy_action)

        menu.addSeparator()

        delete_action = QAction("حذف", self)
        delete_action.setShortcut(QKeySequence.Delete)
        delete_action.triggered.connect(lambda: self.delete_requested.emit(self.widget.id))
        menu.addAction(delete_action)

        menu.exec_(event.globalPos())


# ---------------------------------------------------------------------------
# Form Canvas
# ---------------------------------------------------------------------------

class FormCanvas(QScrollArea):
    """
    Form design canvas with advanced features.

    Phase 2 features:
    - QUndoStack for undo/redo
    - Multi-select with rubber band
    - Alignment guides
    - Zoom
    - Copy/Paste

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
        self._selected_widgets: Set[str] = set()
        self._next_widget_id = 1
        self._grid_size = 10
        self._show_grid = True

        # Undo/Redo
        self._undo_stack = QUndoStack(self)

        # Zoom
        self._zoom_level = 1.0
        self._min_zoom = 0.5
        self._max_zoom = 2.0

        # Rubber band selection
        self._rubber_band: Optional[QRubberBand] = None
        self._rubber_origin = QPoint()
        self._rubber_active = False

        # Alignment guides
        self._snap_threshold = 8
        self._guide_lines: List[Tuple[QPoint, QPoint]] = []

        # Copy/Paste clipboard
        self._clipboard: List[Dict] = []

        # Track move/resize for undo
        self._pending_move: Optional[Tuple[str, int, int]] = None  # widget_id, start_x, start_y
        self._pending_resize: Optional[Tuple[str, int, int]] = None  # widget_id, start_w, start_h

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
        self._canvas.mousePressEvent = self._canvas_mouse_press
        self._canvas.mouseMoveEvent = self._canvas_mouse_move
        self._canvas.mouseReleaseEvent = self._canvas_mouse_release

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

    # -----------------------------------------------------------------------
    # Undo/Redo access
    # -----------------------------------------------------------------------

    def get_undo_stack(self) -> QUndoStack:
        """Get the undo stack for external wiring (menu actions)."""
        return self._undo_stack

    # -----------------------------------------------------------------------
    # Zoom
    # -----------------------------------------------------------------------

    @property
    def zoom_level(self) -> float:
        return self._zoom_level

    def set_zoom(self, level: float) -> None:
        """Set zoom level (0.5 - 2.0)."""
        level = max(self._min_zoom, min(self._max_zoom, level))
        self._zoom_level = level

        # Scale the canvas
        new_w = int(800 * level)
        new_h = int(600 * level)
        self._canvas.setMinimumSize(new_w, new_h)

        # Scale all widget positions and sizes
        for widget_id, widget in self._widgets.items():
            item = self._widget_items.get(widget_id)
            if item:
                item._zoom = level
                item.setGeometry(
                    int(widget.x * level),
                    int(widget.y * level),
                    int(widget.width * level),
                    int(widget.height * level)
                )

        self._canvas.update()
        app_logger.debug(f"Canvas zoom set to {level:.0%}")

    def zoom_in(self) -> None:
        """Zoom in by 10%."""
        self.set_zoom(self._zoom_level + 0.1)

    def zoom_out(self) -> None:
        """Zoom out by 10%."""
        self.set_zoom(self._zoom_level - 0.1)

    def zoom_reset(self) -> None:
        """Reset zoom to 100%."""
        self.set_zoom(1.0)

    # -----------------------------------------------------------------------
    # Multi-select
    # -----------------------------------------------------------------------

    def get_selected_widgets(self) -> List[FormWidget]:
        """Get all selected widgets."""
        return [
            self._widgets[wid]
            for wid in self._selected_widgets
            if wid in self._widgets
        ]

    def select_all(self) -> None:
        """Select all widgets."""
        self._selected_widgets = set(self._widgets.keys())
        for item in self._widget_items.values():
            item.set_selected(True)
        self.canvas_changed.emit()

    # -----------------------------------------------------------------------
    # Copy/Paste
    # -----------------------------------------------------------------------

    def copy_selected(self) -> None:
        """Copy selected widgets to clipboard."""
        self._clipboard.clear()
        for wid in self._selected_widgets:
            widget = self._widgets.get(wid)
            if widget:
                self._clipboard.append(widget.to_dict())

        if self._clipboard:
            app_logger.debug(f"Copied {len(self._clipboard)} widget(s)")

    def paste(self) -> None:
        """Paste widgets from clipboard with offset."""
        if not self._clipboard:
            return

        offset = 20
        for data in self._clipboard:
            # Create new widget with offset
            new_data = dict(data)
            new_id = f"widget_{self._next_widget_id}"
            self._next_widget_id += 1

            new_data["id"] = new_id
            new_data["x"] = data.get("x", 50) + offset
            new_data["y"] = data.get("y", 50) + offset

            widget = FormWidget.from_dict(new_data)
            cmd = AddWidgetCommand(self, widget, f"Paste {widget.widget_type.value}")
            self._undo_stack.push(cmd)

        app_logger.debug(f"Pasted {len(self._clipboard)} widget(s)")

    def cut_selected(self) -> None:
        """Cut selected widgets (copy then delete)."""
        self.copy_selected()
        self.delete_selected()

    def delete_selected(self) -> None:
        """Delete all selected widgets."""
        for wid in list(self._selected_widgets):
            widget = self._widgets.get(wid)
            if widget:
                cmd = RemoveWidgetCommand(self, widget)
                self._undo_stack.push(cmd)

        self._selected_widgets.clear()
        self.widget_selected.emit(None)

    # -----------------------------------------------------------------------
    # Alignment
    # -----------------------------------------------------------------------

    def align_left(self) -> None:
        """Align selected widgets to leftmost edge."""
        widgets = self.get_selected_widgets()
        if len(widgets) < 2:
            return
        min_x = min(w.x for w in widgets)
        for w in widgets:
            if w.x != min_x:
                cmd = MoveWidgetCommand(self, w.id, w.x, w.y, min_x, w.y, "Align left")
                self._undo_stack.push(cmd)

    def align_right(self) -> None:
        """Align selected widgets to rightmost edge."""
        widgets = self.get_selected_widgets()
        if len(widgets) < 2:
            return
        max_right = max(w.x + w.width for w in widgets)
        for w in widgets:
            new_x = max_right - w.width
            if w.x != new_x:
                cmd = MoveWidgetCommand(self, w.id, w.x, w.y, new_x, w.y, "Align right")
                self._undo_stack.push(cmd)

    def align_top(self) -> None:
        """Align selected widgets to topmost edge."""
        widgets = self.get_selected_widgets()
        if len(widgets) < 2:
            return
        min_y = min(w.y for w in widgets)
        for w in widgets:
            if w.y != min_y:
                cmd = MoveWidgetCommand(self, w.id, w.x, w.y, w.x, min_y, "Align top")
                self._undo_stack.push(cmd)

    def align_bottom(self) -> None:
        """Align selected widgets to bottommost edge."""
        widgets = self.get_selected_widgets()
        if len(widgets) < 2:
            return
        max_bottom = max(w.y + w.height for w in widgets)
        for w in widgets:
            new_y = max_bottom - w.height
            if w.y != new_y:
                cmd = MoveWidgetCommand(self, w.id, w.x, w.y, w.x, new_y, "Align bottom")
                self._undo_stack.push(cmd)

    def distribute_horizontal(self) -> None:
        """Distribute selected widgets evenly horizontally."""
        widgets = self.get_selected_widgets()
        if len(widgets) < 3:
            return
        widgets.sort(key=lambda w: w.x)
        total_space = widgets[-1].x + widgets[-1].width - widgets[0].x
        total_widget_w = sum(w.width for w in widgets)
        gap = (total_space - total_widget_w) / (len(widgets) - 1) if len(widgets) > 1 else 0
        current_x = widgets[0].x
        for w in widgets:
            new_x = int(current_x)
            if w.x != new_x:
                cmd = MoveWidgetCommand(self, w.id, w.x, w.y, new_x, w.y, "Distribute horizontal")
                self._undo_stack.push(cmd)
            current_x += w.width + gap

    def distribute_vertical(self) -> None:
        """Distribute selected widgets evenly vertically."""
        widgets = self.get_selected_widgets()
        if len(widgets) < 3:
            return
        widgets.sort(key=lambda w: w.y)
        total_space = widgets[-1].y + widgets[-1].height - widgets[0].y
        total_widget_h = sum(w.height for w in widgets)
        gap = (total_space - total_widget_h) / (len(widgets) - 1) if len(widgets) > 1 else 0
        current_y = widgets[0].y
        for w in widgets:
            new_y = int(current_y)
            if w.y != new_y:
                cmd = MoveWidgetCommand(self, w.id, w.x, w.y, w.x, new_y, "Distribute vertical")
                self._undo_stack.push(cmd)
            current_y += w.height + gap

    # -----------------------------------------------------------------------
    # Snap guides
    # -----------------------------------------------------------------------

    def _compute_snap_guides(self, moving_widget_id: str, x: int, y: int, w: int, h: int) -> Tuple[int, int]:
        """Compute alignment guides and snapped position (all in logical coords)."""
        self._guide_lines.clear()

        snapped_x = x
        snapped_y = y
        z = self._zoom_level  # For converting guide lines to screen coords

        for wid, other in self._widgets.items():
            if wid == moving_widget_id:
                continue

            ox, oy, ow, oh = other.x, other.y, other.width, other.height

            # Horizontal alignment: left edges
            if abs(x - ox) < self._snap_threshold:
                snapped_x = ox
                gx = int(ox * z)
                self._guide_lines.append((QPoint(gx, 0), QPoint(gx, self._canvas.height())))

            # Right edges
            if abs(x + w - (ox + ow)) < self._snap_threshold:
                snapped_x = ox + ow - w
                gx = int((ox + ow) * z)
                self._guide_lines.append((QPoint(gx, 0), QPoint(gx, self._canvas.height())))

            # Left to right
            if abs(x - (ox + ow)) < self._snap_threshold:
                snapped_x = ox + ow
                gx = int((ox + ow) * z)
                self._guide_lines.append((QPoint(gx, 0), QPoint(gx, self._canvas.height())))

            # Vertical alignment: top edges
            if abs(y - oy) < self._snap_threshold:
                snapped_y = oy
                gy = int(oy * z)
                self._guide_lines.append((QPoint(0, gy), QPoint(self._canvas.width(), gy)))

            # Bottom edges
            if abs(y + h - (oy + oh)) < self._snap_threshold:
                snapped_y = oy + oh - h
                gy = int((oy + oh) * z)
                self._guide_lines.append((QPoint(0, gy), QPoint(self._canvas.width(), gy)))

            # Center horizontal
            cx = x + w // 2
            ocx = ox + ow // 2
            if abs(cx - ocx) < self._snap_threshold:
                snapped_x = ocx - w // 2
                gx = int(ocx * z)
                self._guide_lines.append((QPoint(gx, 0), QPoint(gx, self._canvas.height())))

            # Center vertical
            cy = y + h // 2
            ocy = oy + oh // 2
            if abs(cy - ocy) < self._snap_threshold:
                snapped_y = ocy - h // 2
                gy = int(ocy * z)
                self._guide_lines.append((QPoint(0, gy), QPoint(self._canvas.width(), gy)))

        return snapped_x, snapped_y

    # -----------------------------------------------------------------------
    # Canvas painting
    # -----------------------------------------------------------------------

    def _paint_canvas(self, event) -> None:
        """Paint canvas with grid and alignment guides."""
        painter = QPainter(self._canvas)

        # Background
        p = self._p
        painter.fillRect(self._canvas.rect(), QColor(p['bg_main']))

        # Form area
        form_w = int(600 * self._zoom_level)
        form_h = int(500 * self._zoom_level)
        form_rect = QRect(20, 20, form_w, form_h)
        painter.fillRect(form_rect, QColor(p['bg_card']))
        painter.setPen(QPen(QColor(p['border']), 1))
        painter.drawRect(form_rect)

        # Grid
        if self._show_grid:
            grid_step = max(1, int(self._grid_size * self._zoom_level))
            painter.setPen(QPen(QColor(p['border_light']), 1))

            for x in range(form_rect.left(), form_rect.right(), grid_step):
                painter.drawLine(x, form_rect.top(), x, form_rect.bottom())

            for y in range(form_rect.top(), form_rect.bottom(), grid_step):
                painter.drawLine(form_rect.left(), y, form_rect.right(), y)

        # Alignment guide lines
        if self._guide_lines:
            guide_pen = QPen(QColor(p['primary']), 1, Qt.DashLine)
            painter.setPen(guide_pen)
            for p1, p2 in self._guide_lines:
                painter.drawLine(p1, p2)

        # Zoom indicator
        if abs(self._zoom_level - 1.0) > 0.01:
            painter.setPen(QPen(QColor(p['text_muted']), 1))
            painter.drawText(
                self._canvas.rect().adjusted(0, 0, -10, -10),
                Qt.AlignBottom | Qt.AlignRight,
                f"{self._zoom_level:.0%}"
            )

    # -----------------------------------------------------------------------
    # Drag & drop from toolbox
    # -----------------------------------------------------------------------

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

            pos = event.pos()
            # Convert screen position to logical, then snap to grid
            zoom = self._zoom_level if self._zoom_level > 0 else 1.0
            logical_x = pos.x() / zoom
            logical_y = pos.y() / zoom
            x = round(logical_x / self._grid_size) * self._grid_size
            y = round(logical_y / self._grid_size) * self._grid_size

            self.add_widget(widget_type, x, y)
            event.acceptProposedAction()

    # -----------------------------------------------------------------------
    # Mouse events on canvas (rubber band, deselect)
    # -----------------------------------------------------------------------

    def _canvas_mouse_press(self, event) -> None:
        """Handle canvas click for rubber band or deselect."""
        if event.button() == Qt.LeftButton:
            # Start rubber band selection
            self._rubber_origin = event.pos()
            self._rubber_active = True

            if self._rubber_band is None:
                self._rubber_band = QRubberBand(QRubberBand.Rectangle, self._canvas)
            self._rubber_band.setGeometry(QRect(self._rubber_origin, QSize()))
            self._rubber_band.show()

            # Deselect unless Ctrl held
            if not (event.modifiers() & Qt.ControlModifier):
                self._deselect_all()
                self.widget_selected.emit(None)

    def _canvas_mouse_move(self, event) -> None:
        """Handle rubber band dragging."""
        if self._rubber_active and self._rubber_band:
            rect = QRect(self._rubber_origin, event.pos()).normalized()
            self._rubber_band.setGeometry(rect)

    def _canvas_mouse_release(self, event) -> None:
        """Finish rubber band selection."""
        if self._rubber_active and self._rubber_band:
            self._rubber_band.hide()
            self._rubber_active = False

            select_rect = QRect(self._rubber_origin, event.pos()).normalized()

            # Only select if dragged area is meaningful
            if select_rect.width() > 5 or select_rect.height() > 5:
                for wid, item in self._widget_items.items():
                    item_rect = item.geometry()
                    if select_rect.intersects(item_rect):
                        self._selected_widgets.add(wid)
                        item.set_selected(True)

                selected = self.get_selected_widgets()
                if len(selected) == 1:
                    self.widget_selected.emit(selected[0])
                elif len(selected) > 1:
                    self.widget_selected.emit(selected[0])

    # -----------------------------------------------------------------------
    # Widget management (public)
    # -----------------------------------------------------------------------

    def add_widget(
        self,
        widget_type: WidgetType,
        x: int = 50,
        y: int = 50,
        width: Optional[int] = None,
        height: Optional[int] = None,
        label: str = ""
    ) -> FormWidget:
        """Add new widget to canvas (with undo support)."""
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

        widget = FormWidget(
            id=widget_id,
            widget_type=widget_type,
            x=x,
            y=y,
            width=width or default_w,
            height=height or default_h,
            label=label or default_labels.get(widget_type, "")
        )

        cmd = AddWidgetCommand(self, widget)
        self._undo_stack.push(cmd)

        return widget

    def remove_widget(self, widget_id: str) -> None:
        """Remove widget with undo support."""
        widget = self._widgets.get(widget_id)
        if widget:
            cmd = RemoveWidgetCommand(self, widget)
            self._undo_stack.push(cmd)

    def get_widget(self, widget_id: str) -> Optional[FormWidget]:
        """Get widget by ID."""
        return self._widgets.get(widget_id)

    def get_selected_widget(self) -> Optional[FormWidget]:
        """Get currently selected widget (first if multi-select)."""
        if self._selected_widgets:
            first_id = next(iter(self._selected_widgets))
            return self._widgets.get(first_id)
        return None

    def update_widget(self, widget: FormWidget) -> None:
        """Update widget appearance (with undo support for property changes)."""
        if widget.id in self._widget_items:
            item = self._widget_items[widget.id]
            z = self._zoom_level
            item.setGeometry(
                int(widget.x * z), int(widget.y * z),
                int(widget.width * z), int(widget.height * z)
            )
            item._update_style()
            item.update()

        self.widget_changed.emit(widget)
        self.canvas_changed.emit()

    def update_widget_with_undo(self, widget: FormWidget, old_data: Dict) -> None:
        """Update widget with undo support for property changes."""
        new_data = widget.to_dict()
        cmd = ChangePropertyCommand(self, widget.id, old_data, new_data, "Change property")
        self._undo_stack.push(cmd)

    # -----------------------------------------------------------------------
    # Widget management (internal - called by undo commands)
    # -----------------------------------------------------------------------

    def _add_widget_internal(self, widget: FormWidget) -> None:
        """Add widget without undo (used by undo commands)."""
        item = DesignWidgetItem(widget, self._canvas)
        item.selected.connect(self._on_widget_selected)
        item.moved.connect(self._on_widget_moved)
        item.resized.connect(self._on_widget_resized)
        item.delete_requested.connect(self.remove_widget)
        item.copy_requested.connect(self._on_copy_requested)
        item.move_started.connect(self._on_move_started)
        item.move_finished.connect(self._on_move_finished)
        item.resize_started.connect(self._on_resize_started)
        item.resize_finished.connect(self._on_resize_finished)

        # Apply current zoom level
        item._zoom = self._zoom_level
        if self._zoom_level != 1.0:
            item.setGeometry(
                int(widget.x * self._zoom_level),
                int(widget.y * self._zoom_level),
                int(widget.width * self._zoom_level),
                int(widget.height * self._zoom_level)
            )
        item.show()

        self._widgets[widget.id] = widget
        self._widget_items[widget.id] = item

        # Update next ID
        try:
            num = int(widget.id.split("_")[-1])
            self._next_widget_id = max(self._next_widget_id, num + 1)
        except (ValueError, IndexError) as e:
            app_logger.debug(f"Could not parse widget ID number from '{widget.id}': {e}")

        self.canvas_changed.emit()
        app_logger.debug(f"Added form widget: {widget.id} ({widget.widget_type.value})")

    def _remove_widget_internal(self, widget_id: str) -> None:
        """Remove widget without undo (used by undo commands)."""
        if widget_id in self._widget_items:
            self._widget_items[widget_id].deleteLater()
            del self._widget_items[widget_id]

        if widget_id in self._widgets:
            del self._widgets[widget_id]

        self._selected_widgets.discard(widget_id)

        if not self._selected_widgets:
            self.widget_selected.emit(None)

        self.canvas_changed.emit()

    def _move_widget_internal(self, widget_id: str, x: int, y: int) -> None:
        """Move widget without undo (used by undo commands)."""
        widget = self._widgets.get(widget_id)
        item = self._widget_items.get(widget_id)
        if widget and item:
            widget.x = x
            widget.y = y
            item.move(int(x * self._zoom_level), int(y * self._zoom_level))
            item.widget.x = x
            item.widget.y = y
            self.widget_changed.emit(widget)
            self.canvas_changed.emit()

    def _resize_widget_internal(self, widget_id: str, w: int, h: int) -> None:
        """Resize widget without undo (used by undo commands)."""
        widget = self._widgets.get(widget_id)
        item = self._widget_items.get(widget_id)
        if widget and item:
            widget.width = w
            widget.height = h
            item.resize(int(w * self._zoom_level), int(h * self._zoom_level))
            item.widget.width = w
            item.widget.height = h
            self.widget_changed.emit(widget)
            self.canvas_changed.emit()

    def _apply_widget_data(self, widget_id: str, data: Dict) -> None:
        """Apply full widget data from undo command."""
        widget = self._widgets.get(widget_id)
        if not widget:
            return

        widget.label = data.get("label", widget.label)
        widget.placeholder = data.get("placeholder", widget.placeholder)
        widget.x = data.get("x", widget.x)
        widget.y = data.get("y", widget.y)
        widget.width = data.get("width", widget.width)
        widget.height = data.get("height", widget.height)
        widget.data_binding = data.get("data_binding", widget.data_binding)

        style_data = data.get("style", {})
        if style_data:
            widget.style.font_family = style_data.get("font_family", widget.style.font_family)
            widget.style.font_size = style_data.get("font_size", widget.style.font_size)
            widget.style.font_color = style_data.get("font_color", widget.style.font_color)
            widget.style.background_color = style_data.get("background_color", widget.style.background_color)
            widget.style.border_color = style_data.get("border_color", widget.style.border_color)

        props = data.get("properties", {})
        if props:
            widget.properties.update(props)

        validation_data = data.get("validation", [])
        widget.validation = [
            ValidationRule(v.get("type", "required"), v.get("value"), v.get("message", ""))
            for v in validation_data
        ]

        item = self._widget_items.get(widget_id)
        if item:
            z = self._zoom_level
            item.setGeometry(
                int(widget.x * z), int(widget.y * z),
                int(widget.width * z), int(widget.height * z)
            )
            item._update_style()
            item.update()

        self.widget_changed.emit(widget)
        self.canvas_changed.emit()

    # -----------------------------------------------------------------------
    # Internal signal handlers
    # -----------------------------------------------------------------------

    def _on_widget_selected(self, widget: FormWidget) -> None:
        """Handle widget selection."""
        modifiers = QApplication.keyboardModifiers()

        if modifiers & Qt.ControlModifier:
            # Toggle selection
            if widget.id in self._selected_widgets:
                self._selected_widgets.discard(widget.id)
                if widget.id in self._widget_items:
                    self._widget_items[widget.id].set_selected(False)
            else:
                self._selected_widgets.add(widget.id)
                if widget.id in self._widget_items:
                    self._widget_items[widget.id].set_selected(True)
        else:
            # Single select
            self._deselect_all()
            self._selected_widgets.add(widget.id)
            if widget.id in self._widget_items:
                self._widget_items[widget.id].set_selected(True)

        self.widget_selected.emit(widget)

    def _on_widget_moved(self, widget: FormWidget, x: int, y: int) -> None:
        """Handle widget move (during drag - update guides)."""
        snapped_x, snapped_y = self._compute_snap_guides(
            widget.id, x, y, widget.width, widget.height
        )

        if snapped_x != x or snapped_y != y:
            widget.x = snapped_x
            widget.y = snapped_y
            item = self._widget_items.get(widget.id)
            if item:
                # Move in screen coordinates (logical * zoom)
                item.move(int(snapped_x * self._zoom_level), int(snapped_y * self._zoom_level))
                item.widget.x = snapped_x
                item.widget.y = snapped_y

        self._canvas.update()  # Redraw guides
        self.widget_changed.emit(widget)
        self.canvas_changed.emit()

    def _on_widget_resized(self, widget: FormWidget, width: int, height: int) -> None:
        """Handle widget resize."""
        self.widget_changed.emit(widget)
        self.canvas_changed.emit()

    def _on_copy_requested(self, widget_id: str) -> None:
        """Handle copy request from context menu."""
        if widget_id not in self._selected_widgets:
            self._deselect_all()
            self._selected_widgets.add(widget_id)
            if widget_id in self._widget_items:
                self._widget_items[widget_id].set_selected(True)
        self.copy_selected()

    def _on_move_started(self, widget_id: str, x: int, y: int) -> None:
        """Track move start for undo."""
        self._pending_move = (widget_id, x, y)

    def _on_move_finished(self, widget_id: str, x: int, y: int) -> None:
        """Push move undo command."""
        if self._pending_move and self._pending_move[0] == widget_id:
            old_x, old_y = self._pending_move[1], self._pending_move[2]
            if old_x != x or old_y != y:
                cmd = MoveWidgetCommand(self, widget_id, old_x, old_y, x, y)
                self._undo_stack.push(cmd)
        self._pending_move = None
        self._guide_lines.clear()
        self._canvas.update()

    def _on_resize_started(self, widget_id: str, w: int, h: int) -> None:
        """Track resize start for undo."""
        self._pending_resize = (widget_id, w, h)

    def _on_resize_finished(self, widget_id: str, w: int, h: int) -> None:
        """Push resize undo command."""
        if self._pending_resize and self._pending_resize[0] == widget_id:
            old_w, old_h = self._pending_resize[1], self._pending_resize[2]
            if old_w != w or old_h != h:
                cmd = ResizeWidgetCommand(self, widget_id, old_w, old_h, w, h)
                self._undo_stack.push(cmd)
        self._pending_resize = None

    def _deselect_all(self) -> None:
        """Deselect all widgets."""
        for item in self._widget_items.values():
            item.set_selected(False)
        self._selected_widgets.clear()

    # -----------------------------------------------------------------------
    # Canvas operations
    # -----------------------------------------------------------------------

    def set_grid_visible(self, visible: bool) -> None:
        """Show/hide grid."""
        self._show_grid = visible
        self._canvas.update()

    def clear(self) -> None:
        """Clear all widgets."""
        for widget_id in list(self._widget_items.keys()):
            self._remove_widget_internal(widget_id)
        self._next_widget_id = 1
        self._undo_stack.clear()

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

        self._canvas.setMinimumSize(
            data.get("canvas_width", 800),
            data.get("canvas_height", 600)
        )

        for widget_data in data.get("widgets", []):
            widget = FormWidget.from_dict(widget_data)
            self._add_widget_internal(widget)

        self.canvas_changed.emit()
