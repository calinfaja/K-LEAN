# K-LEAN

> Multi-Model Code Review & Knowledge Capture System for Claude Code

[![Version](https://img.shields.io/badge/version-1.0.0--beta-blue.svg)](VERSION)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-yellow.svg)](https://python.org)

## What is K-LEAN?

K-LEAN extends Claude Code with:
- **12 AI Models** via LiteLLM (NanoGPT, $0.50/1M tokens)
- **4-Tier Reviews** - Quick → Compare → Deep → Audit
- **Knowledge DB** - Semantic search for captured insights
- **20+ Commands** - `/kln:quickReview`, `/kln:deepAudit`, etc.
- **8 Droids** - Specialized AI agents (security, performance, etc.)

## Quick Install

```bash
git clone https://github.com/calinfaja/k-lean.git
cd k-lean
./install.sh --full
```

## Quick Start

```bash
# Review code
/kln:quickReview qwen3-coder security

# Compare 3 models
/kln:quickCompare architecture

# Capture knowledge
GoodJob https://useful-docs.com
SaveThis learned pattern X improves Y

# Search knowledge
FindKnowledge authentication
```

## Commands

```bash
k-lean status       # Check components
k-lean doctor       # Diagnose issues
k-lean models       # List available models
k-lean start        # Start services
```

## Documentation

| Document | Description |
|----------|-------------|
| [DOCS.md](DOCS.md) | Complete documentation |
| [docs/DEVELOPER.md](docs/DEVELOPER.md) | Developer guide |

## Requirements

- Claude Code CLI
- Python 3.9+
- LiteLLM (`pipx install litellm`)
- NanoGPT API key (or OpenRouter)

## License

MIT - See [LICENSE](LICENSE)
