---
description: Quick automated checks on a single file - runs fast pattern matching
allowed-tools: Read, Bash(grep:*), Bash(python:*)
---

# Quick Check for $ARGUMENTS

Run these fast pattern checks on the specified file:

```bash
FILE="$ARGUMENTS"

echo "=== CRITICAL PATTERN CHECK ==="

echo "--- SQL Injection ---"
grep -n 'f"SELECT\|f"INSERT\|f"UPDATE\|f"DELETE\|f"DROP\|f"CREATE' "$FILE" 2>/dev/null

echo "--- Unsafe Date Arithmetic ---"
grep -n 'replace(day=\|replace(hour=\|replace(month=' "$FILE" 2>/dev/null

echo "--- QThread.terminate() ---"
grep -n '\.terminate()' "$FILE" 2>/dev/null

echo "--- Bare Except ---"
grep -n 'except.*:.*pass\|except Exception.*pass' "$FILE" 2>/dev/null

echo "--- Missing Lock ---"
grep -n '_running\|_active\|_processing' "$FILE" 2>/dev/null

echo "--- Float to Qt ---"
grep -n '\.scaled(\|\.resize(\|\.setGeometry(' "$FILE" 2>/dev/null

echo "--- os.startfile ---"
grep -n 'os\.startfile\|os\.system' "$FILE" 2>/dev/null

echo "--- Hardcoded Colors ---"
grep -n '#[0-9a-fA-F]\{6\}' "$FILE" 2>/dev/null

echo "--- Division Without Check ---"
grep -n '/ .*total\|/ .*count\|/ .*len(' "$FILE" 2>/dev/null

echo "=== CHECK COMPLETE ==="
```

For each match found, read the surrounding context (5 lines before and after)
and determine if it's actually a violation or a false positive.
Report only confirmed issues.
