# INTEGRA v2.1 - Master Reference Document
**آخر تحديث:** 2 فبراير 2026
**المرحلة:** Phase 2 - Enterprise-Grade Development

---

## 1. هوية المشروع

| البند | التفاصيل |
|---|---|
| الاسم | INTEGRA (Integrated Management System) |
| النوع | Desktop ERP Application |
| الإصدار | v2.1.0 |
| الحالة | Architecture Complete ✅ → Next: Enterprise-Grade Tables |
| المستودع | https://github.com/Insightify2029/integra.git |
| إجمالي الملفات | 206+ Python files |

---

## 2. المستخدم (محمد)

- محاسب تكاليف - خبرة 20 سنة - شركة تكرير زيت نخيل بالسعودية
- مسؤول: التكاليف + HR + الرواتب + مراجعة رواتب Oracle NetSuite الشهرية
- صفر خبرة برمجة - يحتاج شرح خطوة بخطوة
- اللهجة: مصرية | التفكير: استراتيجي تحليلي منطقي
- جهازين: العمل (Prosaba) + البيت (DESKTOP-HC577P1)
- المسار الموحد: D:\Projects\Integra

---

## 3. التقنيات (Technical Stack)

### الأساسي:
- **Python 3.11.9** (system-wide, بدون venv)
- **PyQt5** (Desktop UI Framework)
- **PostgreSQL 16.11** (localhost:5432, user: postgres, DB: integra)
- **psycopg2-binary** (DB connector)
- **Git** (user: m.mahmoud@teknosaba.com)

### المكتبات المثبتة:
- Core: psycopg2-binary, SQLAlchemy, alembic
- Data: pandas, numpy
- File Readers: openpyxl, xlrd, PyPDF2, pdfplumber, python-docx, Pillow, tika
- Utilities: python-dotenv, loguru, rich, pydantic
- UI: PyQt5

### حالة الأجهزة:
- **Prosaba (العمل):** ✅ كل المكتبات + PostgreSQL + Git | ❌ .env مفقود
- **DESKTOP-HC577P1 (البيت):** ✅ Python/PostgreSQL/Git | ❌ ناقص alembic + tika + .env

---

## 4. البنية المعمارية (Architecture)

### الفلسفة:
- **SRP** (Single Responsibility Principle): ملف واحد = وظيفة/كلاس واحد
- **شاشات نظيفة:** الشاشات الرئيسية بدون بيانات - البيانات عبر القوائم
- **قوائم متقدمة:** Deep menu hierarchy مع keyboard shortcuts
- **جداول Enterprise-Grade:** فرز + فلترة + بحث + تصدير + اختيار أعمدة

### هيكل المجلدات:
```
D:\Projects\Integra\
├── main.py                          # Entry point (717 bytes)
├── core/
│   ├── config/
│   │   ├── app/                     # APP_NAME, APP_VERSION
│   │   ├── database/                # DB_HOST, DB_PORT, DB_NAME, DB_USER
│   │   ├── window/                  # MIN_WIDTH, MIN_HEIGHT
│   │   └── modules/                 # Module definitions
│   ├── database/
│   │   ├── connection/              # Connector, checker, config
│   │   └── queries/                 # SELECT, INSERT, UPDATE, DELETE, SCALAR
│   ├── themes/
│   │   ├── dark/                    # Dark theme (colors, fonts, components)
│   │   ├── light/                   # Light theme
│   │   ├── theme_manager.py
│   │   └── current_theme.py
│   └── sync/                        # Sync system v2
│       ├── sync_config.py
│       ├── sync_runner.py (13KB)
│       └── sync_worker.py
├── ui/
│   ├── windows/
│   │   ├── base/                    # BaseWindow class
│   │   └── launcher/                # Main launcher window
│   ├── components/
│   │   ├── cards/
│   │   │   ├── module_card/         # Module cards (adaptive font)
│   │   │   └── stat_card/           # Statistics cards
│   │   ├── buttons/
│   │   ├── inputs/
│   │   ├── labels/
│   │   └── tables/
│   │       └── enterprise/          # Enterprise table components
│   │           ├── enterprise_table.py (18KB)
│   │           ├── export_manager.py (16KB)
│   │           ├── filter_panel.py (10KB)
│   │           └── column_chooser.py (7KB)
│   └── dialogs/
│       ├── message/                 # Info, Warning, Error dialogs
│       ├── settings/                # Settings dialog
│       ├── sync_settings/           # Sync settings (18KB)
│       └── themes/                  # Theme selection dialog
├── modules/
│   └── mostahaqat/                  # مستحقات العاملين
│       ├── window/                  # mostahaqat_window.py (27KB)
│       ├── toolbar/                 # mostahaqat_toolbar.py
│       ├── employees/               # Employee list, queries
│       ├── screens/
│       │   ├── employees_list/
│       │   ├── employee_profile/
│       │   └── edit_employee/       # Edit screen (20KB)
│       └── stats/                   # stats_cards.py
├── Tools/
│   ├── INTEGRA_HEALTH_CHECK.py (35KB)
│   ├── install_edit_screen.py (32KB)
│   ├── install_sync_system.py (55KB)
│   └── health_check reports (.txt)
└── Updates/
    └── integra_v2.1/
        └── database_backup.sql
```

---

## 5. قاعدة البيانات

### الاتصال:
```
Host: localhost | Port: 5432 | DB: integra | User: postgres
Password: في ملف .env (غير موجود في Git)
```

### الجداول الموجودة:
| الجدول | عدد السجلات |
|---|---|
| employees | 180 |
| departments | 20 |
| job_titles | 88 |
| nationalities | 12 |
| banks | موجود |
| companies | موجود |
| employee_statuses | موجود |

---

## 6. الميزات المكتملة

### 6.1 الواجهة الرئيسية (Launcher):
- شاشة INTEGRA نظيفة مع logo
- 5 بطاقات modules بخطوط تكيّفية (مستحقات 18pt | تكاليف 22pt | لوجستيات 22pt | عهد 30pt | تأمين 26pt)
- قائمة hamburger + شريط حالة + دعم Dark/Light themes
- بدون حدود، أركان مدورة (20px)، كل بطاقة تفتح نافذة مستقلة

### 6.2 موديول المستحقات (Mostahaqat):
- شاشة رئيسية نظيفة + شريط قوائم شامل:
  - 👥 الموظفين (عرض، إضافة، تعديل، بحث، استيراد/تصدير)
  - 💰 المستحقات (رواتب، بدلات، استقطاعات)
  - 🏖️ الإجازات (أرصدة، طلبات، تسوية)
  - ⏰ الإضافي (تسجيل، حساب، تقارير)
  - 🚪 نهاية الخدمة (حاسبة، مخالصة، سجل)
  - 📊 التقارير (موظفين، مالية، مخصصة)
  - ⚙️ الإعدادات (بيانات أساسية، إعدادات الموديول)
- شريط أدوات سريع
- شاشة قائمة الموظفين + شاشة ملف الموظف (مع أزرار إجراءات) + شاشة تعديل الموظف

### 6.3 مكوّن Enterprise Table:
- Double-click → شاشة التفاصيل
- فرز متقدم + فلترة ذكية + بحث مباشر
- تصدير (Excel/PDF/CSV) + اختيار أعمدة + دعم RTL

### 6.4 نظام المزامنة (Sync System v2):
- تلقائي عند الفتح (git pull + DB restore) وعند الإغلاق (DB backup + git push)
- مزامنة دورية + أزرار يدوية (جلب/رفع/كاملة/إعدادات)
- نافذة إعدادات + نسخ/استعادة PostgreSQL تلقائي + تكامل Git

### 6.5 أدوات البنية التحتية:
- INTEGRA_HEALTH_CHECK.py (35KB): فحص شامل مع تقارير لكل جهاز
- install_edit_screen.py (32KB) + install_sync_system.py (55KB)
- INTEGRA.bat: Launcher تلقائي

---

## 7. المرحلة القادمة (Phase 2)

### الأولويات:
1. Enterprise-Grade Tables لكل الشاشات
2. أزرار Employee Profile (تعطيل، تسوية إجازات، نهاية خدمة، إضافي)
3. باقي الموديولات: التكاليف، اللوجستيات، العهد، التأمين
4. نظام التقارير المتقدم
5. Dashboard مع تحليلات

### بنود معلقة:
- إنشاء ملف .env على الجهازين
- تثبيت alembic + tika على جهاز البيت
- رفع 2 تغييرات غير محفوظة على جهاز العمل

---

## 8. نظام المزامنة

- **الاستراتيجية:** Local PostgreSQL + Git + Automated Backup/Restore
- **الدورة:** فتح → pull+restore → شغل → إغلاق → backup+commit+push → الجهاز التاني
- **خارج Git:** .env | venv/ | __pycache__/ | *.pyc | logs/ | database_backup.sql

---

## 9. أوامر أساسية

```bash
cd D:\Projects\Integra
git status && git log --oneline -5
git pull && git add --all && git commit -m "message" && git push
python main.py
python Tools\INTEGRA_HEALTH_CHECK.py
```

---

## 10. قرارات تصميمية

| القرار | الاختيار | السبب |
|---|---|---|
| Desktop vs Web | Desktop (PyQt5) | أداء + offline + واجهة احترافية |
| Database | PostgreSQL | أقوى + مرن + مجاني |
| Sync | Local DB + Git | بدون اعتماد على إنترنت |
| Virtual Environment | لا يُستخدم | مكتبات system-wide (تفضيل المستخدم) |
| Architecture | SRP | ملف واحد = وظيفة واحدة |

---

## 11. مبادئ العمل

- خطوة بخطوة (مهمة واحدة في كل مرة)
- تأكيد بصري قبل المتابعة
- تواصل بالعامية المصرية
- جودة Enterprise-grade
- تخطيط شامل قبل الكود
- اختبار على الجهازين + مزامنة متكررة

---

## 12. معلومات ERP مرجعية

### أنماط معمارية:
- Three-tier layered architecture + module-based extensibility
- Manifest-based plugin system
- Hierarchical configuration (system → company → user)
- Optimistic locking مع version columns
- QThreadPool للمعالجة الخلفية
- PostgreSQL triggers لـ audit trails

### مكتبات مستقبلية:
- ORM: SQLAlchemy 2.0 | Scheduling: APScheduler | File Watch: watchdog
- Excel: xlwings | Validation: Pydantic | Reports: ReportLab
- Email: SendGrid | Backup: pg_dump -Fc + gzip
- Security: Argon2 + OS keyring + RBAC
