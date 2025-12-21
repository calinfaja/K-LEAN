# K-LEAN

> Multi-Model Code Review & Knowledge Capture System for Claude Code

[![Version](https://img.shields.io/badge/version-1.0.0--beta-blue.svg)](VERSION)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-yellow.svg)](https://python.org)

## What is K-LEAN?

K-LEAN extends Claude Code with:
- **12 AI Models** via LiteLLM (NanoGPT, OpenRouter)
- **9 Consolidated Commands** - Simplified from 21 old commands
- **Knowledge DB** - Semantic search for captured insights
- **Rethink Mode** - Fresh debugging perspectives from multiple models
- **8 Droids** - Specialized AI agents (security, performance, etc.)

## Quick Install

```bash
# Install K-LEAN
pipx install k-lean

# Install components to ~/.claude/
k-lean install

# Configure API keys (interactive wizard)
~/.claude/scripts/setup-litellm.sh

# Verify installation
k-lean doctor
```

## Commands (9 total)

| Command | Description | Example |
|---------|-------------|---------|
| `/kln:quick` | Fast single-model review | `/kln:quick security` |
| `/kln:multi` | Multi-model consensus (3-5 models) | `/kln:multi --models 5 architecture` |
| `/kln:deep` | Thorough review with SDK tools | `/kln:deep --async security` |
| `/kln:droid` | Role-based AI workers | `/kln:droid --role security audit` |
| `/kln:rethink` | Fresh debugging perspectives | `/kln:rethink memory leak` |
| `/kln:doc` | Session documentation | `/kln:doc "Session Title"` |
| `/kln:remember` | End-of-session knowledge capture | `/kln:remember` |
| `/kln:status` | Models, health, help | `/kln:status` |
| `/kln:help` | Complete command reference | `/kln:help` |

### Key Features

- **--async flag**: Run any command in background (replaces separate async commands)
- **--models N**: Specify number of models for multi-model commands
- **Auto-discovery**: Models discovered from LiteLLM, not hardcoded

## Quick Start

```bash
# Quick review with auto-selected model
/kln:quick security audit

# Multi-model consensus (5 models)
/kln:multi --models 5 architecture review

# Fresh debugging ideas when stuck
/kln:rethink "bug persists after fix"

# Check system status
/kln:status
```

## Knowledge System

```bash
# Capture URL to knowledge DB
GoodJob https://useful-docs.com

# Save lesson directly
SaveThis learned pattern X improves Y

# Search knowledge
FindKnowledge authentication
```

## CLI Commands

```bash
k-lean status       # Check all components
k-lean doctor       # Diagnose + auto-fix
k-lean models       # List available models with health
k-lean start        # Start services
k-lean debug        # Monitoring dashboard
```

## Documentation

| Document | Description |
|----------|-------------|
| [docs/installation.md](docs/installation.md) | Installation guide |
| [docs/usage.md](docs/usage.md) | Commands & workflows |
| [docs/reference.md](docs/reference.md) | Complete reference |
| [.agents/](.agents/) | Technical docs for AI agents |

## Requirements

- Python 3.9+
- Claude Code CLI 2.0+
- pipx (for installing K-LEAN)
- NanoGPT API key (or OpenRouter)

## MCP Servers (Optional)

K-LEAN works with these MCP servers. Install via `claude mcp add`:

```bash
# Context7 - Documentation lookup (Recommended)
claude mcp add context7 -- npx -y @upstash/context7-mcp

# Sequential Thinking - Multi-step reasoning (Recommended)
claude mcp add sequential-thinking -- npx -y @anthropics/mcp-server-sequential-thinking

# Tavily - Web search (requires API key)
claude mcp add tavily --env TAVILY_API_KEY=your-key -- npx -y @tavily/mcp

# Serena - Semantic code understanding (Python-based)
# See: https://github.com/oraios/serena
```

Check installed: `claude mcp list`

## Changelog

### v1.0.0-beta (2025-12-16)

- **Breaking**: Consolidated 21 commands → 9 commands
- **New**: `/kln:rethink` - Fresh debugging perspectives
- **New**: `klean_core.py` - 1189-line execution engine
- **New**: Auto-discovery model resolution
- **Improved**: `--async` flag replaces separate async commands
- **Improved**: Multi-model consensus with ranked findings

## License

Apache 2.0 - See [LICENSE](LICENSE)
