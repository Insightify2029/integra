"""
Widget Factory for INTEGRA FormRenderer.

Creates PyQt5 widgets from JSON field definitions. Each widget type
maps to a concrete PyQt5 class with proper configuration for:
- Labels and placeholders (Arabic/English)
- Properties (readonly, enabled, visible, tooltip)
- Style overrides on top of the current theme
- Required indicator (*)
- RTL support
- Signal connections for dirty tracking
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from PyQt5.QtCore import Qt, QDate, QTime, QDateTime, pyqtSignal, QObject
from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QTextEdit,
    QSpinBox,
    QDoubleSpinBox,
    QComboBox,
    QCheckBox,
    QRadioButton,
    QButtonGroup,
    QDateEdit,
    QTimeEdit,
    QDateTimeEdit,
    QPushButton,
    QFrame,
    QGroupBox,
    QTableWidget,
    QSlider,
    QProgressBar,
    QHBoxLayout,
    QVBoxLayout,
    QFileDialog,
    QColorDialog,
    QSizePolicy,
)
from PyQt5.QtGui import QFont, QPixmap, QColor, QIntValidator, QDoubleValidator

from core.logging import app_logger
from core.themes import (
    get_current_palette,
    get_font,
    FONT_FAMILY_ARABIC,
    FONT_SIZE_BODY,
    FONT_SIZE_SMALL,
    FONT_WEIGHT_NORMAL,
    FONT_WEIGHT_BOLD,
)
from modules.designer.shared.form_schema import (
    SUPPORTED_WIDGET_TYPES,
    DEFAULT_FIELD_PROPERTIES,
    merge_with_defaults,
)


class WidgetFactory:
    """
    Factory that creates PyQt5 widgets from .iform JSON field definitions.

    Usage::

        factory = WidgetFactory()
        label, widget = factory.create(field_def)
    """

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def create(
        self,
        field_def: dict[str, Any],
        parent: Optional[QWidget] = None,
        show_required: bool = True,
    ) -> tuple[Optional[QLabel], QWidget]:
        """
        Create a label + widget pair from a field definition.

        Args:
            field_def: Merged field definition dict.
            parent: Optional parent widget.
            show_required: Whether to append '*' to labels of required fields.

        Returns:
            Tuple of (label_widget, input_widget).
            For types that don't need a label (separator, button, label),
            the label_widget may be *None*.
        """
        field_def = merge_with_defaults(field_def)
        widget_type = field_def.get("widget_type", "text_input")
        field_id = field_def.get("id", "unknown")

        if widget_type not in SUPPORTED_WIDGET_TYPES:
            app_logger.warning(f"Unsupported widget type '{widget_type}' for field '{field_id}'")
            widget_type = "text_input"

        # Build label
        label_widget = self._create_label(field_def, show_required)

        # Build input widget
        creator = self._CREATORS.get(widget_type, self._create_text_input)
        try:
            input_widget = creator(self, field_def, parent)
        except Exception:
            app_logger.error(
                f"Error creating widget '{field_id}' (type={widget_type})",
                exc_info=True,
            )
            input_widget = QLineEdit(parent)
            input_widget.setPlaceholderText("(error creating widget)")
            input_widget.setEnabled(False)

        # Common setup
        input_widget.setObjectName(field_id)
        self._apply_properties(input_widget, field_def)
        self._apply_style_override(input_widget, field_def)

        return label_widget, input_widget

    # -----------------------------------------------------------------------
    # Label creation
    # -----------------------------------------------------------------------

    def _create_label(
        self,
        field_def: dict[str, Any],
        show_required: bool,
    ) -> Optional[QLabel]:
        """Create a QLabel for the field. Returns None for types without labels."""
        widget_type = field_def.get("widget_type", "")
        if widget_type in ("separator", "button", "label", "progress"):
            return None

        label_text = field_def.get("label_ar") or field_def.get("label_en", "")
        if not label_text:
            return None

        # Check if field is required
        is_required = any(
            r.get("rule") == "required"
            for r in field_def.get("validation", [])
        )

        if show_required and is_required:
            label_text = f"{label_text} *"

        label = QLabel(label_text)
        label.setFont(get_font(size=FONT_SIZE_BODY))
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        if show_required and is_required:
            palette = get_current_palette()
            danger_color = palette.get("danger", "#ef4444")
            label.setStyleSheet(f"QLabel {{ color: {danger_color}; }}")

        return label

    # -----------------------------------------------------------------------
    # Widget creators (one per widget type)
    # -----------------------------------------------------------------------

    def _create_text_input(
        self, field_def: dict[str, Any], parent: Optional[QWidget] = None
    ) -> QLineEdit:
        widget = QLineEdit(parent)
        placeholder = field_def.get("placeholder_ar") or field_def.get("placeholder_en", "")
        if placeholder:
            widget.setPlaceholderText(placeholder)

        props = field_def.get("properties", {})
        mask = props.get("mask")
        if mask:
            widget.setInputMask(mask)

        prefix = props.get("prefix")
        suffix = props.get("suffix")
        if prefix:
            widget.setPlaceholderText(f"{prefix} {widget.placeholderText()}")
        if suffix:
            widget.setPlaceholderText(f"{widget.placeholderText()} {suffix}")

        # Max length from validation
        for rule in field_def.get("validation", []):
            if rule.get("rule") == "max_length":
                max_len = rule.get("value")
                if isinstance(max_len, int) and max_len > 0:
                    widget.setMaxLength(max_len)
                break

        return widget

    def _create_text_area(
        self, field_def: dict[str, Any], parent: Optional[QWidget] = None
    ) -> QTextEdit:
        widget = QTextEdit(parent)
        placeholder = field_def.get("placeholder_ar") or field_def.get("placeholder_en", "")
        if placeholder:
            widget.setPlaceholderText(placeholder)

        layout = field_def.get("layout", {})
        height = layout.get("height")
        if height and isinstance(height, (int, float)):
            widget.setFixedHeight(int(height))
        else:
            widget.setFixedHeight(100)

        return widget

    def _create_number_input(
        self, field_def: dict[str, Any], parent: Optional[QWidget] = None
    ) -> QSpinBox:
        widget = QSpinBox(parent)
        widget.setAlignment(Qt.AlignRight)

        min_val = 0
        max_val = 999999999

        for rule in field_def.get("validation", []):
            rule_name = rule.get("rule")
            value = rule.get("value")
            if rule_name == "min_value" and isinstance(value, (int, float)):
                min_val = int(value)
            elif rule_name == "max_value" and isinstance(value, (int, float)):
                max_val = int(value)

        widget.setMinimum(min_val)
        widget.setMaximum(max_val)

        props = field_def.get("properties", {})
        prefix = props.get("prefix")
        suffix = props.get("suffix")
        if prefix:
            widget.setPrefix(f"{prefix} ")
        if suffix:
            widget.setSuffix(f" {suffix}")

        return widget

    def _create_decimal_input(
        self, field_def: dict[str, Any], parent: Optional[QWidget] = None
    ) -> QDoubleSpinBox:
        widget = QDoubleSpinBox(parent)
        widget.setAlignment(Qt.AlignRight)
        widget.setDecimals(2)

        min_val = 0.0
        max_val = 999999999.99

        for rule in field_def.get("validation", []):
            rule_name = rule.get("rule")
            value = rule.get("value")
            if rule_name == "min_value" and isinstance(value, (int, float)):
                min_val = float(value)
            elif rule_name == "max_value" and isinstance(value, (int, float)):
                max_val = float(value)

        widget.setMinimum(min_val)
        widget.setMaximum(max_val)

        props = field_def.get("properties", {})
        prefix = props.get("prefix")
        suffix = props.get("suffix")
        if prefix:
            widget.setPrefix(f"{prefix} ")
        if suffix:
            widget.setSuffix(f" {suffix}")

        return widget

    def _create_combo_box(
        self, field_def: dict[str, Any], parent: Optional[QWidget] = None
    ) -> QComboBox:
        widget = QComboBox(parent)
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        combo_src = field_def.get("combo_source", {})
        if combo_src:
            default_text = (
                combo_src.get("default_text_ar")
                or combo_src.get("default_text_en")
                or "-- اختر --"
            )
            widget.addItem(default_text, None)

            # Static items
            src_type = combo_src.get("type", "")
            if src_type == "static":
                items = combo_src.get("items", [])
                for item in items:
                    display = item.get("display_ar") or item.get("display_en", "")
                    value = item.get("value")
                    widget.addItem(display, value)

            # Query-based items are loaded asynchronously by FormDataBridge
            # We store the query info as a property on the widget
            if src_type == "query":
                widget.setProperty("combo_query", combo_src.get("query"))
                widget.setProperty("combo_value_col", combo_src.get("value_column", "id"))
                widget.setProperty("combo_display_col", combo_src.get("display_column", "name_ar"))

        return widget

    def _create_check_box(
        self, field_def: dict[str, Any], parent: Optional[QWidget] = None
    ) -> QCheckBox:
        label = field_def.get("label_ar") or field_def.get("label_en", "")
        widget = QCheckBox(label, parent)
        return widget

    def _create_radio_group(
        self, field_def: dict[str, Any], parent: Optional[QWidget] = None
    ) -> QWidget:
        """Create a container widget holding radio buttons in a group."""
        container = QWidget(parent)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        group = QButtonGroup(container)
        group.setExclusive(True)
        container.setProperty("_button_group", group)

        combo_src = field_def.get("combo_source", {})
        if combo_src and combo_src.get("type") == "static":
            items = combo_src.get("items", [])
            for item in items:
                display = item.get("display_ar") or item.get("display_en", "")
                value = item.get("value")
                radio = QRadioButton(display, container)
                radio.setProperty("radio_value", value)
                group.addButton(radio)
                layout.addWidget(radio)

        return container

    def _create_date_picker(
        self, field_def: dict[str, Any], parent: Optional[QWidget] = None
    ) -> QDateEdit:
        widget = QDateEdit(parent)
        widget.setCalendarPopup(True)
        widget.setDate(QDate.currentDate())
        widget.setDisplayFormat("yyyy-MM-dd")
        widget.setAlignment(Qt.AlignRight)
        return widget

    def _create_time_picker(
        self, field_def: dict[str, Any], parent: Optional[QWidget] = None
    ) -> QTimeEdit:
        widget = QTimeEdit(parent)
        widget.setTime(QTime.currentTime())
        widget.setDisplayFormat("HH:mm")
        widget.setAlignment(Qt.AlignRight)
        return widget

    def _create_datetime_picker(
        self, field_def: dict[str, Any], parent: Optional[QWidget] = None
    ) -> QDateTimeEdit:
        widget = QDateTimeEdit(parent)
        widget.setCalendarPopup(True)
        widget.setDateTime(QDateTime.currentDateTime())
        widget.setDisplayFormat("yyyy-MM-dd HH:mm")
        widget.setAlignment(Qt.AlignRight)
        return widget

    def _create_button(
        self, field_def: dict[str, Any], parent: Optional[QWidget] = None
    ) -> QPushButton:
        label = field_def.get("label_ar") or field_def.get("label_en", "Button")
        widget = QPushButton(label, parent)
        return widget

    def _create_label_widget(
        self, field_def: dict[str, Any], parent: Optional[QWidget] = None
    ) -> QLabel:
        text = field_def.get("label_ar") or field_def.get("label_en", "")
        widget = QLabel(text, parent)
        widget.setWordWrap(True)
        return widget

    def _create_separator(
        self, field_def: dict[str, Any], parent: Optional[QWidget] = None
    ) -> QFrame:
        widget = QFrame(parent)
        widget.setFrameShape(QFrame.HLine)
        widget.setFrameShadow(QFrame.Sunken)
        widget.setFixedHeight(2)
        return widget

    def _create_image(
        self, field_def: dict[str, Any], parent: Optional[QWidget] = None
    ) -> QLabel:
        widget = QLabel(parent)
        widget.setAlignment(Qt.AlignCenter)

        props = field_def.get("properties", {})
        icon_path = props.get("icon")
        if icon_path:
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                layout = field_def.get("layout", {})
                w = layout.get("width", 64)
                h = layout.get("height", 64)
                widget.setPixmap(
                    pixmap.scaled(
                        int(w) if w else 64,
                        int(h) if h else 64,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                )
        else:
            widget.setText("(no image)")
            widget.setStyleSheet("border: 1px dashed gray; padding: 10px;")

        return widget

    def _create_group_box(
        self, field_def: dict[str, Any], parent: Optional[QWidget] = None
    ) -> QGroupBox:
        title = field_def.get("label_ar") or field_def.get("label_en", "")
        widget = QGroupBox(title, parent)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        return widget

    def _create_table(
        self, field_def: dict[str, Any], parent: Optional[QWidget] = None
    ) -> QTableWidget:
        widget = QTableWidget(parent)
        widget.setAlternatingRowColors(True)

        props = field_def.get("properties", {})
        cols = props.get("columns", [])
        if cols:
            widget.setColumnCount(len(cols))
            headers = [
                c.get("header_ar") or c.get("header_en", f"Col {i}")
                for i, c in enumerate(cols)
            ]
            widget.setHorizontalHeaderLabels(headers)

        return widget

    def _create_file_picker(
        self, field_def: dict[str, Any], parent: Optional[QWidget] = None
    ) -> QWidget:
        container = QWidget(parent)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        line_edit = QLineEdit(container)
        line_edit.setReadOnly(True)
        line_edit.setObjectName(f"{field_def.get('id', '')}_path")

        browse_btn = QPushButton("...", container)
        browse_btn.setFixedWidth(40)

        def _browse() -> None:
            path, _ = QFileDialog.getOpenFileName(
                container, "اختر ملف", "", "All Files (*)"
            )
            if path:
                line_edit.setText(path)

        browse_btn.clicked.connect(_browse)

        layout.addWidget(line_edit, 1)
        layout.addWidget(browse_btn, 0)

        return container

    def _create_color_picker(
        self, field_def: dict[str, Any], parent: Optional[QWidget] = None
    ) -> QPushButton:
        widget = QPushButton(parent)
        widget.setFixedHeight(35)
        widget.setText(field_def.get("label_ar", "اختر لون"))

        current_color = "#ffffff"
        widget.setProperty("selected_color", current_color)
        widget.setStyleSheet(
            f"background-color: {current_color}; border: 1px solid #ccc;"
        )

        def _pick_color() -> None:
            color = QColorDialog.getColor(
                QColor(widget.property("selected_color") or "#ffffff"),
                widget,
                "اختر لون",
            )
            if color.isValid():
                hex_color = color.name()
                widget.setProperty("selected_color", hex_color)
                widget.setStyleSheet(
                    f"background-color: {hex_color}; border: 1px solid #ccc;"
                )

        widget.clicked.connect(_pick_color)
        return widget

    def _create_slider(
        self, field_def: dict[str, Any], parent: Optional[QWidget] = None
    ) -> QSlider:
        widget = QSlider(Qt.Horizontal, parent)

        min_val = 0
        max_val = 100
        for rule in field_def.get("validation", []):
            rule_name = rule.get("rule")
            value = rule.get("value")
            if rule_name == "min_value" and isinstance(value, (int, float)):
                min_val = int(value)
            elif rule_name == "max_value" and isinstance(value, (int, float)):
                max_val = int(value)

        widget.setMinimum(min_val)
        widget.setMaximum(max_val)
        return widget

    def _create_progress(
        self, field_def: dict[str, Any], parent: Optional[QWidget] = None
    ) -> QProgressBar:
        widget = QProgressBar(parent)
        widget.setMinimum(0)
        widget.setMaximum(100)
        widget.setValue(0)
        widget.setAlignment(Qt.AlignCenter)
        return widget

    def _create_rich_text(
        self, field_def: dict[str, Any], parent: Optional[QWidget] = None
    ) -> QTextEdit:
        widget = QTextEdit(parent)
        widget.setAcceptRichText(True)
        placeholder = field_def.get("placeholder_ar") or field_def.get("placeholder_en", "")
        if placeholder:
            widget.setPlaceholderText(placeholder)

        layout = field_def.get("layout", {})
        height = layout.get("height")
        if height and isinstance(height, (int, float)):
            widget.setFixedHeight(int(height))
        else:
            widget.setFixedHeight(150)

        return widget

    # -----------------------------------------------------------------------
    # Creator registry
    # -----------------------------------------------------------------------

    _CREATORS: dict[str, Callable] = {
        "text_input": _create_text_input,
        "text_area": _create_text_area,
        "number_input": _create_number_input,
        "decimal_input": _create_decimal_input,
        "combo_box": _create_combo_box,
        "check_box": _create_check_box,
        "radio_group": _create_radio_group,
        "date_picker": _create_date_picker,
        "time_picker": _create_time_picker,
        "datetime_picker": _create_datetime_picker,
        "button": _create_button,
        "label": _create_label_widget,
        "separator": _create_separator,
        "image": _create_image,
        "group_box": _create_group_box,
        "table": _create_table,
        "file_picker": _create_file_picker,
        "color_picker": _create_color_picker,
        "slider": _create_slider,
        "progress": _create_progress,
        "rich_text": _create_rich_text,
    }

    # -----------------------------------------------------------------------
    # Internals – property & style application
    # -----------------------------------------------------------------------

    @staticmethod
    def _apply_properties(widget: QWidget, field_def: dict[str, Any]) -> None:
        """Apply common properties (readonly, enabled, visible, tooltip)."""
        props = field_def.get("properties", {})

        # Enabled
        enabled = props.get("enabled", True)
        widget.setEnabled(bool(enabled))

        # Visible
        visible = props.get("visible", True)
        widget.setVisible(bool(visible))

        # Readonly
        readonly = props.get("readonly", False)
        if readonly:
            if hasattr(widget, "setReadOnly"):
                widget.setReadOnly(True)
            else:
                widget.setEnabled(False)

        # Tooltip
        tooltip = props.get("tooltip_ar") or props.get("tooltip_en", "")
        if tooltip:
            widget.setToolTip(tooltip)

        # Font
        widget.setFont(get_font(size=FONT_SIZE_BODY))

    @staticmethod
    def _apply_style_override(widget: QWidget, field_def: dict[str, Any]) -> None:
        """Apply optional style overrides on top of the theme."""
        style = field_def.get("style_override", {})
        if not style:
            return

        parts: list[str] = []

        font_size = style.get("font_size")
        if font_size is not None:
            parts.append(f"font-size: {int(font_size)}px;")

        font_weight = style.get("font_weight")
        if font_weight is not None:
            parts.append(f"font-weight: {font_weight};")

        text_color = style.get("text_color")
        if text_color:
            parts.append(f"color: {text_color};")

        background = style.get("background")
        if background:
            parts.append(f"background-color: {background};")

        border_color = style.get("border_color")
        if border_color:
            parts.append(f"border-color: {border_color};")

        border_radius = style.get("border_radius")
        if border_radius is not None:
            parts.append(f"border-radius: {int(border_radius)}px;")

        custom_css = style.get("custom_css")
        if custom_css:
            parts.append(custom_css)

        if parts:
            class_name = type(widget).__name__
            existing = widget.styleSheet()
            new_style = f"{class_name} {{ {' '.join(parts)} }}"
            widget.setStyleSheet(f"{existing}\n{new_style}" if existing else new_style)


# ---------------------------------------------------------------------------
# Value getters / setters (used by FormRenderer for data binding)
# ---------------------------------------------------------------------------

def get_widget_value(widget: QWidget, widget_type: str) -> Any:
    """
    Extract the current value from a widget based on its type.

    Returns the Python value appropriate for the widget type.
    """
    if widget_type == "text_input":
        return widget.text() if isinstance(widget, QLineEdit) else ""

    if widget_type == "text_area" or widget_type == "rich_text":
        return widget.toPlainText() if isinstance(widget, QTextEdit) else ""

    if widget_type == "number_input":
        return widget.value() if isinstance(widget, QSpinBox) else 0

    if widget_type == "decimal_input":
        return widget.value() if isinstance(widget, QDoubleSpinBox) else 0.0

    if widget_type == "combo_box":
        if isinstance(widget, QComboBox):
            return widget.currentData()
        return None

    if widget_type == "check_box":
        return widget.isChecked() if isinstance(widget, QCheckBox) else False

    if widget_type == "radio_group":
        group = widget.property("_button_group")
        if isinstance(group, QButtonGroup):
            checked = group.checkedButton()
            if checked:
                return checked.property("radio_value")
        return None

    if widget_type == "date_picker":
        if isinstance(widget, QDateEdit):
            return widget.date().toString("yyyy-MM-dd")
        return None

    if widget_type == "time_picker":
        if isinstance(widget, QTimeEdit):
            return widget.time().toString("HH:mm")
        return None

    if widget_type == "datetime_picker":
        if isinstance(widget, QDateTimeEdit):
            return widget.dateTime().toString("yyyy-MM-dd HH:mm")
        return None

    if widget_type == "slider":
        return widget.value() if isinstance(widget, QSlider) else 0

    if widget_type == "color_picker":
        return widget.property("selected_color") if isinstance(widget, QPushButton) else None

    if widget_type == "file_picker":
        path_edit = widget.findChild(QLineEdit)
        return path_edit.text() if path_edit else ""

    return None


def set_widget_value(widget: QWidget, widget_type: str, value: Any) -> None:
    """
    Set the value of a widget based on its type.
    """
    if value is None:
        return

    try:
        if widget_type == "text_input" and isinstance(widget, QLineEdit):
            widget.setText(str(value))

        elif widget_type in ("text_area", "rich_text") and isinstance(widget, QTextEdit):
            widget.setPlainText(str(value))

        elif widget_type == "number_input" and isinstance(widget, QSpinBox):
            widget.setValue(int(value))

        elif widget_type == "decimal_input" and isinstance(widget, QDoubleSpinBox):
            widget.setValue(float(value))

        elif widget_type == "combo_box" and isinstance(widget, QComboBox):
            for i in range(widget.count()):
                if widget.itemData(i) == value:
                    widget.setCurrentIndex(i)
                    break

        elif widget_type == "check_box" and isinstance(widget, QCheckBox):
            widget.setChecked(bool(value))

        elif widget_type == "radio_group":
            group = widget.property("_button_group")
            if isinstance(group, QButtonGroup):
                for btn in group.buttons():
                    if btn.property("radio_value") == value:
                        btn.setChecked(True)
                        break

        elif widget_type == "date_picker" and isinstance(widget, QDateEdit):
            date = QDate.fromString(str(value), "yyyy-MM-dd")
            if date.isValid():
                widget.setDate(date)

        elif widget_type == "time_picker" and isinstance(widget, QTimeEdit):
            time = QTime.fromString(str(value), "HH:mm")
            if time.isValid():
                widget.setTime(time)

        elif widget_type == "datetime_picker" and isinstance(widget, QDateTimeEdit):
            dt = QDateTime.fromString(str(value), "yyyy-MM-dd HH:mm")
            if dt.isValid():
                widget.setDateTime(dt)

        elif widget_type == "slider" and isinstance(widget, QSlider):
            widget.setValue(int(value))

        elif widget_type == "color_picker" and isinstance(widget, QPushButton):
            widget.setProperty("selected_color", str(value))
            widget.setStyleSheet(
                f"background-color: {value}; border: 1px solid #ccc;"
            )

        elif widget_type == "file_picker":
            path_edit = widget.findChild(QLineEdit)
            if path_edit:
                path_edit.setText(str(value))

        elif widget_type == "progress" and isinstance(widget, QProgressBar):
            widget.setValue(int(value))

    except (ValueError, TypeError):
        app_logger.warning(
            f"Could not set value '{value}' on widget type '{widget_type}'"
        )


def connect_change_signal(
    widget: QWidget,
    widget_type: str,
    callback: Callable[[], None],
) -> None:
    """
    Connect the appropriate change signal of a widget to a callback.

    This is used by FormRenderer for dirty-tracking.
    """
    try:
        if widget_type == "text_input" and isinstance(widget, QLineEdit):
            widget.textChanged.connect(callback)

        elif widget_type in ("text_area", "rich_text") and isinstance(widget, QTextEdit):
            widget.textChanged.connect(callback)

        elif widget_type == "number_input" and isinstance(widget, QSpinBox):
            widget.valueChanged.connect(callback)

        elif widget_type == "decimal_input" and isinstance(widget, QDoubleSpinBox):
            widget.valueChanged.connect(callback)

        elif widget_type == "combo_box" and isinstance(widget, QComboBox):
            widget.currentIndexChanged.connect(callback)

        elif widget_type == "check_box" and isinstance(widget, QCheckBox):
            widget.stateChanged.connect(callback)

        elif widget_type == "radio_group":
            group = widget.property("_button_group")
            if isinstance(group, QButtonGroup):
                group.buttonClicked.connect(callback)

        elif widget_type == "date_picker" and isinstance(widget, QDateEdit):
            widget.dateChanged.connect(callback)

        elif widget_type == "time_picker" and isinstance(widget, QTimeEdit):
            widget.timeChanged.connect(callback)

        elif widget_type == "datetime_picker" and isinstance(widget, QDateTimeEdit):
            widget.dateTimeChanged.connect(callback)

        elif widget_type == "slider" and isinstance(widget, QSlider):
            widget.valueChanged.connect(callback)

    except Exception:
        app_logger.warning(
            f"Could not connect change signal for widget type '{widget_type}'",
            exc_info=True,
        )
