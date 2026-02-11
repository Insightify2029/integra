# CLAUDE.md - AI Assistant Guide for INTEGRA Web

> **INTEGRA Web** is the web-based successor to the INTEGRA PyQt5 desktop application.
> This file is the SINGLE SOURCE OF TRUTH for AI-assisted development.

---

## CRITICAL: Session Protocol

> **Every session MUST start by reading `docs/PRE_SESSION_CHECKLIST.md` and executing it.**
> **Every session MUST end by updating `docs/SESSION_TRACKER.md` and `docs/PROJECT_PLAN.md`.**

---

## Project Overview

| Item | Value |
|------|-------|
| **Project** | INTEGRA Web — Integrated Management System |
| **Migrating from** | PyQt5 Desktop Application (see `../integra/`) |
| **Framework** | Django 5.x |
| **Frontend** | Django Templates + HTMX + Tailwind CSS |
| **Database** | PostgreSQL 16+ (existing schema preserved) |
| **Language** | Python 3.11+ |
| **Primary Language** | Arabic (RTL) with English fallback |
| **Font** | Cairo (Google Fonts) |
| **Author** | Mohamed |

---

## Essential Documents (READ THESE)

| Document | Path | Purpose |
|----------|------|---------|
| **Project Plan** | `docs/PROJECT_PLAN.md` | Full migration roadmap (28 sessions) |
| **Session Tracker** | `docs/SESSION_TRACKER.md` | Progress tracking across sessions |
| **Quality Standards** | `docs/QUALITY_STANDARDS.md` | Coding standards and conventions |
| **Architecture Decisions** | `docs/ARCHITECTURE_DECISIONS.md` | All technical decisions with rationale |
| **Pre-Session Checklist** | `docs/PRE_SESSION_CHECKLIST.md` | What to do at start/end of each session |

---

## Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Web Framework | Django 5.x | See ADR-001 |
| Frontend | Django Templates + HTMX | See ADR-002 |
| CSS | Tailwind CSS + RTL plugin | See ADR-003 |
| Linting/Formatting | Ruff | See ADR-004 |
| Type Checking | mypy + django-stubs | Strict type safety |
| Testing | pytest + pytest-django | See ADR-007 |
| Background Tasks | Celery + Redis | See ADR-008 |
| Logging | structlog | See ADR-009 |
| Dynamic UI | HTMX | See ADR-010 |
| Database | PostgreSQL 16+ | Existing, preserved |
| API (future) | Django REST Framework | Session 23-24 |

---

## Project Structure (Target)

```
integra-web/
├── CLAUDE.md                    # This file (AI guide)
├── manage.py                    # Django management
├── pyproject.toml               # Dependencies + tool config
├── .pre-commit-config.yaml      # Pre-commit hooks
├── .env.example                 # Environment template
├── .github/
│   └── workflows/
│       └── ci.yml               # CI pipeline
├── docs/                        # Project documentation
│   ├── PROJECT_PLAN.md
│   ├── SESSION_TRACKER.md
│   ├── QUALITY_STANDARDS.md
│   ├── ARCHITECTURE_DECISIONS.md
│   └── PRE_SESSION_CHECKLIST.md
├── integra_web/                 # Main Django project
│   ├── __init__.py
│   ├── celery.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── settings/
│       ├── __init__.py
│       ├── base.py              # Shared settings
│       ├── development.py       # Dev overrides
│       └── production.py        # Prod overrides
├── core/                        # Shared infrastructure
│   ├── models/                  # Base models, mixins
│   ├── views/                   # Base views, mixins
│   ├── forms/                   # Base forms
│   ├── services/                # Base service class
│   ├── middleware/               # Logging, error handling
│   ├── management/              # Management commands
│   └── templatetags/            # Custom template tags
├── accounts/                    # Authentication & users
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   └── permissions.py
├── employees/                   # Employee management
│   ├── models.py
│   ├── managers.py
│   ├── services.py
│   ├── views.py
│   ├── forms.py
│   ├── filters.py
│   ├── admin.py
│   └── urls.py
├── companies/                   # Company management
├── departments/                 # Department management
├── lookups/                     # Reference data (job titles, nationalities, banks, statuses)
├── mostahaqat/                  # Employee benefits/calculations
├── costing/                     # Cost management
├── logistics/                   # Logistics management
├── custody/                     # Custody management
├── insurance/                   # Insurance management
├── dashboard/                   # Main dashboard
├── reports/                     # Reporting engine
├── notifications/               # Notification system
├── templates/                   # Global templates
│   ├── base.html
│   ├── components/              # Reusable UI components
│   ├── errors/                  # Error pages (400, 403, 404, 500)
│   └── includes/                # Shared partials
├── static/                      # Static files
│   ├── css/
│   ├── js/
│   └── images/
├── locale/                      # Translation files
│   └── ar/
│       └── LC_MESSAGES/
├── tests/                       # Test suite
│   ├── conftest.py
│   ├── factories.py
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── fixtures/                    # Seed data
```

---

## Mandatory Rules (13 Rules from Desktop — STILL APPLY)

These rules were extracted from 92 bugs found in the desktop version. They are adapted for Django:

### 1. Date/Time Arithmetic
```python
# ❌ NEVER
tomorrow = today.replace(day=today.day + 1)

# ✅ ALWAYS
from datetime import timedelta
tomorrow = today + timedelta(days=1)
```

### 2. SQL Injection Prevention
```python
# ❌ NEVER (even with Django raw SQL)
Employee.objects.raw(f"SELECT * FROM employees WHERE id = {user_id}")

# ✅ ALWAYS
Employee.objects.raw("SELECT * FROM employees WHERE id = %s", [user_id])
# Or better: use the ORM
Employee.objects.get(pk=user_id)
```

### 3. Security
- NEVER expose secrets in code or `__all__`
- Use `django-environ` for ALL environment variables
- Use `hmac.compare_digest()` for sensitive comparisons
- Escape user content: `{{ variable }}` (Django auto-escapes)
- CSRF token on ALL forms: `{% csrf_token %}`

### 4. Error Handling
```python
# ❌ NEVER
except:
    pass

except Exception:
    pass

# ✅ ALWAYS
except SpecificException:
    logger.error("description", exc_info=True)

# ✅ Check for None
result = queryset.first()
if result is not None:
    process(result)
```

### 5. Theme Support
ALL UI MUST respect dark/light theme. Use Tailwind's `dark:` variant:
```html
<div class="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
```

### 6. Arabic/RTL
- ALL user-facing text via `{% trans "text" %}` or `gettext_lazy`
- Arabic is PRIMARY language
- Use logical properties: `ms-4` (margin-start) not `ml-4` (margin-left)
- Font: Cairo

### 7. No Print Statements
```python
# ❌ NEVER
print("debug info")

# ✅ ALWAYS
import structlog
logger = structlog.get_logger()
logger.debug("debug info", context="value")
```

### 8. Database Transactions
```python
# ✅ For multi-step operations
from django.db import transaction

@transaction.atomic
def complex_operation():
    # All DB operations here are atomic
    ...
```

### 9. Query Optimization
```python
# ❌ N+1 queries
for emp in Employee.objects.all():
    print(emp.company.name)  # DB hit per employee!

# ✅ Eager loading
for emp in Employee.objects.select_related("company"):
    print(emp.company.name)  # Single query
```

### 10. Type Safety
- ALL functions MUST have type hints
- mypy strict mode enforced
- Use `django-stubs` for Django type support

### 11. Testing
- ALL services MUST have unit tests
- ALL views MUST have integration tests
- Test names: `test_<what>_<condition>_<expected>`
- Use `factory_boy` for test data (not fixtures)

### 12. Division by Zero
```python
# ❌ NEVER
percentage = count / total * 100

# ✅ ALWAYS
percentage = (count / total * 100) if total > 0 else 0
```

### 13. Documentation Updates
After EVERY session:
- Update `docs/SESSION_TRACKER.md`
- Update `docs/PROJECT_PLAN.md`
- Update `docs/ARCHITECTURE_DECISIONS.md` (if new decisions)

---

## Import Patterns

```python
# Django
from django.db import models, transaction
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.http import HttpRequest, HttpResponse

# Third-party
import structlog
from django_filters import FilterSet

# Local - core
from core.models.mixins import AuditMixin, SoftDeleteMixin
from core.services.base import BaseService
from core.views.mixins import PaginationMixin

# Local - app
from employees.models import Employee
from employees.services import EmployeeService
```

---

## Database Schema (Existing)

| Table | Django App | Description |
|-------|-----------|-------------|
| `employees` | `employees` | Core employee records |
| `companies` | `companies` | Company information |
| `departments` | `departments` | Department management |
| `job_titles` | `lookups` | Job classifications |
| `nationalities` | `lookups` | Nationality data |
| `banks` | `lookups` | Banking institutions |
| `employee_statuses` | `lookups` | Status types |

### Key Relationships
```
employees.company_id      → companies.id
employees.department_id   → departments.id
employees.job_title_id    → job_titles.id
employees.nationality_id  → nationalities.id
employees.bank_id         → banks.id
employees.status_id       → employee_statuses.id
```

---

## Available Modules

| Module | Arabic Name | English Name | Color | Priority |
|--------|-------------|--------------|-------|----------|
| mostahaqat | مستحقات العاملين | Employee Benefits | #2563eb | High (Session 13-18) |
| costing | التكاليف | Costing | #10b981 | Medium (Session 19) |
| logistics | اللوجستيات | Logistics | #f59e0b | Medium (Session 19) |
| custody | العهد | Custody | #8b5cf6 | Medium (Session 20) |
| insurance | التأمين | Insurance | #ef4444 | Medium (Session 20) |

---

## Commands

```bash
# Development
python manage.py runserver              # Start dev server
python manage.py shell_plus             # Enhanced shell
python manage.py makemigrations         # Create migrations
python manage.py migrate                # Apply migrations

# Quality
ruff check .                            # Lint
ruff format .                           # Format
python -m mypy integra_web/             # Type check
python -m pytest                        # Run tests
python -m pytest --cov=integra_web      # Tests with coverage

# Database
python manage.py inspectdb              # Generate models from DB
python manage.py dbshell                # PostgreSQL shell
python manage.py dumpdata --indent=2    # Export data as JSON

# Translations
python manage.py makemessages -l ar     # Extract Arabic strings
python manage.py compilemessages        # Compile translations
```

---

## Git Workflow

```bash
# Branch naming
feat/EMP-123-add-employee-list     # Features
fix/EMP-456-fix-calculation        # Bug fixes
refactor/core-logging              # Refactoring

# Commit message format
feat(employees): add bulk termination endpoint
fix(reports): correct overtime calculation
refactor(core): extract audit mixin
test(employees): add service layer tests
docs(session-5): update tracker and plan
```

---

## DO NOT

- ❌ Use `print()` — use structlog
- ❌ Write raw SQL — use ORM (unless ORM literally cannot express it)
- ❌ Skip type hints — mypy strict mode
- ❌ Hardcode colors — use Tailwind dark: variant
- ❌ Hardcode strings — use gettext_lazy
- ❌ Skip tests — minimum 80% coverage on services
- ❌ Fat views — max 20 lines, delegate to services
- ❌ Bare except — always specific exception + logging
- ❌ Skip CSRF — `{% csrf_token %}` on ALL forms
- ❌ Skip session documentation — update tracker EVERY time
- ❌ Add comments explaining "what" — code should be self-documenting
- ❌ Create files unnecessarily — prefer editing existing ones
- ❌ Over-engineer — minimum complexity for current requirements
