# INTEGRA v2.1 - خطة تطوير البنية التحتية المتقدمة
**التاريخ:** 2 فبراير 2026
**الحالة:** مسودة للمراجعة والاعتماد

---

## نظرة عامة

هذه الخطة تغطي **3 محاور رئيسية** لتطوير البنية التحتية:

| المحور | الوصف | الأولوية |
|---|---|---|
| **A** | البنية التحتية الأساسية (من ERP Research) | أساسي - يُبنى عليه كل شيء |
| **B** | الذكاء الاصطناعي المدمج (Ollama AI) | استراتيجي - يرفع كفاءة العمل |
| **C** | موديول الإيميل (Outlook Classic Sync) | تشغيلي - يربط سير العمل اليومي |

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

### مكتبات جديدة تحتاج تثبيت:
```bash
pip install ollama apscheduler watchdog argon2-cffi keyring pywin32
```

### معلومات مطلوبة من محمد:
1. **إمكانيات الأجهزة:** RAM + GPU (لاختيار مودل Ollama المناسب)
2. **حساب Outlook:** هل Outlook Classic مثبت ومتصل على الجهازين؟
3. **المودلات المحملة على Ollama:** `ollama list` لمعرفة المتاح
4. **أولويات العمل:** هل نبدأ بالبنية التحتية أم الـ AI أم الإيميل؟

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
