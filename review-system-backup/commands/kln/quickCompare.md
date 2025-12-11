---
name: quickCompare
description: "Run 3 models in PARALLEL and compare reviews"
allowed-tools: Bash, Read, Grep
argument-hint: "[models] [focus] — default: qwen,kimi,glm or specify 3 models"
---

# Quick Compare - 3 Models in Parallel (API)

Runs **3 models** simultaneously via parallel API calls.
All models use the same unified checklist - compare their findings for consensus.

**Arguments:** $ARGUMENTS

---

## Model Selection

**Default models:** qwen, kimi, glm

**All available:**
| Alias | Model |
|-------|-------|
| `qwen` | qwen3-coder |
| `deepseek` | deepseek-v3-thinking |
| `kimi` | kimi-k2-thinking |
| `glm` | glm-4.6-thinking |
| `minimax` | minimax-m2 |
| `hermes` | hermes-4-70b |

**Custom selection:** Specify 3 models comma-separated before focus:
- `qwen,deepseek,glm security audit` → runs qwen, deepseek, glm
- `kimi,hermes,minimax check architecture` → runs kimi, hermes, minimax

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│  /kln:quickCompare "security audit"                                 │
│       │                                                             │
│       ├──► Model 1 (qwen) ───────┐                                  │
│       │                          │                                  │
│       ├──► Model 2 (kimi) ───────┼──► PARALLEL EXECUTION            │
│       │                          │                                  │
│       └──► Model 3 (glm) ────────┘                                  │
│                                                                     │
│       All 3 return → COMPARE & SYNTHESIZE                           │
│       • Issues found by ALL 3 = HIGH CONFIDENCE                     │
│       • Issues found by 2/3 = MEDIUM CONFIDENCE                     │
│       • Issues found by 1/3 = LOW CONFIDENCE (review manually)      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Parse Arguments

From $ARGUMENTS:
- If first word contains commas (e.g., `qwen,deepseek,glm`), use those 3 models
- Otherwise use default: qwen, kimi, glm
- **Focus**: Everything after model selection

Examples:
- `security audit` → models=qwen,kimi,glm, focus="security audit"
- `qwen,deepseek,glm memory safety` → models=qwen,deepseek,glm, focus="memory safety"

---

## Step 2: Gather Context

```bash
DIFF=$(git diff HEAD~1..HEAD 2>/dev/null | head -300)
FILES=$(git diff --name-only HEAD~1..HEAD 2>/dev/null)
echo "Context gathered: $(echo "$DIFF" | wc -l) lines of diff"
```

---

## Step 3: Run Parallel Reviews

All 3 models use the SAME unified system prompt:

### System Prompt (UNIFIED)

```
You are an expert embedded systems code reviewer.

REVIEW ALL of these areas, with extra attention to the user's focus:

## CORRECTNESS
- Logic errors, edge cases, off-by-one
- Algorithm correctness, state management
- Variable initialization

## MEMORY SAFETY
- Buffer overflows, null pointer dereferences
- Memory leaks (especially error paths)
- Stack usage, integer overflow/underflow

## ERROR HANDLING
- Input validation at trust boundaries
- Error propagation and resource cleanup
- Defensive programming patterns

## CONCURRENCY
- Race conditions, thread safety
- ISR constraints (fast, non-blocking)
- Shared data protection, volatile usage

## ARCHITECTURE
- Module coupling and cohesion
- Abstraction quality, API consistency
- Testability, maintainability

## HARDWARE (if applicable)
- I/O state correctness, timing
- Volatile usage for registers

## STANDARDS
- Coding style consistency
- MISRA-C guidelines (where applicable)
```

### User Prompt

```
REVIEW REQUEST
Focus: [USER_FOCUS]

CODE CHANGES:
[GIT_DIFF]

Provide:
1. Grade (A-F)
2. Risk Level (CRITICAL/HIGH/MEDIUM/LOW)
3. Top 3 Critical Issues (if any)
4. Top 3 Warnings
5. Verdict (APPROVE/REQUEST_CHANGES)
```

### Parallel Execution

Run all 3 selected models in parallel using `&` and `wait`.

---

## Step 4: Display Individual Results

Show each model's review output.

---

## Step 5: Synthesize Consensus

```markdown
## Consensus Summary

### HIGH CONFIDENCE (All 3 agree)
| Issue | Model 1 | Model 2 | Model 3 |
|-------|---------|---------|---------|
| [issue] | found | found | found |

### MEDIUM CONFIDENCE (2/3 agree)
| Issue | Found By | Not Found By |
|-------|----------|--------------|

### LOW CONFIDENCE (Only 1 found)
| Issue | Found By | Action |
|-------|----------|--------|

### Grade Consensus
| Model | Grade | Risk | Verdict |
|-------|-------|------|---------|
| [model1] | [A-F] | [level] | [verdict] |
| [model2] | [A-F] | [level] | [verdict] |
| [model3] | [A-F] | [level] | [verdict] |
| **CONSENSUS** | **[avg]** | **[level]** | **[verdict]** |
```

---

## Usage

```bash
# Default models (qwen, kimi, glm)
/kln:quickCompare review recent changes

# Custom model selection
/kln:quickCompare qwen,deepseek,glm security audit

# Different combination
/kln:quickCompare kimi,minimax,hermes check architecture patterns
```

---

## Benefits

1. **Speed**: All 3 run in parallel (~60s total)
2. **Coverage**: Same checklist, different model perspectives
3. **Confidence**: Consensus = higher confidence in findings
4. **Flexibility**: Choose which 3 models to compare
