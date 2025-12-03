---
name: asyncReviewDoc
description: "Run /sc:createReviewDoc in a SEPARATE subagent - you can keep working!"
allowed-tools: Task
argument-hint: "[session-title] — Creates and persists doc in background subagent"
---

# Async Review Document (Subagent)

Runs `/sc:createReviewDoc` in a **separate subagent context**.
Creates and **persists** documentation while you keep working.

**Arguments:** $ARGUMENTS

---

## Execute Now

Use the **Task tool** with:

**subagent_type:** `general-purpose`

**description:** `Async review document creation`

**prompt:**
```
You are creating a session review document in the background.

SESSION TITLE: $ARGUMENTS

## Step 1: Gather Context

Run these bash commands:
```bash
echo "=== GIT STATUS ===" && git status --porcelain 2>/dev/null | head -15
echo "=== RECENT COMMITS ===" && git log --oneline -5 2>/dev/null
echo "=== CHANGES SUMMARY ===" && git diff --stat HEAD~3 2>/dev/null | tail -10
echo "=== PROJECT CONFIG ===" && cat prj.conf 2>/dev/null | head -20
echo "=== CONFIG CHANGES ===" && git diff HEAD~3 -- prj.conf 2>/dev/null | grep "^[+-]CONFIG" | head -10
```

## Step 2: Check Serena

Call mcp__serena__list_memories to see existing context.

## Step 3: Create Review Document

Generate markdown with this structure:

# Session Review: [SESSION_TITLE]

| Field | Value |
|-------|-------|
| **Date** | [current datetime] |
| **Project** | [from git/directory] |
| **Target** | [from prj.conf BOARD=] |

## Executive Summary
[2-3 sentences on accomplishments]

## Quality Assessment
### Overall Grade: [A/B/C/D/F]
| Category | Score | Notes |
|----------|-------|-------|
| Code Quality | X/10 | [note] |
| Memory Safety | X/10 | [note] |
| Error Handling | X/10 | [note] |

### Risk Level: [CRITICAL/HIGH/MEDIUM/LOW]

## Changes Made
[List from git diff]

## Lessons Learned
### Patterns (Reuse)
- **[PATTERN]** `name`: description

### Gotchas (Avoid)
- **[GOTCHA]** `name`: description

## Open Items
- [ ] [TODO items]

## Step 4: PERSIST (CRITICAL)

You MUST call mcp__serena__write_memory with:
- memory_file_name: "review-YYYY-MM-DD-[slug].md"
- content: [The complete document]

## Step 5: Return Confirmation

```
═══════════════════════════════════════════════════
ASYNC REVIEW DOC COMPLETE
═══════════════════════════════════════════════════
✅ Document saved: review-YYYY-MM-DD-[slug].md
📊 Grade: [A-F]
⚠️  Risk: [level]
📝 Lessons captured: [count]
🔧 Improvements: [count]
📋 Open items: [count]
═══════════════════════════════════════════════════

To read the full document:
mcp__serena__read_memory with memory_file_name: "[filename]"
```

SESSION TITLE: $ARGUMENTS
```
