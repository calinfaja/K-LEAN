# Claude System Configuration

## K-LEAN Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/kln:quick` | Fast review - single model (~30s) | `/kln:quick security` |
| `/kln:multi` | Consensus review - 3-5 models (~60s) | `/kln:multi --models 5 arch` |
| `/kln:agent` | SmolKLN - specialist agents | `/kln:agent --role security` |
| `/kln:rethink` | Fresh perspectives - debugging help | `/kln:rethink bug` |
| `/kln:doc` | Documentation - session notes | `/kln:doc "Sprint Review"` |
| `/kln:learn` | Save learnings from context (mid-session) | `/kln:learn "auth bug"` |
| `/kln:remember` | Knowledge capture - end of session | `/kln:remember` |
| `/kln:status` | System status - models, health | `/kln:status` |
| `/kln:help` | Command reference | `/kln:help` |

**Flags**: `--async` (background), `--models N` (count), `--output json/text`

## Quick Commands (Type directly)

| Shortcut | Action |
|----------|--------|
| `FindKnowledge <query>` | Search knowledge DB |
| `SaveInfo <url>` | Smart save URL with LLM evaluation |

## Knowledge Database

Per-project semantic search. **Auto-initializes on first use.**

### Saving Knowledge

**Recommended:** Use `/kln:learn` - context-aware extraction from session:
```bash
/kln:learn                    # Auto-detect learnings from recent context
/kln:learn "auth bug"         # Focused extraction on specific topic
```

**Hook keywords:**
```bash
FindKnowledge <query>         # Semantic search
SaveInfo <url>                # Evaluate URL and save if relevant
```

### Direct Script Usage (for automation)
```bash
# Capture entry - CORRECT syntax (no "add" subcommand)
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-capture.py \
    "lesson text here" \
    --type lesson \
    --tags tag1,tag2 \
    --priority medium

# Types: lesson, finding, solution, pattern, warning, best-practice
# Priority: low, medium, high, critical

# Query via server (~30ms)
~/.claude/scripts/knowledge-query.sh "<topic>"

# Direct query (~17s cold start)
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-search.py "<query>"
```

**Storage**: `.knowledge-db/` per project | **Server**: Auto-starts on first use

## K-LEAN CLI

```bash
# Core Setup
kln install    # Install components to ~/.claude/
kln setup      # Configure API provider (interactive)
kln uninstall  # Remove components from ~/.claude/

# Service Management
kln start      # Start LiteLLM proxy and services
kln stop       # Stop all K-LEAN services
kln status     # Component status and health
kln debug      # Real-time monitoring dashboard

# Diagnostics
kln doctor -f  # Diagnose + auto-fix issues
kln models     # List available models with health
kln test       # Run full test suite (27 tests)
kln test-model # Test a specific model with quick prompt

# Development
kln multi      # Run multi-agent orchestrated review
kln sync       # Sync root directories for PyPI packaging
kln version    # Show version information
```

## SmolKLN CLI

```bash
smol-kln <agent> <task> [--model MODEL] [--telemetry]
smol-kln security-auditor "audit auth module"
smol-kln --list   # List available agents
```

**Output**: `.claude/kln/agentExecute/<timestamp>_<agent>_<task>.md`

**Agent Tools**: `read_file`, `search_files`, `grep`, `knowledge_search`, `get_complexity` (Python + C/C++)

## Available Models

**Dynamic discovery** from LiteLLM proxy. Models depend on your configuration.

```bash
kln models          # List all available models
kln models --first  # Show default model
```

Configure models in `~/.config/litellm/config.yaml`. Supports any provider (NanoGPT, OpenRouter, Ollama, etc.).

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
kln setup
```

Providers: NanoGPT, OpenRouter

## Serena Memories

Curated insights via `mcp__serena__*_memory` tools:
- `lessons-learned` - Gotchas, patterns
- `architecture-review-system` - System docs

## Hooks

- **UserPromptSubmit**: FindKnowledge, SaveInfo, async reviews
- **PostToolUse (Bash)**: Post-commit docs, timeline
- **PostToolUse (Web*)**: Auto-capture to knowledge DB
- **SessionStart**: Auto-start LiteLLM + Knowledge Server
