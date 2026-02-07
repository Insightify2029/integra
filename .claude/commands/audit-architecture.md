---
description: Architecture review - module consistency, patterns, coupling, and overall design health
allowed-tools: Read, Grep, Glob, Bash(find:*), Bash(wc:*), Bash(python:*)
agent: integra-auditor
---

# Architecture Audit for INTEGRA

## Step 1: Map the Codebase Structure
```bash
find . -name "*.py" -not -path "./.venv/*" | head -200
find . -name "*.py" -not -path "./.venv/*" | wc -l
```

## Step 2: Module Consistency Check
For each module in modules/:
- Does it have models/, repository/, screens/ subdirectories?
- Are repository patterns consistent (get_by_*, create_*, update_*, delete_*)?
- Do models use consistent patterns (dataclass, enum, property)?
- Is the module registered properly in the launcher?

## Step 3: Dependency Analysis
```bash
# Find circular import risks
grep -rn "^from core" --include="*.py" modules/
grep -rn "^from modules" --include="*.py" core/
grep -rn "^import " --include="*.py" . | grep -v ".venv" | sort
```
- core/ should NEVER import from modules/
- modules/ should NEVER import from ui/ directly
- Check for lazy imports and whether they're necessary

## Step 4: Database Layer Consistency
```bash
find . -name "*repository*.py" -o -name "*query*.py" | grep -v .venv
```
- All queries use the same connection pool pattern?
- Transaction boundaries for multi-step operations?
- Consistent error handling?

## Step 5: UI Layer Consistency
```bash
find ui/ -name "*.py" | head -50
```
- Theme support across all components?
- Consistent widget cleanup patterns?
- No direct DB access from UI (should go through modules)?

## Step 6: Event/Signal Architecture
```bash
grep -rn "Signal\|signal\|emit\|EventBus" --include="*.py" .
```
- Is the EventBus used consistently?
- Are custom signals properly typed?
- Signal/slot connections cleaned up?

## Step 7: Configuration Consistency
```bash
grep -rn "\.env\|os\.environ\|config\[" --include="*.py" .
```
- Single source of truth for config?
- No hardcoded values that should be config?
- Deep merge for nested configs?

## Step 8: Error Handling Patterns
```bash
grep -rn "except.*pass\|except Exception" --include="*.py" . | head -30
```

## Report
Provide:
1. Architecture health score (1-10) with justification
2. Module consistency issues
3. Coupling problems
4. Recommended refactorings prioritized by impact
5. Patterns that should be standardized
