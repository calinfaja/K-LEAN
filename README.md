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
- **Semantic search**: `FindKnowledge <query>`
- **Headless integration**: Review scripts inject relevant prior knowledge

### Infrastructure
- **Health check + fallback**: Auto-routes to healthy models
- **Session folders**: Each Claude instance gets its own output folder
- **Sync verification**: Check scripts/commands/config against backup

## Quick Start

```bash
# Check all models
healthcheck

# Run code review
/kln:review qwen security vulnerabilities

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

## Directory Structure

```
~/claudeAgentic/                    # This repository
├── docs/                           # Documentation
├── review-system-backup/           # Backup of all scripts/commands/config
│   ├── scripts/
│   ├── commands/                   # SuperClaude commands backup
│   ├── commands-kln/               # Custom /kln: commands backup
│   └── config/
└── NEXT_FEATURES/                  # Feature ideas

~/.claude/                          # Active Claude configuration
├── scripts/                        # All executable scripts
├── commands/
│   ├── sc/                         # SuperClaude commands (30)
│   └── kln/                        # Custom review commands (12)
├── settings.json                   # Hooks and configuration
└── CLAUDE.md                       # System instructions

~/.venvs/knowledge-db/              # txtai virtual environment
/tmp/claude-reviews/                # Review outputs
```

## Requirements

- Claude Code CLI
- LiteLLM proxy with NanoGPT API key
- Python 3.10+ with txtai
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
