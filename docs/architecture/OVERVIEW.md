# K-LEAN Overview

> **Multi-Model Code Reviews & Persistent Knowledge for Claude Code**

**Version:** 1.0.0-beta | **License:** Apache 2.0

---

## What is K-LEAN?

K-LEAN (Knowledge-Lean) is an addon for Claude Code that provides:

- **18 LLM models** via LiteLLM proxy (dynamic discovery)
- **Consensus reviews** from 3-5 models in parallel
- **Persistent Knowledge DB** with semantic search (210+ entries)
- **8 SmolKLN agents** for domain-specific analysis
- **10 slash commands** for reviews, debugging, and documentation
- **5 hooks** for automatic knowledge capture

### The Problem

Claude Code uses a single AI model. K-LEAN adds:
- Multiple perspectives on code quality
- Persistent memory across sessions
- Specialized domain expertise

### Positioning

**K-LEAN is an ADDON, not a replacement.** Works alongside Claude Code and other extensions (SuperClaude, Serena MCP, Context7).

---

## Architecture

```
                          Claude Code
   ┌─────────────────────────────────────────────────────────────┐
   │  ┌──────────────┐  ┌─────────────┐  ┌────────────────────┐  │
   │  │    Hooks     │  │  /kln:*     │  │   SmolKLN Agents   │  │
   │  │  (5 total)   │  │  Commands   │  │  (8 specialists)   │  │
   │  └──────┬───────┘  └──────┬──────┘  └─────────┬──────────┘  │
   └─────────┼─────────────────┼───────────────────┼─────────────┘
             │                 │                   │
             ▼                 ▼                   ▼
   ┌─────────────────────────────────────────────────────────────┐
   │                      K-LEAN Layer                            │
   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
   │  │   Review     │  │  Knowledge   │  │    Agent         │   │
   │  │   Engine     │  │  Capture     │  │  Orchestration   │   │
   │  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘   │
   └─────────┼─────────────────┼───────────────────┼─────────────┘
             │                 │                   │
             ▼                 ▼                   ▼
   ┌─────────────────────┐  ┌──────────────────────────────────┐
   │  LiteLLM Proxy      │  │  Knowledge DB (txtai)            │
   │  localhost:4000     │  │  .knowledge-db/ per project      │
   │  18 models          │  │  Unix socket for fast queries    │
   └──────────┬──────────┘  └──────────────────────────────────┘
              │
              ▼
   ┌─────────────────────────────────────────────────────────────┐
   │                    LLM Providers                             │
   │  ┌─────────────────┐  ┌─────────────────────────────────┐   │
   │  │  NanoGPT        │  │  OpenRouter                     │   │
   │  │  $15/mo flat    │  │  Pay-per-use                    │   │
   │  └─────────────────┘  └─────────────────────────────────┘   │
   └─────────────────────────────────────────────────────────────┘
```

### Component Summary

| Component | Count | Description |
|-----------|-------|-------------|
| Models | 18 | Via LiteLLM (dynamic discovery) |
| Slash Commands | 10 | /kln:quick, multi, deep, agent, rethink, doc, learn, remember, status, help |
| SmolKLN Agents | 8 | code-reviewer, security-auditor, debugger, performance-engineer, rust-expert, c-pro, arm-cortex-expert, orchestrator |
| Hooks | 5 | FindKnowledge, SaveInfo, async reviews, session-start, post-tool |
| Rules | 1 | ~/.claude/rules/k-lean.md |

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

## Hook Keywords

Type directly in Claude Code:

| Keyword | Action |
|---------|--------|
| `FindKnowledge <query>` | Semantic search knowledge DB |
| `SaveInfo <url>` | Smart save URL with LLM evaluation |
| `asyncReview <focus>` | Background quick review |
| `asyncConsensus <focus>` | Background multi-model review |

**Note:** For context-aware knowledge capture, use `/kln:learn` (slash command) instead of hook keywords.

---

## Quick Start

### Installation

```bash
# Clone and install
git clone https://github.com/calinfaja/k-lean.git
cd k-lean
pipx install .

# Setup
k-lean install          # Deploy to ~/.claude/
k-lean setup            # Configure API (interactive)
k-lean doctor           # Verify everything works
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
k-lean install          # Install to ~/.claude/
k-lean setup            # Configure API provider
k-lean uninstall        # Remove components

# Services
k-lean start            # Start LiteLLM proxy
k-lean start -s all     # Start LiteLLM + Knowledge server
k-lean stop             # Stop all services

# Status
k-lean status           # Component status
k-lean doctor [-f]      # Diagnose (auto-fix)
k-lean models [--health]# List models

# Development
k-lean test             # Run test suite
k-lean debug            # Live monitoring
```

---

## Project Structure

```
k-lean/
├── src/klean/              # Main package
│   ├── __init__.py         # Version: 1.0.0-beta
│   ├── cli.py              # CLI entry point
│   ├── smol/               # SmolKLN agent system
│   └── data/               # Installable assets
│       ├── scripts/        # 36+ shell & Python scripts
│       ├── commands/kln/   # 10 slash commands
│       ├── hooks/          # 5 Claude Code hooks
│       ├── agents/         # 8 SmolKLN agent definitions
│       └── core/           # Review engine & prompts
├── docs/                   # User documentation
├── .agents/                # Technical documentation
├── CLAUDE.md               # Claude Code instructions
└── AGENTS.md               # Universal AI instructions
```

### Symlink Architecture

After `k-lean install`, ~/.claude/ contains:

```
~/.claude/
├── scripts/        -> src/klean/data/scripts
├── commands/kln/   -> src/klean/data/commands/kln
├── hooks/          -> src/klean/data/hooks
├── lib/            -> src/klean/data/lib
└── rules/          -> src/klean/data/rules
```

### Per-Project Isolation

Each git repository gets its own:

```
.knowledge-db/              # Knowledge DB (in .gitignore)
├── entries.jsonl           # V2 schema entries
└── index/                  # Semantic embeddings

.claude/kln/                # K-LEAN outputs (in .gitignore)
├── agentExecute/           # SmolKLN agent reports
├── quickReview/            # /kln:quick results
└── quickCompare/           # /kln:multi results
```

---

## Data Flow

### Review Flow
```
/kln:quick -> hooks -> quick-review.sh
  -> LiteLLM /chat/completions -> Provider -> response
  -> parse (content || reasoning_content) -> display
```

### Knowledge Capture Flow
```
/kln:learn "topic" -> Claude extracts from context
  -> knowledge-capture.py -> V2 schema -> entries.jsonl
  -> txtai re-index (on next query)
```

### Consensus Flow
```
/kln:multi -> consensus-review.sh
  -> parallel curl to 5 models
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
| [project-overview.md](project-overview.md) | Problem/solution context |
| [architecture.md](architecture.md) | Detailed system design |
| [smolkln-implementation.md](smolkln-implementation.md) | Agent system details |
| [knowledge-db.md](knowledge-db.md) | Semantic memory system |
| [review-system.md](review-system.md) | Multi-model pipeline |
| [troubleshooting.md](troubleshooting.md) | Common issues & fixes |
