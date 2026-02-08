# INTEGRA Comprehensive Audit Program
# برنامج التدقيق والمراجعة الشامل

**Version:** 1.0
**Date:** 8 February 2026
**Scope:** Full system audit across 10 dimensions
**Codebase:** 528 Python files | ~97,000 lines of code

---

## Overview / نظرة عامة

This program defines a **10-phase audit system** modeled after enterprise ERP quality standards
(SAP, Oracle, Odoo). Each phase is independent and produces a scored report.

```
Phase 1: Code Quality ──→ Phase 2: Architecture ──→ Phase 3: Database
    │                          │                          │
Phase 4: Performance ──→ Phase 5: Security ──→ Phase 6: Thread Safety
    │                          │                          │
Phase 7: UI/UX ──→ Phase 8: Testing ──→ Phase 9: Dead Code ──→ Phase 10: Final Score
```

**Target:** Zero errors, maximum speed, bulletproof architecture.

---

## Scoring System / نظام التقييم

Each phase scores 0-100. Final grade is weighted average:

| Phase | Weight | Description |
|-------|--------|-------------|
| 1. Code Quality | 15% | Clean, typed, documented code |
| 2. Architecture | 15% | Module separation, patterns, coupling |
| 3. Database | 15% | Schema, queries, performance, safety |
| 4. Performance | 15% | Speed, memory, startup time |
| 5. Security | 10% | OWASP, secrets, injection prevention |
| 6. Thread Safety | 10% | Locks, race conditions, deadlocks |
| 7. UI/UX | 8% | Theme, responsiveness, memory |
| 8. Testing | 5% | Coverage, regression, integration |
| 9. Dead Code | 4% | Unused imports, functions, files |
| 10. Final Report | 3% | Documentation completeness |

**Grade Scale:**
- **A+ (95-100):** Enterprise production ready
- **A (90-94):** Professional quality
- **B (80-89):** Good, minor issues
- **C (70-79):** Needs improvement
- **D (60-69):** Significant problems
- **F (<60):** Critical issues, not production ready

---

## Phase 1: Code Quality Audit / تدقيق جودة الكود

### 1.1 Static Analysis with Pylint
```bash
python -m pylint core/ modules/ ui/ --rcfile=.pylintrc --output-format=json > audit_results/pylint_report.json
```

**Checks:**
- [ ] All functions have type hints
- [ ] No bare `except: pass`
- [ ] No `except Exception: pass` without logging
- [ ] Cyclomatic complexity < 15 per function
- [ ] No functions > 50 lines
- [ ] No files > 500 lines (flag for refactoring)
- [ ] No duplicate code blocks > 6 lines
- [ ] All imports are used
- [ ] No wildcard imports (`from x import *`)
- [ ] Consistent naming (snake_case functions, PascalCase classes)

### 1.2 Type Checking with MyPy
```bash
python -m mypy core/ modules/ ui/ --config-file=mypy.ini --html-report audit_results/mypy/
```

**Checks:**
- [ ] All public functions have return type annotations
- [ ] All function parameters have type annotations
- [ ] No `Any` type used without justification
- [ ] Qt method calls use `int()` conversion (Rule 7)
- [ ] No implicit `Optional` without explicit annotation

### 1.3 Code Complexity with Radon
```bash
pip install radon
radon cc core/ modules/ ui/ -s -n C  # Show functions with complexity >= C
radon mi core/ modules/ ui/ -s -n B  # Show files with maintainability < B
```

**Thresholds:**
| Metric | Target | Action if exceeded |
|--------|--------|--------------------|
| Cyclomatic Complexity | < 10 (A/B) | Refactor function |
| Maintainability Index | > 20 (A/B) | Simplify module |
| Lines per function | < 50 | Split function |
| Lines per file | < 500 | Split into modules |
| Lines per class | < 300 | Extract sub-classes |

### 1.4 Known INTEGRA Patterns Scanner
Run the custom scanner from `scripts/integra_scanner.py`:
```bash
python scripts/integra_scanner.py core/ modules/ ui/
```

**Scans for all 13 mandatory rules violations:**
1. `date.replace(day=` without timedelta
2. f-string SQL queries
3. Shared state without Lock
4. Non-thread-safe singletons
5. `QThread.terminate()`
6. Widget lifecycle violations
7. Float passed to Qt int methods
8. DB connections not in finally
9. Bare except/silent exception
10. Password/secret exposure
11. Hardcoded colors
12. `os.startfile()` without platform check
13. Blocking operations in UI thread

### 1.5 Flagged Files (from current analysis)
These files exceed 800 lines and need refactoring:

| File | Lines | Priority |
|------|-------|----------|
| `modules/desktop_apps/window/desktop_apps_window.py` | 1,390 | HIGH |
| `modules/file_manager/window/file_manager_window.py` | 1,294 | HIGH |
| `modules/device_manager/window/device_manager_window.py` | 1,280 | HIGH |
| `modules/tasks/repository/task_repository.py` | 905 | MEDIUM |
| `modules/designer/report_designer/design_canvas.py` | 862 | MEDIUM |
| `core/reporting/template_engine.py` | 850 | MEDIUM |
| `modules/calendar/repository/calendar_repository.py` | 827 | MEDIUM |
| `core/desktop_apps/automation/desktop_automation.py` | 826 | MEDIUM |
| `core/ai/workflow/workflow_engine.py` | 824 | MEDIUM |
| `modules/copilot/components/chat_sidebar.py` | 806 | MEDIUM |
| `core/reporting/pdf_generator.py` | 801 | MEDIUM |

---

## Phase 2: Architecture Audit / تدقيق المعمارية

### 2.1 Layer Dependency Rules

```
ALLOWED DEPENDENCIES:
  modules/ → core/, ui/
  ui/      → core/
  core/    → (nothing - standalone)

FORBIDDEN DEPENDENCIES:
  core/    → ui/      ❌ (currently CLEAN: 0 violations)
  core/    → modules/ ❌
  ui/      → modules/ ❌ (ui components must be generic)
```

**Audit checks:**
- [ ] `core/` has zero imports from `ui/` or `modules/` (VERIFIED CLEAN)
- [ ] `ui/components/` has zero imports from `modules/`
- [ ] Each module is self-contained (no cross-module imports)
- [ ] All shared logic lives in `core/`

### 2.2 Module Consistency Check
Each module MUST follow this structure:
```
modules/<name>/
├── __init__.py
├── window/           # Main window
├── screens/          # Sub-screens
├── models/           # Data models (if needed)
├── repository/       # Database access (if needed)
├── widgets/          # Module-specific widgets (if needed)
└── toolbar/          # Module toolbar (if needed)
```

**Audit:**
- [ ] Every module has `__init__.py`
- [ ] Every module has `window/` directory
- [ ] No business logic in `window/` files (delegate to services/repository)
- [ ] No direct SQL in window files

### 2.3 God Class Detection
Classes with > 20 methods/attributes need refactoring:

**Action plan for god classes:**
1. Extract related methods into service classes
2. Use composition over inheritance
3. Apply Single Responsibility Principle
4. Maximum 15 methods per class (target)

### 2.4 Singleton Audit
- [ ] All singletons use `threading.Lock()` (Rule 4)
- [ ] All singletons use factory function `get_<name>()`
- [ ] No duplicate singleton implementations
- [ ] Singletons are documented in a registry

### 2.5 Import Chain Analysis
```bash
# Check for circular imports
python -c "
import ast, os, sys
from collections import defaultdict

graph = defaultdict(set)
for root, dirs, files in os.walk('core'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            module = path.replace('/', '.').replace('.py', '')
            try:
                tree = ast.parse(open(path).read())
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module:
                        graph[module].add(node.module)
            except: pass

# Detect cycles (DFS)
visited, stack = set(), set()
def dfs(node):
    if node in stack: return True
    if node in visited: return False
    visited.add(node); stack.add(node)
    for dep in graph.get(node, []):
        if dfs(dep): print(f'CYCLE: {node} -> {dep}'); return True
    stack.discard(node); return False

for m in graph: dfs(m)
"
```

---

## Phase 3: Database Audit / تدقيق قاعدة البيانات

### 3.1 Schema Validation
- [ ] All tables have primary keys
- [ ] All foreign keys have proper constraints
- [ ] All foreign keys have indexes
- [ ] Column types match Python types (no implicit casting)
- [ ] NOT NULL constraints on required fields
- [ ] Default values set for optional fields
- [ ] No orphaned tables (tables with no references)

### 3.2 Query Performance Audit
```sql
-- Find slow queries (> 100ms)
SELECT query, mean_exec_time, calls, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;

-- Find missing indexes (sequential scans on large tables)
SELECT relname, seq_scan, seq_tup_read, idx_scan, idx_tup_fetch
FROM pg_stat_user_tables
WHERE seq_scan > 100 AND idx_scan < seq_scan
ORDER BY seq_tup_read DESC;

-- Find unused indexes (wasting disk space)
SELECT indexrelname, idx_scan, pg_size_pretty(pg_relation_size(indexrelid))
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;
```

**Checks:**
- [ ] All WHERE columns are indexed
- [ ] No N+1 query patterns (loop with individual queries)
- [ ] No `SELECT *` in production code (select only needed columns)
- [ ] All queries use parameterized values (Rule 2)
- [ ] Complex queries use EXPLAIN ANALYZE
- [ ] Connection pool size is appropriate
- [ ] Connections are returned in `finally` blocks (Rule 8)

### 3.3 N+1 Query Detection
Scan for patterns like:
```python
# ❌ N+1 PATTERN
employees = select_all("SELECT * FROM employees")
for emp in employees:
    dept = select_one("SELECT * FROM departments WHERE id = %s", (emp.dept_id,))

# ✅ CORRECT - JOIN or batch query
employees = select_all("""
    SELECT e.*, d.name as dept_name
    FROM employees e
    JOIN departments d ON e.department_id = d.id
""")
```

### 3.4 Connection Pool Health
- [ ] Pool size configured (min=2, max=10)
- [ ] Connection timeout set (30 seconds)
- [ ] Idle connections are recycled
- [ ] Pool exhaustion is logged and alerted
- [ ] All connections returned in `finally` blocks

### 3.5 Data Integrity
- [ ] Cascading deletes configured properly
- [ ] Unique constraints on business keys
- [ ] Check constraints on enum-like columns
- [ ] Audit trail on sensitive tables (employees, payroll)

---

## Phase 4: Performance Audit / تدقيق الأداء

### 4.1 Startup Time Profiling
```python
import time
start = time.monotonic()
# ... application startup ...
elapsed = time.monotonic() - start
print(f"Startup time: {elapsed:.2f}s")
```

**Targets:**
| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Cold startup | < 3 seconds | TBD | |
| Window open | < 500ms | TBD | |
| Module load | < 1 second | TBD | |
| DB query (simple) | < 50ms | TBD | |
| DB query (complex) | < 500ms | TBD | |
| Table render (1000 rows) | < 1 second | TBD | |

### 4.2 Memory Profiling
```bash
pip install memray tracemalloc
python -m memray run main.py
python -m memray flamegraph memray-output.bin -o audit_results/memory_flamegraph.html
```

**Checks:**
- [ ] Memory usage < 200MB at idle
- [ ] No memory growth over time (leak detection)
- [ ] Closed windows are garbage collected (Rule 6)
- [ ] Large data structures are released after use
- [ ] Images/pixmaps are not duplicated unnecessarily

### 4.3 Lazy Loading Audit
- [ ] Modules loaded on demand (not all at startup)
- [ ] Database queries only when data is needed
- [ ] Heavy imports deferred (`import inside function`)
- [ ] Tab content loaded when tab is selected (not all tabs at once)

### 4.4 Caching Strategy
- [ ] Frequently accessed data is cached (departments, statuses, etc.)
- [ ] Cache has TTL (time-to-live) - not stale forever
- [ ] Cache invalidated on data change
- [ ] Cache size is bounded (LRU or similar)

### 4.5 Blocking Operations Scan
All DB/network/file operations MUST be off main thread (Rule 13):

```bash
# Scan for blocking calls in UI files
grep -rn "select_all\|select_one\|insert\|update\|delete\|execute" ui/ modules/*/window/ modules/*/screens/
```

**Priority files to check:**
- All `window/` files in modules
- All `screens/` files in modules
- All `ui/dialogs/` files

### 4.6 Large File Refactoring Plan
Files > 800 lines impact performance and maintainability:

| File | Lines | Refactoring Strategy |
|------|-------|---------------------|
| `desktop_apps_window.py` | 1,390 | Split into: app_launcher, app_config, app_monitor |
| `file_manager_window.py` | 1,294 | Split into: file_browser, file_operations, pdf_tools |
| `device_manager_window.py` | 1,280 | Split into: scanner_panel, printer_panel, device_config |
| `task_repository.py` | 905 | Split into: task_queries, task_filters, task_stats |
| `design_canvas.py` | 862 | Split into: canvas_core, canvas_tools, canvas_export |

---

## Phase 5: Security Audit / تدقيق الأمان

### 5.1 SQL Injection Scan (Rule 2)
```bash
# Find ALL SQL with f-strings or .format()
grep -rn 'f".*SELECT\|f".*INSERT\|f".*UPDATE\|f".*DELETE\|\.format.*SELECT' core/ modules/ ui/
```

- [ ] Zero f-string SQL queries
- [ ] All user input parameterized with `%s`
- [ ] Table/column names use `psycopg2.sql.Identifier()`

### 5.2 Secrets Scanning
```bash
# Find hardcoded passwords/keys/tokens
grep -rn 'password\s*=\s*["\x27]' --include="*.py" core/ modules/ ui/
grep -rn 'secret\|api_key\|token\s*=' --include="*.py" core/ modules/ ui/
grep -rn 'DB_PASSWORD' core/ modules/ ui/
```

- [ ] No hardcoded passwords in source code
- [ ] `DB_PASSWORD` not in `__all__` exports (Rule 10)
- [ ] Secrets stored in `.env` or keyring
- [ ] `.env` in `.gitignore`

### 5.3 HTML Injection (XSS)
- [ ] All user content escaped with `html.escape()` before rendering
- [ ] Email content sanitized before display
- [ ] No `setHtml()` with unsanitized input

### 5.4 Dependency Vulnerability Scan
```bash
pip install safety
safety check --json > audit_results/dependency_vulnerabilities.json
pip audit  # Python 3.12+
```

### 5.5 Password Security
- [ ] `hmac.compare_digest()` for comparisons (Rule 10)
- [ ] Argon2/bcrypt for password hashing (not MD5/SHA)
- [ ] Encryption keys in keyring (not plaintext files)
- [ ] Key rotation supported

---

## Phase 6: Thread Safety Audit / تدقيق سلامة الخيوط

### 6.1 Shared State Analysis
```bash
# Find class attributes modified without locks
grep -rn 'self\._.*=' --include="*.py" core/ | grep -v 'self\._lock\|with self\._lock\|def __init__'
```

- [ ] All shared lists/dicts protected with `Lock()`
- [ ] All counters protected with `Lock()`
- [ ] All singletons thread-safe (Rule 4)
- [ ] No global mutable state without protection

### 6.2 QThread Safety (Rule 5)
- [ ] Zero uses of `QThread.terminate()`
- [ ] All threads use cooperative shutdown
- [ ] All threads have proper `wait()` on exit
- [ ] Worker threads don't modify UI directly (use signals)

### 6.3 Signal/Slot Thread Safety
- [ ] Cross-thread signals use `Qt.QueuedConnection`
- [ ] No direct widget manipulation from background threads
- [ ] `QMetaObject.invokeMethod()` for cross-thread calls

### 6.4 Deadlock Prevention
- [ ] Lock acquisition order is consistent
- [ ] No nested locks without documented ordering
- [ ] All locks have timeout capability
- [ ] `threading.RLock()` used where re-entrant locking needed

---

## Phase 7: UI/UX Audit / تدقيق الواجهة

### 7.1 Theme Compliance (Rule 11)
```bash
# Find hardcoded colors
grep -rn '#[0-9a-fA-F]\{6\}' --include="*.py" ui/ modules/
grep -rn 'background.*:.*#\|color.*:.*#' --include="*.py" ui/ modules/
```

- [ ] Zero hardcoded colors in stylesheets
- [ ] All components use QPalette or theme-aware values
- [ ] Dark mode tested on all screens
- [ ] Light mode tested on all screens

### 7.2 RTL/Arabic Support
- [ ] All labels support Arabic text
- [ ] Layout direction is RTL-aware
- [ ] Cairo font used consistently (Rule 12)
- [ ] No text truncation in Arabic mode

### 7.3 Widget Memory Management (Rule 6)
- [ ] Closed windows removed from cache dicts
- [ ] `deleteLater()` called after removal from collections
- [ ] Old layouts cleared before rebuild
- [ ] `processEvents()` has re-entrance guard

### 7.4 Responsiveness
- [ ] No operation blocks UI for > 200ms
- [ ] Progress dialogs for operations > 1 second
- [ ] Cancel buttons on long operations
- [ ] Loading indicators on data fetch

### 7.5 Accessibility
- [ ] Font size configurable
- [ ] High contrast mode available
- [ ] Keyboard navigation works on all dialogs
- [ ] Tab order is logical

---

## Phase 8: Testing Audit / تدقيق الاختبارات

### 8.1 Test Coverage
```bash
pip install pytest pytest-cov
python -m pytest tests/ --cov=core --cov=modules --cov=ui --cov-report=html:audit_results/coverage/
```

**Targets:**
| Layer | Target Coverage |
|-------|----------------|
| `core/database/` | 90% |
| `core/security/` | 90% |
| `core/threading/` | 80% |
| `modules/*/repository/` | 85% |
| `modules/*/models/` | 80% |
| `ui/components/` | 60% |

### 8.2 Critical Path Tests
These MUST have tests:
- [ ] Database CRUD operations
- [ ] Authentication/password verification
- [ ] Data validation (Pydantic schemas)
- [ ] Export operations (Excel, CSV, PDF)
- [ ] Sync system (backup/restore)
- [ ] Thread worker completion/cancellation

### 8.3 Regression Tests
- [ ] Test for each of the 92 fixed bugs (prevent regression)
- [ ] Date boundary tests (end of month, year, leap year)
- [ ] Division by zero edge cases
- [ ] Empty data handling (empty tables, null values)

---

## Phase 9: Dead Code Audit / تدقيق الكود الميت

### 9.1 Unused Imports
```bash
pip install autoflake
autoflake --check --remove-all-unused-imports -r core/ modules/ ui/
```

### 9.2 Unused Functions/Classes
```bash
pip install vulture
vulture core/ modules/ ui/ --min-confidence 80
```

### 9.3 Unreachable Code
- [ ] No code after `return` statements
- [ ] No `if False:` blocks
- [ ] No commented-out code blocks > 5 lines
- [ ] No unused files (empty or orphaned modules)

### 9.4 Install/Tool Scripts Cleanup
These files in root are installation scripts that should be archived:
- `install_sync_system.py` (1,348 lines)
- `install_edit_screen.py`
- `INTEGRA_HEALTH_CHECK.py` (867 lines)
- `Tools/fix_sync_import.py` (813 lines)
- `Tools/fix_sync_v3_final.py`
- `Tools/fix_all_issues.py`
- `Tools/install_*.py`

**Action:** Move to `Tools/archive/` or remove if no longer needed.

---

## Phase 10: Final Report / التقرير النهائي

### 10.1 Report Generation
After all phases complete, generate:

```
audit_results/
├── AUDIT_REPORT.md          # Summary with scores
├── pylint_report.json        # Phase 1
├── mypy/                     # Phase 1
├── complexity_report.txt     # Phase 1
├── architecture_diagram.md   # Phase 2
├── db_performance.sql        # Phase 3
├── memory_flamegraph.html    # Phase 4
├── security_scan.json        # Phase 5
├── thread_safety.md          # Phase 6
├── ui_audit.md               # Phase 7
├── coverage/                 # Phase 8
├── dead_code.txt             # Phase 9
└── action_items.md           # Prioritized fix list
```

### 10.2 Action Items Priority
After audit, issues are categorized:

| Priority | SLA | Description |
|----------|-----|-------------|
| P0 - Critical | Fix immediately | Security vulnerabilities, data loss risk, crashes |
| P1 - High | Fix within session | Performance > 3s, memory leaks, thread safety |
| P2 - Medium | Fix within week | Code quality, architecture violations |
| P3 - Low | Backlog | Style, dead code, minor improvements |

---

## Execution Plan / خطة التنفيذ

### Session 1: Phases 1 + 9 (Code Quality + Dead Code)
- Run pylint, mypy, radon, vulture
- Fix critical findings
- Remove dead code
- **Expected duration:** 1 session

### Session 2: Phase 2 (Architecture)
- Validate layer dependencies
- Refactor god classes
- Fix circular imports
- Enforce module structure
- **Expected duration:** 1-2 sessions

### Session 3: Phase 3 (Database)
- Run query performance analysis
- Add missing indexes
- Fix N+1 patterns
- Validate schema integrity
- **Expected duration:** 1 session

### Session 4: Phase 4 (Performance)
- Profile startup time
- Memory leak detection
- Move blocking operations off main thread
- Implement lazy loading
- Refactor large files
- **Expected duration:** 2-3 sessions

### Session 5: Phase 5 + 6 (Security + Threads)
- Full security scan
- Thread safety verification
- Fix any remaining issues
- **Expected duration:** 1 session

### Session 6: Phase 7 (UI/UX)
- Theme compliance check
- RTL audit
- Widget memory check
- Responsiveness testing
- **Expected duration:** 1 session

### Session 7: Phase 8 (Testing)
- Write critical path tests
- Write regression tests for 92 bugs
- Set up test coverage reporting
- **Expected duration:** 2-3 sessions

### Session 8: Phase 10 (Final Report)
- Generate all reports
- Calculate final score
- Create prioritized action plan
- **Expected duration:** 1 session

---

## Tools Required / الأدوات المطلوبة

```bash
# Code Quality
pip install pylint mypy radon

# Dead Code
pip install vulture autoflake

# Performance
pip install memray scalene py-spy

# Security
pip install safety bandit

# Testing
pip install pytest pytest-cov pytest-qt

# Database
# pg_stat_statements extension (PostgreSQL)
```

---

## Success Criteria / معايير النجاح

The audit program is complete when:
- [ ] All 10 phases executed
- [ ] Final score >= 90 (Grade A)
- [ ] Zero P0 (critical) issues remaining
- [ ] Zero P1 (high) issues remaining
- [ ] Test coverage > 70% on core/
- [ ] Startup time < 3 seconds
- [ ] Memory usage < 200MB at idle
- [ ] All 13 mandatory rules verified (zero violations)

---

## Continuous Monitoring / المراقبة المستمرة

After initial audit, set up automated checks:

1. **Pre-commit hooks:** Run integra_scanner.py on changed files
2. **Weekly:** Run pylint + mypy on full codebase
3. **Monthly:** Full performance profiling
4. **Per release:** Complete security scan
5. **Quarterly:** Full 10-phase audit re-run

---

*This document is the master reference for INTEGRA quality assurance.*
*Update phase scores as audits are completed.*
