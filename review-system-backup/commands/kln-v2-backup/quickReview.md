---
name: quickReview
description: Fast code review via LiteLLM API with grades and risk assessment
allowed-tools: Read, Bash, Grep, Glob, mcp__serena__write_memory, mcp__serena__read_memory, mcp__serena__list_memories
argument-hint: "[model] [focus] — models: qwen, deepseek, glm, minimax, kimi, hermes"
---

# Quick Review - API Method

Fast code review via LiteLLM API. All models use the same comprehensive checklist.

**Arguments:** $ARGUMENTS

---

## Model Selection

| Alias | Model |
|-------|-------|
| `qwen` | qwen3-coder |
| `deepseek` | deepseek-v3-thinking |
| `kimi` | kimi-k2-thinking |
| `glm` | glm-4.6-thinking |
| `minimax` | minimax-m2 |
| `hermes` | hermes-4-70b |

**Default:** `qwen` if no model specified

---

## Step 1: Parse Arguments

From $ARGUMENTS, extract:
- **Model**: First word if it matches a model alias, otherwise default to `qwen`
- **Focus**: Everything after the model (or entire string if no model specified)

Examples:
- `qwen memory safety` → model=qwen, focus="memory safety"
- `glm check error handling` → model=glm, focus="check error handling"
- `look for race conditions` → model=qwen (default), focus="look for race conditions"

---

## Step 2: Gather Code Context

```bash
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

## Step 3: Build Review Request

### System Prompt (UNIFIED - Same for ALL models)

```
You are an expert embedded systems code reviewer.

REVIEW ALL of these areas, with extra attention to the user's focus:

## CORRECTNESS
- Logic errors, edge cases, off-by-one
- Algorithm correctness, state management
- Variable initialization, single responsibility

## MEMORY SAFETY
- Buffer overflows, null pointer dereferences
- Memory leaks (especially error paths)
- Stack usage, integer overflow/underflow
- Static vs dynamic allocation

## ERROR HANDLING
- Input validation at trust boundaries
- Error propagation and resource cleanup
- Defensive programming patterns
- All error paths tested

## CONCURRENCY
- Race conditions, thread safety
- ISR constraints (fast, non-blocking)
- Shared data protection, volatile usage
- Deadlock potential

## ARCHITECTURE
- Module coupling and cohesion
- Abstraction quality, API consistency
- Dependency direction (no circular)
- Testability, maintainability

## HARDWARE (if applicable)
- I/O state correctness, timing
- Volatile usage for registers
- Power/reset handling

## STANDARDS
- Coding style consistency
- Documentation quality
- MISRA-C guidelines (where applicable)
```

### User Prompt Template

```
REVIEW REQUEST
==============
Focus: [USER_FOCUS]

CODE CHANGES:
[GIT_DIFF_CONTENT]

FILES AFFECTED:
[FILE_LIST]

---

Provide a STRUCTURED REVIEW:

## Grade: [A/B/C/D/F]
[1-2 sentence justification]

## Risk: [CRITICAL/HIGH/MEDIUM/LOW]

## Critical Issues (MUST FIX)
| # | Location | Issue | Fix |
|---|----------|-------|-----|

## Warnings (SHOULD FIX)
| # | Location | Issue | Fix |
|---|----------|-------|-----|

## Suggestions (NICE TO HAVE)
| # | Location | Suggestion | Benefit |
|---|----------|------------|---------|

## Code Practices
| Practice | Status | Notes |
|----------|--------|-------|
| Memory Safety | [ok/warn/fail] | |
| Error Handling | [ok/warn/fail] | |
| Concurrency | [ok/warn/fail] | |
| Architecture | [ok/warn/fail] | |
| Standards | [ok/warn/fail] | |

## Positive Observations
- [Good practices found]

## Summary
[2-3 sentences: key findings and recommended action]
```

---

## Step 4: Call LiteLLM API

Map alias to model name:
- qwen → qwen3-coder
- deepseek → deepseek-v3-thinking
- glm → glm-4.6-thinking
- minimax → minimax-m2
- kimi → kimi-k2-thinking
- hermes → hermes-4-70b

```bash
MODEL="[mapped-model-name]"

curl -s http://localhost:4000/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "'$MODEL'",
    "messages": [
      {"role": "system", "content": "[SYSTEM_PROMPT]"},
      {"role": "user", "content": "[USER_PROMPT_WITH_DIFF]"}
    ],
    "temperature": 0.3,
    "max_tokens": 4000
  }' | jq -r '.choices[0].message.content // .choices[0].message.reasoning_content'
```

---

## Step 5: Display Results

Show the complete review, then summarize:

```
═══════════════════════════════════════════════════
REVIEW COMPLETE
═══════════════════════════════════════════════════
Model: [model used]
Grade: [A-F]
Risk: [CRITICAL/HIGH/MEDIUM/LOW]
Critical: [count] | Warnings: [count] | Suggestions: [count]
═══════════════════════════════════════════════════
```

---

## Quick Reference

```bash
# General review
/kln:quickReview qwen review recent changes

# Specific focus
/kln:quickReview glm check memory safety and error handling

# Different model
/kln:quickReview kimi review architecture patterns

# Default model (qwen)
/kln:quickReview look for race conditions
```
