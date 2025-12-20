# K-LEAN Quick Start

**K-LEAN** = Knowledge-Leveraged Engineering Analysis Network

Get multi-model code reviews running in 5 minutes.

---

## Prerequisites

- **Claude Code CLI** (latest version)
- **Python 3.9+**
- **NanoGPT API key** from [nano-gpt.com](https://nano-gpt.com) ($0.50/1M tokens)

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/AICodingDojo/claudeAgentic.git
cd claudeAgentic

# 2. Install K-LEAN CLI
pipx install -e review-system-backup

# 3. Set your API key
export NANOGPT_API_KEY="your-key-here"

# 4. Start services
k-lean start

# 5. Verify everything works
k-lean test
```

---

## Your First Review

```bash
# Check models are working
healthcheck

# Quick security review (~30s)
/kln:quick security

# Multi-model consensus (~60s)
/kln:multi architecture review

# Deep analysis with tools (~3min)
/kln:deep security audit

# Get help
/kln:help
```

---

## Commands Overview

| Command | What It Does | Time |
|---------|--------------|------|
| `/kln:quick` | Fast single-model review | ~30s |
| `/kln:multi` | Consensus from 3-5 models | ~60s |
| `/kln:deep` | Full codebase analysis with tools | ~3min |
| `/kln:droid` | Specialist agent (security, perf, etc.) | ~2min |
| `/kln:rethink` | Fresh debugging perspectives | ~30s |
| `/kln:status` | System health check | instant |
| `/kln:help` | Command reference | instant |

### Command Flags

- `--async` - Run in background
- `--models N` - Number of models (3-5)
- `--output json|text` - Output format
- `--role <droid>` - Specialist for /kln:droid

---

## Models

| Model | Strength | Best For |
|-------|----------|----------|
| `qwen3-coder` | Code quality | Bug detection, refactoring |
| `deepseek-v3-thinking` | Architecture | Design, structure |
| `glm-4.6-thinking` | Standards | Compliance, style |
| `minimax-m2` | Context | Large codebases |
| `kimi-k2-thinking` | Planning | Agents, workflows |
| `hermes-4-70b` | Scripting | Automation, tooling |

Check available models: `k-lean models`

---

## Knowledge Database

Save and search knowledge across sessions:

```bash
# Save a lesson learned
SaveThis "Connection pooling in Python requires explicit close() calls"

# Search your knowledge
FindKnowledge connection pooling

# Knowledge is stored per-project in .knowledge-db/
```

---

## Specialist Droids

8 domain experts available via `/kln:droid`:

| Droid | Expertise |
|-------|-----------|
| `code-reviewer` | Code quality, SOLID, OWASP |
| `security-auditor` | Vulnerabilities, auth, crypto |
| `performance-engineer` | Profiling, optimization |
| `debugger` | Root cause analysis |
| `rust-expert` | Rust patterns, ownership |
| `c-pro` | C/embedded, memory |
| `arm-cortex-expert` | ARM, FreeRTOS, ISRs |
| `orchestrator` | Multi-droid coordination |

```bash
/kln:droid --role security audit authentication flow
/kln:droid --role performance check memory usage
```

---

## K-LEAN CLI

```bash
k-lean status     # Component health
k-lean doctor -f  # Diagnose + auto-fix
k-lean start      # Start all services
k-lean stop       # Stop all services
k-lean models     # List available models
k-lean test       # Run verification suite
```

---

## File Locations

| Type | Path |
|------|------|
| Scripts | `~/.claude/scripts/` |
| Commands | `~/.claude/commands/kln/` |
| Settings | `~/.claude/settings.json` |
| LiteLLM Config | `~/.config/litellm/config.yaml` |
| Droids | `~/.factory/droids/` |
| Knowledge | `.knowledge-db/` (per project) |

---

## Next Steps

- **[User Guide](USER_GUIDE.md)** - Complete command reference
- **[Installation Guide](INSTALLATION.md)** - Detailed setup
- **[Architecture](../architecture/SYSTEMS.md)** - System design

---

## Troubleshooting

### LiteLLM not running

```bash
k-lean doctor -f  # Auto-diagnose and fix
k-lean start      # Start services
```

### Model not responding

```bash
healthcheck       # Check all models
k-lean models     # See model status
```

### Command not found

```bash
/kln:help         # List all commands
```
