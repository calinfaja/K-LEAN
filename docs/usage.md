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

Persistent semantic memory across sessions.

### Saving Knowledge

| Method | When to Use |
|--------|-------------|
| `/kln:learn` | Mid-session, capture insights from context |
| `/kln:learn "topic"` | Focused capture on specific topic |
| `/kln:remember` | End-of-session, comprehensive capture |

### Searching Knowledge

Type these keywords directly in Claude Code (no `/` prefix):

| Keyword | Action |
|---------|--------|
| `FindKnowledge <query>` | Semantic search Knowledge DB |
| `SaveInfo <url>` | Evaluate URL with LLM, save if relevant |
| `InitKB` | Initialize Knowledge DB for current project |

**Examples:**
```bash
FindKnowledge "authentication patterns"
SaveInfo https://docs.example.com/api
```

### End-of-Session Workflow

```bash
/kln:remember    # Captures learnings + syncs Serena lessons
/clear           # Clear context
```

The `/kln:remember` command:
1. Extracts learnings from git diff/log
2. Saves entries to Knowledge DB
3. Syncs Serena lessons to KB (searchable by agents)

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
kln admin test         # Run test suite
kln admin sync         # Sync package data
kln admin debug        # Live monitoring dashboard
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
| System logs | `~/.klean/logs/` |
| Phoenix traces | `http://localhost:6006` |

---

See [reference.md](reference.md) for complete configuration options.
