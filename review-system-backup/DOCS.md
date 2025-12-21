# K-LEAN Complete Documentation

> Multi-Model Code Review & Knowledge Capture System for Claude Code

**Version:** 2.2.0 | **License:** MIT | **Author:** Calin Faja

---

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Review System](#review-system)
5. [Knowledge System](#knowledge-system)
6. [Commands Reference](#commands-reference)
7. [Hooks](#hooks)
8. [LiteLLM Configuration](#litellm-configuration)
9. [Factory Droids](#factory-droids)
10. [CLI Reference](#cli-reference)
11. [Troubleshooting](#troubleshooting)

---

## Overview

K-LEAN is a comprehensive code review and knowledge capture system that extends Claude Code with:

- **Multi-Model Reviews** - Route to 12 specialized AI models via LiteLLM
- **Knowledge Capture** - Semantic search database for storing insights
- **Slash Commands** - 20+ `/kln:` commands for reviews, audits, droids
- **Event Hooks** - Auto-capture web content, timeline tracking
- **Factory Droids** - 8 specialized AI agents for deep analysis

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  Claude Code (Native)                                               │
│       │                                                             │
│       ├── /kln: Commands (20) ─── Quick reviews, deep audits        │
│       │                                                             │
│       ├── Hooks ─────────────────────────────────────────────────── │
│       │   ├── UserPromptSubmit: Keywords, async dispatch            │
│       │   └── PostToolUse: Auto-capture, timeline                   │
│       │                                                             │
│       ├── LiteLLM Proxy (localhost:4000) ────────────────────────── │
│       │   ├── qwen3-coder         - Code quality, bugs              │
│       │   ├── deepseek-v3-thinking - Architecture, design           │
│       │   ├── glm-4.6-thinking    - Standards, compliance           │
│       │   ├── kimi-k2-thinking    - Agent tasks                     │
│       │   └── + 8 more models                                       │
│       │                                                             │
│       ├── Knowledge DB (.knowledge-db/) ─────────────────────────── │
│       │   └── txtai semantic search (~30ms via server)              │
│       │                                                             │
│       └── Factory Droids (~/.factory/droids/) ───────────────────── │
│           └── 8 specialist agents with tools                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Installation

### Prerequisites

- Python 3.9+
- Claude Code CLI
- Git, curl, jq

### Option 1: From Source (Development)

```bash
git clone https://github.com/calinfaja/k-lean.git
cd k-lean
./install.sh --full
```

### Option 2: Via pipx (Production)

```bash
pipx install k-lean
k-lean install
```

### Post-Install

```bash
# Configure LiteLLM provider
~/.claude/scripts/setup-litellm.sh

# Start services
k-lean start

# Verify installation
k-lean status
```

---

## Quick Start

### Run a Code Review

```bash
# Quick single-model review
/kln:quickReview qwen3-coder security

# Compare 3 models
/kln:quickCompare architecture

# Deep review with tools
/kln:deepInspect qwen3-coder full audit
```

### Capture Knowledge

```bash
# Capture URL
GoodJob https://docs.example.com

# Save lesson learned
SaveThis learned X improves Y

# Search knowledge
FindKnowledge authentication patterns
```

### Check System Status

```bash
k-lean status      # Component status
k-lean doctor      # Diagnose issues
k-lean models      # List available models
```

---

## Review System

### 4-Tier Review Hierarchy

| Tier | Command | Time | Description |
|------|---------|------|-------------|
| 1 | `/kln:quickReview` | ~30s | Single model, fast feedback |
| 2 | `/kln:quickCompare` | ~90s | 3 models, consensus |
| 3 | `/kln:deepInspect` | ~3min | Single model with tools |
| 4 | `/kln:deepAudit` | ~5min | 3 models with tools |

### Available Models

| Model | Tier | Speed | Use Case |
|-------|------|-------|----------|
| qwen3-coder | elite | 35 tok/s | Coding, bugs |
| devstral-2 | elite | 32 tok/s | Coding |
| deepseek-v3-thinking | reasoning | 20 tok/s | Architecture |
| deepseek-r1 | reasoning | 15 tok/s | Deep reasoning |
| glm-4.6-thinking | reasoning | 11 tok/s | Standards |
| kimi-k2 | agent | 28 tok/s | Agents |
| kimi-k2-thinking | agent | 20 tok/s | Agents |
| llama-4-scout | speed | 47 tok/s | Fast reviews |
| llama-4-maverick | context | 28 tok/s | Large repos |
| minimax-m2 | specialist | 23 tok/s | Research |
| hermes-4-70b | specialist | 20 tok/s | Scripting |
| qwen3-235b | value | 16 tok/s | General |

### Review Output

Reviews are saved to `.claude/kln/<command>/` in each project:
```
.claude/kln/
├── quickReview/
├── quickCompare/
├── deepInspect/
└── deepAudit/
```

---

## Knowledge System

### Storage

Per-project knowledge in `.knowledge-db/`:
```
.knowledge-db/
├── entries.jsonl    # All entries (JSONL format)
├── timeline.txt     # Chronological log
└── index/           # txtai vector index
```

### Capture Commands

| Command | Description |
|---------|-------------|
| `GoodJob <url>` | Capture web page content |
| `SaveThis <text>` | Save lesson learned |
| `SaveInfo <text>` | Smart capture with evaluation |

### Search

```bash
# Via server (fast, ~30ms)
~/.claude/scripts/knowledge-query.sh "query"

# Direct (slow, ~17s cold)
FindKnowledge "query"
```

### Knowledge Server

Auto-starts on terminal open. Keeps txtai embeddings in memory.

```bash
# Check status
ls -la /tmp/knowledge-server.sock

# Manual start
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-server.py start &
```

---

## Commands Reference

### Review Commands

| Command | Args | Description |
|---------|------|-------------|
| `/kln:quickReview` | `<model> <focus>` | Single model review |
| `/kln:quickCompare` | `[models] [focus]` | 3 model comparison |
| `/kln:deepInspect` | `<model> <focus>` | Single model with tools |
| `/kln:deepAudit` | `[models] [focus]` | 3 models with tools |

### Async Commands (Background)

| Command | Description |
|---------|-------------|
| `/kln:asyncQuickReview` | Background quick review |
| `/kln:asyncQuickCompare` | Background comparison |
| `/kln:asyncDeepAudit` | Background deep audit |

### Droid Commands

| Command | Args | Description |
|---------|------|-------------|
| `/kln:droid` | `<model> <focus>` | Fast droid review |
| `/kln:droidAudit` | `[focus]` | 3 droids in parallel |
| `/kln:droidExecute` | `<model> <droid> <task>` | Execute specific droid |

### Utility Commands

| Command | Description |
|---------|-------------|
| `/kln:models` | List available models |
| `/kln:help` | Show all commands |
| `/kln:createReport` | Generate session report |

---

## Hooks

### UserPromptSubmit

Triggers on user prompt, handles keywords:

| Keyword | Action |
|---------|--------|
| `healthcheck` | Check all models |
| `GoodJob <url>` | Capture URL |
| `SaveThis <text>` | Save lesson |
| `qreview`, `dreview` | Quick/deep review |

### PostToolUse

| Matcher | Action |
|---------|--------|
| `Bash` | Post-commit docs, timeline |
| `WebFetch\|WebSearch` | Auto-capture URLs |
| `mcp__tavily__.*` | Auto-capture search results |
| `.*` | Context monitoring |

### Hook Files

```
~/.claude/hooks/
├── user-prompt-handler.sh
├── post-bash-handler.sh
├── post-web-handler.sh
├── context-monitor.sh
└── async-review.sh
```

---

## LiteLLM Configuration

### Config Location

```
~/.config/litellm/
├── config.yaml      # Main config (12 models)
├── .env             # API keys (NEVER commit)
├── .env.example     # Template
└── openrouter.yaml  # Alternative provider
```

### Setup Wizard

```bash
~/.claude/scripts/setup-litellm.sh
```

Providers:
- **NanoGPT**
- **OpenRouter**

### Start LiteLLM

```bash
~/.claude/scripts/start-litellm.sh
# Or: k-lean start
```

---

## Factory Droids

### Available Droids

| Droid | Specialization |
|-------|----------------|
| orchestrator | Task coordination |
| code-reviewer | Quality gatekeeper |
| security-auditor | OWASP compliance |
| debugger | Root cause analysis |
| arm-cortex-expert | Embedded systems |
| c-pro | C programming |
| rust-expert | Rust/safety |
| performance-engineer | Optimization |

### Execute Droid

```bash
/kln:droidExecute qwen3-coder security-auditor "audit authentication"
```

### Droid Files

```
~/.factory/droids/
├── orchestrator.md
├── code-reviewer.md
├── security-auditor.md
├── debugger.md
├── arm-cortex-expert.md
├── c-pro.md
├── rust-expert.md
└── performance-engineer.md
```

---

## CLI Reference

### k-lean Commands

```bash
k-lean status           # Component status
k-lean doctor           # Diagnose issues
k-lean doctor --auto-fix # Auto-fix issues
k-lean start            # Start services
k-lean stop             # Stop services
k-lean models           # List models
k-lean test-model <m>   # Test specific model
k-lean install          # Install components
k-lean install --dev    # Dev mode (symlinks)
k-lean uninstall        # Remove components
k-lean debug            # Monitoring dashboard
k-lean version          # Version info
```

### Maintenance Scripts

```bash
# Sync verification
~/.claude/scripts/sync-check.sh           # Check sync
~/.claude/scripts/sync-check.sh --fix     # Fix symlinks
~/.claude/scripts/sync-check.sh --orphans # Find orphans
~/.claude/scripts/sync-check.sh --clean   # Remove orphans

# Testing
./test.sh                                 # Run test suite

# Update
./update.sh                               # Pull and reinstall
```

---

## Troubleshooting

### LiteLLM Not Starting

```bash
# Check port
lsof -i :4000

# Debug mode
source ~/.config/litellm/.env
litellm --config ~/.config/litellm/config.yaml --debug
```

### Models Not Available

```bash
# Test API
curl http://localhost:4000/v1/models

# Check config
cat ~/.config/litellm/config.yaml

# Verify API keys
cat ~/.config/litellm/.env
```

### Knowledge DB Errors

```bash
# Reinstall dependencies
~/.venvs/knowledge-db/bin/pip install --upgrade txtai sentence-transformers
```

### Sync Issues

```bash
# Check status
sync-check.sh

# Fix broken symlinks
sync-check.sh --fix

# Clean orphaned files
sync-check.sh --clean
```

---

## Directory Structure

```
~/.claude/                    # Claude config
├── scripts/                  # All scripts (symlinked)
├── commands/kln/             # /kln: commands (symlinked)
├── hooks/                    # Event hooks (symlinked)
├── lib/                      # Shared libraries
├── settings.json             # Claude settings
└── CLAUDE.md                 # System instructions

~/.factory/droids/            # Factory Droid specialists
~/.config/litellm/            # LiteLLM configuration
~/.venvs/knowledge-db/        # Python venv for txtai

<project>/
├── .claude/kln/              # Review outputs
└── .knowledge-db/            # Project knowledge
```

---

## Support

- **Issues:** https://github.com/calinfaja/k-lean/issues
- **Documentation:** This file
- **Developer Guide:** See `docs/DEVELOPER.md`
