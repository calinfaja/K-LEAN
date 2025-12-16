## Output Format

Respond with this structure:

```
GRADE: [A|B|C|D|F]
(1-2 sentence justification)

RISK: [LOW|MEDIUM|HIGH|CRITICAL]

CRITICAL ISSUES:
- [severity] file:line - Issue description
  Evidence: [code snippet or reasoning]
  Fix: [specific suggestion]

HIGH ISSUES:
- [list if any, or "None"]

WARNINGS:
- [list medium-priority concerns]

SUGGESTIONS:
- [list optional improvements]

SUMMARY:
[2-3 sentence summary of findings and recommended action]
```
