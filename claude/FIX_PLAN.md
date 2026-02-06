# INTEGRA - خطة إصلاح شاملة للكود
**تاريخ الإنشاء:** 6 فبراير 2026
**المرجع:** `claude/CODE_REVIEW_AUDIT.md` (95 مشكلة)
**الحالة:** جارٍ التنفيذ

---

## منهجية المتابعة عبر الجلسات

### كيف تبدأ كل جلسة جديدة:
```
اقرأ الملف claude/FIX_PLAN.md وأكمل الجلسة التالية غير المكتملة في خطة الإصلاح
```

### قواعد العمل:
1. **بداية الجلسة:** اقرأ هذا الملف → حدد الجلسة المطلوبة → ابدأ التنفيذ
2. **أثناء الجلسة:** حدّث حالة كل مشكلة فور إصلاحها (🔴 → ✅)
3. **نهاية الجلسة:** حدّث هذا الملف + SESSION_LOG.md → commit + push + PR
4. **لا تنتقل للجلسة التالية** قبل إكمال الحالية بالكامل

### رموز الحالة:
| الرمز | المعنى |
|-------|--------|
| ✅ | لم يبدأ |
| 🟡 | قيد التنفيذ |
| ✅ | مكتمل |
| ⏭️ | مؤجل (مع سبب) |

---

## الجلسة 1: الأخطاء الحرجة - انهيارات التطبيق
**المدة المتوقعة:** جلسة واحدة
**الهدف:** منع كل حالات الانهيار (Crash) الفورية
**الحالة:** ✅ مكتمل (2026-02-06)

| # | المشكلة | الخطورة | الملفات | الحالة |
|---|---------|---------|---------|--------|
| CRIT-01 | تسرب اتصالات قاعدة البيانات | حرج | `core/database/queries/*.py` (5 ملفات) | ✅ |
| CRIT-03 | انهيار المجدول عند الساعة 23:00 | حرج | `core/bi/export_scheduler.py` | ✅ |
| CRIT-04 | انهيار EventBus عند أحداث متزامنة | حرج | `core/ai/orchestration/event_bus.py` | ✅ |
| CRIT-08 | انهيار `due_date_formatted` آخر الشهر | حرج | `modules/tasks/models/task_models.py` | ✅ |
| CRIT-09 | انهيار التنقل في التقويم | حرج | `modules/calendar/widgets/calendar_header.py` | ✅ |
| CRIT-10 | `QPixmap.scaled()` float بدل int | حرج | `modules/tasks/screens/task_board/kanban_board.py` | ✅ |

**الإصلاحات المنفذة:**
- CRIT-01: إضافة `return_connection(conn)` في `finally` block لجميع ملفات الاستعلام (5 ملفات) + إنشاء دالة `return_connection()` في `connector.py`
- CRIT-03: استخدام `timedelta(hours=1)` بدل `hour + 1`
- CRIT-04: إضافة `__lt__` لكلاس `Event` للمقارنة عبر `timestamp`
- CRIT-08: استخدام `timedelta(days=1)` بدل `replace(day=today.day + 1)`
- CRIT-09: استخدام `timedelta(days=7)` و `timedelta(days=1)` بدل `replace(day=...)` في جميع دوال التنقل + إصلاح عرض الأسبوع عبر حدود الشهر
- CRIT-10: تحويل لـ `int()` قبل `scaled()` + إنشاء `QPoint` يدوياً بدل `event.pos() * 0.8`

---

## الجلسة 2: الأخطاء الحرجة - أمان + Import + واجهة
**المدة المتوقعة:** جلسة واحدة
**الهدف:** سد ثغرات SQL Injection + إصلاح ImportError + إصلاح واجهة معطلة
**الحالة:** ✅ مكتمل (2026-02-06)

| # | المشكلة | الخطورة | الملفات | الحالة |
|---|---------|---------|---------|--------|
| CRIT-11 | حقن SQL في مصمم النماذج | حرج | `modules/designer/form_builder/data_binding.py` | ✅ |
| HIGH-01 | حقن SQL في BI Exporter | عالي | `core/bi/data_exporter.py` | ✅ |
| HIGH-02 | حقن SQL في BI Views Manager | عالي | `core/bi/views_manager.py` | ✅ |
| CRIT-02 | `execute_query` ImportError | حرج | `core/bi/views_manager.py` | ✅ |
| CRIT-05 | `os.startfile()` Linux/macOS | حرج | `ui/components/tables/enterprise/export_manager.py` | ✅ |
| CRIT-06 | FilterPanel لا تُضاف للواجهة | حرج | `ui/components/tables/enterprise/enterprise_table_widget.py` | ✅ |
| CRIT-07 | `QThread.terminate()` خطير | حرج | `ui/components/email/email_panel.py` | ✅ |

**الإصلاحات المنفذة:**
- CRIT-11: استخدام `psycopg2.sql.Identifier()` و `sql.SQL()` في `load_data()` و `save_data()` + التحقق من `table_name` ضد `_schemas`
- HIGH-01: استخدام `psql.SQL("SELECT * FROM {}.{}").format(psql.Identifier("bi_views"), psql.Identifier(view_name))` في `export_to_csv()` و `export_to_excel()`
- HIGH-02: نفس المنهج لـ `get_view_row_count()`, `drop_view()`, `get_view_data()` باستخدام `psycopg2.sql.Identifier`
- CRIT-02: إنشاء دالة `execute_query()` جديدة في `core/database/queries/execute_query.py` وتسجيلها في `__init__.py`
- CRIT-05: استخدام `sys.platform` للتمييز: `os.startfile` (Windows) / `subprocess.Popen(['open', ...])` (macOS) / `subprocess.Popen(['xdg-open', ...])` (Linux)
- CRIT-06: استبدال FilterPanel القديمة بالجديدة في الـ layout عبر `replaceWidget()` + `deleteLater()` للقديمة
- CRIT-07: استبدال `terminate()` بـ `requestInterruption()` + `quit()` + `wait(3000)` في كلا العاملين

---

## الجلسة 3: المشاكل العالية - وظائف معطلة
**المدة المتوقعة:** جلسة واحدة
**الهدف:** إصلاح الوظائف التي لا تعمل أصلاً
**الحالة:** ✅ مكتمل (2026-02-06)

| # | المشكلة | الخطورة | الملفات | الحالة |
|---|---------|---------|---------|--------|
| HIGH-08 | زر "حفظ" لا يحفظ | عالي | `ui/dialogs/settings/settings_dialog.py` | ✅ |
| HIGH-09 | "اختبار الاتصال" لا يختبر المدخلات | عالي | `ui/dialogs/settings/settings_dialog.py` | ✅ |
| HIGH-10 | فلاتر "اليوم" و"المتأخرة" لا تعمل | عالي | `modules/tasks/screens/task_list/task_list_screen.py` | ✅ |
| HIGH-11 | `get_by_employee()` تستثني IN_PROGRESS | عالي | `modules/tasks/repository/task_repository.py` | ✅ |
| HIGH-14 | PDFAIStudio غير مستوردة | عالي | `modules/file_manager/window/file_manager_window.py` | ✅ |
| HIGH-03 | ActionType ValueError غير محمي | عالي | `core/ai/agents/action_agent.py` | ✅ |
| HIGH-04 | Singleton يتجاهل host | عالي | `core/ai/ollama_client.py` | ✅ |

**الإصلاحات المنفذة:**
- HIGH-08: ربط `save_btn` بدالة `_save_settings()` تحفظ الإعدادات في ملف `.env` + تحميل القيم الحالية من `core.config`
- HIGH-09: استخدام `psycopg2.connect()` مباشرةً مع القيم المدخلة من المستخدم + `connect_timeout=5` بدل فحص الاتصال الحالي
- HIGH-10: استخدام `get_tasks_due_today()` و `get_overdue_tasks()` عبر مفتاح `_quick` في الفلاتر بدل `pass`
- HIGH-11: تغيير المنطق لفلترة `COMPLETED` و `CANCELLED` في Python بدل تقييد الاستعلام بـ `PENDING` فقط
- HIGH-14: إضافة `from core.file_manager.pdf import PDFAIStudio` في `_pdf_merge()` كاستيراد محلي
- HIGH-03: لف `ActionType(action_type_str)` بـ `try/except ValueError` مع إرجاع رسالة خطأ واضحة
- HIGH-04: مقارنة `new_host != self._host` في `__init__` وإعادة التهيئة عند التغيير + تحديث `get_ollama_client()` للتعامل مع host جديد

---

## الجلسة 4: المشاكل العالية - Threading + تسرب ذاكرة
**المدة المتوقعة:** جلسة واحدة
**الهدف:** إصلاح سباقات الخيوط وتسريبات الذاكرة
**الحالة:** ✅ مكتمل (2026-02-06)

| # | المشكلة | الخطورة | الملفات | الحالة |
|---|---------|---------|---------|--------|
| HIGH-05 | `_action_history` بدون قفل | عالي | `core/ai/agents/action_agent.py` | ✅ |
| HIGH-06 | ConversationContext غير آمنة | عالي | `core/ai/ai_service.py` | ✅ |
| HIGH-07 | `_running` flag بدون قفل | عالي | `core/bi/export_scheduler.py` | ✅ |
| HIGH-12 | تسرب ذاكرة النوافذ المفتوحة | عالي | `ui/windows/launcher/launcher_window.py` | ✅ |
| HIGH-13 | حذف widget لا ينظف البيانات | عالي | `modules/designer/form_builder/form_canvas.py` | ✅ |
| MED-06 | عداد التنبيهات غير آمن | متوسط | `core/ai/agents/alert_agent.py` | ✅ |
| MED-07 | `get_insights()` بدون قفل | متوسط | `core/ai/agents/learning_agent.py` | ✅ |
| MED-22 | ExportWorker بدون إدارة دورة حياة | متوسط | `ui/dialogs/bi_settings/bi_settings_dialog.py` | ✅ |

**الإصلاحات المنفذة:**
- HIGH-05: إضافة `with self._lock:` في `_add_to_history()`, `get_action_history()`, `get_action()` (كان القفل موجوداً لكن غير مُستخدم في هذه الدوال)
- HIGH-06: إضافة `threading.Lock` كـ field في `ConversationContext` مع حماية `add_message()`, `get_context()`, `clear()`
- HIGH-07: إضافة `threading.Lock()` في `ExportScheduler` مع حماية `_running` في `start()`, `stop()`, `_schedule_next_export()`, `_execute_export()`, `is_running`, `get_status()`
- HIGH-12: تنظيف النوافذ المغلقة في `_open_module()` + استدعاء `deleteLater()` و `clear()` في `closeEvent()`
- HIGH-13: إضافة signal `delete_requested` في `DesignWidgetItem` + ربطه بـ `FormCanvas.remove_widget()` بدل `deleteLater()` المباشر
- MED-06: إضافة `threading.Lock()` في `AlertAgent` مع حماية `_generate_id()`, `_add_alert()`, `get_alerts()`, `get_summary()`, `mark_as_read()`, `dismiss_alert()`, `clear_alerts()`
- MED-07: حماية `get_insights()` بأخذ snapshot من `_feedback_history` و `_patterns` داخل `self._lock`
- MED-22: منع بدء تصدير جديد أثناء تنفيذ آخر + إضافة `closeEvent()` لتنظيف Worker عند إغلاق Dialog

---

## الجلسة 5: المشاكل المتوسطة - أمان + واجهة
**المدة المتوقعة:** جلسة واحدة
**الهدف:** إصلاح الثغرات الأمنية المتبقية + مشاكل الواجهة
**الحالة:** ✅ مكتمل (2026-02-06)

| # | المشكلة | الخطورة | الملفات | الحالة |
|---|---------|---------|---------|--------|
| MED-24 | DB_PASSWORD في `__all__` | متوسط | `core/config/__init__.py` | ✅ |
| MED-25 | مفتاح التشفير في ملف نصي | متوسط | `core/security/encryption.py` | ✅ |
| MED-26 | مقارنة كلمات مرور بـ `==` | متوسط | `core/security/encryption.py` | ✅ |
| MED-04 | `where_clause` SQL خام | متوسط | `core/database/queries/scalar_query.py` | ✅ |
| MED-12 | حقن HTML في البريد | متوسط | `ui/components/email/email_viewer.py` | ✅ |
| MED-08 | ألوان الجدول للظلام فقط | متوسط | `ui/components/tables/enterprise/enterprise_table.py` | ✅ |
| MED-09 | `accent_color` يُتجاهل | متوسط | `ui/components/cards/module_card/card_style.py` | ✅ |
| MED-17 | CSS يتراكم عند فشل التحقق | متوسط | `modules/tasks/widgets/task_form.py` | ✅ |

**الإصلاحات المنفذة:**
- MED-24: حذف `DB_PASSWORD` من `__all__` في `core/config/__init__.py`
- MED-25: ترحيل المفتاح من الملف إلى keyring عند التوفر + إضافة تحذير logging عند التخزين في ملف + إضافة `import hmac, logging`
- MED-26: استبدال `==` بـ `hmac.compare_digest()` في `verify_password()`
- MED-04: إضافة regex validation لرفض `where_clause` يحتوي أنماط SQL خطيرة (`;`, `--`, `DROP`, `ALTER`, إلخ)
- MED-12: إضافة `html.escape()` للنص العادي قبل تحويله لـ HTML في `set_email()`
- MED-08: جعل `EnterpriseTableDelegate.paint()` يقرأ السمة الحالية ويستخدم ألوان مناسبة (فاتح: `#f1f5f9` للـ hover)
- MED-09: استخدام `accent_color` في f-string CSS لإضافة حدود ملونة عند الـ hover
- MED-17: إعادة تعيين CSS نظيف عبر `_style_input()` قبل التحقق، ثم تعيين stylesheet خطأ كامل بدل الإلحاق

---

## الجلسة 6: المشاكل المتوسطة - منطق + أداء + تقويم
**المدة المتوقعة:** جلسة واحدة
**الهدف:** إصلاح أخطاء المنطق والأداء والتقويم
**الحالة:** ✅ مكتمل (2026-02-06)

| # | المشكلة | الخطورة | الملفات | الحالة |
|---|---------|---------|---------|--------|
| MED-14 | أسماء الأيام خاطئة | متوسط | `modules/calendar/models/calendar_models.py` | ✅ |
| MED-15 | DayCell layouts متكررة | متوسط | `modules/calendar/widgets/day_cell.py` | ✅ |
| MED-16 | شهر خاطئ في عرض الأسبوع | متوسط | `modules/calendar/widgets/calendar_header.py` | ✅ |
| MED-19 | `_always_on_top` متناقض | متوسط | `modules/copilot/components/chat_window.py` | ✅ |
| MED-20 | `except: pass` يبتلع الأخطاء | متوسط | `modules/copilot/knowledge/sources.py` | ✅ |
| MED-23 | خطأ تدفق في StreamWorker | متوسط | `ui/components/ai/chat_panel.py` | ✅ |
| MED-01 | منطق اقتباس CSV خاطئ | متوسط | `core/bi/data_exporter.py` | ✅ |
| MED-02 | دمج إعدادات BI سطحي | متوسط | `core/bi/connection_config.py` | ✅ |

**الإصلاحات المنفذة:**
- MED-14: تصحيح ترتيب مصفوفة الأيام لتتوافق مع `weekday()` (الإثنين=0, ..., الأحد=6)
- MED-15: مسح layout القديم وحذف children قبل إنشاء layout جديد في `set_events()` عبر `takeAt()` + `deleteLater()` + نقل layout لـ widget مؤقت
- MED-16: حساب الشهر من `week_start` وليس `current_date` + معالجة حدود السنة في عرض الأسبوع
- MED-19: مزامنة `_always_on_top = True` مع `WindowStaysOnTopHint` + تحديث أيقونة الـ pin button لتتطابق
- MED-20: استبدال `except: pass` بـ `app_logger.error()` في 4 مواقع بـ `sources.py` (DocumentSource, DatabaseSource×2, ModuleSource)
- MED-23: نقل `finished.emit()` من `finally` لداخل `try` + إضافة إعادة تمكين الإدخال وتنظيف worker في `_on_stream_error()`
- MED-01: فحص `needs_quoting` قبل `replace('"', '""')` لتجنب double-wrapping (RFC 4180)
- MED-02: إضافة `_deep_merge()` واستخدامها بدل `.update()` السطحي للحفاظ على البنية المتداخلة

---

## الجلسة 7: المشاكل المتوسطة + المنخفضة المتبقية
**المدة المتوقعة:** جلسة واحدة
**الهدف:** إصلاح بقية المشاكل المتوسطة والمنخفضة المهمة
**الحالة:** ✅ مكتمل (2026-02-06)

| # | المشكلة | الخطورة | الملفات | الحالة |
|---|---------|---------|---------|--------|
| MED-03 | Icons class يُستبدل بمثيل | متوسط | `core/utils/icons.py` | ✅ |
| MED-05 | مراقب الملفات ليس Singleton | متوسط | `core/file_watcher/watcher.py` | ✅ |
| MED-10 | قسمة على صفر في التصدير | متوسط | `ui/components/tables/enterprise/export_manager.py` | ✅ |
| MED-11 | ترتيب القاموس لا يتطابق | متوسط | `ui/components/tables/enterprise/export_manager.py` | ✅ |
| MED-13 | تجميد الواجهة عند الاستعادة | متوسط | `ui/dialogs/sync_settings/sync_settings_dialog.py` | ✅ |
| MED-21 | تحميل كل المهام للفلترة | متوسط | `modules/tasks/integration/*.py` | ✅ |
| MED-27 | `fetchone()[0]` بدون None | متوسط | `core/database/queries/insert_query.py` | ✅ |
| MED-28 | لا توجد حدود معاملات في BI | متوسط | `core/bi/views_manager.py` | ✅ |

**الإصلاحات المنفذة:**
- MED-03: فصل المثيل عن الكلاس - تغيير `Icons = get_icons()` إلى `icons = get_icons()` (حرف صغير) مع تصدير كلاهما من `__init__.py`
- MED-05: استخدام `get_file_watcher()` (Singleton) بدل `FileWatcher()` جديد في دالة `watch_folder()`
- MED-10: إضافة `if total > 0` قبل حساب النسبة المئوية في `_export_excel()`, `_export_csv()`, `_export_pdf()`
- MED-11: استخدام `row_data.get(col, "")` مع ترتيب `self._columns` بدل `row_data.values()` في جميع دوال التصدير
- MED-13: إنشاء `RestoreWorker(QThread)` لتنفيذ الاستعادة في خيط منفصل بدل التنفيذ المتزامن + إضافة `_on_restore_finished()` callback
- MED-21: إضافة `get_by_source_email()`, `get_by_due_date()`, `get_by_due_date_range()` في `task_repository.py` + تحديث `email_integration.py` و `calendar_sync.py` لاستخدام SQL بدل تحميل كل المهام
- MED-27: فحص `result = cursor.fetchone()` و `result is None` قبل الوصول لـ `result[0]`
- MED-28: لف `create_all_views()` في transaction واحد عبر اتصال مباشر مع `rollback` عند الفشل و `commit` عند النجاح

---

## الجلسة 8: المشاكل المنخفضة + التحسينات النهائية
**المدة المتوقعة:** جلسة واحدة
**الهدف:** إغلاق كل المشاكل المتبقية

| # | المشكلة | الخطورة | الملفات | الحالة |
|---|---------|---------|---------|--------|
| LOW-01 | `humanize.activate("ar")` عند الاستيراد | منخفض | `core/utils/formatters.py` | ✅ |
| LOW-02 | معامل `time` يخفي الوحدة | منخفض | `core/utils/formatters.py` | ✅ |
| LOW-03 | القالب المشترك بمرجع مباشر | منخفض | `core/ai/agents/form_agent.py` | ✅ |
| LOW-04 | استيراد دائري محتمل | منخفض | `core/threading/worker.py` | ✅ |
| LOW-06 | ملفات لا تُغلق في main.py | منخفض | `main.py` | ✅ |
| LOW-07 | خط Segoe UI متاح فقط على Windows | منخفض | `ui/components/labels/labels.py` | ✅ |
| LOW-08 | `setCursor(0)` بدل Qt.ArrowCursor | منخفض | `ui/components/buttons/buttons.py` | ✅ |
| LOW-09 | `processEvents()` قد يسبب إعادة دخول | منخفض | `ui/components/progress/progress_dialog.py` | ✅ |
| LOW-10 | `_include_headers` لا تُفحص | منخفض | `ui/components/tables/enterprise/export_manager.py` | ✅ |
| LOW-11 | bare except | منخفض | `ui/components/tables/enterprise/export_manager.py` | ✅ |
| LOW-12 | اتصال DB لا يُغلق عند الإغلاق | منخفض | `ui/windows/launcher/launcher_window.py` | ✅ |
| LOW-13 | Debounce بدون إلغاء السابقة | منخفض | `modules/tasks/screens/task_list/task_list_screen.py` | ✅ |
| LOW-14 | لا يوجد timeout لطلبات AI | منخفض | `modules/copilot/components/chat_sidebar.py` | ✅ |
| LOW-15 | Singletons غير آمنة | منخفض | ملفات متعددة | ✅ |
| LOW-17 | Singleton مزدوج في AIService | منخفض | `core/ai/ai_service.py` | ✅ |
| LOW-18 | تدوير المفاتيح بدون re-encrypt | منخفض | `core/security/encryption.py` | ✅ |
| MED-18 | مكونات AI/Email لا تحترم السمة | متوسط | 5+ ملفات | ✅ |

**ملاحظات:**
- LOW-05 (win32com) و LOW-16 (Emoji) لا تحتاج إصلاح - قيود منصة
- MED-18 مؤجلة لهنا لأنها تحتاج تعديل 5+ ملفات
- LOW-04: الاستيراد الدائري محلول مسبقاً عبر lazy import في worker.py

**الإصلاحات المنفذة (تاريخ: 2026-02-06):**
- LOW-01: تأجيل `humanize.activate("ar")` من import-time إلى lazy initialization عبر `_ensure_arabic()`
- LOW-02: إعادة تسمية معامل `time` إلى `dt` لتجنب إخفاء وحدة Python المدمجة
- LOW-03: إرجاع `copy.deepcopy()` من `get_form_template()` لمنع تعديل القوالب الأصلية
- LOW-04: تم التحقق - محلول مسبقاً عبر lazy import في `worker.py:201`
- LOW-06: إضافة `atexit.register(_close_streams)` لإغلاق ملفات stdout/stderr عند الخروج
- LOW-07: استبدال خط "Segoe UI" (Windows فقط) بـ "Cairo" (متعدد المنصات)
- LOW-08: استبدال `setCursor(0)` بـ `setCursor(Qt.ArrowCursor)`
- LOW-09: إضافة guard flag `_processing_events` لمنع إعادة الدخول في `processEvents()`
- LOW-10: تمرير `include_headers` checkbox إلى `ExportWorker` وتطبيقه في Excel/CSV/PDF
- LOW-11: استبدال `except:` المطلق بـ `except (TypeError, AttributeError):`
- LOW-12: إضافة `disconnect()` في `closeEvent()` لإغلاق اتصال قاعدة البيانات
- LOW-13: استبدال `QTimer.singleShot()` المتكرر بـ `QTimer` واحد مُعاد الاستخدام مع `start()`
- LOW-14: إضافة timeout (60 ثانية) لطلبات AI عبر `time.monotonic()` في حلقة streaming
- LOW-15: إضافة double-checked locking بـ `threading.Lock()` لكل singletons في: template_manager, views_manager, data_exporter, export_scheduler, watcher, encryption, form_agent
- LOW-17: توحيد singleton AIService - إزالة المتغير الوسيط `_service` واستخدام `AIService.__new__()` مباشرة
- LOW-18: إضافة `re_encrypt_values` parameter في `rotate_key()` لإعادة التشفير عند تدوير المفاتيح
- MED-18: إضافة دعم السمة (Dark/Light) لـ 5 مكونات: `chat_panel.py`, `ai_toolbar.py`, `email_panel.py`, `email_viewer.py`, `email_list.py`

---

## ملخص التقدم

| الجلسة | الوصف | عدد المشاكل | الحالة |
|--------|-------|-------------|--------|
| 1 | انهيارات التطبيق | 6 | ✅ |
| 2 | أمان + Import + واجهة | 7 | ✅ |
| 3 | وظائف معطلة | 7 | ✅ |
| 4 | Threading + تسرب ذاكرة | 8 | ✅ |
| 5 | أمان + واجهة | 8 | ✅ |
| 6 | منطق + أداء + تقويم | 8 | ✅ |
| 7 | متوسطة متبقية | 8 | ✅ |
| 8 | منخفضة + تحسينات نهائية | 17 | ✅ |
| **المجموع** | | **69 إصلاح فريد** | |

> **ملاحظة:** بعض المشاكل في التقرير الأصلي (95) تتداخل أو هي توصيات معمارية وليست أخطاء مباشرة. تم تقليصها لـ 69 إصلاح فعلي قابل للتنفيذ.

---

## المشاكل المستثناة (بقرار المستخدم)

| # | المشكلة | السبب |
|---|---------|-------|
| LOW-05 | win32com على Windows فقط | قيد منصة - التطبيق أساساً لـ Windows |
| LOW-16 | Emoji قد لا تُعرض | قيد منصة - مقبول |
