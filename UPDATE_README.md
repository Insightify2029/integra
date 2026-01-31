# INTEGRA v2.1 Update - Enterprise Tables
# ========================================
# تحديث: الجداول فائقة التطور + شاشة ملف الموظف

## 📁 الملفات الجديدة:

### 1. Enterprise Table Component
```
ui/components/tables/enterprise/
├── __init__.py
├── enterprise_table.py          # الجدول الأساسي
├── enterprise_table_widget.py   # الويدجت الكامل (استخدم ده)
├── table_toolbar.py             # شريط الأدوات
├── search_box.py                # صندوق البحث
├── filter_panel.py              # لوحة التصفية
├── column_chooser.py            # اختيار الأعمدة
└── export_manager.py            # التصدير
```

### 2. Employees Screens
```
modules/mostahaqat/screens/
├── __init__.py
├── employees_list/
│   ├── __init__.py
│   └── employees_list_screen.py   # شاشة قائمة الموظفين
└── employee_profile/
    ├── __init__.py
    └── employee_profile_screen.py # شاشة ملف الموظف
```

## 🔧 طريقة التثبيت:

1. انسخ مجلد `ui/components/tables/enterprise/` إلى المشروع
2. انسخ مجلد `modules/mostahaqat/screens/` إلى المشروع
3. اعمل commit و push

## 📋 طريقة الاستخدام:

### Enterprise Table:
```python
from ui.components.tables.enterprise import EnterpriseTableWidget

table = EnterpriseTableWidget()
table.set_title("قائمة الموظفين")
table.set_columns(["الكود", "الاسم"], ["code", "name"])
table.set_data([{"code": "001", "name": "أحمد"}])
table.row_double_clicked.connect(self.on_row_clicked)
```

### Employee Profile:
```python
from modules.mostahaqat.screens import EmployeeProfileScreen

profile = EmployeeProfileScreen()
profile.set_employee(employee_data)
profile.edit_clicked.connect(self.on_edit)
```

## ✨ المميزات:

### الجدول فائق التطور:
- ✅ نقر مزدوج لفتح التفاصيل
- ✅ ترتيب على كل الأعمدة
- ✅ بحث فوري
- ✅ تصفية ذكية
- ✅ تصدير (Excel/PDF/CSV)
- ✅ إظهار/إخفاء الأعمدة
- ✅ تحديد متعدد
- ✅ دعم RTL

### شاشة ملف الموظف:
- ✅ عرض كل البيانات
- ✅ زر تعديل
- ✅ زر إيقاف
- ✅ زر تسوية إجازة
- ✅ زر نهاية خدمة
- ✅ زر حساب الإضافي
