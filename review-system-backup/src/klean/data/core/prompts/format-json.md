## Output Format

Respond ONLY with valid JSON (no markdown, no explanation before or after):

```json
{
  "grade": "A|B|C|D|F",
  "grade_rationale": "1-2 sentence justification",
  "risk": "LOW|MEDIUM|HIGH|CRITICAL",
  "findings": [
    {
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "category": "CORRECTNESS|MEMORY_SAFETY|ERROR_HANDLING|CONCURRENCY|ARCHITECTURE|SECURITY|STANDARDS",
      "location": "file:line",
      "issue": "description of the problem",
      "evidence": "code snippet or reasoning that proves it",
      "fix": "specific actionable suggestion"
    }
  ],
  "summary": "2-3 sentence summary"
}
```

IMPORTANT:
- Return ONLY the JSON object, nothing else
- All findings must have location, evidence, and fix
- Empty findings array if no issues found
- Grade rationale explains the grade choice
