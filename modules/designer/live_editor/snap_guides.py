"""
Snap Guides for INTEGRA Live Editor.

Provides smart alignment guides that appear when dragging widgets,
helping the user align elements precisely. Features:

- Edge alignment: left/right/top/bottom edges between widgets
- Center alignment: horizontal/vertical centers
- Spacing guides: shows distance between widgets
- Section guides: align with section card borders
- Configurable snap threshold (default 8px)
- Tolerance for guide display (default 5px)

The guides are drawn as an overlay using QPainter on the parent widget.

Follows INTEGRA rules:
- Rule #7: int() for all Qt size operations
- Rule #11: Theme-aware colors from get_current_palette()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtWidgets import QWidget

from core.logging import app_logger
from core.themes import get_current_palette, get_font, FONT_SIZE_TINY


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SnapGuide:
    """A single alignment guide line."""

    orientation: str  # "horizontal" or "vertical"
    position: int  # pixel position (x for vertical, y for horizontal)
    start: int  # start of the line segment
    end: int  # end of the line segment
    guide_type: str = "edge"  # "edge", "center", "spacing"
    label: Optional[str] = None  # distance label for spacing guides


@dataclass
class SnapResult:
    """Result of a snap calculation - which axis snapped and by how much."""

    snapped_x: bool = False
    snapped_y: bool = False
    delta_x: int = 0
    delta_y: int = 0
    guides: list[SnapGuide] = field(default_factory=list)


# ---------------------------------------------------------------------------
# SnapGuideEngine
# ---------------------------------------------------------------------------

class SnapGuideEngine:
    """
    Calculates and draws alignment guides during drag operations.

    Usage::

        engine = SnapGuideEngine()
        engine.set_reference_rects(other_widget_rects)
        result = engine.calculate_snap(dragging_rect)
        engine.paint_guides(painter, result.guides)
    """

    # Pixels within which snap activates
    SNAP_THRESHOLD = 8
    # Pixels within which a guide line is shown (but no snap)
    GUIDE_TOLERANCE = 5
    # Minimum distance label display threshold
    MIN_SPACING_LABEL = 10

    def __init__(self) -> None:
        self._reference_rects: list[tuple[str, QRect]] = []
        self._container_rect: Optional[QRect] = None
        self._guide_color: Optional[QColor] = None
        self._spacing_color: Optional[QColor] = None

    # -----------------------------------------------------------------------
    # Configuration
    # -----------------------------------------------------------------------

    def set_reference_rects(
        self,
        rects: list[tuple[str, QRect]],
    ) -> None:
        """
        Set the reference rectangles (other widgets) to snap against.

        Args:
            rects: List of (widget_id, QRect) tuples in parent coordinates.
        """
        self._reference_rects = list(rects)

    def set_container_rect(self, rect: QRect) -> None:
        """Set the container (section card) rect for section-edge snapping."""
        self._container_rect = rect

    def _ensure_colors(self) -> None:
        """Lazily load theme colors for guide drawing."""
        if self._guide_color is None:
            palette = get_current_palette()
            primary = palette.get("primary", "#3b82f6")
            self._guide_color = QColor(primary)
            self._guide_color.setAlpha(180)

            info = palette.get("info", "#06b6d4")
            self._spacing_color = QColor(info)
            self._spacing_color.setAlpha(150)

    # -----------------------------------------------------------------------
    # Snap calculation
    # -----------------------------------------------------------------------

    def calculate_snap(
        self,
        dragging_rect: QRect,
        excluded_id: Optional[str] = None,
    ) -> SnapResult:
        """
        Calculate snap offsets and guide lines for a dragging rectangle.

        Args:
            dragging_rect: The current rect of the widget being dragged.
            excluded_id: Widget ID to exclude from reference (self).

        Returns:
            SnapResult with delta offsets and guide lines.
        """
        result = SnapResult()
        best_dx: Optional[tuple[int, SnapGuide]] = None
        best_dy: Optional[tuple[int, SnapGuide]] = None

        drag_left = dragging_rect.left()
        drag_right = dragging_rect.right()
        drag_top = dragging_rect.top()
        drag_bottom = dragging_rect.bottom()
        drag_cx = int(dragging_rect.center().x())
        drag_cy = int(dragging_rect.center().y())

        for ref_id, ref_rect in self._reference_rects:
            if ref_id == excluded_id:
                continue

            ref_left = ref_rect.left()
            ref_right = ref_rect.right()
            ref_top = ref_rect.top()
            ref_bottom = ref_rect.bottom()
            ref_cx = int(ref_rect.center().x())
            ref_cy = int(ref_rect.center().y())

            # --- Vertical (X-axis) snapping ---

            # Left-to-left
            dx = ref_left - drag_left
            if abs(dx) <= self.SNAP_THRESHOLD:
                guide = SnapGuide(
                    orientation="vertical",
                    position=ref_left,
                    start=min(drag_top, ref_top) - 10,
                    end=max(drag_bottom, ref_bottom) + 10,
                    guide_type="edge",
                )
                if best_dx is None or abs(dx) < abs(best_dx[0]):
                    best_dx = (dx, guide)

            # Right-to-right
            dx = ref_right - drag_right
            if abs(dx) <= self.SNAP_THRESHOLD:
                guide = SnapGuide(
                    orientation="vertical",
                    position=ref_right,
                    start=min(drag_top, ref_top) - 10,
                    end=max(drag_bottom, ref_bottom) + 10,
                    guide_type="edge",
                )
                if best_dx is None or abs(dx) < abs(best_dx[0]):
                    best_dx = (dx, guide)

            # Left-to-right
            dx = ref_right - drag_left
            if abs(dx) <= self.SNAP_THRESHOLD:
                guide = SnapGuide(
                    orientation="vertical",
                    position=ref_right,
                    start=min(drag_top, ref_top) - 10,
                    end=max(drag_bottom, ref_bottom) + 10,
                    guide_type="edge",
                )
                if best_dx is None or abs(dx) < abs(best_dx[0]):
                    best_dx = (dx, guide)

            # Right-to-left
            dx = ref_left - drag_right
            if abs(dx) <= self.SNAP_THRESHOLD:
                guide = SnapGuide(
                    orientation="vertical",
                    position=ref_left,
                    start=min(drag_top, ref_top) - 10,
                    end=max(drag_bottom, ref_bottom) + 10,
                    guide_type="edge",
                )
                if best_dx is None or abs(dx) < abs(best_dx[0]):
                    best_dx = (dx, guide)

            # Center-to-center (vertical)
            dx = ref_cx - drag_cx
            if abs(dx) <= self.SNAP_THRESHOLD:
                guide = SnapGuide(
                    orientation="vertical",
                    position=ref_cx,
                    start=min(drag_top, ref_top) - 10,
                    end=max(drag_bottom, ref_bottom) + 10,
                    guide_type="center",
                )
                if best_dx is None or abs(dx) < abs(best_dx[0]):
                    best_dx = (dx, guide)

            # --- Horizontal (Y-axis) snapping ---

            # Top-to-top
            dy = ref_top - drag_top
            if abs(dy) <= self.SNAP_THRESHOLD:
                guide = SnapGuide(
                    orientation="horizontal",
                    position=ref_top,
                    start=min(drag_left, ref_left) - 10,
                    end=max(drag_right, ref_right) + 10,
                    guide_type="edge",
                )
                if best_dy is None or abs(dy) < abs(best_dy[0]):
                    best_dy = (dy, guide)

            # Bottom-to-bottom
            dy = ref_bottom - drag_bottom
            if abs(dy) <= self.SNAP_THRESHOLD:
                guide = SnapGuide(
                    orientation="horizontal",
                    position=ref_bottom,
                    start=min(drag_left, ref_left) - 10,
                    end=max(drag_right, ref_right) + 10,
                    guide_type="edge",
                )
                if best_dy is None or abs(dy) < abs(best_dy[0]):
                    best_dy = (dy, guide)

            # Top-to-bottom
            dy = ref_bottom - drag_top
            if abs(dy) <= self.SNAP_THRESHOLD:
                guide = SnapGuide(
                    orientation="horizontal",
                    position=ref_bottom,
                    start=min(drag_left, ref_left) - 10,
                    end=max(drag_right, ref_right) + 10,
                    guide_type="edge",
                )
                if best_dy is None or abs(dy) < abs(best_dy[0]):
                    best_dy = (dy, guide)

            # Bottom-to-top
            dy = ref_top - drag_bottom
            if abs(dy) <= self.SNAP_THRESHOLD:
                guide = SnapGuide(
                    orientation="horizontal",
                    position=ref_top,
                    start=min(drag_left, ref_left) - 10,
                    end=max(drag_right, ref_right) + 10,
                    guide_type="edge",
                )
                if best_dy is None or abs(dy) < abs(best_dy[0]):
                    best_dy = (dy, guide)

            # Center-to-center (horizontal)
            dy = ref_cy - drag_cy
            if abs(dy) <= self.SNAP_THRESHOLD:
                guide = SnapGuide(
                    orientation="horizontal",
                    position=ref_cy,
                    start=min(drag_left, ref_left) - 10,
                    end=max(drag_right, ref_right) + 10,
                    guide_type="center",
                )
                if best_dy is None or abs(dy) < abs(best_dy[0]):
                    best_dy = (dy, guide)

        # Container edge snapping
        if self._container_rect is not None:
            cr = self._container_rect
            for edge_x in (cr.left(), cr.right()):
                for drag_edge in (drag_left, drag_right, drag_cx):
                    dx = edge_x - drag_edge
                    if abs(dx) <= self.SNAP_THRESHOLD:
                        guide = SnapGuide(
                            orientation="vertical",
                            position=edge_x,
                            start=cr.top(),
                            end=cr.bottom(),
                            guide_type="edge",
                        )
                        if best_dx is None or abs(dx) < abs(best_dx[0]):
                            best_dx = (dx, guide)

            for edge_y in (cr.top(), cr.bottom()):
                for drag_edge in (drag_top, drag_bottom, drag_cy):
                    dy = edge_y - drag_edge
                    if abs(dy) <= self.SNAP_THRESHOLD:
                        guide = SnapGuide(
                            orientation="horizontal",
                            position=edge_y,
                            start=cr.left(),
                            end=cr.right(),
                            guide_type="edge",
                        )
                        if best_dy is None or abs(dy) < abs(best_dy[0]):
                            best_dy = (dy, guide)

        # Build result
        if best_dx is not None:
            result.snapped_x = True
            result.delta_x = best_dx[0]
            result.guides.append(best_dx[1])

        if best_dy is not None:
            result.snapped_y = True
            result.delta_y = best_dy[0]
            result.guides.append(best_dy[1])

        # Add spacing guides for nearby widgets
        self._add_spacing_guides(dragging_rect, excluded_id, result)

        return result

    def _add_spacing_guides(
        self,
        dragging_rect: QRect,
        excluded_id: Optional[str],
        result: SnapResult,
    ) -> None:
        """Add distance labels between the dragged widget and nearby widgets."""
        drag_cx = int(dragging_rect.center().x())
        drag_cy = int(dragging_rect.center().y())

        for ref_id, ref_rect in self._reference_rects:
            if ref_id == excluded_id:
                continue

            # Horizontal spacing (widget is to the left or right)
            if (
                dragging_rect.bottom() >= ref_rect.top()
                and dragging_rect.top() <= ref_rect.bottom()
            ):
                # Widget to the right
                if dragging_rect.left() > ref_rect.right():
                    gap = dragging_rect.left() - ref_rect.right()
                    if gap < 200:
                        mid_x = int(ref_rect.right() + gap / 2)
                        mid_y = max(dragging_rect.top(), ref_rect.top())
                        guide = SnapGuide(
                            orientation="horizontal",
                            position=mid_y - 5,
                            start=ref_rect.right(),
                            end=dragging_rect.left(),
                            guide_type="spacing",
                            label=f"{gap}px",
                        )
                        result.guides.append(guide)

                # Widget to the left
                elif ref_rect.left() > dragging_rect.right():
                    gap = ref_rect.left() - dragging_rect.right()
                    if gap < 200:
                        mid_y = max(dragging_rect.top(), ref_rect.top())
                        guide = SnapGuide(
                            orientation="horizontal",
                            position=mid_y - 5,
                            start=dragging_rect.right(),
                            end=ref_rect.left(),
                            guide_type="spacing",
                            label=f"{gap}px",
                        )
                        result.guides.append(guide)

            # Vertical spacing (widget is above or below)
            if (
                dragging_rect.right() >= ref_rect.left()
                and dragging_rect.left() <= ref_rect.right()
            ):
                # Widget below
                if dragging_rect.top() > ref_rect.bottom():
                    gap = dragging_rect.top() - ref_rect.bottom()
                    if gap < 200:
                        mid_x = max(dragging_rect.left(), ref_rect.left())
                        guide = SnapGuide(
                            orientation="vertical",
                            position=mid_x - 5,
                            start=ref_rect.bottom(),
                            end=dragging_rect.top(),
                            guide_type="spacing",
                            label=f"{gap}px",
                        )
                        result.guides.append(guide)

                # Widget above
                elif ref_rect.top() > dragging_rect.bottom():
                    gap = ref_rect.top() - dragging_rect.bottom()
                    if gap < 200:
                        mid_x = max(dragging_rect.left(), ref_rect.left())
                        guide = SnapGuide(
                            orientation="vertical",
                            position=mid_x - 5,
                            start=dragging_rect.bottom(),
                            end=ref_rect.top(),
                            guide_type="spacing",
                            label=f"{gap}px",
                        )
                        result.guides.append(guide)

    # -----------------------------------------------------------------------
    # Painting
    # -----------------------------------------------------------------------

    def paint_guides(
        self,
        painter: QPainter,
        guides: list[SnapGuide],
    ) -> None:
        """
        Draw snap guides using the given QPainter.

        Args:
            painter: Active QPainter on the overlay widget.
            guides: List of SnapGuide objects to draw.
        """
        self._ensure_colors()

        for guide in guides:
            if guide.guide_type == "spacing":
                self._paint_spacing_guide(painter, guide)
            elif guide.guide_type == "center":
                self._paint_center_guide(painter, guide)
            else:
                self._paint_edge_guide(painter, guide)

    def _paint_edge_guide(self, painter: QPainter, guide: SnapGuide) -> None:
        """Draw an edge alignment guide (dashed line)."""
        pen = QPen(self._guide_color, 1, Qt.DashLine)
        painter.setPen(pen)

        if guide.orientation == "vertical":
            painter.drawLine(
                int(guide.position), int(guide.start),
                int(guide.position), int(guide.end),
            )
        else:
            painter.drawLine(
                int(guide.start), int(guide.position),
                int(guide.end), int(guide.position),
            )

    def _paint_center_guide(self, painter: QPainter, guide: SnapGuide) -> None:
        """Draw a center alignment guide (dotted line)."""
        pen = QPen(self._guide_color, 1, Qt.DotLine)
        painter.setPen(pen)

        if guide.orientation == "vertical":
            painter.drawLine(
                int(guide.position), int(guide.start),
                int(guide.position), int(guide.end),
            )
        else:
            painter.drawLine(
                int(guide.start), int(guide.position),
                int(guide.end), int(guide.position),
            )

    def _paint_spacing_guide(self, painter: QPainter, guide: SnapGuide) -> None:
        """Draw a spacing guide with distance label."""
        pen = QPen(self._spacing_color, 1, Qt.DashDotLine)
        painter.setPen(pen)

        if guide.orientation == "horizontal":
            y = int(guide.position)
            painter.drawLine(int(guide.start), y, int(guide.end), y)
            # Arrow heads
            painter.drawLine(int(guide.start), y - 3, int(guide.start), y + 3)
            painter.drawLine(int(guide.end), y - 3, int(guide.end), y + 3)
        else:
            x = int(guide.position)
            painter.drawLine(x, int(guide.start), x, int(guide.end))
            painter.drawLine(x - 3, int(guide.start), x + 3, int(guide.start))
            painter.drawLine(x - 3, int(guide.end), x + 3, int(guide.end))

        # Distance label
        if guide.label:
            painter.setFont(get_font(size=FONT_SIZE_TINY))
            painter.setPen(QPen(self._spacing_color))

            if guide.orientation == "horizontal":
                label_x = int((guide.start + guide.end) / 2) - 15
                label_y = int(guide.position) - 8
            else:
                label_x = int(guide.position) + 5
                label_y = int((guide.start + guide.end) / 2) - 5

            # Background for label readability
            palette = get_current_palette()
            bg = QColor(palette.get("background", "#0f172a"))
            bg.setAlpha(200)
            metrics = painter.fontMetrics()
            text_rect = metrics.boundingRect(guide.label)
            bg_rect = QRect(
                label_x - 2, label_y - text_rect.height(),
                text_rect.width() + 4, text_rect.height() + 2,
            )
            painter.fillRect(bg_rect, bg)
            painter.drawText(label_x, label_y, guide.label)

    # -----------------------------------------------------------------------
    # Cleanup
    # -----------------------------------------------------------------------

    def clear(self) -> None:
        """Clear all reference data."""
        self._reference_rects.clear()
        self._container_rect = None
        self._guide_color = None
        self._spacing_color = None
