# Review System - Usage Guide

## Overview

A 3-tier code review system that uses Native Claude for primary work and LiteLLM local models for independent reviews.

---

## Prerequisites

### 1. Claude Code CLI
```bash
# Verify installation
claude --version
```

### 2. LiteLLM Proxy
```bash
# Install if needed
pip install litellm

# Configuration file should exist at:
~/.config/litellm/nanogpt.yaml
```

### 3. Bash Aliases (in ~/.bashrc)
```bash
# Start LiteLLM proxy
alias start-nano-proxy='litellm --config ~/.config/litellm/nanogpt.yaml &'

# Switch between native and LiteLLM
alias use-nano='cp ~/.claude/settings-nanogpt.json ~/.claude/settings.json'
alias use-native='cp ~/.claude/settings-native.json ~/.claude/settings.json'
```

### 4. MCP Servers
- **Serena**: For memory persistence (stores review documents)
- Activate project before using: `mcp__serena__activate_project`

### 5. Source Bash Functions
```bash
source ~/.bashrc
```

---

## Quick Start

### Step 1: Start LiteLLM (if not running)
```bash
start-nano-proxy
# Verify: curl http://localhost:4000/health
```

### Step 2: Use Native Claude for Coding
```bash
use-native
claude
```

### Step 3: Work Normally
Code with Claude as usual. Claude has full power and MCP access.

### Step 4: Review When Ready
Use the appropriate tier based on your needs.

---

## The Review Tiers (Single + Parallel)

### Tier 1: Quick Review (`/sc:review`)

**Speed:** Fast (10-30 seconds)
**Tool Access:** None
**Use For:** Quick sanity checks

```bash
# Inside Claude session:
/sc:review qwen check for buffer overflows
/sc:review deepseek evaluate coupling
/sc:review glm MISRA compliance
```

**Models:**
| Alias | Model | Specialty |
|-------|-------|-----------|
| qwen | coding-qwen | Bugs, memory safety |
| deepseek | architecture-deepseek | Architecture, design |
| glm | tools-glm | MISRA, standards |

---

### Tier 2: Second Opinion (`/sc:secondOpinion`)

**Speed:** Medium (30-60 seconds)
**Tool Access:** None (but receives full context)
**Use For:** Independent opinion with comprehensive context

```bash
# Inside Claude session:
/sc:secondOpinion qwen Is this implementation memory-safe?
/sc:secondOpinion deepseek Is the module structure correct?
/sc:secondOpinion glm Check standards compliance
```

**What It Sends:**
- Git diff (last 3 commits)
- Recently modified files
- Project configuration
- Serena memories (lessons learned)
- Your specific question

---

### Tier 3: Deep Review (`/sc:deepReview`)

**Speed:** Slow (2-5 minutes)
**Tool Access:** FULL (Read, Grep, Bash, Serena)
**Use For:** Thorough pre-release audits

```bash
# Inside Claude session:
/sc:deepReview qwen Thorough security audit
/sc:deepReview deepseek Analyze architecture deeply
/sc:deepReview glm Full MISRA-C:2012 audit
```

**How It Works:**
1. Temporarily switches settings to LiteLLM
2. Spawns headless Claude with the LiteLLM model
3. Model can READ files, GREP code, run GIT commands
4. Model INVESTIGATES and VERIFIES findings
5. Restores your native settings when done

**From Terminal (outside Claude):**
```bash
deep-review qwen "security audit"
deep-review deepseek "architecture review"

# Or use aliases:
review-security      # Security with qwen
review-architecture  # Architecture with deepseek
review-misra         # MISRA with glm
review-memory        # Memory safety with qwen
```

---

## Parallel Reviews (All 3 Models)

### Tier 2P: Consensus Review (`/sc:consensus`)

**Speed:** Fast (~1 minute total)
**Tool Access:** None
**Models:** ALL 3 (qwen + deepseek + glm) run simultaneously
**Use For:** Quick multi-perspective check

```bash
# Inside Claude session:
/sc:consensus security audit
/sc:consensus check for memory issues
```

**How It Works:**
1. Runs 3 parallel curl requests to LiteLLM
2. Each model reviews the same diff
3. Compares findings for consensus
4. Issues found by ALL 3 = HIGH confidence
5. Issues found by 2/3 = MEDIUM confidence
6. Issues found by 1/3 = investigate manually

**From Terminal:**
```bash
consensus-review "memory safety"
```

---

### Tier 3P: Parallel Deep Review (`/sc:parallelDeepReview`)

**Speed:** Medium (~5 minutes total, but all run simultaneously)
**Tool Access:** FULL for all 3 instances
**Models:** ALL 3 with independent investigation
**Use For:** Comprehensive pre-release audit

```bash
# Inside Claude session:
/sc:parallelDeepReview Complete security audit before release
/sc:parallelDeepReview Validate architecture before merge
```

**How It Works:**
1. Spawns 3 headless Claude instances in parallel
2. Each uses a different LiteLLM model
3. Each has FULL tool access (Read, Grep, Bash, Serena)
4. Each investigates independently and VERIFIES findings
5. Results compared for consensus

**From Terminal:**
```bash
parallel-review "security audit"
```

**Output Files:**
- `/tmp/claude-reviews/review-qwen-[timestamp].txt`
- `/tmp/claude-reviews/review-deepseek-[timestamp].txt`
- `/tmp/claude-reviews/review-glm-[timestamp].txt`

---

## Tier Comparison Table

| Tier | Command | Models | Parallel | Tools | Async | Time |
|------|---------|--------|----------|-------|-------|------|
| 1 | `/sc:review` | 1 | - | ❌ | - | 30s |
| 2 | `/sc:secondOpinion` | 1 | - | ❌ | - | 1min |
| 3 | `/sc:deepReview` | 1 | - | ✅ | - | 3min |
| 2P | `/sc:consensus` | 3 | ✅ | ❌ | - | 1min |
| 3P | `/sc:parallelDeepReview` | 3 | ✅ | ✅ | - | 5min |
| 3P+ | `/sc:asyncDeepReview` | 3 | ✅ | ✅ | **✅** | 5min |

### Async Commands via Hooks (Work While Reviewing)

These commands run via **UserPromptSubmit hook** - they execute immediately in background!

| Trigger Keyword | What Runs | Output |
|-----------------|-----------|--------|
| `asyncDeepReview <focus>` | 3 models with tools | `/tmp/claude-reviews/deep-review-latest.log` |
| `asyncConsensus <focus>` | 3 models via curl | `/tmp/claude-reviews/consensus-latest.log` |
| `asyncReview qwen <focus>` | Quick qwen review | `/tmp/claude-reviews/review-qwen-latest.log` |
| `asyncReview deepseek <focus>` | Quick deepseek | `/tmp/claude-reviews/review-deepseek-latest.log` |
| `asyncReview glm <focus>` | Quick glm review | `/tmp/claude-reviews/review-glm-latest.log` |
| `asyncSecondOpinion qwen <q>` | Opinion from qwen | `/tmp/claude-reviews/opinion-qwen-latest.log` |
| `asyncSecondOpinion deepseek <q>` | Opinion from deepseek | `/tmp/claude-reviews/opinion-deepseek-latest.log` |
| `asyncSecondOpinion glm <q>` | Opinion from glm | `/tmp/claude-reviews/opinion-glm-latest.log` |

**How Hook-Based Async Works:**
```
YOU: "asyncDeepReview security audit"
     │
     └──► UserPromptSubmit hook (async-dispatch.sh)
              │
              ├──► Detects keyword "asyncDeepReview"
              │
              └──► Runs parallel-deep-review.sh in background (nohup)
                        │
                        └──► Writes to /tmp/claude-reviews/

YOU: Keep working, Claude responds normally
     │
LATER: Check results with `cat /tmp/claude-reviews/deep-review-latest.log`
```

**Implementation (per Claude Code docs):**
```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/scripts/async-dispatch.sh",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

**Note:** `UserPromptSubmit` doesn't support `matcher` - the dispatch script handles keyword detection internally.

**Advantage over subagents:** Hooks run shell scripts directly - guaranteed execution, no interpretation.

---

## Session Documentation (`/sc:createReviewDoc`)

Document your coding session with grades and persist to Serena memory.

```bash
/sc:createReviewDoc Secure Boot Implementation
/sc:createReviewDoc BLE Stack Integration
```

**What It Creates:**
- Session summary
- Quality grades (A-F)
- Risk assessment
- Files modified
- Lessons learned (PATTERN/GOTCHA/TIP)
- Potential improvements
- Code practices checklist

**Persistence:**
Saves to Serena memory as `review-YYYY-MM-DD-slug.md`

---

## Recommended Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│  RECOMMENDED WORKFLOW                                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. START SESSION                                               │
│     $ use-native                                                │
│     $ start-nano-proxy  (if not running)                        │
│     $ claude                                                    │
│                                                                 │
│  2. CODE WITH NATIVE CLAUDE                                     │
│     • Plan, implement, debug                                    │
│     • Full power, all MCP tools                                 │
│                                                                 │
│  3. CHECKPOINT (document progress)                              │
│     /sc:createReviewDoc "Feature Name"                          │
│                                                                 │
│  4. QUICK CHECK (Tier 1)                                        │
│     /sc:review qwen any obvious issues?                         │
│                                                                 │
│  5. SECOND OPINION (Tier 2) - if needed                         │
│     /sc:secondOpinion deepseek is this architecture right?      │
│                                                                 │
│  6. PRE-RELEASE AUDIT (Tier 3)                                  │
│     /sc:deepReview qwen thorough security audit                 │
│                                                                 │
│  7. ADDRESS FINDINGS                                            │
│     Fix issues found by reviews                                 │
│                                                                 │
│  8. FINAL DOCUMENTATION                                         │
│     /sc:createReviewDoc "Ready for Merge"                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Output Formats

### Review Output (Tier 1, 2, 3)
```
## Overall Grade: [A-F]

## Risk Assessment
| Level | Score | Justification |
|-------|-------|---------------|

## Critical Issues (MUST FIX)
| # | File:Line | Issue | Fix |

## Warnings (SHOULD FIX)
...

## Suggestions
...

## Verdict
[APPROVE / APPROVE_WITH_CHANGES / REQUEST_CHANGES]
```

### Session Documentation Output
```
# Session Review: [Title]

| Date | Project | Target | Grade | Risk |
...

## Quality Assessment
| Category | Score |
...

## Lessons Learned
- [PATTERN] ...
- [GOTCHA] ...
- [TIP] ...
```

---

## Troubleshooting

### LiteLLM Not Responding
```bash
# Check if running
curl http://localhost:4000/health

# Start it
start-nano-proxy

# Check models
curl http://localhost:4000/models | jq '.data[].id'
```

### Serena Memory Errors
```bash
# Activate project first
# In Claude session:
mcp__serena__activate_project with project: "zephyr"
```

### Deep Review Settings Issue
```bash
# Manually restore native settings
use-native

# Check backup exists
ls ~/.claude/settings-pre-review-backup.json
```

### Model Not Found
```bash
# Verify model is configured in nanogpt.yaml
cat ~/.config/litellm/nanogpt.yaml | grep model_name
```

---

## Command Reference

### Slash Commands (inside Claude)

| Command | Tier | Models | Tool Access | Async | Time | Use Case |
|---------|------|--------|-------------|-------|------|----------|
| `/sc:review` | 1 | 1 | None | - | 30s | Quick check |
| `/sc:secondOpinion` | 2 | 1 | None | - | 1min | Full context opinion |
| `/sc:deepReview` | 3 | 1 | Full | - | 3min | Thorough audit |
| `/sc:consensus` | 2P | **3** | None | - | 1min | Quick multi-perspective |
| `/sc:parallelDeepReview` | 3P | **3** | Full | - | 5min | Comprehensive audit |
| `/sc:createReviewDoc` | - | - | Serena | - | Fast | Document session |
| **Async Versions** | | | | | | |
| `/sc:asyncReview` | 1 | 1 | None | **✅** | 30s | Quick check (background) |
| `/sc:asyncSecondOpinion` | 2 | 1 | None | **✅** | 1min | Opinion (background) |
| `/sc:asyncConsensus` | 2P | **3** | None | **✅** | 1min | 3 models (background) |
| `/sc:asyncDeepReview` | 3P | **3** | Full | **✅** | 5min | Full audit (background) |
| `/sc:asyncReviewDoc` | - | - | Serena | **✅** | Fast | Doc (background) |

### Bash Functions (from terminal)

| Function | Purpose |
|----------|---------|
| `deep-review <model> "<prompt>"` | Run Tier 3 (single model) |
| `parallel-review "<prompt>"` | Run Tier 3P (all 3 models in parallel) |
| `consensus-review "<focus>"` | Run Tier 2P (all 3 via curl) |
| `quick-review "<focus>"` | Run Tier 1 from terminal |
| `review-security` | Security audit alias (qwen) |
| `review-architecture` | Architecture review alias (deepseek) |
| `review-misra` | MISRA compliance alias (glm) |
| `review-memory` | Memory safety alias (qwen) |

---

## Version

- Created: 2025-12-02
- Author: Claude + User
- System: SuperClaude + LiteLLM + Serena
