# CLAUDE.md - AI Assistant Guide for INTEGRA

## 📋 Development Plan Reference

> **IMPORTANT:** Always read `claude/INTEGRA_INFRASTRUCTURE_PLAN.md` for the current development roadmap.
>
> The plan covers 3 main tracks:
> - **Track A:** Core Infrastructure (Logging, Error Handling, Auto-Save, Audit, Threading, Scheduler, File Watcher, Backup, Security, Validation)
> - **Track B:** AI Integration (Ollama - Email Agent, Data Agent, Smart Alerts)
> - **Track C:** Email Module (Outlook Classic Sync)

---

## ⚠️ تعليمات التوثيق المستديمة (CRITICAL)

> **قاعدة ذهبية:** التوثيق الفوري بعد اكتمال كل خطوة!

### يجب تحديث الملفات التالية فور اكتمال أي مهمة:

1. **`claude/INTEGRA_INFRASTRUCTURE_PLAN.md`**
   - تحديث حالة المهمة من 🔴 إلى ✅
   - إضافة تاريخ الاكتمال
   - توثيق الملفات المُنشأة أو المُعدّلة

2. **`claude/SESSION_LOG.md`**
   - إضافة ملخص الجلسة في الأعلى (الأحدث أولاً)
   - توثيق: ما تم إنجازه، الملفات الجديدة، كيفية الاستخدام
   - تحديث جدول حالة المراحل

### لماذا هذا مهم؟
- هذان الملفان هما **المرجع الدائم** بين المحادثات
- بدون توثيق فوري، قد تضيع المعلومات
- يضمن استمرارية العمل بين الجلسات المختلفة

### 🔀 إنشاء Pull Request بعد كل تطوير

> **قاعدة إلزامية:** بعد اكتمال أي تغيير في الكود، يجب:
> 1. عمل commit بوصف واضح
> 2. Push إلى الـ branch
> 3. إنشاء Pull Request
> 4. **إرسال رابط الـ PR في المحادثة** ← ليقوم المستخدم بدمجه في main

**مثال الرد المطلوب:**
```
✅ تم إنشاء PR: https://github.com/Insightify2029/integra/pull/XX
```

---

## Project Overview

**INTEGRA** is an enterprise-grade Integrated Management System built with PyQt5 and PostgreSQL. It's a desktop application primarily designed for managing employee data and various business modules.

- **Version:** 2.1.0
- **Author:** Mohamed
- **Language:** Bilingual (Arabic + English with RTL support)
- **Framework:** PyQt5 (GUI) + PostgreSQL (Database)
- **Font:** Cairo (Arabic typography)

## Tech Stack

| Component | Technology |
|-----------|------------|
| GUI Framework | PyQt5 |
| Database | PostgreSQL 16+ |
| DB Driver | psycopg2 |
| Logging | loguru |
| Version Control | Git |
| Runtime | Python 3.11+ |

## Directory Structure

```
integra/
├── main.py                 # Application entry point
├── INTEGRA.pyw             # Windows GUI launcher (no console)
├── INTEGRA.bat             # Windows batch launcher
├── sync_settings.json      # Sync configuration
│
├── core/                   # Infrastructure layer
│   ├── config/             # Centralized configuration
│   │   ├── app/            # APP_NAME, APP_VERSION, etc.
│   │   ├── database/       # DB_HOST, DB_PORT, DB_NAME, etc.
│   │   ├── window/         # WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT
│   │   └── modules/        # Module registry
│   ├── database/           # Database abstraction
│   │   ├── connection/     # PostgreSQL connection management
│   │   └── queries/        # Query utilities
│   ├── logging/            # Structured logging (app + audit)
│   ├── error_handling/     # Global exception handler
│   ├── sync/               # Git + Database sync system (v3.1)
│   └── themes/             # Dark/Light theme system
│
├── ui/                     # Presentation layer
│   ├── windows/            # Main windows
│   │   ├── launcher/       # Main navigation window
│   │   └── base/           # Base window class
│   ├── dialogs/            # Dialog windows
│   │   ├── message/        # Message dialogs
│   │   ├── settings/       # Settings dialog
│   │   ├── themes/         # Theme selection
│   │   └── sync_settings/  # Sync configuration UI
│   └── components/         # Reusable UI components
│       ├── tables/         # Table components (enterprise)
│       ├── cards/          # Card components
│       ├── buttons/        # Button components
│       └── inputs/         # Input components
│
├── modules/                # Business logic modules
│   └── mostahaqat/         # Employee benefits module
│       ├── window/         # Module main window
│       ├── screens/        # Sub-screens
│       │   ├── employees_list/
│       │   ├── employee_profile/
│       │   └── edit_employee/
│       ├── employees/      # Employee business logic
│       ├── stats/          # Statistics cards
│       └── toolbar/        # Module toolbar
│
├── backups/                # Database backups
│   └── database/           # SQL backup files
├── logs/                   # Application logs (gitignored)
└── Tools/                  # Installation/maintenance scripts
```

## Entry Points

### main.py (Primary)
```python
# Standard entry point - run this
python main.py
```

### INTEGRA.pyw (Windows GUI)
- Launches without console window (uses pythonw.exe)
- Redirects stdout/stderr to log files

### INTEGRA.bat (Windows Batch)
- Legacy Windows launcher
- Sets working directory automatically

## Core Modules

### Configuration (`core/config/`)
Import all configs from `core.config`:
```python
from core.config import (
    APP_NAME, APP_VERSION,           # App info
    DB_HOST, DB_PORT, DB_NAME,       # Database
    get_enabled_modules              # Module registry
)
```

### Database (`core/database/`)
Unified query interface:
```python
from core.database import (
    connect, disconnect, is_connected,  # Connection
    select_all, select_one,             # Read
    insert, insert_returning_id,        # Create
    update, update_returning_count,     # Update
    delete, delete_returning_count,     # Delete
    get_scalar, get_count               # Utilities
)

# Example usage
columns, rows = select_all("SELECT * FROM employees WHERE status_id = %s", (1,))
```

### Logging (`core/logging/`)
```python
from core.logging import setup_logging, app_logger, audit_logger

# In main.py only:
setup_logging(debug_mode=True)

# Anywhere else:
app_logger.info("Application event")
app_logger.error("Error occurred", exc_info=True)
audit_logger.log(action="UPDATE", table="employees", record_id=123)
```

### Error Handling (`core/error_handling/`)
```python
from core.error_handling import install_exception_handler

# In main.py after QApplication creation:
install_exception_handler()
```

### Threading (`core/threading/`)
Background task execution without freezing the UI:
```python
from core.threading import run_in_background, Worker, get_task_manager

# Simple usage - run function in background
run_in_background(
    save_to_database,
    args=(data,),
    on_finished=lambda result: print("Done!"),
    on_error=lambda t, m, tb: print(f"Error: {m}")
)

# With progress reporting
def heavy_task(progress_callback, items):
    for i, item in enumerate(items):
        process(item)
        progress_callback(int((i+1)/len(items)*100), f"Processing {i+1}")
    return "Complete"

worker = Worker(heavy_task, args=(my_items,), use_progress=True)
worker.signals.progress.connect(lambda p, msg: progress_bar.setValue(p))
worker.signals.finished.connect(handle_result)
worker.start()

# Task manager for advanced control
tm = get_task_manager()
task_id = tm.run(my_function, on_finished=callback)
tm.cancel(task_id)  # Cancel specific task
tm.cancel_all()     # Cancel all tasks
```

### Sync System (`core/sync/`)
```python
from core.sync import get_sync_manager, SyncWorker

# Get singleton instance
sm = get_sync_manager()

# Start async sync
worker = SyncWorker(sync_type="startup")  # or "shutdown", "git_pull", "git_push"
worker.progress.connect(on_progress)
worker.finished.connect(on_finished)
worker.start()
```

## Database Schema

**PostgreSQL Database:** `integra`

| Table | Purpose |
|-------|---------|
| `employees` | Core employee records |
| `companies` | Company information |
| `departments` | Department management |
| `job_titles` | Job classifications |
| `nationalities` | Nationality data |
| `banks` | Banking institutions |
| `employee_statuses` | Status types (active, terminated, etc.) |

### Key Relationships
```
employees.company_id      → companies.id
employees.department_id   → departments.id
employees.job_title_id    → job_titles.id
employees.nationality_id  → nationalities.id
employees.bank_id         → banks.id
employees.status_id       → employee_statuses.id
```

## Sync System

The sync system (v3.1) provides automatic Git + Database synchronization:

### Sync Types
- `startup`: Git pull → Restore latest backup (on app launch)
- `shutdown`: Backup database → Git push (on app exit)
- `git_pull`: Manual git pull only
- `git_push`: Manual git push with auto-commit
- `db_only`: Database backup only

### Configuration (sync_settings.json)
```json
{
  "sync_on_startup": true,
  "sync_on_exit": true,
  "auto_sync_enabled": true,
  "auto_sync_interval_hours": 3,
  "backup_retention_days": 30
}
```

### Backup Location
- Path: `backups/database/`
- Format: `backup_YYYY-MM-DD_HH-MM-SS.sql`
- Tools: pg_dump (backup), psql (restore)

## Coding Conventions

### Naming
| Type | Convention | Example |
|------|------------|---------|
| Files | snake_case | `sync_manager.py` |
| Classes | PascalCase | `SyncManager` |
| Functions | snake_case | `get_all_employees()` |
| Constants | UPPER_CASE | `DB_HOST`, `APP_VERSION` |

### Patterns Used

**Singleton Pattern:**
```python
sm = get_sync_manager()  # Always use factory function
```

**Signal-Slot (PyQt5):**
```python
class MyWindow(QMainWindow):
    data_changed = pyqtSignal(dict)

    def __init__(self):
        self.data_changed.connect(self.on_data_changed)
```

**Thread Worker Pattern:**
```python
worker = SyncWorker(sync_type="startup")
worker.progress.connect(lambda p, msg: print(f"{p}%: {msg}"))
worker.finished.connect(lambda ok, msg: print(f"Done: {msg}"))
worker.start()
```

### UI Dialog Pattern
```python
from ui.dialogs import show_info, show_error, confirm

show_info(parent, "Title", "Message")
show_error(parent, "Error", "Something went wrong")
if confirm(parent, "Confirm", "Are you sure?"):
    # User confirmed
```

### Module Registration
Each module has its own config file in `core/config/modules/`:
```python
# module_mostahaqat.py
MODULE_ID = "mostahaqat"
MODULE_NAME_AR = "مستحقات العاملين"
MODULE_NAME_EN = "Mostahaqat"
MODULE_ICON = "👥"
MODULE_COLOR = "#2563eb"
MODULE_ENABLED = True
```

## Available Modules

| ID | Arabic Name | English Name | Color | Status |
|----|-------------|--------------|-------|--------|
| mostahaqat | مستحقات العاملين | Mostahaqat | #2563eb | Enabled |
| costing | التكاليف | Costing | #10b981 | Enabled |
| logistics | اللوجستيات | Logistics | #f59e0b | Enabled |
| custody | العهد | Custody | #8b5cf6 | Enabled |
| insurance | التأمين | Insurance | #ef4444 | Enabled |

## Development Guidelines

### Adding a New Module
1. Create module config in `core/config/modules/module_<name>.py`
2. Register in `core/config/modules/modules_list.py`
3. Create module directory in `modules/<name>/`
4. Follow the `mostahaqat` module structure

### Adding UI Components
1. Place in appropriate `ui/components/` subdirectory
2. Export via `__init__.py`
3. Follow existing component patterns

### Database Changes
1. Update relevant query functions in `core/database/queries/`
2. Test with existing sync system
3. Backup current database before schema changes

### Git Workflow
- The app auto-syncs with Git on startup/shutdown
- Database backups are committed and pushed automatically
- Commit messages: "Sync YYYY-MM-DD HH:MM"

## Important Files (Do Not Modify Without Care)

- `main.py` - Application entry point
- `core/sync/sync_manager.py` - Critical sync orchestration
- `core/database/connection/connector.py` - Database connection
- `core/error_handling/exception_hook.py` - Global error handling
- `sync_settings.json` - Sync configuration

## Gitignore Notes

The following are excluded from version control:
- `logs/` - Application logs
- `__pycache__/` - Python bytecode
- `venv/` - Virtual environment
- `.env` - Environment secrets
- `*.log` - Log files

## Common Tasks

### Check Database Connection
```python
from core.database import is_connected, connect
if not is_connected():
    connect()
```

### Run Health Check
```bash
python INTEGRA_HEALTH_CHECK.py
```

### Manual Sync
Use the sync settings dialog in the UI, or:
```python
from core.sync import get_sync_manager
sm = get_sync_manager()
sm.sync(sync_type="git_push")
```

## RTL/Arabic Support

- The application uses Cairo font for Arabic text
- UI components support RTL layout
- Labels use Arabic text with English fallbacks
- Example: `"👥 الموظفين"` (Employees)
