# Review System - File Structure

## Overview

This document describes all files created for the 3-tier review system that integrates Native Claude with LiteLLM local models.

---

## Directory Structure

```
/home/calin/
├── .claude/
│   ├── commands/
│   │   └── sc/
│   │       ├── createReviewDoc.md    # Session documentation command
│   │       ├── review.md             # Tier 1: Quick curl review
│   │       ├── secondOpinion.md      # Tier 2: Full context review
│   │       ├── deepReview.md         # Tier 3: Headless with tool access
│   │       ├── consensus.md          # Tier 2P: 3 models parallel (curl)
│   │       ├── parallelDeepReview.md # Tier 3P: 3 models parallel (tools)
│   │       ├── asyncDeepReview.md    # Async version - runs in subagent
│   │       └── backgroundReviewDoc.md # Background doc creation (subagent)
│   ├── scripts/
│   │   ├── deep-review.sh            # Bash script for Tier 3
│   │   ├── litellm-review.sh         # Helper for curl calls
│   │   └── parallel-deep-review.sh   # Script for Tier 3P parallel
│   ├── skills/
│   │   └── embedded-review.md        # Embedded review expertise
│   ├── bash_functions.sh             # Helper functions for terminal
│   ├── settings.json                 # Active settings (native or nano)
│   ├── settings-native.json          # Native Anthropic settings
│   └── settings-nanogpt.json         # LiteLLM proxy settings
│
├── .claude-review/
│   └── settings.json                 # Dedicated LiteLLM config for deep reviews
│
├── .config/
│   └── litellm/
│       └── nanogpt.yaml              # LiteLLM model configuration
│
└── claudeAgentic/
    ├── REVIEW_SYSTEM_STRUCTURE.md    # This file
    ├── REVIEW_SYSTEM_USAGE.md        # Usage documentation
    └── review-system-backup/         # Backup of all created files
        ├── commands/
        ├── scripts/
        ├── config/
        └── skills/
```

---

## Files Created

### 1. Slash Commands (`~/.claude/commands/sc/`)

| File | Size | Purpose |
|------|------|---------|
| `createReviewDoc.md` | ~4.5KB | Creates session documentation with grades, risk assessment, and persists to Serena memory |
| `review.md` | ~7.8KB | Tier 1: Quick code review via direct curl to LiteLLM |
| `secondOpinion.md` | ~8.1KB | Tier 2: Comprehensive context review via curl |
| `deepReview.md` | ~7.9KB | Tier 3: Spawns headless Claude with LiteLLM for tool-enabled review |
| `consensus.md` | ~8KB | Tier 2P: All 3 models in parallel via curl (no tool access) |
| `parallelDeepReview.md` | ~5KB | Tier 3P: All 3 models in parallel with FULL tool access |
| `asyncReview.md` | ~2KB | **Async Tier 1**: Quick review in subagent |
| `asyncSecondOpinion.md` | ~3KB | **Async Tier 2**: Full context review in subagent |
| `asyncConsensus.md` | ~3KB | **Async Tier 2P**: 3 models parallel in subagent |
| `asyncDeepReview.md` | ~3KB | **Async Tier 3P**: parallelDeepReview in subagent |
| `asyncReviewDoc.md` | ~3KB | **Async Doc**: createReviewDoc in subagent |
| `backgroundReviewDoc.md` | ~3KB | **Async Doc**: Alternative doc creation in subagent |

### 2. Scripts (`~/.claude/scripts/`)

| File | Size | Purpose |
|------|------|---------|
| `deep-review.sh` | ~5.2KB | Bash script that handles settings switching and spawns headless Claude |
| `litellm-review.sh` | ~1.4KB | Helper script for making LiteLLM API calls |
| `parallel-deep-review.sh` | ~8KB | Spawns 3 parallel headless instances with different models |

### 3. Helper Files (`~/.claude/`)

| File | Size | Purpose |
|------|------|---------|
| `bash_functions.sh` | ~4KB | Shell functions for terminal-based review commands |

### 4. Skills (`~/.claude/skills/`)

| File | Size | Purpose |
|------|------|---------|
| `embedded-review.md` | ~5.2KB | Embedded systems review expertise and checklists |

### 5. Configuration (`~/.claude-review/`)

| File | Size | Purpose |
|------|------|---------|
| `settings.json` | ~320B | LiteLLM settings for isolated deep reviews |

### 6. Bash Functions (added to `~/.bashrc`)

```bash
# Tier 3 - Single model deep review
deep-review()           # Run Tier 3 review with model and prompt

# Tier 3P - Parallel deep review (all 3 models)
parallel-review()       # Run ALL 3 models in parallel with tool access

# Tier 2P - Consensus review (all 3 via curl)
consensus-review()      # Run ALL 3 models in parallel via curl (faster)

# Convenience aliases
review-security         # Security audit with qwen
review-architecture     # Architecture review with deepseek
review-misra           # MISRA compliance with glm
review-memory          # Memory safety with qwen

# Quick review function
quick-review()         # Fast Tier 1 review from terminal
```

---

## Model Mapping

When using `use-nano` settings:

| Claude Model | LiteLLM Model | Actual Model |
|--------------|---------------|--------------|
| sonnet | coding-qwen | Qwen3 Coder |
| haiku | architecture-deepseek | DeepSeek V3.2 Thinking |
| opus | tools-glm | GLM 4.6 |

---

## Dependencies

### Required
- Claude Code CLI (`claude`)
- LiteLLM (`~/.local/bin/litellm`)
- jq (for JSON parsing)
- curl

### MCP Servers
- Serena (for memory persistence)
- Context7 (optional, for documentation)

### LiteLLM Models (via NanoGPT)
- coding-qwen
- architecture-deepseek
- tools-glm
- research-minimax
- agent-kimi
- scripting-hermes

---

## File Checksums

```bash
# Verify files with:
md5sum ~/.claude/commands/sc/createReviewDoc.md
md5sum ~/.claude/commands/sc/review.md
md5sum ~/.claude/commands/sc/secondOpinion.md
md5sum ~/.claude/commands/sc/deepReview.md
md5sum ~/.claude/scripts/deep-review.sh
```
