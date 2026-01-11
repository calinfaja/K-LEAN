---
name: remember
description: "Reviews git status/diff/log, extracts learnings by category, saves to Knowledge DB, appends index to Serena. Use at session end before /clear."
allowed-tools: Bash, Read, Grep, mcp__serena__read_memory, mcp__serena__edit_memory
argument-hint: "[optional focus area]"
---

# /kln:remember - End-of-Session Knowledge Capture

Comprehensive extraction and saving of session learnings before clearing context.

## When to Use

- End of productive session, before `/clear` or `/compact`
- After solving tricky problems worth remembering
- Before closing a long debugging session

**NOT for:**
- Mid-session learnings → use `/kln:learn` instead
- Code review → use `/kln:quick`, `/kln:multi`, or `/kln:agent`

## Why This Works (Research-Backed)

Based on cognitive science research:
- **Spaced Retrieval** (Cohen's d = 0.38-1.41): Summaries trigger active recall
- **Progressive Summarization**: Hub notes index atomic entries
- **Zettelkasten Method**: Atomic notes (KB) linked from index (Serena)
- **Cognitive Load Theory**: Short summaries reduce mental overhead

## Process

### Step 1: Review Session Accomplishments

```bash
git status
git diff --stat
git log --oneline -5
```

### Step 2: Extract Learnings by Category

| Category | What to Capture |
|----------|-----------------|
| **Warnings** | Problems encountered, gotchas, things to AVOID |
| **Solutions** | Working fixes, workarounds that resolved issues |
| **Patterns** | Reusable approaches, design decisions with rationale |
| **Findings** | Undocumented behavior, API quirks, edge cases |

### Step 3: Save to Knowledge DB (V3 Schema)

**Path**: Use `~/.venvs/knowledge-db/bin/python` (Unix) or `~/.venvs/knowledge-db/Scripts/python.exe` (Windows).

For each significant learning:

```bash
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-capture.py \
    --json-input '{
      "title": "Short descriptive title (max 80 chars)",
      "insight": "2-4 sentence explanation. Be specific. 50-150 words.",
      "type": "warning|solution|pattern|finding",
      "priority": "critical|high|medium|low",
      "keywords": ["keyword1", "keyword2", "keyword3"],
      "source": "file:path.py:42 or git:hash or conv:YYYY-MM-DD"
    }' --json
```

**Note**: `type` is auto-inferred from content if omitted (detects warning/solution/pattern signals).

**Track what you save** for the Serena summary:
- Count entries by type (warnings, patterns, solutions, findings)
- Collect all unique keywords
- Identify the single most important insight

### Step 4: Generate Auto-Summary for Serena

**This is the key step that links KB entries to Serena for future retrieval.**

Use `mcp__serena__edit_memory` to append to `lessons-learned.md`:

```markdown
---

### Remember: YYYY-MM-DD HH:MM
**Topics**: keyword1, keyword2, keyword3
**Captured**: N KB entries (X warnings, Y patterns, Z solutions)
**Key insight**: [One sentence - the most important thing learned]
> Search KB: "keyword1" "keyword2" "keyword3"
```

**Why this format works:**
- **Topics**: Enable future keyword search in Serena
- **Captured count**: Know something exists without reading all
- **Key insight**: Triggers spaced retrieval (forces recall)
- **Search KB line**: Direct prompts for FindKnowledge in next session

### Step 5: Verify and Clear

1. **Verify KB saves**: `FindKnowledge <topic>`
2. **Check Serena**: `mcp__serena__read_memory lessons-learned`
3. **Clear when ready**: `/compact` or `/clear`

## Example Output

```
/kln:remember

Reviewing session...
Git: 6 files changed, 3 commits

Extracting learnings...

**Warnings (2):**
- SessionStart hook needs BOTH startup+resume matchers
- Cross-platform paths differ between Windows/Linux/macOS

**Patterns (2):**
- Per-project KB servers with TCP port (14000 + hash offset)
- Python entry points work cross-platform via pipx

**Solutions (1):**
- `kln doctor -f` diagnoses and auto-repairs KB issues

Saving to Knowledge DB...
[OK] Saved 5 entries

Generating Serena summary...
[OK] Appended to lessons-learned.md

---
### Remember: 2026-01-11 15:45
**Topics**: hooks, knowledge-db, session-start, cross-platform
**Captured**: 5 KB entries (2 warnings, 2 patterns, 1 solution)
**Key insight**: SessionStart hook needs both startup+resume matchers for --resume to work
> Search KB: "SessionStart" "cross-platform" "kb-doctor"
---

Session learnings captured. Ready for /clear.
```

## Next Session

When you start a new session, Serena context is injected. You'll see:

```
> Search KB: "SessionStart" "cross-platform" "kb-doctor"
```

Use `FindKnowledge <keyword>` to retrieve the full atomic entries from KB.

The summary acts as an **index** - you know WHAT was captured and WHERE to find details.
