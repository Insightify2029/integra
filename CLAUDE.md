# INTEGRA - ERP Desktop Application
# Python + PyQt5 + PostgreSQL

## Project Overview
Palm oil refinery ERP system handling production, costing, BI, tasks, calendar,
email, AI copilot, form designer, report designer, and notifications.

## Architecture
- `core/` - Database, AI, BI, threading, security, config, utilities
- `modules/` - Business modules (tasks, calendar, copilot, designer, file_manager, notifications)
- `ui/` - Shared UI components (tables, buttons, labels, cards, dialogs, email, AI panels)
- `main.py` - Application entry point

## ⚠️ MANDATORY RULES - NEVER VIOLATE THESE

### 1. Date/Time Arithmetic
NEVER use `date.replace(day=day+N)` or `hour + N` for date math.
ALWAYS use `timedelta()`:
```python
# ❌ WRONG - crashes at month/day boundaries
tomorrow = today.replace(day=today.day + 1)
next_hour = now.replace(hour=now.hour + 1)

# ✅ CORRECT
tomorrow = today + timedelta(days=1)
next_hour = now + timedelta(hours=1)
```

### 2. SQL Injection Prevention
NEVER use f-strings or .format() for SQL queries.
ALWAYS use parameterized queries or psycopg2.sql module:
```python
# ❌ WRONG
f"SELECT * FROM {table_name} WHERE id = {user_id}"

# ✅ CORRECT
sql.SQL("SELECT * FROM {} WHERE id = %s").format(sql.Identifier(table_name))
```

### 3. Thread Safety
ALL shared state MUST be protected with threading.Lock():
```python
# ❌ WRONG
self._data.append(item)  # from multiple threads

# ✅ CORRECT
with self._lock:
    self._data.append(item)
```

### 4. Singleton Pattern
ALL singletons MUST use double-checked locking:
```python
_lock = threading.Lock()
_instance = None

@classmethod
def get_instance(cls):
    if cls._instance is None:
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
    return cls._instance
```

### 5. QThread Safety
NEVER use QThread.terminate(). ALWAYS use cooperative shutdown:
```python
# ❌ WRONG
thread.terminate()

# ✅ CORRECT
thread.requestInterruption()
thread.quit()
thread.wait(3000)
```

### 6. PyQt Widget Lifecycle
- ALWAYS call deleteLater() AND remove from parent collections
- ALWAYS clear old layout before rebuilding
- ALWAYS clean up closed windows from cache dicts
- NEVER let processEvents() cause re-entrance (use guard flag)

### 7. Type Safety with Qt
ALWAYS convert to int() before passing to Qt methods expecting integers:
```python
# ❌ WRONG
pixmap.scaled(width * 0.8, height * 0.8)

# ✅ CORRECT
pixmap.scaled(int(width * 0.8), int(height * 0.8))
```

### 8. Database Connections
ALWAYS return connections to pool in finally blocks:
```python
conn = pool.get_connection()
try:
    # work
finally:
    pool.return_connection(conn)
```

### 9. Error Handling
- NEVER use bare `except: pass` - always log with app_logger.error()
- NEVER use `except Exception: pass` silently
- ALWAYS check fetchone() result for None before accessing [0]
- ALWAYS handle division by zero: `if total > 0`
- ALWAYS wrap enum conversions in try/except

### 10. Security
- NEVER expose DB_PASSWORD in __all__ or public exports
- ALWAYS use hmac.compare_digest() for password comparison (not ==)
- ALWAYS escape HTML content before rendering: html.escape()
- ALWAYS use keyring for sensitive key storage when available

### 11. Theme Support
ALL UI components MUST respect dark/light theme. Never hardcode colors.
Read current theme and use appropriate palette colors.

### 12. Cross-Platform
- NEVER use os.startfile() directly - use platform detection
- NEVER use Windows-only fonts (Segoe UI) - use cross-platform (Cairo)
- Use Qt.ArrowCursor instead of magic numbers like setCursor(0)

### 13. Blocking Operations
NEVER run blocking operations (DB, network, file I/O) on the main Qt thread.
ALWAYS use QThread or Worker pattern with proper signals.

## Code Style
- Python 3.10+
- Type hints on all function signatures
- Arabic UI support (RTL) with Cairo font
- Logging via app_logger (never print())

## Testing Commands
```bash
python -m pytest tests/ -v
python -m mypy src/ --strict
python -m pylint src/ --disable=C0114,C0115,C0116
```
