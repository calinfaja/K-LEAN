---
name: learn
description: Extract and save learnings from current session context to Knowledge DB
---

You are a **knowledge curator** extracting reusable insights from this coding session.

## Focus Area
$ARGUMENTS

## Task

Scan the recent conversation context and extract learnings worth preserving to the Knowledge DB.

### What to Look For:
- Bugs found and their root causes
- Fixes that worked (and why)
- Undocumented behaviors discovered
- Integration patterns that succeeded
- Gotchas and warnings
- Relevant info from research/web searches
- API quirks or edge cases

### Quality Filters (IMPORTANT):
- **SKIP** generic advice ("write tests", "use good names", "follow best practices")
- **SKIP** session-specific details (temp paths, local variable names, timestamps)
- **SKIP** obvious/well-documented behaviors
- **PRIORITIZE** surprising discoveries, non-obvious fixes, gotchas, undocumented behavior

### Entry Types (auto-inferred from content):
| Type | Content Signals |
|------|----------------|
| `warning` | "don't", "avoid", "never", "careful", "bug", "fails", "gotcha" |
| `solution` | "fixed", "solved", "workaround", "the fix was" |
| `pattern` | "use X for Y", "prefer", "best way", "approach" |
| `finding` | Default - discovered behavior, API quirk, etc. |

### Priority Levels:
| Priority | When to Use |
|----------|-------------|
| `critical` | Will cause major issues if forgotten |
| `high` | Important, frequently relevant |
| `medium` | Useful, occasionally relevant |
| `low` | Nice to know, edge case |

### Output Flow:

1. **Present findings** for user review:
```
Found N learnings to save:

1. [type] Title
   Insight: 2-4 sentence explanation with specific details
   Keywords: keyword1, keyword2, keyword3
   Source: file.py:42 or https://... or conv:YYYY-MM-DD
   Priority: high

2. [type] Title
   ...
```

2. **Ask for confirmation**: "Save all? [Y/n/edit]"

3. **Save each** using knowledge-capture.py with V3 schema (JSON input):

**Path**: Use `~/.venvs/knowledge-db/bin/python` (Unix) or `~/.venvs/knowledge-db/Scripts/python.exe` (Windows).

```bash
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-capture.py \
    --json-input '{
      "title": "Short descriptive title (max 80 chars)",
      "insight": "2-4 sentence explanation. Be specific about what, why, and how. Include enough context for future retrieval. 50-150 words.",
      "type": "warning|solution|pattern|finding",
      "priority": "critical|high|medium|low",
      "keywords": ["searchable", "terms", "3-5"],
      "source": "file:path/to/file.py:42 or https://url or git:hash or conv:YYYY-MM-DD"
    }' --json
```

**V3 Schema Fields:**
| Field | Description |
|-------|-------------|
| `title` | Short descriptive title (max 80 chars) |
| `insight` | 2-4 sentence explanation with actionable details (50-150 words) |
| `type` | Auto-inferred: warning, solution, pattern, finding |
| `priority` | critical, high, medium, low |
| `keywords` | 3-5 searchable terms |
| `source` | Actionable source: file:path:line, https://url, git:hash, conv:date |

4. **Confirm** what was saved with total count.

### If No Focus Provided ($ARGUMENTS is empty):
Auto-detect learnings from the last 10-20 exchanges in conversation context.
Look for:
- Error messages that were resolved
- "Aha!" moments in the discussion
- Things that "finally worked"
- Corrections to initial assumptions

### Example Learnings:

**Good** (specific, actionable):
```json
{
  "title": "Thinking models use reasoning_content field",
  "insight": "DeepSeek, GLM, Minimax, and Kimi models return responses in reasoning_content instead of content field. Always check both fields when parsing responses. This affected our review aggregation where thinking model outputs were silently dropped.",
  "type": "warning",
  "priority": "high",
  "keywords": ["thinking-models", "litellm", "reasoning_content", "response-parsing"],
  "source": "file:src/klean/reviews.py:142"
}
```

**Bad** (too generic):
- "Always test your code"
- "Read the documentation"
- "Use meaningful variable names"

## Notes
- Can be run multiple times during a session
- For end-of-session comprehensive capture, use /kln:remember instead
