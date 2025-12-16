# Claude System Configuration

## K-LEAN v1.0.0-beta Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/kln:quick` | Fast single-model review (~30s) | `/kln:quick security` |
| `/kln:multi` | Multi-model consensus | `/kln:multi --models 5 arch` |
| `/kln:deep` | Thorough with SDK tools | `/kln:deep --async security` |
| `/kln:droid` | Role-based AI workers | `/kln:droid --role coder` |
| `/kln:rethink` | Fresh debugging perspectives | `/kln:rethink bug` |
| `/kln:status` | Check models & health | `/kln:status` |
| `/kln:help` | Complete reference | `/kln:help` |

**Flags**: `--async` (background), `--models N` (count), `--output json/text`

## Quick Commands (Type directly)

| Shortcut | Action |
|----------|--------|
| `healthcheck` | Check all LiteLLM models |
| `GoodJob <url>` | Capture web knowledge |
| `SaveThis <lesson>` | Save a lesson learned |
| `FindKnowledge <query>` | Search knowledge DB |

## Knowledge Database

Fast semantic search for stored knowledge (URLs, solutions, lessons).

```bash
# Query via server (~30ms)
~/.claude/scripts/knowledge-query.sh "<topic>"

# Direct query (~17s cold)
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-search.py "<query>"
```

**Storage**: `.knowledge-db/` per project | **Server**: Auto-starts via ~/.bashrc

## K-LEAN CLI

```bash
k-lean status     # Component status (9 commands, 12 models)
k-lean doctor -f  # Diagnose + auto-fix
k-lean start      # Start services
k-lean debug      # Monitoring dashboard
k-lean models     # List with health
```

## Available Models (12)

Auto-discovered from LiteLLM. Use `k-lean models` to see current list.

Common models: `qwen3-coder`, `deepseek-v3-thinking`, `glm-4.6-thinking`, `kimi-k2-thinking`, `minimax-m2`

## Profiles

| Command | Profile | Backend |
|---------|---------|---------|
| `claude` | Native | Anthropic API |
| `claude-nano` | NanoGPT | LiteLLM localhost:4000 |

Check: `claude-status`

## Timeline

Chronological log at `.knowledge-db/timeline.txt`

```bash
~/.claude/scripts/timeline-query.sh [today|week|commits|reviews|<search>]
```

## LiteLLM Setup

```bash
~/.claude/scripts/setup-litellm.sh
```

Providers: NanoGPT ($0.50/1M), OpenRouter, Ollama (local)

## Serena Memories

Curated insights via `mcp__serena__*_memory` tools:
- `lessons-learned` - Gotchas, patterns
- `architecture-review-system` - System docs

## Hooks

- **UserPromptSubmit**: Review dispatch, GoodJob, healthcheck
- **PostToolUse (Bash)**: Post-commit docs, timeline
- **PostToolUse (Web*)**: Auto-capture to knowledge DB
