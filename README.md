# Claude Agentic Workflow

A multi-tier code review and semantic knowledge system for Claude Code with LiteLLM routing to local models.

## Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Claude (Native) ─── Primary coding agent                               │
│       │                                                                 │
│       ├── Hooks (UserPromptSubmit, PostToolUse)                        │
│       │       ├── Trigger async reviews, health checks                 │
│       │       ├── Capture knowledge (GoodJob, SaveThis)                │
│       │       └── Auto-capture web research                            │
│       │                                                                 │
│       ├── LiteLLM Proxy (localhost:4000)                               │
│       │       ├── coding-qwen (Qwen 3 Coder)                           │
│       │       ├── architecture-deepseek (DeepSeek V3)                  │
│       │       ├── tools-glm (GLM 4.6)                                  │
│       │       ├── research-minimax (MiniMax M2)                        │
│       │       ├── agent-kimi (Kimi K2)                                 │
│       │       └── scripting-hermes (Hermes 4)                          │
│       │                                                                 │
│       ├── Knowledge DB (txtai + SQLite)                                │
│       │       └── Per-project semantic search                          │
│       │                                                                 │
│       └── Serena MCP (project docs, memories)                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Features

### Multi-Model Code Review
- **6 Models**: qwen, deepseek, glm, minimax, kimi, hermes via NanoGPT
- **3-Tier Reviews**: Quick -> Second Opinion -> Deep Review
- **Consensus Reviews**: 3 models in parallel, compare findings
- **Async Execution**: Run reviews in background via hooks

### Semantic Knowledge System
- **Per-project knowledge database** using txtai
- **Manual capture**: `GoodJob <url>`, `SaveThis <lesson>`
- **Auto-capture**: PostToolUse hooks on WebFetch/WebSearch
- **Automatic fact generation**: Extract patterns from reviews and commits using native Haiku
- **Semantic search**: `FindKnowledge <query>`
- **Headless integration**: Review scripts inject relevant prior knowledge
- **TOON Integration**: Token-Oriented Object Notation format for 2-10% token reduction on extractions

### Infrastructure
- **Health check + fallback**: Auto-routes to healthy models
- **Session folders**: Each Claude instance gets its own output folder
- **Sync verification**: Check scripts/commands/config against backup
- **Profile system**: Run native and nano modes simultaneously

## Profile System

K-LEAN uses `CLAUDE_CONFIG_DIR` for clean profile separation:

```bash
claude        # Native Anthropic (default)
claude-nano   # NanoGPT via LiteLLM proxy
claude-status # Show current profile
```

Both can run **simultaneously** in different terminals - no more settings file switching!

```
~/.claude/           # Native profile
~/.claude-nano/      # NanoGPT profile (symlinks to shared resources)
```

## Installation

### One-Line Install (New Machine)
```bash
git clone https://github.com/yourusername/claudeAgentic.git
cd claudeAgentic/review-system-backup
./install.sh --full
```

### Options
```bash
./install.sh --full      # Complete installation (includes nano profile)
./install.sh --minimal   # Scripts only
./install.sh --check     # Verify installation
./update.sh              # Pull updates and reinstall
./test.sh                # Run test suite (18 tests)
```

### Post-Install: Add to ~/.bashrc
```bash
alias claude-nano='CLAUDE_CONFIG_DIR=~/.claude-nano claude'
alias claude-status='if [ -n "$CLAUDE_CONFIG_DIR" ]; then echo "Profile: nano"; else echo "Profile: native"; fi'
```

### Prerequisites
- Claude Code CLI
- Python 3.9+
- LiteLLM (`pipx install litellm`)
- API key for your chosen provider (NanoGPT, OpenRouter, or local Ollama)

### Setup LiteLLM

The installer includes an interactive setup wizard for configuring LiteLLM:

```bash
./install.sh --full
# → Prompts to configure provider (NanoGPT / OpenRouter / Ollama)
```

Or reconfigure anytime:
```bash
~/.claude/scripts/setup-litellm.sh
```

## Quick Start

```bash
# Check all models
healthcheck

# Run code review
/kln:quickReview qwen security vulnerabilities

# Capture knowledge
GoodJob https://example.com/docs focus on authentication
SaveThis learned that connection pooling improves performance 10x

# Search knowledge
FindKnowledge authentication patterns

# Run async deep review
asyncDeepReview security audit
```

## Documentation

| Document | Description |
|----------|-------------|
| [docs/INSTALLATION.md](docs/INSTALLATION.md) | Step-by-step setup guide for new machines |
| [docs/COMMANDS_REFERENCE.md](docs/COMMANDS_REFERENCE.md) | All commands and keywords |
| [docs/REVIEW_SYSTEM.md](docs/REVIEW_SYSTEM.md) | Multi-model review architecture |
| [docs/KNOWLEDGE_SYSTEM.md](docs/KNOWLEDGE_SYSTEM.md) | Semantic knowledge database |
| [docs/TOON_PROJECT_COMPLETE.md](docs/TOON_PROJECT_COMPLETE.md) | TOON format integration - production ready |
| [docs/TOON_TECHNICAL_SPEC.md](docs/TOON_TECHNICAL_SPEC.md) | TOON format API reference |

## Directory Structure

```
~/claudeAgentic/                    # This repository
├── docs/                           # Documentation
├── review-system-backup/           # Backup of all scripts/commands/config
│   ├── scripts/
│   ├── commands/kln/               # Custom /kln: commands
│   ├── commands/sc/                # SuperClaude commands
│   └── config/
└── NEXT_FEATURES/                  # Feature ideas

~/.claude/                          # Native profile (default)
├── scripts/                        # All executable scripts
├── commands/
│   ├── sc/                         # SuperClaude commands (31)
│   └── kln/                        # Custom review commands (13)
├── hooks/                          # Event hooks
├── settings.json                   # Native API configuration
└── CLAUDE.md                       # System instructions

~/.claude-nano/                     # NanoGPT profile
├── settings.json                   # LiteLLM proxy configuration
├── commands -> ~/.claude/commands  # Symlink
├── scripts -> ~/.claude/scripts    # Symlink
└── hooks -> ~/.claude/hooks        # Symlink

~/.venvs/knowledge-db/              # txtai virtual environment
/tmp/claude-reviews/                # Review outputs
```

## Requirements

- Claude Code CLI
- Python 3.9+
- LiteLLM (`pipx install litellm`)
- API key for chosen provider (NanoGPT, OpenRouter, or local Ollama)
- jq, curl, bc (for scripts)
- Serena MCP server (optional)

## Maintenance

```bash
# Verify all scripts synced with backup
~/.claude/scripts/sync-check.sh

# Sync differences to backup
~/.claude/scripts/sync-check.sh --sync

# Test system health
~/.claude/scripts/test-system.sh
```

## License

MIT
