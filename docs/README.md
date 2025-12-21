# K-LEAN Documentation

**K-LEAN** = Knowledge-Leveraged Engineering Analysis Network

Multi-model code review and knowledge capture for Claude Code.

---

## Quick Links
- [Quick Start](QUICK_START.md) - Get started in 5 minutes
- [Installation](INSTALLATION.md) - Full installation guide

---

## What It Does

- **6 LLM models** review your code (unified prompts, all areas)
- **Quick reviews** (30s) or **Deep audits** (5min with tools)
- **Factory Droid** fast agentic reviews with 8 specialist droids
- **Knowledge capture** from web research and lessons learned
- **Background execution** - review while you keep coding

---

## Guides

| Guide | Description |
|-------|-------------|
| [Knowledge Database](guides/knowledge-db.md) | Semantic search for your knowledge |
| [Droids](guides/droids.md) | Factory droid integration |
| [Hooks](guides/hooks.md) | Claude Code automation |

---

## Reference

| Document | Description |
|----------|-------------|
| [Commands](reference/commands.md) | All `/kln:*` commands |
| [Architecture](reference/architecture.md) | System design |
| [CLI](reference/cli.md) | `k-lean` command reference |

---

## Developer

| Document | Description |
|----------|-------------|
| [Development](dev/development.md) | Contributing guide |
| [Lessons Learned](dev/lessons-learned.md) | Design decisions |

---

## Commands Quick Reference

| Command | What It Does | Time |
|---------|--------------|------|
| `/kln:quick <model> <focus>` | Fast single-model review | ~30s |
| `/kln:multi [models] <focus>` | 3-model comparison | ~60s |
| `/kln:deep <model> <focus>` | Thorough review with tools | ~3min |
| `/kln:droid <model> <focus>` | Fast agentic review | ~30s |
| `/kln:help` | Show all commands | - |

## Models

| Alias | Model | Notes |
|-------|-------|-------|
| `qwen` | qwen3-coder | Default single-model |
| `deepseek` | deepseek-v3-thinking | Architecture |
| `kimi` | kimi-k2-thinking | Planning |
| `glm` | glm-4.6-thinking | Standards |
| `minimax` | minimax-m2 | Research |
| `hermes` | hermes-4-70b | Scripting |

## Keywords

| Keyword | What It Does |
|---------|--------------|
| `healthcheck` | Test all 6 models |
| `InitKB` | Initialize knowledge DB |
| `SaveThis <lesson>` | Save lesson learned |
| `FindKnowledge <query>` | Search knowledge DB |

---

## File Locations

| Type | Path |
|------|------|
| Scripts | `~/.klean/scripts/` |
| Commands | `~/.klean/commands/kln/` |
| Settings | `~/.klean/settings.json` |
| LiteLLM | `~/.config/litellm/config.yaml` |
| Droids | `~/.factory/droids/` |
| Output | `.claude/kln/` (per project) |
| Knowledge | `.knowledge-db/` (per project) |
