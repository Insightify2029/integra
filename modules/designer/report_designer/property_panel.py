"""
Property Panel
==============
Properties editor for selected report elements.

Features:
- Dynamic property editing
- Font settings
- Colors and borders
- Alignment options
- Data binding
"""

from typing import Optional, Any, Dict, Callable
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QPushButton,
    QColorDialog, QFontDialog, QFrame, QScrollArea, QGridLayout,
    QGroupBox, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont

from core.logging import app_logger

from .design_canvas import CanvasElement, ElementType, ElementStyle


class ColorButton(QPushButton):
    """Button that shows and selects a color."""

    color_changed = pyqtSignal(str)  # Hex color

    def __init__(self, color: str = "#000000", parent=None):
        super().__init__(parent)
        self._color = color
        self._update_style()
        self.clicked.connect(self._pick_color)
        self.setFixedSize(60, 25)

    def _update_style(self) -> None:
        """Update button style."""
        self.setStyleSheet(f"""
            QPushButton {{
                background: {self._color};
                border: 1px solid #d1d5db;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border-color: #2563eb;
            }}
        """)
        self.setToolTip(self._color)

    def _pick_color(self) -> None:
        """Open color picker."""
        color = QColorDialog.getColor(QColor(self._color), self, "اختر اللون")
        if color.isValid():
            self._color = color.name()
            self._update_style()
            self.color_changed.emit(self._color)

    def get_color(self) -> str:
        """Get current color."""
        return self._color

    def set_color(self, color: str) -> None:
        """Set color."""
        self._color = color
        self._update_style()


class PropertyGroup(QGroupBox):
    """Group of related properties."""

    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(10, 15, 10, 10)
        self._layout.setSpacing(8)
        self._row = 0

        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top right;
                padding: 0 8px;
                color: #374151;
            }
        """)

    def add_property(self, label: str, widget: QWidget) -> None:
        """Add property row."""
        lbl = QLabel(label)
        lbl.setStyleSheet("font-weight: normal; color: #6b7280;")
        self._layout.addWidget(lbl, self._row, 0)
        self._layout.addWidget(widget, self._row, 1)
        self._row += 1


class PropertyPanel(QWidget):
    """
    Property panel for editing selected element properties.

    Signals:
        property_changed: Emitted when a property is changed
    """

    property_changed = pyqtSignal(object)  # CanvasElement

    def __init__(self, parent=None):
        super().__init__(parent)

        self._current_element: Optional[CanvasElement] = None
        self._updating = False  # Prevent recursive updates

        self._setup_ui()
        self.set_element(None)

    def _setup_ui(self) -> None:
        """Setup panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Title
        self._title_label = QLabel("الخصائص")
        self._title_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #1f2937;
            padding: 5px;
        """)
        layout.addWidget(self._title_label)

        # No selection message
        self._no_selection = QLabel("اختر عنصراً لتعديل خصائصه")
        self._no_selection.setStyleSheet("color: #9ca3af; padding: 20px;")
        self._no_selection.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._no_selection)

        # Scroll area for properties
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        # Properties container
        self._properties_widget = QWidget()
        self._properties_layout = QVBoxLayout(self._properties_widget)
        self._properties_layout.setContentsMargins(0, 0, 5, 0)
        self._properties_layout.setSpacing(10)

        # ---- General Properties ----
        self._general_group = PropertyGroup("عام")

        # Element type (read-only)
        self._type_label = QLabel()
        self._type_label.setStyleSheet("color: #2563eb; font-weight: bold;")
        self._general_group.add_property("النوع:", self._type_label)

        # ID (read-only)
        self._id_label = QLabel()
        self._id_label.setStyleSheet("color: #6b7280;")
        self._general_group.add_property("المعرّف:", self._id_label)

        self._properties_layout.addWidget(self._general_group)

        # ---- Position & Size ----
        self._position_group = PropertyGroup("الموضع والحجم")

        # X position
        self._x_spin = QSpinBox()
        self._x_spin.setRange(0, 2000)
        self._x_spin.setSuffix(" px")
        self._x_spin.valueChanged.connect(self._on_position_changed)
        self._position_group.add_property("X:", self._x_spin)

        # Y position
        self._y_spin = QSpinBox()
        self._y_spin.setRange(0, 3000)
        self._y_spin.setSuffix(" px")
        self._y_spin.valueChanged.connect(self._on_position_changed)
        self._position_group.add_property("Y:", self._y_spin)

        # Width
        self._width_spin = QSpinBox()
        self._width_spin.setRange(10, 2000)
        self._width_spin.setSuffix(" px")
        self._width_spin.valueChanged.connect(self._on_size_changed)
        self._position_group.add_property("العرض:", self._width_spin)

        # Height
        self._height_spin = QSpinBox()
        self._height_spin.setRange(10, 2000)
        self._height_spin.setSuffix(" px")
        self._height_spin.valueChanged.connect(self._on_size_changed)
        self._position_group.add_property("الارتفاع:", self._height_spin)

        self._properties_layout.addWidget(self._position_group)

        # ---- Content ----
        self._content_group = PropertyGroup("المحتوى")

        # Content text
        self._content_edit = QLineEdit()
        self._content_edit.setPlaceholderText("أدخل النص...")
        self._content_edit.textChanged.connect(self._on_content_changed)
        self._content_group.add_property("النص:", self._content_edit)

        # Field name (for field elements)
        self._field_combo = QComboBox()
        self._field_combo.setEditable(True)
        self._field_combo.addItems([
            "employee_name", "employee_number", "department",
            "job_title", "salary", "hire_date", "phone", "email"
        ])
        self._field_combo.currentTextChanged.connect(self._on_field_changed)
        self._content_group.add_property("الحقل:", self._field_combo)

        self._properties_layout.addWidget(self._content_group)

        # ---- Font ----
        self._font_group = PropertyGroup("الخط")

        # Font family
        self._font_family = QComboBox()
        self._font_family.addItems(["Cairo", "Arial", "Tahoma", "Times New Roman"])
        self._font_family.currentTextChanged.connect(self._on_style_changed)
        self._font_group.add_property("نوع الخط:", self._font_family)

        # Font size
        self._font_size = QSpinBox()
        self._font_size.setRange(6, 72)
        self._font_size.setValue(12)
        self._font_size.valueChanged.connect(self._on_style_changed)
        self._font_group.add_property("الحجم:", self._font_size)

        # Font color
        self._font_color = ColorButton("#000000")
        self._font_color.color_changed.connect(self._on_style_changed)
        self._font_group.add_property("اللون:", self._font_color)

        # Bold, Italic, Underline
        style_widget = QWidget()
        style_layout = QHBoxLayout(style_widget)
        style_layout.setContentsMargins(0, 0, 0, 0)
        style_layout.setSpacing(5)

        self._bold_check = QCheckBox("عريض")
        self._bold_check.stateChanged.connect(self._on_style_changed)
        style_layout.addWidget(self._bold_check)

        self._italic_check = QCheckBox("مائل")
        self._italic_check.stateChanged.connect(self._on_style_changed)
        style_layout.addWidget(self._italic_check)

        self._underline_check = QCheckBox("تحته خط")
        self._underline_check.stateChanged.connect(self._on_style_changed)
        style_layout.addWidget(self._underline_check)

        style_layout.addStretch()
        self._font_group.add_property("التنسيق:", style_widget)

        self._properties_layout.addWidget(self._font_group)

        # ---- Alignment ----
        self._align_group = PropertyGroup("المحاذاة")

        self._alignment = QComboBox()
        self._alignment.addItem("يمين", "right")
        self._alignment.addItem("وسط", "center")
        self._alignment.addItem("يسار", "left")
        self._alignment.currentIndexChanged.connect(self._on_style_changed)
        self._align_group.add_property("المحاذاة:", self._alignment)

        self._properties_layout.addWidget(self._align_group)

        # ---- Background & Border ----
        self._appearance_group = PropertyGroup("المظهر")

        # Background color
        self._bg_color = ColorButton("#ffffff")
        self._bg_color.color_changed.connect(self._on_style_changed)
        self._appearance_group.add_property("لون الخلفية:", self._bg_color)

        # Border color
        self._border_color = ColorButton("#cccccc")
        self._border_color.color_changed.connect(self._on_style_changed)
        self._appearance_group.add_property("لون الحد:", self._border_color)

        # Border width
        self._border_width = QDoubleSpinBox()
        self._border_width.setRange(0, 10)
        self._border_width.setValue(0)
        self._border_width.setSuffix(" px")
        self._border_width.valueChanged.connect(self._on_style_changed)
        self._appearance_group.add_property("عرض الحد:", self._border_width)

        self._properties_layout.addWidget(self._appearance_group)

        self._properties_layout.addStretch()

        scroll.setWidget(self._properties_widget)
        layout.addWidget(scroll)

        # Initially hide properties
        self._properties_widget.hide()

        # Style
        self.setStyleSheet("""
            PropertyPanel {
                background: #ffffff;
                border-right: 1px solid #e5e7eb;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                padding: 5px;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                background: white;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border-color: #2563eb;
            }
            QCheckBox {
                font-size: 11px;
            }
        """)

        self.setMinimumWidth(250)
        self.setMaximumWidth(300)

    def set_element(self, element: Optional[CanvasElement]) -> None:
        """
        Set the element to edit.

        Args:
            element: Element to edit, or None to clear
        """
        self._current_element = element

        if element is None:
            self._no_selection.show()
            self._properties_widget.hide()
            self._title_label.setText("الخصائص")
            return

        self._no_selection.hide()
        self._properties_widget.show()

        self._updating = True  # Prevent signals during update

        # Update title
        type_names = {
            ElementType.TEXT: "نص",
            ElementType.FIELD: "حقل بيانات",
            ElementType.TABLE: "جدول",
            ElementType.IMAGE: "صورة",
            ElementType.LINE: "خط",
            ElementType.RECTANGLE: "مستطيل",
            ElementType.CHART: "رسم بياني",
            ElementType.BARCODE: "باركود",
            ElementType.FORMULA: "صيغة"
        }
        self._title_label.setText(f"خصائص: {type_names.get(element.element_type, 'عنصر')}")

        # General
        self._type_label.setText(type_names.get(element.element_type, element.element_type.value))
        self._id_label.setText(element.id)

        # Position & Size
        self._x_spin.setValue(int(element.x))
        self._y_spin.setValue(int(element.y))
        self._width_spin.setValue(int(element.width))
        self._height_spin.setValue(int(element.height))

        # Content
        self._content_edit.setText(str(element.content or ""))

        # Field name
        field_name = element.properties.get("field_name", "")
        idx = self._field_combo.findText(field_name)
        if idx >= 0:
            self._field_combo.setCurrentIndex(idx)
        else:
            self._field_combo.setCurrentText(field_name)

        # Show/hide field combo based on element type
        self._field_combo.setVisible(element.element_type == ElementType.FIELD)

        # Font
        self._font_family.setCurrentText(element.style.font_family)
        self._font_size.setValue(element.style.font_size)
        self._font_color.set_color(element.style.font_color)
        self._bold_check.setChecked(element.style.bold)
        self._italic_check.setChecked(element.style.italic)
        self._underline_check.setChecked(element.style.underline)

        # Alignment
        align_idx = {"right": 0, "center": 1, "left": 2}.get(element.style.alignment, 0)
        self._alignment.setCurrentIndex(align_idx)

        # Appearance
        self._bg_color.set_color(element.style.background_color or "#ffffff")
        self._border_color.set_color(element.style.border_color or "#cccccc")
        self._border_width.setValue(element.style.border_width)

        self._updating = False

    def _on_position_changed(self) -> None:
        """Handle position change."""
        if self._updating or not self._current_element:
            return

        self._current_element.x = self._x_spin.value()
        self._current_element.y = self._y_spin.value()
        self.property_changed.emit(self._current_element)

    def _on_size_changed(self) -> None:
        """Handle size change."""
        if self._updating or not self._current_element:
            return

        self._current_element.width = self._width_spin.value()
        self._current_element.height = self._height_spin.value()
        self.property_changed.emit(self._current_element)

    def _on_content_changed(self) -> None:
        """Handle content change."""
        if self._updating or not self._current_element:
            return

        self._current_element.content = self._content_edit.text()
        self.property_changed.emit(self._current_element)

    def _on_field_changed(self) -> None:
        """Handle field name change."""
        if self._updating or not self._current_element:
            return

        self._current_element.properties["field_name"] = self._field_combo.currentText()
        self.property_changed.emit(self._current_element)

    def _on_style_changed(self) -> None:
        """Handle style change."""
        if self._updating or not self._current_element:
            return

        style = self._current_element.style

        style.font_family = self._font_family.currentText()
        style.font_size = self._font_size.value()
        style.font_color = self._font_color.get_color()
        style.bold = self._bold_check.isChecked()
        style.italic = self._italic_check.isChecked()
        style.underline = self._underline_check.isChecked()

        style.alignment = self._alignment.currentData() or "right"

        style.background_color = self._bg_color.get_color()
        style.border_color = self._border_color.get_color()
        style.border_width = self._border_width.value()

        self.property_changed.emit(self._current_element)
