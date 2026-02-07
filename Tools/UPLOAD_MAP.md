# خريطة رفع الملفات على GitHub
# كل ملف والمسار بتاعه في الـ Repo

## ارفعهم بالترتيب ده على main:

| # | الملف | المسار في الـ Repo | الوظيفة |
|---|-------|-------------------|---------|
| 1 | CLAUDE.md | `CLAUDE.md` | القواعد الـ 13 الإلزامية |
| 2 | settings.json | `.claude/settings.json` | الـ Hooks التلقائية |
| 3 | integra-auditor.md (agents) | `.claude/agents/integra-auditor.md` | المدقق الداخلي |
| 4 | audit.md | `.claude/commands/audit.md` | أمر /audit |
| 5 | audit-security.md | `.claude/commands/audit-security.md` | أمر /audit-security |
| 6 | audit-threads.md | `.claude/commands/audit-threads.md` | أمر /audit-threads |
| 7 | audit-architecture.md | `.claude/commands/audit-architecture.md` | أمر /audit-architecture |
| 8 | quick-check.md | `.claude/commands/quick-check.md` | أمر /quick-check |
| 9 | pre-task.md | `.claude/commands/pre-task.md` | أمر /pre-task |
| 10 | SKILL.md | `.claude/skills/integra-auditor/SKILL.md` | قاعدة معرفة الـ 92 خطأ |
| 11 | integra_scanner.py | `scripts/integra_scanner.py` | سكانر الأنماط الخطيرة |
| 12 | mypy.ini | `mypy.ini` | إعدادات فحص الأنواع |
| 13 | .pylintrc | `.pylintrc` | إعدادات فحص الكود |

## بعد الرفع:

```bash
# في VS Code Terminal
git pull origin main

# افتح Claude Code
claude

# جرب
/hooks        ← لازم تشوف 3 hooks
/audit        ← تدقيق شامل
```
