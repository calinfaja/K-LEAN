# K-LEAN Companion v2.0

**K-LEAN** = Knowledge-Leveraged Engineering Analysis Network

Multi-model code review and knowledge capture for Claude Code.

---

## What It Does

- **6 LLM models** review your code (unified prompts, all areas)
- **Quick reviews** (30s) or **Deep audits** (5min with tools)
- **Knowledge capture** from web research and lessons learned
- **Background execution** - review while you keep coding

---

## Quick Start

```bash
# Start LiteLLM proxy
start-nano-proxy

# Check models
healthcheck

# Quick review
/kln:quickReview qwen security audit

# 3-model comparison
/kln:quickCompare check error handling

# Deep audit with tools
/kln:deepAudit pre-release review

# Get help
/kln:help
```

---

## Models

| Alias | Model | Notes |
|-------|-------|-------|
| `qwen` | qwen3-coder | Default single-model |
| `deepseek` | deepseek-v3-thinking | Architecture |
| `kimi` | kimi-k2-thinking | Planning |
| `glm` | glm-4.6-thinking | Standards |
| `minimax` | minimax-m2 | Research |
| `hermes` | hermes-4-70b | Scripting |

---

## Commands

| Command | What It Does |
|---------|--------------|
| `/kln:quickReview <model> <focus>` | Fast single-model review |
| `/kln:quickCompare [models] <focus>` | 3-model comparison |
| `/kln:deepInspect <model> <focus>` | Thorough review with tools |
| `/kln:deepAudit [models] <focus>` | Full 3-model audit with tools |
| `/kln:quickConsult <model> <question>` | Get second opinion |
| `/kln:createReport <title>` | Document session |

## Keywords

| Keyword | What It Does |
|---------|--------------|
| `healthcheck` | Test all 6 models |
| `GoodJob <url>` | Capture knowledge from URL |
| `SaveThis <lesson>` | Save lesson learned |
| `FindKnowledge <query>` | Search knowledge DB |

---

## Documentation

| Document | Contents |
|----------|----------|
| **[USER_GUIDE.md](USER_GUIDE.md)** | Commands, keywords, workflows, examples |
| **[INSTALLATION.md](INSTALLATION.md)** | Setup, prerequisites, configuration |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | Hooks, scripts, knowledge system internals |

---

## File Locations

| Type | Path |
|------|------|
| Scripts | `~/.claude/scripts/` |
| Commands | `~/.claude/commands/kln/` |
| Settings | `~/.claude/settings.json` |
| LiteLLM | `~/.config/litellm/nanogpt.yaml` |
| Output | `/tmp/claude-reviews/` |
| Knowledge | `.knowledge-db/` (per project) |
