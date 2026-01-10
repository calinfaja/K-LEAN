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

## Hook Keywords (Type directly)

| Keyword | Action |
|---------|--------|
| `FindKnowledge <query>` | Search knowledge DB |
| `SaveInfo <url>` | Evaluate URL with LLM and save if relevant |

## Knowledge Database

Per-project semantic search. **Auto-initializes on first use.**

Queries go through the TCP server (~30ms) which auto-starts on session begin.

**Storage**: `.knowledge-db/` per project | **Server**: TCP on port 14000+hash

## K-LEAN CLI

```bash
kln status           # Component status
kln doctor -f        # Diagnose + auto-fix
kln start            # Start services
kln model list       # List available models
kln admin test       # Run test suite
```

## Available Models

**Dynamic discovery** from LiteLLM proxy. Models depend on your configuration.

```bash
kln model list              # List all available models
kln model list --health     # Check model health status
```

Configure in `~/.config/litellm/config.yaml`. Supports NanoGPT, OpenRouter, Ollama, etc.

## Profiles

| Command | Profile | Backend |
|---------|---------|---------|
| `claude` | Native | Anthropic API |
| `claude-nano` | NanoGPT | LiteLLM localhost:4000 |

## Timeline

Chronological log at `.knowledge-db/timeline.txt`

Events logged automatically by hooks. Query via Knowledge DB search.

## LiteLLM Setup

```bash
kln init --provider nanogpt --api-key $KEY    # Configure provider
kln start                                      # Start LiteLLM proxy
```

Providers: NanoGPT, OpenRouter, Ollama (any OpenAI-compatible)

## Serena Memories

Curated insights via `mcp__serena__*_memory` tools:
- `lessons-learned` - Gotchas, patterns
- `architecture-review-system` - System docs

## Hooks

- **PostToolUse (Bash)**: Post-commit docs, timeline
- **PostToolUse (Web*)**: Auto-capture to knowledge DB
