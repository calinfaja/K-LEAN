# K-LEAN Companion v3.0

**K-LEAN** = Knowledge-Leveraged Engineering Analysis Network

Multi-model code review and knowledge capture for Claude Code.

---

## What It Does

- **6 LLM models** review your code (unified prompts, all areas)
- **Quick reviews** (30s) or **Deep audits** (5min with tools)
- **Factory Droid** fast agentic reviews with 8 specialist droids
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

| Command | What It Does | Time |
|---------|--------------|------|
| `/kln:quickReview <model> <focus>` | Fast single-model review | ~30s |
| `/kln:quickCompare [models] <focus>` | 3-model comparison | ~60s |
| `/kln:deepInspect <model> <focus>` | Thorough review with tools | ~3min |
| `/kln:deepAudit [models] <focus>` | Full 3-model audit with tools | ~5min |
| `/kln:droid <model> <focus>` | Fast agentic review | ~30s |
| `/kln:droidAudit [models] <focus>` | 3-droid parallel review | ~1min |
| `/kln:droidExecute <model> <droid> <prompt>` | Specialized droid | ~30s |
| `/kln:quickConsult <model> <question>` | Get second opinion | ~60s |
| `/kln:createReport <title>` | Document session | - |

## Specialist Droids

| Droid | Expertise |
|-------|-----------|
| `orchestrator` | System architecture, task coordination |
| `code-reviewer` | Code quality, OWASP, SOLID principles |
| `security-auditor` | Vulnerabilities, auth, encryption |
| `debugger` | Root cause analysis, error tracing |
| `arm-cortex-expert` | ARM Cortex-M, DMA, ISRs, FreeRTOS |
| `c-pro` | C99/C11, POSIX, memory management |
| `rust-expert` | Ownership, lifetimes, embedded Rust |
| `performance-engineer` | Profiling, optimization |

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
| **[DROID-SYSTEM.md](DROID-SYSTEM.md)** | Factory Droid integration, specialists |

---

## File Locations

| Type | Path |
|------|------|
| Scripts | `~/.claude/scripts/` |
| Commands | `~/.claude/commands/kln/` |
| Settings | `~/.claude/settings.json` |
| LiteLLM | `~/.config/litellm/config.yaml` |
| Droids | `~/.factory/droids/` |
| Output | `.claude/kln/` (per project) |
| Knowledge | `.knowledge-db/` (per project) |
