---
description: Security-focused audit - SQL injection, secrets, HTML injection, timing attacks
allowed-tools: Read, Grep, Glob, Bash(grep:*), Bash(find:*)
agent: integra-auditor
---

# Security Audit for INTEGRA

Run a comprehensive security scan on the entire codebase.

## Scan Categories

### 1. SQL Injection (11 historical instances found)
```bash
grep -rn 'f"SELECT\|f"INSERT\|f"UPDATE\|f"DELETE\|f"DROP\|f"CREATE\|f"ALTER' --include="*.py" .
grep -rn '\.format.*SELECT\|\.format.*INSERT\|\.format.*UPDATE' --include="*.py" .
grep -rn 'f".*FROM.*{' --include="*.py" .
```
Verify EVERY match uses psycopg2.sql.Identifier() or parameterized queries.

### 2. Secrets Exposure
```bash
grep -rn 'DB_PASSWORD\|SECRET_KEY\|API_KEY\|ENCRYPTION_KEY' --include="*.py" .
grep -rn '__all__' --include="__init__.py" .
```
Check no sensitive values in __all__, logs, or error messages.

### 3. HTML Injection
```bash
grep -rn 'setHtml\|insertHtml\|setContent.*html' --include="*.py" .
```
Verify html.escape() used before rendering user/email content.

### 4. Timing Attacks
```bash
grep -rn '== .*password\|password.*==' --include="*.py" .
grep -rn '== .*key\|key.*==' --include="*.py" .
grep -rn '== .*token\|token.*==' --include="*.py" .
```
Verify hmac.compare_digest() for all secret comparisons.

### 5. Plaintext Storage
```bash
grep -rn 'open.*key\|write.*key\|save.*key' --include="*.py" core/security/
```
Verify keyring usage for sensitive storage.

### 6. Platform Command Injection
```bash
grep -rn 'os\.startfile\|os\.system\|subprocess.*shell=True' --include="*.py" .
```

Report ALL findings with severity and fix recommendations.
