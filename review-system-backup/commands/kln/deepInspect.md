---
name: deepInspect
description: "Thorough review with FULL TOOL ACCESS - spawns headless Claude with LiteLLM model"
allowed-tools: Bash, Read
argument-hint: "[model] [focus] — models: qwen, deepseek, kimi, glm, minimax, hermes"
---

# Deep Inspect - CLI Method with Full Tools

Spawns a **headless Claude instance** with a LiteLLM model that has **FULL TOOL ACCESS**.
The reviewing model can read files, grep code, check git - it INVESTIGATES, not just opines.

**Arguments:** $ARGUMENTS

---

## Quick vs Deep

| Command | Method | Tool Access | Time |
|---------|--------|-------------|------|
| `/kln:quickReview` | API | None | ~30s |
| **`/kln:deepInspect`** | **CLI** | **Full** | **~3min** |

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

## How It Works

```
┌────────────────────────────────────────────────────────────────┐
│  YOUR SESSION (Native Claude)                                  │
│       │                                                        │
│       │ /kln:deepInspect qwen "security audit"                 │
│       ▼                                                        │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  SPAWNS HEADLESS CLAUDE INSTANCE                         │ │
│  │  • Uses LiteLLM model via settings                       │ │
│  │  • Has FULL tool access:                                 │ │
│  │    - Read any file                                       │ │
│  │    - Grep/search codebase                                │ │
│  │    - Run git commands                                    │ │
│  │    - Access Serena memories                              │ │
│  └──────────────────────────────────────────────────────────┘ │
│       │                                                        │
│       ▼                                                        │
│  Returns VERIFIED findings (with evidence)                     │
└────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Parse Arguments

From $ARGUMENTS:
- **Model**: First word if it matches a model alias, else default to `qwen`
- **Focus**: The rest of the arguments

Examples:
- `qwen security audit` → model=qwen, focus="security audit"
- `glm check MISRA compliance` → model=glm, focus="check MISRA compliance"
- `review error handling` → model=qwen (default), focus="review error handling"

---

## Step 2: Inform User

```
⚠️  DEEP INSPECT - Full Tool Access
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Spawning headless Claude with LiteLLM model.
The reviewer will INVESTIGATE the codebase using tools.

Model: [selected model]
Focus: [user's focus]

This may take 2-5 minutes...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Step 3: Execute Deep Review

Run the deep-review script:

```bash
~/.claude/scripts/deep-review.sh "[MODEL]" "[FOCUS]" "$(pwd)"
```

The script:
1. Switches to LiteLLM settings
2. Runs headless Claude with the unified review prompt
3. Restores original settings

---

## System Prompt (UNIFIED - Same for all models)

The headless Claude receives this system context:

```
You are an expert embedded systems code reviewer with FULL TOOL ACCESS.

TOOLS AVAILABLE:
- Read, Grep, Glob, Bash - explore and read any file
- Sequential Thinking MCP - use for complex analysis
- Serena MCP - access project memories and symbols
- Context7 MCP - lookup library documentation

IMPORTANT CONSTRAINTS:
- READ-ONLY: Do NOT modify, edit, or implement any code
- Do NOT create files or make changes to the codebase
- Your ONLY output is the review report
- Use tools to INVESTIGATE and VERIFY, then report findings

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
1. Use Sequential Thinking for complex analysis
2. Read relevant files to understand context
3. Use Serena to check project memories and symbols
4. Search for patterns related to the focus area
5. Verify issues with evidence (file:line references)
6. Suggest fixes in your report (do NOT implement them)

REMEMBER: You are a REVIEWER, not an IMPLEMENTER.
Output ONLY the review report. Do NOT modify any files.
```

---

## Expected Output Format

```
═══════════════════════════════════════════════════════════════
DEEP INSPECT COMPLETE
═══════════════════════════════════════════════════════════════
Model: [model]
Focus: [focus]

## Investigation Summary
Files examined: [list]
Patterns searched: [list]

## Grade: [A-F]
[justification]

## Risk: [CRITICAL/HIGH/MEDIUM/LOW]

## Critical Issues (VERIFIED)
| # | Location | Issue | Evidence | Fix |
|---|----------|-------|----------|-----|

## Warnings (VERIFIED)
| # | Location | Issue | Evidence | Fix |
|---|----------|-------|----------|-----|

## Suggestions
| # | Location | Suggestion | Benefit |
|---|----------|------------|---------|

## Positive Observations
- [good practices found]

## Summary
[2-3 sentences]
═══════════════════════════════════════════════════════════════
```

---

## Usage Examples

```bash
# Security audit
/kln:deepInspect qwen security audit focusing on buffer handling

# Architecture review
/kln:deepInspect kimi analyze module structure and coupling

# Standards compliance
/kln:deepInspect glm MISRA-C compliance check

# Default model (qwen)
/kln:deepInspect find memory safety issues in crypto module
```

---

## Notes

- **Duration**: 2-5 minutes (model investigates using tools)
- **Settings**: Automatically restored after review
- **LiteLLM**: Must be running (`start-nano-proxy`)
- **Available models**: qwen, deepseek, kimi, glm, minimax, hermes
