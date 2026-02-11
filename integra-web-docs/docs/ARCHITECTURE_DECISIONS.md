# INTEGRA Web - Architecture Decision Records (ADRs)

> **Purpose:** Document all significant technical decisions with context and rationale.
> **Rule:** Every non-trivial technical choice MUST be recorded here before implementation.

---

## ADR Index

| # | Decision | Status | Date |
|---|----------|--------|------|
| ADR-001 | Use Django over Frappe Framework | ✅ Accepted | 2026-02-11 |
| ADR-002 | Use Django Templates over SPA (React/Vue) | ✅ Accepted | 2026-02-11 |
| ADR-003 | Use Tailwind CSS for styling | ✅ Accepted | 2026-02-11 |
| ADR-004 | Use Ruff for linting and formatting | ✅ Accepted | 2026-02-11 |
| ADR-005 | Keep existing PostgreSQL schema | ✅ Accepted | 2026-02-11 |
| ADR-006 | Service Layer pattern for business logic | ✅ Accepted | 2026-02-11 |
| ADR-007 | Use pytest over Django's TestCase | ✅ Accepted | 2026-02-11 |
| ADR-008 | Use Celery for background tasks | ✅ Accepted | 2026-02-11 |
| ADR-009 | Use structlog for structured logging | ✅ Accepted | 2026-02-11 |
| ADR-010 | Use HTMX for dynamic interactions | ✅ Accepted | 2026-02-11 |

---

## ADR-001: Use Django over Frappe Framework

**Date:** 2026-02-11
**Status:** ✅ Accepted
**Deciders:** Project team

### Context

We are migrating INTEGRA from a PyQt5 desktop app to a web application. Two main frameworks were considered:

1. **Frappe Framework** — Full-stack web framework with built-in ERP features
2. **Django** — Mature, general-purpose Python web framework

### Decision

**Use Django** as the web framework.

### Rationale

| Criteria | Django | Frappe |
|----------|--------|--------|
| **Learning curve** | Moderate, well-documented | Steep, opinionated conventions |
| **Flexibility** | Full control over architecture | Constrained by DocType patterns |
| **Ecosystem** | Massive (20,000+ packages) | Limited to Frappe/ERPNext ecosystem |
| **Database control** | Full ORM + raw SQL when needed | Abstracted behind DocTypes |
| **Community & Hiring** | #1 Python web framework | Niche community |
| **Arabic/RTL** | django-i18n + manual RTL | Built-in but limited |
| **Existing DB** | `inspectdb` maps existing schema | Would need DocType recreation |
| **Performance** | Predictable, well-understood | Overhead from metadata layer |
| **Customization** | Unlimited | Limited by framework patterns |

**Key factors:**
1. We have an existing PostgreSQL schema that Django can adopt directly via `inspectdb`
2. Frappe's DocType system would require re-creating our entire data model in its format
3. Django's flexibility allows us to match our desktop app's exact behavior
4. The team has more Python experience than Frappe-specific knowledge

### Consequences

- **Positive:** Full control, easier migration from existing DB, vast ecosystem
- **Negative:** Must build admin/CRUD manually (no auto-generation like Frappe)
- **Mitigation:** Use Django admin for quick management, build custom views for user-facing UI

### Alternatives Rejected

- **Frappe:** Too opinionated, would require schema recreation
- **FastAPI:** Better for API-only; we need server-rendered pages for our use case
- **Flask:** Too minimal; would need to assemble everything manually

---

## ADR-002: Use Django Templates over SPA (React/Vue)

**Date:** 2026-02-11
**Status:** ✅ Accepted

### Context

Frontend architecture decision: server-rendered HTML (Django Templates) vs. Single Page Application (React/Vue).

### Decision

**Use Django Templates** with HTMX for dynamic interactions.

### Rationale

| Criteria | Django Templates + HTMX | React/Vue SPA |
|----------|------------------------|---------------|
| **Complexity** | Low — single codebase | High — two codebases (API + frontend) |
| **Development speed** | Fast — no build step | Slower — needs API layer first |
| **SEO** | Built-in | Needs SSR/SSG |
| **RTL support** | Standard CSS | Framework-specific solutions |
| **Django integration** | Native | Requires DRF API |
| **Team skills** | Python-focused | Needs JS expertise |
| **Deployment** | Simple — one server | Complex — separate deploys |
| **Performance** | Fast initial load | Better for heavy interactions |

**Key factors:**
1. INTEGRA is a business management tool, not a consumer app — SEO and initial load matter more than SPA-style transitions
2. HTMX gives us dynamic behavior (live search, inline edits, partial updates) without the SPA complexity
3. Single codebase = faster development, simpler deployment
4. Team is Python-first; no need to introduce a separate JS framework

### Consequences

- **Positive:** Faster development, simpler deployment, less infrastructure
- **Negative:** Less interactive than a full SPA
- **Mitigation:** HTMX handles 90% of dynamic needs; use vanilla JS for the remaining 10%

---

## ADR-003: Use Tailwind CSS for Styling

**Date:** 2026-02-11
**Status:** ✅ Accepted

### Context

Need a CSS framework that supports RTL, dark/light themes, and responsive design.

### Decision

**Use Tailwind CSS** with the official RTL plugin (`tailwindcss-rtl`).

### Rationale

1. **RTL support:** `tailwindcss-rtl` plugin provides `ms-`, `me-`, `ps-`, `pe-` utilities that automatically flip for RTL
2. **Dark mode:** Built-in `dark:` variant via `class` strategy
3. **Customization:** Utility-first approach matches our theme variable system
4. **File size:** PurgeCSS eliminates unused styles (tiny production CSS)
5. **Component patterns:** Works excellently with Django template components

### Alternatives Rejected

- **Bootstrap:** Good RTL support but heavier, less customizable
- **Custom CSS:** Too time-consuming, harder to maintain consistency

---

## ADR-004: Use Ruff for Linting and Formatting

**Date:** 2026-02-11
**Status:** ✅ Accepted

### Context

Need consistent code quality tooling. Previously used multiple tools (Black, isort, Flake8, pylint).

### Decision

**Use Ruff** as the single tool for both linting and formatting.

### Rationale

1. **Speed:** 10-100x faster than Flake8/pylint (written in Rust)
2. **Unified:** Replaces Black + isort + Flake8 + pylint + pyupgrade + bandit + pydocstyle
3. **Configuration:** Single `[tool.ruff]` section in `pyproject.toml`
4. **Pre-commit:** Excellent pre-commit integration
5. **Active development:** Rapid feature addition, strong community adoption
6. **Django rules:** Built-in `DJ` rule set for Django-specific checks

### Consequences

- **Positive:** One tool, fast, comprehensive
- **Negative:** Relatively newer than established tools
- **Mitigation:** Ruff is now the most popular Python linter on PyPI

---

## ADR-005: Keep Existing PostgreSQL Schema

**Date:** 2026-02-11
**Status:** ✅ Accepted

### Context

INTEGRA desktop has an existing PostgreSQL database with employee data. We need to decide whether to keep the schema or redesign it.

### Decision

**Keep the existing schema** and use Django's `inspectdb` to generate models from it.

### Rationale

1. **Zero data migration risk:** No need to transform or move data
2. **Parallel operation:** Desktop and web can share the same database during transition
3. **Speed:** No time spent on schema redesign and data migration
4. **Validation:** Existing data validates the schema design

### Strategy

```bash
# Step 1: Generate models from existing DB
python manage.py inspectdb > models_raw.py

# Step 2: Clean up and distribute to apps
# Step 3: Create initial migration
python manage.py makemigrations

# Step 4: Fake-apply (DB already exists)
python manage.py migrate --fake
```

### Consequences

- **Positive:** Zero downtime, zero data risk, fast migration
- **Negative:** May inherit suboptimal schema decisions
- **Mitigation:** Document issues in `SCHEMA_NOTES.md`, plan improvements as separate migrations later

---

## ADR-006: Service Layer Pattern for Business Logic

**Date:** 2026-02-11
**Status:** ✅ Accepted

### Context

Need to organize business logic. Common Django patterns: fat models, fat views, or service layer.

### Decision

**Use a dedicated Service Layer** — classes in `<app>/services.py` that contain all business logic.

### Rationale

```
Views (thin)  →  Services (business logic)  →  Models (data access)
     ↑                    ↑                          ↑
  HTTP stuff         Domain rules              ORM queries
```

1. **Testability:** Services can be unit-tested without HTTP/views
2. **Reusability:** Same service used by views, API, management commands
3. **Clarity:** Clear separation of concerns
4. **Consistency:** Matches the pattern used in INTEGRA desktop's business logic layer

### Rules

- Views: max 20 lines, only HTTP handling
- Services: all business logic, validation, transaction management
- Models: data definition, simple properties, managers for queryset methods

---

## ADR-007: Use pytest over Django's TestCase

**Date:** 2026-02-11
**Status:** ✅ Accepted

### Context

Django ships with its own test framework (`unittest.TestCase`), but `pytest` is the de facto standard for Python testing.

### Decision

**Use pytest** with `pytest-django` plugin.

### Rationale

1. **Simpler syntax:** Plain functions and `assert` instead of `self.assertEqual()`
2. **Fixtures:** Powerful fixture system with dependency injection
3. **Plugins:** Rich ecosystem (pytest-cov, pytest-xdist for parallel, factory_boy)
4. **Output:** Better test failure output
5. **Parametrize:** Easy test parameterization for multiple inputs

---

## ADR-008: Use Celery for Background Tasks

**Date:** 2026-02-11
**Status:** ✅ Accepted

### Context

Need background task processing for: database backups, report generation, email sending, data exports.

### Decision

**Use Celery** with Redis as the message broker.

### Rationale

1. **Industry standard** for Django async tasks
2. **Reliable:** Built-in retry, error handling, dead letter queues
3. **Periodic tasks:** Celery Beat for scheduled tasks (replaces desktop's QTimer/scheduler)
4. **Monitoring:** Flower dashboard for task monitoring
5. **Scalable:** Can add workers as needed

### Alternatives Rejected

- **Django-Q2:** Simpler but less mature
- **Huey:** Lighter but fewer features
- **RQ (Redis Queue):** Simpler but no periodic tasks

---

## ADR-009: Use structlog for Structured Logging

**Date:** 2026-02-11
**Status:** ✅ Accepted

### Context

INTEGRA desktop uses `loguru`. Need to decide on web app logging.

### Decision

**Use structlog** with Python's standard `logging` module.

### Rationale

1. **Structured output:** JSON logs for production, colored console for development
2. **Django integration:** Works with Django's logging configuration
3. **Context binding:** Add request_id, user_id automatically to all log entries
4. **Performance:** Lazy evaluation, no overhead when log level disabled
5. **Standard library compatible:** Works alongside Django's built-in logging

### Migration from loguru

```python
# Desktop (loguru)
from loguru import logger
logger.info("Employee updated", employee_id=123)

# Web (structlog)
import structlog
logger = structlog.get_logger()
logger.info("employee_updated", employee_id=123)
```

---

## ADR-010: Use HTMX for Dynamic Interactions

**Date:** 2026-02-11
**Status:** ✅ Accepted

### Context

Need dynamic UI behavior (live search, inline edits, modal loading) without a full SPA framework.

### Decision

**Use HTMX** for all dynamic interactions.

### Rationale

1. **HTML-over-the-wire:** Server renders HTML, HTMX swaps it into the DOM
2. **No build step:** Single `<script>` tag, no npm/webpack
3. **Django-friendly:** Works perfectly with Django templates and views
4. **Progressive enhancement:** Works without JS (forms still submit normally)
5. **Small:** ~14KB gzipped

### Use Cases

```html
<!-- Live search -->
<input type="search"
       hx-get="/employees/search/"
       hx-trigger="keyup changed delay:300ms"
       hx-target="#results">

<!-- Inline edit -->
<button hx-get="/employees/5/edit-inline/"
        hx-target="#employee-5"
        hx-swap="outerHTML">
    تعديل
</button>

<!-- Delete with confirmation -->
<button hx-delete="/employees/5/"
        hx-confirm="هل أنت متأكد من الحذف؟"
        hx-target="#employee-5"
        hx-swap="outerHTML swap:1s">
    حذف
</button>
```

---

## Template for New ADRs

```markdown
## ADR-XXX: [Title]

**Date:** YYYY-MM-DD
**Status:** 🟡 Proposed / ✅ Accepted / ❌ Rejected / 🔄 Superseded by ADR-XXX

### Context
What is the issue? What forces are at play?

### Decision
What is the change that we're making?

### Rationale
Why is this the best option? Include comparison table if multiple options.

### Consequences
- **Positive:** Benefits
- **Negative:** Drawbacks
- **Mitigation:** How we handle the drawbacks

### Alternatives Rejected
- Option and why rejected
```
