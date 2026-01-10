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

### For Each Learning, Determine Type:
| Type | When to Use |
|------|-------------|
| `solution` | Fixed a specific problem |
| `warning` | Don't do this / watch out for |
| `pattern` | Reusable approach that worked |
| `finding` | Discovered behavior (API, library, tool) |
| `lesson` | General insight from experience |
| `best-practice` | Proven approach worth repeating |

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
   Description of the insight
   Atomic insight: One-sentence takeaway
   Source: file.py:42 (if from a specific file)
   Tags: tag1, tag2

2. [type] Title
   ...
```

2. **Ask for confirmation**: "Save all? [Y/n/edit]"

3. **Save each** using knowledge-capture.py with V2 schema (JSON input):
```bash
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-capture.py \
    --json-input '{
      "title": "Short descriptive title",
      "summary": "Detailed description of the insight",
      "atomic_insight": "One-sentence actionable takeaway",
      "type": "solution|warning|pattern|finding|lesson|best-practice",
      "priority": "critical|high|medium|low",
      "tags": ["tag1", "tag2"],
      "key_concepts": ["searchable", "terms"],
      "source": "conversation",
      "source_path": "path/to/file.py:42"
    }' --json
```

**IMPORTANT - Include These Fields:**
- `atomic_insight`: Always generate a single-sentence, actionable takeaway
- `source_path`: Include `file:line` if the learning came from a specific file
- `key_concepts`: Extract 3-5 searchable terms for better retrieval

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
- "Thinking models (deepseek, glm, minimax, kimi) return responses in reasoning_content field instead of content"
- "knowledge-capture.py takes content as first positional arg, not 'add' subcommand"
- "LiteLLM model_name must match exactly what proxy returns in response"

**Bad** (too generic):
- "Always test your code"
- "Read the documentation"
- "Use meaningful variable names"

## Notes
- This command replaces the old `SaveThis` hook keyword
- Unlike SaveThis (literal text only), /kln:learn has full conversation context
- Can be run multiple times during a session
- For end-of-session comprehensive capture, use /kln:remember instead
