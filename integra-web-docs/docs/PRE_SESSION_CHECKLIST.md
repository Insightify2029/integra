# INTEGRA Web - Pre-Session Checklist

> **CRITICAL:** Claude MUST execute this checklist at the START of every session.
> **Purpose:** Ensure continuity between sessions and prevent duplicate/conflicting work.

---

## Mandatory Steps (Execute in Order)

### Step 1: Read Project State (30 seconds)

```
□ Read docs/SESSION_TRACKER.md — understand current phase and last session
□ Read docs/PROJECT_PLAN.md — identify next tasks to work on
□ Read docs/ARCHITECTURE_DECISIONS.md — review decisions made so far
```

**Output:** State to user:
> "آخر جلسة كانت Session X بتاريخ [DATE]. المرحلة الحالية: [PHASE]. المهمة القادمة: [TASK]."

### Step 2: Check Git State (15 seconds)

```bash
git status                    # Any uncommitted changes?
git log --oneline -5          # Last 5 commits
git branch -a                 # Current branch
```

**If uncommitted changes exist:** Ask user whether to commit or stash them.

### Step 3: Verify Development Environment (15 seconds)

```bash
python manage.py check        # Django system check
python manage.py migrate --check  # Pending migrations?
```

**If checks fail:** Fix before proceeding with new work.

### Step 4: Run Tests (30 seconds)

```bash
python -m pytest --tb=short -q  # Quick test run
```

**If tests fail:** Prioritize fixing broken tests before new work.

### Step 5: Identify Today's Tasks (15 seconds)

Based on SESSION_TRACKER.md and PROJECT_PLAN.md:

```
□ Confirm which session number we're working on
□ List the specific tasks for this session
□ Identify any blockers from the previous session
□ Ask user if they want to override the planned tasks
```

**Output:** Present task list to user:
> "جلسة اليوم: Session X — [Title]"
> "المهام المخططة:"
> "1. [Task 1]"
> "2. [Task 2]"
> "..."
> "هل تريد تعديل الخطة؟"

---

## Post-Session Checklist (Execute Before Ending)

### Step 1: Update Documentation

```
□ Update docs/SESSION_TRACKER.md with session entry
□ Update docs/PROJECT_PLAN.md — mark completed tasks ✅
□ Update docs/ARCHITECTURE_DECISIONS.md if any new decisions made
```

### Step 2: Run Quality Checks

```bash
ruff check .                    # Lint check
ruff format --check .           # Format check
python -m mypy integra_web/     # Type check
python -m pytest --tb=short     # All tests pass
```

### Step 3: Commit and Push

```bash
git add -A
git commit -m "feat(session-X): [description]"
git push origin [branch]
```

### Step 4: Summary to User

```
□ List what was completed
□ List what's pending for next session
□ Mention any blockers or decisions needed
□ Create PR if significant changes were made
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────┐
│           SESSION START FLOW                 │
│                                              │
│  1. Read SESSION_TRACKER.md                  │
│  2. Read PROJECT_PLAN.md                     │
│  3. git status + git log                     │
│  4. python manage.py check                   │
│  5. pytest --tb=short -q                     │
│  6. Present tasks → ask user                 │
│  7. BEGIN WORK                               │
│                                              │
│           SESSION END FLOW                   │
│                                              │
│  1. ruff check + format                      │
│  2. mypy                                     │
│  3. pytest (all pass?)                        │
│  4. Update SESSION_TRACKER.md                │
│  5. Update PROJECT_PLAN.md                   │
│  6. git commit + push                        │
│  7. Create PR if needed                      │
│  8. Summary to user                          │
└─────────────────────────────────────────────┘
```

---

## Emergency Recovery

If a session starts and things are broken:

1. **Tests failing?** → `git stash` → check if tests pass on clean state → `git stash pop`
2. **Migration conflict?** → `python manage.py showmigrations` → resolve
3. **Dependencies broken?** → `pip install -e ".[dev]"` → retry
4. **Can't determine state?** → Read git log, check SESSION_TRACKER.md, ask user
