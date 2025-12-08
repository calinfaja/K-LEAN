---
name: deepAudit
description: "Run 3 models in PARALLEL with FULL TOOL ACCESS - comprehensive audit"
allowed-tools: Bash
argument-hint: "[models] [focus] — default: qwen,kimi,glm or specify 3 models"
---

# Deep Audit - 3 Models in Parallel (CLI with Tools)

Spawns **3 headless Claude instances** running different models **in parallel**.
Each instance has **FULL TOOL ACCESS** and can investigate independently.

**Arguments:** $ARGUMENTS

---

## Quick vs Deep Comparison

| Command | Models | Method | Tools | Time |
|---------|--------|--------|-------|------|
| `/kln:quickReview` | 1 | API | None | ~30s |
| `/kln:quickCompare` | 3 | API | None | ~60s |
| `/kln:deepInspect` | 1 | CLI | Full | ~3min |
| **`/kln:deepAudit`** | **3** | **CLI** | **Full** | **~5min** |

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
- `qwen,deepseek,glm security audit`
- `kimi,hermes,minimax architecture review`

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│  /kln:deepAudit "security audit"                                    │
│       │                                                             │
│       ├──► Headless #1 (qwen) ───────┐                              │
│       │    • Full tool access         │                              │
│       │                               │   PARALLEL                   │
│       ├──► Headless #2 (kimi) ────────┤   EXECUTION                  │
│       │    • Full tool access         │   (3-5 min)                  │
│       │                               │                              │
│       └──► Headless #3 (glm) ─────────┘                              │
│            • Full tool access                                        │
│                                                                     │
│       All 3 complete → Compare VERIFIED findings                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Parse Arguments

From $ARGUMENTS:
- If first word contains commas, use those 3 models
- Otherwise use default: qwen, kimi, glm
- **Focus**: Everything after model selection

---

## Step 2: Inform User

```
⚠️  DEEP AUDIT - Maximum Coverage
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Spawning 3 headless Claude instances in parallel.
Each has FULL TOOL ACCESS to investigate the codebase.

Models: [model1], [model2], [model3]
Focus: [user's focus]

Expected time: 3-5 minutes (all run simultaneously)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Step 3: Execute Parallel Deep Review

Run the parallel review script:

```bash
~/.claude/scripts/parallel-deep-review.sh "[FOCUS]" "$(pwd)" "[MODEL1]" "[MODEL2]" "[MODEL3]"
```

Each headless instance receives the unified system prompt with full tool access.

---

## System Prompt (UNIFIED - Same for all models)

```
You are an expert embedded systems code reviewer with FULL TOOL ACCESS.

INVESTIGATE the codebase thoroughly. Use tools to VERIFY issues, not just suspect them.

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

INVESTIGATION PROCESS:
1. Read relevant files to understand context
2. Search for patterns related to the focus area
3. Verify issues with evidence (file:line references)
4. Provide concrete fixes
```

---

## Step 4: Display Results & Synthesize

After all 3 complete, show individual results then synthesize:

```markdown
## Deep Audit Summary

### Reviewer Verdicts
| Model | Grade | Risk | Verdict |
|-------|-------|------|---------|
| [model1] | [A-F] | [level] | [verdict] |
| [model2] | [A-F] | [level] | [verdict] |
| [model3] | [A-F] | [level] | [verdict] |

### Consensus Analysis
- **Unanimous Issues** (all 3 found): [list]
- **Majority Issues** (2/3 found): [list]
- **Single Reviewer Issues** (investigate): [list]

### Final Recommendation
Based on consensus: [APPROVE / REQUEST_CHANGES / NEEDS_DISCUSSION]
```

---

## Usage

```bash
# Default models (qwen, kimi, glm)
/kln:deepAudit pre-release security audit

# Custom models
/kln:deepAudit qwen,deepseek,glm review BLE stack refactor

# Architecture focus
/kln:deepAudit kimi,hermes,minimax validate module structure
```

---

## Output Files

Results saved to:
- `/tmp/claude-reviews/review-[model1]-[timestamp].txt`
- `/tmp/claude-reviews/review-[model2]-[timestamp].txt`
- `/tmp/claude-reviews/review-[model3]-[timestamp].txt`

---

## Notes

- **Duration**: 3-5 minutes (all run simultaneously)
- **Resource usage**: 3 headless Claude processes
- **Use case**: Pre-release audits, major refactors, security reviews
- **Settings**: Automatically restored after review
