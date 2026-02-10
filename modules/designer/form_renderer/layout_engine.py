"""
Layout Engine for INTEGRA FormRenderer.

Arranges widgets in the form using one of three layout modes:
- **Smart Grid** (default): QGridLayout with row/col/colspan/rowspan
- **Absolute**: Fixed x/y positions for precise placement
- **Flow**: Automatic wrapping layout (right-to-left for RTL)

The engine handles:
- Section cards with optional collapse
- Column width distribution
- Margins and spacing
- RTL/LTR direction
- Responsive min/max width constraints
- int() conversion for all Qt size methods (Rule #7)
"""

from __future__ import annotations

import copy
from typing import Any, Optional

from PyQt5.QtCore import Qt, QSize, QRect
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QScrollArea,
    QSizePolicy,
    QGroupBox,
    QPushButton,
    QLayout,
)
from PyQt5.QtGui import QFont

from core.logging import app_logger
from core.themes import (
    get_current_palette,
    get_font,
    FONT_FAMILY_ARABIC,
    FONT_SIZE_BODY,
    FONT_SIZE_SUBTITLE,
    FONT_SIZE_TITLE,
    FONT_WEIGHT_BOLD,
    FONT_WEIGHT_NORMAL,
)
from modules.designer.shared.form_schema import DEFAULT_FORM_SETTINGS


class LayoutEngine:
    """
    Arranges label+widget pairs into the form based on settings and
    field layout definitions.

    Usage::

        engine = LayoutEngine(form_settings)
        container = engine.build_form(sections_data, widget_map)
    """

    def __init__(self, settings: Optional[dict[str, Any]] = None) -> None:
        self._settings = copy.deepcopy(DEFAULT_FORM_SETTINGS)
        if settings:
            self._settings.update(settings)

        self._section_frames: dict[str, QFrame] = {}
        self._section_content_widgets: dict[str, QWidget] = {}
        self._section_toggle_buttons: dict[str, QPushButton] = {}

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def build_form(
        self,
        sections: list[dict[str, Any]],
        widget_map: dict[str, tuple[Optional[QLabel], QWidget, dict[str, Any]]],
        parent: Optional[QWidget] = None,
    ) -> QWidget:
        """
        Build the complete form layout from sections and widgets.

        Args:
            sections: List of section definitions from the .iform JSON.
            widget_map: Dict mapping field_id to (label, widget, field_def).
            parent: Optional parent widget.

        Returns:
            A QWidget containing the fully laid-out form.
        """
        layout_mode = self._settings.get("layout_mode", "smart_grid")
        direction = self._settings.get("direction", "rtl")

        # Main container
        container = QWidget(parent)
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(int(self._settings.get("row_gap", 15)))

        if direction == "rtl":
            main_layout.setAlignment(Qt.AlignRight)
            container.setLayoutDirection(Qt.RightToLeft)

        # Build each section
        for section_def in sections:
            section_widget = self._build_section(
                section_def, widget_map, layout_mode, direction, container
            )
            if section_widget:
                main_layout.addWidget(section_widget)

        # Spacer at the bottom
        main_layout.addStretch(1)

        return container

    def build_action_bar(
        self,
        actions: list[dict[str, Any]],
        parent: Optional[QWidget] = None,
    ) -> QWidget:
        """
        Build the action buttons bar (save, cancel, etc.).

        Args:
            actions: List of action definitions from .iform JSON.
            parent: Optional parent widget.

        Returns:
            A QWidget containing the action buttons.
        """
        bar = QWidget(parent)
        layout = QHBoxLayout(bar)
        margins = self._settings.get("margins", {})
        layout.setContentsMargins(
            int(margins.get("left", 20)),
            10,
            int(margins.get("right", 20)),
            int(margins.get("bottom", 20)),
        )
        layout.setSpacing(10)

        position = self._settings.get("save_button_position", "bottom_left")

        if position in ("bottom_right", "top_right"):
            layout.addStretch(1)

        if position == "bottom_center":
            layout.addStretch(1)

        for action_def in actions:
            btn = self._create_action_button(action_def, bar)
            if btn:
                layout.addWidget(btn)

        if position in ("bottom_left",):
            layout.addStretch(1)

        if position == "bottom_center":
            layout.addStretch(1)

        return bar

    def get_section_frame(self, section_id: str) -> Optional[QFrame]:
        """Get the card frame for a section by ID."""
        return self._section_frames.get(section_id)

    def set_section_visible(self, section_id: str, visible: bool) -> None:
        """Show or hide a section."""
        frame = self._section_frames.get(section_id)
        if frame:
            frame.setVisible(visible)

    def toggle_section(self, section_id: str) -> None:
        """Collapse/expand a section."""
        content = self._section_content_widgets.get(section_id)
        toggle_btn = self._section_toggle_buttons.get(section_id)
        if content is not None:
            new_visible = not content.isVisible()
            content.setVisible(new_visible)
            if toggle_btn:
                toggle_btn.setText("▼" if new_visible else "▶")

    # -----------------------------------------------------------------------
    # Section building
    # -----------------------------------------------------------------------

    def _build_section(
        self,
        section_def: dict[str, Any],
        widget_map: dict[str, tuple[Optional[QLabel], QWidget, dict[str, Any]]],
        layout_mode: str,
        direction: str,
        parent: QWidget,
    ) -> Optional[QFrame]:
        """Build a single section card."""
        section_id = section_def.get("id", "")
        visible = section_def.get("visible", True)

        # Card frame
        card = QFrame(parent)
        card.setObjectName(f"section_{section_id}")
        card.setFrameShape(QFrame.StyledPanel)
        card.setVisible(bool(visible))

        # Apply card styling from palette
        palette = get_current_palette()
        card_bg = palette.get("card_bg", palette.get("surface", "#1e293b"))
        card_border = palette.get("border", "#334155")
        card.setStyleSheet(
            f"QFrame#section_{section_id} {{"
            f"  background-color: {card_bg};"
            f"  border: 1px solid {card_border};"
            f"  border-radius: 8px;"
            f"  padding: 0px;"
            f"}}"
        )

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # Section header
        header = self._build_section_header(section_def, card)
        if header:
            card_layout.addWidget(header)

        # Section content
        content_widget = QWidget(card)
        content_widget.setObjectName(f"section_content_{section_id}")

        # Determine section-level column count (override or global)
        section_columns = section_def.get("columns", self._settings.get("columns", 2))

        if layout_mode == "smart_grid":
            self._layout_smart_grid(content_widget, section_def, widget_map, section_columns)
        elif layout_mode == "absolute":
            self._layout_absolute(content_widget, section_def, widget_map)
        else:
            self._layout_flow(content_widget, section_def, widget_map, direction)

        card_layout.addWidget(content_widget)

        # Handle collapsible
        collapsed = section_def.get("collapsed", False)
        if collapsed:
            content_widget.setVisible(False)

        self._section_frames[section_id] = card
        self._section_content_widgets[section_id] = content_widget

        return card

    def _build_section_header(
        self,
        section_def: dict[str, Any],
        parent: QWidget,
    ) -> Optional[QWidget]:
        """Build section header with title and optional collapse toggle."""
        title = section_def.get("title_ar") or section_def.get("title_en", "")
        if not title:
            return None

        section_id = section_def.get("id", "")
        collapsible = section_def.get("collapsible", True)
        collapsed = section_def.get("collapsed", False)

        header = QWidget(parent)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 12, 15, 8)
        header_layout.setSpacing(8)

        # Toggle button
        if collapsible:
            toggle_btn = QPushButton("▼" if not collapsed else "▶", header)
            toggle_btn.setFixedSize(24, 24)
            toggle_btn.setFlat(True)
            toggle_btn.setFont(get_font(size=FONT_SIZE_BODY))
            toggle_btn.setCursor(Qt.PointingHandCursor)
            toggle_btn.clicked.connect(lambda: self.toggle_section(section_id))
            header_layout.addWidget(toggle_btn)
            self._section_toggle_buttons[section_id] = toggle_btn

        # Title label
        title_label = QLabel(title, header)
        title_label.setFont(get_font(size=FONT_SIZE_SUBTITLE, weight=FONT_WEIGHT_BOLD))
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)

        # Separator line below header
        separator = QFrame(parent)
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setFixedHeight(1)

        wrapper = QWidget(parent)
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(0)
        wrapper_layout.addWidget(header)
        wrapper_layout.addWidget(separator)

        return wrapper

    # -----------------------------------------------------------------------
    # Layout modes
    # -----------------------------------------------------------------------

    def _layout_smart_grid(
        self,
        content_widget: QWidget,
        section_def: dict[str, Any],
        widget_map: dict[str, tuple[Optional[QLabel], QWidget, dict[str, Any]]],
        columns: int,
    ) -> None:
        """Arrange widgets in a QGridLayout with row/col placement."""
        margins = self._settings.get("margins", {})
        col_gap = int(self._settings.get("column_gap", 20))
        row_gap = int(self._settings.get("row_gap", 15))

        grid = QGridLayout(content_widget)
        grid.setContentsMargins(
            int(margins.get("left", 20)),
            10,
            int(margins.get("right", 20)),
            int(margins.get("bottom", 20)),
        )
        grid.setHorizontalSpacing(col_gap)
        grid.setVerticalSpacing(row_gap)

        fields = section_def.get("fields", [])

        # Auto-assign row/col for fields that don't specify them
        auto_row = 0
        auto_col = 0

        for field_def in fields:
            field_id = field_def.get("id", "")
            entry = widget_map.get(field_id)
            if not entry:
                continue

            label_widget, input_widget, _ = entry
            layout_info = field_def.get("layout", {})

            row = layout_info.get("row")
            col = layout_info.get("col")
            colspan = int(layout_info.get("colspan", 1))
            rowspan = int(layout_info.get("rowspan", 1))

            # Auto-placement if row/col not specified
            if row is None or col is None:
                row = auto_row
                col = auto_col

            row = int(row)
            col = int(col)

            # Apply size constraints
            self._apply_size_constraints(input_widget, layout_info)

            # Each field occupies 2 grid columns: label + widget
            # So for N logical columns we use N*2 grid columns
            grid_col_base = col * 2

            if label_widget:
                grid.addWidget(label_widget, row, grid_col_base, rowspan, 1, Qt.AlignRight | Qt.AlignTop)
                grid.addWidget(input_widget, row, grid_col_base + 1, rowspan, max(1, colspan * 2 - 1))
            else:
                # No label - widget spans both label and widget columns
                grid.addWidget(input_widget, row, grid_col_base, rowspan, colspan * 2)

            # Alignment
            alignment = layout_info.get("alignment", "stretch")
            if alignment != "stretch":
                align_map = {
                    "left": Qt.AlignLeft,
                    "center": Qt.AlignHCenter,
                    "right": Qt.AlignRight,
                }
                qt_align = align_map.get(alignment, Qt.AlignLeft)
                grid.setAlignment(input_widget, qt_align | Qt.AlignVCenter)

            # Advance auto-placement
            auto_col = col + colspan
            if auto_col >= columns:
                auto_col = 0
                auto_row = row + rowspan

        # Add column stretch
        total_grid_cols = columns * 2
        for c in range(total_grid_cols):
            if c % 2 == 0:
                # Label columns: don't stretch
                grid.setColumnStretch(c, 0)
            else:
                # Widget columns: stretch equally
                grid.setColumnStretch(c, 1)

    def _layout_absolute(
        self,
        content_widget: QWidget,
        section_def: dict[str, Any],
        widget_map: dict[str, tuple[Optional[QLabel], QWidget, dict[str, Any]]],
    ) -> None:
        """Position widgets at absolute x/y coordinates."""
        # No layout manager for absolute positioning
        content_widget.setMinimumHeight(400)

        fields = section_def.get("fields", [])
        for field_def in fields:
            field_id = field_def.get("id", "")
            entry = widget_map.get(field_id)
            if not entry:
                continue

            label_widget, input_widget, _ = entry
            layout_info = field_def.get("layout", {})

            x = int(layout_info.get("x", 0))
            y = int(layout_info.get("y", 0))
            w = layout_info.get("width")
            h = layout_info.get("height")

            input_widget.setParent(content_widget)

            if w and h:
                input_widget.setGeometry(x, y, int(w), int(h))
            elif w:
                input_widget.move(x, y)
                input_widget.setFixedWidth(int(w))
            else:
                input_widget.move(x, y)

            input_widget.show()

            # Place label above the widget
            if label_widget:
                label_widget.setParent(content_widget)
                label_widget.move(x, max(0, y - 25))
                label_widget.show()

    def _layout_flow(
        self,
        content_widget: QWidget,
        section_def: dict[str, Any],
        widget_map: dict[str, tuple[Optional[QLabel], QWidget, dict[str, Any]]],
        direction: str,
    ) -> None:
        """Arrange widgets in a flow layout (wraps automatically)."""
        margins = self._settings.get("margins", {})
        col_gap = int(self._settings.get("column_gap", 20))
        row_gap = int(self._settings.get("row_gap", 15))

        layout = _FlowLayout(content_widget, direction == "rtl")
        layout.setContentsMargins(
            int(margins.get("left", 20)),
            10,
            int(margins.get("right", 20)),
            int(margins.get("bottom", 20)),
        )
        layout.setSpacing(col_gap)

        fields = section_def.get("fields", [])
        for field_def in fields:
            field_id = field_def.get("id", "")
            entry = widget_map.get(field_id)
            if not entry:
                continue

            label_widget, input_widget, _ = entry
            layout_info = field_def.get("layout", {})

            # Wrap label + widget in a vertical container
            item_widget = QWidget(content_widget)
            item_layout = QVBoxLayout(item_widget)
            item_layout.setContentsMargins(0, 0, 0, 0)
            item_layout.setSpacing(4)

            if label_widget:
                item_layout.addWidget(label_widget)
            item_layout.addWidget(input_widget)

            self._apply_size_constraints(input_widget, layout_info)

            layout.addWidget(item_widget)

    # -----------------------------------------------------------------------
    # Action button creation
    # -----------------------------------------------------------------------

    def _create_action_button(
        self,
        action_def: dict[str, Any],
        parent: QWidget,
    ) -> Optional[QPushButton]:
        """Create a styled action button from an action definition."""
        action_id = action_def.get("id", "")
        label = action_def.get("label_ar") or action_def.get("label_en", "Button")
        action_type = action_def.get("type", "secondary")
        visible = action_def.get("visible", True)
        width = action_def.get("width")

        btn = QPushButton(label, parent)
        btn.setObjectName(f"action_{action_id}")
        btn.setFont(get_font(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD))
        btn.setCursor(Qt.PointingHandCursor)
        btn.setVisible(bool(visible))

        if width:
            btn.setFixedWidth(int(width))

        btn.setMinimumHeight(38)

        # Styling based on type
        palette = get_current_palette()
        style = self._get_action_button_style(action_type, palette)
        btn.setStyleSheet(style)

        # Shortcut
        shortcut = action_def.get("shortcut")
        if shortcut:
            btn.setShortcut(shortcut)

        return btn

    @staticmethod
    def _get_action_button_style(action_type: str, palette: dict) -> str:
        """Generate QSS for an action button based on its type."""
        button_fg = palette.get("button_fg", "#ffffff")
        disabled_bg = palette.get("disabled_bg", palette.get("surface", "#555"))
        disabled_fg = palette.get("disabled_fg", palette.get("text_muted", "#999"))

        color_map = {
            "primary": {
                "bg": palette.get("primary", "#2563eb"),
                "fg": button_fg,
                "hover_bg": palette.get("primary_hover", "#1d4ed8"),
            },
            "secondary": {
                "bg": palette.get("secondary", "#64748b"),
                "fg": button_fg,
                "hover_bg": palette.get("secondary_hover", "#475569"),
            },
            "danger": {
                "bg": palette.get("danger", "#ef4444"),
                "fg": button_fg,
                "hover_bg": palette.get("danger_hover", "#dc2626"),
            },
            "success": {
                "bg": palette.get("success", "#22c55e"),
                "fg": button_fg,
                "hover_bg": palette.get("success_hover", "#16a34a"),
            },
        }

        colors = color_map.get(action_type, color_map["secondary"])
        return (
            f"QPushButton {{"
            f"  background-color: {colors['bg']};"
            f"  color: {colors['fg']};"
            f"  border: none;"
            f"  border-radius: 6px;"
            f"  padding: 8px 20px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {colors['hover_bg']};"
            f"}}"
            f"QPushButton:disabled {{"
            f"  background-color: {disabled_bg};"
            f"  color: {disabled_fg};"
            f"}}"
        )

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _apply_size_constraints(widget: QWidget, layout_info: dict[str, Any]) -> None:
        """Apply width/height/min/max constraints to a widget."""
        width = layout_info.get("width")
        height = layout_info.get("height")
        min_width = layout_info.get("min_width")
        max_width = layout_info.get("max_width")

        if width is not None:
            widget.setFixedWidth(int(width))
        else:
            if min_width is not None:
                widget.setMinimumWidth(int(min_width))
            if max_width is not None:
                widget.setMaximumWidth(int(max_width))

        if height is not None:
            widget.setFixedHeight(int(height))


# ---------------------------------------------------------------------------
# Flow Layout implementation (RTL-aware)
# ---------------------------------------------------------------------------

class _FlowLayout(QLayout):
    """
    A flow layout that wraps widgets automatically.

    Supports RTL by reversing the placement direction.
    """

    def __init__(self, parent: Optional[QWidget] = None, rtl: bool = False) -> None:
        super().__init__(parent)
        self._items: list = []
        self._rtl = rtl
        self._spacing_val = 10

    def addItem(self, item) -> None:  # noqa: N802
        self._items.append(item)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int):  # noqa: N802
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int):  # noqa: N802
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def setSpacing(self, spacing: int) -> None:  # noqa: N802
        self._spacing_val = spacing

    def spacing(self) -> int:
        return self._spacing_val

    def hasHeightForWidth(self) -> bool:  # noqa: N802
        return True

    def heightForWidth(self, width: int) -> int:  # noqa: N802
        return self._do_layout(width, test_only=True)

    def setGeometry(self, rect) -> None:  # noqa: N802
        super().setGeometry(rect)
        self._do_layout(rect.width())

    def sizeHint(self) -> QSize:  # noqa: N802
        return self.minimumSize()

    def minimumSize(self) -> QSize:  # noqa: N802
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def _do_layout(self, width: int, test_only: bool = False) -> int:
        margins = self.contentsMargins()
        effective_width = width - margins.left() - margins.right()

        x = margins.left() if not self._rtl else (width - margins.right())
        y = margins.top()
        row_height = 0
        spacing = self._spacing_val

        for item in self._items:
            item_size = item.sizeHint()
            item_w = item_size.width()
            item_h = item_size.height()

            if self._rtl:
                next_x = x - item_w
                if next_x < margins.left() and x != (width - margins.right()):
                    # Wrap to next row
                    x = width - margins.right()
                    y += row_height + spacing
                    row_height = 0
                    next_x = x - item_w

                if not test_only:
                    item.setGeometry(
                        QRect(int(next_x), int(y), int(item_w), int(item_h))
                    )
                x = next_x - spacing
            else:
                next_x = x + item_w
                if next_x > effective_width + margins.left() and x != margins.left():
                    x = margins.left()
                    y += row_height + spacing
                    row_height = 0
                    next_x = x + item_w

                if not test_only:
                    item.setGeometry(QRect(int(x), int(y), int(item_w), int(item_h)))
                x = next_x + spacing

            row_height = max(row_height, item_h)

        return y + row_height + margins.bottom()
