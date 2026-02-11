# INTEGRA Web - Migration Project Plan

> **Version:** 1.0.0 | **Last Updated:** 2026-02-11
> **Migration:** PyQt5 Desktop → Django Web Application
> **Database:** PostgreSQL 16+ (preserved from original)

---

## Executive Summary

This plan migrates INTEGRA from a PyQt5 desktop application to a Django-based web application. The migration preserves the existing PostgreSQL database schema and all business logic while modernizing the UI to a responsive web interface with full Arabic/RTL support.

**Total Estimated Sessions:** 25-30 (each session = 1 Claude Code conversation)

---

## Phase Overview

```
Phase 0: Foundation (Sessions 1-3)          ██░░░░░░░░░░░░░░░░░░  Setup & Infrastructure
Phase 1: Core Models (Sessions 4-7)         ████░░░░░░░░░░░░░░░░  Database & Models
Phase 2: Auth & UI (Sessions 8-12)          ██████░░░░░░░░░░░░░░  Authentication & Base UI
Phase 3: Modules (Sessions 13-20)           ████████████░░░░░░░░  Business Modules
Phase 4: Advanced (Sessions 21-25)          ████████████████░░░░  Reports, API, Polish
Phase 5: Production (Sessions 26-28)        ████████████████████  Deploy & Go-Live
```

---

## Phase 0: Foundation & Infrastructure

### Session 1: Project Bootstrap
**Goal:** Django project initialized with production-grade configuration

| # | Task | Status | Files |
|---|------|--------|-------|
| 1.1 | Initialize Django project (`integra_web`) | 🔴 | `manage.py`, `integra_web/` |
| 1.2 | Configure `pyproject.toml` (dependencies, ruff, mypy) | 🔴 | `pyproject.toml` |
| 1.3 | Set up environment management (`django-environ`) | 🔴 | `.env.example`, `settings/` |
| 1.4 | Create settings split: `base.py`, `development.py`, `production.py` | 🔴 | `integra_web/settings/` |
| 1.5 | Configure PostgreSQL connection (reuse existing DB) | 🔴 | `settings/base.py` |
| 1.6 | Set up `pre-commit` hooks (ruff, mypy) | 🔴 | `.pre-commit-config.yaml` |
| 1.7 | Create initial GitHub Actions CI pipeline | 🔴 | `.github/workflows/ci.yml` |
| 1.8 | Set up `.gitignore` | 🔴 | `.gitignore` |

**Dependencies:** None (starting point)
**Deliverable:** `python manage.py runserver` works, CI passes

---

### Session 2: Core Infrastructure - Logging & Error Handling
**Goal:** Production-grade logging and error handling

| # | Task | Status | Files |
|---|------|--------|-------|
| 2.1 | Configure structured logging (loguru → Python logging + structlog) | 🔴 | `core/logging/` |
| 2.2 | Create `app_logger` and `audit_logger` equivalents | 🔴 | `core/logging/loggers.py` |
| 2.3 | Implement Django middleware for request logging | 🔴 | `core/middleware/logging.py` |
| 2.4 | Set up global exception handling middleware | 🔴 | `core/middleware/error_handling.py` |
| 2.5 | Create custom error pages (400, 403, 404, 500) | 🔴 | `templates/errors/` |
| 2.6 | Write tests for logging and error handling | 🔴 | `tests/unit/test_logging.py` |

**Dependencies:** Session 1 complete
**Deliverable:** All errors logged properly, custom error pages render

---

### Session 3: Core Infrastructure - Utilities & Base Classes
**Goal:** Shared utilities and base classes for all modules

| # | Task | Status | Files |
|---|------|--------|-------|
| 3.1 | Create base model mixin (audit fields: created_at, updated_at, created_by) | 🔴 | `core/models/mixins.py` |
| 3.2 | Create base service class with common patterns | 🔴 | `core/services/base.py` |
| 3.3 | Create base view mixins (permissions, pagination) | 🔴 | `core/views/mixins.py` |
| 3.4 | Create base form classes with Arabic validation messages | 🔴 | `core/forms/base.py` |
| 3.5 | Set up Django management commands structure | 🔴 | `core/management/` |
| 3.6 | Create health check endpoint | 🔴 | `core/views/health.py` |
| 3.7 | Write tests for all base classes | 🔴 | `tests/unit/test_core.py` |

**Dependencies:** Session 2 complete
**Deliverable:** All base classes tested and ready for module use

---

## Phase 1: Database & Models

### Session 4: Database Inspection & Model Generation
**Goal:** Generate Django models from existing PostgreSQL schema

| # | Task | Status | Files |
|---|------|--------|-------|
| 4.1 | Run `inspectdb` on existing database | 🔴 | (auto-generated) |
| 4.2 | Clean up and organize generated models | 🔴 | `employees/models.py`, etc. |
| 4.3 | Add proper field types, validators, and choices | 🔴 | All model files |
| 4.4 | Add `Meta` classes (ordering, indexes, verbose_name) | 🔴 | All model files |
| 4.5 | Create Django apps: `employees`, `companies`, `departments` | 🔴 | App directories |
| 4.6 | Create initial migration (fake-applied to existing DB) | 🔴 | `*/migrations/0001_initial.py` |
| 4.7 | Verify all relationships match existing FK constraints | 🔴 | Verification script |

**Dependencies:** Session 3 complete, access to existing DB
**Deliverable:** All models match existing DB schema, `python manage.py check` passes

---

### Session 5: Lookup Tables & Reference Data
**Goal:** Models for all reference/lookup tables

| # | Task | Status | Files |
|---|------|--------|-------|
| 5.1 | Create `companies` app with Company model | 🔴 | `companies/` |
| 5.2 | Create `departments` app with Department model | 🔴 | `departments/` |
| 5.3 | Create `lookups` app (job_titles, nationalities, banks, statuses) | 🔴 | `lookups/` |
| 5.4 | Create model managers with common querysets | 🔴 | `*/managers.py` |
| 5.5 | Create admin registrations for all models | 🔴 | `*/admin.py` |
| 5.6 | Write model tests (creation, validation, relationships) | 🔴 | `tests/unit/test_models.py` |

**Dependencies:** Session 4 complete
**Deliverable:** All reference tables modeled, admin shows data correctly

---

### Session 6: Employee Model - Complete
**Goal:** Full Employee model with all fields and relationships

| # | Task | Status | Files |
|---|------|--------|-------|
| 6.1 | Complete Employee model with ALL fields from existing schema | 🔴 | `employees/models.py` |
| 6.2 | Create Employee model manager (active, by_company, etc.) | 🔴 | `employees/managers.py` |
| 6.3 | Create Employee admin with search, filters, list_display | 🔴 | `employees/admin.py` |
| 6.4 | Create Employee serializer (for future API) | 🔴 | `employees/serializers.py` |
| 6.5 | Verify data integrity with existing database records | 🔴 | Verification script |
| 6.6 | Write comprehensive model tests | 🔴 | `tests/unit/test_employee_model.py` |

**Dependencies:** Session 5 complete
**Deliverable:** Employee model fully matches DB, reads existing data correctly

---

### Session 7: Data Migration & Verification
**Goal:** Ensure Django ORM reads existing data correctly

| # | Task | Status | Files |
|---|------|--------|-------|
| 7.1 | Create migration verification management command | 🔴 | `core/management/commands/verify_db.py` |
| 7.2 | Test all relationships (FK, cascades, indexes) | 🔴 | Verification tests |
| 7.3 | Create data integrity test suite | 🔴 | `tests/integration/test_data_integrity.py` |
| 7.4 | Document any schema differences or issues | 🔴 | `docs/SCHEMA_NOTES.md` |
| 7.5 | Create seed data fixtures for development | 🔴 | `fixtures/` |

**Dependencies:** Session 6 complete
**Deliverable:** 100% data integrity verified, dev fixtures ready

---

## Phase 2: Authentication & Base UI

### Session 8: Authentication System
**Goal:** User login, permissions, and session management

| # | Task | Status | Files |
|---|------|--------|-------|
| 8.1 | Configure Django auth with custom User model | 🔴 | `accounts/models.py` |
| 8.2 | Create login page (Arabic/English) | 🔴 | `templates/accounts/login.html` |
| 8.3 | Set up permission groups (Admin, Manager, Viewer) | 🔴 | `accounts/permissions.py` |
| 8.4 | Create password change/reset flow | 🔴 | `accounts/views.py` |
| 8.5 | Add session timeout (30 min inactivity) | 🔴 | `settings/base.py` |
| 8.6 | Write auth tests (login, logout, permissions) | 🔴 | `tests/integration/test_auth.py` |

**Dependencies:** Session 3 complete
**Deliverable:** Login works, permissions enforced, sessions managed

---

### Session 9: Base Template & Theme System
**Goal:** Responsive layout with RTL support and dark/light theme

| # | Task | Status | Files |
|---|------|--------|-------|
| 9.1 | Create base HTML template (RTL, Cairo font, meta tags) | 🔴 | `templates/base.html` |
| 9.2 | Set up Tailwind CSS with RTL plugin | 🔴 | `tailwind.config.js` |
| 9.3 | Create dark/light theme CSS variables | 🔴 | `static/css/themes.css` |
| 9.4 | Build responsive navigation (sidebar + topbar) | 🔴 | `templates/components/nav.html` |
| 9.5 | Create theme toggle (persisted in localStorage) | 🔴 | `static/js/theme.js` |
| 9.6 | Build footer and common layout components | 🔴 | `templates/components/` |

**Dependencies:** Session 8 complete (needs auth for nav)
**Deliverable:** Responsive layout renders, theme switching works

---

### Session 10: Reusable UI Components
**Goal:** Component library matching INTEGRA desktop quality

| # | Task | Status | Files |
|---|------|--------|-------|
| 10.1 | Create card component (stats, info, action) | 🔴 | `templates/components/card.html` |
| 10.2 | Create table component (sortable, filterable, paginated) | 🔴 | `templates/components/table.html` |
| 10.3 | Create form components (inputs, selects, date pickers) | 🔴 | `templates/components/forms/` |
| 10.4 | Create button components (primary, secondary, danger) | 🔴 | `templates/components/button.html` |
| 10.5 | Create modal/dialog component | 🔴 | `templates/components/modal.html` |
| 10.6 | Create toast/notification component | 🔴 | `templates/components/toast.html` |
| 10.7 | Create loading/spinner component | 🔴 | `templates/components/loading.html` |

**Dependencies:** Session 9 complete
**Deliverable:** All components render correctly in both themes and RTL/LTR

---

### Session 11: Dashboard (Launcher)
**Goal:** Main dashboard replacing the PyQt launcher window

| # | Task | Status | Files |
|---|------|--------|-------|
| 11.1 | Create dashboard view with module cards | 🔴 | `dashboard/views.py` |
| 11.2 | Create dashboard template with stats overview | 🔴 | `templates/dashboard/index.html` |
| 11.3 | Add quick stats (total employees, active, by company) | 🔴 | `dashboard/services.py` |
| 11.4 | Create module navigation cards (matching desktop icons) | 🔴 | `templates/dashboard/modules.html` |
| 11.5 | Add recent activity feed | 🔴 | `dashboard/widgets.py` |
| 11.6 | Write dashboard tests | 🔴 | `tests/integration/test_dashboard.py` |

**Dependencies:** Sessions 6, 10 complete
**Deliverable:** Dashboard shows live data, modules accessible

---

### Session 12: Arabic/i18n Setup
**Goal:** Full internationalization with Arabic as primary language

| # | Task | Status | Files |
|---|------|--------|-------|
| 12.1 | Configure Django i18n (LANGUAGES, LOCALE_PATHS) | 🔴 | `settings/base.py` |
| 12.2 | Extract all strings to translation files | 🔴 | `locale/ar/LC_MESSAGES/` |
| 12.3 | Translate all UI strings to Arabic | 🔴 | `django.po` |
| 12.4 | Add language switcher (AR/EN) | 🔴 | `templates/components/lang_switch.html` |
| 12.5 | Test RTL layout across all pages | 🔴 | Visual testing |
| 12.6 | Test number/date formatting for Arabic locale | 🔴 | `tests/unit/test_i18n.py` |

**Dependencies:** Session 9 complete
**Deliverable:** Full Arabic UI, RTL layout perfect, language switching works

---

## Phase 3: Business Modules

### Session 13-14: Mostahaqat Module - Employee List
**Goal:** Employee listing with search, filter, and pagination

| # | Task | Status | Files |
|---|------|--------|-------|
| 13.1 | Create EmployeeService (list, filter, search) | 🔴 | `employees/services.py` |
| 13.2 | Create EmployeeListView with filters | 🔴 | `employees/views.py` |
| 13.3 | Build employee list template (table + cards view) | 🔴 | `templates/employees/list.html` |
| 13.4 | Add search (name, number, company) | 🔴 | `employees/filters.py` |
| 13.5 | Add export to Excel/PDF | 🔴 | `employees/exports.py` |
| 14.1 | Create employee stats cards (total, active, by status) | 🔴 | `employees/stats.py` |
| 14.2 | Add bulk actions (activate, suspend) | 🔴 | `employees/views.py` |
| 14.3 | Write comprehensive view tests | 🔴 | `tests/integration/test_employee_views.py` |

**Dependencies:** Session 11 complete
**Deliverable:** Employee list fully functional with all filters

---

### Session 15-16: Mostahaqat Module - Employee Profile
**Goal:** Detailed employee profile view

| # | Task | Status | Files |
|---|------|--------|-------|
| 15.1 | Create EmployeeDetailView | 🔴 | `employees/views.py` |
| 15.2 | Build profile template (personal, job, financial info) | 🔴 | `templates/employees/profile.html` |
| 15.3 | Add tab navigation (info, documents, history) | 🔴 | `templates/employees/profile_tabs.html` |
| 16.1 | Create employee edit form | 🔴 | `employees/forms.py` |
| 16.2 | Build edit template with validation | 🔴 | `templates/employees/edit.html` |
| 16.3 | Add audit trail display (who changed what, when) | 🔴 | `employees/audit.py` |
| 16.4 | Write profile/edit tests | 🔴 | `tests/integration/test_employee_profile.py` |

**Dependencies:** Session 13-14 complete
**Deliverable:** Full employee CRUD with audit trail

---

### Session 17-18: Mostahaqat Module - Financial Calculations
**Goal:** Port benefit calculations from desktop app

| # | Task | Status | Files |
|---|------|--------|-------|
| 17.1 | Create BenefitCalculationService | 🔴 | `mostahaqat/services.py` |
| 17.2 | Port salary calculation logic | 🔴 | `mostahaqat/calculations.py` |
| 17.3 | Create calculation views | 🔴 | `mostahaqat/views.py` |
| 18.1 | Build calculation templates | 🔴 | `templates/mostahaqat/` |
| 18.2 | Add print/export capability | 🔴 | `mostahaqat/exports.py` |
| 18.3 | Write calculation tests with known values | 🔴 | `tests/unit/test_calculations.py` |

**Dependencies:** Session 15-16 complete
**Deliverable:** All calculations match desktop app results exactly

---

### Session 19-20: Additional Modules (Costing, Logistics, Custody, Insurance)
**Goal:** Scaffold remaining modules

| # | Task | Status | Files |
|---|------|--------|-------|
| 19.1 | Create Costing module scaffold | 🔴 | `costing/` |
| 19.2 | Create Logistics module scaffold | 🔴 | `logistics/` |
| 19.3 | Create Custody module scaffold | 🔴 | `custody/` |
| 20.1 | Create Insurance module scaffold | 🔴 | `insurance/` |
| 20.2 | Create module navigation and routing | 🔴 | Module URLs |
| 20.3 | Register modules in dashboard | 🔴 | `dashboard/` |

**Dependencies:** Session 11 complete (dashboard)
**Deliverable:** All 5 modules accessible from dashboard with basic CRUD

---

## Phase 4: Advanced Features

### Session 21-22: Reports & Analytics
**Goal:** Reporting engine with charts and exports

| # | Task | Status | Files |
|---|------|--------|-------|
| 21.1 | Create report engine base class | 🔴 | `reports/engine.py` |
| 21.2 | Build employee statistics reports | 🔴 | `reports/employee_reports.py` |
| 21.3 | Add Chart.js integration for visualizations | 🔴 | `static/js/charts.js` |
| 22.1 | Create PDF report generation (WeasyPrint) | 🔴 | `reports/pdf.py` |
| 22.2 | Create Excel export (openpyxl) | 🔴 | `reports/excel.py` |
| 22.3 | Build report scheduler (background tasks) | 🔴 | `reports/scheduler.py` |

**Dependencies:** Session 13-18 complete (needs data)
**Deliverable:** Reports generate correctly, export to PDF/Excel

---

### Session 23-24: REST API
**Goal:** API layer for future mobile app / integrations

| # | Task | Status | Files |
|---|------|--------|-------|
| 23.1 | Set up Django REST Framework | 🔴 | `settings/base.py` |
| 23.2 | Create API serializers for all models | 🔴 | `api/serializers.py` |
| 23.3 | Create API viewsets with permissions | 🔴 | `api/views.py` |
| 24.1 | Add API authentication (token-based) | 🔴 | `api/auth.py` |
| 24.2 | Create API documentation (drf-spectacular) | 🔴 | `api/schema.py` |
| 24.3 | Write API tests | 🔴 | `tests/integration/test_api.py` |

**Dependencies:** Session 13-18 complete
**Deliverable:** Full CRUD API with auth, docs at `/api/docs/`

---

### Session 25: Background Tasks & Notifications
**Goal:** Async tasks for heavy operations

| # | Task | Status | Files |
|---|------|--------|-------|
| 25.1 | Set up Celery with Redis broker | 🔴 | `celery.py`, `tasks/` |
| 25.2 | Create email notification system | 🔴 | `notifications/` |
| 25.3 | Create in-app notification system | 🔴 | `notifications/models.py` |
| 25.4 | Add database backup task (matching desktop sync) | 🔴 | `tasks/backup.py` |
| 25.5 | Write task tests | 🔴 | `tests/unit/test_tasks.py` |

**Dependencies:** Sessions 1-3 complete
**Deliverable:** Background tasks execute, notifications delivered

---

## Phase 5: Production & Deployment

### Session 26: Security Hardening
**Goal:** Production security audit and hardening

| # | Task | Status | Files |
|---|------|--------|-------|
| 26.1 | Security audit (OWASP Top 10) | 🔴 | Audit report |
| 26.2 | Configure CSP, HSTS, X-Frame headers | 🔴 | `settings/production.py` |
| 26.3 | Set up rate limiting | 🔴 | `core/middleware/rate_limit.py` |
| 26.4 | Run `pip-audit` and fix vulnerabilities | 🔴 | `pyproject.toml` |
| 26.5 | Penetration test critical flows | 🔴 | Test results |

**Dependencies:** All features complete
**Deliverable:** Security audit passes, no critical/high vulnerabilities

---

### Session 27: Performance Optimization
**Goal:** Meet all performance targets

| # | Task | Status | Files |
|---|------|--------|-------|
| 27.1 | Database query optimization (N+1, indexes) | 🔴 | Various |
| 27.2 | Set up Redis caching | 🔴 | `settings/base.py` |
| 27.3 | Configure static file serving (WhiteNoise) | 🔴 | `settings/production.py` |
| 27.4 | Add database connection pooling | 🔴 | `settings/production.py` |
| 27.5 | Load testing and benchmark | 🔴 | Test results |

**Dependencies:** All features complete
**Deliverable:** All pages meet performance targets

---

### Session 28: Deployment
**Goal:** Production deployment configuration

| # | Task | Status | Files |
|---|------|--------|-------|
| 28.1 | Create Docker configuration | 🔴 | `Dockerfile`, `docker-compose.yml` |
| 28.2 | Configure Gunicorn/Uvicorn | 🔴 | `gunicorn.conf.py` |
| 28.3 | Set up Nginx reverse proxy config | 🔴 | `nginx/` |
| 28.4 | Create deployment scripts | 🔴 | `scripts/deploy.sh` |
| 28.5 | Write deployment documentation | 🔴 | `docs/DEPLOYMENT.md` |
| 28.6 | Create monitoring setup (health checks, alerts) | 🔴 | `core/monitoring/` |

**Dependencies:** Sessions 26-27 complete
**Deliverable:** App deployable with one command, monitoring active

---

## Dependency Graph

```
Session 1 ──→ Session 2 ──→ Session 3 ──→ Session 4 ──→ Session 5
                                 │              │            │
                                 │              ▼            ▼
                                 │         Session 6 ──→ Session 7
                                 │              │
                                 ▼              ▼
                            Session 8 ──→ Session 9 ──→ Session 10
                                              │             │
                                              ▼             ▼
                                         Session 12    Session 11
                                                           │
                                              ┌────────────┤
                                              ▼            ▼
                                         Session 13-14  Session 19-20
                                              │
                                              ▼
                                         Session 15-16
                                              │
                                              ▼
                                         Session 17-18
                                              │
                                    ┌─────────┼─────────┐
                                    ▼         ▼         ▼
                               Session 21  Session 23  Session 25
                               Session 22  Session 24
                                    │         │
                                    ▼         ▼
                               Session 26 ──→ Session 27 ──→ Session 28
```

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Schema mismatch between desktop and web | Medium | High | Session 4: thorough `inspectdb` + manual verification |
| Business logic not fully ported | Medium | High | Session 17-18: test against known desktop results |
| RTL layout breaks on some pages | High | Medium | Session 12: dedicated testing session |
| Performance with large datasets | Medium | Medium | Session 27: load testing early |
| User resistance to web UI | Low | High | Match desktop UX as closely as possible |

---

## Success Criteria

1. **Functional Parity:** All 5 modules work identically to desktop version
2. **Data Integrity:** Zero data loss during migration
3. **Performance:** All pages load within target times
4. **Security:** Zero critical/high vulnerabilities
5. **Test Coverage:** Minimum 80% on services and models
6. **RTL Support:** Perfect Arabic layout on all pages
7. **Theme Support:** Dark/light modes work on all components
