---
name: agent
description: "Execute SmolKLN agents for specialized analysis. Use /kln:agent <role> \"<task>\" [--model MODEL]"
allowed-tools: Bash, Read, Grep, Glob, Task
argument-hint: "[--role ROLE] [--model MODEL] [--parallel] <task>"
---

# /kln:agent - SmolKLN Agent Execution

Specialized AI agents with role-based expertise powered by smolagents. Each agent has
domain-specific prompts and access to tools for file reading, pattern search, and knowledge DB.

## When to Use

- Task requires domain expertise (security audit, architecture review)
- Role-based analysis is more effective than general review
- Need multiple specialists in parallel (--parallel mode)
- Want agents that can actually read and analyze files

**NOT for:**
- General code review → use `/kln:quick` or `/kln:multi`
- Quick feedback without role specialization → use `/kln:quick`
- Fresh debugging perspectives → use `/kln:rethink`

## Arguments

$ARGUMENTS

## Flags

- `--role, -r` - Agent role: code-reviewer, security-auditor, etc.
- `--model, -m` - Specific model (auto-selects best for role if omitted)
- `--parallel, -p` - Run 3 agents in parallel
- `--async, -a` - Run in background

## Available Roles

| Role | Focus | Agent File |
|------|-------|------------|
| `code-reviewer` | Code quality, bugs, best practices | code-reviewer.md |
| `security-auditor` | Security, compliance, OWASP | security-auditor.md |
| `orchestrator` | Task coordination, planning | orchestrator.md |
| `debugger` | Root cause analysis | debugger.md |
| `arm-cortex-expert` | Embedded ARM systems | arm-cortex-expert.md |
| `c-pro` | C99/C11/POSIX expertise | c-pro.md |
| `rust-expert` | Rust ownership, lifetimes | rust-expert.md |
| `performance-engineer` | Profiling, optimization | performance-engineer.md |

## Execution

Run via `smol-kln` command (installed with k-lean) which uses smolagents with LiteLLM:

```bash
# Preferred: Use the installed command
smol-kln <agent> "<task>" [--model MODEL] [--telemetry]

# Fallback: Script path (same functionality)
~/.claude/scripts/smol-kln.py <agent> "<task>" [--model MODEL]
```

**Note:** Requires smolagents: `pipx inject k-lean 'smolagents[litellm]' 'txtai[ann]'`

### Tools Available to Agents

- `read_file` - Read file contents
- `search_files` - Glob pattern search (recursive by default)
- `grep` - Pattern search in files
- `knowledge_search` - Query project's Knowledge DB

### MCP Integration (if available)

- Serena MCP for code symbol analysis
- Context7 for documentation lookup

## Parallel Mode (--parallel)

When `--parallel` is set, spawn 3 agents simultaneously:
- code-reviewer (quality focus)
- security-auditor (security focus)
- performance-engineer (performance focus)

Aggregate their findings into a unified report.

## Examples

```
/kln:agent code-reviewer "review auth module"
/kln:agent --role security-auditor "audit API endpoints"
/kln:agent --role orchestrator "plan refactoring of data layer"
/kln:agent --parallel "comprehensive review of latest changes"
/kln:agent -r debugger "investigate memory leak in parser"
```

## Agent Locations

- Installed: `~/.klean/agents/*.md`
- Source: `src/klean/data/agents/*.md`
