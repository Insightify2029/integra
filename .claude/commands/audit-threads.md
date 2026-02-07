---
description: Thread safety audit - race conditions, locks, shared state, QThread patterns
allowed-tools: Read, Grep, Glob, Bash(grep:*), Bash(find:*)
agent: integra-auditor
---

# Thread Safety Audit for INTEGRA

## Step 1: Find All Threading Code
```bash
grep -rn 'threading\|QThread\|Thread\|_lock\|Lock()\|daemon' --include="*.py" .
grep -rn '_running\|_active\|_processing\|_started' --include="*.py" .
```

## Step 2: Find All Singletons
```bash
grep -rn '_instance\|__new__\|get_instance\|getInstance' --include="*.py" .
```
Verify each has double-checked locking with threading.Lock().

## Step 3: Find Shared Mutable State
```bash
grep -rn 'self\._.*= \[\]\|self\._.*= {}\|self\._.*\.append\|self\._.*\.update' --include="*.py" .
```
For each: Is it accessed from multiple threads? Is it protected by a lock?

## Step 4: Check QThread Patterns
```bash
grep -rn '\.terminate()\|\.start()\|\.quit()\|\.wait(' --include="*.py" .
```
- NEVER terminate() - must use requestInterruption()
- Every start() should have corresponding cleanup
- wait() should have timeout

## Step 5: Check Signal/Slot Thread Boundaries
Verify signals used for cross-thread communication (not direct method calls).

## Step 6: Check Worker Lifecycle
```bash
grep -rn 'Worker\|worker' --include="*.py" ui/ modules/
```
- Workers cleaned up in closeEvent()?
- Prevent overlapping workers?
- Error signals handled properly?

Report ALL race conditions, missing locks, and unsafe patterns.
