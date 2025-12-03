---
name: review
description: Route code review to local LLM via LiteLLM with grades, risk assessment, and structured output
allowed-tools: Read, Bash, Grep, Glob, mcp__serena__write_memory, mcp__serena__read_memory, mcp__serena__list_memories
argument-hint: "[model] [focus-prompt] — models: qwen (bugs), deepseek (architecture), glm (standards)"
---

# Code Review via LiteLLM

Route a comprehensive code review to a local LLM model via LiteLLM proxy.
Returns **graded assessment** with risk levels and actionable improvements.

**Arguments:** $ARGUMENTS

---

## Model Selection

| Alias | LiteLLM Model | Specialty | Best For |
|-------|---------------|-----------|----------|
| `qwen` | `coding-qwen` | Code quality, bugs | Memory safety, logic errors, buffer overflows |
| `deepseek` | `architecture-deepseek` | Architecture | Module coupling, design patterns, abstraction |
| `glm` | `tools-glm` | Standards | MISRA-C, coding standards, compliance |

**Default:** `qwen` if no model specified

---

## Step 1: Parse Arguments

From $ARGUMENTS, extract:
- **Model**: First word if it's `qwen`, `deepseek`, or `glm` — otherwise default to `qwen`
- **Focus**: Everything after the model (or entire string if no model specified)

Examples:
- `qwen memory safety audit` → model=qwen, focus="memory safety audit"
- `deepseek evaluate coupling` → model=deepseek, focus="evaluate coupling"
- `check for buffer overflows` → model=qwen (default), focus="check for buffer overflows"

---

## Step 2: Gather Code Context

Execute these bash commands:

```bash
# Create context
echo "=== REVIEW CONTEXT ==="
echo "Date: $(date)"
echo "Directory: $(pwd)"
echo ""
echo "=== GIT DIFF ==="
git diff HEAD~1..HEAD 2>/dev/null | head -200
echo ""
echo "=== FILES CHANGED ==="
git diff --name-only HEAD~1..HEAD 2>/dev/null
echo ""
echo "=== RECENT COMMITS ==="
git log --oneline -3 2>/dev/null
```

---

## Step 3: Check for Previous Lessons (Optional)

If Serena is available, check for relevant past reviews:
```
mcp__serena__list_memories
```

Look for `review-*.md` files that might contain relevant lessons.

---

## Step 4: Build Review Request

### System Prompt (Model-Specific)

**For QWEN (coding-qwen):**
```
You are an expert embedded systems code reviewer for Zephyr RTOS / nRF5340.

EXPERTISE: Memory safety, bug detection, defensive programming

REVIEW CHECKLIST:
- Buffer overflow vulnerabilities
- Null pointer dereferences
- Memory leaks (especially error paths)
- Integer overflow/underflow
- Race conditions in ISR context
- Incorrect volatile usage
- Stack overflow risks
- Resource cleanup failures

EMBEDDED PRINCIPLES:
- Every byte matters (static allocation only)
- Every cycle matters (profile first)
- Interrupts must be fast and safe
- Hardware can fail - code defensively
```

**For DEEPSEEK (architecture-deepseek):**
```
You are an expert firmware architect for Zephyr RTOS / nRF5340.

EXPERTISE: System design, module structure, API design

REVIEW CHECKLIST:
- Module boundaries and coupling
- Abstraction layers (HAL → Driver → Service → App)
- Dependency direction (inward, not circular)
- State management patterns
- Configuration design
- API consistency

ARCHITECTURE PRINCIPLES:
- Hardware abstraction enables portability
- Dependency injection enables testing
- Clear interfaces reduce coupling
- Event-driven where appropriate
```

**For GLM (tools-glm):**
```
You are an expert compliance reviewer for safety-critical embedded systems.

EXPERTISE: MISRA-C:2012, coding standards, safety analysis

REVIEW CHECKLIST:
- MISRA-C:2012 mandatory rule violations
- MISRA-C:2012 required rule violations
- Naming conventions
- Function complexity
- Dead/unreachable code
- Magic numbers

KEY MISRA RULES:
- 9.1: Variables initialized before use
- 17.2: No recursive functions
- 21.3: No dynamic memory
- 11.3: No pointer type casts
```

### User Prompt Template

```
REVIEW REQUEST
==============
Focus: [USER_FOCUS_PROMPT]

CODE CHANGES:
[GIT_DIFF_CONTENT]

FILES AFFECTED:
[FILE_LIST]

---

Provide a STRUCTURED REVIEW with these exact sections:

## Overall Grade: [A/B/C/D/F]
[Brief justification for grade]

## Risk Assessment
| Level | Score | Justification |
|-------|-------|---------------|
| Overall Risk | [CRITICAL/HIGH/MEDIUM/LOW] | [why] |
| Security Risk | [CRITICAL/HIGH/MEDIUM/LOW] | [why] |
| Stability Risk | [CRITICAL/HIGH/MEDIUM/LOW] | [why] |

## Critical Issues (MUST FIX - blocks merge)
| # | File:Line | Issue | Severity | Fix |
|---|-----------|-------|----------|-----|
| 1 | [location] | [description] | CRITICAL | [how to fix] |

## Warnings (SHOULD FIX)
| # | File:Line | Issue | Severity | Fix |
|---|-----------|-------|----------|-----|
| 1 | [location] | [description] | HIGH/MEDIUM | [how to fix] |

## Suggestions (NICE TO HAVE)
| # | File:Line | Suggestion | Benefit |
|---|-----------|------------|---------|
| 1 | [location] | [suggestion] | [why] |

## Code Practices Assessment
| Practice | Status | Notes |
|----------|--------|-------|
| Memory Safety | ✅/⚠️/❌ | [notes] |
| Error Handling | ✅/⚠️/❌ | [notes] |
| Naming Conventions | ✅/⚠️/❌ | [notes] |
| Documentation | ✅/⚠️/❌ | [notes] |
| Testability | ✅/⚠️/❌ | [notes] |

## Potential Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| [risk] | [High/Med/Low] | [High/Med/Low] | [how to mitigate] |

## Potential Improvements
| Priority | Improvement | Effort | Impact |
|----------|-------------|--------|--------|
| HIGH | [what to improve] | [hours] | [benefit] |

## Positive Observations
- [Good practice 1]
- [Good practice 2]

## Summary
[2-3 sentence summary of review findings and recommended actions]
```

---

## Step 5: Call LiteLLM API

Execute the review via curl:

```bash
# Set model based on selection (qwen/deepseek/glm)
MODEL="coding-qwen"  # or architecture-deepseek or tools-glm

curl -s http://localhost:4000/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "'$MODEL'",
    "messages": [
      {"role": "system", "content": "[SYSTEM_PROMPT_FOR_SELECTED_MODEL]"},
      {"role": "user", "content": "[USER_PROMPT_WITH_DIFF]"}
    ],
    "temperature": 0.3,
    "max_tokens": 4000
  }' | jq -r '.choices[0].message.content'
```

If the API fails, report:
- Check LiteLLM: `curl http://localhost:4000/health`
- Check models: `curl http://localhost:4000/models`

---

## Step 6: Display and Optionally Persist

### Display Results
Show the complete review report to the user.

### Optional: Save Review
If the user wants to save the review, call:
```
mcp__serena__write_memory
  memory_file_name: "code-review-YYYY-MM-DD-[model]-[short-focus].md"
  content: [The complete review output]
```

---

## Quick Reference

```bash
# Bug hunting
/sc:review qwen check for buffer overflows and null pointer issues

# Architecture review
/sc:review deepseek evaluate module coupling and abstraction quality

# Standards compliance
/sc:review glm MISRA-C:2012 compliance audit

# Default (qwen)
/sc:review look for memory safety issues
```

---

## Output Summary Format

After the review completes, summarize:

```
═══════════════════════════════════════════════════
REVIEW COMPLETE
═══════════════════════════════════════════════════
📊 Grade: [A-F]
⚠️  Risk Level: [CRITICAL/HIGH/MEDIUM/LOW]
🔴 Critical Issues: [count]
🟡 Warnings: [count]
🟢 Suggestions: [count]
✅ Positive Observations: [count]
═══════════════════════════════════════════════════
```
