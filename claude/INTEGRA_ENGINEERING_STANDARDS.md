# INTEGRA Web -- Software Engineering Standards & Quality Manual

> **Document Purpose:** Comprehensive, actionable engineering standards for building the INTEGRA ERP
> system with zero-bug aspiration. Every rule includes a principle, a mandate, a code example,
> and a verification method.
>
> **Stack:** Django 5.x + PostgreSQL 16+ + HTMX + Tailwind CSS
> **Language:** Arabic-first bilingual (RTL support)
> **Date:** 2026-02-11

---

## Table of Contents

1. [Code Quality Principles](#1-code-quality-principles)
2. [Architecture & Design](#2-architecture--design)
3. [Testing Strategy](#3-testing-strategy)
4. [Error Handling & Resilience](#4-error-handling--resilience)
5. [Security (OWASP for Django)](#5-security-owasp-for-django)
6. [Database Design](#6-database-design)
7. [Project Management Methodology](#7-project-management-methodology)
8. [Code Review Standards](#8-code-review-standards)
9. [Documentation Standards](#9-documentation-standards)
10. [Git & Version Control](#10-git--version-control)
11. [Django-Specific Best Practices](#11-django-specific-best-practices)
12. [Performance](#12-performance)
13. [Zero-Bug Methodologies](#13-zero-bug-methodologies)
14. [Appendix A: Pre-Commit Configuration](#appendix-a-pre-commit-configuration)
15. [Appendix B: Quality Checklists](#appendix-b-quality-checklists)

---

## 1. Code Quality Principles

### 1.1 SOLID Principles

#### S -- Single Responsibility Principle (SRP)

**PRINCIPLE:** A class/module should have only one reason to change.

**RULE:** Every Django app, every service class, every view must own exactly one concern.
Do not mix data access, business logic, and presentation in the same unit.

**EXAMPLE:**
```python
# --- WRONG: View does validation, business logic, DB access, and email ---
class EmployeeCreateView(View):
    def post(self, request):
        name = request.POST["name_ar"]
        if not name:
            return HttpResponse("Name required", status=400)
        emp = Employee.objects.create(name_ar=name, ...)
        send_mail("New employee", f"{name} added", ...)
        AuditLog.objects.create(action="CREATE", ...)
        return redirect("employee-list")

# --- CORRECT: Each concern is a separate unit ---
# services/employee_service.py
class EmployeeService:
    """Owns employee business logic only."""

    def __init__(self, repo: EmployeeRepository, notifier: Notifier):
        self._repo = repo
        self._notifier = notifier

    def create_employee(self, data: EmployeeCreateDTO) -> Employee:
        employee = self._repo.create(data)
        self._notifier.notify_employee_created(employee)
        return employee

# views/employee_views.py
class EmployeeCreateView(LoginRequiredMixin, View):
    """Owns HTTP concern only."""

    def post(self, request):
        form = EmployeeCreateForm(request.POST)
        if not form.is_valid():
            return render(request, "hr/employee_form.html", {"form": form})
        service = get_employee_service()
        service.create_employee(form.to_dto())
        return redirect("hr:employee-list")
```

**VERIFICATION:**
- Each file must be under 300 lines (enforced by ruff rule).
- Each class must have at most one public-facing domain verb (create, update, delete, list).
- Code review checklist item: "Does this class have more than one reason to change?"

---

#### O -- Open/Closed Principle (OCP)

**PRINCIPLE:** Software entities should be open for extension but closed for modification.

**RULE:** Use abstract base classes and the Strategy pattern for behaviors that vary.
Never modify existing working code to add a new variant -- extend it.

**EXAMPLE:**
```python
# core/notifications/base.py
from abc import ABC, abstractmethod

class Notifier(ABC):
    @abstractmethod
    def send(self, recipient: str, message: str) -> None: ...

# core/notifications/email.py
class EmailNotifier(Notifier):
    def send(self, recipient: str, message: str) -> None:
        send_mail(subject="INTEGRA", message=message, recipient_list=[recipient], ...)

# core/notifications/sms.py  (new channel -- NO changes to existing code)
class SMSNotifier(Notifier):
    def send(self, recipient: str, message: str) -> None:
        sms_gateway.send(to=recipient, body=message)
```

**VERIFICATION:**
- `grep` for classes that use `if isinstance(...)` chains to branch on type -- refactor to polymorphism.
- mypy `--strict` ensures abstract methods are implemented.

---

#### L -- Liskov Substitution Principle (LSP)

**PRINCIPLE:** Subtypes must be substitutable for their base types without altering correctness.

**RULE:** If a function accepts `Notifier`, every concrete `Notifier` subclass must honor
the same contract (same signature, same postconditions, no extra preconditions).

**EXAMPLE:**
```python
# WRONG -- subclass restricts parent's contract
class ReadOnlyEmployeeRepository(EmployeeRepository):
    def create(self, data: EmployeeCreateDTO) -> Employee:
        raise NotImplementedError("Read-only!")  # Violates LSP

# CORRECT -- separate interface
class EmployeeReader(ABC):
    @abstractmethod
    def get_by_id(self, pk: int) -> Employee: ...

class EmployeeWriter(ABC):
    @abstractmethod
    def create(self, data: EmployeeCreateDTO) -> Employee: ...
```

**VERIFICATION:**
- Ensure no subclass raises `NotImplementedError` for inherited abstract methods.
- Run `mypy --strict`: type-level contract violations are caught.

---

#### I -- Interface Segregation Principle (ISP)

**PRINCIPLE:** Clients should not be forced to depend on interfaces they do not use.

**RULE:** Keep ABCs small and focused. Prefer multiple small protocols over one large ABC.

**EXAMPLE:**
```python
from typing import Protocol

class Readable(Protocol):
    def get(self, pk: int) -> Employee: ...
    def list(self, filters: dict) -> QuerySet[Employee]: ...

class Writable(Protocol):
    def create(self, data: EmployeeCreateDTO) -> Employee: ...
    def update(self, pk: int, data: EmployeeUpdateDTO) -> Employee: ...

class Deletable(Protocol):
    def delete(self, pk: int) -> None: ...

# A service that only reads does not depend on write/delete interfaces
class EmployeeReportService:
    def __init__(self, reader: Readable):
        self._reader = reader
```

**VERIFICATION:**
- No ABC/Protocol should have more than 5 methods.
- mypy `Protocol` checking enforces structural subtyping.

---

#### D -- Dependency Inversion Principle (DIP)

**PRINCIPLE:** High-level modules should not depend on low-level modules. Both should depend on abstractions.

**RULE:** Service classes receive their dependencies via constructor injection (or Django's
dependency injection container). Never import concrete repositories/gateways directly
inside a service method.

**EXAMPLE:**
```python
# WRONG -- tightly coupled to Django ORM
class EmployeeService:
    def get_active(self):
        return Employee.objects.filter(status__name="active")

# CORRECT -- depends on abstraction
class EmployeeService:
    def __init__(self, repo: EmployeeReader):
        self._repo = repo

    def get_active(self) -> list[Employee]:
        return self._repo.list({"status": "active"})

# Wiring (in apps.py or a container module)
def get_employee_service() -> EmployeeService:
    return EmployeeService(repo=DjangoEmployeeRepository())
```

**VERIFICATION:**
- Service modules must NOT import `from django.db import models` or ORM querysets.
- `ruff` rule: ban specific imports in service layer directories via `per-file-ignores`.

---

### 1.2 DRY (Don't Repeat Yourself)

**PRINCIPLE:** Every piece of knowledge must have a single, unambiguous, authoritative
representation within a system.

**RULE:**
- Extract repeated query logic into custom managers/querysets.
- Extract repeated form validation into mixins.
- Extract repeated template fragments into `{% include %}` partials.
- Shared constants live in `core/constants.py`.

**EXAMPLE:**
```python
# WRONG -- duplicated filter logic
# In view A:
Employee.objects.filter(status__name="active", company_id=company_id)
# In view B:
Employee.objects.filter(status__name="active", company_id=company_id)

# CORRECT -- custom queryset
class EmployeeQuerySet(models.QuerySet):
    def active(self) -> "EmployeeQuerySet":
        return self.filter(status__name="active")

    def for_company(self, company_id: int) -> "EmployeeQuerySet":
        return self.filter(company_id=company_id)

# Usage in any view:
Employee.objects.active().for_company(company_id)
```

**VERIFICATION:**
- `ruff` duplicate detection.
- Code review: "Is this logic defined elsewhere? If so, extract."

---

### 1.3 KISS (Keep It Simple, Stupid)

**PRINCIPLE:** The simplest solution that works is the best solution.

**RULE:**
- No meta-programming unless there is a proven need.
- No custom ORM backends.
- No class hierarchies deeper than 3 levels.
- Prefer Django's built-in features before reaching for third-party packages.

**VERIFICATION:**
- Cyclomatic complexity per function must not exceed 10 (enforced by ruff `C901`).
- Review checklist: "Could a junior developer understand this in 5 minutes?"

---

### 1.4 YAGNI (You Aren't Gonna Need It)

**PRINCIPLE:** Do not build features or abstractions until they are actually needed.

**RULE:**
- Do not create abstract base classes until there are at least 2 concrete implementations.
- Do not add configuration options for hypothetical future needs.
- Do not build a "plugin system" until the second plugin is needed.

**VERIFICATION:**
- Code review: "Is this being used right now? If not, remove it."
- Dead code detection via `vulture` or `ruff` unused-import rules.

---

### 1.5 Clean Code (Robert C. Martin)

**RULE -- Naming:**
- Functions: verb + noun (`create_employee`, `calculate_salary`).
- Classes: noun (`EmployeeService`, `DepartmentRepository`).
- Booleans: `is_`, `has_`, `can_` prefix (`is_active`, `has_dependents`).
- Constants: `UPPER_SNAKE_CASE` (`MAX_RETRY_ATTEMPTS`).
- No abbreviations except universally understood ones (`pk`, `id`, `url`, `html`).

**RULE -- Functions:**
- Maximum 20 lines per function (soft limit; 30 hard limit).
- Maximum 4 parameters. Use dataclasses/TypedDicts for more.
- One level of abstraction per function.

**RULE -- Comments:**
- Code should be self-documenting. Comments explain *why*, not *what*.
- Every public function/method MUST have a docstring (enforced by ruff `D`).
- TODOs must have a ticket reference: `# TODO(INTEGRA-42): Handle pagination`.

**EXAMPLE:**
```python
# WRONG
def proc(d, c, s, f):
    # process data
    ...

# CORRECT
def create_employee_from_form(
    form_data: EmployeeCreateDTO,
    company: Company,
) -> Employee:
    """Create a new employee record and trigger onboarding notifications.

    Args:
        form_data: Validated employee creation data.
        company: The company to assign the employee to.

    Returns:
        The newly created Employee instance.

    Raises:
        DuplicateEmployeeError: If employee_code already exists.
    """
    ...
```

**VERIFICATION:**
- ruff rules: `D` (docstring), `N` (naming), `C901` (complexity).
- `radon` for maintainability index (must be A or B grade).

---

### 1.6 Defensive Programming

**PRINCIPLE:** Code should validate its assumptions and fail early with clear messages.

**RULE:**
- Validate all function inputs at the boundary (views, forms, API endpoints).
- Use type hints + runtime checks for critical paths.
- Never trust data from external sources (user input, API responses, file contents).

**EXAMPLE:**
```python
def set_employee_salary(employee_id: int, amount: Decimal) -> None:
    if not isinstance(amount, Decimal):
        raise TypeError(f"amount must be Decimal, got {type(amount).__name__}")
    if amount < Decimal("0"):
        raise ValueError(f"Salary cannot be negative: {amount}")
    if amount > Decimal("999999.99"):
        raise ValueError(f"Salary exceeds maximum: {amount}")

    employee = Employee.objects.get(pk=employee_id)
    employee.salary = amount
    employee.save(update_fields=["salary", "updated_at"])
```

**VERIFICATION:**
- mypy `--strict` catches type mismatches at analysis time.
- Unit tests include negative/boundary test cases.

---

### 1.7 Fail-Fast Principle

**PRINCIPLE:** If something is wrong, fail immediately and loudly rather than propagating
a corrupt state.

**RULE:**
- Use `django.core.exceptions.ValidationError` at the model layer.
- Use assertions in development for invariants (disabled in production).
- Services raise domain-specific exceptions immediately upon detecting invalid state.
- Never swallow exceptions silently.

**EXAMPLE:**
```python
class Employee(models.Model):
    def clean(self):
        if self.hire_date and self.hire_date > date.today():
            raise ValidationError(
                {"hire_date": _("Hire date cannot be in the future.")}
            )

    def save(self, *args, **kwargs):
        self.full_clean()  # Fail fast -- validate before hitting DB
        super().save(*args, **kwargs)
```

**VERIFICATION:**
- `grep -r "except:$"` and `grep -r "except Exception: pass"` must return zero results.
- All `except` blocks must log the exception.

---

## 2. Architecture & Design

### 2.1 Project Architecture: Layered Service Architecture

We adopt a **pragmatic layered architecture** adapted for Django, inspired by Clean Architecture
but without over-engineering the repository layer where Django's ORM provides adequate abstraction.

```
integra_web/                          # Django project root
|
+-- config/                           # Project configuration
|   +-- settings/
|   |   +-- base.py                   # Shared settings
|   |   +-- local.py                  # Development settings
|   |   +-- production.py             # Production settings
|   |   +-- test.py                   # Test settings
|   +-- urls.py                       # Root URL configuration
|   +-- wsgi.py
|   +-- asgi.py
|
+-- core/                             # Shared infrastructure (Django app)
|   +-- models/                       # Abstract base models
|   +-- exceptions.py                 # Project-wide exception hierarchy
|   +-- constants.py                  # Global constants
|   +-- types.py                      # Shared type definitions
|   +-- middleware/                    # Custom middleware
|   +-- templatetags/                 # Global template tags
|   +-- utils/                        # Pure utility functions
|
+-- apps/                             # Business domain apps
|   +-- hr/                           # HR Module (first priority)
|   |   +-- models/                   # Django models (data layer)
|   |   +-- services/                 # Business logic (service layer)
|   |   +-- selectors/                # Read-only query logic
|   |   +-- forms/                    # Django forms (validation)
|   |   +-- views/                    # HTTP handlers (thin)
|   |   +-- urls.py
|   |   +-- admin.py
|   |   +-- constants.py
|   |   +-- exceptions.py             # App-specific exceptions
|   |   +-- types.py                  # App-specific DTOs
|   |   +-- tests/
|   |   |   +-- test_models.py
|   |   |   +-- test_services.py
|   |   |   +-- test_selectors.py
|   |   |   +-- test_views.py
|   |   |   +-- test_forms.py
|   |   |   +-- factories.py          # Test data factories
|   |   +-- templates/hr/
|   |   |   +-- employee_list.html
|   |   |   +-- employee_detail.html
|   |   |   +-- partials/             # HTMX partial templates
|   |   |       +-- _employee_row.html
|   |   |       +-- _employee_form.html
|   |   +-- static/hr/
|   |
|   +-- costing/                      # Future: Costing module
|   +-- logistics/                    # Future: Logistics module
|   +-- custody/                      # Future: Custody module
|   +-- insurance/                    # Future: Insurance module
|
+-- templates/                        # Global templates
|   +-- base.html                     # Master layout (RTL-aware)
|   +-- components/                   # Reusable UI components
|   +-- partials/                     # Shared HTMX partials
|
+-- static/                           # Global static files
|   +-- css/
|   +-- js/
|   +-- images/
|
+-- locale/                           # i18n translation files
|   +-- ar/
|   +-- en/
|
+-- docs/                             # Documentation
|   +-- adr/                          # Architecture Decision Records
|   +-- api/                          # API documentation
|
+-- tests/                            # Cross-app integration/E2E tests
|   +-- integration/
|   +-- e2e/
|
+-- manage.py
+-- pyproject.toml
+-- .pre-commit-config.yaml
+-- .env.example
```

---

### 2.2 Layer Responsibilities

| Layer | Directory | Responsibility | Can Import From |
|-------|-----------|---------------|-----------------|
| **Presentation** | `views/`, `templates/`, `forms/` | HTTP handling, form validation, rendering | Services, Selectors, Forms |
| **Service** | `services/` | Business logic, orchestration, write operations | Models, Selectors, External APIs |
| **Selector** | `selectors/` | Complex read queries, reporting | Models only |
| **Model** | `models/` | Data structure, DB constraints, simple validation | Nothing (lowest layer) |

**THE GOLDEN RULE OF IMPORTS:**

```
Views --> Services --> Models
Views --> Selectors --> Models
Views --> Forms

Services NEVER import from Views.
Models NEVER import from Services or Views.
```

---

### 2.3 Service Layer Pattern

**PRINCIPLE:** Business logic lives in service functions, not in views or models.

**RULE:**
- Services are plain Python functions (or classes for complex workflows).
- Services take validated, typed inputs and return domain objects.
- Services handle transactions explicitly.
- One service module per domain aggregate.

**EXAMPLE:**
```python
# apps/hr/services/employee_service.py
from django.db import transaction
from apps.hr.models import Employee
from apps.hr.types import EmployeeCreateDTO
from apps.hr.exceptions import DuplicateEmployeeCodeError
from core.exceptions import IntegraBizError

def create_employee(*, data: EmployeeCreateDTO, created_by: User) -> Employee:
    """Create a new employee with all business rules enforced.

    Args:
        data: Validated employee data.
        created_by: The user performing the action (for audit).

    Returns:
        The newly created Employee.

    Raises:
        DuplicateEmployeeCodeError: If employee_code is already taken.
        IntegraBizError: If business rules are violated.
    """
    if Employee.objects.filter(employee_code=data.employee_code).exists():
        raise DuplicateEmployeeCodeError(code=data.employee_code)

    with transaction.atomic():
        employee = Employee.objects.create(
            employee_code=data.employee_code,
            name_ar=data.name_ar,
            name_en=data.name_en,
            national_id=data.national_id,
            nationality_id=data.nationality_id,
            hire_date=data.hire_date,
            department_id=data.department_id,
            job_title_id=data.job_title_id,
            bank_id=data.bank_id,
            iban=data.iban,
            company_id=data.company_id,
            status_id=data.status_id,
        )
        AuditLog.objects.create(
            user=created_by,
            action="CREATE",
            table_name="employees",
            record_id=employee.pk,
        )
    return employee
```

**VERIFICATION:**
- Views must not contain `Model.objects.create()`, `.update()`, `.delete()` calls.
- Views must call service functions for any write operation.
- Service functions must be decorated with `@transaction.atomic` or use explicit `with transaction.atomic()`.

---

### 2.4 Selector Pattern (Read-Only Queries)

**PRINCIPLE:** Complex read queries are extracted into selector functions, keeping views thin
and enabling reuse.

**EXAMPLE:**
```python
# apps/hr/selectors/employee_selectors.py
from django.db.models import QuerySet, Count, Q
from apps.hr.models import Employee

def get_employee_list(
    *,
    company_id: int | None = None,
    department_id: int | None = None,
    status: str | None = None,
    search: str | None = None,
) -> QuerySet[Employee]:
    """Return filtered employee list with optimized joins."""
    qs = Employee.objects.select_related(
        "department", "job_title", "nationality", "company", "status"
    )

    if company_id is not None:
        qs = qs.filter(company_id=company_id)
    if department_id is not None:
        qs = qs.filter(department_id=department_id)
    if status is not None:
        qs = qs.filter(status__name=status)
    if search:
        qs = qs.filter(
            Q(name_ar__icontains=search)
            | Q(name_en__icontains=search)
            | Q(employee_code__icontains=search)
        )

    return qs.order_by("-created_at")


def get_department_stats(company_id: int) -> QuerySet:
    """Return employee count per department."""
    return (
        Employee.objects.filter(company_id=company_id, status__name="active")
        .values("department__name_ar", "department__name_en")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
```

---

### 2.5 Data Transfer Objects (DTOs)

**RULE:** Use dataclasses or TypedDicts for data flowing between layers.

```python
# apps/hr/types.py
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

@dataclass(frozen=True)
class EmployeeCreateDTO:
    employee_code: str
    name_ar: str
    name_en: str
    national_id: str
    nationality_id: int
    hire_date: date
    department_id: int
    job_title_id: int
    bank_id: int
    iban: str
    company_id: int
    status_id: int
```

---

### 2.6 Design Patterns for INTEGRA

| Pattern | Where | Purpose |
|---------|-------|---------|
| **Service Layer** | `apps/*/services/` | Encapsulate business logic |
| **Selector** | `apps/*/selectors/` | Complex read-only queries |
| **Repository** (light) | Custom Managers/QuerySets | Data access abstraction within Django ORM |
| **Factory** | `tests/factories.py` | Test data generation (using `factory_boy`) |
| **Strategy** | `core/notifications/` | Pluggable notification channels |
| **Observer** | Django signals (sparingly) | Cross-app decoupled events |
| **DTO** | `apps/*/types.py` | Typed data transfer between layers |
| **Template Method** | Abstract base models | Shared model behaviors (timestamps, audit) |

---

### 2.7 Anti-Patterns to Avoid

| Anti-Pattern | What It Looks Like | What To Do Instead |
|---|---|---|
| **God Model** | 2000-line `models.py` with business logic | Split into model + service + selector |
| **Fat View** | View does validation + DB + email + audit | Move logic to service, keep view thin |
| **Spaghetti Signals** | 10+ signals triggering each other | Explicit service calls; signals only for cross-app |
| **Premature Abstraction** | ABC with one implementation | Wait until second implementation is needed |
| **Raw SQL Everywhere** | `cursor.execute(f"SELECT...")` | Use ORM; if raw SQL needed, use parameterized queries |
| **Settings Import Soup** | `from django.conf import settings` in 50 files | Inject config via constructor or app-level constants |
| **Circular Imports** | App A imports from App B and vice versa | Introduce a shared `core` app or use signals |

---

## 3. Testing Strategy

### 3.1 Test Pyramid

```
                    /\
                   /  \        E2E Tests (10-15%)
                  /    \       Selenium/Playwright -- full user flows
                 /------\
                /        \     Integration Tests (30-35%)
               /          \    Django TestCase -- views, forms, DB
              /------------\
             /              \  Unit Tests (50-55%)
            /                \ SimpleTestCase -- services, selectors, utils
           /------------------\
```

**Coverage Targets:**
| Layer | Target | Notes |
|-------|--------|-------|
| Services | 95%+ | Critical business logic |
| Models | 90%+ | Constraints, clean(), properties |
| Selectors | 85%+ | Query correctness |
| Views | 80%+ | HTTP status codes, redirects, permissions |
| Forms | 90%+ | Validation rules |
| Templates | Smoke tests | Render without errors |
| **Overall** | **85%+** | Measured per app |

---

### 3.2 Test-Driven Development (TDD) Cycle

```
     +-------+
     |       |
     v       |
   RED ------+------> GREEN -------> REFACTOR
   (Write a       (Write minimum     (Clean up,
    failing        code to pass)      tests stay
    test)                             green)
```

**RULE:** For every new service function:
1. **RED:** Write the test first. It must fail.
2. **GREEN:** Write the simplest implementation that makes it pass.
3. **REFACTOR:** Clean up both test and implementation.

**EXAMPLE -- TDD in action:**
```python
# Step 1: RED -- test first
# apps/hr/tests/test_services.py
import pytest
from apps.hr.services.employee_service import create_employee
from apps.hr.exceptions import DuplicateEmployeeCodeError
from apps.hr.tests.factories import EmployeeCreateDTOFactory, EmployeeFactory

@pytest.mark.django_db
class TestCreateEmployee:
    def test_creates_employee_with_valid_data(self, admin_user):
        data = EmployeeCreateDTOFactory()
        employee = create_employee(data=data, created_by=admin_user)

        assert employee.pk is not None
        assert employee.employee_code == data.employee_code
        assert employee.name_ar == data.name_ar

    def test_raises_on_duplicate_code(self, admin_user):
        existing = EmployeeFactory(employee_code="EMP-001")
        data = EmployeeCreateDTOFactory(employee_code="EMP-001")

        with pytest.raises(DuplicateEmployeeCodeError):
            create_employee(data=data, created_by=admin_user)

    def test_creates_audit_log(self, admin_user):
        data = EmployeeCreateDTOFactory()
        employee = create_employee(data=data, created_by=admin_user)

        assert AuditLog.objects.filter(
            record_id=employee.pk,
            action="CREATE",
            table_name="employees",
        ).exists()
```

---

### 3.3 What to Test (Per Layer)

#### Models
```python
@pytest.mark.django_db
class TestEmployeeModel:
    def test_str_returns_name_ar(self):
        emp = Employee(name_ar="محمد أحمد")
        assert str(emp) == "محمد أحمد"

    def test_clean_rejects_future_hire_date(self):
        emp = Employee(hire_date=date.today() + timedelta(days=1))
        with pytest.raises(ValidationError):
            emp.full_clean()

    def test_employee_code_unique(self):
        EmployeeFactory(employee_code="EMP-001")
        with pytest.raises(IntegrityError):
            EmployeeFactory(employee_code="EMP-001")
```

#### Services
```python
@pytest.mark.django_db
class TestUpdateEmployeeDepartment:
    def test_updates_department_successfully(self, admin_user):
        emp = EmployeeFactory(department__name_en="IT")
        new_dept = DepartmentFactory(name_en="HR")

        updated = update_employee_department(
            employee_id=emp.pk,
            department_id=new_dept.pk,
            updated_by=admin_user,
        )

        assert updated.department_id == new_dept.pk

    def test_raises_on_nonexistent_employee(self, admin_user):
        with pytest.raises(EmployeeNotFoundError):
            update_employee_department(
                employee_id=99999,
                department_id=1,
                updated_by=admin_user,
            )
```

#### Views
```python
@pytest.mark.django_db
class TestEmployeeListView:
    def test_requires_login(self, client):
        response = client.get(reverse("hr:employee-list"))
        assert response.status_code == 302  # Redirect to login

    def test_renders_employee_list(self, auth_client):
        EmployeeFactory.create_batch(5)
        response = auth_client.get(reverse("hr:employee-list"))

        assert response.status_code == 200
        assert "employee_list" in response.context
        assert len(response.context["employee_list"]) == 5

    def test_htmx_returns_partial(self, auth_client):
        response = auth_client.get(
            reverse("hr:employee-list"),
            HTTP_HX_REQUEST="true",
        )
        assert "partials/_employee_table.html" in [
            t.name for t in response.templates
        ]
```

#### Forms
```python
class TestEmployeeCreateForm:
    def test_valid_data(self):
        form = EmployeeCreateForm(data={
            "employee_code": "EMP-001",
            "name_ar": "محمد أحمد",
            "national_id": "1234567890",
            ...
        })
        assert form.is_valid()

    def test_rejects_empty_name_ar(self):
        form = EmployeeCreateForm(data={"name_ar": ""})
        assert not form.is_valid()
        assert "name_ar" in form.errors

    def test_rejects_duplicate_national_id(self):
        EmployeeFactory(national_id="1234567890")
        form = EmployeeCreateForm(data={"national_id": "1234567890", ...})
        assert not form.is_valid()
```

---

### 3.4 Testing Tools

| Tool | Purpose | Config Key |
|------|---------|------------|
| `pytest` + `pytest-django` | Test runner | `pyproject.toml: [tool.pytest.ini_options]` |
| `pytest-xdist` | Parallel test execution | `-n auto` |
| `factory_boy` | Test data factories | `tests/factories.py` per app |
| `coverage.py` | Code coverage measurement | `.coveragerc` |
| `pytest-randomly` | Detect inter-test dependencies | Default enabled |
| `Playwright` | E2E browser tests | `tests/e2e/` |
| `django-test-plus` | Cleaner test assertions | Optional |

**Test Configuration (`pyproject.toml`):**
```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings.test"
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = [
    "--strict-markers",
    "--strict-config",
    "-ra",
    "--tb=short",
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "e2e: marks end-to-end tests",
]

[tool.coverage.run]
source = ["apps", "core"]
omit = ["*/tests/*", "*/migrations/*"]

[tool.coverage.report]
fail_under = 85
show_missing = true
```

---

### 3.5 Test Factories (factory_boy)

```python
# apps/hr/tests/factories.py
import factory
from factory.django import DjangoModelFactory
from apps.hr.models import Employee, Department, Company
from apps.hr.types import EmployeeCreateDTO

class CompanyFactory(DjangoModelFactory):
    class Meta:
        model = Company

    code = factory.Sequence(lambda n: f"C{n:03d}")
    name_ar = factory.Faker("company", locale="ar_SA")
    name_en = factory.Faker("company")

class DepartmentFactory(DjangoModelFactory):
    class Meta:
        model = Department

    name_ar = factory.Faker("job", locale="ar_SA")
    name_en = factory.Faker("job")

class EmployeeFactory(DjangoModelFactory):
    class Meta:
        model = Employee

    employee_code = factory.Sequence(lambda n: f"EMP-{n:04d}")
    name_ar = factory.Faker("name", locale="ar_SA")
    name_en = factory.Faker("name")
    national_id = factory.Sequence(lambda n: f"{n:010d}")
    department = factory.SubFactory(DepartmentFactory)
    company = factory.SubFactory(CompanyFactory)
    hire_date = factory.Faker("date_this_decade")

class EmployeeCreateDTOFactory(factory.Factory):
    class Meta:
        model = EmployeeCreateDTO

    employee_code = factory.Sequence(lambda n: f"EMP-{n:04d}")
    name_ar = factory.Faker("name", locale="ar_SA")
    name_en = factory.Faker("name")
```

---

## 4. Error Handling & Resilience

### 4.1 Exception Hierarchy

```python
# core/exceptions.py

class IntegraError(Exception):
    """Base exception for all INTEGRA application errors."""

    def __init__(self, message: str, code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class IntegraBizError(IntegraError):
    """Business rule violation."""
    pass


class IntegraNotFoundError(IntegraError):
    """Requested resource does not exist."""

    def __init__(self, resource: str, identifier: str | int):
        super().__init__(
            message=f"{resource} with identifier '{identifier}' not found.",
            code="NOT_FOUND",
        )
        self.resource = resource
        self.identifier = identifier


class IntegraPermissionError(IntegraError):
    """User lacks permission for the requested action."""
    pass


class IntegraValidationError(IntegraError):
    """Input validation failed."""

    def __init__(self, errors: dict[str, list[str]]):
        self.errors = errors
        super().__init__(
            message="Validation failed.",
            code="VALIDATION_ERROR",
        )


class IntegraExternalServiceError(IntegraError):
    """External service (API, email, etc.) is unavailable or returned an error."""
    pass
```

```python
# apps/hr/exceptions.py
from core.exceptions import IntegraBizError, IntegraNotFoundError

class DuplicateEmployeeCodeError(IntegraBizError):
    def __init__(self, code: str):
        super().__init__(
            message=f"Employee code '{code}' already exists.",
            code="DUPLICATE_EMPLOYEE_CODE",
        )

class EmployeeNotFoundError(IntegraNotFoundError):
    def __init__(self, employee_id: int):
        super().__init__(resource="Employee", identifier=employee_id)
```

---

### 4.2 Exception Handling in Views (Error Boundary)

```python
# core/middleware/exception_middleware.py
import logging
import structlog

logger = structlog.get_logger(__name__)

class IntegraExceptionMiddleware:
    """Catches domain exceptions and converts them to appropriate HTTP responses."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, IntegraValidationError):
            logger.warning(
                "validation_error",
                errors=exception.errors,
                path=request.path,
            )
            return render(request, "errors/400.html", {
                "errors": exception.errors,
            }, status=400)

        if isinstance(exception, IntegraNotFoundError):
            logger.warning(
                "resource_not_found",
                resource=exception.resource,
                identifier=exception.identifier,
            )
            return render(request, "errors/404.html", {
                "message": exception.message,
            }, status=404)

        if isinstance(exception, IntegraPermissionError):
            logger.warning(
                "permission_denied",
                user=getattr(request.user, "pk", None),
                path=request.path,
            )
            return render(request, "errors/403.html", status=403)

        if isinstance(exception, IntegraBizError):
            logger.error(
                "business_error",
                code=exception.code,
                message=exception.message,
            )
            return render(request, "errors/400.html", {
                "message": exception.message,
            }, status=400)

        # Unexpected errors -- log full traceback
        logger.exception(
            "unhandled_exception",
            path=request.path,
            method=request.method,
            user=getattr(request.user, "pk", None),
        )
        return None  # Let Django's default 500 handler take over
```

---

### 4.3 Structured Logging Strategy

**RULE:** Use `structlog` for JSON-structured logging throughout the application.

```python
# config/settings/base.py -- Logging Configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "structlog.stdlib.ProcessorFormatter",
            "processor": structlog.dev.ConsoleRenderer(),  # dev
            # For production: structlog.processors.JSONRenderer()
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {"level": "INFO", "propagate": True},
        "django.db.backends": {"level": "WARNING", "propagate": False},
        "apps": {"level": "DEBUG", "propagate": True},
    },
}

# structlog configuration
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
```

**Logging Rules:**
| Level | When to Use | Example |
|-------|-------------|---------|
| `DEBUG` | Detailed diagnostic info (dev only) | `logger.debug("query_executed", sql=query, params=params)` |
| `INFO` | Normal operations worth recording | `logger.info("employee_created", employee_id=emp.pk)` |
| `WARNING` | Unexpected but recoverable situation | `logger.warning("slow_query", duration_ms=1500, query=q)` |
| `ERROR` | Operation failed, needs attention | `logger.error("payment_failed", employee_id=pk, reason=r)` |
| `CRITICAL` | System is unusable | `logger.critical("database_connection_lost")` |

**NEVER log:**
- Passwords, tokens, or secrets
- Full national ID numbers (mask: `****567890`)
- Credit card numbers
- Session IDs

---

### 4.4 Graceful Degradation

**RULE:** When a non-critical subsystem fails, the rest of the application continues to work.

```python
def create_employee(*, data: EmployeeCreateDTO, created_by: User) -> Employee:
    with transaction.atomic():
        employee = Employee.objects.create(**data.__dict__)

    # Non-critical: notification failure should NOT roll back employee creation
    try:
        notifier.notify_employee_created(employee)
    except IntegraExternalServiceError:
        logger.warning(
            "notification_failed",
            employee_id=employee.pk,
            event="employee_created",
        )

    return employee
```

---

## 5. Security (OWASP for Django)

### 5.1 SQL Injection Prevention

**PRINCIPLE:** Never construct SQL queries using string formatting with user input.

**RULE:**
- Use Django ORM for all queries (default protection).
- If raw SQL is absolutely necessary, use parameterized queries.
- NEVER use f-strings, `.format()`, or `%` formatting for SQL.

**EXAMPLE:**
```python
# WRONG -- SQL injection vulnerability
Employee.objects.raw(f"SELECT * FROM employees WHERE name_ar = '{name}'")
cursor.execute("SELECT * FROM employees WHERE id = %d" % employee_id)

# CORRECT -- parameterized
Employee.objects.raw("SELECT * FROM employees WHERE name_ar = %s", [name])
cursor.execute("SELECT * FROM employees WHERE id = %s", [employee_id])

# CORRECT -- ORM (inherently safe)
Employee.objects.filter(name_ar=name)
```

**VERIFICATION:**
- `bandit` scan for SQL injection patterns (S608).
- `grep -r "cursor.execute.*f\"" apps/` must return zero results.
- `grep -r "\.raw\(f\"" apps/` must return zero results.

---

### 5.2 XSS Prevention

**PRINCIPLE:** All user-supplied data rendered in templates must be escaped.

**RULE:**
- Django auto-escapes template variables by default. Never disable it.
- NEVER use `|safe` or `mark_safe()` on user input.
- Use `{{ value|json_script:"my-data" }}` to pass data to JavaScript.
- Sanitize any stored HTML with `bleach` before rendering.

**EXAMPLE:**
```html
<!-- WRONG -- XSS vulnerability -->
{{ employee.bio|safe }}
<script>var name = "{{ employee.name_ar }}";</script>

<!-- CORRECT -- auto-escaped -->
{{ employee.bio }}

<!-- CORRECT -- safe JS data passing -->
{{ employee_data|json_script:"employee-data" }}
<script>
    const data = JSON.parse(
        document.getElementById("employee-data").textContent
    );
</script>
```

**VERIFICATION:**
- `grep -r "|safe" templates/` -- each occurrence must be justified and reviewed.
- `grep -r "mark_safe" apps/` -- each occurrence must handle only trusted data.

---

### 5.3 CSRF Protection

**RULE:**
- `CsrfViewMiddleware` must be in MIDDLEWARE (enabled by default).
- Every POST form must include `{% csrf_token %}`.
- HTMX requests must include the CSRF token in headers.
- Never use `@csrf_exempt` unless for webhooks with proper alternative verification.

**EXAMPLE (HTMX + CSRF):**
```html
<!-- base.html -- configure HTMX to send CSRF token -->
<body hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>
    {% block content %}{% endblock %}
</body>
```

```python
# WRONG
@csrf_exempt
def update_employee(request):
    ...

# CORRECT -- no decorator needed, CSRF middleware handles it
def update_employee(request):
    ...
```

---

### 5.4 Input Validation & Sanitization

**RULE:**
- All input is validated through Django Forms or DRF Serializers.
- Model-level validation via `clean()` as a second defense line.
- Database constraints as the final defense line.

```python
# apps/hr/forms/employee_forms.py
import bleach
from django import forms
from apps.hr.models import Employee

class EmployeeCreateForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            "employee_code", "name_ar", "name_en", "national_id",
            "nationality", "hire_date", "department", "job_title",
            "bank", "iban", "company", "status",
        ]

    def clean_name_ar(self):
        name = self.cleaned_data["name_ar"]
        # Sanitize: strip HTML tags
        return bleach.clean(name, tags=[], strip=True)

    def clean_employee_code(self):
        code = self.cleaned_data["employee_code"]
        if not code.startswith("EMP-"):
            raise forms.ValidationError("Employee code must start with 'EMP-'.")
        return code

    def clean_iban(self):
        iban = self.cleaned_data.get("iban", "")
        if iban and len(iban) < 15:
            raise forms.ValidationError("IBAN is too short.")
        return iban

    def to_dto(self) -> EmployeeCreateDTO:
        """Convert cleaned form data to a service-layer DTO."""
        d = self.cleaned_data
        return EmployeeCreateDTO(
            employee_code=d["employee_code"],
            name_ar=d["name_ar"],
            ...
        )
```

---

### 5.5 Django Security Settings (Production)

```python
# config/settings/production.py
from .base import *  # noqa: F403

DEBUG = False

# HTTPS
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HSTS
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Content Security
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# Session
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 28800  # 8 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Secret key from environment
SECRET_KEY = env("DJANGO_SECRET_KEY")

# Allowed hosts from environment
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")
```

**VERIFICATION:**
```bash
python manage.py check --deploy
```
This command checks for common security misconfigurations.

---

### 5.6 Security Checklist

| Check | How | Tool |
|-------|-----|------|
| SQL Injection | No f-strings in raw SQL | `bandit -r apps/ -t B608` |
| XSS | No unescaped user data | Template review, `grep \|safe` |
| CSRF | Token in all POST forms | Django's built-in check |
| Secrets | No hardcoded passwords | `gitleaks`, `detect-secrets` |
| Dependencies | No known vulnerabilities | `pip-audit`, `safety check` |
| Headers | Security headers set | `python manage.py check --deploy` |
| Auth | Rate limiting on login | `django-axes` |
| Permissions | Every view has auth check | Code review |

---

## 6. Database Design

### 6.1 Normalization (3NF Minimum)

**RULE:** All tables must be in Third Normal Form (3NF) at minimum.

| Normal Form | Rule | INTEGRA Example |
|-------------|------|-----------------|
| **1NF** | Atomic values, no repeating groups | `name_ar` and `name_en` as separate columns, not a JSON blob |
| **2NF** | No partial dependencies on composite keys | All tables use single `id` primary key |
| **3NF** | No transitive dependencies | Department name stored in `departments` table, not repeated in `employees` |

**Exception:** Selective denormalization is permitted for read-heavy reporting views,
documented with an ADR explaining the trade-off.

---

### 6.2 Model Design Standards

```python
# core/models/base.py
from django.db import models

class TimestampedModel(models.Model):
    """Abstract base model with automatic timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BilingualNameModel(models.Model):
    """Abstract base model for entities with Arabic/English names."""

    name_ar = models.CharField(max_length=200, verbose_name="الاسم بالعربية")
    name_en = models.CharField(
        max_length=200, blank=True, default="", verbose_name="Name (English)"
    )

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return self.name_ar or self.name_en


class CodedModel(models.Model):
    """Abstract base model for entities with a unique code."""

    code = models.CharField(
        max_length=20, unique=True, verbose_name="Code"
    )

    class Meta:
        abstract = True
```

---

### 6.3 Index Strategy

**RULE:** Add indexes based on actual query patterns, not speculation.

```python
class Employee(TimestampedModel, BilingualNameModel):
    employee_code = models.CharField(max_length=20, unique=True)  # auto-indexed
    national_id = models.CharField(max_length=20, db_index=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)  # auto-indexed
    status = models.ForeignKey(EmployeeStatus, on_delete=models.PROTECT)

    class Meta:
        indexes = [
            # Composite index for common filter: active employees per department
            models.Index(
                fields=["department", "status"],
                name="idx_emp_dept_status",
            ),
            # Partial index for active employees only
            models.Index(
                fields=["name_ar"],
                name="idx_emp_active_name",
                condition=models.Q(status__name="active"),
            ),
            # GIN index for full-text search (Arabic)
            GinIndex(
                fields=["name_ar", "name_en"],
                name="idx_emp_name_gin",
                opclasses=["gin_trgm_ops", "gin_trgm_ops"],
            ),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(employee_code__regex=r"^EMP-\d{4}$"),
                name="chk_employee_code_format",
            ),
        ]
```

**Index Decision Table:**

| Query Pattern | Index Type | When |
|---|---|---|
| Exact match (`WHERE code = X`) | B-tree (default) | Always |
| Range query (`WHERE date > X`) | B-tree | When frequently filtered |
| Full-text search (`LIKE '%X%'`) | GIN with trigram | For search fields |
| Status flags (`WHERE active = true`) | Partial index | When majority of queries filter on one value |
| JSON fields | GIN | For JSONB containment queries |
| Geo-spatial | GiST | If location data added |

---

### 6.4 Migration Best Practices

**RULE:**
1. Never edit a migration that has been applied to any shared environment.
2. Keep data migrations separate from schema migrations.
3. Use `AddIndexConcurrently` for production index additions.
4. Test migrations both forward and backward.

**EXAMPLE -- Safe index addition for production:**
```python
# Generated migration: 0005_add_employee_name_index.py
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models

class Migration(migrations.Migration):
    atomic = False  # Required for CONCURRENTLY

    dependencies = [
        ("hr", "0004_previous_migration"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="employee",
            index=models.Index(
                fields=["name_ar"],
                name="idx_employee_name_ar",
            ),
        ),
    ]
```

**EXAMPLE -- Data migration (separate from schema):**
```python
# 0006_populate_default_statuses.py
from django.db import migrations

def create_default_statuses(apps, schema_editor):
    EmployeeStatus = apps.get_model("hr", "EmployeeStatus")
    statuses = [
        {"name_ar": "نشط", "name_en": "Active"},
        {"name_ar": "غير نشط", "name_en": "Inactive"},
    ]
    for s in statuses:
        EmployeeStatus.objects.get_or_create(name_en=s["name_en"], defaults=s)

def reverse(apps, schema_editor):
    EmployeeStatus = apps.get_model("hr", "EmployeeStatus")
    EmployeeStatus.objects.filter(name_en__in=["Active", "Inactive"]).delete()

class Migration(migrations.Migration):
    dependencies = [("hr", "0005_add_employee_name_index")]
    operations = [migrations.RunPython(create_default_statuses, reverse)]
```

---

### 6.5 Data Integrity

```python
# Enforce at ALL three levels:

# Level 1: Application (forms/services)
class EmployeeCreateForm(forms.ModelForm):
    def clean_hire_date(self):
        hire_date = self.cleaned_data["hire_date"]
        if hire_date > date.today():
            raise forms.ValidationError("Cannot be in the future.")
        return hire_date

# Level 2: Model
class Employee(models.Model):
    def clean(self):
        if self.hire_date and self.hire_date > date.today():
            raise ValidationError({"hire_date": "Cannot be in the future."})

# Level 3: Database (migration)
class Migration(migrations.Migration):
    operations = [
        migrations.AddConstraint(
            model_name="employee",
            constraint=models.CheckConstraint(
                check=models.Q(hire_date__lte=Now()),
                name="chk_hire_date_not_future",
            ),
        ),
    ]
```

---

### 6.6 Query Optimization Rules

| Rule | Bad | Good |
|------|-----|------|
| No `SELECT *` in raw SQL | `SELECT * FROM employees` | `SELECT id, name_ar, dept FROM employees` |
| Use `.only()` for partial loads | `Employee.objects.all()` (if only need name) | `Employee.objects.only("id", "name_ar")` |
| Count at DB level | `len(Employee.objects.all())` | `Employee.objects.count()` |
| Exists check | `Employee.objects.count() > 0` | `Employee.objects.exists()` |
| Bulk operations | Loop of `.save()` | `Employee.objects.bulk_create(list)` |

---

## 7. Project Management Methodology

### 7.1 Session-Based Sprint Methodology

Since INTEGRA is developed through AI pair programming sessions, each session is treated
as a mini-sprint with clear objectives.

```
SESSION WORKFLOW:

1. PLAN (5 min)
   - Read SESSION_LOG.md for context
   - Read INTEGRA_INFRASTRUCTURE_PLAN.md for next tasks
   - Define 2-3 concrete deliverables for this session

2. BUILD (main session)
   - Follow TDD: test -> implement -> refactor
   - Commit after each complete feature/fix
   - Update documentation as you go

3. VERIFY (10 min)
   - Run full test suite: pytest --tb=short
   - Run linting: ruff check .
   - Run type check: mypy apps/
   - Run security scan: bandit -r apps/

4. DOCUMENT (5 min)
   - Update SESSION_LOG.md with session summary
   - Update INTEGRA_INFRASTRUCTURE_PLAN.md task status
   - Create PR with clear description

5. SHIP
   - Push to feature branch
   - Create PR
   - Share PR link
```

---

### 7.2 Definition of Ready (DoR)

A task is **Ready** to work on when:

| # | Criterion | How to Check |
|---|-----------|-------------|
| 1 | Clear user story or requirement | Written in INTEGRA_INFRASTRUCTURE_PLAN.md |
| 2 | Acceptance criteria defined | At least 3 testable criteria |
| 3 | Database schema decided | Models designed, reviewed |
| 4 | Dependencies identified | Required apps/packages listed |
| 5 | No blocking dependencies | Prior tasks completed |
| 6 | Test scenarios outlined | At least happy path + 2 error cases |

---

### 7.3 Definition of Done (DoD)

A task is **Done** when ALL of the following are true:

| # | Criterion | Verification |
|---|-----------|-------------|
| 1 | Code compiles and runs | `python manage.py check` passes |
| 2 | All tests pass | `pytest` returns 0 |
| 3 | Coverage target met | `coverage report --fail-under=85` |
| 4 | No linting errors | `ruff check .` returns 0 |
| 5 | No type errors | `mypy apps/` returns 0 |
| 6 | No security issues | `bandit -r apps/` returns 0 |
| 7 | Migrations created and tested | `python manage.py migrate --check` |
| 8 | Documentation updated | SESSION_LOG.md and plan updated |
| 9 | PR created with description | Link shared |
| 10 | RTL layout verified | Arabic text displays correctly |

---

### 7.4 Quality Gates

```
                   GATE 1              GATE 2              GATE 3
    Feature        Code                Integration         Release
    Branch    ---> Review    ------->  Testing     ------> Candidate
                   |                   |                    |
                   | - Ruff pass       | - All tests pass   | - Full regression
                   | - Mypy pass       | - Coverage >= 85%  | - Performance test
                   | - Bandit pass     | - DB migrations OK | - Security audit
                   | - Docstrings      | - HTMX partials OK | - RTL review
                   | - Tests written   | - Arabic rendering | - Deployment test
```

---

### 7.5 Risk Management

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Data loss during migration from PyQt5 | Medium | Critical | Backup before every migration step; validate row counts |
| Arabic text rendering issues | High | Medium | Test with real Arabic data from day 1; RTL-specific tests |
| N+1 queries in employee list | High | High | `select_related`/`prefetch_related` in every selector; django-debug-toolbar |
| Session state loss between AI sessions | High | Medium | Comprehensive SESSION_LOG.md updates after every session |
| HTMX partial template complexity | Medium | Medium | Keep partials small (<50 lines); test individually |

---

## 8. Code Review Standards

### 8.1 Automated Checks (Pre-Merge)

All of the following must pass before a PR can be merged:

```yaml
# .github/workflows/ci.yml
name: CI
on: [pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -r requirements/dev.txt

      - name: Lint (ruff)
        run: ruff check .

      - name: Format check (ruff)
        run: ruff format --check .

      - name: Type check (mypy)
        run: mypy apps/ core/

      - name: Security scan (bandit)
        run: bandit -r apps/ core/ -c pyproject.toml

      - name: Tests
        run: pytest --tb=short -q

      - name: Coverage
        run: |
          coverage run -m pytest
          coverage report --fail-under=85

      - name: Migration check
        run: python manage.py migrate --check
```

---

### 8.2 Manual Review Checklist

Every PR reviewer must check:

**Correctness:**
- [ ] Does the code do what the PR description says?
- [ ] Are edge cases handled (empty input, None, boundary values)?
- [ ] Are error conditions handled and logged?
- [ ] Is the happy path tested?
- [ ] Are at least 2 error path tests written?

**Architecture:**
- [ ] Does business logic live in services, not views?
- [ ] Are write operations in services wrapped in `transaction.atomic()`?
- [ ] Are read queries in selectors using `select_related`/`prefetch_related`?
- [ ] Do views delegate to services/selectors (thin views)?

**Security:**
- [ ] No hardcoded secrets?
- [ ] No raw SQL with user input?
- [ ] Forms validate and sanitize input?
- [ ] Views check permissions?

**Database:**
- [ ] Migrations are reversible?
- [ ] No new N+1 query risks?
- [ ] Indexes added for new filter fields?

**Internationalization:**
- [ ] Arabic text properly handled?
- [ ] All user-facing strings use `gettext`/`_()` or `gettext_lazy`?
- [ ] RTL layout works?

**Performance:**
- [ ] No unnecessary queries in loops?
- [ ] Pagination used for list views?
- [ ] Caching considered for expensive operations?

---

### 8.3 Performance Review Checklist

- [ ] Run `django-debug-toolbar` in development and check query count
- [ ] Each list view must execute < 10 SQL queries
- [ ] Each detail view must execute < 5 SQL queries
- [ ] No query takes more than 100ms (check with `EXPLAIN ANALYZE`)
- [ ] Response time < 200ms for standard pages
- [ ] Response time < 500ms for complex reports

---

## 9. Documentation Standards

### 9.1 Code Documentation

**RULE:** Every public function, class, and module must have a docstring.

```python
# Google-style docstrings (enforced by ruff D rules)

def transfer_employee(
    *,
    employee_id: int,
    new_department_id: int,
    effective_date: date,
    transferred_by: User,
) -> Employee:
    """Transfer an employee to a new department.

    Validates that the employee exists, the department exists, and
    the effective date is not in the past. Creates an audit log entry
    for the transfer.

    Args:
        employee_id: The primary key of the employee to transfer.
        new_department_id: The primary key of the target department.
        effective_date: When the transfer takes effect.
        transferred_by: The user authorizing the transfer.

    Returns:
        The updated Employee instance.

    Raises:
        EmployeeNotFoundError: If employee does not exist.
        DepartmentNotFoundError: If department does not exist.
        IntegraBizError: If effective_date is in the past.
    """
```

**Type Hints:** Mandatory on all function signatures.

```python
# WRONG
def get_employees(company_id, status=None):
    ...

# CORRECT
def get_employees(
    company_id: int,
    status: str | None = None,
) -> QuerySet[Employee]:
    ...
```

---

### 9.2 Architecture Documentation (C4 Model)

Maintain four levels of architecture diagrams:

**Level 1 -- System Context:**
```
[External User] --> [INTEGRA Web App]
[INTEGRA Web App] --> [PostgreSQL Database]
[INTEGRA Web App] --> [Email Server (SMTP)]
[INTEGRA Web App] --> [Ollama AI Service]
```

**Level 2 -- Container:**
```
[Browser (HTMX+Tailwind)] --> [Django Web Server]
[Django Web Server] --> [PostgreSQL 16+]
[Django Web Server] --> [Redis Cache]
[Django Web Server] --> [Celery Workers]
[Celery Workers] --> [PostgreSQL 16+]
```

**Level 3 -- Component (per Django app):**
```
HR App:
  [Views] --> [Services] --> [Models]
  [Views] --> [Selectors] --> [Models]
  [Views] --> [Forms]
  [Templates] --> [Partials]
```

**Level 4 -- Code:** Auto-generated from docstrings and type hints.

Store diagrams in `docs/architecture/` as Mermaid files (`.mmd`) which render in GitHub.

---

### 9.3 Architecture Decision Records (ADRs)

**RULE:** Record every significant architectural decision.

Store in `docs/adr/` using the MADR template:

```markdown
# ADR-0001: Use Service Layer Pattern for Business Logic

## Status
Accepted

## Context
Business logic is currently spread across views, models, and signals.
This makes it hard to test, reuse, and maintain.

## Decision
We will use a Service Layer pattern where:
- All write operations go through service functions
- All complex read operations go through selector functions
- Views remain thin HTTP handlers

## Consequences

### Positive
- Business logic is centralized and testable
- Views are simple and focused on HTTP
- Services can be reused across views, management commands, and API

### Negative
- Extra layer of indirection
- More files to maintain
- Developers must resist putting logic in views

## References
- HackSoft Django Styleguide: https://github.com/HackSoftware/Django-Styleguide
- Cosmic Python: https://www.cosmicpython.com/
```

---

### 9.4 Session Documentation

Every development session must update `claude/SESSION_LOG.md`:

```markdown
## Session 2026-02-12 -- Employee CRUD Implementation

### Completed
- [x] Employee model with all constraints
- [x] EmployeeService: create, update
- [x] Employee list view with HTMX pagination
- [x] 15 unit tests, 8 integration tests

### Files Created/Modified
- `apps/hr/models/employee.py` (new)
- `apps/hr/services/employee_service.py` (new)
- `apps/hr/tests/test_services.py` (new)
- `apps/hr/views/employee_views.py` (new)

### Decisions Made
- Used `select_related` for department in list view (avoids N+1)
- Added GIN index for Arabic name search

### Next Session
- Employee detail view
- Employee edit form
- Delete with soft-delete pattern
```

---

## 10. Git & Version Control

### 10.1 Branching Strategy

We use **GitHub Flow** (simplified trunk-based development):

```
main (protected)
  |
  +-- feature/hr-employee-crud
  +-- feature/hr-department-management
  +-- fix/employee-list-pagination
  +-- chore/update-dependencies
```

**Branch Naming Convention:**
```
<type>/<short-description>

Types:
  feature/  -- New feature
  fix/      -- Bug fix
  chore/    -- Maintenance, refactoring, dependencies
  docs/     -- Documentation only
  test/     -- Test additions/fixes
```

**Rules:**
- `main` is always deployable.
- All changes go through PRs.
- Branch from `main`, merge back to `main`.
- Delete branch after merge.
- No force pushes to `main` ever.

---

### 10.2 Commit Message Convention (Conventional Commits)

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

**Types:**

| Type | When |
|------|------|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test` | Adding or correcting tests |
| `docs` | Documentation only changes |
| `style` | Formatting, missing semicolons, etc. |
| `perf` | Performance improvement |
| `chore` | Updating build tasks, configs, etc. |
| `ci` | CI/CD changes |

**Scope:** The Django app or module affected (e.g., `hr`, `core`, `config`).

**Examples:**
```
feat(hr): add employee creation service with audit logging

Implements EmployeeService.create_employee() with:
- Duplicate code detection
- Atomic transaction with audit log
- Comprehensive validation

Closes #12

---

fix(hr): prevent N+1 queries in employee list view

Add select_related for department, job_title, and status
to the employee_list selector. Reduces query count from
182 to 3 for the standard employee list page.

---

refactor(core): extract bilingual name model to base module

Move BilingualNameModel from hr/models to core/models/base
so it can be reused by all modules (costing, logistics, etc.)
```

**VERIFICATION:**
- Pre-commit hook validates commit message format.
- Configuration in `pyproject.toml` with `commitizen` or `conventional-pre-commit`.

---

### 10.3 PR Process

```
1. Developer creates feature branch
2. Developer pushes code
3. CI runs automatically (lint, type check, security, tests)
4. Developer creates PR with:
   - Clear title (conventional commit style)
   - Description of WHAT changed and WHY
   - Screenshots for UI changes
   - Test plan
5. Reviewer reviews using checklist (Section 8.2)
6. All CI checks must pass
7. At least 1 approval required
8. Squash and merge to main
9. Delete feature branch
```

---

## 11. Django-Specific Best Practices

### 11.1 Fat Models, Thin Views (Refined)

In our architecture, the mantra becomes:
**"Thin Models, Thin Views, Fat Services"**

| Layer | What Goes Here | What Does NOT Go Here |
|-------|---------------|----------------------|
| **Models** | Field definitions, `__str__`, `clean()`, `Meta`, properties, custom managers | Business logic, external API calls, email sending |
| **Views** | HTTP handling, form instantiation, calling services, template rendering | Business logic, complex queries, data transformation |
| **Services** | Business rules, orchestration, transaction management | HTTP concepts, template rendering |
| **Selectors** | Complex queries, aggregations, reporting queries | Write operations, business rules |
| **Forms** | Input validation, data cleaning, DTO conversion | Business logic, database queries |

---

### 11.2 Custom Managers and QuerySets

```python
# apps/hr/models/managers.py
from django.db import models

class EmployeeQuerySet(models.QuerySet):
    def active(self):
        return self.filter(status__name="active")

    def inactive(self):
        return self.filter(status__name="inactive")

    def for_company(self, company_id: int):
        return self.filter(company_id=company_id)

    def for_department(self, department_id: int):
        return self.filter(department_id=department_id)

    def with_full_relations(self):
        """Eagerly load all FK relations to prevent N+1."""
        return self.select_related(
            "department", "job_title", "nationality",
            "company", "status", "bank",
        )

    def search(self, query: str):
        """Search by Arabic name, English name, or employee code."""
        return self.filter(
            models.Q(name_ar__icontains=query)
            | models.Q(name_en__icontains=query)
            | models.Q(employee_code__icontains=query)
        )


class EmployeeManager(models.Manager):
    def get_queryset(self):
        return EmployeeQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def with_full_relations(self):
        return self.get_queryset().with_full_relations()
```

Usage:
```python
# In selectors (readable, chainable, reusable)
Employee.objects.active().for_company(1).with_full_relations().search("محمد")
```

---

### 11.3 Form Validation Patterns

```python
# Three-level validation:

# Level 1: Field-level (clean_<fieldname>)
def clean_national_id(self):
    nid = self.cleaned_data["national_id"]
    if not nid.isdigit():
        raise forms.ValidationError(_("National ID must contain only digits."))
    if len(nid) != 10:
        raise forms.ValidationError(_("National ID must be exactly 10 digits."))
    return nid

# Level 2: Cross-field (clean)
def clean(self):
    cleaned = super().clean()
    hire_date = cleaned.get("hire_date")
    status = cleaned.get("status")
    if status and status.name == "active" and not hire_date:
        raise forms.ValidationError(
            _("Active employees must have a hire date.")
        )
    return cleaned

# Level 3: Unique-together (validate_unique -- called by full_clean)
# Handled automatically by Meta.constraints
```

---

### 11.4 Template Organization

```
templates/
+-- base.html                    # Master layout
+-- base_auth.html               # Auth pages layout (login, etc.)
+-- components/
|   +-- _pagination.html         # Reusable pagination
|   +-- _search_bar.html         # Reusable search
|   +-- _alert.html              # Flash messages
|   +-- _modal.html              # Modal container
|   +-- _loading.html            # HTMX loading indicator
|   +-- _breadcrumb.html         # Breadcrumb navigation
+-- partials/
|   +-- _header.html             # Site header
|   +-- _sidebar.html            # Navigation sidebar
|   +-- _footer.html             # Site footer
+-- errors/
    +-- 400.html
    +-- 403.html
    +-- 404.html
    +-- 500.html

apps/hr/templates/hr/
+-- employee_list.html           # Full page
+-- employee_detail.html
+-- employee_form.html
+-- partials/
    +-- _employee_table.html     # HTMX-swappable table
    +-- _employee_row.html       # Single table row
    +-- _employee_form.html      # HTMX-swappable form
    +-- _employee_card.html      # Card component
    +-- _department_filter.html  # Filter dropdown
```

**HTMX Partial Pattern:**
```python
# views/employee_views.py
class EmployeeListView(LoginRequiredMixin, View):
    def get(self, request):
        employees = get_employee_list(
            company_id=request.user.company_id,
            search=request.GET.get("search"),
        )
        paginator = Paginator(employees, 25)
        page = paginator.get_page(request.GET.get("page"))

        # Return partial for HTMX requests, full page otherwise
        if request.htmx:
            return render(request, "hr/partials/_employee_table.html", {
                "page_obj": page,
            })
        return render(request, "hr/employee_list.html", {
            "page_obj": page,
        })
```

---

### 11.5 Settings Management (Split Settings)

```
config/settings/
+-- __init__.py          # Empty or auto-detect environment
+-- base.py              # All shared settings
+-- local.py             # DEBUG=True, console email, etc.
+-- production.py        # DEBUG=False, security hardened
+-- test.py              # Fast test settings
```

```python
# config/settings/base.py
import environ
from pathlib import Path

env = environ.Env()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG", default=False)

INSTALLED_APPS = [
    # Django built-in
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    # Third-party
    "django_htmx",
    # Local apps
    "core",
    "apps.hr",
]

# Database
DATABASES = {
    "default": env.db("DATABASE_URL", default="postgres://localhost/integra"),
}

# Internationalization
LANGUAGE_CODE = "ar"
LANGUAGES = [
    ("ar", "العربية"),
    ("en", "English"),
]
USE_I18N = True
USE_L10N = True
```

```python
# config/settings/local.py
from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Django Debug Toolbar
INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405
INTERNAL_IPS = ["127.0.0.1"]

# Console email in development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
```

```python
# config/settings/test.py
from .base import *  # noqa: F403

# Use faster password hasher for tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Use in-memory SQLite for speed (optional; prefer PostgreSQL for accuracy)
# DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3"}}

# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()
```

---

### 11.6 Middleware Best Practices

```python
# config/settings/base.py
MIDDLEWARE = [
    # Security first
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",     # Static files
    # Session & Auth
    "django.contrib.sessions.middleware.SessionMiddleware",
    # Internationalization
    "django.middleware.locale.LocaleMiddleware",
    # Common
    "django.middleware.common.CommonMiddleware",
    # CSRF
    "django.middleware.csrf.CsrfViewMiddleware",
    # Auth
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Messages
    "django.contrib.messages.middleware.MessageMiddleware",
    # Security headers
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # HTMX
    "django_htmx.middleware.HtmxMiddleware",
    # INTEGRA custom
    "core.middleware.exception_middleware.IntegraExceptionMiddleware",
    "core.middleware.request_logging.RequestLoggingMiddleware",
    "core.middleware.arabic_middleware.ArabicContextMiddleware",
]
```

**Custom Arabic Context Middleware:**
```python
# core/middleware/arabic_middleware.py
class ArabicContextMiddleware:
    """Adds RTL direction and Arabic-specific context to every request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_template_response(self, request, response):
        if hasattr(response, "context_data") and response.context_data is not None:
            lang = getattr(request, "LANGUAGE_CODE", "ar")
            response.context_data["text_direction"] = "rtl" if lang == "ar" else "ltr"
            response.context_data["lang"] = lang
        return response
```

---

## 12. Performance

### 12.1 N+1 Query Prevention

**RULE:** Every queryset that will access related objects MUST use
`select_related()` or `prefetch_related()`.

| Relationship Type | Method | SQL |
|---|---|---|
| ForeignKey (forward) | `select_related` | JOIN |
| OneToOneField | `select_related` | JOIN |
| ManyToManyField | `prefetch_related` | Separate IN query |
| Reverse ForeignKey | `prefetch_related` | Separate IN query |

**EXAMPLE:**
```python
# WRONG -- N+1 problem (1 + N queries)
employees = Employee.objects.all()
for emp in employees:
    print(emp.department.name_ar)  # Each access = 1 query!

# CORRECT -- 1 query with JOIN
employees = Employee.objects.select_related("department").all()
for emp in employees:
    print(emp.department.name_ar)  # No additional query

# CORRECT -- ManyToMany
departments = Department.objects.prefetch_related("employees").all()
for dept in departments:
    print(dept.employees.count())  # Prefetched, no additional query

# ADVANCED -- filtered prefetch
from django.db.models import Prefetch

departments = Department.objects.prefetch_related(
    Prefetch(
        "employees",
        queryset=Employee.objects.filter(status__name="active"),
        to_attr="active_employees",
    )
)
```

**VERIFICATION:**
- Install `django-debug-toolbar` in development and check "SQL" panel.
- Maximum queries per page:
  - List page: <= 10 queries
  - Detail page: <= 5 queries
  - Dashboard: <= 15 queries
- Use `nplusone` library to auto-detect N+1 in tests:
  ```python
  # In test settings
  INSTALLED_APPS += ["nplusone.ext.django"]
  MIDDLEWARE.insert(0, "nplusone.ext.django.NPlusOneMiddleware")
  NPLUSONE_RAISE = True  # Fail tests on N+1
  ```

---

### 12.2 Caching Strategy

```
Layer 1: Template Fragment Caching (page-level)
Layer 2: View Caching (per-URL)
Layer 3: QuerySet Caching (data-level)
Layer 4: Database Query Cache (PostgreSQL level)
```

```python
# Template fragment caching
{% load cache %}
{% cache 600 department_stats request.user.company_id %}
    {% include "hr/partials/_department_stats.html" %}
{% endcache %}

# View-level caching (for read-only pages)
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # 15 minutes
def department_list(request):
    ...

# Low-level caching in selectors
from django.core.cache import cache

def get_department_choices(company_id: int) -> list[tuple[int, str]]:
    cache_key = f"dept_choices_{company_id}"
    choices = cache.get(cache_key)
    if choices is None:
        choices = list(
            Department.objects.filter(company_id=company_id)
            .values_list("id", "name_ar")
        )
        cache.set(cache_key, choices, timeout=3600)  # 1 hour
    return choices

# Cache invalidation in services
def create_department(*, data: DepartmentCreateDTO, created_by: User) -> Department:
    dept = Department.objects.create(**data.__dict__)
    cache.delete(f"dept_choices_{data.company_id}")  # Invalidate
    return dept
```

**Cache Configuration:**
```python
# config/settings/base.py
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://127.0.0.1:6379/0"),
        "KEY_PREFIX": "integra",
        "TIMEOUT": 3600,  # 1 hour default
    }
}
```

---

### 12.3 Database Query Optimization

```python
# Use .values() or .values_list() for lightweight queries
department_ids = Employee.objects.filter(
    status__name="active"
).values_list("department_id", flat=True).distinct()

# Use annotate instead of Python-side counting
from django.db.models import Count

departments = Department.objects.annotate(
    employee_count=Count("employees", filter=Q(employees__status__name="active"))
).order_by("-employee_count")

# Use Subquery for complex lookups
from django.db.models import Subquery, OuterRef

latest_audit = AuditLog.objects.filter(
    table_name="employees",
    record_id=OuterRef("pk"),
).order_by("-created_at").values("created_at")[:1]

employees = Employee.objects.annotate(
    last_updated_by_audit=Subquery(latest_audit)
)

# Use bulk operations
Employee.objects.filter(company_id=1).update(status_id=2)  # Single query
Employee.objects.bulk_create([Employee(...), Employee(...)])  # Single query
Employee.objects.bulk_update(employees, ["status_id"])       # Single query
```

---

### 12.4 Frontend Performance (HTMX + Tailwind)

| Technique | Implementation |
|-----------|---------------|
| **Lazy loading** | `hx-trigger="revealed"` on below-fold content |
| **Pagination** | Server-side with HTMX infinite scroll or page numbers |
| **Debounced search** | `hx-trigger="keyup changed delay:300ms"` |
| **Partial updates** | `hx-target="#employee-table"` replaces only the table |
| **Prefetching** | `hx-trigger="mouseenter"` on links to prefetch |
| **Static compression** | Whitenoise + Brotli/Gzip |
| **Tailwind purge** | Build step removes unused CSS classes |
| **Image optimization** | WebP format, lazy loading with `loading="lazy"` |

**HTMX Search Example:**
```html
<input
    type="search"
    name="search"
    placeholder="بحث بالاسم أو رقم الموظف..."
    hx-get="{% url 'hr:employee-list' %}"
    hx-trigger="keyup changed delay:300ms"
    hx-target="#employee-table"
    hx-indicator="#search-spinner"
    class="w-full px-4 py-2 border rounded-lg text-right"
    dir="rtl"
/>
<div id="search-spinner" class="htmx-indicator">
    {% include "components/_loading.html" %}
</div>
<div id="employee-table">
    {% include "hr/partials/_employee_table.html" %}
</div>
```

---

## 13. Zero-Bug Methodologies

### 13.1 IBM Cleanroom Software Engineering (Adapted)

**PRINCIPLE:** Defect prevention is more effective and cheaper than defect detection.

**Adapted for INTEGRA:**

| Cleanroom Concept | INTEGRA Implementation |
|---|---|
| **Formal specification** | Comprehensive docstrings with Args/Returns/Raises + type hints |
| **Correctness verification** | Service functions reviewed for logical correctness before testing |
| **Statistical testing** | Usage-based test scenarios reflecting real Arabic ERP workflows |
| **No developer debugging** | TDD: write test first, then code. Tests ARE the debugging tool |
| **Incremental development** | Session-based sprints delivering testable increments |

**The "No Debugging" Discipline:**
Instead of writing code then debugging, the developer:
1. Writes a precise specification (docstring with types).
2. Reasons about correctness (does the logic handle all cases?).
3. Writes tests encoding the expected behavior.
4. Writes the implementation to pass the tests.
5. If tests fail, the developer reads the code and reasons about the failure
   rather than using a debugger.

---

### 13.2 Zero-Bug Bounce Policy

**PRINCIPLE:** At any point in time, the known bug count should be zero.

**Implementation:**
1. **In-Sprint Bugs:** Any bug discovered during development of a feature must be
   fixed before the feature is considered done.
2. **Triage Rule:** When a bug is reported post-merge:
   - **Fix Now:** Degraded user experience with no workaround -> next commit.
   - **Fix This Sprint:** Degraded experience with workaround -> current sprint.
   - **Won't Fix:** Edge case with minimal impact -> document and close.
3. **No Bug Backlog:** We do not maintain a "bug backlog." Bugs are either fixed
   immediately or explicitly won't-fixed with documented rationale.

---

### 13.3 Static Analysis Tools

| Tool | What It Catches | Configuration |
|------|----------------|---------------|
| **ruff** | Linting + formatting (replaces flake8, isort, black, pyupgrade) | `pyproject.toml [tool.ruff]` |
| **mypy** | Type errors, missing annotations | `pyproject.toml [tool.mypy]` |
| **bandit** | Security vulnerabilities | `pyproject.toml [tool.bandit]` |
| **vulture** | Dead/unused code | CLI or pre-commit |
| **pip-audit** | Known CVEs in dependencies | CI pipeline |
| **djhtml** | Django template formatting | Pre-commit |
| **nplusone** | N+1 query detection in tests | Test settings |
| **django-migration-linter** | Unsafe migration operations | CI pipeline |

**Mypy Configuration (Strict from Day 1):**
```toml
# pyproject.toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
no_implicit_optional = true
check_untyped_defs = true

plugins = ["mypy_django_plugin.main"]

[tool.django-stubs]
django_settings_module = "config.settings.local"

[[tool.mypy.overrides]]
module = "*.migrations.*"
ignore_errors = true
```

**Ruff Configuration:**
```toml
# pyproject.toml
[tool.ruff]
target-version = "py312"
line-length = 99
src = ["apps", "core", "config"]

[tool.ruff.lint]
select = [
    "E",     # pycodestyle errors
    "W",     # pycodestyle warnings
    "F",     # pyflakes
    "I",     # isort
    "N",     # pep8-naming
    "UP",    # pyupgrade
    "B",     # flake8-bugbear
    "C4",    # flake8-comprehensions
    "SIM",   # flake8-simplify
    "S",     # flake8-bandit (security)
    "T20",   # flake8-print (no print statements)
    "D",     # pydocstyle (docstrings)
    "C901",  # mccabe complexity
    "RUF",   # ruff-specific rules
    "DJ",    # flake8-django
    "PTH",   # flake8-use-pathlib
    "ERA",   # eradicate (commented-out code)
]
ignore = [
    "D100",  # Missing module docstring (too noisy early on)
    "D104",  # Missing package docstring
]

[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.per-file-ignores]
"*/tests/*" = ["S101", "D"]    # Allow assert and skip docstrings in tests
"*/migrations/*" = ["E501", "D"]  # Auto-generated
```

---

### 13.4 Pre-Commit Hooks for Quality Enforcement

```yaml
# .pre-commit-config.yaml
repos:
  # Ruff: lint + format
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  # Mypy: type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.14.0
    hooks:
      - id: mypy
        additional_dependencies:
          - django-stubs
          - types-requests

  # Security: detect secrets
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets

  # Conventional commits
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v4.0.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]

  # Django template formatting
  - repo: https://github.com/rtts/djhtml
    rev: "3.0.7"
    hooks:
      - id: djhtml

  # General file checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-merge-conflict
      - id: check-added-large-files
        args: [--maxkb=500]
      - id: debug-statements
      - id: no-commit-to-branch
        args: [--branch, main]
```

---

### 13.5 Formal Verification (Simplified for Django)

Full formal verification is impractical for a web application, but we borrow key concepts:

| Concept | Practical Implementation |
|---|---|
| **Preconditions** | Type hints + defensive checks at function entry |
| **Postconditions** | Assertions after critical operations in tests |
| **Invariants** | Model `clean()` methods + DB constraints |
| **State machine verification** | Employee status transitions validated in service |
| **Property-based testing** | Use `hypothesis` for edge case discovery |

**Property-Based Testing Example:**
```python
from hypothesis import given, strategies as st
from hypothesis.extra.django import from_model

@given(
    name=st.text(min_size=1, max_size=200),
    code=st.from_regex(r"EMP-\d{4}", fullmatch=True),
)
def test_employee_creation_never_crashes(name, code):
    """No input combination should cause an unhandled exception."""
    form = EmployeeCreateForm(data={
        "name_ar": name,
        "employee_code": code,
        # ... other required fields
    })
    # Form should either be valid or have clean error messages
    if form.is_valid():
        assert form.cleaned_data["name_ar"]  # postcondition
    else:
        assert len(form.errors) > 0  # postcondition
```

---

## Appendix A: Pre-Commit Configuration

Complete setup commands:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install
pre-commit install --hook-type commit-msg

# Run on all files (first time)
pre-commit run --all-files

# Update hooks to latest versions
pre-commit autoupdate
```

---

## Appendix B: Quality Checklists

### B.1 New Feature Checklist

- [ ] Feature branch created from `main`
- [ ] Tests written FIRST (TDD)
- [ ] Service function created for business logic
- [ ] Selector function created for complex queries
- [ ] Form validation covers all inputs
- [ ] Model constraints mirror form validation
- [ ] Migration created and tested (forward + backward)
- [ ] HTMX partial works independently
- [ ] Arabic text displays correctly (RTL)
- [ ] Error states handled gracefully
- [ ] Structured logging added for key operations
- [ ] Documentation updated (docstrings, SESSION_LOG)
- [ ] All pre-commit hooks pass
- [ ] All tests pass with >= 85% coverage
- [ ] PR created with clear description

### B.2 Database Change Checklist

- [ ] Schema is in 3NF
- [ ] Foreign keys use `on_delete=PROTECT` (not CASCADE) for lookup tables
- [ ] Indexes added for commonly filtered fields
- [ ] Check constraints mirror application validation
- [ ] Data migration is separate from schema migration
- [ ] Migration is reversible
- [ ] Migration tested on copy of production data
- [ ] No breaking changes to existing data

### B.3 Security Release Checklist

- [ ] `python manage.py check --deploy` passes
- [ ] `pip-audit` shows no known CVEs
- [ ] `bandit -r apps/` shows no issues
- [ ] `detect-secrets scan` shows no secrets in code
- [ ] All passwords/tokens in environment variables
- [ ] HTTPS enforced
- [ ] HSTS enabled
- [ ] CSRF token in all forms
- [ ] Session cookies are secure and HTTP-only
- [ ] Rate limiting on authentication endpoints

---

## Sources & References

### Architecture & Best Practices
- [Django Best Practices 2025 -- Settings, Apps, and Structure](https://medium.com/write-a-catalyst/django-best-practices-2025-settings-apps-and-structure-9c96970c1a5b)
- [Scalable Django Architecture: Best Practices for 2025](https://python.plainenglish.io/scalable-django-project-architecture-best-practices-for-2025-6be2f9665f7e)
- [Clean Architecture in Django with OOP & SOLID](https://www.mindbowser.com/clean-architecture-django-guide/)
- [Django 2026 Roadmap](https://medium.com/@djangowiki/django-2026-roadmap-what-to-learn-what-to-skip-and-how-i-plan-to-teach-it-82eefe2aa5f0)
- [Django Configurations: Best Practices](https://djangostars.com/blog/configuring-django-settings-best-practices/)

### Service Layer & DDD
- [Python Design Patterns: Service Layer + Repository + Specification](https://craftedstack.com/blog/python/design-patterns-repository-service-layer-specification/)
- [Saving Django Legacy Projects Using DDD](https://betterprogramming.pub/saving-django-legacy-project-using-ddd-f1e709795291)
- [Repository and Unit of Work Patterns with Django -- Cosmic Python](https://www.cosmicpython.com/book/appendix_django.html)
- [A Practical Blueprint for DDD in Django](https://medium.com/@hamz.ghp/a-practical-blueprint-for-domain-driven-design-ddd-in-django-projects-2d36652b03b9)
- [Cosmic Django (Sep 2025)](https://brunodantas.github.io/blog/2025/09/12/cosmic-django/)

### Testing
- [TDD in Django: Best Practices for Modern Software](https://python.plainenglish.io/test-driven-development-tdd-in-django-best-practices-for-modern-software-iteration-f65106137efd)
- [Modern Test-Driven Development in Python](https://testdriven.io/blog/modern-tdd/)
- [Modern Test Pyramid Guide 2025](https://fullscale.io/blog/modern-test-pyramid-guide/)
- [Django Tests Cheatsheet 2025](https://medium.com/@jonathan.hoffman91/django-tests-cheatsheet-2025-4fae3d32c3c5)

### Security
- [Django Security -- Official Documentation](https://docs.djangoproject.com/en/6.0/topics/security/)
- [OWASP Django Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Django_Security_Cheat_Sheet.html)
- [Django Security in 2025](https://www.programmingworld.tech/blog/django-security-in-2025-how-to-protect-your-web-app-from-hackers)

### Error Handling & Logging
- [Django Error Handling Patterns -- Better Stack](https://betterstack.com/community/guides/scaling-python/error-handling-django/)
- [Structured Logging with Python and Django](https://morethanmonkeys.medium.com/structured-logging-with-python-and-django-from-log-soup-to-useful-events-a8de3003ac87)
- [6 Best Practices for Python Exception Handling](https://www.qodo.ai/blog/6-best-practices-for-python-exception-handling/)

### Performance
- [How to Avoid N+1 Queries in Django -- AppSignal](https://blog.appsignal.com/2025/07/09/how-to-avoid-nplus1-queries-in-django-python.html)
- [Advanced PostgreSQL Indexing Tips in Django](https://idego-group.com/blog/2022/10/20/advanced-postgresql-indexing-tips-in-django/)

### SOLID Principles
- [SOLID Design Principles in Python -- Real Python](https://realpython.com/solid-principles-python/)
- [Applying SOLID Principles in Django: Real-World Examples](https://www.linkedin.com/pulse/applying-solid-principles-django-real-world-examples-fa-alfard-uqhbf)

### Zero-Bug Methodology
- [Cleanroom Software Engineering for Zero-Defect Software -- IEEE](https://ieeexplore.ieee.org/document/346060/)
- [Cleanroom Software Engineering Reference -- CMU/SEI](https://resources.sei.cmu.edu/library/asset-view.cfm?assetid=12635)
- [Zero-Bug Software Development](https://medium.com/qualityfaster/the-zero-bug-policy-b0bd987be684)
- [0 Bugs Policy -- InfoQ](https://www.infoq.com/articles/0-bugs-policy/)

### HTMX + Tailwind
- [Django + HTMX + TailwindCSS Setup Guide 2025](https://blog.sparrow.so/comprehensive-guide-to-setting-up-a-django-project-with-htmx-and-tailwindcss-integration/)
- [Full-Stack Django with HTMX and Tailwind -- TestDriven.io](https://testdriven.io/courses/django-htmx/)

### Documentation & Git
- [C4 Model + ADR Integration](https://visual-c4.com/blog/c4-model-architecture-adr-integration)
- [Architecture Decision Records](https://adr.github.io/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Branching Strategy Guide -- DataCamp](https://www.datacamp.com/tutorial/git-branching-strategy-guide)

### Static Analysis & Quality Tools
- [Modern Python Code Quality: uv, ruff, and mypy](https://simone-carolini.medium.com/modern-python-code-quality-setup-uv-ruff-and-mypy-8038c6549dcc)
- [Effortless Code Quality: Pre-Commit Hooks Guide 2025](https://gatlenculp.medium.com/effortless-code-quality-the-ultimate-pre-commit-hooks-guide-for-2025-57ca501d9835)
- [Top 10 Python Code Analysis Tools 2026](https://www.jit.io/resources/appsec-tools/top-python-code-analysis-tools-to-improve-code-quality)
