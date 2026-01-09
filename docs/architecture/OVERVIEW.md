# K-LEAN Overview

> **Multi-Model Code Reviews & Persistent Knowledge for Claude Code**

**Version:** 1.0.0b6 | **License:** Apache 2.0

---

## What is K-LEAN?

K-LEAN (Knowledge-Lean) is an addon for Claude Code that provides:

- **Multiple LLM models** via LiteLLM proxy (dynamic discovery)
- **Consensus reviews** from 3-5 models in parallel
- **Persistent Knowledge DB** with semantic search (per-project)
- **8 SmolKLN agents** for domain-specific analysis
- **9 slash commands** for reviews, debugging, and documentation
- **4 hooks** for automatic knowledge capture (Python entry points)

### The Problem

Claude Code uses a single AI model. K-LEAN adds:
- Multiple perspectives on code quality
- Persistent memory across sessions
- Specialized domain expertise

### Positioning

**K-LEAN is an ADDON, not a replacement.** Works alongside Claude Code and other extensions (SuperClaude, Serena MCP, Context7).

### Cross-Platform Support

K-LEAN works natively on **Windows, Linux, and macOS**:
- No shell scripts required for core functionality
- TCP localhost for IPC (not Unix sockets)
- Python entry points for hooks (not bash scripts)
- platformdirs for cross-platform paths

---

## Architecture

```
                          Claude Code
   +-----------------------------------------------------------------+
   |  +----------------+  +-------------+  +----------------------+  |
   |  |  Python Hooks  |  |  /kln:*     |  |   SmolKLN Agents     |  |
   |  |  (4 entry pts) |  |  Commands   |  |   (8 specialists)    |  |
   |  +-------+--------+  +------+------+  +-----------+----------+  |
   +---------|--------------------|----------------------|-----------+
             |                    |                      |
             v                    v                      v
   +-----------------------------------------------------------------+
   |                       K-LEAN Layer                               |
   |  +----------------+  +----------------+  +-------------------+   |
   |  |   reviews.py   |  |   Knowledge    |  |      Agent        |   |
   |  |   (async)      |  |   Capture      |  |  Orchestration    |   |
   |  +-------+--------+  +-------+--------+  +--------+----------+   |
   +---------|--------------------|----------------------|------------+
             |                    |                      |
             v                    v                      v
   +----------------------+  +----------------------------------+
   |  LiteLLM Proxy       |  |  Knowledge DB (fastembed)        |
   |  localhost:4000      |  |  .knowledge-db/ per project      |
   |  Dynamic discovery   |  |  TCP localhost for fast queries  |
   +----------+-----------+  +----------------------------------+
              |
              v
   +-----------------------------------------------------------------+
   |                     LLM Providers                                |
   |  +------------------+  +-------------------------------------+   |
   |  |  NanoGPT         |  |  OpenRouter                         |   |
   |  |  $15/mo flat     |  |  Pay-per-use                        |   |
   |  +------------------+  +-------------------------------------+   |
   +-----------------------------------------------------------------+
```

### Component Summary

| Component | Count | Description |
|-----------|-------|-------------|
| Models | Dynamic | Via LiteLLM (auto-discovered) |
| Slash Commands | 9 | /kln:quick, multi, agent, rethink, doc, learn, remember, status, help |
| SmolKLN Agents | 8 | code-reviewer, security-auditor, debugger, performance-engineer, rust-expert, c-pro, arm-cortex-expert, orchestrator |
| Hooks | 4 | Python entry points (session, prompt, bash, web) |
| Rules | 1 | ~/.claude/rules/kln.md |

---

## Slash Commands

| Command | Description | Time |
|---------|-------------|------|
| `/kln:quick <focus>` | Single model review | ~30s |
| `/kln:multi <focus>` | 3-5 model consensus | ~60s |
| `/kln:agent <role>` | Specialist agent with tools | ~2min |
| `/kln:rethink` | Contrarian debugging (4 techniques) | ~20s |
| `/kln:doc <title>` | Generate session docs | ~30s |
| `/kln:learn [topic]` | Extract learnings from context (mid-session) | ~30s |
| `/kln:remember` | End-of-session knowledge capture | ~20s |
| `/kln:status` | System health check | ~2s |
| `/kln:help` | Command reference | instant |

**Flags:** `--async` (background), `--models N` (count), `--output json|text`

---

## SmolKLN Agents

Domain experts powered by [smolagents](https://github.com/huggingface/smolagents):

| Agent | Expertise |
|-------|-----------|
| `code-reviewer` | OWASP Top 10, SOLID principles, code quality |
| `security-auditor` | Vulnerabilities, authentication, cryptography |
| `debugger` | Root cause analysis, systematic debugging |
| `performance-engineer` | Profiling, optimization, scalability |
| `rust-expert` | Ownership, lifetimes, unsafe code |
| `c-pro` | C99/C11, POSIX, memory management |
| `arm-cortex-expert` | Embedded ARM, real-time constraints |
| `orchestrator` | Multi-agent coordination |

---

## Hook System (Python Entry Points)

K-LEAN hooks are Python entry points that work cross-platform:

| Entry Point | Hook Type | Purpose |
|-------------|-----------|---------|
| `kln-hook-session` | SessionStart | Auto-start LiteLLM + per-project KB |
| `kln-hook-prompt` | UserPromptSubmit | Keyword detection (FindKnowledge, SaveInfo, etc.) |
| `kln-hook-bash` | PostToolUse (Bash) | Git events -> timeline |
| `kln-hook-web` | PostToolUse (Web*) | Auto-capture web content to KB |

**Keywords detected by prompt handler:**

| Keyword | Action |
|---------|--------|
| `FindKnowledge <query>` | Search KB |
| `SaveInfo <url>` | Smart save URL with LLM evaluation |
| `InitKB` | Initialize project KB |
| `asyncReview` | Background quick review |
| `asyncConsensus` | Background multi-model review |

**Note:** For context-aware knowledge capture, use `/kln:learn` (slash command) instead of hook keywords.

---

## Quick Start

### Installation

```bash
# Install via pipx (recommended)
pipx install kln-ai

# Setup
kln init             # Configure provider + install
kln start            # Start services
kln doctor           # Verify everything works
```

### First Use

```bash
# In Claude Code
/kln:quick security           # Fast review
/kln:multi "error handling"   # Consensus review
/kln:agent security-auditor   # Specialist review
```

### CLI Reference

```bash
# Core
kln init             # Interactive setup (provider + install)
kln install          # Install to ~/.claude/
kln uninstall        # Remove components

# Services
kln start            # Start LiteLLM proxy
kln start -s all     # Start LiteLLM + Knowledge server
kln stop             # Stop all services

# Status
kln status           # Component status
kln doctor [-f]      # Diagnose (auto-fix)
kln model list [--health]  # List models

# Model management
kln model add        # Add model
kln model remove     # Remove model
kln model test       # Test model

# Provider management
kln provider list    # List providers
kln provider add     # Add provider
kln provider set-key # Update API key
```

---

## Project Structure

```
k-lean/
├── src/klean/              # Main package
│   ├── __init__.py         # Version
│   ├── cli.py              # CLI entry point (kln command)
│   ├── platform.py         # Cross-platform utilities (psutil, platformdirs)
│   ├── reviews.py          # Async review engine (httpx)
│   ├── hooks.py            # Hook entry points
│   ├── smol/               # SmolKLN agent system
│   └── data/               # Installable assets
│       ├── scripts/        # Python scripts for knowledge DB
│       ├── commands/kln/   # Slash commands
│       ├── agents/         # SmolKLN agent definitions
│       └── config/         # LiteLLM config templates
├── docs/                   # Documentation
│   └── architecture/       # Technical docs
├── CLAUDE.md               # Claude Code instructions
└── pyproject.toml          # Package metadata
```

### Installation Architecture

After `kln install`, ~/.claude/ contains:

```
~/.claude/
├── scripts/        -> src/klean/data/scripts (Python scripts)
├── commands/kln/   -> src/klean/data/commands/kln
└── rules/          -> src/klean/data/rules

# Hooks are Python entry points (cross-platform):
kln-hook-session    -> klean.hooks:session_start
kln-hook-prompt     -> klean.hooks:prompt_handler
kln-hook-bash       -> klean.hooks:post_bash
kln-hook-web        -> klean.hooks:post_web
```

### Per-Project Isolation

Each git repository gets its own:

```
.knowledge-db/              # Knowledge DB (in .gitignore)
├── entries.jsonl           # V2 schema entries
├── embeddings.npy          # Dense embeddings
└── entries.pkl             # Entry metadata

.claude/kln/                # K-LEAN outputs (in .gitignore)
├── agentExecute/           # SmolKLN agent reports
├── quickReview/            # /kln:quick results
└── quickCompare/           # /kln:multi results
```

---

## Data Flow

### Review Flow
```
/kln:quick -> reviews.quick_review()
  -> httpx async to LiteLLM /chat/completions -> Provider -> response
  -> parse (content || reasoning_content) -> display
```

### Knowledge Capture Flow
```
/kln:learn "topic" -> Claude extracts from context
  -> knowledge-capture.py -> V2 schema
  -> TCP to KB server (immediate index) OR direct to entries.jsonl
```

### Consensus Flow
```
/kln:multi -> reviews.consensus_review()
  -> httpx async parallel to 5 models
  -> collect responses -> parse JSON
  -> group by location similarity
  -> classify by agreement (HIGH/MEDIUM/LOW)
```

---

## Requirements

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.9+ | `python3 --version` |
| Claude Code | 2.0+ | `claude --version` |
| pipx | any | `pipx --version` |
| API Key | - | NanoGPT ($15/mo) or OpenRouter |

---

## Related Documentation

| Document | Description |
|----------|-------------|
| [COMPONENTS.md](COMPONENTS.md) | CLI, Hooks, Knowledge DB, LiteLLM, Reviews, SmolKLN |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Setup, workflow, coding conventions, release |
