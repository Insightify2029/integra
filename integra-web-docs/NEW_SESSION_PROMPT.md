# INTEGRA Web — Session Initialization

## Context

I'm migrating **INTEGRA** from a PyQt5 desktop app to a Django web application.
The original desktop repo is at: `github.com/Insightify2029/integra`

This is the new **`integra-web`** repo — currently empty. I need you to set it up completely.

---

## Step 1: Create Project Documentation (6 files)

Create these files with FULL content (not stubs):

### 1. `CLAUDE.md` (root) — AI Assistant Master Guide
- Project overview: INTEGRA Web = Django 5.x + HTMX + Tailwind CSS + PostgreSQL 16+
- Arabic primary language (RTL), Cairo font, English fallback
- Python 3.11+, Author: Mohamed
- Tech stack table: Django, HTMX, Tailwind, Ruff, mypy+django-stubs, pytest, Celery+Redis, structlog
- Target project structure (Django apps: core, accounts, employees, companies, departments, lookups, mostahaqat, costing, logistics, custody, insurance, dashboard, reports, notifications)
- 13 mandatory rules carried from desktop (date arithmetic with timedelta, SQL injection prevention via ORM, no bare except, no print() use structlog, theme support with Tailwind dark:, Arabic/RTL with gettext_lazy, type hints mandatory, division by zero guards, query optimization with select_related, transactions for multi-step ops, testing requirements 80%, documentation updates every session)
- Database schema: employees, companies, departments, job_titles, nationalities, banks, employee_statuses (with FK relationships)
- 5 modules: mostahaqat(#2563eb), costing(#10b981), logistics(#f59e0b), custody(#8b5cf6), insurance(#ef4444)
- Import patterns, commands reference, git workflow
- CRITICAL: every session must start by reading PRE_SESSION_CHECKLIST.md and end by updating SESSION_TRACKER.md + PROJECT_PLAN.md

### 2. `docs/QUALITY_STANDARDS.md` — Engineering Standards (10 sections)
1. Architecture: 5-layer separation (Presentation → API → Service → Data Access → Infrastructure), SOLID, DRY, KISS
2. Code quality: Ruff config (target py311, line-length 120, select E/W/F/I/B/C4/UP/S/T20/SIM/DJ), mypy strict with django-stubs
3. Naming: files=snake_case, classes=PascalCase, functions=snake_case, constants=UPPER_SNAKE, URLs=kebab-case, CSS=kebab-case, JS=camelCase
4. Function standards: max 30 lines, max 5 params, max 15 class methods, max 400 lines per file, max cyclomatic complexity 10
5. Django/Frappe conventions: Model standards (audit fields on every model, gettext_lazy, PROTECT for FK, IntegerChoices for status, explicit db_table, composite indexes), View standards (LoginRequiredMixin + PermissionRequiredMixin always, thin views ≤20 lines), Service Layer pattern, URL patterns
6. Database: never edit applied migrations, select_related/prefetch_related, transactions for atomic ops, parameterized queries only
7. Security: CSRF on all forms, django-environ for secrets, ORM over raw SQL, pip-audit in CI, hmac.compare_digest for sensitive comparison
8. Testing: pytest+pytest-django, 80% coverage on services/models, factory_boy for test data, test naming: test_what_condition_expected
9. Performance targets: list views <200ms, detail <100ms, forms <300ms, reports <2s, max 10 DB queries per page
10. Arabic/RTL: Cairo font, gettext_lazy for all strings, logical CSS properties (ms-/me- not ml-/mr-), dir="rtl"

### 3. `docs/PROJECT_PLAN.md` — 28-Session Migration Roadmap
- **Phase 0 (Sessions 1-3):** Foundation — Django bootstrap, logging/error handling, base classes/mixins
- **Phase 1 (Sessions 4-7):** Core Models — inspectdb from existing DB, lookup tables, Employee model, data verification
- **Phase 2 (Sessions 8-12):** Auth & UI — authentication, base template+Tailwind+RTL, UI components, dashboard, i18n
- **Phase 3 (Sessions 13-20):** Business Modules — employee list, profile, financial calculations, other 4 modules
- **Phase 4 (Sessions 21-25):** Advanced — reports/charts, REST API (DRF), Celery background tasks
- **Phase 5 (Sessions 26-28):** Production — security hardening, performance optimization, Docker deployment
- Include dependency graph between sessions
- Each session has numbered tasks with status (🔴), files, and deliverables

### 4. `docs/SESSION_TRACKER.md` — Progress Tracking
- Current status table (phase, session, progress %)
- Phase progress bars
- Session log template (completed tasks, issues, decisions, next session, files created, tests)
- Blockers & open questions table
- Key metrics history table (tests, coverage, lint errors, type errors)
- Instructions for how to update at start/end of session

### 5. `docs/ARCHITECTURE_DECISIONS.md` — 10 ADRs
- ADR-001: Django over Frappe (flexibility, existing DB compatibility, ecosystem)
- ADR-002: Django Templates + HTMX over SPA/React (single codebase, faster dev, no build step)
- ADR-003: Tailwind CSS with RTL plugin (dark: variant, utility-first, small bundle)
- ADR-004: Ruff for linting+formatting (replaces Black+isort+Flake8, 10-100x faster, Rust-based)
- ADR-005: Keep existing PostgreSQL schema (zero data risk, inspectdb, fake migrations)
- ADR-006: Service Layer pattern (testable, reusable, thin views)
- ADR-007: pytest over Django TestCase (simpler syntax, better fixtures, plugins)
- ADR-008: Celery + Redis for background tasks (industry standard, periodic tasks, monitoring)
- ADR-009: structlog for logging (structured JSON in prod, colored console in dev, context binding)
- ADR-010: HTMX for dynamic UI (HTML-over-the-wire, no build step, 14KB, progressive enhancement)
- Each ADR: Context, Decision, Rationale (with comparison table), Consequences, Alternatives Rejected

### 6. `docs/PRE_SESSION_CHECKLIST.md` — Session Protocol
- Start: read SESSION_TRACKER → read PROJECT_PLAN → git status → manage.py check → pytest → present tasks
- End: ruff check → mypy → pytest → update SESSION_TRACKER → update PROJECT_PLAN → commit+push → summary
- Quick reference card (visual flow)
- Emergency recovery steps

---

## Step 2: After Creating Documents

- Commit all files with a clear message
- Push to main branch
- Then tell me "Ready to start Session 1?" — but do NOT start Session 1 yet, wait for my confirmation

---

## Key Architecture Decisions Summary

| Choice | Decision | Why |
|--------|----------|-----|
| Framework | Django 5.x | Flexibility, existing DB, massive ecosystem |
| Frontend | Django Templates + HTMX | Single codebase, no build step, fast dev |
| CSS | Tailwind + RTL plugin | Dark mode, RTL support, utility-first |
| Tooling | Ruff + mypy + pytest | Fast, modern, strict |
| Database | Keep existing PostgreSQL | Zero migration risk |
| Business Logic | Service Layer pattern | Testable, reusable, clean |
| Background | Celery + Redis | Industry standard |
| Logging | structlog | Structured, context-aware |
