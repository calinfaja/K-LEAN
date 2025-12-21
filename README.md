# K-LEAN Companion

> **Second opinions for Claude Code** — Multi-model reviews, persistent knowledge, specialist agents

[![CI](https://github.com/calinfaja/K-LEAN-Companion/actions/workflows/ci.yml/badge.svg)](https://github.com/calinfaja/K-LEAN-Companion/actions)
[![Version](https://img.shields.io/badge/version-1.0.0--beta-blue.svg)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-yellow.svg)](https://python.org)

---

## The Problem

Claude Code is exceptional — but sometimes you need a **second opinion**.

When debugging goes circular, when architecture decisions feel uncertain, or when you want validation before merging — getting perspectives from multiple top-tier models breaks the loop and catches what a single model might miss.

That's why I built K-LEAN: to access the best open-source models (DeepSeek, Qwen, GLM, Kimi) through a single NanoGPT subscription, while maintaining persistent knowledge across sessions.

---

## What K-LEAN Adds

| | Feature | What It Does |
|---|---------|--------------|
| **Multi-Model Reviews** | Get consensus from 3-5 models on any code question |
| **Persistent Knowledge** | Semantic search across sessions using txtai embeddings |
| **Factory Droids** | 8 specialist agents (security, performance, architecture...) |
| **Live Status Bar** | Real-time model health, KB status, active reviews |

---

## Quick Install

```bash
pipx install k-lean           # Install CLI
k-lean install                # Deploy to ~/.claude/
k-lean setup                  # Configure API (interactive)
k-lean doctor                 # Verify everything works
```

---

## System Components

| Component | Purpose | Usage |
|-----------|---------|-------|
| **Hooks** | Auto-trigger on prompts & git commits | `SaveThis`, `FindKnowledge`, `GoodJob`, `asyncReview`... |
| **Slash Commands** | 9 consolidated `/kln:*` commands | `/kln:quick`, `/kln:multi`, `/kln:deep`, `/kln:droid` |
| **Review System** | Headless Claude + LiteLLM proxy | Multi-model consensus, async background reviews |
| **Factory Droids** | 8 specialist AI agents | `--role security`, `--role architect`, `--role performance` |
| **Knowledge DB** | Per-project semantic memory | Auto-captures lessons, searchable across sessions |
| **Status Bar** | Claude Code statusline integration | Model health, KB entries, active background tasks |

---

## Commands (9 total)

| Command | Description | Example |
|---------|-------------|---------|
| `/kln:quick` | Fast single-model review (~30s) | `/kln:quick security` |
| `/kln:multi` | Multi-model consensus (~60s) | `/kln:multi --models 5 architecture` |
| `/kln:deep` | Thorough review with full tool access (~3min) | `/kln:deep --async security audit` |
| `/kln:droid` | Specialist agent review | `/kln:droid --role security` |
| `/kln:rethink` | Fresh debugging perspectives | `/kln:rethink "bug persists after fix"` |
| `/kln:doc` | Session documentation | `/kln:doc "Sprint Review"` |
| `/kln:remember` | End-of-session knowledge capture | `/kln:remember` |
| `/kln:status` | System health check | `/kln:status` |
| `/kln:help` | Command reference | `/kln:help` |

**Flags:** `--async` (background), `--models N` (count), `--output json|text`

---

## How It Works

```
┌──────────────────────────────────────────────────────────────┐
│                      Claude Code                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
│  │   Hooks     │  │  /kln:*     │  │   Factory Droids    │   │
│  │ SaveThis    │  │  Commands   │  │   8 Specialists     │   │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘   │
└─────────┼────────────────┼────────────────────┼──────────────┘
          │                │                    │
          ▼                ▼                    ▼
┌──────────────────────────────────────────────────────────────┐
│                    LiteLLM Proxy (:4000)                      │
│         Qwen · DeepSeek · GLM · Kimi · Minimax · Hermes       │
└──────────────────────────────────────────────────────────────┘
          │                                     │
          ▼                                     ▼
┌─────────────────────────┐    ┌───────────────────────────────┐
│     Knowledge DB        │    │      NanoGPT / OpenRouter     │
│  txtai embeddings       │◄───│      12+ Models, $15/mo       │
│  .knowledge-db/         │    │      or pay-per-use           │
└─────────────────────────┘    └───────────────────────────────┘
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Installation Guide](docs/installation.md) | Detailed setup instructions |
| [Usage Guide](docs/usage.md) | Commands, workflows, examples |
| [Reference](docs/reference.md) | Complete command & config reference |
| [Architecture](.agents/architecture.md) | System design & components |
| [Review System](.agents/review-system.md) | Multi-model review pipeline |
| [Knowledge DB](.agents/knowledge-db.md) | Semantic memory system |
| [Factory Droids](.agents/droids.md) | Specialist agent roles |

---

## Compatibility

K-LEAN works seamlessly with:

| Framework/Tool | Integration |
|----------------|-------------|
| **[SuperClaude](https://github.com/SuperClaude-Org/SuperClaude_Framework)** | Full compatibility — use `/sc:*` and `/kln:*` together |
| **[Serena MCP](https://github.com/oraios/serena)** | Shares memory system, enhances code understanding |
| **Context7 MCP** | Documentation lookup for reviews |
| **Tavily MCP** | Web search for research tasks |
| **Sequential Thinking MCP** | Multi-step reasoning in deep reviews |

---

## Why NanoGPT?

K-LEAN uses [NanoGPT](https://nano-gpt.com) as the default backend:

- **$15/month** — Unlimited access to most models
- **12+ models** — DeepSeek, Qwen, GLM, Kimi, Minimax, Hermes
- **Best open-source models** — Often match or exceed GPT-4 on coding tasks
- **Alternative:** [OpenRouter](https://openrouter.ai) (pay-per-use)

Configure with: `k-lean setup`

---

## Requirements

- **Python 3.9+**
- **Claude Code CLI 2.0+** (the tool this extends)
- **pipx** (for installation)
- **API Key** — NanoGPT ($15/mo) or OpenRouter (pay-per-use)

---

## CLI Reference

```bash
k-lean install      # Install components to ~/.claude/
k-lean setup        # Configure API provider (interactive)
k-lean uninstall    # Remove components
k-lean status       # Check component status
k-lean doctor       # Diagnose issues
k-lean doctor -f    # Auto-fix common issues
k-lean start        # Start LiteLLM proxy
k-lean stop         # Stop services
k-lean models       # List available models
k-lean test         # Run test suite
```

---

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

Apache 2.0 — See [LICENSE](LICENSE)

---

<p align="center">
  <i>Built for developers who want more perspectives on their code.</i>
</p>
