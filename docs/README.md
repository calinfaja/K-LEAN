# K-LEAN

Multi-model code review and knowledge capture for Claude Code.

## What It Does

- **Reviews**: 12 LLM models review your code with consensus scoring
- **Knowledge**: Captures lessons learned with semantic search
- **SmolKLN Agents**: 8 specialist AI agents for domain-specific analysis

## Quick Start

```bash
pipx install k-lean
k-lean install
k-lean doctor
```

## Documentation

| Doc | Purpose |
|-----|---------|
| [Installation](installation.md) | Setup guide |
| [Usage](usage.md) | Commands and workflows |
| [Reference](reference.md) | All options and configuration |

## Quick Commands

```bash
# In Claude Code
/kln:quick security          # Fast review (~30s)
/kln:multi architecture      # 3-5 model consensus (~60s)
/kln:agent security-auditor  # Specialist agent (~2min)
/kln:learn "topic"           # Extract learnings from context

# Keywords (type directly)
FindKnowledge "topic"         # Search knowledge
```

## Requirements

- Python 3.9+
- Claude Code 2.0+
- LiteLLM proxy (included)
- NanoGPT or OpenRouter API key
