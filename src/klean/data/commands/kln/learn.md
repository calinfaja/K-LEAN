---
name: learn
description: Extract and save learnings from current session context to Knowledge DB
---

You are a **knowledge curator** extracting reusable insights from this coding session.

## Focus Area
$ARGUMENTS

## Task

Scan the recent conversation context and extract learnings worth preserving to the Knowledge DB.

### Extraction Method (Two-Stage)

**Stage 1 - Identify candidates.** For each potential learning, ask:
1. **Grounding test**: Can I point to a specific file, function, error message, or config that this is about? If not, discard.
2. **Counterfactual test**: Would a competent developer who just joined this project already know this? If yes, discard.
3. **Transferability test**: Would this be useful in a different session on this same project? If no, discard.

**Stage 2 - Synthesize.** For each surviving candidate, write a grounded entry:
- Title must name the specific thing (function, file, tool, API, config)
- Insight must include the concrete detail (the error, the fix, the value, the flag)
- Source must point to a real location (file:path:line, git:hash, url)

### What to Capture:
- Bugs found and their **specific** root causes
- Fixes that worked: what was wrong, what fixed it, why
- Undocumented behaviors with **reproduction steps**
- Integration gotchas with **specific versions/configs**
- API quirks or edge cases with **exact parameters**

### What to DISCARD (Mandatory):
- Generic advice ("write tests", "use good names", "follow best practices")
- Session logistics ("session started", "worked on X today", "spent time on")
- Obvious/well-documented behaviors (things in official docs)
- Vague observations without specific grounding ("the system is complex")
- Documentation references (these are already on the web)
- Anything that fails the three tests above

### Entry Types:
| Type | Content Signals |
|------|----------------|
| `warning` | "don't", "avoid", "never", "careful", "bug", "fails", "gotcha" |
| `solution` | "fixed by", "solved with", "workaround", "the fix was" |
| `pattern` | "use X for Y", "prefer", "approach", "technique" |
| `decision` | "chose X over Y", "trade-off", "decided because" |
| `discovery` | "found that", "turns out", "surprisingly", "undocumented" |
| `finding` | Default - specific behavior, API quirk, edge case |

### Priority Levels:
| Priority | When to Use |
|----------|-------------|
| `critical` | Will cause data loss or major breakage if forgotten |
| `high` | Frequently relevant, saves significant debugging time |
| `medium` | Useful, occasionally relevant |
| `low` | Edge case, nice to know |

### Output Flow:

1. **Present findings** for user review:
```
Found N learnings to save:

1. [type] Title
   Insight: 2-4 sentences with specific details and grounding
   Keywords: keyword1, keyword2, keyword3
   Source: file:path.py:42
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
      "title": "Short descriptive title naming the specific thing (max 80 chars)",
      "insight": "2-4 sentences. MUST include: what specifically happened, why, and the concrete detail (error message, config value, function name). 50-150 words.",
      "type": "warning|solution|pattern|finding|decision|discovery",
      "priority": "critical|high|medium|low",
      "keywords": ["specific-tool", "specific-function", "3-5-terms"],
      "source": "file:path/to/file.py:42 or git:hash or conv:YYYY-MM-DD"
    }' --json
```

4. **Confirm** what was saved with total count.

### If No Focus Provided ($ARGUMENTS is empty):
Auto-detect learnings from the last 10-20 exchanges in conversation context.
Look for:
- Error messages that were resolved
- Things that "finally worked" after debugging
- Corrections to initial assumptions
- Surprising behaviors discovered

### Example Learnings:

**Good** (specific, grounded, actionable):
```json
{
  "title": "LiteLLM thinking models use reasoning_content field",
  "insight": "DeepSeek, GLM, Minimax, and Kimi models return responses in reasoning_content instead of content field. Always check both fields when parsing LiteLLM responses. This caused review aggregation to silently drop thinking model outputs in reviews.py:142.",
  "type": "warning",
  "priority": "high",
  "keywords": ["thinking-models", "litellm", "reasoning_content", "response-parsing"],
  "source": "file:src/klean/reviews.py:142"
}
```

**Bad** (generic, ungrounded - would be DISCARDED):
- "Always test your code" (generic advice)
- "Documentation: MDN - Array methods" (web reference)
- "Worked on the knowledge system today" (session log)
- "The codebase is complex" (vague observation)

## Notes
- Can be run multiple times during a session
- For end-of-session comprehensive capture, use /kln:remember instead
