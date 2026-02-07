---
description: Run a full INTEGRA code audit on modified files or specified paths
allowed-tools: Read, Grep, Glob, Bash(python:*), Bash(grep:*), Bash(find:*), Bash(git:*)
agent: integra-auditor
---

# Full INTEGRA Audit

## Target Files
Determine which files to audit:

1. If `$ARGUMENTS` is provided, audit those specific files/directories
2. If no arguments, find all files modified since last commit:
   ```bash
   git diff --name-only HEAD
   git diff --name-only --staged
   ```
3. If no git changes, audit the most recently modified .py files:
   ```bash
   find . -name "*.py" -mmin -60 -not -path "./.venv/*"
   ```

## Audit Procedure

For EACH file:
1. Read the entire file content
2. Run through ALL 16 checklist categories from your auditor instructions
3. Cross-reference with CLAUDE.md mandatory rules
4. Check consistency with other modules in the same directory

After individual file review:
1. Check cross-module consistency (imports, shared interfaces, event flow)
2. Verify thread safety across the full call chain
3. Check for any new singletons that might conflict

Report ALL findings. Zero tolerance policy.
