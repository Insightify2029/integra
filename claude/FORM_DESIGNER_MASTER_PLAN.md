# INTEGRA - Form Designer Enhancement Master Plan
# خطة تطوير نظام تصميم الفورمز الشاملة

> **Status:** 📋 PLANNING
> **Created:** 2026-02-10
> **Author:** Mohamed + Claude
> **Version:** 1.0.0
> **Target:** Transform INTEGRA forms from hardcoded layouts to a JSON-configurable, visually editable system

---

## 🎯 المشكلة والهدف

### المشكلة الحالية
1. الفورمز مكتوبة بكود Python صلب (hardcoded) - أي تغيير في الشكل يحتاج تعديل كود
2. المبرمج (Claude) بيعمل تصميمات مش جمالية - text boxes عريضة، أزرار في أماكن غلط، مفيش لمسات فنية
3. المستخدم (Mohamed) مش يقدر يتحكم في شكل الفورمز بدون تعديل كود Python

### الهدف
إنشاء نظام يفصل **شكل الفورم** عن **لوجيك الفورم** بحيث:
- Claude يكتب اللوجيك والربط بالداتا
- Mohamed يتحكم في الشكل بصرياً (drag & drop / resize / rearrange)
- التغييرات تتحفظ في JSON ويتم تحميلها تلقائياً

### ما هو موجود حالياً
- **Form Builder** موجود في `modules/designer/form_builder/` (2,500 سطر)
- يدعم 14 نوع widget مع drag & drop وgrid snapping
- يحفظ كـ `.iform` JSON
- **لكن** مفيش FormRenderer يحول الـ JSON لفورمز شغالة!

---

## 📐 المعمارية العامة (Architecture)

```
┌─────────────────────────────────────────────────────────┐
│                    Form System Architecture               │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │ Form Designer │───▶│  .iform JSON  │◀───│ Live Editor │ │
│  │  (التصميم)    │    │  (الحفظ)      │    │(التعديل)    │ │
│  └──────────────┘    └──────┬───────┘    └────────────┘ │
│                              │                            │
│                     ┌────────▼────────┐                   │
│                     │  FormRenderer    │                   │
│                     │  (محرك العرض)    │                   │
│                     └────────┬────────┘                   │
│                              │                            │
│              ┌───────────────┼───────────────┐            │
│              ▼               ▼               ▼            │
│    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│    │ Data Binding  │ │  Validation  │ │   Theme      │   │
│    │  (ربط البيانات)│ │  (التحقق)    │ │  (الثيمات)   │   │
│    └──────────────┘ └──────────────┘ └──────────────┘   │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## 🗂️ هيكل الملفات المستهدف

```
modules/designer/
├── form_builder/                    # ← موجود (سيتم تحسينه)
│   ├── __init__.py
│   ├── form_builder_window.py       # نافذة المصمم الرئيسية
│   ├── form_canvas.py               # سطح التصميم
│   ├── widget_toolbox.py            # لوحة الأدوات
│   ├── property_editor.py           # محرر الخصائص
│   └── data_binding.py              # ربط البيانات
│
├── form_renderer/                   # ← جديد (Phase 1)
│   ├── __init__.py
│   ├── form_renderer.py             # المحرك الرئيسي - يحول JSON → PyQt5
│   ├── widget_factory.py            # مصنع العناصر - ينشئ widgets حقيقية
│   ├── layout_engine.py             # محرك التخطيط - يحسب الأبعاد والمواقع
│   ├── validation_engine.py         # محرك التحقق - ينفذ قواعد الـ validation
│   ├── form_data_bridge.py          # جسر البيانات - يربط الفورم بالداتابيز
│   └── form_state_manager.py        # إدارة حالة الفورم
│
├── live_editor/                     # ← جديد (Phase 3)
│   ├── __init__.py
│   ├── live_edit_overlay.py         # طبقة التعديل المرئية
│   ├── selection_handles.py         # مقابض التحديد والتحريك
│   ├── property_popup.py            # نافذة خصائص سريعة
│   └── snap_guides.py              # خطوط محاذاة ذكية
│
├── templates/                       # ← جديد (Phase 2)
│   ├── __init__.py
│   ├── template_manager.py          # إدارة القوالب
│   └── builtin/                     # قوالب جاهزة
│       ├── employee_edit.iform
│       ├── employee_profile.iform
│       ├── master_data_form.iform
│       ├── search_form.iform
│       └── settings_form.iform
│
└── shared/                          # ← جديد (مشترك)
    ├── __init__.py
    ├── form_schema.py               # تعريف هيكل JSON Schema
    ├── form_constants.py            # ثوابت مشتركة
    └── form_utils.py                # دوال مساعدة مشتركة
```

---

## 📋 المراحل التفصيلية

---

## المرحلة 1: FormRenderer Engine (محرك عرض الفورمز)

> **الأولوية:** 🔴 عالية جداً (الأساس لكل شيء)
> **التقدير:** جلسة واحدة مكثفة
> **المخرجات:** 6 ملفات جديدة في `form_renderer/`

### 1.1 Form Schema Definition (`shared/form_schema.py`)

**الهدف:** تعريف هيكل JSON رسمي ومعياري لملفات `.iform`

```python
# Enhanced .iform JSON Schema v2.0
{
    "version": "2.0",
    "form_id": "edit_employee",
    "form_name_ar": "تعديل بيانات الموظف",
    "form_name_en": "Edit Employee",
    "target_table": "employees",

    # إعدادات الفورم العامة
    "settings": {
        "direction": "rtl",           # rtl | ltr
        "layout_mode": "smart_grid",  # smart_grid | absolute | flow
        "columns": 2,                 # عدد أعمدة الـ grid
        "column_gap": 20,             # المسافة بين الأعمدة (px)
        "row_gap": 15,                # المسافة بين الصفوف (px)
        "margins": {
            "top": 20, "right": 20,
            "bottom": 20, "left": 20
        },
        "min_width": 600,
        "max_width": 1200,
        "scrollable": true,
        "show_required_indicator": true,
        "save_button_position": "bottom_left"  # bottom_left | bottom_right | bottom_center | top_right
    },

    # تعريف الأقسام (Cards)
    "sections": [
        {
            "id": "basic_info",
            "title_ar": "📋 البيانات الأساسية",
            "title_en": "Basic Info",
            "collapsed": false,
            "collapsible": true,
            "columns": 2,           # override global columns
            "visible": true,
            "condition": null,       # شرط إظهار/إخفاء

            "fields": [
                {
                    "id": "employee_code",
                    "widget_type": "text_input",
                    "label_ar": "كود الموظف",
                    "label_en": "Employee Code",
                    "placeholder_ar": "أدخل كود الموظف",
                    "placeholder_en": "Enter employee code",

                    # التخطيط
                    "layout": {
                        "row": 0,
                        "col": 0,
                        "colspan": 1,
                        "rowspan": 1,
                        "width": null,       # null = auto
                        "min_width": 120,
                        "max_width": 300,
                        "height": null,       # null = default per widget type
                        "alignment": "stretch" # stretch | left | center | right
                    },

                    # الخصائص
                    "properties": {
                        "readonly": true,
                        "enabled": true,
                        "visible": true,
                        "tooltip_ar": "كود الموظف الفريد",
                        "tooltip_en": "Unique employee code",
                        "icon": null,
                        "prefix": null,
                        "suffix": null,
                        "mask": null          # input mask مثل "####-####"
                    },

                    # التنسيق المخصص (اختياري - يتجاوز الثيم)
                    "style_override": {
                        "font_size": null,    # null = use theme default
                        "font_weight": null,
                        "text_color": null,
                        "background": null,
                        "border_color": null,
                        "border_radius": null,
                        "custom_css": null    # QSS إضافي
                    },

                    # ربط البيانات
                    "data_binding": {
                        "table": "employees",
                        "column": "employee_code",
                        "data_type": "string",
                        "display_format": null  # مثل "{:,.2f}" للأرقام
                    },

                    # قواعد التحقق
                    "validation": [
                        {"rule": "required", "message_ar": "هذا الحقل مطلوب"},
                        {"rule": "max_length", "value": 50, "message_ar": "الحد الأقصى 50 حرف"},
                        {"rule": "pattern", "value": "^EMP-\\d{4}$", "message_ar": "الصيغة: EMP-0000"}
                    ]
                },
                {
                    "id": "status_id",
                    "widget_type": "combo_box",
                    "label_ar": "الحالة",

                    "layout": {"row": 0, "col": 1},

                    # خصائص الكومبو بوكس
                    "combo_source": {
                        "type": "query",      # query | static | api
                        "query": "SELECT id, name_ar FROM employee_statuses ORDER BY name_ar",
                        "value_column": "id",
                        "display_column": "name_ar",
                        "default_text_ar": "-- اختر الحالة --",
                        "allow_empty": false
                    },

                    "data_binding": {
                        "table": "employees",
                        "column": "status_id",
                        "data_type": "integer"
                    },

                    "validation": [
                        {"rule": "required", "message_ar": "يجب اختيار الحالة"}
                    ]
                }
            ]
        }
    ],

    # تعريف الأزرار
    "actions": [
        {
            "id": "save",
            "type": "primary",        # primary | secondary | danger | success
            "label_ar": "✅ حفظ التعديلات",
            "label_en": "Save Changes",
            "action": "save",          # save | cancel | custom | navigate
            "position": "footer_left",
            "width": 160,
            "shortcut": "Ctrl+S",
            "confirm_message_ar": null, # رسالة تأكيد قبل التنفيذ
            "visible": true,
            "enabled_condition": null   # شرط تفعيل
        },
        {
            "id": "cancel",
            "type": "danger",
            "label_ar": "❌ إلغاء",
            "action": "cancel",
            "position": "footer_left",
            "width": 120
        }
    ],

    # قواعد شرطية (Conditional Logic)
    "rules": [
        {
            "id": "hide_bank_for_cash",
            "trigger_field": "payment_method",
            "trigger_value": "cash",
            "action": "hide_section",
            "target": "bank_info"
        }
    ],

    # إعدادات الأحداث
    "events": {
        "on_load": null,              # function name to call on form load
        "on_save": null,              # function name to call before save
        "on_validate": null,          # custom validation function
        "on_field_change": {          # field-specific change handlers
            "department_id": "refresh_job_titles"
        }
    }
}
```

### 1.2 Widget Factory (`form_renderer/widget_factory.py`)

**الهدف:** مصنع ينشئ PyQt5 widgets حقيقية من تعريف JSON

**المسؤوليات:**
- إنشاء الـ widget المناسب لكل نوع (QLineEdit, QComboBox, QDateEdit, إلخ)
- تطبيق الخصائص (readonly, enabled, placeholder, tooltip)
- تطبيق الـ style override فوق الثيم الحالي
- إنشاء الـ label المصاحب للـ widget
- إضافة أيقونة required indicator (*) للحقول المطلوبة

**Widget Type Mapping:**
```python
WIDGET_MAP = {
    "text_input":     → QLineEdit
    "text_area":      → QTextEdit (مع تحديد ارتفاع)
    "number_input":   → QSpinBox
    "decimal_input":  → QDoubleSpinBox
    "combo_box":      → QComboBox (مع تحميل بيانات من الـ query)
    "check_box":      → QCheckBox
    "radio_group":    → QButtonGroup + QRadioButton (مجموعة)
    "date_picker":    → QDateEdit (مع calendar popup)
    "time_picker":    → QTimeEdit
    "datetime_picker":→ QDateTimeEdit
    "button":         → QPushButton
    "label":          → QLabel
    "separator":      → QFrame (horizontal line)
    "image":          → QLabel (مع QPixmap)
    "group_box":      → QGroupBox
    "table":          → QTableWidget
    "file_picker":    → QLineEdit + QPushButton (browse)
    "color_picker":   → QPushButton (مع QColorDialog)
    "slider":         → QSlider
    "progress":       → QProgressBar
    "rich_text":      → QTextEdit (مع toolbar)
}
```

**احتياطات مهمة:**
- ✅ كل widget يتم إنشاؤه يجب أن يحترم الثيم الحالي
- ✅ ComboBox loading يجب أن يكون async (لا يجمد الـ UI)
- ✅ جميع الـ widgets يجب أن تدعم RTL
- ✅ إضافة `objectName` لكل widget للوصول السهل
- ✅ ربط `textChanged`/`currentIndexChanged` signals للـ dirty tracking

### 1.3 Layout Engine (`form_renderer/layout_engine.py`)

**الهدف:** محرك تخطيط ذكي يرتب العناصر بطريقة جميلة

**3 أوضاع تخطيط:**

**1. Smart Grid (الافتراضي والموصى):**
```
┌─────────────────────────────────────────┐
│ 📋 البيانات الأساسية                    │
│                                          │
│  [كود الموظف: ______]  [الحالة: ▼____]  │
│  [الاسم عربي: _______]  [الاسم إنجليزي] │
│  [الرقم القومي: _____]  [الجنسية: ▼___] │
│  [تاريخ التعيين: 📅__]                   │
└─────────────────────────────────────────┘
```
- يستخدم QGridLayout
- يحترم `row`, `col`, `colspan`, `rowspan`
- يحسب عرض الأعمدة تلقائياً
- يضيف stretch للأعمدة بالتساوي

**2. Absolute (للتحكم الكامل):**
- يستخدم absolute positioning
- كل widget عند إحداثيات x, y محددة
- مناسب للفورمز المعقدة

**3. Flow (تلقائي):**
- يرتب العناصر تلقائياً من اليمين لليسار (RTL)
- يلف للسطر التالي عند امتلاء السطر
- مناسب للفورمز البسيطة

**مسؤوليات المحرك:**
- حساب عرض كل عمود بناءً على المحتوى
- توزيع المساحة الفائضة بالتساوي
- ضمان تناسق ارتفاع الصفوف
- إضافة الـ margins والـ spacing
- معالجة الأقسام (Cards) كـ containers مستقلة
- دعم الأقسام القابلة للطي (collapsible)

### 1.4 Validation Engine (`form_renderer/validation_engine.py`)

**الهدف:** تنفيذ قواعد التحقق من البيانات

**القواعد المدعومة:**
```python
VALIDATION_RULES = {
    "required":     # الحقل مطلوب (ليس فارغاً)
    "min_length":   # الحد الأدنى لعدد الأحرف
    "max_length":   # الحد الأقصى لعدد الأحرف
    "min_value":    # الحد الأدنى للقيمة (أرقام)
    "max_value":    # الحد الأقصى للقيمة (أرقام)
    "pattern":      # Regular Expression
    "email":        # صيغة بريد إلكتروني
    "phone":        # صيغة رقم هاتف
    "iban":         # صيغة IBAN
    "national_id":  # صيغة رقم قومي
    "date_range":   # نطاق تاريخ
    "unique":       # القيمة فريدة في الجدول
    "custom":       # دالة تحقق مخصصة
}
```

**سلوك التحقق:**
- التحقق الفوري (Real-time) عند تغيير قيمة الحقل
- التحقق الكامل قبل الحفظ
- إظهار رسالة خطأ تحت الحقل مباشرة (بلون أحمر)
- إبراز الحقل الخاطئ بحدود حمراء
- عند الحفظ: التركيز على أول حقل خاطئ والـ scroll إليه
- جمع كل الأخطاء في قائمة (وليس التوقف عند أول خطأ)

**احتياطات:**
- ✅ التحقق من unique يجب أن يكون async (لا يجمد الـ UI)
- ✅ رسائل الخطأ بالعربي
- ✅ دعم رسائل خطأ مخصصة لكل قاعدة

### 1.5 Form Data Bridge (`form_renderer/form_data_bridge.py`)

**الهدف:** جسر بين الفورم وقاعدة البيانات

**المسؤوليات:**
- **load_record(table, id)** → تحميل سجل من الداتابيز وتعبئة الفورم
- **save_record(table, data, id?)** → حفظ البيانات (INSERT أو UPDATE)
- **load_combo_data(query)** → تحميل بيانات الـ dropdowns بشكل async
- **check_unique(table, column, value, exclude_id?)** → فحص التفرد
- **delete_record(table, id)** → حذف سجل مع تأكيد

**احتياطات حرجة:**
- ✅ SQL parameterized queries حصراً (القاعدة #2)
- ✅ psycopg2.sql.Identifier لأسماء الجداول والأعمدة
- ✅ جميع عمليات DB في background thread (القاعدة #13)
- ✅ إرجاع الاتصال للـ pool في finally (القاعدة #8)
- ✅ logging لكل عملية DB
- ✅ audit trail للتعديلات

### 1.6 Form State Manager (`form_renderer/form_state_manager.py`)

**الهدف:** إدارة حالة الفورم

**الحالات:**
```
LOADING  → يتم تحميل البيانات
READY    → جاهز للتعديل
DIRTY    → تم تعديل بيانات (unsaved changes)
SAVING   → يتم الحفظ
SAVED    → تم الحفظ بنجاح
ERROR    → حدث خطأ
```

**المسؤوليات:**
- تتبع التغييرات (dirty tracking) - أي حقل تغيرت قيمته
- رسالة تأكيد عند محاولة الإغلاق مع وجود تغييرات
- Undo/Redo على مستوى الحقل
- Reset form to original values
- إدارة الـ loading state (spinner أثناء التحميل)

### 1.7 Main FormRenderer (`form_renderer/form_renderer.py`)

**الهدف:** المنسق الرئيسي - يجمع كل المكونات

```python
class FormRenderer(QWidget):
    """
    Renders a form from .iform JSON definition.

    Usage:
        renderer = FormRenderer()
        renderer.load_form("path/to/form.iform")
        renderer.set_record(table="employees", record_id=123)
        renderer.saved.connect(on_form_saved)
        renderer.cancelled.connect(on_form_cancelled)
    """

    # Signals
    saved = pyqtSignal(dict)           # بيانات الحفظ
    cancelled = pyqtSignal()            # إلغاء
    dirty_changed = pyqtSignal(bool)    # تغيير حالة التعديل
    validation_failed = pyqtSignal(list) # قائمة أخطاء التحقق
    field_changed = pyqtSignal(str, object) # field_id, new_value

    def load_form(self, form_path: str) -> bool:
        """Load form definition from .iform file"""

    def load_form_dict(self, form_dict: dict) -> bool:
        """Load form from dictionary (for embedded forms)"""

    def set_record(self, table: str, record_id: int) -> None:
        """Load record data into form (async)"""

    def set_data(self, data: dict) -> None:
        """Set form data from dictionary"""

    def get_data(self) -> dict:
        """Get current form data as dictionary"""

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate all fields, return (is_valid, errors)"""

    def save(self) -> None:
        """Save form data (async)"""

    def reset(self) -> None:
        """Reset form to original values"""

    def is_dirty(self) -> bool:
        """Check if form has unsaved changes"""

    def get_field_value(self, field_id: str) -> Any:
        """Get single field value"""

    def set_field_value(self, field_id: str, value: Any) -> None:
        """Set single field value"""

    def set_field_visible(self, field_id: str, visible: bool) -> None:
        """Show/hide a field"""

    def set_field_enabled(self, field_id: str, enabled: bool) -> None:
        """Enable/disable a field"""

    def enable_live_edit(self) -> None:
        """Enable live editing mode (Phase 3)"""
```

**سير العمل (Workflow):**
```
1. load_form("employee_edit.iform")
   ├── Parse JSON
   ├── Validate schema
   └── Store form definition

2. _build_ui()
   ├── Create header (back button + title)
   ├── Create scroll area
   ├── For each section:
   │   ├── Create card frame
   │   ├── Add title + separator
   │   ├── Create grid layout
   │   └── For each field:
   │       ├── widget_factory.create(field_def)
   │       ├── layout_engine.place(widget, layout_info)
   │       └── Connect signals
   └── Create footer (action buttons)

3. set_record("employees", 123)
   ├── form_data_bridge.load_record()  [async]
   ├── Populate widgets from data
   ├── Load combo data  [async]
   └── form_state_manager.set_state(READY)

4. User edits fields...
   ├── field_changed signal
   ├── validation_engine.validate_field()
   ├── form_state_manager.mark_dirty()
   └── dirty_changed signal

5. save()
   ├── validation_engine.validate_all()
   ├── If invalid → validation_failed signal, focus first error
   ├── form_data_bridge.save_record()  [async]
   ├── form_state_manager.set_state(SAVED)
   └── saved signal with data
```

---

## المرحلة 2: تحسين Form Designer الموجود

> **الأولوية:** 🟡 متوسطة
> **التقدير:** جلسة واحدة
> **المخرجات:** تحسينات على 5 ملفات موجودة + 3 ملفات جديدة

### 2.1 تفعيل Preview Mode

**الحالة الحالية:** زرار Preview موجود لكن يعرض "قيد التطوير"

**التحسين:**
- ربط زرار Preview بـ FormRenderer من المرحلة 1
- فتح نافذة preview تعرض الفورم كما سيظهر للمستخدم
- إضافة toolbar في Preview: تبديل الثيم، تغيير حجم النافذة، تحميل بيانات تجريبية

### 2.2 تفعيل Undo/Redo

**الحالة الحالية:** عناصر القائمة موجودة لكن غير مربوطة

**التحسين:**
- استخدام QUndoStack
- تسجيل كل عملية: إضافة widget, حذف, تحريك, تغيير حجم, تغيير خصائص
- ربط Ctrl+Z / Ctrl+Y

### 2.3 تحسين Property Editor

**الحالة الحالية:** خصائص أساسية فقط (position, size, font, required)

**التحسين:**
- إضافة تبويبات: عام | تخطيط | تنسيق | بيانات | تحقق | متقدم
- **تبويب عام:** ID, Type, Label AR, Label EN, Placeholder AR, Placeholder EN, Tooltip
- **تبويب تخطيط:** Row, Col, Colspan, Rowspan, Width, Min/Max Width, Alignment
- **تبويب تنسيق:** Font Override, Color Override, Background Override, Border Override, Custom CSS
- **تبويب بيانات:** Table, Column, Data Type, Display Format, Combo Source
- **تبويب تحقق:** قائمة قواعد مع إضافة/حذف/ترتيب
- **تبويب متقدم:** Visible Condition, Enabled Condition, Default Value, Events

### 2.4 تحسين Data Binding

**الحالة الحالية:** 3 جداول hardcoded فقط

**التحسين:**
- اكتشاف ديناميكي لجداول الداتابيز (database introspection)
- عرض أعمدة كل جدول مع أنواعها
- اقتراح ذكي لربط الحقول (matching بالاسم)
- معاينة البيانات (عرض أول 5 سجلات)

### 2.5 Template Library (مكتبة القوالب)

**الهدف:** قوالب فورمز جاهزة ومصممة بشكل احترافي

**القوالب المطلوبة:**
1. **نموذج تعديل موظف** - الفورم الرئيسي مع 3 أقسام
2. **نموذج عرض ملف شخصي** - عرض بيانات read-only
3. **نموذج بيانات رئيسية** - إضافة/تعديل (أقسام، وظائف، بنوك)
4. **نموذج بحث** - حقول فلترة + زرار بحث
5. **نموذج إعدادات** - تبويبات مع checkboxes وdropdowns
6. **نموذج تقرير** - اختيار فلاتر + عرض نتائج
7. **نموذج فارغ 2 أعمدة** - قالب فارغ جاهز للتخصيص
8. **نموذج فارغ 3 أعمدة** - قالب فارغ جاهز للتخصيص

**كل قالب يتضمن:**
- تصميم احترافي مع spacing مناسب
- ألوان متوافقة مع الثيم
- أبعاد مدروسة للحقول (مش text box عريض!)
- أزرار في أماكن منطقية
- RTL support
- لمسات فنية (icons, separators, section headers)

### 2.6 تحسين Canvas

**الحالة الحالية:** Canvas بسيط 800x600 مع grid

**التحسين:**
- **Alignment Guides:** خطوط محاذاة تظهر عند السحب (كـ Photoshop)
- **Smart Snapping:** الالتصاق بحواف العناصر المجاورة
- **Multi-select:** تحديد عدة عناصر + تحريك/محاذاة جماعية
- **Align Tools:** محاذاة يسار/يمين/وسط/توزيع بالتساوي
- **Zoom:** تكبير/تصغير
- **Canvas Resize:** تغيير حجم مساحة التصميم
- **Copy/Paste:** نسخ عنصر أو مجموعة عناصر

---

## المرحلة 3: Live Edit Mode (وضع التعديل المباشر)

> **الأولوية:** 🟢 مهمة (الميزة التي يريدها المستخدم أكثر)
> **التقدير:** جلسة واحدة
> **المخرجات:** 4 ملفات جديدة في `live_editor/`

### 3.1 Live Edit Overlay (`live_editor/live_edit_overlay.py`)

**الهدف:** طبقة شفافة تُرسم فوق الفورم الشغال لتمكين التعديل المرئي

**كيف يعمل:**
```
1. المستخدم يفتح الفورم (مثلاً تعديل موظف)
2. يضغط زرار "🎨 تعديل التصميم" أو Ctrl+Shift+E
3. يظهر:
   - حدود زرقاء حول كل عنصر (widget)
   - مقابض resize في الأركان
   - شريط أدوات علوي (save, cancel, reset, undo, redo)
   - لوحة خصائص سريعة عند تحديد عنصر
4. المستخدم يسحب ويغير أحجام العناصر
5. يضغط "حفظ" → التغييرات تُكتب في .iform JSON
6. الفورم يتحدث فوراً بدون إغلاقه
```

**الميزات:**
- **Drag to reposition:** سحب أي عنصر لمكان جديد
- **Resize handles:** مقابض في الأركان لتغيير الحجم
- **Quick property popup:** نقر مزدوج يفتح نافذة خصائص مصغرة
- **Section reorder:** سحب الأقسام (Cards) لترتيبها
- **Field reorder:** سحب الحقول داخل القسم لترتيبها
- **Visual feedback:** خطوط محاذاة + تأثير ظل أثناء السحب

### 3.2 Selection Handles (`live_editor/selection_handles.py`)

**الهدف:** مقابض تحكم مرئية حول العنصر المحدد

**8 مقابض:**
```
[NW]────[N]────[NE]
  │               │
 [W]             [E]
  │               │
[SW]────[S]────[SE]
```

- مربعات زرقاء صغيرة (8x8 px) في الأركان والأضلاع
- السحب من الأركان يغير الحجم مع الحفاظ على النسبة (مع Shift)
- السحب من الأضلاع يغير بُعد واحد فقط
- السحب من الوسط يحرك العنصر

### 3.3 Property Popup (`live_editor/property_popup.py`)

**الهدف:** نافذة خصائص سريعة تظهر بجانب العنصر المحدد

**المحتوى:**
```
┌─────────────────────────────┐
│ 📝 كود الموظف               │
├─────────────────────────────┤
│ العرض:  [_250_] px          │
│ الارتفاع: [_35_] px         │
│ النص:   [كود الموظف_____]   │
│ للقراءة فقط: [✓]            │
│                              │
│ [🎨 خصائص متقدمة]           │
│ [🗑️ حذف]  [📋 نسخ]         │
└─────────────────────────────┘
```

### 3.4 Snap Guides (`live_editor/snap_guides.py`)

**الهدف:** خطوط محاذاة ذكية أثناء السحب

**أنواع المحاذاة:**
- **Edge alignment:** محاذاة حواف العناصر (يسار مع يسار، يمين مع يمين)
- **Center alignment:** محاذاة مراكز العناصر
- **Spacing guides:** عرض المسافات بين العناصر
- **Section guides:** محاذاة مع حدود الأقسام

**السلوك:**
- تظهر خطوط منقطة زرقاء عند الاقتراب (tolerance: 5px)
- الالتصاق التلقائي عند الاقتراب (snap threshold: 8px)
- عرض قيمة المسافة بين العناصر

---

## المرحلة 4: تحويل الفورمز الحالية (Migration)

> **الأولوية:** 🟡 متوسطة
> **التقدير:** جلسة واحدة
> **المخرجات:** ملفات .iform للفورمز الموجودة + تعديل الشاشات لاستخدام FormRenderer

### 4.1 تحويل Edit Employee Screen

**الحالي:** `modules/mostahaqat/screens/edit_employee/edit_employee_screen.py` (كود Python صلب)

**المطلوب:**
1. إنشاء `templates/builtin/employee_edit.iform` يحتوي تصميم الفورم
2. تعديل `EditEmployeeScreen` لاستخدام `FormRenderer` بدلاً من الكود الصلب
3. الحفاظ على نفس الـ signals والـ events

### 4.2 تحويل Employee Profile Screen

**تحويل مشابه مع:**
- حقول read-only
- أزرار الإجراءات (تعديل، إجازة، إنهاء خدمة)
- InfoCard pattern

### 4.3 تحويل Master Data Forms

**تحويل نماذج البيانات الرئيسية:**
- إضافة/تعديل قسم
- إضافة/تعديل وظيفة
- إضافة/تعديل جنسية
- إضافة/تعديل بنك
- إضافة/تعديل شركة

---

## 📏 معايير الجودة والاحتياطات

### القواعد الـ 13 الإلزامية - كيف تُطبق في هذا النظام

| # | القاعدة | التطبيق في Form System |
|---|---------|----------------------|
| 1 | Date math بـ timedelta | DatePicker يستخدم QDateEdit مباشرة - لا نحتاج timedelta |
| 2 | SQL parameterized | form_data_bridge.py يستخدم psycopg2.sql حصراً |
| 3 | Thread safety | FormStateManager يستخدم threading.Lock() |
| 4 | Singletons thread-safe | TemplateManager singleton مع lock |
| 5 | QThread cooperative | جميع DB operations في Worker مع requestInterruption |
| 6 | Widget lifecycle | FormRenderer.clear() ينظف كل widgets قبل rebuild |
| 7 | Qt type safety | LayoutEngine يستخدم int() قبل كل Qt method |
| 8 | DB connections | form_data_bridge: return connection في finally |
| 9 | Error handling | كل عملية في try/except مع app_logger |
| 10 | Security | لا يوجد تعامل مع passwords في الفورمز |
| 11 | Theme support | WidgetFactory يقرأ من get_current_palette() |
| 12 | Cross-platform | لا يوجد os.startfile, يستخدم Cairo font |
| 13 | No blocking | كل DB/file operations في background |

### احتياطات إضافية

1. **Backward Compatibility:** الفورمز القديمة (Python code) تبقى تعمل حتى يتم تحويلها
2. **JSON Validation:** التحقق من صحة هيكل JSON عند التحميل (schema validation)
3. **Error Recovery:** إذا فشل تحميل .iform، عرض رسالة واضحة مع خيار فتح في المحرر
4. **Auto-backup:** نسخة احتياطية تلقائية من .iform قبل أي تعديل
5. **Version Migration:** حقل version في JSON للتعامل مع تحديثات الهيكل
6. **Performance:** Lazy loading لبيانات Combo boxes (لا يتم تحميلها حتى يتم الحاجة)
7. **Memory:** تنظيف widgets عند إغلاق الفورم (deleteLater + remove from collections)
8. **Accessibility:** Tab order محترم، keyboard navigation كامل
9. **RTL:** كل العناصر تدعم الاتجاه من اليمين لليسار
10. **Responsive:** الفورم يتكيف مع حجم النافذة (min/max width)

### اختبارات مطلوبة لكل مرحلة

**Phase 1 Tests:**
- [ ] تحميل .iform صالح → الفورم يعرض بشكل صحيح
- [ ] تحميل .iform غير صالح → رسالة خطأ واضحة
- [ ] تحميل بيانات من DB → الحقول تمتلئ
- [ ] حفظ بيانات → DB يتحدث بنجاح
- [ ] Validation → أخطاء تظهر بشكل صحيح
- [ ] تبديل الثيم → الفورم يتحدث فوراً
- [ ] RTL layout → كل العناصر في الاتجاه الصحيح

**Phase 2 Tests:**
- [ ] Preview → يعرض الفورم كما سيظهر
- [ ] Undo/Redo → يعمل بشكل صحيح
- [ ] Templates → تُحمل وتُعدل بنجاح
- [ ] DB introspection → يكتشف الجداول والأعمدة

**Phase 3 Tests:**
- [ ] Live Edit toggle → يظهر/يخفي بشكل نظيف
- [ ] Drag → يحرك العنصر بسلاسة
- [ ] Resize → يغير الحجم مع snap
- [ ] Save → التغييرات تنعكس فوراً
- [ ] Cancel → يرجع للحالة الأصلية

**Phase 4 Tests:**
- [ ] كل فورم محول يعمل كالأصلي تماماً
- [ ] الأداء لا يقل عن الأصلي
- [ ] كل الـ signals تعمل كما هي

---

## 🔗 تكامل مع النظام الحالي

### Integration Points

1. **Theme System:** FormRenderer يستمع لتغييرات الثيم ويحدث الفورم
2. **Database Layer:** form_data_bridge يستخدم `core.database` functions
3. **Logging:** كل العمليات تُسجل في app_logger
4. **Error Handling:** الأخطاء تُلتقط وتُعرض عبر toast notifications
5. **Threading:** Worker pattern من `core.threading`
6. **Audit Trail:** التعديلات على السجلات تُسجل في audit log
7. **Module Registration:** الفورمز تُسجل كجزء من كل module
8. **Sync System:** ملفات .iform تُضاف لـ git sync

### الملفات الموجودة التي ستتأثر

| الملف | التغيير |
|------|---------|
| `modules/designer/form_builder/__init__.py` | إضافة exports جديدة |
| `modules/designer/form_builder/form_builder_window.py` | ربط Preview بـ FormRenderer |
| `modules/designer/form_builder/property_editor.py` | إضافة تبويبات جديدة |
| `modules/designer/form_builder/data_binding.py` | DB introspection ديناميكي |
| `modules/designer/form_builder/form_canvas.py` | Alignment guides + multi-select |
| `modules/mostahaqat/screens/edit_employee/` | استخدام FormRenderer |
| `modules/mostahaqat/screens/employee_profile/` | استخدام FormRenderer |

---

## 📌 البرومبت لكل جلسة

### جلسة 1: Phase 1 - FormRenderer Engine

```
أنا شغال على مشروع INTEGRA (PyQt5 + PostgreSQL).

المهمة: تنفيذ Phase 1 من خطة Form Designer Enhancement

📋 اقرأ الخطة الكاملة: claude/FORM_DESIGNER_MASTER_PLAN.md

المطلوب تنفيذه في هذه الجلسة:
1. إنشاء form_schema.py (shared/) - تعريف JSON Schema v2.0
2. إنشاء widget_factory.py - مصنع العناصر
3. إنشاء layout_engine.py - محرك التخطيط (Smart Grid + Absolute + Flow)
4. إنشاء validation_engine.py - محرك التحقق
5. إنشاء form_data_bridge.py - جسر البيانات مع async DB operations
6. إنشاء form_state_manager.py - إدارة حالة الفورم
7. إنشاء form_renderer.py - المنسق الرئيسي
8. إنشاء __init__.py لـ form_renderer/

⚠️ القواعد الإلزامية:
- SQL: parameterized queries حصراً
- Thread safety: Lock لكل shared state
- QThread: cooperative shutdown
- Widget lifecycle: cleanup في finally
- Qt type safety: int() قبل كل Qt method
- Error handling: try/except مع logging
- Theme support: get_current_palette()
- Blocking ops: كلها في background

بعد الانتهاء: commit + push + PR + update plan docs
```

### جلسة 2: Phase 2 - Enhanced Form Designer

```
أنا شغال على مشروع INTEGRA (PyQt5 + PostgreSQL).

المهمة: تنفيذ Phase 2 من خطة Form Designer Enhancement

📋 اقرأ الخطة الكاملة: claude/FORM_DESIGNER_MASTER_PLAN.md

المطلوب تنفيذه في هذه الجلسة:
1. تفعيل Preview Mode في form_builder_window.py (ربطه بـ FormRenderer)
2. تفعيل Undo/Redo بـ QUndoStack
3. تحسين property_editor.py بإضافة تبويبات (عام، تخطيط، تنسيق، بيانات، تحقق، متقدم)
4. تحسين data_binding.py بـ database introspection ديناميكي
5. إنشاء template_manager.py + 8 قوالب .iform جاهزة
6. تحسين form_canvas.py: alignment guides, multi-select, zoom

⚠️ اقرأ الكود الموجود أولاً قبل التعديل
بعد الانتهاء: commit + push + PR + update plan docs
```

### جلسة 3: Phase 3 - Live Edit Mode

```
أنا شغال على مشروع INTEGRA (PyQt5 + PostgreSQL).

المهمة: تنفيذ Phase 3 من خطة Form Designer Enhancement

📋 اقرأ الخطة الكاملة: claude/FORM_DESIGNER_MASTER_PLAN.md

المطلوب تنفيذه في هذه الجلسة:
1. إنشاء live_edit_overlay.py - الطبقة الشفافة فوق الفورم
2. إنشاء selection_handles.py - مقابض التحكم (8 مقابض + drag)
3. إنشاء property_popup.py - نافذة خصائص سريعة
4. إنشاء snap_guides.py - خطوط محاذاة ذكية
5. ربط Live Edit بـ FormRenderer (زرار Ctrl+Shift+E)
6. حفظ التغييرات مباشرة في .iform JSON

⚠️ الاحتياطات:
- لا تجمد الـ UI أثناء التعديل
- cleanup صحيح عند إنهاء وضع التعديل
- تأكد من عمل Undo/Redo في وضع التعديل

بعد الانتهاء: commit + push + PR + update plan docs
```

### جلسة 4: Phase 4 - Migration

```
أنا شغال على مشروع INTEGRA (PyQt5 + PostgreSQL).

المهمة: تنفيذ Phase 4 من خطة Form Designer Enhancement

📋 اقرأ الخطة الكاملة: claude/FORM_DESIGNER_MASTER_PLAN.md

المطلوب تنفيذه في هذه الجلسة:
1. تحويل EditEmployeeScreen → FormRenderer + employee_edit.iform
2. تحويل EmployeeProfileScreen → FormRenderer + employee_profile.iform
3. تحويل MasterDataWindow → FormRenderer + master_data.iform
4. التأكد من أن كل الـ signals والـ events تعمل كالأصلي
5. اختبار كل فورم محول

⚠️ اقرأ الكود الأصلي بالكامل أولاً
⚠️ الفورم المحول يجب أن يعمل بنفس الطريقة بالضبط
⚠️ لا تحذف الكود القديم - اتركه كـ fallback

بعد الانتهاء: commit + push + PR + update plan docs
```

---

## 📊 جدول المتابعة

| المرحلة | الحالة | تاريخ البدء | تاريخ الانتهاء | الملاحظات |
|---------|--------|------------|---------------|-----------|
| Phase 1: FormRenderer | ✅ مكتمل + مراجعة | 2026-02-10 | 2026-02-10 | 8 ملفات في form_renderer/ و shared/ + مراجعة شاملة: إصلاح 26 مشكلة (1 CRITICAL, 13 HIGH, 9 MEDIUM, 3 LOW) |
| Phase 2: Designer Enhancement | ✅ مكتمل | 2026-02-10 | 2026-02-10 | Preview, Undo/Redo, Property Tabs, DB Introspection, 8 Templates, Canvas Improvements |
| Phase 3: Live Edit Mode | 🔴 لم يبدأ | - | - | يعتمد على Phase 1 |
| Phase 4: Migration | 🔴 لم يبدأ | - | - | يعتمد على Phase 1+2+3 |

---

## 📝 ملاحظات المستخدم (Mohamed)

> هذا القسم مخصص لملاحظاتك الشخصية على الخطة.
> أضف هنا أي تعديلات أو تفضيلات أو أفكار إضافية.

---

*آخر تحديث: 2026-02-10*
