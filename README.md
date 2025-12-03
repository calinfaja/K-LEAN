# Claude Agentic Workflow

A multi-tier code review and documentation system for Claude Code with LiteLLM routing to local models.

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Claude (Native) ─── Primary coding agent                      │
│       │                                                         │
│       ├── Hooks (UserPromptSubmit, PostToolUse)                │
│       │       └── Trigger async reviews, post-commit docs      │
│       │                                                         │
│       ├── LiteLLM Proxy (localhost:4000)                       │
│       │       ├── coding-qwen (bugs, memory safety)            │
│       │       ├── architecture-deepseek (design, coupling)     │
│       │       └── tools-glm (MISRA, standards)                 │
│       │                                                         │
│       └── Serena MCP (project docs, memories)                  │
└─────────────────────────────────────────────────────────────────┘
```

## Features

- **Multi-tier reviews**: Quick (Tier 1) → Second Opinion (Tier 2) → Deep Review (Tier 3)
- **Health check + fallback**: Auto-routes to healthy models
- **Async execution**: Run reviews in background via hooks
- **Post-commit docs**: Auto-update Serena memories after commits
- **Consensus reviews**: 3 models in parallel, compare findings

## Quick Reference

| Command | What It Does |
|---------|--------------|
| `/sc:review qwen <focus>` | Quick single-model review |
| `/sc:secondOpinion deepseek <q>` | Get independent opinion |
| `/sc:consensus <focus>` | 3 models in parallel |
| `asyncDeepReview <focus>` | Background 3-model review |

See [COMMANDS_REFERENCE.md](COMMANDS_REFERENCE.md) for full list.

## Structure

```
claudeAgentic/
├── README.md                      # This file
├── COMMANDS_REFERENCE.md          # Quick command reference
├── REVIEW_SYSTEM_DETAILED.md      # Full documentation
├── NEXT_FEATURES/                 # Planned improvements
│   ├── README.md                  # Feature roadmap
│   └── SEMANTIC_MEMORY_SYSTEM.md  # txtai + Serena plan
└── review-system-backup/          # Active configuration
    ├── scripts/                   # Bash scripts
    ├── commands/                  # Slash commands (.md)
    ├── config/                    # Settings files
    └── skills/                    # Skills (if any)
```

## Installation

1. Copy scripts to `~/.claude/scripts/`
2. Copy settings to `~/.claude/settings.json`
3. Copy commands to `~/.claude/commands/sc/`
4. Start LiteLLM: `start-nano-proxy`
5. Restart Claude

## Requirements

- Claude Code CLI
- LiteLLM proxy with NanoGPT models
- Serena MCP server
- jq (for JSON parsing)

## License

MIT
