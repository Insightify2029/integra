"""
Form Property Editor (Enhanced - Phase 2)
==========================================
Property editor panel for form builder widgets.

Enhanced with QTabWidget containing 6 tabs:
1. General (عام) - ID, Type, Label, Placeholder, Tooltip
2. Layout (تخطيط) - Position, Size, Grid, Alignment
3. Format (تنسيق) - Font, Colors, Border, Custom CSS
4. Data (بيانات) - Table, Column, Data Type, Format
5. Validation (تحقق) - Required, Rules list
6. Advanced (متقدم) - Default, Visibility, Conditions
"""

from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox,
    QComboBox, QCheckBox, QPushButton, QScrollArea, QTabWidget,
    QGroupBox, QGridLayout, QColorDialog, QTextEdit, QListWidget,
    QListWidgetItem, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont

from core.logging import app_logger
from core.themes import get_current_palette
from .form_canvas import FormWidget, WidgetType, ValidationRule


# ---------------------------------------------------------------------------
# ColorButton
# ---------------------------------------------------------------------------

class ColorButton(QPushButton):
    """Color picker button."""

    color_changed = pyqtSignal(str)

    def __init__(self, color: str = "#000000", parent=None):
        super().__init__(parent)
        self._color = color
        self._update_style()
        self.clicked.connect(self._pick_color)
        self.setFixedSize(int(60), int(25))

    def _update_style(self) -> None:
        p = get_current_palette()
        self.setStyleSheet(f"""
            QPushButton {{
                background: {self._color};
                border: 1px solid {p['border']};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border-color: {p['primary']};
            }}
        """)
        self.setToolTip(self._color)

    def _pick_color(self) -> None:
        try:
            color = QColorDialog.getColor(QColor(self._color), self, "اختر اللون")
            if color.isValid():
                self._color = color.name()
                self._update_style()
                self.color_changed.emit(self._color)
        except Exception as e:
            app_logger.error(f"Error picking color: {e}", exc_info=True)

    def get_color(self) -> str:
        return self._color

    def set_color(self, color: str) -> None:
        self._color = color
        self._update_style()


# ---------------------------------------------------------------------------
# PropertyGroup
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Validation Rule Row Widget
# ---------------------------------------------------------------------------

class _ValidationRuleRow(QFrame):
    """Single validation rule row with type, value, and message."""

    changed = pyqtSignal()
    remove_requested = pyqtSignal(object)  # self

    RULE_TYPES = [
        ("required", "مطلوب"),
        ("min", "الحد الأدنى"),
        ("max", "الحد الأقصى"),
        ("min_length", "أقل عدد أحرف"),
        ("max_length", "أقصى عدد أحرف"),
        ("pattern", "نمط (Regex)"),
        ("email", "بريد إلكتروني"),
        ("numeric", "رقمي فقط"),
        ("custom", "مخصص"),
    ]

    def __init__(self, rule: Optional[ValidationRule] = None, parent=None):
        super().__init__(parent)

        p = get_current_palette()
        self.setStyleSheet(f"""
            _ValidationRuleRow {{
                border: 1px solid {p['border_light']};
                border-radius: 4px;
                padding: 4px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # Row 1: type combo + remove button
        row1 = QHBoxLayout()
        row1.setSpacing(4)

        self._type_combo = QComboBox()
        self._type_combo.setFont(QFont("Cairo", 10))
        for value, display in self.RULE_TYPES:
            self._type_combo.addItem(display, value)
        self._type_combo.currentIndexChanged.connect(self._on_changed)
        row1.addWidget(self._type_combo, 1)

        self._remove_btn = QPushButton("✕")
        self._remove_btn.setFixedSize(int(24), int(24))
        self._remove_btn.setStyleSheet(f"""
            QPushButton {{
                background: {p['danger']};
                color: {p['text_on_primary']};
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {p['danger']};
                opacity: 0.8;
            }}
        """)
        self._remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))
        row1.addWidget(self._remove_btn)

        layout.addLayout(row1)

        # Row 2: value
        val_layout = QHBoxLayout()
        val_layout.setSpacing(4)
        val_label = QLabel("القيمة:")
        val_label.setStyleSheet(f"color: {p['text_muted']}; font-size: 10px;")
        val_label.setFont(QFont("Cairo", 9))
        val_layout.addWidget(val_label)
        self._value_edit = QLineEdit()
        self._value_edit.setPlaceholderText("القيمة (اختياري)")
        self._value_edit.textChanged.connect(self._on_changed)
        val_layout.addWidget(self._value_edit, 1)
        layout.addLayout(val_layout)

        # Row 3: message
        msg_layout = QHBoxLayout()
        msg_layout.setSpacing(4)
        msg_label = QLabel("الرسالة:")
        msg_label.setStyleSheet(f"color: {p['text_muted']}; font-size: 10px;")
        msg_label.setFont(QFont("Cairo", 9))
        msg_layout.addWidget(msg_label)
        self._message_edit = QLineEdit()
        self._message_edit.setPlaceholderText("رسالة الخطأ")
        self._message_edit.textChanged.connect(self._on_changed)
        msg_layout.addWidget(self._message_edit, 1)
        layout.addLayout(msg_layout)

        # Populate if rule provided
        if rule is not None:
            self._set_rule(rule)

    def _set_rule(self, rule: ValidationRule) -> None:
        """Populate from a ValidationRule."""
        for i in range(self._type_combo.count()):
            if self._type_combo.itemData(i) == rule.rule_type:
                self._type_combo.setCurrentIndex(i)
                break

        self._value_edit.setText(str(rule.value) if rule.value is not None else "")
        self._message_edit.setText(rule.message or "")

    def get_rule(self) -> ValidationRule:
        """Build a ValidationRule from current state."""
        rule_type = self._type_combo.currentData() or "required"
        value_text = self._value_edit.text().strip()
        value: Any = value_text if value_text else None

        # Try numeric conversion for min/max rules
        if rule_type in ("min", "max", "min_length", "max_length") and value_text:
            try:
                value = int(value_text)
            except ValueError:
                try:
                    value = float(value_text)
                except ValueError:
                    value = value_text

        return ValidationRule(
            rule_type=rule_type,
            value=value,
            message=self._message_edit.text().strip()
        )

    def _on_changed(self) -> None:
        self.changed.emit()


# ---------------------------------------------------------------------------
# FormPropertyEditor
# ---------------------------------------------------------------------------

class FormPropertyEditor(QWidget):
    """
    Enhanced property editor for form widgets with 6-tab QTabWidget.

    Signals:
        property_changed: Emitted when any property changes (FormWidget)
        property_change_started: Emitted before changes with old data snapshot (dict)
    """

    property_changed = pyqtSignal(object)  # FormWidget
    property_change_started = pyqtSignal(dict)  # old data snapshot for undo

    # Widget type display names (Arabic)
    _TYPE_NAMES: Dict[WidgetType, str] = {
        WidgetType.LABEL: "نص",
        WidgetType.TEXT_INPUT: "حقل نصي",
        WidgetType.TEXT_AREA: "منطقة نص",
        WidgetType.NUMBER_INPUT: "رقم",
        WidgetType.DECIMAL_INPUT: "رقم عشري",
        WidgetType.COMBO_BOX: "قائمة منسدلة",
        WidgetType.CHECK_BOX: "مربع اختيار",
        WidgetType.RADIO_BUTTON: "زر راديو",
        WidgetType.DATE_PICKER: "تاريخ",
        WidgetType.TIME_PICKER: "وقت",
        WidgetType.BUTTON: "زر",
        WidgetType.GROUP_BOX: "مجموعة",
        WidgetType.SEPARATOR: "فاصل",
        WidgetType.IMAGE: "صورة",
        WidgetType.TABLE: "جدول",
    }

    def __init__(self, parent=None):
        super().__init__(parent)

        self._current_widget: Optional[FormWidget] = None
        self._updating = False
        self._validation_rows: List[_ValidationRuleRow] = []

        self._setup_ui()
        self.set_widget(None)

    # ===================================================================
    # UI Setup
    # ===================================================================

    def _setup_ui(self) -> None:
        """Build the entire property editor UI."""
        p = get_current_palette()

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # --- Header title ---
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(10, 10, 10, 6)

        self._title = QLabel("الخصائص")
        self._title.setFont(QFont("Cairo", 13, QFont.Bold))
        self._title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._title.setStyleSheet(f"color: {p['text_primary']};")
        header_layout.addWidget(self._title)

        root_layout.addWidget(header)

        # --- "No selection" message ---
        self._no_selection = QLabel("اختر عنصرا لتعديل خصائصه")
        self._no_selection.setFont(QFont("Cairo", 11))
        self._no_selection.setStyleSheet(f"color: {p['text_muted']}; padding: 30px 10px;")
        self._no_selection.setAlignment(Qt.AlignCenter)
        self._no_selection.setWordWrap(True)
        root_layout.addWidget(self._no_selection)

        # --- Tab widget ---
        self._tab_widget = QTabWidget()
        self._tab_widget.setLayoutDirection(Qt.RightToLeft)
        self._tab_widget.setFont(QFont("Cairo", 10))
        self._tab_widget.setStyleSheet(self._build_tab_stylesheet(p))

        # Build all 6 tabs
        self._build_tab_general(p)
        self._build_tab_layout(p)
        self._build_tab_format(p)
        self._build_tab_data(p)
        self._build_tab_validation(p)
        self._build_tab_advanced(p)

        root_layout.addWidget(self._tab_widget)

        self._tab_widget.hide()

        # --- Widget-level style ---
        self.setStyleSheet(f"""
            FormPropertyEditor {{
                background: {p['bg_card']};
                border-right: 1px solid {p['border']};
            }}
            QLineEdit, QSpinBox, QComboBox {{
                font-family: Cairo;
                padding: 5px;
                border: 1px solid {p['border']};
                border-radius: 4px;
                background: {p['bg_input']};
                color: {p['text_primary']};
            }}
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
                border-color: {p['border_focus']};
            }}
            QCheckBox {{
                font-family: Cairo;
                color: {p['text_primary']};
            }}
            QTextEdit {{
                font-family: Cairo;
                padding: 4px;
                border: 1px solid {p['border']};
                border-radius: 4px;
                background: {p['bg_input']};
                color: {p['text_primary']};
            }}
            QLabel {{
                font-family: Cairo;
            }}
        """)

        self.setMinimumWidth(int(250))
        self.setMaximumWidth(int(320))

    # ---------------------------------------------------------------
    # Tab stylesheet helper
    # ---------------------------------------------------------------

    @staticmethod
    def _build_tab_stylesheet(p: Dict[str, str]) -> str:
        return f"""
            QTabWidget::pane {{
                border: 1px solid {p['border']};
                border-top: none;
                background: {p['bg_card']};
            }}
            QTabBar::tab {{
                font-family: Cairo;
                font-size: 10px;
                padding: 6px 8px;
                border: 1px solid {p['border']};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                background: {p['bg_main']};
                color: {p['text_muted']};
                min-width: 32px;
            }}
            QTabBar::tab:selected {{
                background: {p['bg_card']};
                color: {p['primary']};
                font-weight: bold;
                border-bottom-color: {p['bg_card']};
            }}
            QTabBar::tab:hover:!selected {{
                background: {p['bg_hover']};
                color: {p['text_primary']};
            }}
        """

    # ---------------------------------------------------------------
    # Helper: create a scroll area wrapping a grid-based form
    # ---------------------------------------------------------------

    def _make_scroll_form(self, p: Dict[str, str]) -> tuple:
        """
        Return (scroll_widget, grid_layout) for a tab body.

        The scroll area expands to fill the tab, and the inner grid
        is where add_row(...) style controls are placed.
        """
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        inner = QWidget()
        grid = QGridLayout(inner)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setSpacing(6)
        grid.setColumnStretch(1, 1)

        scroll.setWidget(inner)
        return scroll, grid

    def _add_label_row(
        self, grid: QGridLayout, row: int, text: str, widget: QWidget, p: Dict[str, str]
    ) -> int:
        """Add a label+widget row to a grid, return next row number."""
        lbl = QLabel(text)
        lbl.setFont(QFont("Cairo", 10))
        lbl.setStyleSheet(f"color: {p['text_muted']};")
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(lbl, row, 0)
        grid.addWidget(widget, row, 1)
        return row + 1

    # ===================================================================
    # Tab 1: عام (General)
    # ===================================================================

    def _build_tab_general(self, p: Dict[str, str]) -> None:
        scroll, grid = self._make_scroll_form(p)
        row = 0

        # -- ID (read-only) --
        self._id_label = QLabel()
        self._id_label.setFont(QFont("Cairo", 10))
        self._id_label.setStyleSheet(f"color: {p['text_muted']};")
        self._id_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        row = self._add_label_row(grid, row, "المعرّف:", self._id_label, p)

        # -- Type (read-only) --
        self._type_label = QLabel()
        self._type_label.setFont(QFont("Cairo", 10, QFont.Bold))
        self._type_label.setStyleSheet(f"color: {p['primary']};")
        row = self._add_label_row(grid, row, "النوع:", self._type_label, p)

        # -- Label AR --
        self._label_ar_edit = QLineEdit()
        self._label_ar_edit.setFont(QFont("Cairo", 10))
        self._label_ar_edit.setPlaceholderText("العنوان بالعربية")
        self._label_ar_edit.textChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "العنوان (عربي):", self._label_ar_edit, p)

        # -- Label EN --
        self._label_en_edit = QLineEdit()
        self._label_en_edit.setFont(QFont("Cairo", 10))
        self._label_en_edit.setPlaceholderText("Label in English")
        self._label_en_edit.textChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "العنوان (إنجليزي):", self._label_en_edit, p)

        # -- Placeholder AR --
        self._placeholder_ar_edit = QLineEdit()
        self._placeholder_ar_edit.setFont(QFont("Cairo", 10))
        self._placeholder_ar_edit.setPlaceholderText("النص الإرشادي بالعربية")
        self._placeholder_ar_edit.textChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "إرشاد (عربي):", self._placeholder_ar_edit, p)

        # -- Placeholder EN --
        self._placeholder_en_edit = QLineEdit()
        self._placeholder_en_edit.setFont(QFont("Cairo", 10))
        self._placeholder_en_edit.setPlaceholderText("Placeholder in English")
        self._placeholder_en_edit.textChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "إرشاد (إنجليزي):", self._placeholder_en_edit, p)

        # -- Tooltip --
        self._tooltip_edit = QLineEdit()
        self._tooltip_edit.setFont(QFont("Cairo", 10))
        self._tooltip_edit.setPlaceholderText("تلميح عند التمرير")
        self._tooltip_edit.textChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "التلميح:", self._tooltip_edit, p)

        grid.setRowStretch(row, 1)
        self._tab_widget.addTab(scroll, "عام")

    # ===================================================================
    # Tab 2: تخطيط (Layout)
    # ===================================================================

    def _build_tab_layout(self, p: Dict[str, str]) -> None:
        scroll, grid = self._make_scroll_form(p)
        row = 0

        # -- X --
        self._x_spin = QSpinBox()
        self._x_spin.setRange(0, 5000)
        self._x_spin.setSuffix(" px")
        self._x_spin.valueChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "X:", self._x_spin, p)

        # -- Y --
        self._y_spin = QSpinBox()
        self._y_spin.setRange(0, 5000)
        self._y_spin.setSuffix(" px")
        self._y_spin.valueChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "Y:", self._y_spin, p)

        # -- Width --
        self._width_spin = QSpinBox()
        self._width_spin.setRange(10, 2000)
        self._width_spin.setSuffix(" px")
        self._width_spin.valueChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "العرض:", self._width_spin, p)

        # -- Height --
        self._height_spin = QSpinBox()
        self._height_spin.setRange(10, 2000)
        self._height_spin.setSuffix(" px")
        self._height_spin.valueChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "الارتفاع:", self._height_spin, p)

        # -- Row --
        self._row_spin = QSpinBox()
        self._row_spin.setRange(0, 100)
        self._row_spin.valueChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "الصف:", self._row_spin, p)

        # -- Col --
        self._col_spin = QSpinBox()
        self._col_spin.setRange(0, 20)
        self._col_spin.valueChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "العمود:", self._col_spin, p)

        # -- Colspan --
        self._colspan_spin = QSpinBox()
        self._colspan_spin.setRange(1, 12)
        self._colspan_spin.setValue(1)
        self._colspan_spin.valueChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "امتداد الأعمدة:", self._colspan_spin, p)

        # -- Rowspan --
        self._rowspan_spin = QSpinBox()
        self._rowspan_spin.setRange(1, 12)
        self._rowspan_spin.setValue(1)
        self._rowspan_spin.valueChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "امتداد الصفوف:", self._rowspan_spin, p)

        # -- Min Width --
        self._min_width_spin = QSpinBox()
        self._min_width_spin.setRange(0, 2000)
        self._min_width_spin.setSuffix(" px")
        self._min_width_spin.valueChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "أقل عرض:", self._min_width_spin, p)

        # -- Max Width --
        self._max_width_spin = QSpinBox()
        self._max_width_spin.setRange(0, 5000)
        self._max_width_spin.setSuffix(" px")
        self._max_width_spin.valueChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "أقصى عرض:", self._max_width_spin, p)

        # -- Alignment --
        self._alignment_combo = QComboBox()
        self._alignment_combo.setFont(QFont("Cairo", 10))
        self._alignment_combo.addItem("يمين", "right")
        self._alignment_combo.addItem("يسار", "left")
        self._alignment_combo.addItem("وسط", "center")
        self._alignment_combo.addItem("ملء", "stretch")
        self._alignment_combo.currentIndexChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "المحاذاة:", self._alignment_combo, p)

        grid.setRowStretch(row, 1)
        self._tab_widget.addTab(scroll, "تخطيط")

    # ===================================================================
    # Tab 3: تنسيق (Format)
    # ===================================================================

    def _build_tab_format(self, p: Dict[str, str]) -> None:
        scroll, grid = self._make_scroll_form(p)
        row = 0

        # -- Font family --
        self._font_family_combo = QComboBox()
        self._font_family_combo.setFont(QFont("Cairo", 10))
        self._font_family_combo.addItems([
            "Cairo", "Arial", "Tahoma", "Roboto",
            "Amiri", "Tajawal", "Noto Sans Arabic", "Courier New"
        ])
        self._font_family_combo.currentTextChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "الخط:", self._font_family_combo, p)

        # -- Font size --
        self._font_size_spin = QSpinBox()
        self._font_size_spin.setRange(6, 72)
        self._font_size_spin.setSuffix(" px")
        self._font_size_spin.valueChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "حجم الخط:", self._font_size_spin, p)

        # -- Font weight --
        self._font_weight_combo = QComboBox()
        self._font_weight_combo.setFont(QFont("Cairo", 10))
        self._font_weight_combo.addItem("عادي", "normal")
        self._font_weight_combo.addItem("متوسط", "medium")
        self._font_weight_combo.addItem("عريض", "bold")
        self._font_weight_combo.currentIndexChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "سمك الخط:", self._font_weight_combo, p)

        # -- Text color --
        self._text_color_btn = ColorButton("#000000")
        self._text_color_btn.color_changed.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "لون النص:", self._text_color_btn, p)

        # -- Background color --
        self._bg_color_btn = ColorButton("#ffffff")
        self._bg_color_btn.color_changed.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "لون الخلفية:", self._bg_color_btn, p)

        # -- Border color --
        self._border_color_btn = ColorButton("#d1d5db")
        self._border_color_btn.color_changed.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "لون الحدود:", self._border_color_btn, p)

        # -- Border width --
        self._border_width_spin = QSpinBox()
        self._border_width_spin.setRange(0, 10)
        self._border_width_spin.setSuffix(" px")
        self._border_width_spin.valueChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "سمك الحدود:", self._border_width_spin, p)

        # -- Border radius --
        self._border_radius_spin = QSpinBox()
        self._border_radius_spin.setRange(0, 50)
        self._border_radius_spin.setSuffix(" px")
        self._border_radius_spin.valueChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "تدوير الحدود:", self._border_radius_spin, p)

        # -- Custom CSS --
        css_label = QLabel("CSS مخصص:")
        css_label.setFont(QFont("Cairo", 10))
        css_label.setStyleSheet(f"color: {p['text_muted']};")
        css_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        grid.addWidget(css_label, row, 0)

        self._custom_css_edit = QTextEdit()
        self._custom_css_edit.setFont(QFont("Courier New", 9))
        self._custom_css_edit.setPlaceholderText("/* أنماط مخصصة */")
        self._custom_css_edit.setMaximumHeight(int(100))
        self._custom_css_edit.textChanged.connect(self._on_property_changed)
        grid.addWidget(self._custom_css_edit, row, 1)
        row += 1

        grid.setRowStretch(row, 1)
        self._tab_widget.addTab(scroll, "تنسيق")

    # ===================================================================
    # Tab 4: بيانات (Data)
    # ===================================================================

    def _build_tab_data(self, p: Dict[str, str]) -> None:
        scroll, grid = self._make_scroll_form(p)
        row = 0

        # -- Table --
        self._data_table_combo = QComboBox()
        self._data_table_combo.setFont(QFont("Cairo", 10))
        self._data_table_combo.setEditable(True)
        self._data_table_combo.addItems([
            "", "employees", "companies", "departments",
            "job_titles", "nationalities", "banks", "employee_statuses"
        ])
        self._data_table_combo.currentTextChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "الجدول:", self._data_table_combo, p)

        # -- Column --
        self._data_column_combo = QComboBox()
        self._data_column_combo.setFont(QFont("Cairo", 10))
        self._data_column_combo.setEditable(True)
        self._data_column_combo.addItems([
            "", "id", "name_ar", "name_en", "employee_number",
            "department_id", "job_title_id", "salary", "phone",
            "email", "status_id", "hire_date", "national_id"
        ])
        self._data_column_combo.currentTextChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "العمود:", self._data_column_combo, p)

        # -- Data type --
        self._data_type_combo = QComboBox()
        self._data_type_combo.setFont(QFont("Cairo", 10))
        self._data_type_combo.addItem("نص", "text")
        self._data_type_combo.addItem("رقم صحيح", "integer")
        self._data_type_combo.addItem("رقم عشري", "decimal")
        self._data_type_combo.addItem("تاريخ", "date")
        self._data_type_combo.addItem("وقت", "time")
        self._data_type_combo.addItem("تاريخ ووقت", "datetime")
        self._data_type_combo.addItem("منطقي", "boolean")
        self._data_type_combo.addItem("JSON", "json")
        self._data_type_combo.currentIndexChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "نوع البيانات:", self._data_type_combo, p)

        # -- Display format --
        self._display_format_edit = QLineEdit()
        self._display_format_edit.setFont(QFont("Cairo", 10))
        self._display_format_edit.setPlaceholderText("مثال: %Y-%m-%d أو #,##0.00")
        self._display_format_edit.textChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "تنسيق العرض:", self._display_format_edit, p)

        # -- Combo source type --
        self._combo_source_combo = QComboBox()
        self._combo_source_combo.setFont(QFont("Cairo", 10))
        self._combo_source_combo.addItem("لا يوجد", "none")
        self._combo_source_combo.addItem("قائمة ثابتة", "static")
        self._combo_source_combo.addItem("جدول مرجعي", "table")
        self._combo_source_combo.addItem("استعلام SQL", "query")
        self._combo_source_combo.addItem("API خارجي", "api")
        self._combo_source_combo.currentIndexChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "مصدر القائمة:", self._combo_source_combo, p)

        grid.setRowStretch(row, 1)
        self._tab_widget.addTab(scroll, "بيانات")

    # ===================================================================
    # Tab 5: تحقق (Validation)
    # ===================================================================

    def _build_tab_validation(self, p: Dict[str, str]) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # -- Required checkbox --
        self._required_check = QCheckBox("مطلوب")
        self._required_check.setFont(QFont("Cairo", 11))
        self._required_check.setLayoutDirection(Qt.RightToLeft)
        self._required_check.stateChanged.connect(self._on_property_changed)
        layout.addWidget(self._required_check)

        # -- Separator --
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {p['border']};")
        layout.addWidget(sep)

        # -- Rules header + add button --
        rules_header = QHBoxLayout()
        rules_title = QLabel("قواعد التحقق:")
        rules_title.setFont(QFont("Cairo", 11, QFont.Bold))
        rules_title.setStyleSheet(f"color: {p['text_primary']};")
        rules_header.addWidget(rules_title)
        rules_header.addStretch()

        self._add_rule_btn = QPushButton("+ إضافة قاعدة")
        self._add_rule_btn.setFont(QFont("Cairo", 9))
        self._add_rule_btn.setStyleSheet(f"""
            QPushButton {{
                background: {p['primary']};
                color: {p['text_on_primary']};
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
            }}
            QPushButton:hover {{
                background: {p['primary_hover']};
            }}
        """)
        self._add_rule_btn.clicked.connect(self._add_validation_rule)
        rules_header.addWidget(self._add_rule_btn)
        layout.addLayout(rules_header)

        # -- Rules container --
        self._rules_container = QVBoxLayout()
        self._rules_container.setSpacing(6)
        layout.addLayout(self._rules_container)

        layout.addStretch()

        scroll.setWidget(inner)
        self._tab_widget.addTab(scroll, "تحقق")

    # ===================================================================
    # Tab 6: متقدم (Advanced)
    # ===================================================================

    def _build_tab_advanced(self, p: Dict[str, str]) -> None:
        scroll, grid = self._make_scroll_form(p)
        row = 0

        # -- Default value --
        self._default_value_edit = QLineEdit()
        self._default_value_edit.setFont(QFont("Cairo", 10))
        self._default_value_edit.setPlaceholderText("القيمة الافتراضية")
        self._default_value_edit.textChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "القيمة الافتراضية:", self._default_value_edit, p)

        # -- Visible --
        self._visible_check = QCheckBox("مرئي")
        self._visible_check.setFont(QFont("Cairo", 10))
        self._visible_check.setLayoutDirection(Qt.RightToLeft)
        self._visible_check.setChecked(True)
        self._visible_check.stateChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "الظهور:", self._visible_check, p)

        # -- Enabled --
        self._enabled_check = QCheckBox("مفعّل")
        self._enabled_check.setFont(QFont("Cairo", 10))
        self._enabled_check.setLayoutDirection(Qt.RightToLeft)
        self._enabled_check.setChecked(True)
        self._enabled_check.stateChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "التفعيل:", self._enabled_check, p)

        # -- Read-only --
        self._readonly_check = QCheckBox("للقراءة فقط")
        self._readonly_check.setFont(QFont("Cairo", 10))
        self._readonly_check.setLayoutDirection(Qt.RightToLeft)
        self._readonly_check.stateChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "القراءة فقط:", self._readonly_check, p)

        # -- Visible condition --
        self._visible_cond_edit = QLineEdit()
        self._visible_cond_edit.setFont(QFont("Cairo", 10))
        self._visible_cond_edit.setPlaceholderText("مثال: status_id == 1")
        self._visible_cond_edit.textChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "شرط الظهور:", self._visible_cond_edit, p)

        # -- Enabled condition --
        self._enabled_cond_edit = QLineEdit()
        self._enabled_cond_edit.setFont(QFont("Cairo", 10))
        self._enabled_cond_edit.setPlaceholderText("مثال: role == 'admin'")
        self._enabled_cond_edit.textChanged.connect(self._on_property_changed)
        row = self._add_label_row(grid, row, "شرط التفعيل:", self._enabled_cond_edit, p)

        grid.setRowStretch(row, 1)
        self._tab_widget.addTab(scroll, "متقدم")

    # ===================================================================
    # Validation rule management
    # ===================================================================

    def _add_validation_rule(self, rule: Optional[ValidationRule] = None) -> _ValidationRuleRow:
        """Add a new validation rule row to the validation tab."""
        row_widget = _ValidationRuleRow(rule)
        row_widget.changed.connect(self._on_property_changed)
        row_widget.remove_requested.connect(self._remove_validation_rule)

        self._validation_rows.append(row_widget)
        self._rules_container.addWidget(row_widget)
        return row_widget

    def _remove_validation_rule(self, row_widget: _ValidationRuleRow) -> None:
        """Remove a validation rule row."""
        if row_widget in self._validation_rows:
            self._validation_rows.remove(row_widget)
            self._rules_container.removeWidget(row_widget)
            row_widget.deleteLater()
            self._on_property_changed()

    def _clear_validation_rules(self) -> None:
        """Remove all validation rule rows from the UI."""
        for row_widget in self._validation_rows:
            self._rules_container.removeWidget(row_widget)
            row_widget.deleteLater()
        self._validation_rows.clear()

    # ===================================================================
    # set_widget  --  populate all tabs from a FormWidget
    # ===================================================================

    def set_widget(self, widget: Optional[FormWidget]) -> None:
        """Set the widget whose properties are being edited."""
        self._current_widget = widget

        if widget is None:
            self._no_selection.show()
            self._tab_widget.hide()
            self._title.setText("الخصائص")
            return

        self._no_selection.hide()
        self._tab_widget.show()

        # Block change signals while populating
        self._updating = True

        try:
            type_name = self._TYPE_NAMES.get(widget.widget_type, "عنصر")
            self._title.setText(f"خصائص: {type_name}")

            props = widget.properties

            # ----- Tab 1: General -----
            self._id_label.setText(widget.id)
            self._type_label.setText(type_name)
            self._label_ar_edit.setText(widget.label)
            self._label_en_edit.setText(props.get("label_en", ""))
            self._placeholder_ar_edit.setText(widget.placeholder)
            self._placeholder_en_edit.setText(props.get("placeholder_en", ""))
            self._tooltip_edit.setText(props.get("tooltip", ""))

            # ----- Tab 2: Layout -----
            self._x_spin.setValue(widget.x)
            self._y_spin.setValue(widget.y)
            self._width_spin.setValue(widget.width)
            self._height_spin.setValue(widget.height)
            self._row_spin.setValue(props.get("grid_row", 0))
            self._col_spin.setValue(props.get("grid_col", 0))
            self._colspan_spin.setValue(props.get("colspan", 1))
            self._rowspan_spin.setValue(props.get("rowspan", 1))
            self._min_width_spin.setValue(props.get("min_width", 0))
            self._max_width_spin.setValue(props.get("max_width", 0))

            alignment_val = props.get("alignment", "right")
            for i in range(self._alignment_combo.count()):
                if self._alignment_combo.itemData(i) == alignment_val:
                    self._alignment_combo.setCurrentIndex(i)
                    break

            # ----- Tab 3: Format -----
            self._font_family_combo.setCurrentText(widget.style.font_family)
            self._font_size_spin.setValue(widget.style.font_size)

            font_weight_val = props.get("font_weight", "normal")
            for i in range(self._font_weight_combo.count()):
                if self._font_weight_combo.itemData(i) == font_weight_val:
                    self._font_weight_combo.setCurrentIndex(i)
                    break

            self._text_color_btn.set_color(widget.style.font_color)
            self._bg_color_btn.set_color(widget.style.background_color)
            self._border_color_btn.set_color(widget.style.border_color)
            self._border_width_spin.setValue(widget.style.border_width)
            self._border_radius_spin.setValue(widget.style.border_radius)
            self._custom_css_edit.setPlainText(props.get("custom_css", ""))

            # ----- Tab 4: Data -----
            binding = widget.data_binding or ""
            parts = binding.split(".", 1) if binding else ["", ""]
            table_part = parts[0] if len(parts) > 0 else ""
            column_part = parts[1] if len(parts) > 1 else ""

            self._data_table_combo.setCurrentText(table_part)
            self._data_column_combo.setCurrentText(column_part)

            data_type_val = props.get("data_type", "text")
            for i in range(self._data_type_combo.count()):
                if self._data_type_combo.itemData(i) == data_type_val:
                    self._data_type_combo.setCurrentIndex(i)
                    break

            self._display_format_edit.setText(props.get("display_format", ""))

            source_val = props.get("combo_source_type", "none")
            for i in range(self._combo_source_combo.count()):
                if self._combo_source_combo.itemData(i) == source_val:
                    self._combo_source_combo.setCurrentIndex(i)
                    break

            # ----- Tab 5: Validation -----
            has_required = any(v.rule_type == "required" for v in widget.validation)
            self._required_check.setChecked(has_required)

            # Rebuild rule rows (exclude "required" since it has its own checkbox)
            self._clear_validation_rules()
            for v_rule in widget.validation:
                if v_rule.rule_type != "required":
                    self._add_validation_rule(v_rule)

            # ----- Tab 6: Advanced -----
            default_val = widget.default_value
            self._default_value_edit.setText(str(default_val) if default_val is not None else "")
            self._visible_check.setChecked(props.get("visible", True))
            self._enabled_check.setChecked(props.get("enabled", True))
            self._readonly_check.setChecked(props.get("readonly", False))
            self._visible_cond_edit.setText(props.get("visible_condition", ""))
            self._enabled_cond_edit.setText(props.get("enabled_condition", ""))

        except Exception as e:
            app_logger.error(f"Error populating property editor: {e}", exc_info=True)
        finally:
            self._updating = False

    # ===================================================================
    # _on_property_changed  --  collect all values and emit
    # ===================================================================

    def _on_property_changed(self) -> None:
        """Collect current values from all tabs, apply to widget, emit signal."""
        if self._updating or self._current_widget is None:
            return

        w = self._current_widget

        # Snapshot old data for undo support
        try:
            old_snapshot = w.to_dict()
            self.property_change_started.emit(old_snapshot)
        except Exception as e:
            app_logger.error(f"Error creating undo snapshot: {e}", exc_info=True)

        try:
            # ---- Tab 1: General ----
            w.label = self._label_ar_edit.text()
            w.placeholder = self._placeholder_ar_edit.text()
            w.properties["label_en"] = self._label_en_edit.text()
            w.properties["placeholder_en"] = self._placeholder_en_edit.text()
            w.properties["tooltip"] = self._tooltip_edit.text()

            # ---- Tab 2: Layout ----
            w.x = self._x_spin.value()
            w.y = self._y_spin.value()
            w.width = self._width_spin.value()
            w.height = self._height_spin.value()
            w.properties["grid_row"] = self._row_spin.value()
            w.properties["grid_col"] = self._col_spin.value()
            w.properties["colspan"] = self._colspan_spin.value()
            w.properties["rowspan"] = self._rowspan_spin.value()
            w.properties["min_width"] = self._min_width_spin.value()
            w.properties["max_width"] = self._max_width_spin.value()
            w.properties["alignment"] = self._alignment_combo.currentData() or "right"

            # ---- Tab 3: Format ----
            w.style.font_family = self._font_family_combo.currentText()
            w.style.font_size = self._font_size_spin.value()
            w.properties["font_weight"] = self._font_weight_combo.currentData() or "normal"
            w.style.font_color = self._text_color_btn.get_color()
            w.style.background_color = self._bg_color_btn.get_color()
            w.style.border_color = self._border_color_btn.get_color()
            w.style.border_width = self._border_width_spin.value()
            w.style.border_radius = self._border_radius_spin.value()
            w.properties["custom_css"] = self._custom_css_edit.toPlainText()

            # ---- Tab 4: Data ----
            table_text = self._data_table_combo.currentText().strip()
            column_text = self._data_column_combo.currentText().strip()
            if table_text and column_text:
                w.data_binding = f"{table_text}.{column_text}"
            elif table_text:
                w.data_binding = table_text
            else:
                w.data_binding = None

            w.properties["data_type"] = self._data_type_combo.currentData() or "text"
            w.properties["display_format"] = self._display_format_edit.text()
            w.properties["combo_source_type"] = self._combo_source_combo.currentData() or "none"

            # ---- Tab 5: Validation ----
            w.validation = []
            if self._required_check.isChecked():
                w.validation.append(
                    ValidationRule("required", message="هذا الحقل مطلوب")
                )
            for rule_row in self._validation_rows:
                w.validation.append(rule_row.get_rule())

            # ---- Tab 6: Advanced ----
            default_text = self._default_value_edit.text().strip()
            w.default_value = default_text if default_text else None
            w.properties["visible"] = self._visible_check.isChecked()
            w.properties["enabled"] = self._enabled_check.isChecked()
            w.properties["readonly"] = self._readonly_check.isChecked()
            w.properties["visible_condition"] = self._visible_cond_edit.text()
            w.properties["enabled_condition"] = self._enabled_cond_edit.text()

            # Emit change notification
            self.property_changed.emit(w)

        except Exception as e:
            app_logger.error(f"Error applying property changes: {e}", exc_info=True)
