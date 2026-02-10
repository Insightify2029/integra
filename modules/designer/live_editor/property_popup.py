"""
Property Popup for INTEGRA Live Editor.

A small popup window that appears near the selected widget, allowing
quick edits to common properties without opening the full property editor.

Features:
- Width/height spinboxes
- Label text edit
- Read-only checkbox
- Quick-access "Advanced Properties" button
- Delete and duplicate buttons
- Auto-positioning near the selected widget
- Theme-aware styling

Follows INTEGRA rules:
- Rule #7: int() for all Qt size operations
- Rule #11: Theme-aware colors from get_current_palette()
- Rule #6: Proper widget lifecycle cleanup
"""

from __future__ import annotations

from typing import Any, Optional

from PyQt5.QtCore import Qt, QPoint, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QCheckBox,
    QPushButton,
    QFrame,
    QApplication,
)
from PyQt5.QtGui import QFont

from core.logging import app_logger
from core.themes import (
    get_current_palette,
    get_font,
    FONT_SIZE_BODY,
    FONT_SIZE_SMALL,
    FONT_WEIGHT_BOLD,
    FONT_WEIGHT_NORMAL,
)


class PropertyPopup(QWidget):
    """
    Compact property editor popup for live editing mode.

    Signals:
        property_changed(str, str, object): (field_id, property_name, new_value)
        delete_requested(str): field_id to delete
        duplicate_requested(str): field_id to duplicate
        advanced_requested(str): field_id for advanced editor
        closed(): Popup was closed
    """

    property_changed = pyqtSignal(str, str, object)
    delete_requested = pyqtSignal(str)
    duplicate_requested = pyqtSignal(str)
    advanced_requested = pyqtSignal(str)
    closed = pyqtSignal()

    # Maximum width of the popup
    MAX_WIDTH = 280
    MAX_HEIGHT = 350

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setMaximumWidth(self.MAX_WIDTH)
        self.setMaximumHeight(self.MAX_HEIGHT)

        self._field_id: Optional[str] = None
        self._field_def: Optional[dict[str, Any]] = None
        self._suppress_signals = False

        self._init_ui()
        self._apply_theme()

    # -----------------------------------------------------------------------
    # UI setup
    # -----------------------------------------------------------------------

    def _init_ui(self) -> None:
        """Build the popup UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(6)

        # Header: field name
        self._header_label = QLabel("", self)
        self._header_label.setFont(get_font(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD))
        self._header_label.setAlignment(Qt.AlignRight)
        main_layout.addWidget(self._header_label)

        # Separator
        sep = QFrame(self)
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setFixedHeight(1)
        main_layout.addWidget(sep)

        # Properties grid
        grid = QGridLayout()
        grid.setContentsMargins(0, 4, 0, 4)
        grid.setSpacing(6)
        grid.setColumnStretch(1, 1)

        row = 0

        # Width
        lbl_w = QLabel("العرض:", self)
        lbl_w.setFont(get_font(size=FONT_SIZE_SMALL))
        lbl_w.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._width_spin = QSpinBox(self)
        self._width_spin.setRange(20, 2000)
        self._width_spin.setSuffix(" px")
        self._width_spin.setFont(get_font(size=FONT_SIZE_SMALL))
        self._width_spin.valueChanged.connect(self._on_width_changed)
        grid.addWidget(lbl_w, row, 0)
        grid.addWidget(self._width_spin, row, 1)
        row += 1

        # Height
        lbl_h = QLabel("الارتفاع:", self)
        lbl_h.setFont(get_font(size=FONT_SIZE_SMALL))
        lbl_h.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._height_spin = QSpinBox(self)
        self._height_spin.setRange(15, 1000)
        self._height_spin.setSuffix(" px")
        self._height_spin.setFont(get_font(size=FONT_SIZE_SMALL))
        self._height_spin.valueChanged.connect(self._on_height_changed)
        grid.addWidget(lbl_h, row, 0)
        grid.addWidget(self._height_spin, row, 1)
        row += 1

        # Label text
        lbl_text = QLabel("النص:", self)
        lbl_text.setFont(get_font(size=FONT_SIZE_SMALL))
        lbl_text.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._label_edit = QLineEdit(self)
        self._label_edit.setFont(get_font(size=FONT_SIZE_SMALL))
        self._label_edit.setPlaceholderText("عنوان الحقل")
        self._label_edit.editingFinished.connect(self._on_label_changed)
        grid.addWidget(lbl_text, row, 0)
        grid.addWidget(self._label_edit, row, 1)
        row += 1

        # Readonly checkbox
        self._readonly_check = QCheckBox("للقراءة فقط", self)
        self._readonly_check.setFont(get_font(size=FONT_SIZE_SMALL))
        self._readonly_check.stateChanged.connect(self._on_readonly_changed)
        grid.addWidget(self._readonly_check, row, 0, 1, 2)
        row += 1

        # Visible checkbox
        self._visible_check = QCheckBox("مرئي", self)
        self._visible_check.setFont(get_font(size=FONT_SIZE_SMALL))
        self._visible_check.stateChanged.connect(self._on_visible_changed)
        grid.addWidget(self._visible_check, row, 0, 1, 2)
        row += 1

        main_layout.addLayout(grid)

        # Separator before buttons
        sep2 = QFrame(self)
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFrameShadow(QFrame.Sunken)
        sep2.setFixedHeight(1)
        main_layout.addWidget(sep2)

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)

        self._advanced_btn = QPushButton("خصائص متقدمة", self)
        self._advanced_btn.setFont(get_font(size=FONT_SIZE_SMALL))
        self._advanced_btn.setCursor(Qt.PointingHandCursor)
        self._advanced_btn.clicked.connect(self._on_advanced_clicked)
        btn_layout.addWidget(self._advanced_btn)

        btn_layout.addStretch(1)

        self._duplicate_btn = QPushButton("نسخ", self)
        self._duplicate_btn.setFont(get_font(size=FONT_SIZE_SMALL))
        self._duplicate_btn.setCursor(Qt.PointingHandCursor)
        self._duplicate_btn.setFixedWidth(50)
        self._duplicate_btn.clicked.connect(self._on_duplicate_clicked)
        btn_layout.addWidget(self._duplicate_btn)

        self._delete_btn = QPushButton("حذف", self)
        self._delete_btn.setFont(get_font(size=FONT_SIZE_SMALL))
        self._delete_btn.setCursor(Qt.PointingHandCursor)
        self._delete_btn.setFixedWidth(50)
        self._delete_btn.clicked.connect(self._on_delete_clicked)
        btn_layout.addWidget(self._delete_btn)

        main_layout.addLayout(btn_layout)

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def show_for_field(
        self,
        field_id: str,
        field_def: dict[str, Any],
        widget_rect: Any,
        parent_rect: Any,
    ) -> None:
        """
        Show the popup for a specific field near its widget.

        Args:
            field_id: The field identifier.
            field_def: The field definition dict from the .iform schema.
            widget_rect: QRect of the selected widget in screen coordinates.
            parent_rect: QRect of the parent/overlay in screen coordinates.
        """
        self._field_id = field_id
        self._field_def = field_def

        # Populate values
        self._suppress_signals = True
        try:
            self._populate(field_def, widget_rect)
        finally:
            self._suppress_signals = False

        # Position popup next to the widget
        self._position_popup(widget_rect, parent_rect)
        self.show()
        self.raise_()

    def hide_popup(self) -> None:
        """Hide the popup."""
        self.hide()
        self._field_id = None
        self._field_def = None

    @property
    def current_field_id(self) -> Optional[str]:
        """The field ID currently shown, if any."""
        return self._field_id

    # -----------------------------------------------------------------------
    # Data population
    # -----------------------------------------------------------------------

    def _populate(self, field_def: dict[str, Any], widget_rect: Any) -> None:
        """Fill UI with current field properties."""
        # Header
        label = field_def.get("label_ar") or field_def.get("label_en", "")
        widget_type = field_def.get("widget_type", "")
        self._header_label.setText(f"{label} ({widget_type})")

        # Size from widget rect
        self._width_spin.setValue(int(widget_rect.width()))
        self._height_spin.setValue(int(widget_rect.height()))

        # Label text
        self._label_edit.setText(
            field_def.get("label_ar") or field_def.get("label_en", "")
        )

        # Properties
        props = field_def.get("properties", {})
        self._readonly_check.setChecked(bool(props.get("readonly", False)))
        self._visible_check.setChecked(bool(props.get("visible", True)))

    def _position_popup(self, widget_rect: Any, parent_rect: Any) -> None:
        """Position the popup near the widget, keeping it on screen."""
        # Try to position to the left of the widget (RTL friendly)
        popup_width = self.sizeHint().width()
        popup_height = self.sizeHint().height()

        # Try left side first
        x = int(widget_rect.left()) - popup_width - 10
        y = int(widget_rect.top())

        # If off-screen left, try right side
        if x < 0:
            x = int(widget_rect.right()) + 10

        # Keep on screen vertically
        screen = QApplication.primaryScreen()
        if screen:
            screen_rect = screen.availableGeometry()
            if x + popup_width > screen_rect.right():
                x = int(widget_rect.left()) - popup_width - 10
            if x < screen_rect.left():
                x = screen_rect.left() + 5
            if y + popup_height > screen_rect.bottom():
                y = screen_rect.bottom() - popup_height - 5
            if y < screen_rect.top():
                y = screen_rect.top() + 5

        self.move(int(x), int(y))

    # -----------------------------------------------------------------------
    # Signal handlers
    # -----------------------------------------------------------------------

    def _on_width_changed(self, value: int) -> None:
        if self._suppress_signals or not self._field_id:
            return
        self.property_changed.emit(self._field_id, "width", value)

    def _on_height_changed(self, value: int) -> None:
        if self._suppress_signals or not self._field_id:
            return
        self.property_changed.emit(self._field_id, "height", value)

    def _on_label_changed(self) -> None:
        if self._suppress_signals or not self._field_id:
            return
        self.property_changed.emit(
            self._field_id, "label_ar", self._label_edit.text()
        )

    def _on_readonly_changed(self, state: int) -> None:
        if self._suppress_signals or not self._field_id:
            return
        self.property_changed.emit(
            self._field_id, "readonly", state == Qt.Checked
        )

    def _on_visible_changed(self, state: int) -> None:
        if self._suppress_signals or not self._field_id:
            return
        self.property_changed.emit(
            self._field_id, "visible", state == Qt.Checked
        )

    def _on_advanced_clicked(self) -> None:
        if self._field_id:
            self.advanced_requested.emit(self._field_id)

    def _on_delete_clicked(self) -> None:
        if self._field_id:
            self.delete_requested.emit(self._field_id)

    def _on_duplicate_clicked(self) -> None:
        if self._field_id:
            self.duplicate_requested.emit(self._field_id)

    # -----------------------------------------------------------------------
    # Theming
    # -----------------------------------------------------------------------

    def _apply_theme(self) -> None:
        """Apply theme-aware styling to the popup."""
        palette = get_current_palette()
        bg = palette.get("surface", palette.get("card_bg", "#1e293b"))
        border = palette.get("border", "#334155")
        text_color = palette.get("text", palette.get("foreground", "#e2e8f0"))
        danger = palette.get("danger", "#ef4444")
        primary = palette.get("primary", "#3b82f6")
        muted = palette.get("text_muted", "#94a3b8")

        self.setStyleSheet(
            f"PropertyPopup {{"
            f"  background-color: {bg};"
            f"  border: 1px solid {border};"
            f"  border-radius: 8px;"
            f"  color: {text_color};"
            f"}}"
            f"QLabel {{"
            f"  color: {text_color};"
            f"  background: transparent;"
            f"  border: none;"
            f"}}"
            f"QLineEdit, QSpinBox {{"
            f"  background-color: {palette.get('background', '#0f172a')};"
            f"  color: {text_color};"
            f"  border: 1px solid {border};"
            f"  border-radius: 4px;"
            f"  padding: 3px 6px;"
            f"}}"
            f"QCheckBox {{"
            f"  color: {text_color};"
            f"  background: transparent;"
            f"  spacing: 6px;"
            f"}}"
            f"QPushButton {{"
            f"  background-color: {palette.get('background', '#0f172a')};"
            f"  color: {text_color};"
            f"  border: 1px solid {border};"
            f"  border-radius: 4px;"
            f"  padding: 4px 8px;"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {border};"
            f"}}"
        )

        # Special styling for delete button
        self._delete_btn.setStyleSheet(
            f"QPushButton {{"
            f"  color: {danger};"
            f"  border-color: {danger};"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {danger};"
            f"  color: white;"
            f"}}"
        )

        # Special styling for advanced button
        self._advanced_btn.setStyleSheet(
            f"QPushButton {{"
            f"  color: {primary};"
            f"  border-color: {primary};"
            f"}}"
            f"QPushButton:hover {{"
            f"  background-color: {primary};"
            f"  color: white;"
            f"}}"
        )

    # -----------------------------------------------------------------------
    # Events
    # -----------------------------------------------------------------------

    def focusOutEvent(self, event) -> None:  # noqa: N802
        """Auto-hide when focus is lost (clicking outside)."""
        super().focusOutEvent(event)

        # Don't hide if focus moved to a child widget
        focus_widget = QApplication.focusWidget()
        if focus_widget and self.isAncestorOf(focus_widget):
            return

        # Delay hide to allow child focus transitions (prevents flicker)
        QTimer.singleShot(200, self._check_focus_hide)

    def _check_focus_hide(self) -> None:
        """Check if focus is still outside the popup and hide if so."""
        focus_widget = QApplication.focusWidget()
        if focus_widget and self.isAncestorOf(focus_widget):
            return
        if self.isVisible() and self._field_id:
            self.hide_popup()
            self.closed.emit()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        """Handle Escape to close."""
        if event.key() == Qt.Key_Escape:
            self.hide_popup()
            self.closed.emit()
        else:
            super().keyPressEvent(event)
