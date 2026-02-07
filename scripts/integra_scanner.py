#!/usr/bin/env python3
"""
INTEGRA Quality Scanner - Fast pattern-based bug detection.
Scans for the 8 known bug patterns from INTEGRA's error history.
Exit code 1 = critical issues found, 0 = clean.
"""

import sys
import re
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
# Pattern definitions based on 92 historical bugs
# ═══════════════════════════════════════════════════════════════

CRITICAL_PATTERNS = [
    {
        "name": "SQL Injection",
        "pattern": r'f["\'](?:SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b',
        "message": "SQL injection risk - use psycopg2.sql.Identifier() and parameterized queries",
        "ref": "CRIT-11, HIGH-01, HIGH-02"
    },
    {
        "name": "Unsafe Date Arithmetic",
        "pattern": r'\.replace\(\s*(?:day|hour|month|year)\s*=\s*\w+\s*[\+\-]',
        "message": "Use timedelta() instead of replace() for date arithmetic",
        "ref": "CRIT-03, CRIT-08, CRIT-09"
    },
    {
        "name": "QThread.terminate()",
        "pattern": r'\.terminate\(\)',
        "message": "Use requestInterruption() + quit() + wait() instead",
        "ref": "CRIT-07"
    },
]

HIGH_PATTERNS = [
    {
        "name": "Bare Except",
        "pattern": r'except\s*:\s*pass|except\s+Exception\s*:\s*pass',
        "message": "Use specific exceptions and log errors",
        "ref": "MED-20, LOW-11"
    },
    {
        "name": "os.startfile()",
        "pattern": r'os\.startfile\(',
        "message": "Windows-only - add platform detection for Linux/macOS",
        "ref": "CRIT-05"
    },
    {
        "name": "Raw os.system()",
        "pattern": r'os\.system\(',
        "message": "Use subprocess.run() with shell=False",
        "ref": "Security best practice"
    },
]

MEDIUM_PATTERNS = [
    {
        "name": "Potential Division by Zero",
        "pattern": r'/\s*(?:total|count|len\(|size|num_)',
        "message": "Add 'if denominator > 0' check",
        "ref": "MED-10"
    },
    {
        "name": "Hardcoded Color",
        "pattern": r'["\']#[0-9a-fA-F]{6}["\']',
        "message": "Consider using theme-aware colors instead of hardcoded values",
        "ref": "MED-08, MED-18"
    },
    {
        "name": "Password in String",
        "pattern": r'(?:password|secret|key)\s*=\s*["\'][^"\']+["\']',
        "message": "Don't hardcode credentials - use environment variables or keyring",
        "ref": "MED-24, MED-25"
    },
]


def scan_file(filepath: str) -> list[dict]:
    """Scan a single file for known bug patterns."""
    issues = []
    try:
        content = Path(filepath).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return issues

    lines = content.splitlines()

    for line_num, line in enumerate(lines, 1):
        # Skip comments
        stripped = line.strip()
        if stripped.startswith("#"):
            continue

        for pattern_group, severity in [
            (CRITICAL_PATTERNS, "CRITICAL"),
            (HIGH_PATTERNS, "HIGH"),
            (MEDIUM_PATTERNS, "MEDIUM"),
        ]:
            for p in pattern_group:
                if re.search(p["pattern"], line, re.IGNORECASE):
                    issues.append({
                        "severity": severity,
                        "name": p["name"],
                        "file": filepath,
                        "line": line_num,
                        "code": stripped[:100],
                        "message": p["message"],
                        "ref": p["ref"],
                    })

    return issues


def main():
    if len(sys.argv) < 2:
        print("Usage: python integra_scanner.py <file1.py> [file2.py ...]")
        sys.exit(0)

    all_issues = []
    for filepath in sys.argv[1:]:
        if filepath.endswith(".py"):
            all_issues.extend(scan_file(filepath))

    if not all_issues:
        print("✅ No known bug patterns detected.")
        sys.exit(0)

    # Group by severity
    critical = [i for i in all_issues if i["severity"] == "CRITICAL"]
    high = [i for i in all_issues if i["severity"] == "HIGH"]
    medium = [i for i in all_issues if i["severity"] == "MEDIUM"]

    print(f"\n{'='*60}")
    print(f"  INTEGRA Quality Scanner Results")
    print(f"  {len(critical)} Critical | {len(high)} High | {len(medium)} Medium")
    print(f"{'='*60}\n")

    for issue in all_issues:
        icon = "🔴" if issue["severity"] == "CRITICAL" else "🟡" if issue["severity"] == "HIGH" else "🟠"
        print(f"{icon} [{issue['severity']}] {issue['name']}")
        print(f"   File: {issue['file']}:{issue['line']}")
        print(f"   Code: {issue['code']}")
        print(f"   Fix:  {issue['message']}")
        print(f"   Ref:  {issue['ref']}")
        print()

    # Exit with error if critical issues found
    if critical:
        print("🛑 CRITICAL issues found - must fix before proceeding!")
        sys.exit(1)
    elif high:
        print("⚠️  HIGH severity issues found - strongly recommended to fix.")
        sys.exit(0)
    else:
        print("ℹ️  Medium issues found - review when convenient.")
        sys.exit(0)


if __name__ == "__main__":
    main()
