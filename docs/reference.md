# Reference

## CLI Commands

### Core Commands (Root Level)

| Command | Description |
|---------|-------------|
| `kln init` | Initialize K-LEAN with provider selection |
| `kln install` | Install components to ~/.claude/ |
| `kln uninstall` | Remove components |
| `kln start` | Start LiteLLM proxy |
| `kln start -s all` | Start LiteLLM + KB server |
| `kln start --telemetry` | Start Phoenix telemetry server |
| `kln stop` | Stop services |
| `kln status` | Show component status |
| `kln doctor` | Validate configuration |
| `kln doctor -f` | Auto-fix common issues |
| `kln multi` | Run multi-agent orchestrated review |

### Model Management Subgroup

Access with `kln model <command>`

| Command | Description |
|---------|-------------|
| `kln model list` | List available models |
| `kln model list --health` | Check model health |
| `kln model add` | Add individual model |
| `kln model remove` | Remove model from config |
| `kln model test` | Test a specific model |

### Provider Management Subgroup

Access with `kln provider <command>`

| Command | Description |
|---------|-------------|
| `kln provider list` | Show configured providers |
| `kln provider add <name>` | Add provider with recommended models |
| `kln provider set-key <name>` | Update provider's API key |
| `kln provider remove <name>` | Remove provider configuration |

### Development Tools (Hidden Admin Subgroup)

Access with `kln admin <command>`

| Command | Description |
|---------|-------------|
| `kln admin sync` | Sync files to package data for release |
| `kln admin debug` | Live dashboard (shows Phoenix status) |
| `kln admin test` | Run comprehensive test suite |
| `kln admin persist-session` | Generate session log via Claude Haiku |

## Models

Models are **auto-discovered** from LiteLLM proxy. No hardcoded model names.

```bash
kln model list           # List available models
kln model list --health  # Check model health
```

**Model types:**
- **Standard** — Regular chat completions
- **Thinking** — Return `reasoning_content` with reasoning chains (DeepSeek, GLM, Kimi)

User controls model priority via order in `~/.config/litellm/config.yaml`.

## Slash Commands

| Command | Flags |
|---------|-------|
| `/kln:quick` | `--model`, `--output json\|text` |
| `/kln:multi` | `--models N`, `--output` |
| `/kln:agent` | `--role` |
| `/kln:rethink` | - |
| `/kln:doc` | `--type report\|session\|lessons` |
| `/kln:remember` | Syncs Serena → KB |
| `/kln:status` | - |
| `/kln:help` | - |

## Knowledge Commands

| Command | Action |
|---------|--------|
| `/kln:find <query>` | Semantic search KB |
| `/kln:find <query> since:YYYY-MM-DD` | Search with date filter |
| `/kln:find <query> branch:<name>` | Search filtered by git branch |
| `/kln:find <query> type:<type>` | Search filtered by entry type |
| `/kln:learn` | Extract learnings from current context |
| `/kln:remember` | End-of-session capture + Serena index |

**Filter syntax:** Combine filters inline: `/kln:find auth since:2026-02-01 branch:feature/auth type:decision`

**Note:** Learnings are also auto-extracted on `/compact` via PreCompact hook.

## Configuration Files

| File | Purpose |
|------|---------|
| `~/.config/litellm/config.yaml` | Model definitions |
| `~/.config/litellm/.env` | API keys |
| `~/.claude/settings.json` | Claude Code settings |
| `.knowledge-db/entries.jsonl` | KB entries (per-project) |
| `.knowledge-db/index/` | Semantic index |
| `.serena/memories/session-log-*.md` | Session logs (per-project, Serena-discoverable) |
| `~/.klean/logs/phoenix.log` | Phoenix telemetry logs |
| `.claude/kln/agentExecute/` | SmolKLN agent reports |
| `.claude/kln/quickReview/` | Quick review outputs |

## SmolKLN CLI

Run SmolKLN agents from command line:

```bash
kln-smol <agent> <task> [--model MODEL] [--telemetry]
kln-smol --list
```

**Examples:**
```bash
kln-smol security-auditor "audit authentication module"
kln-smol code-reviewer "review main.py" --model qwen3-coder
kln-smol --list  # List available agents
```

**Output:** Results saved to `.claude/kln/agentExecute/<timestamp>_<agent>_<task>.md`

## Multi-Agent (kln multi)

Orchestrated multi-agent reviews using smolagents `managed_agents`:

```bash
# 3-agent (default) - fast
kln multi "Review src/klean/cli.py for bugs"

# 4-agent (thorough) - comprehensive
kln multi --thorough "Security audit of auth module"

# With telemetry
kln multi "Review changes" --telemetry
```

### Agent Configurations

| Variant | Agents | Time | Use Case |
|---------|--------|------|----------|
| 3-agent (default) | manager + file_scout + analyzer | 30-90s | Quick reviews |
| 4-agent (--thorough) | manager + file_scout + code_analyzer + security_auditor + synthesizer | 60-180s | Deep audits |

### Configuration

All agents use **dynamic model discovery** - first available model from LiteLLM.
User controls priority via model order in `~/.config/litellm/config.yaml`.

| Setting | Value |
|---------|-------|
| Manager max_steps | 7 |
| Specialist max_steps | 6 |
| planning_interval | 3 (all agents) |

**Output:** `.claude/kln/multiAgent/<timestamp>_multi-[3|4]-agent_<task>.md`

## Telemetry

SmolKLN agents can be traced with Phoenix for debugging and performance analysis.

**Install:** `pipx inject kln-ai 'kln-ai[telemetry]'`

| Flag | Command | Effect |
|------|---------|--------|
| `--telemetry` | `kln start` | Start Phoenix on :6006 |
| `-t` / `--telemetry` | `kln-smol` | Enable agent tracing |

**Traced:** LLM calls (prompt, response, tokens), tool invocations, agent reasoning steps.

**UI:** `http://localhost:6006`

## Knowledge DB Schema (V3.1)

```json
{
  "id": "finding-20260207103000",
  "title": "Short descriptive title (max 80 chars)",
  "insight": "2-4 sentence explanation with actionable details",
  "type": "warning|solution|pattern|decision|discovery|finding|commit",
  "priority": "critical|high|medium|low",
  "keywords": ["searchable", "terms"],
  "source": "file:path:line|https://url|git:hash|conv:YYYY-MM-DD",
  "date": "2026-02-07",
  "timestamp": "2026-02-07T10:30:00",
  "branch": "feature/auth",
  "related_to": ["entry-id-1", "entry-id-2"]
}
```

**Entry types:**

| Type | When to Use |
|------|-------------|
| `warning` | Problems, gotchas, things to avoid |
| `solution` | Working fixes, workarounds |
| `pattern` | Reusable approaches, best practices |
| `decision` | Architectural choices, "chose X over Y" |
| `discovery` | "Found that...", "Turns out...", TIL moments |
| `commit` | Git commit captures (auto-captured) |
| `finding` | Default - undocumented behavior, API quirks |

**V3.1 fields** (added to V3 core):
- `timestamp` - ISO 8601 for intra-day ordering (auto-set)
- `branch` - Git branch at capture time (auto-detected)
- `related_to` - Bidirectional links between entries

**Source types:**
- `file:path:line` - Source code reference
- `https://url` - Documentation or web reference
- `git:<hash>` - Git commit
- `conv:YYYY-MM-DD` - Conversation context
- `bash:<command>` - Auto-captured from bash events
- `session:YYYY-MM-DD` - Session journal entry
- `session-log:YYYY-MM-DD` - Session log summary (links to .serena/memories/)

## Review Areas

All reviews check these 7 areas:

1. **CORRECTNESS** - Logic errors, edge cases
2. **MEMORY SAFETY** - Buffer overflows, leaks
3. **ERROR HANDLING** - Validation, propagation
4. **CONCURRENCY** - Race conditions, thread safety
5. **ARCHITECTURE** - Coupling, cohesion
6. **SECURITY** - Vulnerabilities, auth
7. **STANDARDS** - Code style, guidelines

## Audit Mode Permissions

Deep reviews run read-only:

**Allowed:** Read, Glob, Grep, WebSearch, git read ops, MCP search tools

**Denied:** Write, Edit, rm, mv, git commit/push, install commands
