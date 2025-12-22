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

| Keyword | Action |
|---------|--------|
| `SaveThis <text>` | Save a lesson learned |
| `SaveInfo <text>` | Smart save with LLM evaluation |
| `FindKnowledge <query>` | Semantic search |

**Examples:**
```bash
SaveThis "always validate user input before SQL queries"
FindKnowledge "authentication patterns"
```

## SmolKLN Agents

8 specialist agents for domain-specific analysis:

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

## Output Locations

| Type | Path |
|------|------|
| Async logs | `/tmp/claude-reviews/` |
| Knowledge | `.knowledge-db/` |
| Timeline | `.knowledge-db/timeline.txt` |
| System logs | `~/.klean/logs/` |
