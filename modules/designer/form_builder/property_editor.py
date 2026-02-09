"""
Form Property Editor
====================
Property editor panel for form builder widgets.

Features:
- General properties (label, name, etc.)
- Style properties (font, colors, borders)
- Validation rules
- Data binding configuration
"""

from typing import Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QSpinBox,
    QComboBox, QCheckBox, QPushButton, QScrollArea,
    QGroupBox, QGridLayout, QColorDialog, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

from core.logging import app_logger
from core.themes import get_current_palette
from .form_canvas import FormWidget, WidgetType, ValidationRule


class ColorButton(QPushButton):
    """Color picker button."""

    color_changed = pyqtSignal(str)

    def __init__(self, color: str = "#000000", parent=None):
        super().__init__(parent)
        self._color = color
        self._update_style()
        self.clicked.connect(self._pick_color)
        self.setFixedSize(60, 25)

    def _update_style(self) -> None:
        p = get_current_palette()
        self.setStyleSheet(f"""
            QPushButton {{
                background: {self._color};
                border: 1px solid {p['border']};
                border-radius: 4px;
            }}
        """)

    def _pick_color(self) -> None:
        color = QColorDialog.getColor(QColor(self._color), self)
        if color.isValid():
            self._color = color.name()
            self._update_style()
            self.color_changed.emit(self._color)

    def get_color(self) -> str:
        return self._color

    def set_color(self, color: str) -> None:
        self._color = color
        self._update_style()


class PropertyGroup(QGroupBox):
    """Property group container."""

    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(10, 15, 10, 10)
        self._layout.setSpacing(8)
        self._row = 0

        p = get_current_palette()
        self.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {p['border']};
                border-radius: 6px;
                margin-top: 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top right;
                padding: 0 8px;
            }}
        """)

    def add_property(self, label: str, widget: QWidget) -> None:
        p = get_current_palette()
        lbl = QLabel(label)
        lbl.setStyleSheet(f"font-weight: normal; color: {p['text_muted']};")
        self._layout.addWidget(lbl, self._row, 0)
        self._layout.addWidget(widget, self._row, 1)
        self._row += 1


class FormPropertyEditor(QWidget):
    """
    Property editor for form widgets.

    Signals:
        property_changed: Emitted when property changes
    """

    property_changed = pyqtSignal(object)  # FormWidget

    def __init__(self, parent=None):
        super().__init__(parent)

        self._current_widget: Optional[FormWidget] = None
        self._updating = False

        self._setup_ui()
        self.set_widget(None)

    def _setup_ui(self) -> None:
        """Setup editor UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Title
        p = get_current_palette()
        self._title = QLabel("الخصائص")
        self._title.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {p['text_primary']};
        """)
        layout.addWidget(self._title)

        # No selection message
        self._no_selection = QLabel("اختر عنصراً لتعديل خصائصه")
        self._no_selection.setStyleSheet(f"color: {p['text_muted']}; padding: 20px;")
        self._no_selection.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._no_selection)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        self._props_widget = QWidget()
        self._props_layout = QVBoxLayout(self._props_widget)
        self._props_layout.setContentsMargins(0, 0, 5, 0)
        self._props_layout.setSpacing(10)

        # General Properties
        self._general = PropertyGroup("عام")

        self._id_label = QLabel()
        self._id_label.setStyleSheet(f"color: {p['text_muted']};")
        self._general.add_property("المعرّف:", self._id_label)

        self._type_label = QLabel()
        self._type_label.setStyleSheet(f"color: {p['primary']}; font-weight: bold;")
        self._general.add_property("النوع:", self._type_label)

        self._label_edit = QLineEdit()
        self._label_edit.textChanged.connect(self._on_property_changed)
        self._general.add_property("العنوان:", self._label_edit)

        self._placeholder_edit = QLineEdit()
        self._placeholder_edit.textChanged.connect(self._on_property_changed)
        self._general.add_property("النص الإرشادي:", self._placeholder_edit)

        self._props_layout.addWidget(self._general)

        # Position & Size
        self._position = PropertyGroup("الموضع والحجم")

        self._x_spin = QSpinBox()
        self._x_spin.setRange(0, 2000)
        self._x_spin.valueChanged.connect(self._on_property_changed)
        self._position.add_property("X:", self._x_spin)

        self._y_spin = QSpinBox()
        self._y_spin.setRange(0, 2000)
        self._y_spin.valueChanged.connect(self._on_property_changed)
        self._position.add_property("Y:", self._y_spin)

        self._width_spin = QSpinBox()
        self._width_spin.setRange(20, 1000)
        self._width_spin.valueChanged.connect(self._on_property_changed)
        self._position.add_property("العرض:", self._width_spin)

        self._height_spin = QSpinBox()
        self._height_spin.setRange(20, 500)
        self._height_spin.valueChanged.connect(self._on_property_changed)
        self._position.add_property("الارتفاع:", self._height_spin)

        self._props_layout.addWidget(self._position)

        # Style Properties
        self._style = PropertyGroup("التنسيق")

        self._font_family = QComboBox()
        self._font_family.addItems(["Cairo", "Arial", "Tahoma"])
        self._font_family.currentTextChanged.connect(self._on_property_changed)
        self._style.add_property("الخط:", self._font_family)

        self._font_size = QSpinBox()
        self._font_size.setRange(8, 48)
        self._font_size.valueChanged.connect(self._on_property_changed)
        self._style.add_property("الحجم:", self._font_size)

        self._font_color = ColorButton("#000000")
        self._font_color.color_changed.connect(self._on_property_changed)
        self._style.add_property("اللون:", self._font_color)

        self._bg_color = ColorButton("#ffffff")
        self._bg_color.color_changed.connect(self._on_property_changed)
        self._style.add_property("الخلفية:", self._bg_color)

        self._props_layout.addWidget(self._style)

        # Data Binding
        self._data = PropertyGroup("ربط البيانات")

        self._binding_combo = QComboBox()
        self._binding_combo.setEditable(True)
        self._binding_combo.addItems([
            "", "employees.name_ar", "employees.employee_number",
            "employees.department", "employees.salary", "employees.phone"
        ])
        self._binding_combo.currentTextChanged.connect(self._on_property_changed)
        self._data.add_property("الحقل:", self._binding_combo)

        self._props_layout.addWidget(self._data)

        # Validation
        self._validation = PropertyGroup("التحقق")

        self._required = QCheckBox("مطلوب")
        self._required.stateChanged.connect(self._on_property_changed)
        self._validation.add_property("", self._required)

        self._props_layout.addWidget(self._validation)

        self._props_layout.addStretch()

        scroll.setWidget(self._props_widget)
        layout.addWidget(scroll)

        self._props_widget.hide()

        # Style
        self.setStyleSheet(f"""
            FormPropertyEditor {{
                background: {p['bg_card']};
                border-right: 1px solid {p['border']};
            }}
            QLineEdit, QSpinBox, QComboBox {{
                padding: 5px;
                border: 1px solid {p['border']};
                border-radius: 4px;
            }}
        """)

        self.setMinimumWidth(250)
        self.setMaximumWidth(300)

    def set_widget(self, widget: Optional[FormWidget]) -> None:
        """Set widget to edit."""
        self._current_widget = widget

        if widget is None:
            self._no_selection.show()
            self._props_widget.hide()
            self._title.setText("الخصائص")
            return

        self._no_selection.hide()
        self._props_widget.show()

        self._updating = True

        # Type names
        type_names = {
            WidgetType.LABEL: "نص",
            WidgetType.TEXT_INPUT: "حقل نصي",
            WidgetType.TEXT_AREA: "منطقة نص",
            WidgetType.NUMBER_INPUT: "رقم",
            WidgetType.COMBO_BOX: "قائمة",
            WidgetType.CHECK_BOX: "اختيار",
            WidgetType.BUTTON: "زر",
            WidgetType.DATE_PICKER: "تاريخ",
        }

        self._title.setText(f"خصائص: {type_names.get(widget.widget_type, 'عنصر')}")
        self._id_label.setText(widget.id)
        self._type_label.setText(type_names.get(widget.widget_type, widget.widget_type.value))

        self._label_edit.setText(widget.label)
        self._placeholder_edit.setText(widget.placeholder)

        self._x_spin.setValue(widget.x)
        self._y_spin.setValue(widget.y)
        self._width_spin.setValue(widget.width)
        self._height_spin.setValue(widget.height)

        self._font_family.setCurrentText(widget.style.font_family)
        self._font_size.setValue(widget.style.font_size)
        self._font_color.set_color(widget.style.font_color)
        self._bg_color.set_color(widget.style.background_color)

        self._binding_combo.setCurrentText(widget.data_binding or "")

        has_required = any(v.rule_type == "required" for v in widget.validation)
        self._required.setChecked(has_required)

        self._updating = False

    def _on_property_changed(self) -> None:
        """Handle property change."""
        if self._updating or not self._current_widget:
            return

        w = self._current_widget

        w.label = self._label_edit.text()
        w.placeholder = self._placeholder_edit.text()

        w.x = self._x_spin.value()
        w.y = self._y_spin.value()
        w.width = self._width_spin.value()
        w.height = self._height_spin.value()

        w.style.font_family = self._font_family.currentText()
        w.style.font_size = self._font_size.value()
        w.style.font_color = self._font_color.get_color()
        w.style.background_color = self._bg_color.get_color()

        w.data_binding = self._binding_combo.currentText() or None

        # Update validation
        w.validation = []
        if self._required.isChecked():
            w.validation.append(ValidationRule("required", message="هذا الحقل مطلوب"))

        self.property_changed.emit(w)
