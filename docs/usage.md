# Usage

Complete guide to K-LEAN commands, agents, and workflows.

---

## Contents

- [Slash Commands](#slash-commands)
- [SmolKLN Agents](#smolkln-agents)
- [Knowledge System](#knowledge-system)
- [Workflows](#workflows)
- [CLI Commands](#cli-commands)
- [Output Locations](#output-locations)

---

## Slash Commands

All commands are used inside Claude Code.

### Review Commands

| Command | Description | Time |
|---------|-------------|------|
| `/kln:quick <focus>` | Single model review | ~30s |
| `/kln:multi <focus>` | 3-5 model consensus | ~60s |
| `/kln:agent <role> <task>` | Specialist agent | ~2min |
| `/kln:rethink` | Contrarian debugging | ~20s |

**Examples:**
```bash
/kln:quick security
/kln:multi "check error handling"
/kln:agent security-auditor "audit authentication"
```

### Knowledge Commands

| Command | Description |
|---------|-------------|
| `/kln:learn` | Extract learnings from conversation context |
| `/kln:learn "topic"` | Focused extraction on specific topic |
| `/kln:remember` | End-of-session comprehensive capture |

**Examples:**
```bash
/kln:learn                     # Auto-detect learnings from context
/kln:learn "auth bug fix"      # Extract insights about auth bug
/kln:remember                  # End-of-session, syncs to KB
```

### Utility Commands

| Command | Description |
|---------|-------------|
| `/kln:status` | System health check (services, models, KB) |
| `/kln:doc <title>` | Generate session documentation |
| `/kln:help` | Show command reference |

### Flags

Most commands support these flags:

| Flag | Description |
|------|-------------|
| `--async` | Run in background |
| `--models N` | Number of models (for `/kln:multi`) |
| `--output json\|text` | Output format |

---

## SmolKLN Agents

8 specialist agents with domain expertise, powered by smolagents.

### Available Agents

| Agent | Expertise |
|-------|-----------|
| `code-reviewer` | OWASP, SOLID, code quality |
| `security-auditor` | Vulnerabilities, auth, crypto |
| `debugger` | Root cause analysis |
| `performance-engineer` | Profiling, optimization |
| `rust-expert` | Ownership, lifetimes, unsafe |
| `c-pro` | C99/C11, POSIX, memory |
| `arm-cortex-expert` | Embedded ARM, real-time |
| `orchestrator` | Multi-agent coordination |

### Usage

```bash
# In Claude Code
/kln:agent security-auditor "audit the payment module"
/kln:agent debugger "investigate the memory leak"
/kln:agent rust-expert "review unsafe blocks"

# Direct CLI
kln-smol security-auditor "audit auth" --model qwen3-coder
kln-smol --list  # List available agents
```

### Agent Features

- **Tools**: Agents can read files, search code, query Knowledge DB
- **Memory**: Session learnings persist to KB after execution
- **Telemetry**: Enable tracing with `--telemetry` flag

```bash
kln-smol security-auditor "audit" --telemetry
# View traces at http://localhost:6006
```

### Multi-Agent Reviews

Orchestrated reviews using multiple agents:

```bash
# 3-agent (default) - manager + file_scout + analyzer
kln multi "Review src/klean/cli.py for bugs"

# 4-agent (thorough) - adds security_auditor + synthesizer
kln multi --thorough "Security audit of auth module"
```

---

## Knowledge System

Persistent semantic memory across sessions with hybrid search and temporal filtering.

### Saving Knowledge

| Method | When to Use |
|--------|-------------|
| `/kln:learn` | Mid-session, capture insights from context |
| `/kln:learn "topic"` | Focused capture on specific topic |
| `/kln:remember` | End-of-session, comprehensive capture |

**Entry types** (auto-inferred from content):

| Type | Signal Words |
|------|-------------|
| `warning` | "don't", "avoid", "careful", "gotcha" |
| `solution` | "fixed", "solved", "workaround" |
| `pattern` | "use X for Y", "prefer", "best way" |
| `decision` | "chose", "decided", "instead of", "trade-off" |
| `discovery` | "found that", "turns out", "TIL", "surprisingly" |
| `finding` | Default for everything else |

### Searching Knowledge

Use `/kln:find` slash command for knowledge search:

| Command | Action |
|---------|--------|
| `/kln:find <query>` | Semantic search KB |
| `/kln:find <query> since:YYYY-MM-DD` | Search with date filter |
| `/kln:find <query> branch:<name>` | Search filtered by git branch |
| `/kln:find <query> type:<type>` | Search filtered by entry type |

Results are numbered with insight excerpts:
```
  1. [solution] Auth refactor (2026-02-07) [id:abc12345]
     Moved JWT validation to middleware, reduced duplicated checks...
  2. [pattern] JWT token handling (2026-02-06) [id:def67890]
     Use short-lived access tokens with refresh rotation...
```

Use `--id` for full entry details. Type `InitKB` to initialize the Knowledge DB.

**Examples:**
```bash
/kln:find "authentication patterns"
/kln:find auth since:2026-02-01
/kln:find auth branch:feature/auth type:decision
```

### Auto-Captured Events

Hooks automatically capture events to the Knowledge DB:

| Event | Type | Priority |
|-------|------|----------|
| Git commits | `commit` | low |
| Test failures | `finding` | high |
| Build errors | `finding` | high |
| Package installs | `finding` | low |
| Doc URL fetches | `discovery` | low |
| Session learnings (PreCompact) | various | medium |

All auto-captured entries include timestamp and git branch metadata.

### Session Log (Automatic)

When Claude Code compacts context (PreCompact hook), K-LEAN automatically generates a session summary:

1. Reads the conversation transcript (user messages)
2. Gets git log since 6am
3. Queries KB for today's entries (findings, warnings, solutions)
4. Sends all three to Claude Haiku for summarization
5. Appends to `.serena/memories/kln-session-YYYY-MM-DD.md`
6. Creates a searchable KB entry (type: `session`) linking to the full log

Session logs are Serena-discoverable and injected as context on next session start:
```
[SESSION] 14:00 - 16:30 | main
- Implemented PreCompact session log system
- Commits: feat(hooks): add session persistence
- Status: completed
```

**Manual trigger:** `kln admin persist-session [--transcript PATH]`

### End-of-Session Workflow

```bash
/kln:remember    # Captures learnings + syncs Serena lessons
/clear           # Clear context
```

The `/kln:remember` command:
1. Extracts learnings from git diff/log
2. Saves entries to Knowledge DB (V3.1 schema with timestamp + branch)
3. Syncs Serena lessons to KB (searchable by agents)

Session logs are generated automatically on context compaction -- no manual action needed.

---

## Workflows

### Quick Check
```bash
/kln:quick "check for issues"
```

### Pre-Commit
```bash
/kln:multi "review changes"
```

### Pre-Release
```bash
/kln:agent security-auditor "comprehensive security audit"
```

### Stuck Debugging
```bash
/kln:rethink
```

### Found Something Useful
```bash
/kln:learn "the solution we found"
```

### End of Session
```bash
/kln:remember
```

---

## CLI Commands

Commands run in terminal (not Claude Code).

### Core Commands

```bash
kln init               # Initialize: install + configure provider
kln install            # Install components to ~/.claude/
kln uninstall          # Remove components
```

### Service Management

```bash
kln start              # Start LiteLLM proxy
kln start -s all       # Start LiteLLM + Knowledge server
kln stop               # Stop all services
```

### Diagnostics

```bash
kln status             # Component status
kln doctor             # Validate configuration
kln doctor -f          # Auto-fix issues
```

### Model Management

```bash
kln model list         # List available models
kln model list --health  # Check model health
kln model add          # Add individual model
kln model remove       # Remove model
kln model test         # Test a specific model
```

### Provider Management

```bash
kln provider list      # Show configured providers
kln provider add       # Add provider with recommended models
kln provider set-key   # Update API key
kln provider remove    # Remove provider
```

### Development (Hidden Admin Subgroup)

```bash
kln admin test             # Run test suite
kln admin sync             # Sync package data
kln admin debug            # Live monitoring dashboard
kln admin persist-session  # Generate session log via Claude Haiku
```

---

## Output Locations

| Type | Path |
|------|------|
| SmolKLN agents | `.claude/kln/agentExecute/` |
| Multi-agent reviews | `.claude/kln/multiAgent/` |
| Quick reviews | `.claude/kln/quickReview/` |
| Knowledge DB | `.knowledge-db/` |
| Timeline | `.knowledge-db/timeline.txt` |
| Session logs | `.serena/memories/kln-session-YYYY-MM-DD.md` |
| System logs | `~/.klean/logs/` |
| Phoenix traces | `http://localhost:6006` |

---

See [reference.md](reference.md) for complete configuration options.
