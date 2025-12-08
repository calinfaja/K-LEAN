---
name: createReport
description: Create and PERSIST comprehensive session documentation
allowed-tools: Read, Bash, Grep, Glob, mcp__serena__write_memory, mcp__serena__list_memories
argument-hint: "[session-title]"
---

# Create Report - Session Documentation

Generate and **PERSIST** a structured documentation report for the current development session.

**Session Title:** $ARGUMENTS

---

## Purpose

| Command | Purpose | Output |
|---------|---------|--------|
| `/kln:quickReview` | Find issues | Grade, Issues |
| `/kln:quickConsult` | Challenge decisions | Verdict, Alternatives |
| **`/kln:createReport`** | **Capture knowledge** | **Lessons, Decisions, TODOs** |

---

## CRITICAL: This command MUST persist data

**YOU MUST call `mcp__serena__write_memory` at the end to save the document.**

If Serena has no active project, inform the user to activate one first.

---

## Step 1: Gather Context

```bash
echo "=== PROJECT DETECTION ==="
ls prj.conf Kconfig CMakeLists.txt 2>/dev/null | head -3

echo "=== GIT STATUS ==="
git status --porcelain 2>/dev/null | head -15

echo "=== RECENT COMMITS ==="
git log --oneline -5 2>/dev/null

echo "=== CHANGES SUMMARY ==="
git diff --stat HEAD~3 2>/dev/null | tail -10

echo "=== CONFIG CHANGES ==="
git diff HEAD~3 -- prj.conf 2>/dev/null | grep "^[+-]CONFIG" | head -15
```

---

## Step 2: Generate Report

### System Prompt (DOCUMENT)

```
You are a technical documentation specialist capturing development session outcomes.

DOCUMENTATION GOALS:
- Capture WHAT was done and WHY
- Record decisions and their rationale
- Note lessons learned (what worked, what didn't)
- Identify follow-up items and risks
- Create searchable, reusable knowledge

FOCUS ON FUTURE USEFULNESS:
- Make lessons searchable with clear keywords
- Be specific about what worked and why
- Capture context that won't be obvious later
```

### Output Template

```markdown
# Session: [SESSION_TITLE]

| Field | Value |
|-------|-------|
| **Date** | YYYY-MM-DD HH:MM |
| **Project** | [from directory/git] |
| **Session ID** | [short-uuid] |

---

## Summary
[2-3 sentences: What was accomplished, key outcome]

---

## Changes Made

### Files Modified
| File | Change | Impact |
|------|--------|--------|

### CONFIG Changes (if applicable)
| Config | Value | Reason |
|--------|-------|--------|

---

## Technical Decisions
| Decision | Rationale | Alternatives Considered |
|----------|-----------|------------------------|

---

## Lessons Learned

### What Worked Well
- **[PATTERN]** `pattern-name`: [description]

### What to Avoid
- **[GOTCHA]** `gotcha-name`: [description]

### Tips
- **[TIP]** `tip-name`: [description]

---

## Quality Assessment
| Category | Score | Notes |
|----------|-------|-------|
| Code Quality | X/10 | |
| Memory Safety | X/10 | |
| Error Handling | X/10 | |
| Documentation | X/10 | |

---

## Risks & Follow-ups
| Priority | Item | Action Needed |
|----------|------|---------------|
| HIGH/MED/LOW | [item] | [action] |

---

## Open Items
- [ ] [TODO 1]
- [ ] [TODO 2]
```

---

## Step 3: PERSIST THE DOCUMENT (MANDATORY)

**YOU MUST EXECUTE THIS:**

```
mcp__serena__write_memory
  memory_file_name: "session-YYYY-MM-DD-[slug-from-title].md"
  content: [The complete markdown document]
```

Example filename: `session-2025-12-08-ble-optimization.md`

---

## Step 4: Confirm to User

After successful save:

```
═══════════════════════════════════════════════════════════════
REPORT SAVED
═══════════════════════════════════════════════════════════════
File: session-YYYY-MM-DD-[slug].md
Quality: X/10
Lessons: [count]
TODOs: [count]
Risks: [count]
═══════════════════════════════════════════════════════════════
```

---

## Usage

```bash
# After completing a feature
/kln:createReport BLE Pairing Implementation

# After debugging session
/kln:createReport Fixed Crypto Memory Leak

# After optimization work
/kln:createReport Power Optimization Phase 1
```

---

## Verify Saved

Use `mcp__serena__list_memories` to verify the document was saved.
