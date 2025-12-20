<p align="center">
  <img src="docs/assets/klean-logo.png" alt="K-LEAN Logo" width="200"/>
</p>

<h1 align="center">K-LEAN</h1>
<h3 align="center">Knowledge-Leveraged Engineering Analysis Network</h3>

<p align="center">
  <strong>Multi-model AI code reviews without the cloud costs</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#features">Features</a> •
  <a href="#how-it-works">How It Works</a> •
  <a href="#installation">Installation</a> •
  <a href="docs/guides/USER_GUIDE.md">Documentation</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"/>
  <img src="https://img.shields.io/badge/python-3.9+-green.svg" alt="Python 3.9+"/>
  <img src="https://img.shields.io/badge/claude--code-compatible-purple.svg" alt="Claude Code Compatible"/>
</p>

---

## The Problem

You want AI-powered code reviews, but:
- **Claude/GPT API costs add up fast** for large codebases
- **Single-model reviews miss issues** that other models catch
- **You forget solutions** and re-solve the same problems
- **No persistent memory** across coding sessions

## The Solution

K-LEAN gives you **multi-model consensus reviews** using affordable API providers ($0.50/million tokens via NanoGPT), plus a **semantic knowledge database** that remembers everything you learn.

```bash
# Get 5 models to review your code for security issues
/kln:multi --models 5 security audit

# Ask what you learned about authentication last week
FindKnowledge authentication patterns
```

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/AICodingDojo/claudeAgentic.git
cd claudeAgentic

# 2. Run the installer
./review-system-backup/install.sh

# 3. Set your API key
export NANOGPT_API_KEY="your-key-from-nano-gpt.com"

# 4. Start the services
k-lean start

# 5. Try a review!
/kln:quick security
```

**That's it.** You now have multi-model reviews and persistent knowledge capture.

---

## Features

### Multi-Model Reviews

| Command | What It Does | Time |
|---------|--------------|------|
| `/kln:quick` | Fast single-model review | ~30s |
| `/kln:multi` | Consensus from 3-5 models | ~60s |
| `/kln:deep` | Full codebase analysis | ~3min |
| `/kln:droid` | Specialist agent (security, perf, etc.) | ~2min |

### Knowledge Database

```bash
# Save a lesson learned
SaveThis "Connection pooling in Python requires explicit close() calls"

# Find it later
FindKnowledge connection pooling

# Auto-captures from web research
# (URLs you fetch are automatically evaluated and stored)
```

### 8 Specialist Droids

| Droid | Expertise |
|-------|-----------|
| `code-reviewer` | Code quality, patterns |
| `security-auditor` | Vulnerabilities, OWASP |
| `performance-engineer` | Optimization, profiling |
| `debugger` | Root cause analysis |
| `rust-expert` | Rust-specific patterns |
| `c-pro` | C/embedded systems |
| `arm-cortex-expert` | ARM architecture |
| `orchestrator` | Multi-droid coordination |

### CLI Dashboard

```bash
k-lean status    # Component health
k-lean doctor    # Diagnose issues
k-lean models    # List available models with latency
k-lean test      # Run 27-test verification suite
```

---

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│                     Claude Code CLI                      │
├─────────────────────────────────────────────────────────┤
│  /kln:quick    /kln:multi    /kln:deep    /kln:droid   │
├─────────────────────────────────────────────────────────┤
│                    LiteLLM Proxy                        │
│              (localhost:4000)                           │
├─────────────────────────────────────────────────────────┤
│  qwen3-coder │ deepseek │ glm │ minimax │ kimi │ hermes│
│      (NanoGPT: $0.50/1M tokens)                        │
├─────────────────────────────────────────────────────────┤
│              Knowledge Database                         │
│         (per-project semantic search)                   │
└─────────────────────────────────────────────────────────┘
```

1. **You type a command** like `/kln:multi security`
2. **LiteLLM routes** to multiple models in parallel
3. **Each model reviews** your code independently
4. **Results are synthesized** into actionable feedback
5. **Lessons get stored** in your knowledge database

---

## Installation

### Prerequisites

- **Claude Code CLI** (latest version)
- **Python 3.9+**
- **API key** from [NanoGPT](https://nano-gpt.com) ($0.50/1M tokens) or OpenRouter

### Full Installation

```bash
# Clone
git clone https://github.com/AICodingDojo/claudeAgentic.git
cd claudeAgentic

# Install K-LEAN CLI
pipx install -e review-system-backup

# Install components
k-lean install

# Configure LiteLLM
~/.claude/scripts/setup-litellm.sh

# Verify
k-lean test
```

See [Installation Guide](docs/guides/INSTALLATION.md) for detailed instructions.

---

## Configuration

### API Providers

| Provider | Cost | Setup |
|----------|------|-------|
| **NanoGPT** | $0.50/1M | `export NANOGPT_API_KEY=...` |
| **OpenRouter** | Varies | `export OPENROUTER_API_KEY=...` |
| **Ollama** | Free (local) | Install Ollama, run models |

### Available Models

```bash
k-lean models --test  # See all models with latency
```

Default models via NanoGPT:
- `qwen3-coder` - Code quality, bugs
- `deepseek-v3-thinking` - Architecture, design
- `glm-4.6-thinking` - Standards, compliance
- `minimax-m2` - Research, context
- `kimi-k2-thinking` - Planning, agents
- `hermes-4-70b` - Scripting, automation

---

## Documentation

| Guide | Description |
|-------|-------------|
| [Quick Start](docs/guides/QUICK_START.md) | 5-minute setup |
| [User Guide](docs/guides/USER_GUIDE.md) | Complete command reference |
| [Installation](docs/guides/INSTALLATION.md) | Detailed setup |
| [Architecture](docs/architecture/SYSTEMS.md) | System design |
| [Droids](docs/architecture/DROIDS.md) | Specialist agents |

---

## Project Structure

```
claudeAgentic/
├── review-system-backup/       # Main source
│   ├── src/klean/              # K-LEAN CLI
│   ├── scripts/                # Shell/Python scripts
│   ├── commands/kln/           # Slash commands
│   ├── hooks/                  # Claude Code hooks
│   ├── droids/                 # Specialist agents
│   └── config/                 # LiteLLM configs
├── docs/                       # Documentation
│   ├── guides/                 # User guides
│   ├── architecture/           # System design
│   └── reports/                # Test reports
└── LICENSE                     # MIT License
```

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Development setup
git clone https://github.com/AICodingDojo/claudeAgentic.git
cd claudeAgentic
pipx install -e review-system-backup --force
k-lean test  # Run test suite
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- Built for [Claude Code](https://claude.ai/code)
- Powered by [LiteLLM](https://github.com/BerriAI/litellm)
- Embeddings by [txtai](https://github.com/neuml/txtai)
- Models via [NanoGPT](https://nano-gpt.com)

---

<p align="center">
  <strong>Stop paying cloud prices for code reviews.</strong><br/>
  <strong>Start building a knowledge base that remembers.</strong>
</p>
