---
name: doc
description: "Generates session documentation (report/session/lessons types) and persists to Serena memory via mcp__serena__write_memory. Optionally saves to /tmp/claude-reviews/docs/. Use to document completed work."
allowed-tools: Bash, Read, Write, mcp__serena__write_memory
argument-hint: "[--type TYPE] <title>"
---

# /kln:doc - Session Documentation

Create comprehensive session documentation and persist to Serena memories.

## When to Use

- Document significant work for future reference
- Create reports for teammates or stakeholders
- Generate session summary before switching tasks
- Persist important decisions to Serena memory

**NOT for:**
- End-of-session knowledge capture with KB → use `/kln:remember`
- Mid-session learnings → use `/kln:learn`
- Code review documentation → use `/kln:agent` for detailed review

## Arguments

$ARGUMENTS

## Flags

- `--type, -t` - Document type: report (default), session, lessons
- `--async, -a` - Run in background

## Document Types

| Type | Purpose | Output |
|------|---------|--------|
| `report` | Comprehensive session report | Serena memory + file |
| `session` | Quick session summary | Serena memory |
| `lessons` | Extract lessons learned | Knowledge DB + memory |

## Execution

### For type=report (default):

Create a comprehensive document with:
1. Session overview and objectives
2. Work completed (from conversation context)
3. Key decisions made
4. Code changes summary
5. Issues encountered and solutions
6. Next steps and recommendations

Save to Serena memory with name: `session-{title}-{date}`

### For type=session:

Quick summary:
1. Main accomplishments
2. Files modified
3. Outstanding items

### For type=lessons:

Extract and save lessons learned:
1. What worked well
2. What didn't work
3. Patterns discovered
4. Gotchas encountered

Use `/kln:learn` for knowledge DB integration.

## Output

1. Display the document to user
2. Save to Serena memory using mcp__serena__write_memory
3. Optionally save to file: `/tmp/claude-reviews/docs/{title}-{date}.md`

## Examples

```
/kln:doc BLE Implementation Complete
/kln:doc --type session Quick summary
/kln:doc --type lessons Today's learnings
/kln:doc -a Background documentation
```
