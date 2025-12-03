---
name: backgroundReviewDoc
description: "Spawn createReviewDoc in a SEPARATE context window (subagent)"
allowed-tools: Task
argument-hint: "[session-title]"
---

# Background Review Document (Subagent)

Spawns a **separate Claude instance** to create and persist a review document.
Your main session stays free - the subagent does the work in its own context.

**Session Title:** $ARGUMENTS

---

## How It Works

```
YOUR SESSION                    SUBAGENT (separate context)
     │                                │
     │ ──► Task tool ───────────────► │ New Claude instance
     │                                │ • Has own token budget
     │     (you continue working)     │ • Runs createReviewDoc
     │                                │ • Persists to Serena
     │ ◄── Returns summary ◄───────── │
     │                                │
```

---

## Execute Now

Call the **Task tool** with these exact parameters:

**subagent_type:** `general-purpose`

**description:** `Create review document`

**prompt:**
```
You are a documentation agent creating a session review document.

WORKING DIRECTORY: Use the current directory from your environment.

## Step 1: Gather Context

Run these bash commands:
```bash
echo "=== GIT STATUS ===" && git status --porcelain 2>/dev/null | head -15
echo "=== RECENT COMMITS ===" && git log --oneline -5 2>/dev/null
echo "=== CHANGES SUMMARY ===" && git diff --stat HEAD~3 2>/dev/null | tail -10
echo "=== PROJECT CONFIG ===" && cat prj.conf 2>/dev/null | head -20
```

## Step 2: Check Serena Memories

Call mcp__serena__list_memories to see existing project context.

## Step 3: Create Review Document

Generate a markdown document with this structure:

# Session Review: SESSION_TITLE_HERE

| Field | Value |
|-------|-------|
| Date | [current date/time] |
| Project | [from git/directory] |

## Executive Summary
[2-3 sentences on what was accomplished]

## Quality Assessment
### Overall Grade: [A/B/C/D/F]
| Category | Score | Notes |
|----------|-------|-------|
| Code Quality | X/10 | [note] |
| Memory Safety | X/10 | [note] |
| Error Handling | X/10 | [note] |

### Risk Level: [CRITICAL/HIGH/MEDIUM/LOW]

## Changes Made
[List files and changes from git]

## Lessons Learned
### Patterns (Reuse)
- **[PATTERN]** `name`: description

### Gotchas (Avoid)
- **[GOTCHA]** `name`: description

## Open Items
- [ ] [TODO items]

---

## Step 4: PERSIST (CRITICAL)

You MUST call mcp__serena__write_memory with:
- memory_file_name: "review-YYYY-MM-DD-[slug-from-title].md"
- content: [The complete markdown document]

## Step 5: Return Summary

After saving, return a brief summary:
- Document saved: [filename]
- Grade: [A-F]
- Risk: [level]
- Key findings: [1-2 bullets]

SESSION TITLE: $ARGUMENTS
```

---

## After Execution

The subagent will return a summary. Your main session continues with minimal token usage.

The full document is persisted in Serena memories - retrieve with:
```
mcp__serena__list_memories
mcp__serena__read_memory with memory_file_name: "review-..."
```

---

## Usage

```bash
/kln:backgroundReviewDoc Secure Boot Implementation
/kln:backgroundReviewDoc BLE Stack Refactor
/kln:backgroundReviewDoc Power Optimization Phase 1
```
