# Claude Agentic Workflow

A multi-tier code review and documentation system for Claude Code with LiteLLM routing to local models.

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Claude (Native) ─── Primary coding agent                      │
│       │                                                         │
│       ├── Hooks (UserPromptSubmit, PostToolUse)                │
│       │       └── Trigger async reviews, health checks         │
│       │                                                         │
│       ├── LiteLLM Proxy (localhost:4000)                       │
│       │       ├── coding-qwen (Qwen 3 Coder)                   │
│       │       ├── architecture-deepseek (DeepSeek V3 Thinking) │
│       │       ├── tools-glm (GLM 4.6 Thinking)                 │
│       │       ├── research-minimax (MiniMax M2)                │
│       │       ├── agent-kimi (Kimi K2 Thinking)                │
│       │       └── scripting-hermes (Hermes 4)                  │
│       │                                                         │
│       └── Serena MCP (project docs, memories)                  │
└─────────────────────────────────────────────────────────────────┘
```

## Features

- **6 Models**: qwen, deepseek, glm, minimax, kimi, hermes via NanoGPT
- **Multi-tier reviews**: Quick (Tier 1) → Second Opinion (Tier 2) → Deep Review (Tier 3)
- **Health check + fallback**: Auto-routes to healthy models, type `healthcheck` to verify
- **Session folders**: Each Claude instance gets its own output folder
- **Async execution**: Run reviews in background via hooks
- **Consensus reviews**: 3 models in parallel, compare findings

## Quick Reference

| Command | What It Does |
|---------|--------------|
| `healthcheck` | Check all 6 models health |
| `/sc:review qwen <focus>` | Quick single-model review |
| `/sc:secondOpinion deepseek <q>` | Get independent opinion |
| `/sc:consensus <focus>` | 3 models in parallel |
| `asyncDeepReview <focus>` | Background 3-model review |

See [COMMANDS_REFERENCE.md](COMMANDS_REFERENCE.md) for full list.

## Output Structure

```
/tmp/claude-reviews/
├── 2024-12-03-143005/      # Claude instance 1 (session folder)
│   ├── quick-qwen-143022.json
│   ├── opinion-deepseek-143500.json
│   └── consensus-all-144000.json
└── 2024-12-03-150000/      # Claude instance 2 (different session)
    └── deep-glm-150030.txt
```

## Scripts

| Script | Purpose |
|--------|---------|
| `start-litellm.sh` | Start LiteLLM proxy (ensures port 4000) |
| `health-check.sh` | Test all models |
| `quick-review.sh` | Single model API review |
| `second-opinion.sh` | Get second opinion from model |
| `consensus-review.sh` | 3 models in parallel (API) |
| `deep-review.sh` | Headless Claude with tools |
| `parallel-deep-review.sh` | 3 headless Claude instances |
| `async-dispatch.sh` | Hook dispatcher for async keywords |
| `session-helper.sh` | Session folder management |
| `test-system.sh` | Verify system works |

## Installation

1. Copy scripts to `~/.claude/scripts/`
2. Copy settings to `~/.claude/settings.json`
3. Copy commands to `~/.claude/commands/sc/`
4. Add alias to `~/.bashrc`: `alias start-nano-proxy='~/.claude/scripts/start-litellm.sh'`
5. Start LiteLLM: `start-nano-proxy`
6. Restart Claude

## Requirements

- Claude Code CLI
- LiteLLM proxy with NanoGPT models
- Serena MCP server (optional)
- jq, curl (for JSON parsing)

## License

MIT
