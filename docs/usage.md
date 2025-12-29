# Usage

## Review Commands

| Command | Description | Time |
|---------|-------------|------|
| `/kln:quick <focus>` | Single model review | ~30s |
| `/kln:multi <focus>` | 3-5 model consensus | ~60s |
| `/kln:deep <focus>` | Full codebase with tools | ~3min |
| `/kln:agent --role <role>` | SmolKLN specialist agent | ~30s |
| `/kln:rethink` | Contrarian debugging | ~20s |

**Examples:**
```bash
/kln:quick security
/kln:multi "check error handling"
/kln:deep "pre-release audit"
/kln:agent --role security-auditor "audit latest changes"
```

**Async (background):**
```bash
/kln:deep --async "full audit"    # Run in background
```

## Knowledge Commands

### Saving Knowledge

**Recommended:** Use `/kln:learn` for context-aware extraction:

| Command | Description |
|---------|-------------|
| `/kln:learn` | Extract learnings from recent conversation context |
| `/kln:learn "topic"` | Focused extraction on specific topic |
| `/kln:remember` | End-of-session comprehensive capture |

**Examples:**
```bash
/kln:learn                     # Auto-detect learnings from context
/kln:learn "auth bug fix"      # Extract insights about auth bug
/kln:remember                  # End-of-session, reviews git diff/log
```

### Searching Knowledge

| Keyword | Action |
|---------|--------|
| `FindKnowledge <query>` | Semantic search knowledge DB |
| `SaveInfo <url>` | Smart save URL with LLM evaluation |

**Examples:**
```bash
FindKnowledge "authentication patterns"
SaveInfo https://docs.example.com/api
```

## Session Management

| Command | Action |
|---------|--------|
| `/kln:learn` | Mid-session knowledge capture |
| `/kln:remember` | End-of-session capture |
| `/kln:doc` | Generate session docs |

**Mid-session workflow:**
```bash
# Work on feature, find bugs, research solutions...
/kln:learn "the fixes we made"   # Capture learnings
# Continue working...
```

**End-of-session workflow:**
```bash
/kln:remember    # Captures learnings to KB + syncs Serena → KB
/clear           # Clear context
```

The `/kln:remember` command:
1. Extracts learnings from git diff/log
2. Saves entries to Knowledge DB
3. Appends summary to Serena lessons-learned
4. Syncs Serena lessons to KB (makes them searchable by agents)

## SmolKLN Agents

8 specialist agents for domain-specific analysis.

**Agent Memory:** Agents persist session learnings to KB after execution. Future agents can search prior findings via `knowledge_search` tool.

**Tracing:** Enable telemetry for debugging agent behavior:
```bash
smol-kln security-auditor "audit" --telemetry
# View at http://localhost:6006
```

| Agent | Expertise |
|-------|-----------|
| `code-reviewer` | OWASP, SOLID, quality |
| `security-auditor` | Vulnerabilities, auth, crypto |
| `debugger` | Root cause analysis |
| `arm-cortex-expert` | Embedded ARM systems |
| `c-pro` | C99/C11/POSIX |
| `rust-expert` | Ownership, lifetimes |
| `performance-engineer` | Profiling, optimization |
| `orchestrator` | Coordinates other agents |

## Workflows

**Quick check:**
```bash
/kln:quick "check for issues"
```

**Pre-commit:**
```bash
/kln:multi "review changes"
```

**Pre-release:**
```bash
/kln:deep "comprehensive security and quality audit"
```

**Stuck debugging:**
```bash
/kln:rethink
```

**Found something useful:**
```bash
/kln:learn "the solution"
```

## Multi-Agent Reviews (k-lean multi)

Orchestrated reviews using multiple specialized agents:

```bash
# 3-agent (default) - manager + file_scout + analyzer
k-lean multi "Review src/klean/cli.py for bugs"

# 4-agent (thorough) - adds code_analyzer + security_auditor + synthesizer
k-lean multi --thorough "Security audit of auth module"

# With telemetry
k-lean multi "Review changes" --telemetry
```

**Output:** `.claude/kln/multiAgent/<timestamp>_multi-[3|4]-agent_<task>.md`

See [reference.md](reference.md#multi-agent-k-lean-multi) for agent configurations.

## Output Locations

| Type | Path |
|------|------|
| SmolKLN agents | `.claude/kln/agentExecute/` |
| Multi-agent reviews | `.claude/kln/multiAgent/` |
| Quick reviews | `.claude/kln/quickReview/` |
| Deep audits | `.claude/kln/asyncDeepAudit/` |
| Async logs | `/tmp/claude-reviews/` |
| Knowledge | `.knowledge-db/` |
| Timeline | `.knowledge-db/timeline.txt` |
| System logs | `~/.klean/logs/` |
| Phoenix traces | `http://localhost:6006` |
