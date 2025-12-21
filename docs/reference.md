# Reference

## CLI Commands

| Command | Description |
|---------|-------------|
| `k-lean install` | Install components to ~/.claude/ |
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
| `k-lean sync` | Sync droids to ~/.factory/ |

## Models

| Model | Type | Best For |
|-------|------|----------|
| `qwen3-coder` | Standard | General coding |
| `deepseek-v3-thinking` | Thinking | Architecture |
| `glm-4.6-thinking` | Thinking | Standards |
| `kimi-k2-thinking` | Thinking | Planning |
| `minimax-m2` | Thinking | Research |
| `hermes-4-70b` | Standard | Scripting |

**Thinking models** return `reasoning_content` instead of `content`.

## Slash Commands

| Command | Flags |
|---------|-------|
| `/kln:quick` | `--model`, `--output json\|text` |
| `/kln:multi` | `--models N`, `--output` |
| `/kln:deep` | `--async`, `--output` |
| `/kln:droid` | `--role` |
| `/kln:rethink` | - |
| `/kln:doc` | `--type report\|session\|lessons` |
| `/kln:remember` | - |
| `/kln:status` | - |
| `/kln:help` | - |

## Hook Keywords

| Keyword | Action |
|---------|--------|
| `SaveThis` | Direct save to KB |
| `SaveInfo` | LLM-evaluated save |
| `FindKnowledge` | Semantic search |
| `asyncReview` | Background quick review |
| `asyncDeepReview` | Background deep review |
| `asyncConsensus` | Background consensus |

## Configuration Files

| File | Purpose |
|------|---------|
| `~/.config/litellm/config.yaml` | Model definitions |
| `~/.config/litellm/.env` | API keys |
| `~/.claude/settings.json` | Claude Code settings |
| `.knowledge-db/entries.jsonl` | KB entries (per-project) |
| `.knowledge-db/index/` | Semantic index |

## Knowledge DB Schema (V2)

```json
{
  "title": "Short title",
  "summary": "2-3 sentence summary",
  "type": "gotcha|pattern|solution|lesson",
  "key_concepts": ["keyword1", "keyword2"],
  "quality": "high|medium|low",
  "source": "manual|conversation|web|file",
  "found_date": "2024-12-21T10:30:00"
}
```

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
