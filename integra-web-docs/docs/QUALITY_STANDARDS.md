# INTEGRA Web - Quality Standards & Engineering Guidelines

> **Version:** 1.0.0 | **Last Updated:** 2026-02-11
> **Purpose:** Define non-negotiable quality standards for the INTEGRA Web migration project

---

## Table of Contents

1. [Architecture Principles](#1-architecture-principles)
2. [Code Quality Standards](#2-code-quality-standards)
3. [Django/Frappe Conventions](#3-djangofrappe-conventions)
4. [Database Standards](#4-database-standards)
5. [Security Standards](#5-security-standards)
6. [Testing Requirements](#6-testing-requirements)
7. [Performance Standards](#7-performance-standards)
8. [Documentation Standards](#8-documentation-standards)
9. [Git & CI/CD Standards](#9-git--cicd-standards)
10. [Arabic/RTL Standards](#10-arabicrtl-standards)

---

## 1. Architecture Principles

### 1.1 Separation of Concerns (SoC)

Every layer has a single responsibility:

```
┌─────────────────────────────────────────────┐
│  Presentation Layer (Templates/JS/CSS)       │  ← UI rendering only
├─────────────────────────────────────────────┤
│  API Layer (Views/Controllers)               │  ← Request/Response handling
├─────────────────────────────────────────────┤
│  Service Layer (Business Logic)              │  ← Core business rules
├─────────────────────────────────────────────┤
│  Data Access Layer (Models/ORM)              │  ← Database operations
├─────────────────────────────────────────────┤
│  Infrastructure (Config/Logging/Cache)       │  ← Cross-cutting concerns
└─────────────────────────────────────────────┘
```

**Rules:**
- Views MUST NOT contain business logic (max 20 lines per view function)
- Models MUST NOT contain presentation logic
- Templates MUST NOT contain database queries
- Services handle ALL business logic and validation

### 1.2 SOLID Principles

| Principle | Application |
|-----------|------------|
| **S**ingle Responsibility | One class = one reason to change |
| **O**pen/Closed | Extend via inheritance/composition, don't modify base classes |
| **L**iskov Substitution | Subclasses must be usable wherever parent is expected |
| **I**nterface Segregation | Small, focused interfaces over large monolithic ones |
| **D**ependency Inversion | Depend on abstractions, not concrete implementations |

### 1.3 DRY (Don't Repeat Yourself)

- If code appears 3+ times → extract to a utility/mixin
- If SQL pattern appears 2+ times → create a model manager method
- If template block appears 2+ times → extract to a partial/component

### 1.4 KISS (Keep It Simple)

- Prefer readability over cleverness
- No premature optimization
- No premature abstraction — 3 similar lines > 1 premature abstraction
- Prefer standard library solutions over custom implementations

---

## 2. Code Quality Standards

### 2.1 Python Style

**Tooling:**
- **Formatter:** Ruff (replaces Black + isort)
- **Linter:** Ruff (replaces Flake8 + pylint)
- **Type Checker:** mypy with django-stubs plugin
- **Pre-commit:** Enforced on every commit

**Configuration (`pyproject.toml`):**
```toml
[tool.ruff]
target-version = "py311"
line-length = 120
src = ["integra_web"]

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade
    "S",    # flake8-bandit (security)
    "T20",  # flake8-print (no print statements)
    "SIM",  # flake8-simplify
    "DJ",   # flake8-django
]
ignore = ["E501"]  # line length handled by formatter

[tool.ruff.lint.isort]
known-first-party = ["integra_web"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.mypy]
python_version = "3.11"
plugins = ["mypy_django_plugin.main"]
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.django-stubs]
django_settings_module = "integra_web.settings"
```

### 2.2 Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Files/Modules | snake_case | `employee_service.py` |
| Classes | PascalCase | `EmployeeService` |
| Functions/Methods | snake_case | `get_active_employees()` |
| Constants | UPPER_SNAKE | `MAX_RETRY_COUNT` |
| Private | _prefix | `_calculate_bonus()` |
| Protected | _prefix | `_internal_state` |
| Template files | snake_case | `employee_list.html` |
| URL patterns | kebab-case | `/employee-profile/` |
| CSS classes | kebab-case | `.employee-card` |
| JS functions | camelCase | `loadEmployeeData()` |

### 2.3 Function/Method Standards

```python
# ✅ CORRECT - Type hints, docstring, manageable size
def calculate_employee_bonus(
    employee_id: int,
    period: date,
    *,
    include_overtime: bool = False,
) -> Decimal:
    """Calculate employee bonus for the given period.

    Args:
        employee_id: The employee's database ID.
        period: The calculation period date.
        include_overtime: Whether to factor in overtime hours.

    Returns:
        The calculated bonus amount.

    Raises:
        EmployeeNotFoundError: If employee doesn't exist.
        InvalidPeriodError: If period is in the future.
    """
    employee = _get_employee_or_raise(employee_id)
    base = _get_base_salary(employee, period)
    multiplier = _get_bonus_multiplier(employee, include_overtime)
    return base * multiplier
```

**Rules:**
- Max function length: 30 lines (excluding docstring)
- Max function parameters: 5 (use dataclass/dict for more)
- Max class methods: 15 (split into mixins if more)
- Max file length: 400 lines (split into modules if more)
- Max cyclomatic complexity: 10

### 2.4 Import Order

```python
# 1. Standard library
import os
from datetime import date, timedelta
from decimal import Decimal

# 2. Third-party packages
from django.db import models
from django.utils.translation import gettext_lazy as _

# 3. Local application
from integra_web.core.logging import app_logger
from integra_web.employees.models import Employee
```

---

## 3. Django/Frappe Conventions

### 3.1 Model Standards

```python
from django.db import models
from django.utils.translation import gettext_lazy as _


class Employee(models.Model):
    """Employee master record."""

    class Status(models.IntegerChoices):
        ACTIVE = 1, _("Active")
        SUSPENDED = 2, _("Suspended")
        TERMINATED = 3, _("Terminated")

    # Required fields first, then optional
    employee_number = models.CharField(
        _("Employee Number"),
        max_length=20,
        unique=True,
        db_index=True,
    )
    full_name_ar = models.CharField(_("Full Name (Arabic)"), max_length=200)
    full_name_en = models.CharField(_("Full Name (English)"), max_length=200, blank=True)

    # Foreign keys
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.PROTECT,
        related_name="employees",
        verbose_name=_("Company"),
    )
    department = models.ForeignKey(
        "departments.Department",
        on_delete=models.PROTECT,
        related_name="employees",
        verbose_name=_("Department"),
    )

    # Status & dates
    status = models.IntegerField(
        _("Status"),
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    hire_date = models.DateField(_("Hire Date"))
    termination_date = models.DateField(_("Termination Date"), null=True, blank=True)

    # Audit fields (on EVERY model)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="+",
        verbose_name=_("Created By"),
    )

    class Meta:
        db_table = "employees"
        ordering = ["employee_number"]
        verbose_name = _("Employee")
        verbose_name_plural = _("Employees")
        indexes = [
            models.Index(fields=["company", "status"]),
            models.Index(fields=["department", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.employee_number} - {self.full_name_ar}"
```

**Model Rules:**
- EVERY model MUST have `created_at`, `updated_at` audit fields
- Use `gettext_lazy` (`_()`) for ALL field labels
- Use `models.PROTECT` for FK by default (not CASCADE)
- Add `db_index=True` on fields used in WHERE/ORDER BY
- Use `IntegerChoices`/`TextChoices` for status fields
- Define `__str__` on every model
- Set explicit `db_table` name
- Add composite indexes for common query patterns

### 3.2 View Standards

```python
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView

from integra_web.employees.services import EmployeeService


class EmployeeListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """List active employees with filtering."""

    permission_required = "employees.view_employee"
    template_name = "employees/employee_list.html"
    context_object_name = "employees"
    paginate_by = 25

    def get_queryset(self):
        return EmployeeService.get_filtered_employees(
            company_id=self.request.GET.get("company"),
            department_id=self.request.GET.get("department"),
            status=self.request.GET.get("status"),
        )
```

**View Rules:**
- ALWAYS use `LoginRequiredMixin` (no public views in this app)
- ALWAYS use `PermissionRequiredMixin` for authorization
- Views are thin — delegate to services
- Use class-based views (CBV) for standard CRUD
- Use function-based views (FBV) only for simple one-off endpoints

### 3.3 Service Layer Pattern

```python
# employees/services.py

from django.db import transaction
from django.db.models import QuerySet

from integra_web.core.logging import app_logger, audit_logger
from integra_web.employees.models import Employee


class EmployeeService:
    """Business logic for employee operations."""

    @staticmethod
    def get_filtered_employees(
        company_id: int | None = None,
        department_id: int | None = None,
        status: int | None = None,
    ) -> QuerySet[Employee]:
        qs = Employee.objects.select_related("company", "department")
        if company_id:
            qs = qs.filter(company_id=company_id)
        if department_id:
            qs = qs.filter(department_id=department_id)
        if status:
            qs = qs.filter(status=status)
        return qs

    @staticmethod
    @transaction.atomic
    def terminate_employee(employee_id: int, termination_date: date, user) -> Employee:
        employee = Employee.objects.select_for_update().get(pk=employee_id)
        employee.status = Employee.Status.TERMINATED
        employee.termination_date = termination_date
        employee.save(update_fields=["status", "termination_date", "updated_at"])

        audit_logger.log(
            action="TERMINATE",
            table="employees",
            record_id=employee_id,
            user=user,
        )
        app_logger.info(f"Employee {employee_id} terminated by {user}")
        return employee
```

### 3.4 URL Patterns

```python
# employees/urls.py
from django.urls import path
from . import views

app_name = "employees"

urlpatterns = [
    path("", views.EmployeeListView.as_view(), name="list"),
    path("<int:pk>/", views.EmployeeDetailView.as_view(), name="detail"),
    path("create/", views.EmployeeCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", views.EmployeeUpdateView.as_view(), name="edit"),
    path("<int:pk>/terminate/", views.EmployeeTerminateView.as_view(), name="terminate"),
]
```

---

## 4. Database Standards

### 4.1 Migration Standards

- NEVER edit existing migrations that have been applied
- One logical change = one migration file
- Always add `verbose_name` to new fields
- Test migrations forward AND backward: `python manage.py migrate <app> <prev_migration>`
- Add data migrations for seed/reference data

### 4.2 Query Optimization

```python
# ❌ WRONG - N+1 query problem
employees = Employee.objects.all()
for emp in employees:
    print(emp.company.name)  # Hits DB for each employee

# ✅ CORRECT - Use select_related for FK
employees = Employee.objects.select_related("company").all()

# ✅ CORRECT - Use prefetch_related for reverse FK / M2M
companies = Company.objects.prefetch_related("employees").all()

# ❌ WRONG - Loading all columns
Employee.objects.all()

# ✅ CORRECT - Only needed columns
Employee.objects.values("id", "full_name_ar", "status")

# ❌ WRONG - Python-side filtering
active = [e for e in Employee.objects.all() if e.status == 1]

# ✅ CORRECT - Database-side filtering
active = Employee.objects.filter(status=Employee.Status.ACTIVE)
```

### 4.3 Transaction Rules

```python
from django.db import transaction

# ✅ For operations that must be atomic
@transaction.atomic
def transfer_employee(employee_id: int, new_dept_id: int) -> None:
    employee = Employee.objects.select_for_update().get(pk=employee_id)
    old_dept = employee.department_id
    employee.department_id = new_dept_id
    employee.save(update_fields=["department_id", "updated_at"])
    TransferLog.objects.create(
        employee=employee,
        from_department_id=old_dept,
        to_department_id=new_dept_id,
    )
```

### 4.4 Raw SQL Rules

- NEVER use raw SQL unless the ORM genuinely cannot express the query
- If raw SQL is needed, ALWAYS use parameterized queries:

```python
# ❌ NEVER
Employee.objects.raw(f"SELECT * FROM employees WHERE id = {user_input}")

# ✅ ALWAYS
Employee.objects.raw("SELECT * FROM employees WHERE id = %s", [user_input])
```

---

## 5. Security Standards

### 5.1 Authentication & Authorization

- Django's built-in auth system for user management
- Permission-based access control on EVERY view
- Session-based authentication (no JWT for server-rendered app)
- Password hashing via Django's PBKDF2 (default)
- CSRF protection on ALL forms (never `@csrf_exempt`)

### 5.2 Input Validation

```python
# ✅ ALWAYS validate at the boundary
from django import forms

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ["employee_number", "full_name_ar", "full_name_en", "company", "department"]

    def clean_employee_number(self):
        number = self.cleaned_data["employee_number"]
        if not number.isalnum():
            raise forms.ValidationError(_("Employee number must be alphanumeric."))
        return number
```

### 5.3 Security Checklist

| Check | Standard |
|-------|----------|
| SQL Injection | ORM only, parameterized for raw SQL |
| XSS | Django auto-escapes templates, use `|escape` for manual |
| CSRF | `{% csrf_token %}` on ALL forms |
| Secrets | `django-environ` for env vars, NEVER in code |
| Passwords | `hmac.compare_digest()` for comparison |
| File Upload | Validate type, size, and name; store outside webroot |
| Headers | `django-security` middleware (HSTS, X-Frame, etc.) |
| Admin | Non-default URL, IP-restricted in production |
| Dependencies | `pip-audit` in CI pipeline |

---

## 6. Testing Requirements

### 6.1 Coverage Requirements

| Type | Minimum Coverage | Tool |
|------|-----------------|------|
| Unit Tests | 80% of services & models | pytest + pytest-django |
| Integration Tests | All API endpoints | pytest + Django test client |
| E2E Tests | Critical user flows | Playwright |
| Security Tests | OWASP Top 10 | pip-audit + bandit |

### 6.2 Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── factories.py             # Model factories (factory_boy)
├── unit/
│   ├── test_employee_service.py
│   └── test_bonus_calculation.py
├── integration/
│   ├── test_employee_views.py
│   └── test_employee_api.py
└── e2e/
    └── test_employee_workflow.py
```

### 6.3 Test Standards

```python
import pytest
from integra_web.employees.services import EmployeeService
from tests.factories import EmployeeFactory


@pytest.mark.django_db
class TestEmployeeService:
    """Tests for EmployeeService business logic."""

    def test_terminate_employee_updates_status(self):
        employee = EmployeeFactory(status=Employee.Status.ACTIVE)
        result = EmployeeService.terminate_employee(
            employee_id=employee.id,
            termination_date=date.today(),
            user=self.admin_user,
        )
        assert result.status == Employee.Status.TERMINATED

    def test_terminate_employee_sets_date(self):
        employee = EmployeeFactory(status=Employee.Status.ACTIVE)
        today = date.today()
        result = EmployeeService.terminate_employee(
            employee_id=employee.id,
            termination_date=today,
            user=self.admin_user,
        )
        assert result.termination_date == today

    def test_terminate_nonexistent_raises(self):
        with pytest.raises(Employee.DoesNotExist):
            EmployeeService.terminate_employee(
                employee_id=99999,
                termination_date=date.today(),
                user=self.admin_user,
            )
```

**Test Rules:**
- Test names: `test_<what>_<condition>_<expected>`
- One assertion per test (prefer)
- Use factories, not fixtures (factory_boy)
- No hardcoded IDs or magic numbers
- Tests must be independent and order-agnostic
- DB tests use `@pytest.mark.django_db`
- Mock external services, never hit real APIs in tests

---

## 7. Performance Standards

### 7.1 Response Time Targets

| Page Type | Target | Max |
|-----------|--------|-----|
| List views | < 200ms | 500ms |
| Detail views | < 100ms | 300ms |
| Form submissions | < 300ms | 1000ms |
| Report generation | < 2s | 5s |
| API endpoints | < 150ms | 500ms |

### 7.2 Database Query Limits

- Max queries per page: **10** (use `django-debug-toolbar` to monitor)
- Use `select_related` / `prefetch_related` to prevent N+1
- Pagination on ALL list views (max 50 per page)
- Use `only()` / `defer()` for large models
- Add database indexes for common query patterns

### 7.3 Caching Strategy

```python
from django.core.cache import cache

# Cache expensive lookups
CACHE_TIMEOUT = 60 * 15  # 15 minutes

def get_company_list():
    key = "company_list_active"
    result = cache.get(key)
    if result is None:
        result = list(Company.objects.filter(is_active=True).values("id", "name"))
        cache.set(key, result, CACHE_TIMEOUT)
    return result
```

---

## 8. Documentation Standards

### 8.1 Code Documentation

- Module-level docstring on every `.py` file
- Class docstring explaining purpose
- Method docstring for public methods (Google style)
- Inline comments only for "why", not "what"

### 8.2 API Documentation

- Every endpoint documented with: URL, method, params, response, errors
- Use Django REST Framework's built-in schema generation if using DRF

### 8.3 Commit Messages

```
<type>(<scope>): <description>

[optional body]
[optional footer]
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `style`

Examples:
```
feat(employees): add bulk termination endpoint
fix(reports): correct overtime calculation for part-time
refactor(core): extract common audit mixin from models
test(employees): add service layer tests for transfer flow
```

---

## 9. Git & CI/CD Standards

### 9.1 Branch Strategy

```
main                    ← Production-ready code
├── develop             ← Integration branch
│   ├── feat/EMP-123    ← Feature branches
│   ├── fix/EMP-456     ← Bug fix branches
│   └── refactor/core   ← Refactoring branches
```

### 9.2 Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.0
    hooks:
      - id: ruff-check
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.14.0
    hooks:
      - id: mypy
        additional_dependencies:
          - django-stubs>=5.2.0
          - types-requests

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: [--maxkb=500]
      - id: detect-private-key
```

### 9.3 CI Pipeline (GitHub Actions)

Every PR must pass:
1. Ruff lint + format check
2. mypy type check
3. pytest with coverage >= 80%
4. pip-audit security check
5. Migration check (`python manage.py makemigrations --check`)

---

## 10. Arabic/RTL Standards

### 10.1 Translation

- ALL user-facing text via `gettext_lazy`
- Arabic is the PRIMARY language
- English is the FALLBACK language
- Translation files in `locale/ar/LC_MESSAGES/`

### 10.2 RTL Layout

```html
<!-- Base template -->
<html dir="rtl" lang="ar">

<!-- Support both directions -->
<div class="container" dir="{{ LANGUAGE_BIDI|yesno:'rtl,ltr' }}">
```

### 10.3 Font

- Primary: **Cairo** (Google Fonts) — excellent Arabic support
- Fallback: `system-ui, -apple-system, sans-serif`

```css
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap');

body {
    font-family: 'Cairo', system-ui, -apple-system, sans-serif;
}
```

---

## Enforcement

These standards are enforced through:
1. **Pre-commit hooks** — Automated on every commit
2. **CI pipeline** — Blocks PR merge on failure
3. **Code review** — Required for all PRs
4. **Claude AI** — Follows these standards in all generated code

> **Any deviation from these standards requires explicit documentation in ARCHITECTURE_DECISIONS.md with justification.**
