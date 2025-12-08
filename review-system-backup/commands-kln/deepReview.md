---
name: deepReview
description: "TIER 3: Thorough review with FULL TOOL ACCESS - spawns headless Claude with LiteLLM model"
allowed-tools: Bash, Read
argument-hint: "[model] [focus] — models: qwen (code), deepseek (architecture), glm (standards)"
---

# Deep Review (Tier 3) - Full Tool Access

Spawns a **headless Claude instance** with a LiteLLM model that has **FULL TOOL ACCESS**.
The reviewing model can read files, grep code, check git, access Serena - it INVESTIGATES, not just opines.

**Arguments:** $ARGUMENTS

---

## Why Tier 3?

| Tier | Command | Tool Access | Use Case |
|------|---------|-------------|----------|
| 1 | `/kln:review` | ❌ None | Quick sanity check |
| 2 | `/kln:secondOpinion` | ❌ None | Full context, passive review |
| **3** | **`/kln:deepReview`** | **✅ Full** | **Thorough investigation** |

---

## How It Works

```
┌────────────────────────────────────────────────────────────────┐
│  YOUR SESSION (Native Claude)                                  │
│       │                                                        │
│       │ /kln:deepReview qwen "security audit"                  │
│       ▼                                                        │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  SPAWNS NEW HEADLESS INSTANCE                            │ │
│  │  • Temporarily switches to LiteLLM settings              │ │
│  │  • Runs claude --print with your prompt                  │ │
│  │  • Model has FULL tool access:                           │ │
│  │    - Read any file                                       │ │
│  │    - Grep/search codebase                                │ │
│  │    - Run git commands                                    │ │
│  │    - Access Serena memories                              │ │
│  │  • Restores your native settings when done               │ │
│  └──────────────────────────────────────────────────────────┘ │
│       │                                                        │
│       ▼                                                        │
│  Returns VERIFIED findings (not just opinions)                │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Model Selection

| Alias | LiteLLM Model | Specialty |
|-------|---------------|-----------|
| `qwen` | qwen3-coder | Code quality, bugs, memory safety |
| `deepseek` | deepseek-v3-thinking | Architecture, design, coupling |
| `glm` | glm-4.6-thinking | MISRA-C, standards, compliance |

---

## Instructions

### Step 1: Parse Arguments

From $ARGUMENTS:
- **Model**: First word if `qwen`/`deepseek`/`glm`, else default to `qwen`
- **Focus**: The rest of the arguments (what to investigate)

Examples:
- `qwen security audit` → model=qwen, focus="security audit"
- `deepseek review architecture` → model=deepseek, focus="review architecture"
- `glm MISRA compliance` → model=glm, focus="MISRA compliance"

### Step 2: Warn User

Tell the user:
```
⚠️  DEEP REVIEW - Tier 3
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This will spawn a headless Claude instance with LiteLLM.
The reviewing model will have FULL tool access and will
actively investigate the codebase.

This may take several minutes as the model explores.

Model: [selected model]
Focus: [user's focus]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Step 3: Execute Deep Review

Run the deep-review script:

```bash
/home/calin/.claude/scripts/deep-review.sh "[MODEL]" "[FOCUS]" "$(pwd)"
```

Where:
- `[MODEL]` = qwen, deepseek, or glm
- `[FOCUS]` = the user's review focus/question
- `$(pwd)` = current working directory

**IMPORTANT:** This command runs synchronously and may take several minutes.
The script handles settings switching automatically.

### Step 4: Present Results

The script output contains the full review with:
- Investigation summary (what the model checked)
- Verified findings (with evidence)
- Code practices assessment
- Risk assessment
- Verdict (APPROVE/REQUEST_CHANGES/etc.)

Display the full output to the user.

---

## Usage Examples

```bash
# Thorough security audit
/kln:deepReview qwen Conduct a thorough security audit focusing on buffer handling

# Architecture review with investigation
/kln:deepReview deepseek Analyze the module structure and identify coupling issues

# Pre-release MISRA compliance check
/kln:deepReview glm Full MISRA-C:2012 compliance audit before release

# General code quality investigation
/kln:deepReview qwen Find all potential memory safety issues
```

---

## What the Reviewing Model Can Do

The LiteLLM model running in headless mode has access to:

| Tool | What It Can Do |
|------|----------------|
| `Read` | Read any file in the codebase |
| `Grep` | Search for patterns across files |
| `Glob` | Find files by pattern |
| `Bash` | Run git commands, find, etc. |
| `mcp__serena__*` | Access project memories, symbols |

This means it can **VERIFY** issues, not just suspect them.

---

## Expected Output Format

```
═══════════════════════════════════════════════════════════════
DEEP REVIEW - Tier 3 (Full Tool Access)
═══════════════════════════════════════════════════════════════
Model: qwen3-coder (code quality)
Directory: /path/to/project
Prompt: security audit
═══════════════════════════════════════════════════════════════

[Model investigates using tools...]

## Investigation Summary
I checked the following:
- Scanned all .c files for buffer operations
- Reviewed memory allocation patterns
- Checked error handling in critical paths
- Verified interrupt safety markers

## Verified Findings

### Critical Issues (VERIFIED)
| # | File:Line | Issue | Evidence | Fix |
|---|-----------|-------|----------|-----|
| 1 | src/parser.c:45 | Buffer overflow | buf[64] receives up to 128 bytes | Add bounds check |

### Warnings (VERIFIED)
...

## Verdict
REQUEST_CHANGES - 1 critical issue must be fixed

═══════════════════════════════════════════════════════════════
DEEP REVIEW COMPLETE
═══════════════════════════════════════════════════════════════
```

---

## Notes

- **Duration**: Deep reviews take longer (2-5 minutes) because the model investigates
- **Settings**: Your native Claude settings are automatically restored after the review
- **LiteLLM**: Must be running (`start-nano-proxy`)
- **Parallel**: While the review runs, your main session is paused waiting for results
