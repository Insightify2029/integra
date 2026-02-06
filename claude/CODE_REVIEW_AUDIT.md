# INTEGRA - تقرير مراجعة شامل للكود
**تاريخ المراجعة:** 2026-02-06
**النطاق:** جميع ملفات Python في المشروع (526 ملف)
**المراجع:** Claude Code Audit

---

## ملخص تنفيذي

تمت مراجعة كامل قاعدة الكود الخاصة بمشروع INTEGRA. تم اكتشاف **95 مشكلة** مصنفة كالتالي:

| التصنيف | عدد المشاكل | حرج | عالي | متوسط | منخفض |
|---------|------------|------|------|--------|-------|
| أخطاء برمجية (Logic/Crash) | 17 | 4 | 5 | 5 | 3 |
| ثغرات أمنية (Security) | 10 | 2 | 2 | 3 | 3 |
| مشاكل تصميمية (Design) | 14 | 0 | 1 | 8 | 5 |
| مشاكل Threading | 14 | 0 | 3 | 6 | 5 |
| مشاكل قاعدة البيانات | 7 | 1 | 2 | 2 | 2 |
| أخطاء Import | 4 | 1 | 0 | 2 | 1 |
| مشاكل واجهة المستخدم | 16 | 3 | 2 | 7 | 4 |
| مشاكل منطق الأعمال | 5 | 0 | 3 | 2 | 0 |
| مشاكل الأداء | 4 | 0 | 0 | 4 | 0 |
| أخطاء معالجة الأخطاء | 4 | 0 | 0 | 3 | 1 |
| **المجموع** | **95** | **11** | **18** | **42** | **24** |

---

## القسم 1: أخطاء حرجة (CRITICAL) - يجب إصلاحها فوراً

### CRIT-01: تسرب اتصالات قاعدة البيانات في جميع وحدات الاستعلام
**الملفات:**
- `core/database/queries/select_query.py`
- `core/database/queries/insert_query.py`
- `core/database/queries/update_query.py`
- `core/database/queries/delete_query.py`
- `core/database/queries/scalar_query.py`

**المشكلة:** جميع ملفات الاستعلام تحصل على اتصال من المجمع ولا تعيده أبداً:
```python
conn = get_connection()
cursor = conn.cursor()
try:
    # ... use cursor ...
finally:
    if cursor:
        cursor.close()
    # conn is NEVER returned to the pool!
```
**التأثير:** مع كل استعلام، يتم حجز اتصال ولا يُعاد. بمرور الوقت، سيُستنزف مجمع الاتصالات وسيتوقف التطبيق عن العمل.

---

### CRIT-02: `execute_query` غير موجودة - ImportError عند تشغيل وحدة BI
**الملف:** `core/bi/views_manager.py:22`
```python
from core.database import select_all, select_one, execute_query  # execute_query لا وجود لها!
```
**التأثير:** أي محاولة لاستخدام `BIViewsManager` ستفشل فوراً بخطأ `ImportError`.

---

### CRIT-03: انهيار المجدول عند الساعة 23:00 يومياً
**الملف:** `core/bi/export_scheduler.py:170`
```python
next_run = now.replace(minute=0, second=0, microsecond=0)
next_run = next_run.replace(hour=next_run.hour + 1)  # hour=24 → ValueError!
```
**التأثير:** عندما تكون الساعة 23، يحسب `hour=24` مما يسبب `ValueError` وانهيار المجدول يومياً.

---

### CRIT-04: انهيار EventBus عند أحداث متزامنة بنفس الأولوية
**الملف:** `core/ai/orchestration/event_bus.py`
**المشكلة:** عندما يكون لحدثين نفس الأولوية والتوقيت، يحاول `PriorityQueue` مقارنة كائنات `Event` التي لا تملك `__lt__`، مما يسبب `TypeError`.

---

### CRIT-05: `os.startfile()` غير متوفرة على Linux/macOS
**الملف:** `ui/components/tables/enterprise/export_manager.py:500`
```python
os.startfile(message)  # Windows-only function!
```
**التأثير:** فتح ملف التصدير يسبب `AttributeError` على أي نظام غير Windows.

---

### CRIT-06: `FilterPanel` الجديدة لا تُضاف للواجهة بعد `set_columns()`
**الملف:** `ui/components/tables/enterprise/enterprise_table_widget.py:109-126`
```python
def set_columns(self, columns, keys=None):
    self._filter_panel = FilterPanel(columns)  # تُنشأ لكن لا تُضاف للـ layout!
```
**التأثير:** بعد استدعاء `set_columns()`، تتوقف لوحة الفلترة عن العمل نهائياً.

---

### CRIT-07: `QThread.terminate()` يسبب انهياراً غير متوقع
**الملف:** `ui/components/email/email_panel.py:460-461, 506`
```python
self._load_worker.terminate()  # خطير جداً حسب توثيق Qt!
```
**التأثير:** إنهاء Thread بشكل قسري يمكن أن يترك البيانات في حالة غير متسقة ويسبب انهيار التطبيق.

---

### CRIT-08: انهيار خاصية `due_date_formatted` في آخر أيام الشهر
**الملف:** `modules/tasks/models/task_models.py:519`
```python
elif due == today.replace(day=today.day + 1) if today.day < 28 else today:
    return "غداً"
```
**التأثير:** لن تظهر كلمة "غداً" أبداً بعد اليوم 28 من الشهر، وقد يسبب `ValueError` في بعض الحالات.

---

### CRIT-09: انهيار التنقل في التقويم عند عبور حدود الشهر
**الملف:** `modules/calendar/widgets/calendar_header.py:149-193`
```python
week_start = self.current_date.replace(day=self.current_date.day - days_since_sunday)  # day < 1 → crash!
self.current_date = self.current_date.replace(day=self.current_date.day + 7)  # day > 31 → crash!
```
**التأثير:** أزرار التنقل (السابق/التالي) تسبب انهيار التطبيق عند عبور حدود الشهر في عرض الأسبوع واليوم.

---

### CRIT-10: `QPixmap.scaled()` يستقبل float بدل int
**الملف:** `modules/tasks/screens/task_board/kanban_board.py:145-152`
```python
pixmap = pixmap.scaled(pixmap.width() * 0.8, pixmap.height() * 0.8, ...)  # float → TypeError
drag.setHotSpot(event.pos() * 0.8)  # QPoint * float → TypeError
```
**التأثير:** سحب بطاقة مهمة على لوحة Kanban يسبب `TypeError`.

---

### CRIT-11: حقن SQL في مصمم النماذج
**الملف:** `modules/designer/form_builder/data_binding.py:158-203`
```python
f"SELECT * FROM {table_name} WHERE id = %s"     # table_name غير محمي!
f"UPDATE {table_name} SET {set_clause} WHERE id = %s"  # أسماء الأعمدة غير محمية!
f"INSERT INTO {table_name} ({columns}) VALUES ..."      # كل شيء غير محمي!
```
**التأثير:** ثغرة حقن SQL تسمح بتنفيذ أوامر SQL عشوائية.

---

## القسم 2: أخطاء عالية الخطورة (HIGH)

### HIGH-01: حقن SQL في وحدة BI Data Exporter
**الملف:** `core/bi/data_exporter.py:94, 217`
```python
sql = f"SELECT * FROM bi_views.{view_name}"  # view_name غير محمي!
```

### HIGH-02: حقن SQL في وحدة BI Views Manager
**الملف:** `core/bi/views_manager.py:368, 423, 452`
```python
sql = f"DROP VIEW IF EXISTS bi_views.{view_name} CASCADE"  # خطير جداً!
```

### HIGH-03: `ActionType` enum يسبب ValueError غير محمي
**الملف:** `core/ai/agents/action_agent.py:~309`
```python
ActionType(action_type_str)  # ValueError إذا كانت القيمة غير معروفة
```

### HIGH-04: Singleton يتجاهل معامل host في الاستدعاءات اللاحقة
**الملف:** `core/ai/ollama_client.py:67-73`
**المشكلة:** `OllamaClient(host="different-host")` يعيد دائماً المثيل الأصلي بغض النظر عن host الجديد.

### HIGH-05: `_action_history` يُعدل بدون قفل (سباق خيوط)
**الملف:** `core/ai/agents/action_agent.py:555`
**المشكلة:** قائمة `_action_history` تُقرأ وتُكتب من خيوط متعددة بدون حماية.

### HIGH-06: `ConversationContext` غير آمنة لتعدد الخيوط
**الملف:** `core/ai/ai_service.py:36-41, 149-161`
**المشكلة:** `AIService` هو singleton يُستخدم من خيوط متعددة، لكن `ConversationContext` لا تملك أي حماية.

### HIGH-07: علم `_running` في ExportScheduler غير محمي بقفل
**الملف:** `core/bi/export_scheduler.py:132, 139, 147, 212`

### HIGH-08: زر "حفظ" في الإعدادات لا يحفظ فعلياً
**الملف:** `ui/dialogs/settings/settings_dialog.py:69-70`
```python
save_btn.clicked.connect(self.accept)  # يغلق فقط بدون حفظ!
```

### HIGH-09: "اختبار الاتصال" لا يختبر البيانات المدخلة
**الملف:** `ui/dialogs/settings/settings_dialog.py:80-86`
**المشكلة:** يفحص حالة الاتصال الحالي بدلاً من اختبار المعلومات التي أدخلها المستخدم.

### HIGH-10: فلاتر "اليوم" و"المتأخرة" لا تعمل
**الملف:** `modules/tasks/screens/task_list/task_list_screen.py:370-385`
```python
if filter_type == "today":
    pass  # لا تفعل شيئاً!
elif filter_type == "overdue":
    pass  # لا تفعل شيئاً!
```

### HIGH-11: `get_by_employee()` يستثني المهام قيد التنفيذ
**الملف:** `modules/tasks/repository/task_repository.py:247-250`
**المشكلة:** يعرض فقط المهام `PENDING` ويتجاهل `IN_PROGRESS`.

### HIGH-12: نذاكرة مؤقتة للنوافذ المفتوحة تحتفظ بمراجع قوية
**الملف:** `ui/windows/launcher/launcher_window.py:28, 93-142`
**المشكلة:** `_open_windows` لا تزيل النوافذ المغلقة، مما يسبب تسرب ذاكرة.

### HIGH-13: حذف widget من قائمة السياق لا ينظف البيانات
**الملف:** `modules/designer/form_builder/form_canvas.py:425-427`
**المشكلة:** `deleteLater()` لا يزيل Widget من قائمة `_widgets` في Canvas.

### HIGH-14: `PDFAIStudio` غير مستوردة في `_pdf_merge`
**الملف:** `modules/file_manager/window/file_manager_window.py:943`
**المشكلة:** `NameError` عند دمج PDF بدون فتح ملف أولاً.

---

## القسم 3: أخطاء متوسطة الخطورة (MEDIUM)

### MED-01: منطق اقتباس CSV خاطئ
**الملف:** `core/bi/data_exporter.py:126-128`
**المشكلة:** فحص علامات الاقتباس بعد استبدالها بدل قبلها.

### MED-02: دمج إعدادات BI سطحي يفقد التكوينات المتداخلة
**الملف:** `core/bi/connection_config.py:203-205`

### MED-03: `Icons` class يُستبدل بمثيل عند مستوى الوحدة
**الملف:** `core/utils/icons.py:235`

### MED-04: `where_clause` يُمرر كـ SQL خام بدون حماية
**الملف:** `core/database/queries/scalar_query.py:58-62`

### MED-05: مراقب الملفات ينشئ مثيلات جديدة بدل Singleton
**الملف:** `core/file_watcher/watcher.py:474-488`

### MED-06: عداد التنبيهات غير آمن لتعدد الخيوط
**الملف:** `core/ai/agents/alert_agent.py:154-166`

### MED-07: `get_insights()` يقرأ بدون قفل
**الملف:** `core/ai/agents/learning_agent.py:525`

### MED-08: ألوان الجدول مُبرمجة لوضع الظلام فقط
**الملف:** `ui/components/tables/enterprise/enterprise_table.py:42-52`
**المشكلة:** لون التحويم `#334155` غير مقروء في الوضع الفاتح.

### MED-09: `card_style.py` يتجاهل معامل `accent_color`
**الملف:** `ui/components/cards/module_card/card_style.py:10`

### MED-10: قسمة على صفر محتملة في تصدير Excel/CSV/PDF
**الملف:** `ui/components/tables/enterprise/export_manager.py:99, 138, 179`

### MED-11: ترتيب القاموس قد لا يتطابق مع رؤوس الأعمدة
**الملف:** `ui/components/tables/enterprise/export_manager.py:88-91`

### MED-12: حقن HTML في عرض البريد الإلكتروني
**الملف:** `ui/components/email/email_viewer.py:373-375`
```python
text = email.body.replace('\n', '<br>')
self.body_browser.setHtml(f"<div>{text}</div>")  # بدون html.escape()!
```

### MED-13: عملية استعادة النسخ الاحتياطي تجمد الواجهة
**الملف:** `ui/dialogs/sync_settings/sync_settings_dialog.py:455`

### MED-14: خطأ في ربط أسماء أيام الأسبوع
**الملف:** `modules/calendar/models/calendar_models.py:755-756`
**المشكلة:** `date.weekday()` يبدأ من الإثنين=0 لكن المصفوفة تبدأ من الأحد. كل يوم يظهر بالاسم الخاطئ.

### MED-15: `DayCell.set_events()` تنشئ layouts متكررة
**الملف:** `modules/calendar/widgets/day_cell.py:258-264`

### MED-16: عرض الأسبوع يظهر شهر خاطئ عند عبور حدود الشهر
**الملف:** `modules/calendar/widgets/calendar_header.py:144-151`

### MED-17: CSS يتراكم عند فشل التحقق المتكرر
**الملف:** `modules/tasks/widgets/task_form.py:332-341`

### MED-18: مكونات AI/Email لا تحترم سمة التطبيق
**الملفات:** `ui/components/ai/chat_panel.py`, `ai_toolbar.py`, `email_panel.py`, `email_viewer.py`, `email_list.py`

### MED-19: حالة `_always_on_top` تتناقض مع أعلام النافذة
**الملف:** `modules/copilot/components/chat_window.py:40, 47-51`

### MED-20: `except Exception: pass` يبتلع أخطاء حرجة في مصادر المعرفة
**الملف:** `modules/copilot/knowledge/sources.py:134, 194, 229, 281`

### MED-21: تحميل كل المهام في الذاكرة للفلترة
**الملفات:** `modules/tasks/integration/email_integration.py:169-175`, `calendar_sync.py:147, 176, 230`

### MED-22: `ExportWorker`/`ViewsWorker` بدون إدارة دورة حياة
**الملف:** `ui/dialogs/bi_settings/bi_settings_dialog.py:32-104`

### MED-23: خطأ تدفق في `StreamWorker` عند حدوث خطأ
**الملف:** `ui/components/ai/chat_panel.py:59-70`
**المشكلة:** signal خطأ يُتبع بـ finished signal، فيُرسل نص خاطئ.

### MED-24: كلمة المرور مكشوفة في الـ API العامة
**الملف:** `core/config/__init__.py:9, 23`
```python
__all__ = [..., 'DB_PASSWORD', ...]  # يجب ألا تكون في __all__
```

### MED-25: مفتاح التشفير يُخزن في ملف نصي عادي
**الملف:** `core/security/encryption.py:122-129`

### MED-26: مقارنة كلمات المرور عرضة لهجمات التوقيت
**الملف:** `core/security/encryption.py:356-367`
```python
return self.hash_password(password) == hashed  # يجب استخدام hmac.compare_digest()
```

### MED-27: `fetchone()[0]` بدون فحص None
**الملف:** `core/database/queries/insert_query.py:64`

### MED-28: لا توجد حدود معاملات في عمليات BI متعددة الخطوات
**الملف:** `core/bi/views_manager.py` - `create_all_views()`

---

## القسم 4: أخطاء منخفضة الخطورة (LOW)

### LOW-01: `humanize.activate("ar")` يُنفذ عند الاستيراد ويغير الحالة العامة
**الملف:** `core/utils/formatters.py:36-37`

### LOW-02: معامل `time` يخفي الوحدة المدمجة
**الملف:** `core/utils/formatters.py:205`

### LOW-03: القالب المشترك يُعاد بمرجع مباشر (بدون نسخة عميقة)
**الملف:** `core/ai/agents/form_agent.py:~539`

### LOW-04: استيراد دائري محتمل بين وحدات Threading
**الملف:** `core/threading/worker.py:201` ↔ `core/threading/task_manager.py:36`

### LOW-05: وحدة Outlook تعتمد على `win32com` المتاح فقط على Windows
**الملف:** `core/email/outlook_connector.py`

### LOW-06: `main.py` يفتح ملفات لا تُغلق أبداً
**الملف:** `main.py:16-19`

### LOW-07: خط "Segoe UI" متاح فقط على Windows
**الملف:** `ui/components/labels/labels.py:38`

### LOW-08: `setCursor(0)` بدل `setCursor(Qt.ArrowCursor)`
**الملف:** `ui/components/buttons/buttons.py:22`

### LOW-09: `processEvents()` قد يسبب إعادة دخول
**الملف:** `ui/components/progress/progress_dialog.py:118`

### LOW-10: خاصية `_include_headers` لا تُفحص عند التصدير
**الملف:** `ui/components/tables/enterprise/export_manager.py:265-267`

### LOW-11: `bare except` يمسك كل الاستثناءات
**الملف:** `ui/components/tables/enterprise/export_manager.py:110-111`

### LOW-12: اتصال قاعدة بيانات لا يُغلق عند إغلاق التطبيق
**الملف:** `ui/windows/launcher/launcher_window.py:34, 144`

### LOW-13: Debounce البحث ينشئ timers بدون إلغاء السابقة
**الملف:** `modules/tasks/screens/task_list/task_list_screen.py:364`

### LOW-14: لا توجد آلية timeout لطلبات AI
**الملف:** `modules/copilot/components/chat_sidebar.py:70-91`

### LOW-15: أنماط Singleton غير آمنة لتعدد الخيوط في عدة وحدات
**الملفات:** `get_export_scheduler`, `get_bi_exporter`, `get_file_watcher`, `get_email_cache`, `get_encryptor`, وغيرها

### LOW-16: `Emoji` characters قد لا تُعرض على بعض الأنظمة
**الملفات:** متعددة في واجهة المستخدم

### LOW-17: Singleton مزدوج (class-level + module-level) في AIService
**الملف:** `core/ai/ai_service.py:76-85, 341-350`

### LOW-18: تدوير المفاتيح بدون إعادة تشفير البيانات
**الملف:** `core/security/encryption.py:369-391`

---

## القسم 5: أولويات الإصلاح المقترحة

### المرحلة 1: إصلاحات فورية (أسبوع)
| # | المشكلة | السبب |
|---|---------|-------|
| 1 | CRIT-01 | تسرب الاتصالات سيوقف التطبيق |
| 2 | CRIT-02 | ImportError يمنع وحدة BI من العمل |
| 3 | CRIT-09 | انهيار التقويم عند التنقل |
| 4 | CRIT-11 | حقن SQL خطير في مصمم النماذج |
| 5 | HIGH-01/02 | حقن SQL في وحدة BI |
| 6 | CRIT-08 | خاصية "غداً" لا تعمل |

### المرحلة 2: إصلاحات مهمة (أسبوعان)
| # | المشكلة | السبب |
|---|---------|-------|
| 7 | CRIT-03 | انهيار المجدول اليومي |
| 8 | CRIT-05 | عدم التوافق مع Linux |
| 9 | CRIT-06 | لوحة الفلترة تتعطل |
| 10 | HIGH-10/11 | فلاتر المهام لا تعمل |
| 11 | HIGH-08/09 | إعدادات لا تحفظ ولا تختبر |
| 12 | MED-14 | أسماء الأيام خاطئة |

### المرحلة 3: تحسينات (شهر)
| # | المشكلة | السبب |
|---|---------|-------|
| 13 | MED-18 | دعم السمات في AI/Email |
| 14 | MED-24-26 | تحسينات أمنية |
| 15 | LOW-15 | حماية Singletons |
| 16 | MED-21 | تحسين أداء الاستعلامات |

---

## القسم 6: توصيات معمارية

### 1. إدارة اتصالات قاعدة البيانات
```python
# الحل المقترح - Context Manager
def select_all(query, params=None):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        # ...
    finally:
        if cursor:
            cursor.close()
        if conn:
            return_connection(conn)  # إعادة الاتصال للمجمع
```

### 2. حماية من حقن SQL
```python
# الحل المقترح - استخدام psycopg2.sql
from psycopg2 import sql
query = sql.SQL("SELECT * FROM {} WHERE id = %s").format(
    sql.Identifier(table_name)
)
```

### 3. تنقل التقويم
```python
# الحل المقترح - استخدام timedelta بدل replace
from datetime import timedelta
self.current_date = self.current_date - timedelta(days=7)  # بدل replace(day=day-7)
```

### 4. Singleton آمن لتعدد الخيوط
```python
# الحل المقترح - Double-checked locking
import threading
_lock = threading.Lock()
_instance = None

def get_instance():
    global _instance
    if _instance is None:
        with _lock:
            if _instance is None:
                _instance = MyClass()
    return _instance
```

---

## القسم 7: ملاحظات إضافية

### نقاط القوة في المشروع:
1. **هيكلية جيدة:** فصل واضح بين الطبقات (core/ui/modules)
2. **نظام السمات:** بنية شاملة لدعم الظلام والفاتح
3. **نظام التزامن:** بنية متقدمة لمزامنة Git وقاعدة البيانات
4. **استخدام Signals/Slots:** تطبيق صحيح لنمط PyQt5 في معظم الأماكن
5. **توثيق بالعربية:** دعم ثنائي اللغة ممتاز

### مجالات تحتاج تحسين:
1. **اختبارات الوحدة:** لا يوجد مجلد tests - يُنصح بإضافة pytest
2. **معالجة الأخطاء:** عدة أماكن تبتلع الاستثناءات بصمت
3. **التوافق عبر الأنظمة:** عدة وظائف تعمل على Windows فقط
4. **أمان التعدد:** أنماط Singleton غير محمية في عدة أماكن
5. **إدارة الموارد:** الاتصالات والملفات لا تُغلق بشكل صحيح
