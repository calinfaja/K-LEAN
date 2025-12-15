# Claude System Configuration

## Quick Commands (Type these directly)

| Shortcut | Action |
|----------|--------|
| `healthcheck` | Check all 6 LiteLLM models |
| `qreview <model> <focus>` | Quick single-model review |
| `dreview <model> <focus>` | Deep review with tools |
| `droid <model> <type> <task>` | Execute Factory droid |
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

## Review System

Multi-model review via LiteLLM proxy (localhost:4000).

| Keyword | Description |
|---------|-------------|
| `asyncDeepReview <focus>` | 3 models with tools (bg) |
| `asyncConsensus <focus>` | 3 models quick (bg) |
| `asyncReview <model> <focus>` | Single model quick (bg) |

**Models**: qwen (quality), deepseek (arch), glm (standards), minimax (research), kimi (agents), hermes (scripts)

## K-LEAN CLI

```bash
k-lean status     # Component status
k-lean doctor -f  # Diagnose + auto-fix
k-lean start      # Start services
k-lean debug      # Monitoring dashboard
k-lean models     # List with health
```

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
