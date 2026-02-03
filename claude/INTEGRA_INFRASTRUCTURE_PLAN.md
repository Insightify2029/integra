# INTEGRA v2.1 - خطة تطوير البنية التحتية المتقدمة
**التاريخ:** 2 فبراير 2026
**الحالة:** مسودة للمراجعة والاعتماد

---

## نظرة عامة

هذه الخطة تغطي **4 محاور رئيسية** لتطوير البنية التحتية:

| المحور | الوصف | الأولوية |
|---|---|---|
| **A** | البنية التحتية الأساسية (من ERP Research) | أساسي - يُبنى عليه كل شيء |
| **B** | الذكاء الاصطناعي المدمج (Ollama AI) | استراتيجي - يرفع كفاءة العمل |
| **C** | موديول الإيميل (Outlook Classic Sync) | تشغيلي - يربط سير العمل اليومي |
| **D** | تحسينات المكتبات المتاحة (Enhancement Track) | تحسيني - استغلال الإمكانيات الموجودة |

> **ملاحظة مهمة:** المحور D يعتمد على تحليل ملف `claude/ALL_Libraries.txt` لاستغلال المكتبات المثبتة فعلياً

---

## المحور A: البنية التحتية الأساسية

> مصدر: ERP Infrastructure Research + أنماط Odoo/ERPNext

### A1. نظام Logging احترافي (Loguru) ✅ **مكتمل**
- **الحالة:** ✅ تم التنفيذ
- **المكتبة:** `loguru` (مثبتة ✅)
- **المطلوب:**
  - ملفات log يومية مع rotation (10MB) و retention (30 يوم) ✅
  - مستويات: DEBUG/INFO/WARNING/ERROR/CRITICAL ✅
  - ملف audit منفصل لتتبع العمليات الحساسة (رواتب، تعديلات موظفين) ✅
  - JSON structured logging للتحليل ✅
- **الملفات المنفذة:**
  - `core/logging/app_logger.py` ✅
  - `core/logging/audit_logger.py` ✅

### A2. معالجة الأخطاء الشاملة (Global Exception Handler) ✅ **مكتمل**
- **الحالة:** ✅ تم التنفيذ
- **المطلوب:**
  - التقاط كل الأخطاء غير المعالجة في PyQt5 ✅
  - عرض رسالة خطأ واضحة للمستخدم ✅
  - تسجيل التفاصيل الكاملة في log ✅
  - منع البرنامج من الإغلاق المفاجئ ✅
- **الملفات المنفذة:**
  - `core/error_handling/exception_hook.py` ✅

### A3. الحفظ التلقائي (Auto-Save + Recovery)
- **المطلوب:**
  - QTimer كل 60 ثانية لحفظ البيانات غير المحفوظة
  - ملفات recovery في مجلد مخصص
  - فحص عند بدء التشغيل لاسترجاع البيانات
  - إشعار المستخدم بوجود بيانات قابلة للاسترجاع
- **الملفات:**
  - `core/recovery/auto_save.py`
  - `core/recovery/recovery_manager.py`

### A4. Audit Trail بالـ Database (PostgreSQL Triggers)
- **المطلوب:**
  - جدول `audit.logged_actions` لتسجيل كل تغيير
  - Trigger على الجداول الحساسة (employees, payroll, contracts)
  - تسجيل: مين غيّر + إيه اللي اتغيّر + القيم القديمة والجديدة + الوقت
  - شاشة عرض سجل التدقيق في البرنامج
- **الملفات:**
  - `core/database/audit/audit_schema.sql`
  - `core/database/audit/audit_triggers.sql`
  - `modules/mostahaqat/screens/audit_log/`

### A5. معالجة خلفية آمنة (Background Processing) ✅ **مكتمل**
- **الحالة:** ✅ تم التنفيذ (2026-02-03)
- **المطلوب:**
  - QThreadPool + Worker pattern موحد ✅
  - Connection pool لقاعدة البيانات (thread-safe) ⏳ (لاحقاً)
  - Progress signals للـ UI ✅
  - إدارة مركزية للمهام الخلفية ✅
- **الملفات المنفذة:**
  - `core/threading/__init__.py` ✅
  - `core/threading/worker.py` ✅
  - `core/threading/task_manager.py` ✅
- **ملفات مؤجلة:**
  - `core/database/connection/pool.py` (سيُنفذ مع A4 Audit)

### A6. الجدولة (APScheduler)
- **المكتبة:** `apscheduler` (تحتاج تثبيت)
- **المطلوب:**
  - QtScheduler متكامل مع PyQt5 event loop
  - تخزين الـ jobs في PostgreSQL (SQLAlchemyJobStore)
  - معالجة المهام الفائتة (misfire handling)
  - واجهة لإدارة المهام المجدولة
- **الملفات:**
  - `core/scheduler/scheduler_manager.py`
  - `core/scheduler/job_store.py`

### A7. مراقبة الملفات (File Watching)
- **المكتبة:** `watchdog` (تحتاج تثبيت)
- **المطلوب:**
  - Hot folder لاستيراد ملفات Excel/CSV تلقائياً
  - Debouncing + stability detection
  - 4 مجلدات: input → processing → archive → error
  - تكامل مع نظام الاستيراد
- **الملفات:**
  - `core/file_watcher/watcher.py`
  - `core/file_watcher/hot_folder.py`

### A8. النسخ الاحتياطي المتقدم
- **المطلوب:**
  - نسخ تلقائي مجدول (يومي/أسبوعي/شهري - GFS)
  - pg_dump بصيغة مضغوطة (-Fc)
  - Checksum للتحقق من سلامة النسخة
  - تنظيف تلقائي للنسخ القديمة
  - تكامل مع APScheduler
- **الملفات:**
  - `core/backup/backup_manager.py`
  - `core/backup/retention_policy.py`

### A9. الأمان (Security)
- **المكتبات:** `argon2-cffi`, `keyring` (تحتاج تثبيت)
- **المطلوب:**
  - Argon2 password hashing
  - OS keyring لتخزين بيانات الاتصال
  - RBAC (Role-Based Access Control)
  - Account lockout بعد محاولات فاشلة
- **الملفات:**
  - `core/security/auth_manager.py`
  - `core/security/credential_store.py`
  - `core/security/rbac.py`

### A10. التحقق متعدد المستويات (Validation)
- **المكتبة:** `pydantic` (مثبتة ✅)
- **المطلوب:**
  - Pydantic schemas لكل entity (Employee, Payroll, etc.)
  - PostgreSQL constraints كخط دفاع أخير
  - رسائل خطأ واضحة بالعربي
- **الملفات:**
  - `core/validation/schemas/employee.py`
  - `core/validation/schemas/payroll.py`

---

## المحور B: الذكاء الاصطناعي المدمج (Ollama AI)

### المفهوم
دمج Ollama AI محلياً داخل INTEGRA لتحليل البيانات، قراءة الإيميلات، توليد التقارير، والتنبيهات الذكية - بدون إنترنت وبخصوصية كاملة.

### التقنيات
| المكون | التقنية |
|---|---|
| AI Engine | Ollama (مثبت محلياً) |
| Python Library | `ollama` (pip install ollama) |
| الاتصال | localhost:11434 (REST API) |
| التكامل مع UI | QThread workers + streaming |

### B1. طبقة الاتصال (AI Service Layer)
- **المطلوب:**
  - Client class للاتصال بـ Ollama
  - فحص حالة الخدمة (متوفرة/غير متوفرة)
  - إدارة المودلات المتاحة
  - Streaming support مع QThread
  - System prompts مخصصة لكل وظيفة
- **الملفات:**
  - `core/ai/ollama_client.py`
  - `core/ai/ai_service.py`
  - `core/ai/prompts/` (مجلد للـ system prompts)

### B2. مساعد الإيميل الذكي
- **المطلوب:**
  - قراءة وتلخيص الإيميلات
  - استخراج المهام (Tasks) من الإيميلات
  - تصنيف الإيميلات (عاجل/مهم/عادي)
  - اقتراح ردود
  - كشف إيميلات تحتاج إجراء فوري
- **الملفات:**
  - `core/ai/agents/email_agent.py`

### B3. مساعد البيانات
- **المطلوب:**
  - تحليل بيانات الموظفين والرواتب
  - كشف الأخطاء والشذوذ في البيانات
  - اقتراح تصحيحات
  - توليد ملخصات وتقارير نصية
- **الملفات:**
  - `core/ai/agents/data_agent.py`

### B4. نظام التنبيهات الذكية
- **المطلوب:**
  - تحليل دوري للبيانات واكتشاف أنماط تحتاج انتباه
  - تنبيهات: عقود قاربت على الانتهاء، رواتب غير طبيعية، مهام متأخرة
  - أولويات: عاجل (أحمر) / مهم (برتقالي) / عادي (أزرق)
- **الملفات:**
  - `core/ai/agents/alert_agent.py`

### B5. واجهة الـ AI في البرنامج
- **المطلوب:**
  - شريط جانبي أو نافذة chat مع الـ AI
  - عرض النتائج مع streaming (حرف بحرف)
  - أزرار سريعة: "لخّص الإيميلات" / "راجع الرواتب" / "إيه المهام؟"
  - سجل المحادثات
- **الملفات:**
  - `ui/components/ai/chat_panel.py`
  - `ui/components/ai/ai_toolbar.py`

### المودلات المقترحة لـ Ollama
| الاستخدام | المودل | الحجم |
|---|---|---|
| تحليل عام + عربي | `gemma3` أو `llama3.2` | 4-8GB |
| تلخيص + استخراج مهام | `mistral` | 4GB |
| كود + تحليل بيانات | `codellama` | 4GB |

> **ملاحظة:** نحتاج نعرف إمكانيات الأجهزة (RAM + GPU) عشان نختار المودل المناسب.

---

## المحور C: موديول الإيميل (Outlook Classic Sync)

### المفهوم
تزامن كامل مع Outlook Classic عبر COM automation (pywin32) - كل الإيميلات تظهر داخل INTEGRA مع إمكانية البحث، التصنيف، والتحليل بالذكاء الاصطناعي.

### التقنيات
| المكون | التقنية |
|---|---|
| COM Automation | `pywin32` (win32com.client) |
| Outlook Object Model | MAPI Namespace |
| التزامن | QThread + QTimer (polling) |
| التخزين المحلي | PostgreSQL (email cache) |

### C1. طبقة الاتصال بـ Outlook
- **المطلوب:**
  - الاتصال بـ Outlook Classic عبر COM
  - الوصول لكل المجلدات (Inbox, Sent, Drafts, Custom folders)
  - قراءة الإيميلات: الموضوع، المرسل، التاريخ، النص، المرفقات
  - إرسال إيميلات من داخل INTEGRA
  - نقل/نسخ إيميلات بين المجلدات
- **الملفات:**
  - `core/email/outlook_connector.py`
  - `core/email/outlook_reader.py`
  - `core/email/outlook_sender.py`

### C2. التزامن والتخزين المحلي
- **المطلوب:**
  - جدول `emails` في PostgreSQL لتخزين cache محلي
  - جدول `email_attachments` للمرفقات
  - جدول `email_folders` لهيكل المجلدات
  - مزامنة دورية (كل 5 دقائق عبر QTimer)
  - مزامنة تزايدية (incremental - الجديد فقط)
  - فهرسة نص كامل (Full-Text Search) في PostgreSQL
- **الملفات:**
  - `core/email/sync/email_sync.py`
  - `core/email/sync/email_cache.py`
  - `core/email/models/email_tables.sql`

### C3. واجهة موديول الإيميل
- **المطلوب:**
  - شاشة رئيسية: قائمة مجلدات (يسار) + قائمة إيميلات (وسط) + معاينة (يمين)
  - Enterprise Table لعرض الإيميلات مع فرز وفلترة وبحث
  - عرض المرفقات مع إمكانية الحفظ والفتح
  - شريط أدوات: إنشاء، رد، تحويل، بحث، تصنيف
  - تكامل مع AI: زر "حلل هذا الإيميل" / "لخّص المحادثة"
- **الملفات:**
  - `modules/email/window/email_window.py`
  - `modules/email/screens/inbox/`
  - `modules/email/screens/email_viewer/`
  - `modules/email/screens/compose/`
  - `modules/email/toolbar/email_toolbar.py`

### C4. تكامل AI + Email
- **المطلوب:**
  - الـ AI يقرا الإيميلات الجديدة ويستخرج:
    - مهام مطلوبة (Tasks) مع deadlines
    - إيميلات تحتاج رد عاجل
    - ملخص يومي للإيميلات
  - تنبيهات: "عندك 3 إيميلات تحتاج رد النهارده"
  - تقرير أسبوعي: ملخص النشاط + المهام المعلقة
- **الملفات:**
  - `core/ai/agents/email_agent.py` (مشترك مع B2)
  - `modules/email/ai/email_analyzer.py`

---

## خطة التنفيذ المرحلية

### المرحلة 1: الأساسيات (أسبوعين)
```
A1 → Logging (Loguru)
A2 → Exception Handler
A5 → Background Processing (Worker pattern)
```
> هذه هي الأساسيات اللي كل شيء يُبنى عليها

### المرحلة 2: البيانات والأمان (أسبوعين)
```
A4 → Audit Trail (PostgreSQL triggers)
A10 → Pydantic Validation
A9 → Security (RBAC + Argon2)
```

### المرحلة 3: الأتمتة (أسبوع)
```
A3 → Auto-Save + Recovery
A6 → APScheduler
A8 → Backup المتقدم
```

### المرحلة 4: الذكاء الاصطناعي (أسبوعين)
```
B1 → Ollama Service Layer
B5 → AI Chat Panel في الـ UI
B3 → Data Agent (تحليل بيانات)
```

### المرحلة 5: موديول الإيميل (أسبوعين)
```
C1 → Outlook Connector
C2 → Email Sync + Cache
C3 → Email UI
```

### المرحلة 6: التكامل الذكي (أسبوع)
```
B2 + C4 → AI Email Agent
B4 → Smart Alerts
A7 → File Watching
```

---

## المتطلبات للتنفيذ

### ✅ المكتبات - كلها مثبتة!
> **تم التحقق بتاريخ 3 فبراير 2026** من ملف `claude/ALL_Libraries.txt`

```
✅ ollama 0.6.1         - AI
✅ APScheduler 3.11.2   - Scheduling
✅ watchdog 6.0.0       - File Watching
✅ argon2-cffi 25.1.0   - Password Hashing
✅ keyring 25.7.0       - Credential Storage
✅ pywin32 311          - Outlook Integration
✅ pydantic 2.12.5      - Validation
✅ SQLAlchemy 2.0.46    - Database Pool
✅ rich 14.2.0          - Console
✅ humanize 4.15.0      - Formatting
✅ plotly 6.5.2         - Charts
✅ cryptography 46.0.3  - Encryption
✅ PyQt-Fluent-Widgets 1.11.0 - Modern UI
```

**لا يوجد مكتبات تحتاج تثبيت! 🎉**

### معلومات مطلوبة من محمد:
1. **إمكانيات الأجهزة:** RAM + GPU (لاختيار مودل Ollama المناسب)
2. **حساب Outlook:** هل Outlook Classic مثبت ومتصل على الجهازين؟
3. **المودلات المحملة على Ollama:** `ollama list` لمعرفة المتاح
4. **أولويات العمل:** هل نبدأ بالمحور A أم B أم C أم D؟

---

## هيكل المجلدات الجديد
```
core/
├── logging/           ← A1
├── error_handling/    ← A2
├── recovery/          ← A3
├── database/
│   ├── audit/         ← A4
│   ├── connection/    (موجود)
│   └── queries/       (موجود)
├── threading/         ← A5
├── scheduler/         ← A6
├── file_watcher/      ← A7
├── backup/            ← A8
├── security/          ← A9
├── validation/        ← A10
├── ai/                ← B1-B4
│   ├── ollama_client.py
│   ├── ai_service.py
│   ├── prompts/
│   └── agents/
└── email/             ← C1-C2
    ├── outlook_connector.py
    ├── sync/
    └── models/

modules/
├── email/             ← C3-C4
│   ├── window/
│   ├── screens/
│   ├── toolbar/
│   └── ai/
└── mostahaqat/        (موجود)

ui/
└── components/
    └── ai/            ← B5
```

---

## المحور D: تحسينات بناءً على المكتبات المتاحة (Enhancement Track)

> **مصدر:** تحليل ملف `claude/ALL_Libraries.txt` - المكتبات المثبتة فعلياً
> **التاريخ:** 3 فبراير 2026
> **الهدف:** استغلال المكتبات الموجودة لتحسين الأداء وتجربة المستخدم

### 📦 المكتبات المتاحة غير المستغلة

| المكتبة | الإصدار | الفئة | الاستخدام المقترح |
|---------|---------|-------|------------------|
| `rich` | 14.2.0 | Console/Logging | تحسين الـ console output والـ debugging |
| `pydantic` | 2.12.5 | Validation | التحقق من البيانات (مخطط في A10) |
| `SQLAlchemy` | 2.0.46 | Database | Connection Pool + ORM |
| `PyQt-Fluent-Widgets` | 1.11.0 | UI | مكونات Windows 11 style |
| `pyqt-toast-notification` | 1.3.3 | UI | إشعارات Toast حديثة |
| `superqt` | 0.7.7 | UI | Widgets متقدمة (Collapsible, RangeSlider) |
| `plotly` | 6.5.2 | Charts | رسوم بيانية تفاعلية |
| `matplotlib` | 3.10.8 | Charts | رسوم بيانية ثابتة |
| `humanize` | 4.15.0 | Formatting | تنسيق أرقام وتواريخ |
| `cryptography` | 46.0.3 | Security | تشفير البيانات |
| `Faker` | 40.1.0 | Testing | بيانات وهمية للاختبار |
| `nltk` | 3.9.2 | NLP | معالجة نصوص عربية |
| `tqdm` | 4.67.1 | Progress | Progress bars متقدمة |
| `QDarkStyle` | 3.2.3 | Themes | Dark theme جاهز |
| `qt-material` | 2.17 | Themes | Material Design theme |
| `qrcode` | 8.2 | Utility | توليد QR codes |

---

### D1. تحسين نظام Logging (Enhancement لـ A1)

**الحالة الحالية:** `loguru` فقط
**التحسين:** إضافة `rich` للـ console output

**المميزات الجديدة:**
- ✨ Console output ملون ومنسق بشكل احترافي
- ✨ Tables للأخطاء والإحصائيات
- ✨ Syntax highlighting للـ tracebacks
- ✨ Progress bars في الـ console أثناء العمليات الطويلة
- ✨ Panel boxes للرسائل المهمة

**الملفات:**
- `core/logging/rich_console.py` (جديد)
- تحديث `core/logging/app_logger.py`

**مثال:**
```python
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

console = Console()

# عرض جدول
table = Table(title="إحصائيات الموظفين")
table.add_column("القسم", style="cyan")
table.add_column("العدد", style="green")
console.print(table)

# Progress bar
with Progress() as progress:
    task = progress.add_task("جاري المعالجة...", total=100)
    # ...
```

---

### D2. Connection Pool لقاعدة البيانات (تحسين جوهري)

**الحالة الحالية:** Single Connection (اتصال واحد)
**التحسين:** SQLAlchemy Connection Pool

**المشاكل الحالية:**
- ❌ اتصال واحد لكل التطبيق
- ❌ لا يدعم multi-threading بشكل آمن
- ❌ لا يوجد auto-reconnect

**الحل:**
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    "postgresql://user:pass@localhost/integra",
    poolclass=QueuePool,
    pool_size=5,           # اتصالات دائمة
    max_overflow=10,       # اتصالات إضافية عند الحاجة
    pool_timeout=30,       # timeout للانتظار
    pool_recycle=1800,     # إعادة تدوير كل 30 دقيقة
    pool_pre_ping=True     # فحص الاتصال قبل الاستخدام
)
```

**المميزات:**
- ✨ Thread-safe connections
- ✨ Auto-reconnect عند انقطاع الاتصال
- ✨ أداء أفضل مع المهام المتوازية
- ✨ Health checks تلقائية

**الملفات:**
- `core/database/connection/pool.py` (جديد)
- تحديث `core/database/connection/__init__.py`

---

### D3. Toast Notifications (تحسين تجربة المستخدم)

**الحالة الحالية:** `QMessageBox` تقليدي
**التحسين:** `pyqt-toast-notification`

**المشاكل الحالية:**
- ❌ MessageBox يوقف العمل (modal)
- ❌ مظهر قديم
- ❌ لا يختفي تلقائياً

**الحل:**
```python
from pyqt_toast import Toast, ToastPreset

# إشعار نجاح
Toast.show(
    parent=self,
    title="تم الحفظ",
    text="تم حفظ بيانات الموظف بنجاح",
    preset=ToastPreset.SUCCESS,
    duration=3000  # 3 ثواني
)

# إشعار خطأ
Toast.show(
    parent=self,
    title="خطأ",
    text="فشل الاتصال بقاعدة البيانات",
    preset=ToastPreset.ERROR
)
```

**المميزات:**
- ✨ لا يوقف العمل (non-blocking)
- ✨ يختفي تلقائياً
- ✨ مظهر حديث وأنيق
- ✨ أنواع متعددة (Success, Error, Warning, Info)

**الملفات:**
- `ui/components/notifications/toast_manager.py` (جديد)
- تحديث `ui/dialogs/__init__.py`

---

### D4. تنسيق البيانات (Humanize)

**الحالة الحالية:** عرض أرقام وتواريخ خام
**التحسين:** `humanize` للتنسيق

**أمثلة:**
```python
import humanize
from datetime import datetime, timedelta

# الأرقام
humanize.intcomma(5000)           # "5,000"
humanize.intword(1000000)         # "1 million"

# التواريخ (بالعربي)
humanize.activate("ar")
humanize.naturaltime(datetime.now() - timedelta(minutes=5))  # "منذ 5 دقائق"
humanize.naturalday(datetime.now())                           # "اليوم"

# أحجام الملفات
humanize.naturalsize(1024000)     # "1.0 MB"
```

**الاستخدام في INTEGRA:**
- ✨ "آخر تحديث: منذ 5 دقائق" بدل timestamp
- ✨ "الراتب: 5,000 ر.س" بدل 5000
- ✨ "حجم النسخة: 2.5 MB" بدل bytes

**الملفات:**
- `core/utils/formatters.py` (جديد)

---

### D5. رسوم بيانية تفاعلية (Charts)

**المتاح:** `plotly` 6.5.2 + `matplotlib` 3.10.8
**الاستخدام:** Dashboard وإحصائيات

**Plotly (تفاعلي - للـ Dashboard):**
```python
import plotly.express as px
from PyQt5.QtWebEngineWidgets import QWebEngineView

# رسم بياني دائري
fig = px.pie(
    values=[30, 25, 20, 25],
    names=["الإدارة", "المبيعات", "الإنتاج", "الدعم"],
    title="توزيع الموظفين حسب القسم"
)

# عرض في PyQt5
web_view = QWebEngineView()
web_view.setHtml(fig.to_html())
```

**الاستخدام في INTEGRA:**
- ✨ Dashboard إحصائيات الموظفين
- ✨ تحليل الرواتب والمستحقات
- ✨ تقارير بصرية تفاعلية

**الملفات:**
- `ui/components/charts/plotly_widget.py` (جديد)
- `ui/components/charts/stats_dashboard.py` (جديد)

---

### D6. مكونات UI متقدمة (Fluent + SuperQt)

**المتاح:**
- `PyQt-Fluent-Widgets` 1.11.0 - Windows 11 style
- `superqt` 0.7.7 - Widgets متقدمة

**مكونات Fluent:**
```python
from qfluentwidgets import (
    PushButton, PrimaryPushButton,
    LineEdit, SearchLineEdit,
    ComboBox, CheckBox,
    ProgressBar, InfoBar,
    FluentIcon, NavigationInterface
)

# زر أساسي
btn = PrimaryPushButton("حفظ", self)
btn.setIcon(FluentIcon.SAVE)

# شريط بحث
search = SearchLineEdit(self)
search.setPlaceholderText("ابحث عن موظف...")

# إشعار
InfoBar.success(
    title="تم",
    content="تم حفظ البيانات بنجاح",
    parent=self
)
```

**مكونات SuperQt:**
```python
from superqt import QCollapsible, QRangeSlider

# قسم قابل للطي
collapsible = QCollapsible("خيارات متقدمة")
collapsible.addWidget(my_options_widget)

# Slider بقيمتين (min-max)
range_slider = QRangeSlider()
range_slider.setRange(0, 10000)
range_slider.setValue((2000, 8000))  # نطاق الراتب
```

**الملفات:**
- `ui/components/fluent/` (مجلد جديد)
- تحديث المكونات الحالية تدريجياً

---

### D7. تشفير البيانات الحساسة

**المتاح:** `cryptography` 46.0.3
**الاستخدام:** تشفير بيانات الاتصال والبيانات الحساسة

```python
from cryptography.fernet import Fernet

# توليد مفتاح (مرة واحدة)
key = Fernet.generate_key()

# تشفير
cipher = Fernet(key)
encrypted = cipher.encrypt(b"password123")

# فك التشفير
decrypted = cipher.decrypt(encrypted)
```

**الاستخدام في INTEGRA:**
- ✨ تشفير كلمات مرور قاعدة البيانات
- ✨ تشفير ملفات الإعدادات الحساسة
- ✨ تشفير بيانات الموظفين الحساسة (IBAN)

**الملفات:**
- `core/security/encryption.py` (جديد)
- يتكامل مع A9 Security

---

### D8. بيانات اختبار (Faker)

**المتاح:** `Faker` 40.1.0
**الاستخدام:** توليد بيانات وهمية للتطوير والاختبار

```python
from faker import Faker

fake = Faker('ar_SA')  # بيانات عربية سعودية

# موظف وهمي
employee = {
    "name_ar": fake.name(),
    "email": fake.email(),
    "phone": fake.phone_number(),
    "address": fake.address(),
    "hire_date": fake.date_between(start_date='-5y'),
    "salary": fake.random_int(min=3000, max=15000),
    "iban": fake.iban()
}
```

**الاستخدام في INTEGRA:**
- ✨ توليد بيانات للـ demo
- ✨ اختبار الأداء مع بيانات كثيرة
- ✨ اختبار الواجهة

**الملفات:**
- `tools/data_generator.py` (جديد)

---

### D9. QR Codes

**المتاح:** `qrcode` 8.2
**الاستخدام:** بطاقات الموظفين والتقارير

```python
import qrcode
from io import BytesIO

# توليد QR code
qr = qrcode.QRCode(version=1, box_size=10, border=5)
qr.add_data(f"EMP:{employee_id}")
qr.make(fit=True)

img = qr.make_image(fill_color="black", back_color="white")

# تحويل لـ QPixmap
buffer = BytesIO()
img.save(buffer, format='PNG')
pixmap = QPixmap()
pixmap.loadFromData(buffer.getvalue())
```

**الاستخدام في INTEGRA:**
- ✨ بطاقة هوية الموظف بـ QR
- ✨ روابط سريعة في التقارير
- ✨ تسجيل حضور بالـ QR

**الملفات:**
- `core/utils/qr_generator.py` (جديد)

---

## خطة تنفيذ التحسينات (المحور D)

### المرحلة D1: تحسينات سريعة (أسبوع واحد)
```
D3 → Toast Notifications (سهل، أثر كبير)
D4 → Humanize Formatting (سهل، يحسن UX)
D8 → Faker للاختبار (مفيد للتطوير)
```

### المرحلة D2: تحسينات الأداء (أسبوع واحد)
```
D2 → Connection Pool (مهم جداً للاستقرار)
D1 → Rich Logging (يساعد في الـ debugging)
```

### المرحلة D3: تحسينات UI (أسبوعين)
```
D5 → Plotly Charts (Dashboard)
D6 → Fluent Widgets (تدريجي)
D9 → QR Codes
```

### المرحلة D4: الأمان (أسبوع واحد)
```
D7 → Encryption (يتكامل مع A9)
```

---

## ملخص المكتبات

### ✅ مثبتة ومستخدمة:
- `PyQt5` - الواجهة الرسومية
- `psycopg2` - قاعدة البيانات
- `loguru` - التسجيل

### ✅ مثبتة وجاهزة للاستخدام (المحور D):
- `rich`, `humanize`, `tqdm` - Console & Formatting
- `SQLAlchemy` - Database Pool
- `pydantic` - Validation (A10)
- `PyQt-Fluent-Widgets`, `superqt`, `pyqt-toast-notification` - UI
- `plotly`, `matplotlib` - Charts
- `cryptography`, `argon2-cffi`, `keyring` - Security (A9)
- `APScheduler` - Scheduling (A6)
- `watchdog` - File Watching (A7)
- `ollama` - AI (B1-B4)
- `pywin32` - Outlook (C1-C4)
- `Faker` - Testing
- `qrcode` - QR Generation

### ❌ لا تحتاج تثبيت إضافي:
**كل المكتبات المطلوبة للخطة مثبتة بالفعل!** ✅
