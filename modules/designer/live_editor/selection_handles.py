"""
Selection Handles for INTEGRA Live Editor.

Provides visual resize/move handles drawn around the selected widget.
Eight handles arranged at corners and edge midpoints:

    [NW]----[N]----[NE]
      |               |
     [W]             [E]
      |               |
    [SW]----[S]----[SE]

Features:
- Corner handles resize proportionally (with Shift key)
- Edge handles resize one dimension only
- Center drag moves the widget
- Visual feedback with hover effects
- Theme-aware colors

Follows INTEGRA rules:
- Rule #7: int() for all Qt size operations
- Rule #11: Theme-aware colors
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Optional

from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor

from core.themes import get_current_palette


# ---------------------------------------------------------------------------
# Handle positions
# ---------------------------------------------------------------------------

class HandlePosition(Enum):
    """The eight handle positions around a selection."""
    NONE = auto()
    TOP_LEFT = auto()
    TOP = auto()
    TOP_RIGHT = auto()
    RIGHT = auto()
    BOTTOM_RIGHT = auto()
    BOTTOM = auto()
    BOTTOM_LEFT = auto()
    LEFT = auto()


# Cursor map for each handle
_HANDLE_CURSORS = {
    HandlePosition.TOP_LEFT: Qt.SizeFDiagCursor,
    HandlePosition.TOP: Qt.SizeVerCursor,
    HandlePosition.TOP_RIGHT: Qt.SizeBDiagCursor,
    HandlePosition.RIGHT: Qt.SizeHorCursor,
    HandlePosition.BOTTOM_RIGHT: Qt.SizeFDiagCursor,
    HandlePosition.BOTTOM: Qt.SizeVerCursor,
    HandlePosition.BOTTOM_LEFT: Qt.SizeBDiagCursor,
    HandlePosition.LEFT: Qt.SizeHorCursor,
}


# ---------------------------------------------------------------------------
# SelectionHandles
# ---------------------------------------------------------------------------

class SelectionHandles:
    """
    Manages the visual selection handles around a widget.

    This is a pure drawing/hit-testing helper -- it does not own any
    QWidget. The parent overlay calls ``paint()`` during ``paintEvent``
    and ``hit_test()`` during mouse events.

    Usage::

        handles = SelectionHandles()
        handles.set_target_rect(widget.geometry())
        handles.paint(painter)

        handle = handles.hit_test(mouse_pos)
        if handle != HandlePosition.NONE:
            # start resize in that direction
    """

    HANDLE_SIZE = 8  # pixels, half-extent of each handle square
    BORDER_PADDING = 1  # gap between handle border and widget edge

    # Minimum widget size during resize to prevent collapsing
    MIN_WIDGET_WIDTH = 30
    MIN_WIDGET_HEIGHT = 20

    def __init__(self) -> None:
        self._target_rect: Optional[QRect] = None
        self._handle_rects: dict[HandlePosition, QRect] = {}
        self._hovered_handle: HandlePosition = HandlePosition.NONE
        self._handle_color: Optional[QColor] = None
        self._handle_hover_color: Optional[QColor] = None
        self._border_color: Optional[QColor] = None

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def set_target_rect(self, rect: QRect) -> None:
        """
        Set the target widget geometry. Recalculates handle positions.

        Args:
            rect: The widget rect in overlay (parent) coordinates.
        """
        self._target_rect = QRect(rect)
        self._recalculate_handles()

    def get_target_rect(self) -> Optional[QRect]:
        """Get the current target rectangle."""
        return QRect(self._target_rect) if self._target_rect else None

    def set_hovered(self, handle: HandlePosition) -> None:
        """Set which handle is currently hovered for visual feedback."""
        self._hovered_handle = handle

    def hit_test(self, pos: QPoint) -> HandlePosition:
        """
        Test if a point hits any handle.

        Args:
            pos: Point in overlay coordinates.

        Returns:
            The HandlePosition hit, or NONE if no handle was hit.
        """
        for handle_pos, rect in self._handle_rects.items():
            # Use a slightly larger hit area for easier clicking
            inflated = rect.adjusted(-2, -2, 2, 2)
            if inflated.contains(pos):
                return handle_pos
        return HandlePosition.NONE

    def get_cursor(self, handle: HandlePosition) -> Qt.CursorShape:
        """Get the appropriate cursor for a handle position."""
        return _HANDLE_CURSORS.get(handle, Qt.ArrowCursor)

    def calculate_resize(
        self,
        handle: HandlePosition,
        delta: QPoint,
        keep_aspect: bool = False,
    ) -> QRect:
        """
        Calculate new widget rect after resizing from a handle.

        Args:
            handle: Which handle is being dragged.
            delta: Mouse movement delta (dx, dy).
            keep_aspect: If True, maintain aspect ratio (Shift key).

        Returns:
            New QRect for the widget.
        """
        if not self._target_rect:
            return QRect()

        rect = QRect(self._target_rect)
        dx = delta.x()
        dy = delta.y()

        if handle == HandlePosition.TOP_LEFT:
            rect.setLeft(rect.left() + dx)
            rect.setTop(rect.top() + dy)
        elif handle == HandlePosition.TOP:
            rect.setTop(rect.top() + dy)
        elif handle == HandlePosition.TOP_RIGHT:
            rect.setRight(rect.right() + dx)
            rect.setTop(rect.top() + dy)
        elif handle == HandlePosition.RIGHT:
            rect.setRight(rect.right() + dx)
        elif handle == HandlePosition.BOTTOM_RIGHT:
            rect.setRight(rect.right() + dx)
            rect.setBottom(rect.bottom() + dy)
        elif handle == HandlePosition.BOTTOM:
            rect.setBottom(rect.bottom() + dy)
        elif handle == HandlePosition.BOTTOM_LEFT:
            rect.setLeft(rect.left() + dx)
            rect.setBottom(rect.bottom() + dy)
        elif handle == HandlePosition.LEFT:
            rect.setLeft(rect.left() + dx)

        # Enforce minimum size
        if rect.width() < self.MIN_WIDGET_WIDTH:
            if handle in (
                HandlePosition.LEFT,
                HandlePosition.TOP_LEFT,
                HandlePosition.BOTTOM_LEFT,
            ):
                rect.setLeft(rect.right() - self.MIN_WIDGET_WIDTH)
            else:
                rect.setRight(rect.left() + self.MIN_WIDGET_WIDTH)

        if rect.height() < self.MIN_WIDGET_HEIGHT:
            if handle in (
                HandlePosition.TOP,
                HandlePosition.TOP_LEFT,
                HandlePosition.TOP_RIGHT,
            ):
                rect.setTop(rect.bottom() - self.MIN_WIDGET_HEIGHT)
            else:
                rect.setBottom(rect.top() + self.MIN_WIDGET_HEIGHT)

        # Aspect ratio preservation
        if keep_aspect and self._target_rect:
            orig = self._target_rect
            if orig.width() > 0 and orig.height() > 0:
                aspect = orig.width() / orig.height()
                if handle in (
                    HandlePosition.TOP_LEFT,
                    HandlePosition.TOP_RIGHT,
                    HandlePosition.BOTTOM_LEFT,
                    HandlePosition.BOTTOM_RIGHT,
                ):
                    new_h = max(self.MIN_WIDGET_HEIGHT, int(rect.width() / aspect))
                    if handle in (HandlePosition.TOP_LEFT, HandlePosition.TOP_RIGHT):
                        rect.setTop(rect.bottom() - new_h)
                    else:
                        rect.setBottom(rect.top() + new_h)

        return rect

    # -----------------------------------------------------------------------
    # Painting
    # -----------------------------------------------------------------------

    def paint(self, painter: QPainter) -> None:
        """
        Draw the selection border and handles.

        Args:
            painter: Active QPainter on the overlay widget.
        """
        if not self._target_rect:
            return

        self._ensure_colors()

        # Selection border (dashed blue line)
        border_pen = QPen(self._border_color, 2, Qt.DashLine)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(self._target_rect)

        # Draw handles
        for handle_pos, rect in self._handle_rects.items():
            is_hovered = (handle_pos == self._hovered_handle)
            self._paint_handle(painter, rect, is_hovered)

    def _paint_handle(
        self,
        painter: QPainter,
        rect: QRect,
        is_hovered: bool,
    ) -> None:
        """Draw a single handle square."""
        if is_hovered:
            painter.setPen(QPen(self._handle_hover_color, 1))
            painter.setBrush(QBrush(self._handle_hover_color))
        else:
            painter.setPen(QPen(self._handle_color, 1))
            painter.setBrush(QBrush(self._handle_color))

        painter.drawRect(rect)

    # -----------------------------------------------------------------------
    # Internals
    # -----------------------------------------------------------------------

    def _ensure_colors(self) -> None:
        """Load theme colors on first use."""
        if self._handle_color is None:
            palette = get_current_palette()
            primary = palette.get("primary", "#3b82f6")
            self._handle_color = QColor(primary)
            self._handle_hover_color = QColor(primary)
            self._handle_hover_color.setAlpha(200)
            self._border_color = QColor(primary)
            self._border_color.setAlpha(150)

    def _recalculate_handles(self) -> None:
        """Recalculate handle rects from the target rect."""
        self._handle_rects.clear()

        if not self._target_rect:
            return

        r = self._target_rect
        s = self.HANDLE_SIZE
        half = int(s / 2)

        # Center coordinates
        cx = int(r.left() + r.width() / 2)
        cy = int(r.top() + r.height() / 2)

        self._handle_rects[HandlePosition.TOP_LEFT] = QRect(
            r.left() - half, r.top() - half, s, s
        )
        self._handle_rects[HandlePosition.TOP] = QRect(
            cx - half, r.top() - half, s, s
        )
        self._handle_rects[HandlePosition.TOP_RIGHT] = QRect(
            r.right() - half, r.top() - half, s, s
        )
        self._handle_rects[HandlePosition.RIGHT] = QRect(
            r.right() - half, cy - half, s, s
        )
        self._handle_rects[HandlePosition.BOTTOM_RIGHT] = QRect(
            r.right() - half, r.bottom() - half, s, s
        )
        self._handle_rects[HandlePosition.BOTTOM] = QRect(
            cx - half, r.bottom() - half, s, s
        )
        self._handle_rects[HandlePosition.BOTTOM_LEFT] = QRect(
            r.left() - half, r.bottom() - half, s, s
        )
        self._handle_rects[HandlePosition.LEFT] = QRect(
            r.left() - half, cy - half, s, s
        )

    def clear(self) -> None:
        """Clear the selection."""
        self._target_rect = None
        self._handle_rects.clear()
        self._hovered_handle = HandlePosition.NONE
        self._handle_color = None
        self._handle_hover_color = None
        self._border_color = None
