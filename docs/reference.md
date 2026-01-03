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

### Development Tools (Hidden Admin Subgroup)

Access with `kln admin <command>`

| Command | Description |
|---------|-------------|
| `kln admin sync` | Sync files to package data for release |
| `kln admin debug` | Live dashboard (shows Phoenix status) |
| `kln admin test` | Run comprehensive test suite |

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

## Hook Keywords

| Keyword | Action |
|---------|--------|
| `FindKnowledge` | Semantic search KB |
| `SaveInfo` | LLM-evaluated URL save |
| `asyncReview` | Background quick review |
| `asyncConsensus` | Background consensus |

**Note:** For context-aware saves, use `/kln:learn` slash command.

## Configuration Files

| File | Purpose |
|------|---------|
| `~/.config/litellm/config.yaml` | Model definitions |
| `~/.config/litellm/.env` | API keys |
| `~/.claude/settings.json` | Claude Code settings |
| `.knowledge-db/entries.jsonl` | KB entries (per-project) |
| `.knowledge-db/index/` | Semantic index |
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

## Knowledge DB Schema (V2)

```json
{
  "title": "Short title",
  "summary": "2-3 sentence summary",
  "type": "lesson|finding|solution|pattern",
  "key_concepts": ["keyword1", "keyword2"],
  "quality": "high|medium|low",
  "source": "manual|web|agent_<name>|serena",
  "found_date": "2024-12-21T10:30:00"
}
```

**Source types:**
- `manual` - /kln:learn command
- `web` - Auto-captured from web research
- `agent_<name>` - SmolKLN agent session persistence (e.g., `agent_security-auditor`)
- `serena` - Synced from Serena lessons-learned

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
