# K-LEAN v3.0

Knowledge-driven Lightweight Execution & Analysis Network for Claude Code.

## Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Claude (Native) ─── Primary coding agent                               │
│       │                                                                 │
│       ├── Hooks (UserPromptSubmit, PostToolUse)                        │
│       │       ├── SaveThis, FindKnowledge, healthcheck                 │
│       │       └── Auto-capture web research                            │
│       │                                                                 │
│       ├── LiteLLM Proxy (localhost:4000) - 12 NanoGPT models           │
│       │       ├── qwen3-coder, devstral-2 (coding)                     │
│       │       ├── deepseek-r1, deepseek-v3-thinking (reasoning)        │
│       │       ├── glm-4.6-thinking, kimi-k2-thinking (analysis)        │
│       │       ├── llama-4-scout, llama-4-maverick (speed)              │
│       │       └── minimax-m2, hermes-4-70b, qwen3-235b                 │
│       │                                                                 │
│       ├── Knowledge DB (txtai + per-project server)                    │
│       │       └── Auto-initializes on first SaveThis                   │
│       │                                                                 │
│       └── Serena MCP (project docs, memories)                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Features

### V3 Commands
| Command | Description |
|---------|-------------|
| `/kln:quick <focus>` | Fast single-model review (~30s) |
| `/kln:multi <focus>` | Multi-model consensus (~60s) |
| `/kln:deep <focus>` | Deep analysis with tools (~3min) |
| `/kln:droid <task>` | Factory Droid specialists |
| `/kln:rethink <focus>` | Fresh debugging perspectives |
| `/kln:doc <title>` | Create session documentation |
| `/kln:remember` | End-of-session knowledge capture |
| `/kln:status` | System health and models |
| `/kln:help` | Command reference |

### Semantic Knowledge System
- **Per-project knowledge database** using txtai
- **Auto-initializes** on first `SaveThis` command
- **Manual capture**: `SaveThis <lesson>`
- **Semantic search**: `FindKnowledge <query>`
- **Per-project server**: Fast queries via Unix socket

### Infrastructure
- **12 NanoGPT models** via LiteLLM proxy
- **K-LEAN CLI**: `k-lean status`, `k-lean doctor -f`, `k-lean test`
- **Profile system**: Run native and nano modes simultaneously
- **Config validation**: Prevents common LiteLLM config errors

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
# Check system health
k-lean status
healthcheck

# Run code review
/kln:quick security vulnerabilities
/kln:multi --models 3 architecture

# Capture knowledge
SaveThis "Connection pooling improves performance 10x"

# Search knowledge
FindKnowledge authentication patterns

# Deep analysis
/kln:deep security audit
```

## Documentation

**[Complete Documentation Index](docs/INDEX.md)** - Full navigation of all K-LEAN documentation

### Quick Links

| Document | Description |
|----------|-------------|
| [Quick Start Guide](docs/guides/QUICK_START.md) | Get started in 5 minutes |
| [Installation Guide](docs/guides/INSTALLATION.md) | Step-by-step setup for new machines |
| [User Guide](docs/guides/USER_GUIDE.md) | Complete command reference and workflows |
| [System Architecture](docs/architecture/SYSTEMS.md) | How K-LEAN works internally |
| [Droid System](docs/architecture/DROIDS.md) | Factory Droid specialists and integration |
| [CryptoLib Usage Guide](docs/guides/CRYPTOLIB_USAGE_GUIDE.md) | Using the CryptoLib Implementation Droid |

### All Documentation Sections

- **[docs/guides/](docs/guides/)** - User guides and tutorials
- **[docs/architecture/](docs/architecture/)** - System architecture and design
- **[docs/specs/](docs/specs/)** - Technical specifications
- **[docs/reports/](docs/reports/)** - Implementation reports and results

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
│   ├── sc/                         # SuperClaude commands
│   └── kln/                        # K-LEAN V3 commands (9)
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
