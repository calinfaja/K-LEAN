# K-LEAN Agents (formerly Factory Droids)

## ⚠️ DEPRECATED: Factory Droids Removed

Factory Droids have been **completely removed** from K-LEAN in favor of **SmolKLN**, a more powerful and reliable agent system.

## Why SmolKLN Replaced Factory Droids

| Issue with Factory Droids | SmolKLN Solution |
|---------------------------|------------------|
| Relied on external `droid` binary | Uses native smolagents library |
| Binary was unreliable (hung) | Pure Python, no external deps |
| Required separate Factory CLI | Integrated into K-LEAN CLI |
| Limited to single-model calls | True agentic with tools |
| Could not read actual files | Has read_file, grep, search_files |
| No knowledge integration | Built-in Knowledge DB tool |
| No MCP support | Native MCP server support |

## Current Agent System: SmolKLN

SmolKLN uses the same **agent prompts** but with a production-grade execution engine:

### Available Agents

| Agent | Specialization |
|-------|---------------|
| `orchestrator` | Master coordinator |
| `code-reviewer` | OWASP, SOLID, quality |
| `security-auditor` | Vulnerabilities, auth |
| `debugger` | Root cause analysis |
| `arm-cortex-expert` | Embedded ARM systems |
| `c-pro` | C99/C11/POSIX |
| `rust-expert` | Ownership, lifetimes |
| `performance-engineer` | Profiling, optimization |

### Usage

```bash
# Via slash command
/kln:agent code-reviewer

# Via CLI
k-lean agent code-reviewer "review auth module"

# Via Python
from klean.smol import SmolKLNExecutor
executor = SmolKLNExecutor()
result = executor.execute("code-reviewer", "review auth module")
```

### Agent Locations

- Prompts: `~/.klean/agents/*.md`
- Source: `src/klean/data/agents/*.md`

### Key Differences

| Feature | Factory Droids | SmolKLN |
|---------|---------------|---------|
| File reading | ❌ None | ✅ read_file tool |
| Pattern search | ❌ None | ✅ grep, search_files |
| Knowledge DB | ❌ Separate | ✅ Integrated tool |
| MCP servers | ❌ None | ✅ Serena, Context7 |
| Execution | External binary | Native Python |
| Reliability | Poor (hung) | Stable |

## Migration

No migration needed - SmolKLN uses the same prompt format. Just use `/kln:agent` instead of `/kln:droid`.

---
*See [smolkln-implementation.md](smolkln-implementation.md) for full details*
