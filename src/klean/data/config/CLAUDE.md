# Claude System Configuration

## K-LEAN Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/kln:quick` | Fast review - single model (~30s) | `/kln:quick security` |
| `/kln:multi` | Consensus review - 3-5 models (~60s) | `/kln:multi --models 5 arch` |
| `/kln:agent` | SmolKLN agents - specialist analysis | `/kln:agent --role security` |
| `/kln:rethink` | Fresh perspectives - debugging help | `/kln:rethink bug` |
| `/kln:doc` | Documentation - session notes | `/kln:doc "Sprint Review"` |
| `/kln:remember` | Knowledge capture - end of session | `/kln:remember` |
| `/kln:status` | System status - models, health | `/kln:status` |
| `/kln:help` | Command reference | `/kln:help` |

**Flags**: `--async` (background), `--models N` (count), `--output json/text`

## Quick Commands (Type directly)

| Shortcut | Action |
|----------|--------|
| `SaveThis <lesson>` | Save a lesson learned |
| `FindKnowledge <query>` | Search knowledge DB |

## Knowledge Database

Per-project semantic search. **Auto-initializes on first SaveThis.**

```bash
# Query via server (~30ms)
~/.claude/scripts/knowledge-query.sh "<topic>"

# Direct query (~17s cold)
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-search.py "<query>"
```

**Storage**: `.knowledge-db/` per project | **Server**: Auto-starts on first use

## K-LEAN CLI

```bash
k-lean status     # Component status
k-lean doctor -f  # Diagnose + auto-fix
k-lean start      # Start services
k-lean models     # List with health
k-lean test       # Run test suite
```

## Available Models

**Dynamic discovery** from LiteLLM proxy. Models depend on your configuration.

```bash
k-lean models          # List all available models
k-lean models --first  # Show default model
```

Configure in `~/.config/litellm/config.yaml`. Supports NanoGPT, OpenRouter, Ollama, etc.

## Profiles

| Command | Profile | Backend |
|---------|---------|---------|
| `claude` | Native | Anthropic API |
| `claude-nano` | NanoGPT | LiteLLM localhost:4000 |

## Timeline

Chronological log at `.knowledge-db/timeline.txt`

```bash
~/.claude/scripts/timeline-query.sh [today|week|commits|reviews|<search>]
```

## LiteLLM Setup

```bash
k-lean setup      # Interactive configuration
k-lean start      # Start LiteLLM proxy
```

Providers: NanoGPT, OpenRouter, Ollama (any OpenAI-compatible)

## Serena Memories

Curated insights via `mcp__serena__*_memory` tools:
- `lessons-learned` - Gotchas, patterns
- `architecture-review-system` - System docs

## Hooks

- **PostToolUse (Bash)**: Post-commit docs, timeline
- **PostToolUse (Web*)**: Auto-capture to knowledge DB
