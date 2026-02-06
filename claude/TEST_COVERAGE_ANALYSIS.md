# INTEGRA Test Coverage Analysis

**Date:** 2026-02-06
**Analyzed by:** Claude (Automated Analysis)
**Codebase:** ~526 Python files across `core/`, `ui/`, `modules/`

---

## Executive Summary

**The INTEGRA codebase currently has zero automated tests.** There are no test files, no test configuration (pytest.ini, conftest.py, etc.), no coverage tooling, and no CI/CD pipelines. The project has no testing dependencies in `requirements.txt`.

This document identifies the highest-impact areas where tests should be introduced and proposes a phased approach.

---

## Current State

| Item | Status |
|------|--------|
| Test files | None |
| Test framework (pytest/unittest) | Not installed |
| Coverage tool | Not configured |
| CI/CD pipeline | Not configured |
| conftest.py / fixtures | None |
| Mocking library | Not installed |

---

## Recommended Test Infrastructure Setup

### Dependencies to Add

```
# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0
pytest-qt>=4.2.0         # PyQt5 GUI testing
pytest-timeout>=2.2.0    # Prevent hanging tests
```

### Configuration Files Needed

1. **`pytest.ini`** or `[tool.pytest]` in `pyproject.toml`
2. **`conftest.py`** with shared fixtures (mock database, mock QApplication)
3. **`.coveragerc`** to exclude non-testable code (UI stylesheets, `__init__.py`, etc.)

### Suggested Directory Structure

```
tests/
├── conftest.py              # Shared fixtures
├── core/
│   ├── conftest.py          # Core-specific fixtures
│   ├── test_config.py
│   ├── test_database_queries.py
│   ├── test_logging.py
│   ├── test_threading.py
│   ├── test_sync.py
│   ├── test_validation.py
│   ├── test_security.py
│   ├── test_backup_manager.py
│   ├── test_sync_status.py
│   ├── test_formatters.py
│   └── test_time_intelligence.py
├── modules/
│   ├── conftest.py
│   ├── test_task_models.py
│   ├── test_task_repository.py
│   ├── test_employee_queries.py
│   └── test_calendar_models.py
└── ui/
    ├── conftest.py
    └── test_enterprise_table.py
```

---

## Priority Areas for Test Coverage

### Tier 1: Critical — Pure Logic, No External Dependencies

These are the highest-value, lowest-effort targets. They contain real business logic with zero external dependencies (no database, no PyQt5, no filesystem).

#### 1. Task Models (`modules/tasks/models/task_models.py`)

**Why:** Contains computed properties (`is_overdue`, `is_due_today`, `is_due_soon`, `checklist_progress`) and serialization logic (`to_dict`, `from_dict`, `to_json`, `from_json`, `from_row`). Bugs here silently corrupt data.

**What to test:**
- `is_overdue` with past/future/today dates
- `is_due_today` across timezone boundaries
- `is_due_soon` with varying thresholds
- `checklist_progress` with 0/partial/full completion
- Round-trip serialization: `Task → to_dict → from_dict → Task`
- `from_row()` with missing/null database columns
- `TaskStatus` / `TaskPriority` enum color mappings
- Bilingual label generation

**Estimated tests:** 25-35

---

#### 2. Validation Schemas (`core/validation/`)

**Why:** Pydantic models validate all employee data entering the system. Incorrect validation means either rejecting good data or accepting bad data.

**What to test:**
- Valid employee creation/update payloads
- Invalid phone number formats
- Invalid IBAN values
- Email format validation
- Salary constraints (must be > 0)
- Future date rejection
- Arabic error message generation
- Optional field handling (null vs. missing)
- Type coercion behavior (string → int)

**Estimated tests:** 20-30

---

#### 3. Sync Status (`core/sync/sync_status.py`)

**Why:** Pure dataclass state machine that determines sync outcomes. Incorrect state transitions could cause data loss.

**What to test:**
- State transitions: IDLE → SYNCING → SUCCESS/ERROR/PARTIAL
- `finish()` with all-success, all-fail, mixed results
- `add_result()` accumulation
- `get_summary()` text generation
- Duration calculation (started_at → finished_at)
- Edge case: finish() with no results

**Estimated tests:** 10-15

---

#### 4. Utility Formatters (`core/utils/`)

**Why:** Pure functions used throughout the UI. Formatting bugs are visible to end users.

**What to test:**
- `format_number()` with various locales
- `format_currency()` with large/small/negative values
- `format_percentage()` edge cases (0%, 100%, >100%)
- `format_file_size()` — bytes, KB, MB, GB boundaries
- `format_duration()` — seconds, minutes, hours, days
- `format_time_ago()` — just now, minutes, hours, days, months
- `format_date()` with Arabic/English locales
- `format_large_number()` — K, M, B suffixes
- `format_ordinal()` — 1st, 2nd, 3rd, etc.

**Estimated tests:** 30-40

---

#### 5. Time Intelligence (`core/time_intelligence/`)

**Why:** Arabic natural language date parsing with regex patterns. Regex-based parsers are notoriously fragile.

**What to test:**
- Arabic day names (السبت, الأحد, ...)
- Relative expressions ("بعد 3 أيام", "الأسبوع القادم")
- Range expressions ("من الاثنين للجمعة")
- Hijri ↔ Gregorian conversion accuracy
- Holiday detection for Egypt/Saudi Arabia/UAE
- Edge cases: leap years, month boundaries, year rollover
- `parse_to_range()` with various period expressions

**Estimated tests:** 25-35

---

### Tier 2: High Value — Requires Database Mocking

These modules interact with PostgreSQL but the logic is well-separated and can be tested by mocking `core.database` query functions.

#### 6. Database Query Functions (`core/database/queries/`)

**Why:** Every database operation flows through these functions. The error handling has a potential null-pointer bug: `conn.rollback()` is called without checking if `conn` is `None`.

**What to test:**
- `select_all()` — returns (columns, rows) on success, ([], []) on failure
- `select_one()` — returns row or None
- `insert_returning_id()` — returns int or None
- `update_returning_count()` / `delete_returning_count()` — returns count or -1
- Error path: connection is None → should not crash on rollback
- Error path: query execution fails → proper rollback and return value
- Parameter passing (SQL injection prevention via parameterized queries)

**Bug found:** Error handlers call `conn.rollback()` without null-checking `conn`. If `get_connection()` returns `None`, the error handler itself will crash.

**Estimated tests:** 15-20

---

#### 7. Task Repository (`modules/tasks/repository/task_repository.py`)

**Why:** 30+ public methods handling all task CRUD operations, filtering, and relationship management (checklists, attachments, comments). This is the data backbone of the tasks module.

**What to test:**
- `get_all()` with various filter combinations (status, priority, category, search)
- `create()` — proper SQL generation and return value
- `update()` — timestamp updates
- `change_status()` / `change_priority()` — specific field updates
- `get_due_today()` / `get_overdue()` — date-based queries
- Checklist operations: add, toggle, delete
- Attachment operations: add, delete
- Comment operations: add, delete
- `get_statistics()` — aggregate computation
- Singleton pattern correctness

**Estimated tests:** 30-40

---

#### 8. Employee Queries (`modules/mostahaqat/employees/queries/`)

**Why:** Multi-table JOIN queries that power the main employee list. Wrong joins silently show wrong data.

**What to test:**
- `get_all_employees()` — returns correct column/row structure
- `get_employees_count()` / `get_active_employees_count()` — aggregation accuracy
- `get_nationalities_count()` / `get_departments_count()` / `get_jobs_count()` — distinct counts
- Error handling when database is unavailable

**Estimated tests:** 10-15

---

#### 9. Backup Manager (`core/sync/backup_manager.py`)

**Why:** Manages database backup files. Incorrect parsing or sorting means restoring the wrong backup.

**What to test:**
- `generate_backup_path()` — correct filename format
- `list_backups()` — sorted newest-first
- `get_latest_backup()` — returns correct file
- BackupInfo parsing — timestamp extraction from filename
- `age_days` calculation
- `formatted_size` — KB/MB conversion
- Handling of `_migrated` suffix files
- Empty backup directory behavior

**Estimated tests:** 10-15

---

### Tier 3: Medium Value — Requires PyQt5 Mocking or pytest-qt

These test areas require a QApplication instance and potentially pytest-qt for signal/slot testing.

#### 10. Threading System (`core/threading/`)

**Why:** Background task execution. Bugs here cause UI freezes or silent task failures.

**What to test:**
- `Worker` execution and signal emission (finished, error, progress)
- `Worker` cancellation (cooperative flag-based)
- `run_in_background()` — convenience function
- `TaskManager` — submit, cancel, cancel_all
- `TaskManager.get_stats()` — active/completed/error counts
- `all_tasks_completed` signal emission
- Thread safety of singleton `get_task_manager()`

**Estimated tests:** 15-20

---

#### 11. Error Handling (`core/error_handling/`)

**Why:** The global exception handler prevents silent crashes. If it fails, errors go unnoticed.

**What to test:**
- `install_exception_handler()` sets `sys.excepthook`
- KeyboardInterrupt passes through
- Logger availability fallback (missing logger → print)
- Signal emission to main thread
- Exception types are correctly captured

**Estimated tests:** 8-12

---

#### 12. Enterprise Table Filtering (`ui/components/tables/enterprise/`)

**Why:** The `EnterpriseFilterProxy.filterAcceptsRow()` method implements multi-column filtering logic used across the entire application.

**What to test:**
- Single-column text filter
- Multi-column filter (AND logic)
- Case sensitivity
- Empty filter (show all)
- Column visibility toggle
- Sort ordering (ascending/descending)
- Row selection after filtering
- `get_selected_rows()` returns correct data

**Estimated tests:** 15-20

---

### Tier 4: Important but Complex — Integration/System Tests

#### 13. Security — Encryption (`core/security/encryption.py`)

**What to test:**
- Encrypt/decrypt round-trip
- Key generation via PBKDF2
- Graceful degradation when `cryptography` library is missing
- Graceful degradation when `keyring` is unavailable
- File encryption/decryption
- `hash_password()` / `verify_password()` correctness

#### 14. Security — RBAC (`core/security/rbac.py`)

**What to test:**
- Permission checks for each role
- `require_permission` decorator blocks unauthorized calls
- Role → permission mapping completeness
- Audit logging on permission checks

#### 15. Sync System (`core/sync/sync_manager.py`)

**What to test:**
- Backward compatibility (v2 mode → v3 sync_type mapping)
- Startup sync orchestration (git pull → db restore)
- Shutdown sync orchestration (db backup → git push)
- Progress signal emission
- Error handling during partial failures

#### 16. Auto-Save / Recovery (`core/recovery/`)

**What to test:**
- Periodic save trigger
- Recovery file creation/deletion
- Recovery data listing and age-based cleanup
- Handler registration and invocation

---

## Bugs / Issues Found During Analysis

| # | Severity | Location | Description |
|---|----------|----------|-------------|
| 1 | **High** | `core/database/queries/*.py` | `conn.rollback()` called without null-checking `conn`. If `get_connection()` returns `None`, the error handler crashes instead of returning gracefully. |
| 2 | Medium | `core/database/queries/*.py` | Error logging uses `print()` instead of `app_logger`. Errors may be lost in production. |
| 3 | Low | `core/database/queries/*.py` | Return value inconsistency: some functions return `bool`, others return `int` or `-1` for errors. |

---

## Estimated Effort Summary

| Tier | Area | Estimated Test Count | Complexity |
|------|------|---------------------|------------|
| 1 | Pure logic (models, validation, utils, time) | 110-155 | Low |
| 2 | Database-mocked (queries, repositories, backup) | 65-90 | Medium |
| 3 | PyQt5-mocked (threading, error handling, tables) | 38-52 | Medium-High |
| 4 | Integration (security, sync, recovery) | 30-45 | High |
| **Total** | | **~243-342 tests** | |

---

## Recommended Implementation Order

1. **Set up test infrastructure** — Install pytest, create `tests/` directory, write `conftest.py`
2. **Tier 1 tests** — Pure logic, no mocking needed, immediate value
3. **Fix the database null-check bug** — Found during analysis
4. **Tier 2 tests** — Add database mocking fixtures, test repositories
5. **Tier 3 tests** — Add pytest-qt, test UI logic
6. **Tier 4 tests** — Integration tests for complex subsystems
7. **CI/CD** — Add GitHub Actions workflow to run tests on every push
