# K-LEAN: Multi-Model Code Review & Knowledge System

A comprehensive code review and semantic knowledge capture system for Claude Code, using LiteLLM to route to multiple AI models.

## Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Claude (Native) ─── Primary coding agent                               │
│       │                                                                 │
│       ├── Hooks ──────────────────────────────────────────────────────┐│
│       │   ├── UserPromptSubmit: Keywords, async dispatch, capture     ││
│       │   └── PostToolUse: Auto-capture, post-commit docs             ││
│       │                                                                 │
│       ├── LiteLLM Proxy (localhost:4000) ─────────────────────────────┐│
│       │   ├── qwen3-coder         - Code quality, bugs                ││
│       │   ├── deepseek-v3-thinking - Architecture, design             ││
│       │   ├── glm-4.6-thinking    - Standards, compliance             ││
│       │   ├── minimax-m2          - Research                          ││
│       │   ├── kimi-k2-thinking    - Agent tasks                       ││
│       │   └── hermes-4-70b        - Scripting                         ││
│       │                                                                 │
│       ├── Knowledge DB ───────────────────────────────────────────────┐│
│       │   ├── txtai semantic search (~30ms with server)               ││
│       │   ├── Per-project storage (.knowledge-db/)                    ││
│       │   └── Timeline tracking                                       ││
│       │                                                                 │
│       ├── TOON Adapter ───────────────────────────────────────────────┐│
│       │   └── ~18% token reduction for knowledge transmission         ││
│       │                                                                 │
│       └── Persistent Output ──────────────────────────────────────────┐│
│           └── .claude/kln/{quickReview,deepInspect,...}/*.md          ││
└─────────────────────────────────────────────────────────────────────────┘
```

## Features

| Feature | Description |
|---------|-------------|
| **Dynamic Model Discovery** | Auto-detect models from LiteLLM API, no hardcoding |
| **Multi-Model Reviews** | 6 models via NanoGPT, health-check with fallback |
| **4-Tier System** | Quick → Consensus → Deep Inspect → Deep Audit |
| **Knowledge Capture** | Manual (`GoodJob`, `SaveThis`) + auto-capture hooks |
| **Semantic Search** | Fast txtai queries (~30ms via server daemon) |
| **TOON Compression** | ~18% token reduction for LLM transmission |
| **Persistent Output** | Reviews saved to `.claude/kln/` in project |
| **Timeline Tracking** | Chronological log of reviews, commits, lessons |
| **Profile System** | Run native + nano profiles simultaneously |

## Quick Start

```bash
# Install
git clone https://github.com/calinfaja/K-LEAN-Companion.git
cd K-LEAN-Companion/review-system-backup
./install.sh --full

# See available models
/kln:models                              # List all models from LiteLLM

# Run reviews (use exact model names from /kln:models)
/kln:quickReview qwen3-coder security           # Single model review
/kln:quickCompare architecture                  # Auto: 5 healthy models
/kln:deepInspect qwen3-coder full audit         # Headless with tools

# Capture knowledge
GoodJob https://docs.example.com         # Capture URL
SaveThis learned X improves Y            # Capture lesson
SaveInfo pattern for secure authentication     # Smart capture with eval

# Search knowledge
FindKnowledge authentication patterns    # Semantic search
```

## Documentation

| Document | Description |
|----------|-------------|
| [docs/INSTALLATION.md](docs/INSTALLATION.md) | Complete setup guide |
| [docs/REVIEW-SYSTEM.md](docs/REVIEW-SYSTEM.md) | Multi-model review architecture |
| [docs/KNOWLEDGE-SYSTEM.md](docs/KNOWLEDGE-SYSTEM.md) | Semantic knowledge database |
| [docs/HOOKS.md](docs/HOOKS.md) | Event hooks configuration |
| [docs/TOON-ADAPTER.md](docs/TOON-ADAPTER.md) | Token compression system |
| [docs/COMMANDS.md](docs/COMMANDS.md) | All slash commands reference |

## Directory Structure

```
~/.claude/                          # Native profile
├── scripts/                        # All executable scripts
├── commands/kln/                   # /kln: review commands
├── hooks/                          # Event hooks
└── CLAUDE.md                       # System instructions

~/.claude-nano/                     # NanoGPT profile (symlinks)
~/.venvs/knowledge-db/              # txtai + dependencies
~/.config/litellm/                  # LiteLLM configuration

<project>/
├── .claude/kln/                    # Persistent review outputs
│   ├── quickReview/
│   ├── quickCompare/
│   ├── deepInspect/
│   └── asyncDeepAudit/
└── .knowledge-db/                  # Per-project knowledge
    ├── entries.jsonl
    ├── timeline.txt
    └── index/
```

## Models Available

Models are **dynamically discovered** from LiteLLM. Run `/kln:models` to see available models.

Common models (if configured in LiteLLM):

| LiteLLM Model | Specialization |
|---------------|----------------|
| qwen3-coder | Code quality, bugs |
| deepseek-v3-thinking | Architecture, design |
| glm-4.6-thinking | Standards, MISRA |
| minimax-m2 | Research |
| kimi-k2-thinking | Agent tasks |
| hermes-4-70b | Scripting |

**Note:** Use exact model names from `/kln:models` output. Aliases removed - auto-discovery replaces them.

## Requirements

- Claude Code CLI
- Python 3.9+
- LiteLLM (`pipx install litellm`)
- NanoGPT API key (or OpenRouter)
- jq, curl (for scripts)

## License

MIT
