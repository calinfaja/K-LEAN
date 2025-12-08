---
name: createReviewDoc
description: Create and PERSIST comprehensive session review documentation with grades and risk assessment
allowed-tools: Read, Bash, Grep, Glob, mcp__serena__write_memory, mcp__serena__list_memories
argument-hint: "[session-title]"
---

# Create Review Document (Persisted)

Generate and **PERSIST** a structured review document for the current development session.

**Session Title:** $ARGUMENTS

---

## CRITICAL: This command MUST persist data

**YOU MUST call `mcp__serena__write_memory` at the end to save the document.**

If Serena has no active project, inform the user to activate one first:
```
mcp__serena__activate_project with project: "zephyr" (or appropriate project)
```

---

## Step 1: Gather Context

Run these bash commands to gather project state:

```bash
echo "=== PROJECT DETECTION ===" && ls prj.conf Kconfig CMakeLists.txt 2>/dev/null | head -3
echo "=== GIT STATUS ===" && git status --porcelain 2>/dev/null | head -15
echo "=== RECENT COMMITS ===" && git log --oneline -5 2>/dev/null
echo "=== CHANGES SUMMARY ===" && git diff --stat HEAD~3 2>/dev/null | tail -10
echo "=== CONFIG CHANGES ===" && git diff HEAD~3 -- prj.conf 2>/dev/null | grep "^[+-]CONFIG" | head -15
```

---

## Step 2: Generate Review Document

Create a markdown document with this **exact structure**:

```markdown
# Session Review: [SESSION_TITLE]

| Field | Value |
|-------|-------|
| **Date** | YYYY-MM-DD HH:MM |
| **Project** | [from directory/git] |
| **Target** | [from prj.conf BOARD=] |
| **Session ID** | [short-uuid] |

---

## Executive Summary

[2-3 sentences: What was accomplished, key outcome, any blockers]

---

## Quality Assessment

### Overall Grade: [A/B/C/D/F]

| Category | Score | Notes |
|----------|-------|-------|
| Code Quality | X/10 | [brief note] |
| Memory Safety | X/10 | [brief note] |
| Error Handling | X/10 | [brief note] |
| Documentation | X/10 | [brief note] |
| Test Coverage | X/10 | [brief note] |

### Risk Level: [CRITICAL / HIGH / MEDIUM / LOW]

**Risk Factors:**
- [Risk 1 with severity]
- [Risk 2 with severity]

---

## Changes Made

### Files Modified
| File | Change | Impact |
|------|--------|--------|
| path/file.c | Added/Modified | [High/Med/Low] |

### CONFIG Changes (Zephyr)
| Config | Value | Reason |
|--------|-------|--------|
| CONFIG_XXX | y | [why] |

---

## Implementation Details

### Steps Taken
1. [Step 1]
2. [Step 2]

### Technical Decisions
- **Decision:** [what] | **Rationale:** [why] | **Alternatives:** [considered]

---

## Lessons Learned

### Patterns (Reuse These)
- **[PATTERN]** `pattern-name`: [description]

### Gotchas (Avoid These)
- **[GOTCHA]** `gotcha-name`: [description]

### Tips
- **[TIP]** `tip-name`: [description]

---

## Potential Improvements

| Priority | Improvement | Effort | Impact |
|----------|-------------|--------|--------|
| HIGH | [improvement 1] | [hours] | [benefit] |
| MEDIUM | [improvement 2] | [hours] | [benefit] |

---

## Potential Risks

| Severity | Risk | Mitigation |
|----------|------|------------|
| CRITICAL | [risk description] | [how to mitigate] |
| HIGH | [risk description] | [how to mitigate] |

---

## Code Practices Evaluation

### Followed Best Practices
- [x] [Practice 1]
- [x] [Practice 2]

### Needs Improvement
- [ ] [Practice that wasn't followed]

### Embedded-Specific Checklist
- [ ] Static allocation only (no malloc)
- [ ] Interrupt-safe code (volatile, atomics)
- [ ] Bounded execution time
- [ ] Power-aware implementation
- [ ] Error paths tested

---

## Open Items

- [ ] [TODO 1]
- [ ] [TODO 2]

---

## Related Documents
- Previous: [link if known]
- Next steps: [what comes next]
```

---

## Step 3: PERSIST THE DOCUMENT (MANDATORY)

**YOU MUST EXECUTE THIS:**

Call `mcp__serena__write_memory` with:
- **memory_file_name:** `review-YYYY-MM-DD-[slug-from-title].md`
- **content:** The complete markdown document above

Example filename: `review-2025-12-02-secure-boot-impl.md`

---

## Step 4: Confirm to User

After successful save, report:
1. ✅ Document saved: `[filename]`
2. 📊 Grade: [A-F]
3. ⚠️ Risk Level: [CRITICAL/HIGH/MEDIUM/LOW]
4. 📝 Lessons captured: [count]
5. 🔧 Improvements suggested: [count]

---

## Example Usage

```
/kln:createReport Secure Boot Implementation
/kln:createReport BLE Stack Integration
/kln:createReport Power Optimization Phase 1
```

**After running:** Use `mcp__serena__list_memories` to verify the document was saved.
