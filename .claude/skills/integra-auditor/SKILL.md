---
name: integra-auditor
description: >
  Auto-invoke when reviewing, auditing, or writing Python code for INTEGRA.
  Contains the complete bug pattern database from 92 historical issues.
  Triggers on: code review, audit, bug fix, new feature, refactoring.
---

# INTEGRA Quality Knowledge Base

## Historical Bug Pattern Database

These are the 92 bugs found in INTEGRA, categorized by root cause.
When writing or reviewing code, CHECK EVERY PATTERN.

### Pattern 1: Date/Time Boundary Errors (3 bugs)
- CRIT-03: `hour + 1` when hour=23 → ValueError (hour=24)
- CRIT-08: `today.replace(day=today.day + 1)` fails day > 28
- CRIT-09: `replace(day=...)` crashes at month boundaries
**Rule**: ALWAYS use `timedelta()` for ALL date/time arithmetic. No exceptions.

### Pattern 2: SQL Injection (5 bugs)
- CRIT-11: f-strings in form_builder/data_binding.py
- HIGH-01: f-strings in bi/data_exporter.py
- HIGH-02: f-strings in bi/views_manager.py
- MED-04: where_clause as raw SQL in scalar_query.py
- MED-28: No transaction boundaries in multi-step BI ops
**Rule**: psycopg2.sql.Identifier() for names, %s for values. ALWAYS.

### Pattern 3: Thread Safety (8 bugs)
- CRIT-04: EventBus PriorityQueue missing __lt__
- HIGH-05: _action_history modified without lock
- HIGH-06: ConversationContext not thread-safe
- HIGH-07: _running flag unprotected
- MED-06: Alert counter not thread-safe
- MED-07: get_insights() reads without lock
- LOW-15: 7 singletons not thread-safe
- LOW-17: Duplicated singleton in AIService
**Rule**: Lock() on ALL shared state. Double-checked locking on ALL singletons.

### Pattern 4: Qt/PyQt5 Misuse (8 bugs)
- CRIT-06: FilterPanel not added to layout after creation
- CRIT-07: QThread.terminate() → data corruption
- CRIT-10: Float passed to QPixmap.scaled()
- HIGH-12: Window cache memory leak
- HIGH-13: Widget deletion without list cleanup
- MED-15: DayCell layouts created multiple times
- MED-17: CSS accumulates on repeated validation
- LOW-09: processEvents() re-entrance
**Rule**: Clean lifecycle management. int() for Qt. No terminate().

### Pattern 5: Missing/Wrong Logic (10 bugs)
- HIGH-08: Save button doesn't save
- HIGH-09: Test connection tests wrong credentials
- HIGH-10: Filter branches with only `pass`
- HIGH-11: get_by_employee() excludes IN_PROGRESS
- MED-14: Day names mapped incorrectly
- MED-16: Week view shows wrong month at boundaries
- MED-19: _always_on_top contradicts window flags
- MED-21: All tasks loaded in memory for filtering
- MED-23: StreamWorker signal flow broken on error
**Rule**: Every branch must have real implementation. Test edge cases.

### Pattern 6: Security (6 bugs)
- MED-12: HTML injection in email viewer
- MED-24: DB_PASSWORD in public API
- MED-25: Encryption key in plain text
- MED-26: Timing attack on password comparison
- LOW-18: Key rotation without re-encryption
**Rule**: Escape all HTML. Protect all secrets. Use constant-time comparison.

### Pattern 7: Error Handling (5 bugs)
- HIGH-03: Unhandled ValueError on unknown ActionType
- MED-20: 4 locations with `except Exception: pass`
- MED-27: fetchone()[0] without None check
- MED-10: Division by zero in exports
- LOW-11: Bare except clause
**Rule**: Specific exceptions. Log everything. Check for None/zero.

### Pattern 8: Resource Management (4 bugs)
- CRIT-01: Connection pool exhaustion (no return)
- CRIT-02: Missing import prevents module load
- HIGH-14: Missing import causes NameError
- LOW-06: Files never closed in main.py
**Rule**: Finally blocks for resources. Verify all imports.

## Quick Reference Grep Commands

```bash
# Find all potential issues in one sweep
grep -rn 'f"SELECT\|f"INSERT\|f"UPDATE\|f"DELETE' --include="*.py" .
grep -rn 'replace(day=\|replace(hour=\|replace(month=' --include="*.py" .
grep -rn '\.terminate()' --include="*.py" .
grep -rn 'except.*:.*pass\|except Exception.*:.*pass' --include="*.py" .
grep -rn '_instance.*=.*None' --include="*.py" .  # then check for Lock
grep -rn 'os\.startfile' --include="*.py" .
grep -rn 'f".*FROM.*{' --include="*.py" .
```
