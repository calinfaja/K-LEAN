<p align="center">
  <img src="assets/logo-banner.png" alt="K-LEAN" width="500">
</p>

<p align="center">
  <strong>Second opinions from multiple LLMs—right inside Claude Code</strong>
</p>

<p align="center">
  <a href="https://github.com/calinfaja/K-LEAN/actions"><img src="https://github.com/calinfaja/K-LEAN/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://pypi.org/project/kln-ai/"><img src="https://img.shields.io/pypi/v/kln-ai.svg" alt="PyPI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-green.svg" alt="License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/python-3.9+-yellow.svg" alt="Python"></a>
</p>

---

## Why K-LEAN?

Need a second opinion on your code? Want validation before merging? Looking for domain expertise your model doesn't have? Stuck in a loop and need fresh eyes to break out?

One model's confidence isn't proof. K-LEAN brings in **OpenAI, Gemini, DeepSeek, Moonshot, Minimax**, and more—when multiple models agree, you ship with confidence.

- **9 slash commands** — `/kln:quick`, `/kln:multi`, `/kln:agent`, `/kln:rethink`...
- **8 specialist agents** — Security, Rust, embedded C, ARM Cortex, performance
- **4 smart hooks** — Service auto-start, keyword handling, git tracking, web capture
- **Persistent knowledge** — Insights that survive across sessions

Access any model via **NanoGPT** or **OpenRouter**, directly from Claude Code.

---

## Quick Start

```bash
# Install (~60s)
pipx install kln-ai

# Setup (3-4 minutes total)
kln init                  # Initialize with provider selection
kln start                 # Start LiteLLM proxy service
kln status                # Verify configuration

# Optional: Add more models
kln model add --provider openrouter "anthropic/claude-3.5-sonnet"
kln model remove "claude-3-sonnet"  # Remove a model
kln start
```

**In Claude Code:**
```bash
/kln:quick "security"          # Fast review (~60s)
/kln:multi "error handling"    # 3-5 model consensus (~2min)
/kln:agent security-auditor    # Specialist agent (~2min)
```

**For development:**
```bash
kln install               # (Usually automatic, only needed after major upgrades)
```

---

## See It In Action

```
$ /kln:multi "review authentication flow"

GRADE: B+ | RISK: MEDIUM

HIGH CONFIDENCE (4/5 models agree):
  - auth.py:42 - SQL injection risk in user query
  - session.py:89 - Missing token expiration check

MEDIUM CONFIDENCE (2/5 models agree):
  - login.py:15 - Consider rate limiting
```

---

## Features

### Multi-Model Consensus

Get **consensus** from 3-5 different LLMs on your code. When they agree, you know it's real.

```bash
/kln:multi "review authentication flow"
```

### Specialist Agents

8 domain experts powered by [smolagents](https://github.com/huggingface/smolagents), each with tools to explore your codebase:

| Agent | Expertise |
|-------|-----------|
| `code-reviewer` | OWASP Top 10, SOLID, code quality |
| `security-auditor` | Vulnerabilities, auth, crypto |
| `debugger` | Root cause analysis |
| `performance-engineer` | Profiling, optimization |
| `rust-expert` | Ownership, lifetimes, unsafe |
| `c-pro` | C99/C11, POSIX, memory |
| `arm-cortex-expert` | Embedded ARM, real-time |
| `orchestrator` | Multi-agent coordination |

```bash
/kln:agent security-auditor "audit the payment module"
```

### Persistent Knowledge

Never lose insights. K-LEAN captures lessons to a searchable knowledge base:

```bash
/kln:learn "JWT validation issue"    # Save from context
FindKnowledge "JWT validation"       # Search later
```

- **Per-project isolation** — Each repo gets its own knowledge base
- **Semantic search** — Find by meaning, not just keywords
- **Auto-capture** — Git commits and reviews logged automatically

### Contrarian Debugging

When you're stuck, get **fresh perspectives**:

```bash
/kln:rethink
```

Uses 4 techniques: inversion, assumption challenge, domain shift, root cause reframe.

---

## All Commands

| Command | Description | Time |
|---------|-------------|------|
| `/kln:quick <focus>` | Single model review | ~30s |
| `/kln:multi <focus>` | 3-5 model consensus | ~60s |
| `/kln:agent <role>` | Specialist agent with tools | ~2min |
| `/kln:rethink` | Contrarian debugging | ~20s |
| `/kln:learn` | Capture insights from context | ~10s |
| `/kln:remember` | End-of-session knowledge capture | ~20s |
| `/kln:doc <title>` | Generate session docs | ~30s |
| `/kln:status` | System health check | ~2s |
| `/kln:help` | Command reference | instant |

**Flags:** `--async` (background), `--models N` (count), `--output json|text`

---

## Smart Hooks

K-LEAN hooks run automatically in the background:

- **Service auto-start** — LiteLLM proxy and Knowledge Server start on session begin
- **Keyword handling** — Type keywords directly, no slash command needed
- **Git tracking** — Commits logged to timeline, facts extracted automatically
- **Web capture** — URLs from WebFetch/Tavily evaluated and saved if relevant

### Hook Keywords

Type these directly in Claude Code (no `/` prefix):

| Keyword | Action |
|---------|--------|
| `FindKnowledge <query>` | Semantic search knowledge DB |
| `SaveInfo <url>` | Evaluate URL with AI, save if relevant |
| `InitKB` | Initialize knowledge DB for current project |
| `asyncConsensus [focus]` | Background 3-model consensus review |
| `asyncReview <model> <focus>` | Background single-model review |

---

## CLI Reference

```bash
# Installation & Setup
kln install          # Install to ~/.claude/
kln uninstall        # Remove components
kln setup            # Configure API providers (interactive)
kln add-model        # Add individual models to config

# Services
kln start            # Start LiteLLM proxy
kln stop             # Stop all services
kln status           # Show component status

# Diagnostics
kln doctor           # Check configuration
kln doctor -f        # Auto-fix issues
kln models           # List available models
kln models --health  # Check model health

# Development
kln test             # Run test suite
kln version          # Show version
```

---

## Requirements

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.9+ | `python3 --version` |
| Claude Code | 2.0+ | `claude --version` |
| pipx | any | `pipx --version` |
| API Key | - | NanoGPT or OpenRouter |

---

## Recommended Providers

### NanoGPT

[NanoGPT](https://nano-gpt.com) — Best value subscription for top-tier models.

- **Top providers** — DeepSeek, Alibaba, Zhipu, Moonshot, Minimax, Meta
- **Thinking models** — Reasoning chains for complex analysis
- **Simple setup** — One API key, 200+ models

### OpenRouter

[OpenRouter](https://openrouter.ai) — Unified API gateway for major providers.

- **Top providers** — Anthropic, Google, Meta, Mistral, DeepSeek, OpenAI
- **Free tiers** — Some models available at no cost
- **Simple setup** — One API key, 500+ models

---

## Recommended Add-ons

For a complete coding experience:

| Tool | Integration |
|------|-------------|
| [SuperClaude](https://github.com/SuperClaude-Org/SuperClaude) | Use `/sc:*` and `/kln:*` together |
| [Serena MCP](https://github.com/oraios/serena) | Shared memory, code understanding |
| [Context7 MCP](https://github.com/upstash/context7) | Documentation lookup |
| [Tavily MCP](https://github.com/tavily-ai/tavily-mcp) | Web search for research |
| [Sequential Thinking MCP](https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking) | Step-by-step reasoning for complex problems |

**Telemetry:** Install [Phoenix](https://github.com/Arize-ai/phoenix) to watch agent steps and reviews at `localhost:6006`.

---

## Documentation

| Document | Description |
|----------|-------------|
| [Installation](docs/installation.md) | Detailed setup guide |
| [Usage](docs/usage.md) | Commands, workflows, examples |
| [Reference](docs/reference.md) | Complete config reference |
| [Architecture](docs/architecture/OVERVIEW.md) | System design |

---

## Contributing

```bash
git clone https://github.com/calinfaja/K-LEAN.git
cd k-lean
pipx install -e .
kln install --dev
kln test
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

Apache 2.0 — See [LICENSE](LICENSE)

---

<p align="center">
  <b>Get second opinions. Ship with confidence.</b>
</p>
