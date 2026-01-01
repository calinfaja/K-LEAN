# K-LEAN Documentation

Welcome to the K-LEAN documentation. This guide covers installation, usage, and configuration.

---

## Getting Started

New to K-LEAN? Start here:

1. **[Installation](installation.md)** - Install and configure K-LEAN
2. **[Usage](usage.md)** - Learn the commands and workflows
3. **[Reference](reference.md)** - Complete configuration reference

---

## Documentation Index

### User Guides

| Document | Description |
|----------|-------------|
| [Installation](installation.md) | Prerequisites, install steps, provider setup |
| [Usage](usage.md) | Slash commands, agents, workflows, output locations |
| [Reference](reference.md) | CLI flags, config files, KB schema, review areas |

### Architecture

| Document | Description |
|----------|-------------|
| [Overview](architecture/OVERVIEW.md) | System architecture, component summary |
| [Components](architecture/COMPONENTS.md) | CLI, hooks, Knowledge DB, LiteLLM, agents |
| [Development](architecture/DEVELOPMENT.md) | Dev setup, conventions, testing, releases |

### Internals

| Document | Description |
|----------|-------------|
| [Project Index](INDEX.md) | Complete codebase reference with cross-links |

---

## Quick Reference

### Commands

```bash
/kln:quick <focus>     # Single model review (~30s)
/kln:multi <focus>     # 3-5 model consensus (~60s)
/kln:agent <role>      # Specialist agent (~2min)
/kln:rethink           # Contrarian debugging
/kln:learn             # Capture insights from context
/kln:status            # System health
```

### CLI

```bash
kln install            # Install components
kln setup              # Configure API provider
kln doctor -f          # Diagnose and auto-fix
kln start              # Start services
kln models             # List available models
```

### Keywords

```bash
FindKnowledge <query>  # Search knowledge DB
SaveInfo <url>         # Evaluate and save URL
```

---

## Requirements

| Requirement | Version |
|-------------|---------|
| Python | 3.9+ |
| Claude Code | 2.0+ |
| API Key | NanoGPT or OpenRouter |

---

## Support

- **Issues**: [GitHub Issues](https://github.com/calinfaja/K-LEAN/issues)
- **Main README**: [K-LEAN](https://github.com/calinfaja/K-LEAN#readme)
