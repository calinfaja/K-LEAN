# Reference

## CLI Commands

| Command | Description |
|---------|-------------|
| `k-lean install` | Install components to ~/.claude/ |
| `k-lean setup` | Configure API provider (interactive) |
| `k-lean uninstall` | Remove components |
| `k-lean status` | Show component status |
| `k-lean doctor` | Validate configuration |
| `k-lean doctor -f` | Auto-fix common issues |
| `k-lean start` | Start LiteLLM proxy |
| `k-lean start -s all` | Start LiteLLM + KB server |
| `k-lean stop` | Stop services |
| `k-lean models` | List available models |
| `k-lean models --health` | Check model health |
| `k-lean test` | Run test suite |
| `k-lean sync` | Sync files to package data for release |
| `k-lean start --telemetry` | Start Phoenix telemetry server |
| `k-lean debug` | Live dashboard (shows Phoenix status) |

## Models

| Model | Type | Best For |
|-------|------|----------|
| `qwen3-coder` | Standard | General coding |
| `deepseek-v3-thinking` | Thinking | Architecture |
| `glm-4.6-thinking` | Thinking | Standards |
| `kimi-k2-thinking` | Thinking | Planning |
| `minimax-m2` | Thinking | Research |
| `hermes-4-70b` | Standard | Scripting |

*Models are auto-discovered from LiteLLM. Use `k-lean models` for current list.*

**Thinking models** return `reasoning_content` instead of `content`.

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
smol-kln <agent> <task> [--model MODEL] [--telemetry]
smol-kln --list
```

**Examples:**
```bash
smol-kln security-auditor "audit authentication module"
smol-kln code-reviewer "review main.py" --model qwen3-coder
smol-kln --list  # List available agents
```

**Output:** Results saved to `.claude/kln/agentExecute/<timestamp>_<agent>_<task>.md`

## Multi-Agent (k-lean multi)

Orchestrated multi-agent reviews using smolagents `managed_agents`:

```bash
# 3-agent (default) - fast
k-lean multi "Review src/klean/cli.py for bugs"

# 4-agent (thorough) - comprehensive
k-lean multi --thorough "Security audit of auth module"

# With telemetry
k-lean multi "Review changes" --telemetry
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

See [multi-agent-implementation-plan.md](multi-agent-implementation-plan.md) for architecture details.

## Telemetry

SmolKLN agents can be traced with Phoenix for debugging and performance analysis.

**Install:** `pipx inject k-lean 'k-lean[telemetry]'`

| Flag | Command | Effect |
|------|---------|--------|
| `--telemetry` | `k-lean start` | Start Phoenix on :6006 |
| `-t` / `--telemetry` | `smol-kln` | Enable agent tracing |

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
